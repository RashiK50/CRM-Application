import os
import sys
import datetime
from typing import Dict, Any, List, TypedDict
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from backend.database import SessionLocal
from backend.models import Email, Thread, Contact, Action, AuditLog
from backend.services.llm_classifier import LLMClassifierService
from backend.services.rag_pipeline import RAGPipelineService

# Enforce LangGraph State Schema contract
class AgentState(TypedDict):
    email_id: int
    thread_id: str
    sender: str
    body: str
    history: List[Dict[str, str]]
    category: str
    urgency: str
    requires_human: bool
    suggested_reply: str
    reasoning_steps: List[Dict[str, str]]
    tool_counter: int
    dry_run: bool

class AutonomousAgentService:
    def __init__(self):
        self.classifier = LLMClassifierService()
        self.rag = RAGPipelineService()

    def _get_thread_history(self, db: Session, thread_id: str) -> List[Dict[str, str]]:
        """Tool: Retrieves previous turns in the conversation[cite: 116, 119]."""
        emails = db.query(Email).filter(Email.thread_id == thread_id).order_by(Email.timestamp.asc()).all()
        return [{"sender": e.sender, "body": e.body} for e in emails[:-1]]

    def _check_crm_profile(self, db: Session, email: str) -> Dict[str, Any]:
        """Tool: Fetches internal customer tiers and current health risk profiles[cite: 117, 120]."""
        contact = db.query(Contact).filter(Contact.email == email).first()
        if contact:
            return {"status": contact.status, "value": float(contact.account_value), "risk": contact.churn_risk_score}
        return {"status": "Active", "value": 0.00, "risk": 0.0}

    def execute_triage(self, email_id: int, dry_run: bool = False) -> Dict[str, Any]:
        """Main compilation runtime graph engine."""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {"error": "Email target node not found."}

            # Gather historical context layers [cite: 49]
            history = self._get_thread_history(db, email.thread_id)
            crm_profile = self._check_crm_profile(db, email.sender)

            # Execution Layer 2 Classification [cite: 75-76]
            ai_metrics = self.classifier.classify_email(email.body, history)

            # RAG Document Grounding Pulls [cite: 103]
            rag_context = self.rag.search_policies(f"{ai_metrics.category} {email.body}")
            context_str = "\n".join([c["text"] for c in rag_context])

            # Edge Case Traps: Secure Compliance Check overrides [cite: 133, 212, 216]
            final_status = "Replied"
            action_type = "Auto-Reply"
            requires_human = ai_metrics.requires_human

            if email.urgency == "Critical" or ai_metrics.urgency == "Critical" or requires_human:
                final_status = "Escalated"
                action_type = "Escalate"
                requires_human = True

            # Construct system reasoning trail traces [cite: 131]
            trace = [
                {"thought": f"Classified inbound message into category: '{ai_metrics.category}' with {ai_metrics.confidence} confidence."},
                {"action": f"Invoked RAG search engine. Found {len(rag_context)} corporate matches."},
                {"observation": f"Evaluated account level profile context details: {crm_profile}."}
            ]

            proposed_reply = ai_metrics.suggested_reply or "Ticket received. A senior manager has been assigned to investigate."

            # Save tracking states down to database ledgers if not running a dry run execution [cite: 131, 134]
            if not dry_run:
                email.category = ai_metrics.category
                email.status = final_status
                email.requires_human = requires_human
                email.confidence = ai_metrics.confidence
                
                # Update Thread tracking states [cite: 60]
                thread = db.query(Thread).filter(Thread.thread_id == email.thread_id).first()
                if thread:
                    thread.status = final_status

                # Append to Actions trace ledger table [cite: 171-172]
                action = Action(
                    email_id=email.id,
                    agent_reasoning_log={"trace": trace, "ai_raw": ai_metrics.category},
                    action_type=action_type,
                    proposed_content=proposed_reply,
                    executed_at=datetime.datetime.utcnow()
                )
                db.add(action)
                db.commit()

            return {
                "email_id": email_id,
                "category": ai_metrics.category,
                "urgency": email.urgency,
                "status": final_status,
                "reasoning_trace": trace,
                "proposed_draft": proposed_reply
            }
        finally:
            db.close()