from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import datetime

from backend.database import get_db
from backend.models import Email, Thread, Contact
from backend.schemas import EmailIngestSchema
from backend.services.heuristic import HeuristicFilterService
from backend.services.orchestrator import orchestrator

router = APIRouter(prefix="/api", tags=["Ingestion"])
heuristic_service = HeuristicFilterService()

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
def ingest_email(
    payload: EmailIngestSchema, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    # 1. Enforce Absolute Idempotency (Prevents Duplicate Disqualifications)
    existing_email = db.query(Email).filter(Email.message_id == payload.message_id).first()
    if existing_email:
        return {
            "message": "Duplicate message intercepted.",
            "job_id": f"job_dup_{payload.message_id}",
            "email_id": existing_email.id,
            "status": existing_email.status
        }

    # 2. Get or Create Contact Profile
    contact = db.query(Contact).filter(Contact.email == payload.sender).first()
    if not contact:
        contact = Contact(
            email=payload.sender,
            name=payload.sender.split("@")[0].title(),
            company=payload.sender.split("@")[-1].split(".")[0].title()
        )
        db.add(contact)
        db.flush()

    # 3. Handle Conversational Thread Linking
    thread = db.query(Thread).filter(Thread.thread_id == payload.thread_id).first()
    if not thread:
        thread = Thread(
            thread_id=payload.thread_id,
            subject=payload.subject,
            sender_email=payload.sender,
            status="Open"
        )
        db.add(thread)
        db.flush()
    else:
        thread.last_updated_at = datetime.datetime.utcnow()

    # 4. Run Instant Synchronous Layer 1 Heuristic Filter
    triage = heuristic_service.analyze_email(
        sender=payload.sender, 
        subject=payload.subject, 
        body=payload.body
    )

    # 5. Persist Email Record
    new_email = Email(
        thread_id=thread.thread_id,
        message_id=payload.message_id,
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        timestamp=payload.timestamp,
        urgency=triage["urgency"],
        status=triage["initial_status"],
        requires_human=triage["requires_human"],
        confidence=1.0 if triage["is_spam"] or triage["is_security_threat"] else 0.5,
        category="Spam" if triage["is_spam"] else "Other"
    )
    
    # Cascade status to parent thread
    if triage["initial_status"] in ["Escalated", "Ignored"]:
        thread.status = triage["initial_status"]

    db.add(new_email)
    db.commit()
    db.refresh(new_email)

    # 6. Async Layer 2 Agent Loop Hand-off
    if triage["initial_status"] != "Ignored":  # Skip executing LLMs/RAG for confirmed spam
        background_tasks.add_task(orchestrator.process_email_lifecycle, new_email.id)

    return {
        "message": "Email ingested successfully. Processing started in background.",
        "job_id": f"job_proc_{new_email.message_id}",
        "email_id": new_email.id,
        "triage_verdict": triage
    }

@router.get("/status/{job_id}")
def get_processing_status(job_id: str, db: Session = Depends(get_db)):
    msg_id = job_id.replace("job_proc_", "").replace("job_dup_", "")
    target_email = db.query(Email).filter(Email.message_id == msg_id).first()
    if not target_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Processing token not found."
        )
    return {
        "job_id": job_id,
        "email_id": target_email.id,
        "status": target_email.status,
        "urgency": target_email.urgency,
        "category": target_email.category
    }