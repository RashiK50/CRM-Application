from fastapi import APIRouter, Depends, HTTPException, status
from backend.services.agent import AutonomousAgentService
from typing import Dict, Any

router = APIRouter(prefix="/api/agent", tags=["Agent Operations"])
agent_service = AutonomousAgentService()

@router.post("/dry-run/{email_id}", response_model=Dict[str, Any])
def run_agent_dry_run(email_id: int):
    """
    Executes the multi-step agent pipeline in dry-run planning mode.
    Returns the full reasoning trace and proposed actions without modifying database records.
    """
    try:
        result = agent_service.execute_triage(email_id=email_id, dry_run=True)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent runtime loop execution failure: {str(e)}"
        )