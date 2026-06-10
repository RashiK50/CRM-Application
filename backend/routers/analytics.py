from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Email
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/analytics", tags=["Analytics Insights"])

@router.get("/sentiment-trend")
def get_sentiment_trend(
    sender: Optional[str] = Query(None, description="Filter trend lines for a specific sender account"),
    db: Session = Depends(get_db)
):
    """Retrieves chronologically sorted data streams reflecting user sentiment tracking values."""
    query = db.query(Email.timestamp, Email.sentiment_score)
    
    if sender:
        query = query.filter(Email.sender == sender)
        
    results = query.order_by(Email.timestamp.asc()).all()
    
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "sentiment_score": round(r.sentiment_score, 2)
        } for r in results
    ]

@router.get("/category-breakdown")
def get_category_breakdown(db: Session = Depends(get_db)):
    """Computes distribution frequencies across identified system classification headers."""
    results = (
        db.query(Email.category, func.count(Email.id))
        .group_by(Email.category)
        .all()
    )
    
    return [
        {
            "category": r[0] or "Unclassified",
            "count": r[1]
        } for r in results
    ]