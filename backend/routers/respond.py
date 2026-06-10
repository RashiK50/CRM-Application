import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Email, Thread, Action, AuditLog

router = APIRouter(prefix="/api", tags=["Response Operations"])

class DraftUpdateSchema(BaseModel):
    proposed_content: str

@router.patch("/drafts/{action_id}")
def edit_proposed_draft(action_id: int, payload: DraftUpdateSchema, db: Session = Depends(get_db)):
    """Edits a proposed AI reply draft before manual approval[cite: 184]."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target draft action not found.")
    
    action.proposed_content = payload.proposed_content
    db.commit()
    return {"message": "Draft updated successfully.", "action_id": action.id}

@router.post("/drafts/{action_id}/approve")
def approve_and_send_draft(action_id: int, db: Session = Depends(get_db)):
    """Approves a draft, updates the lifecycle state, and logs an entry in the audit trail[cite: 184]."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target draft action not found.")

    # 1. Update verification state metrics
    action.is_approved = True
    action.approved_by = "Human_Operator"
    action.executed_at = datetime.datetime.utcnow()

    # 2. Transition parent email status to Replied
    email = db.query(Email).filter(Email.id == action.email_id).first()
    if email:
        email.status = "Replied"
        thread = db.query(Thread).filter(Thread.thread_id == email.thread_id).first()
        if thread:
            thread.status = "Resolved"

    # 3. Create mandatory system Audit Log [cite: 178-179, 184]
    audit = AuditLog(
        entity_type="Action",
        entity_id=str(action.id),
        action="Approve & Send Draft",
        performed_by="Human_Operator",
        diff={"final_content": action.proposed_content}
    )
    db.add(audit)
    db.commit()

    return {"message": "Draft approved and mock transmission executed successfully."}