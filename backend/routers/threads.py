from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from backend.models import Email, Thread, Action
from typing import List, Dict, Any
from collections import defaultdict

router = APIRouter(prefix="/api/threads", tags=["Threads Workspace"])

# ==========================================
# 1. NEW GLOBAL INBOX ROUTE (MUST BE FIRST)
# ==========================================
@router.get("/global/recent", response_model=List[Dict[str, Any]])
def get_recent_global_threads(db: Session = Depends(get_db)):
    """Fetches the 50 most recent active threads across ALL customers for the inbox view."""
    
    # Grab the last 100 emails across the whole database
    emails = db.query(Email).order_by(Email.timestamp.desc()).limit(100).all()
    if not emails:
        return []

    # Sort ascending so the chat history reads top-to-bottom properly
    emails_asc = sorted(emails, key=lambda x: x.timestamp)
    
    threads_dict = defaultdict(list)
    for email in emails_asc:
        action = db.query(Action).filter(Action.email_id == email.id).first()
        threads_dict[email.thread_id].append({
            "id": email.id,
            "message_id": email.message_id,
            "subject": email.subject,
            "sender": email.sender, # Important for global view
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
    for thread_id, email_list in threads_dict.items():
        thread_meta = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        response_payload.append({
            "thread_id": thread_id,
            "subject": thread_meta.subject if thread_meta else email_list[0]["subject"],
            "status": thread_meta.status if thread_meta else email_list[-1]["status"],
            "assigned_to": thread_meta.assigned_to if thread_meta else "AI_Agent",
            "last_updated_at": thread_meta.last_updated_at if thread_meta else email_list[-1]["timestamp"],
            "customer_email": email_list[0]["sender"], # Attach sender to the top level
            "emails": email_list
        })

    # Sort so the newest threads are at the very top of your left pane
    response_payload.sort(key=lambda x: x["last_updated_at"], reverse=True)
    return response_payload[:50]


# ==========================================
# 2. EXISTING SPECIFIC SEARCH ROUTE
# ==========================================
@router.get("/{contact_email}", response_model=List[Dict[str, Any]])
def get_contact_threads(contact_email: str, db: Session = Depends(get_db)):
    """Fetches full conversation threads for a specific customer email."""
    
    emails = db.query(Email).filter(Email.sender == contact_email).order_by(Email.timestamp.asc()).all()
    
    if not emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No conversational logs found for contact: {contact_email}"
        )

    threads_dict = defaultdict(list)
    for email in emails:
        action = db.query(Action).filter(Action.email_id == email.id).first()
        threads_dict[email.thread_id].append({
            "id": email.id,
            "message_id": email.message_id,
            "subject": email.subject,
            "sender": email.sender, # Added sender here too
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
    for thread_id, email_list in threads_dict.items():
        thread_meta = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        response_payload.append({
            "thread_id": thread_id,
            "subject": thread_meta.subject if thread_meta else email_list[0]["subject"],
            "status": thread_meta.status if thread_meta else email_list[-1]["status"],
            "assigned_to": thread_meta.assigned_to if thread_meta else "AI_Agent",
            "last_updated_at": thread_meta.last_updated_at if thread_meta else email_list[-1]["timestamp"],
            "customer_email": email_list[0]["sender"],
            "emails": email_list
        })

    return response_payload