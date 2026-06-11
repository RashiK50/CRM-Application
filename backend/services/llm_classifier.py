import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from backend.schemas import LLMClassificationResponse
from backend.config import settings

class LLMClassifierService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Using gemini-1.5-flash for rapid, cost-effective processing
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def classify_email(self, email_body: str, thread_history: List[Dict[str, str]] = []) -> LLMClassificationResponse:
        """Analyzes email context and returns structured classification metrics."""
        
        # Format the thread history context for the model
        history_context = ""
        for msg in thread_history:
            history_context += f"Sender: {msg.get('sender')}\nContent: {msg.get('body')}\n---\n"

        prompt = f"""
        You are an expert CRM operational intelligence agent. Your strict directive is to classify incoming emails and output a structured JSON response.

        === CORE TRIAGE RULES ===
        
        RULE 1: THE SPAM SHIELD (Highest Priority)
        If the email is an unsolicited B2B sales pitch, SEO marketing, offshore development offer, paid placement request, or generic lead generation:
        - You MUST classify the intent/category strictly as "Spam".
        - You MUST set `requires_human` to false.
        - You MUST set `urgency` to "Low".
        - Do NOT escalate these under any circumstances.

        RULE 2: ESCALATION CRITERIA (High Risk Only)
        You may only escalate an email (e.g., `requires_human` = true, `urgency` = "High" or "Critical") if it contains:
        - Active security vulnerabilities or phishing attempts.
        - Threats of legal action or severe compliance issues.
        - Critical system outages affecting production.
        - Highly irate customers demanding refunds.
        
        === CONTEXT & PAYLOAD ===
        
        Historical Thread Context:
        {history_context}
        
        Latest Email Body to Classify:
        {email_body}
        
        Analyze the payload strictly against the rules above. Output the final JSON matching the requested schema exactly.
        """

        try:
            # Enforce structured output formatting using Pydantic schemas via API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=LLMClassificationResponse
                )
            )
            
            # Parse response text back into the system validation schema
            data = json.loads(response.text)
            
            # ==========================================
            # THE ENGINEERING OVERRIDE (DETERMINISTIC LOCK)
            # ==========================================
            # ==========================================
            # THE ENGINEERING OVERRIDE (DETERMINISTIC LOCK)
            # ==========================================
            # 1. Define hardcoded spam triggers that overrule the AI
            spam_triggers = [
                "attendee list", "offshore", "seo", "backlink", "guest post", 
                "placement fee", "lead gen", "decision-makers", "synergy"
            ]
            
            # 2. Check if the AI called it Spam, OR if the email body contains a trigger word
            body_lower = email_body.lower()
            is_spam = (data.get("category") == "Spam") or any(trigger in body_lower for trigger in spam_triggers)
            
            if is_spam:
                data["category"] = "Spam"
                data["requires_human"] = False
                data["urgency"] = "Low"
                data["escalation_reason"] = "Auto-filtered by heuristic spam trap."
                
            return LLMClassificationResponse(**data)
            
        except Exception as e:
            # Resilient fallback state for unconfigured keys or network issues
            return LLMClassificationResponse(
                category="Inquiry",
                sentiment="Neutral",
                sentiment_score=0.0,
                urgency="Medium",
                requires_human=True,
                escalation_reason=f"Classification pipeline error fallback: {str(e)}",
                confidence=0.5,
                detected_entities={"order_ids": [], "ticket_ids": [], "monetary_amounts": [], "deadlines": [], "products_mentioned": []}
            )