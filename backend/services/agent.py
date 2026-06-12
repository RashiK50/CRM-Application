import datetime
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from database import SessionLocal
from backend.models import Email, Thread, Action
from backend.services.llm_classifier import LLMClassifierService
from backend.services.rag_pipeline import RAGPipelineService

# Import our beautifully segregated components
from backend.services.agent_state import AgentState
from backend.services.agent_tools import AgentTools
from backend.services.agent_nodes import AgentNodes

class AutonomousAgentService:
    def __init__(self):
        self.classifier = LLMClassifierService()
        self.rag = RAGPipelineService()
        
        # Initialize nodes with our LLM brain and RAG tool
        # self.nodes = AgentNodes(brain=self.classifier.model, rag_service=self.rag)
        self.nodes = AgentNodes(brain=self.classifier.client, rag_service=self.rag)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Compiles the LangGraph ReAct architecture."""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("think", self.nodes.node_think)
        workflow.add_node("act", self.nodes.node_act)
        
        workflow.set_entry_point("think")
        
        workflow.add_conditional_edges(
            "think",
            self.nodes.route_execution,
            {"act": "act", END: END}
        )
        
        workflow.add_edge("act", "think")
        return workflow.compile()

    def execute_triage(self, email_id: int, dry_run: bool = False) -> Dict[str, Any]:
        """Main entry point for processing an email through the agent loop."""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email: return {"error": "Email target node not found."}

            print(f"\n==============================================")
            print(f"🚀 INITIATING AUTONOMOUS AGENT FOR EMAIL ID: {email_id}")
            print(f"==============================================")

            # LAYER 1: The Traffic Cop (Spam Shield)
            history = AgentTools.get_thread_history(db, email.thread_id)
            ai_metrics = self.classifier.classify_email(email.body, history)
            
            if ai_metrics.category == "Spam":
                print(f"🛑 [TRAFFIC COP] Spam detected. Halting LangGraph initiation.")
                if not dry_run:
                    email.status = "Ignored"
                    email.category = "Spam"
                    db.commit()
                return {"status": "Ignored", "category": "Spam"}

            # LAYER 2: Initialize LangGraph State
            initial_state: AgentState = {
                "email_id": email_id,
                "thread_id": email.thread_id,
                "sender": email.sender,
                "body": email.body,
                "history": history,
                "category": ai_metrics.category,
                "urgency": email.urgency,
                "requires_human": ai_metrics.requires_human,
                "suggested_reply": "",
                "reasoning_steps": [{"observation": f"Traffic Cop Category: {ai_metrics.category}"}],
                "tool_counter": 0,
                "dry_run": dry_run
            }

            # EXECUTE THE GRAPH
            print(f"⚡ [LANGGRAPH] Entering ReAct Loop...")
            final_state = self.graph.invoke(initial_state)

            # Extract final decisions from the trace
            # Extract final decisions from the trace
            final_action = [step for step in final_state["reasoning_steps"] if step.get("tool") == "final_answer"][-1]
            final_inputs = final_action.get("tool_input", {})
            
            # 1. Grab raw status from LLM
            raw_status = final_inputs.get("status", "Escalated")
            requires_human = final_inputs.get("requires_human", True)
            
            # Extract the proposed draft
            proposed_draft = final_inputs.get("draft_reply", "Ticket received. A senior manager has been assigned.")
            
            # 2. SANITIZE IT: Force "resolved" -> "Resolved", "auto-replied" -> "Auto-Replied"
            clean_status = str(raw_status).strip().title()
            
            # 3. Let the AI win if it confidently auto-replied!
            if clean_status in ["Auto-Replied", "Replied", "Resolved", "Answered"]:
                action_type = "Auto-Reply"
                requires_human = False
                final_status = "Auto-Replied" # <--- FORCE EXACT MATCH FOR DASHBOARD
            else:
                action_type = "Escalate"
                final_status = "Escalated" # Force standard casing for Escalate too
                
            # Keep your hardcoded safety override for Critical threats only
            if email.urgency == "Critical" or ai_metrics.urgency == "Critical":
                final_status = "Escalated"
                action_type = "Escalate"
                requires_human = True

            print(f"✅ [AGENT COMPLETE] Final Status: {final_status} | Action: {action_type}")

            # Persist to Database
            # Persist to Database
            if not dry_run:
                email.category = final_state["category"]
                email.status = final_status
                email.requires_human = requires_human
                
                # THE MISSING LINK: Actually save the cleaned urgency to the database!
                email.urgency = str(ai_metrics.urgency).strip().title() 
                
                thread = db.query(Thread).filter(Thread.thread_id == email.thread_id).first()
                if thread: thread.status = final_status

                # 1. Safely convert the dictionary to a JSON string
                safe_proposed_content = json.dumps(proposed_draft) if isinstance(proposed_draft, dict) else str(proposed_draft)
                
                # 2. Also convert the reasoning log to a string to be completely safe
                safe_reasoning_log = json.dumps({"trace": final_state["reasoning_steps"]})

                action = Action(
                    email_id=email.id,
                    agent_reasoning_log=safe_reasoning_log,
                    action_type=action_type,
                    proposed_content=safe_proposed_content,
                    executed_at=datetime.datetime.utcnow()
                )
                db.add(action)
                db.commit()

            return {
                "email_id": email_id,
                "status": final_status,
                "reasoning_trace": final_state["reasoning_steps"],
                "proposed_draft": proposed_draft
            }
        finally:
            db.close()