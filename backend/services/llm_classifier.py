import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from backend.schemas import LLMClassificationResponse
from backend.config import settings
from groq import Groq
from backend.config import settings

class LLMClassifierService:
    def __init__(self):
        # genai.configure(api_key=settings.GEMINI_API_KEY)
        # # Using gemini-1.5-flash for rapid, cost-effective processing
        # self.model = genai.GenerativeModel("gemini-2.5-flash")
        

        # Initialize the Groq client
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def classify_email(self, email_body: str, thread_history: List[Dict[str, str]] = []) -> LLMClassificationResponse:
        """Analyzes email context and returns structured classification metrics."""
        
        # Format the thread history context for the model
        history_context = ""
        for msg in thread_history:
            history_context += f"Sender: {msg.get('sender')}\nContent: {msg.get('body')}\n---\n"
            # Dynamically extract the schema so we never have to hardcode fields
        schema_definition = json.dumps(LLMClassificationResponse.model_json_schema(), indent=2)

        # prompt = f"""
        # You are an expert Enterprise Agentic Router. Your objective is to semantically analyze incoming emails and classify them based on their true intent. 
        # Do not rely on single keywords; look at the holistic purpose of the message.

        # === SEMANTIC CATEGORY DEFINITIONS ===
        
        # 1. THE SPAM BUCKET (Category: "Spam")
        # - Intent: Unsolicited B2B sales, SEO services, offshore development pitches, list brokers, fake vanity awards, or generic lead generation.
        # - Action Rules: You MUST set `requires_human` to false, and `urgency` to "Low". 

        # 2. THE ESCALATION BUCKET (Category: "Legal", "Compliance", or "Other")
        # - Intent: Active security vulnerabilities (phishing, malware), threats of legal action, compliance violations, or severe system outages.
        # - Action Rules: You MUST set `requires_human` to true, and `urgency` to "High" or "Critical".

        # 3. THE STANDARD QUEUE (Category: "Inquiry", "Bug Report", "Billing", "Feature Request")
        # - Intent: Standard customer operations, questions, missing invoices, or software bugs.
        # - Action Rules: Set `requires_human` to false if a standard AI auto-reply can handle it, OR set it to true if complex human intervention is needed.

        # === CONTEXT & PAYLOAD ===
        
        # Historical Thread Context:
        # {history_context}
        
        # Latest Email Body to Classify:
        # {email_body}
        
        # Output valid JSON matching the requested schema. Resolve conflicting signals (e.g., a friendly tone hiding a sales pitch) by prioritizing the true business intent.
        # """

        prompt = f"""
        You are an expert Enterprise Agentic Router. Your objective is to semantically analyze incoming emails and classify them based on their true intent. 
        Do not rely on single keywords; look at the holistic purpose of the message.

        === SEMANTIC CATEGORY DEFINITIONS ===
        
        1. THE SPAM BUCKET (Category: "Spam")
        - Intent: Unsolicited B2B sales, SEO services, offshore development pitches, list brokers, fake vanity awards, or generic lead generation.
        - Action Rules: You MUST set `requires_human` to false, and `urgency` to "Low". 

        2. THE ESCALATION BUCKET (Category: "Legal", "Compliance", or "Other")
        - Intent: Active security vulnerabilities (phishing, malware), threats of legal action, compliance violations, or severe system outages.
        - Action Rules: You MUST set `requires_human` to true, and `urgency` to "High" or "Critical".

        3. THE STANDARD QUEUE (Category: "Inquiry", "Bug Report", "Billing", "Feature Request")
        - Intent: Standard customer operations, questions, missing invoices, or software bugs.
        - Action Rules: Set `requires_human` to false if a standard AI auto-reply can handle it, OR set it to true if complex human intervention is needed.

        === CONTEXT & PAYLOAD ===
        
        Historical Thread Context:
        {history_context}
        
        Latest Email Body to Classify:
        {email_body}
        
        === REQUIRED JSON SCHEMA ===
        You MUST output valid JSON exactly matching the following JSON Schema definition. 
        Do not include any markdown formatting, preamble, or conversational text.
        
        {schema_definition}
        """

        try:
            # Enforce structured output formatting using Pydantic schemas via API
            # response = self.model.generate_content(
            #     prompt,
            #     generation_config=genai.GenerationConfig(
            #         response_mime_type="application/json",
            #         response_schema=LLMClassificationResponse
            #     )
            # )

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an autonomous CRM agent..."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"} # <-- CHANGED THIS LINE
            )

            output_text = response.choices[0].message.content
            
            # Parse response text back into the system validation schema
            # data = json.loads(response.text)
            data = json.loads(output_text)

            
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
            print(f"CRITICAL PIPELINE ERROR: {str(e)}")
            
            # THE INDESTRUCTIBLE FALLBACK SHIELD
            body_lower = email_body.lower()
            spam_triggers = ["attendee list", "offshore", "seo", "backlink", "guest post", "placement fee", "lead gen", "decision-makers", "synergy"]
            
            if any(trigger in body_lower for trigger in spam_triggers):
                return LLMClassificationResponse(
                    category="Spam",
                    sentiment="Neutral",
                    sentiment_score=0.0,
                    urgency="Low",
                    requires_human=False,
                    escalation_reason="Auto-filtered by emergency fallback trap.",
                    suggested_reply=None,  # <--- ADDED THIS
                    confidence=1.0,
                    detected_entities={"order_ids": [], "ticket_ids": [], "monetary_amounts": [], "deadlines": [], "products_mentioned": []}
                )

            # Standard Resilient Fallback (for non-spam crashes)
            return LLMClassificationResponse(
                category="Inquiry",
                sentiment="Neutral",
                sentiment_score=0.0,
                urgency="Medium",
                requires_human=True,
                escalation_reason=f"Classification pipeline error fallback: {str(e)}",
                suggested_reply=None,  # <--- ADDED THIS
                confidence=0.5,
                detected_entities={"order_ids": [], "ticket_ids": [], "monetary_amounts": [], "deadlines": [], "products_mentioned": []}
            )