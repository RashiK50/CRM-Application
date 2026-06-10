from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Email, Thread, Action
from typing import List, Dict, Any

router = APIRouter(prefix="/api/threads", tags=["Threads Workspace"])

@router.get("/{contact_email}", response_model=List[Dict[str, Any]])
def get_contact_threads(contact_email: str, db: Session = Depends(get_db)):
    """Fetches full conversation threads for a customer email, including execution logs."""
    # 1. Retrieve all threads linked to the sender domain [cite: 181]
    threads = db.query(Thread).filter(Thread.sender_email == contact_email).all()
    if not threads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No conversational logs found for contact: {contact_email}"
        )

    response_payload = []

    for thread in threads:
        # 2. Fetch all emails associated with this thread timeline [cite: 181]
        emails = (
            db.query(Email)
            .filter(Email.thread_id == thread.thread_id)
            .order_by(Email.timestamp.asc())
            .all()
        )

        email_list = []
        for email in emails:
            # 3. Pull historical agent reasoning execution runs 
            action = db.query(Action).filter(Action.email_id == email.id).first()
            
            email_list.append({
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

        response_payload.append({
            "thread_id": thread.thread_id,
            "subject": thread.subject,
            "status": thread.status,
            "assigned_to": thread.assigned_to,
            "last_updated_at": thread.last_updated_at,
            "emails": email_list
        })

    return response_payload