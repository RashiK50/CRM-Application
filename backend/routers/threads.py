from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from backend.models import Email, Thread, Action
from typing import List, Dict, Any
from collections import defaultdict

router = APIRouter(prefix="/api/threads", tags=["Threads Workspace"])

@router.get("/{contact_email}", response_model=List[Dict[str, Any]])
def get_contact_threads(contact_email: str, db: Session = Depends(get_db)):
    """Fetches full conversation threads for a customer email, including execution logs."""
    
    # 1. THE FIX: Query the Email table directly. This guarantees we find the spam/escalated messages.
    emails = db.query(Email).filter(Email.sender == contact_email).order_by(Email.timestamp.asc()).all()
    
    if not emails:
        # Only throw a 404 if literally no emails exist for this sender
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No conversational logs found for contact: {contact_email}"
        )

    # 2. Group all found emails by their thread_id
    threads_dict = defaultdict(list)
    for email in emails:
        # Pull historical agent reasoning execution runs
        action = db.query(Action).filter(Action.email_id == email.id).first()
        
        threads_dict[email.thread_id].append({
            "id": email.id,
            "message_id": email.message_id,
            "subject": email.subject,
            "body": email.body,
            "timestamp": email.timestamp,
            "sentiment_score": email.sentiment_score,
            "category": email.category,
            "urgency": email.urgency,
            "status": email.status,
            "agent_trace": action.agent_reasoning_log if action else None,
            "proposed_draft": action.proposed_content if action else None
        })

    response_payload = []
    
    # 3. Gracefully build the payload format your React frontend expects
    for thread_id, email_list in threads_dict.items():
        # Try to fetch the formal Thread metadata (might not exist for Spam)
        thread_meta = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        
        response_payload.append({
            "thread_id": thread_id,
            # If thread_meta is missing, fallback safely to the email's data
            "subject": thread_meta.subject if thread_meta else email_list[0]["subject"],
            "status": thread_meta.status if thread_meta else email_list[-1]["status"],
            "assigned_to": thread_meta.assigned_to if thread_meta else "AI_Agent",
            "last_updated_at": thread_meta.last_updated_at if thread_meta else email_list[-1]["timestamp"],
            "emails": email_list
        })

    return response_payload