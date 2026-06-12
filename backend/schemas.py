from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import List, Optional

class EmailIngestSchema(BaseModel):
    """Structural validator for incoming email payloads."""
    message_id: str
    sender: str  # Keeps compatibility open for variant string inputs
    subject: str
    body: str
    timestamp: datetime
    thread_id: str

    @field_validator('body', 'subject')
    @classmethod
    def reject_whitespace_only(cls, v: str) -> str:
        """Handles empty body/subject or whitespace-only edge cases."""
        if not v or v.strip() == "":
            raise ValueError("Field cannot be empty or contain only whitespace.")
        return v

class EntityExtractionSchema(BaseModel):
    """Named entities requested by the assessment specifications."""
    order_ids: List[str]
    ticket_ids: List[str]
    monetary_amounts: List[str]
    deadlines: List[str]
    products_mentioned: List[str]

class LLMClassificationResponse(BaseModel):
    """Enforces the precise JSON schema required for Layer 2 classification."""
    category: str  
    sentiment: str  
    sentiment_score: float 
    urgency: str  
    requires_human: bool
    escalation_reason: Optional[str]
    suggested_reply: Optional[str]
    confidence: float
    detected_entities: EntityExtractionSchema