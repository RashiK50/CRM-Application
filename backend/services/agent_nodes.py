import json
from typing import Dict, Any
import google.generativeai as genai
from langgraph.graph import END

from database import SessionLocal
from backend.services.agent_state import AgentState
from backend.services.agent_tools import AgentTools
from backend.schemas import LLMClassificationResponse



class AgentNodes:
    def __init__(self, brain, rag_service):
        self.brain = brain
        self.rag = rag_service

    def node_think(self, state: AgentState) -> Dict[str, Any]:
        """The Brain: Decides the next step based on the current state."""
        state["tool_counter"] += 1
        print(f"\n🧠 [AGENT THINKING - STEP {state['tool_counter']}] Analyzing current context...")
        
        prompt = f"""
        You are an autonomous CRM agent. You must resolve the following customer email.
        
        Email Body: {state['body']}
        Category: {state['category']}
        
        You have access to the following tools:
        1. "search_rag": Use this to search company policies. Provide a 'tool_input' string.
        2. "check_crm": Use this to check the user's account value. Provide 'tool_input' exactly as this email: {state['sender']}
        3. "flag_legal": Use this IMMEDIATELY if you detect a lawsuit or ransomware. Provide 'tool_input' as reason.
        4. "scrape_sentiment": Use this if the user threatens a public review, mentions PR, or talks about moving to a competitor. Provide 'tool_input' as the name of the company or competitor they are mentioning in the email (e.g., "Stripe" or "OpenAI"). NEVER use the name of the review platform (like Trustpilot or G2) as the input.
        5. "final_answer": Use this when you have enough info. Provide a JSON object for 'tool_input' containing "status", "requires_human", and "draft_reply".

        Previous Steps & Observations:
        {json.dumps(state['reasoning_steps'], indent=2)}

        Decide your next move. You MUST output exactly ONE valid JSON object matching this schema:
        {{"thought": "Why I am doing this", "tool": "tool_name", "tool_input": "input_value_or_object"}}
        """

        import time
        time.sleep(12)

        # try:
        #     response = self.brain.generate_content(prompt, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        #     decision = json.loads(response.text)
        #     print(f"🎯 [AGENT DECISION] Tool chosen: {decision.get('tool')} | Thought: {decision.get('thought')}")
        #     state["reasoning_steps"].append(decision)
        try:
            response = self.brain.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an autonomous CRM routing agent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"} # <-- CHANGED THIS LINE
            )
            output_text = response.choices[0].message.content
            decision = json.loads(output_text)
            print(f"🎯 [AGENT DECISION] Tool chosen: {decision.get('tool')} | Thought: {decision.get('thought')}")
            state["reasoning_steps"].append(decision)

        except Exception as e:
            print(f"❌ [AGENT ERROR] Brain malfunctioned: {str(e)}")
            state["reasoning_steps"].append({
                "thought": "System error during thought process.", 
                "tool": "final_answer", 
                "tool_input": {"status": "Escalated", "requires_human": True, "draft_reply": "Error generating response."}
            })

        return {"reasoning_steps": state["reasoning_steps"], "tool_counter": state["tool_counter"]}

    def node_act(self, state: AgentState) -> Dict[str, Any]:
        """The Hands: Executes the tool chosen by the Brain."""
        db = SessionLocal()
        last_step = state["reasoning_steps"][-1]
        tool = last_step.get("tool")
        tool_input = last_step.get("tool_input")
        
        print(f"🛠️ [AGENT ACTING] Executing Tool: {tool} with input: {tool_input}")
        observation = ""

        try:
            if tool == "search_rag":
                results = self.rag.search_policies(str(tool_input))
                snippets = [f"Doc: {r['metadata'].get('source', 'Unknown')} - {r['text'][:150]}..." for r in results]
                observation = f"RAG Search found {len(results)} results: " + " | ".join(snippets)
            
            elif tool == "check_crm":
                profile = AgentTools.check_crm_profile(db, state["sender"])
                observation = f"CRM Data retrieved: VIP Status={profile['status']}, Value=${profile['value']}, ChurnRisk={profile['risk']}"
            
            elif tool == "flag_legal":
                observation = f"Legal team notified regarding: {tool_input}. Halting auto-reply sequence."
                state["reasoning_steps"].append({"observation": observation})
                state["reasoning_steps"].append({
                    "thought": "Legal flag triggered. Forcing escalation.", 
                    "tool": "final_answer", 
                    "tool_input": {"status": "Escalated", "requires_human": True, "draft_reply": "This matter has been escalated to our legal/compliance team."}
                })
                return {"reasoning_steps": state["reasoning_steps"]}
            
            elif tool == "scrape_sentiment":
                observation = AgentTools.scrape_public_sentiment(str(tool_input))

            else:
                observation = f"Unknown tool requested: {tool}"
                
        finally:
            db.close()

        print(f"👁️ [AGENT OBSERVATION] {observation}")
        state["reasoning_steps"].append({"observation": observation})
        return {"reasoning_steps": state["reasoning_steps"]}

    def route_execution(self, state: AgentState) -> str:
        """The Router: Decides if we loop back to Think, or end the graph."""
        last_step = state["reasoning_steps"][-1]
        
        if last_step.get("tool") == "final_answer":
            print(f"🏁 [AGENT ROUTER] Final answer reached. Exiting loop.")
            return END
        
        if state["tool_counter"] >= 6:
            print(f"⚠️ [AGENT ROUTER] Max steps (6) reached! Forcing escalation circuit breaker.")
            state["reasoning_steps"].append({
                "thought": "Max tool executions reached. I am confused. Escalating to human.",
                "tool": "final_answer",
                "tool_input": {"status": "Escalated", "requires_human": True, "draft_reply": "Ticket auto-escalated due to complex resolution requirements."}
            })
            return END
            
        print(f"🔄 [AGENT ROUTER] Information gathered. Routing back to Brain...")
        return "act"