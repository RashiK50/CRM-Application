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
        
        # Format the thread history context for the model [cite: 49, 77]
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
            return LLMClassificationResponse(**data)
            
        except Exception as e:
            # Resilient fallback state for unconfigured keys or network issues [cite: 13]
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