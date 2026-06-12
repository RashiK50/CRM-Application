from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from backend.models import Email
from typing import Dict, Any

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Metrics"])

@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes top-level operational metrics across all ingested messages."""
    
    # Run an optimized single-pass query grouping by status
    status_counts = (
        db.query(Email.status, func.count(Email.id))
        .group_by(Email.status)
        .all()
    )
    counts_dict = {status: count for status, count in status_counts}

    # Extract Critical priority counts across all items [cite: 82]
    critical_count = (
        db.query(func.count(Email.id))
        .filter(Email.urgency == "Critical")
        .scalar() or 0
    )

    return {
        # Add "Pending" to the calculation!
        "pending": counts_dict.get("Received", 0) + counts_dict.get("Processing", 0) + counts_dict.get("Pending", 0),
        "replied": counts_dict.get("Replied", 0),
        "escalated": counts_dict.get("Escalated", 0),
        "critical": critical_count,
        "spam_filtered": counts_dict.get("Ignored", 0)
    }