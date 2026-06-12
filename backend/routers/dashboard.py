from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database import get_db
from backend.models import Email
from typing import Dict, Any

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Metrics"])

@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes top-level operational metrics using strict, mutually exclusive bucketing."""
    
    # 1. PENDING (Items waiting for AI processing)
    pending_count = db.query(Email).filter(Email.status.in_(["Received", "Processing", "Pending"])).count()
    
    # 2. AUTO REPLIED (AI handled it entirely)
    replied_count = db.query(Email).filter(Email.status.in_(["Auto-Replied", "Replied"])).count()
    
    # 3. HUMAN RESOLVED (Operator clicked Commit & Transmit)
    resolved_count = db.query(Email).filter(Email.status == "Resolved").count()
    
    # 4. CRITICAL THREATS (Needs human AND is a severe threat)
    critical_count = db.query(Email).filter(
        Email.status == "Escalated",
        Email.urgency == "Critical"
    ).count()
    
    # 5. STANDARD ESCALATIONS (Needs human, but just a normal request)
    escalated_count = db.query(Email).filter(
        Email.status == "Escalated",
        or_(Email.urgency != "Critical", Email.urgency.is_(None))
    ).count()
    
    # 6. SPAM INTERCEPTED (Traffic cop killed it)
    spam_count = db.query(Email).filter(Email.status.in_(["Ignored", "Spam"])).count()

    return {
        "pending": pending_count,
        "replied": replied_count,
        "resolved": resolved_count,
        "escalated": escalated_count,
        "critical": critical_count,
        "spam_filtered": spam_count
    }