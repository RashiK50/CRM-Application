from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from backend.models import Contact, Thread
from typing import Dict, Any

router = APIRouter(prefix="/api/contacts", tags=["Contact Management"])

class StatusUpdateSchema(BaseModel):
    status: str # VIP | Blocked | Active | Churned

@router.get("/{email}")
def get_contact_profile(email: str, db: Session = Depends(get_db)):
    """Retrieves a customer's CRM history, lifetime value, and churn risk metrics."""
    contact = db.query(Contact).filter(Contact.email == email).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No contact profile found for email: {email}"
        )
        
    # Count open support tracks belonging to this customer
    open_threads = db.query(Thread).filter(
        Thread.sender_email == email, 
        Thread.status == "Open"
    ).count()

    return {
        "id": contact.id,
        "email": contact.email,
        "name": contact.name,
        "company": contact.company,
        "status": contact.status,
        "account_value": float(contact.account_value),
        "churn_risk_score": contact.churn_risk_score,
        "open_threads_count": open_threads,
        "last_contact_at": contact.last_contact_at.isoformat()
    }

@router.patch("/{email}/status")
def update_contact_status(email: str, payload: StatusUpdateSchema, db: Session = Depends(get_db)):
    """Manually changes a user's status lifecycle category within the core ledger."""
    contact = db.query(Contact).filter(Contact.email == email).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No contact profile found for email: {email}"
        )

    valid_statuses = ["VIP", "Blocked", "Active", "Churned"]
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status value. Must be one of: {valid_statuses}"
        )

    contact.status = payload.status
    db.commit()
    return {"message": "Contact status updated successfully.", "email": email, "new_status": contact.status}