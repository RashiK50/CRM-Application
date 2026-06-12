from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from backend.models import AuditLog
from typing import List, Dict, Any

router = APIRouter(prefix="/api/audit", tags=["Compliance Audit"])

@router.get("/{entity_type}/{entity_id}", response_model=List[Dict[str, Any]])
def get_entity_audit_history(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the chronological audit transaction trail for any specific system entity.
    """
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    
    if not logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit log records found for {entity_type} ID: {entity_id}"
        )

    return [
        {
            "id": log.id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "performed_by": log.performed_by,
            "timestamp": log.timestamp.isoformat(),
            "diff": log.diff
        } for log in logs
    ]