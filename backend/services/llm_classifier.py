import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from backend.schemas import LLMClassificationResponse

class LLMClassifierService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", "MOCK_KEY"))
        # Using gemini-1.5-flash for rapid, cost-effective processing
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def classify_email(self, email_body: str, thread_history: List[Dict[str, str]] = []) -> LLMClassificationResponse:
        """Analyzes email context and returns structured classification metrics."""
        
        # Format the thread history context for the model [cite: 49, 77]
        history_context = ""
        for msg in thread_history:
            history_context += f"Sender: {msg.get('sender')}\nContent: {msg.get('body')}\n---\n"

        prompt = f"""
        You are an expert CRM operational intelligence agent analyzing an incoming business email.
        Analyze the conversation context, historical sequence (if any), and the latest message body carefully.
        
        Historical Thread Context:
        {history_context}
        
        Latest Email Body to Classify:
        {email_body}
        
        Provide your analytical output exactly matching the requested structured schema.
        Resolve conflicting signals (e.g., a compliment mixed with a cancellation threat) by prioritizing the highest business/legal risk.
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