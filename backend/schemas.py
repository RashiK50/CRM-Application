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
    order_ids: List[str] = []
    ticket_ids: List[str] = []
    monetary_amounts: List[str] = []
    deadlines: List[str] = []
    products_mentioned: List[str] = []

class LLMClassificationResponse(BaseModel):
    """Enforces the precise JSON schema required for Layer 2 classification."""
    category: str  # Complaint | Inquiry | Bug Report | Feature Request | Compliance | Legal | Billing | Spam | Internal | Other
    sentiment: str  # Positive | Neutral | Negative | Mixed
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    urgency: str  # Critical | High | Medium | Low
    requires_human: bool
    escalation_reason: Optional[str] = None
    suggested_reply: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected_entities: EntityExtractionSchema