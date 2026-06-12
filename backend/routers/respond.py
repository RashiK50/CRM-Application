import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from backend.models import Email, Thread, Action, AuditLog

# 1. Updated prefix to match the React frontend's fetch URL perfectly
router = APIRouter(prefix="/api/respond", tags=["Response Operations"])

# 2. Added the payload schema to catch the text from the React sandbox editor
class ApprovalPayload(BaseModel):
    final_reply: str

@router.post("/approve/{email_id}")
def approve_and_send_draft(email_id: int, payload: ApprovalPayload, db: Session = Depends(get_db)):
    """Approves a draft, updates the lifecycle state, and logs an entry in the audit trail."""
    
    # Fetch the target email using the ID passed from the frontend button click
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target email not found.")

    # 1. Transition parent email status to Replied and save the edited text
    email.status = "Resolved"
    email.proposed_draft = payload.final_reply 
    
    # 2. Resolve the parent Thread
    thread = db.query(Thread).filter(Thread.thread_id == email.thread_id).first()
    if thread:
        thread.status = "Resolved"

    # 3. Update the associated Action verification state (if the orchestrator created one)
    action = db.query(Action).filter(Action.email_id == email_id).first()
    if action:
        action.is_approved = True
        action.approved_by = "Human_Operator"
        action.executed_at = datetime.datetime.utcnow()
        action.proposed_content = payload.final_reply

    # 4. Create mandatory system Audit Log based on your original compliance logic
    audit = AuditLog(
        entity_type="Email/Action",
        entity_id=str(email.id),
        action="Approve & Send Draft",
        performed_by="Human_Operator",
        diff={"final_content": payload.final_reply}
    )
    db.add(audit)
    
    # Commit all state changes, thread updates, and audit logs in one transaction
    db.commit()

    # 5. Return the exact success dictionary the React app is looking for
    return {"status": "success", "message": "Draft approved and mock transmission executed successfully."}