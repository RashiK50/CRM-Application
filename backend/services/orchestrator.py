import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from backend.services.agent import AutonomousAgentService
from backend.services.sentiment import SentimentTrackerService
from backend.models import Email

# Setup runtime logging diagnostics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SystemOrchestrator")

class WorkflowOrchestrator:
    def __init__(self):
        self.agent_service = AutonomousAgentService()
        self.sentiment_service = SentimentTrackerService()

    def process_email_lifecycle(self, email_id: int):
        """
        Executes background agent triage and calculation metrics.
        Runs downstream deep analysis after Layer 1 ingestion confirmation.
        """
        db: Session = SessionLocal()
        logger.info(f"Starting async processing track for Email Node ID: {email_id}")
        
        try:
            # 1. Fetch targeted tracking node
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                logger.error(f"Aborting execution: Email ID {email_id} vanished from persistence ledger.")
                return

            # Update state to prevent race-condition re-entries
            email.status = "Processing"
            db.commit()

            # 2. Invoke the multi-turn agent engine loop (Layer 2 + RAG Grounding)
            logger.info(f"Invoking autonomous agent engine for email {email_id}...")
            agent_result = self.agent_service.execute_triage(email_id=email_id, dry_run=False)
            
            # Refresh data frame references after agent mutations
            db.refresh(email)

            # 3. Compute structural sentiment alerts and account health updates
            logger.info(f"Analyzing user historical sentiment profiles for sender: {email.sender}")
            sentiment_metrics = self.sentiment_service.process_and_check_alerts(db, email.sender)
            
            # Commit processing modifications to database
            db.commit()
            logger.info(f"Successfully processed email {email_id}. Final Triage Status: {agent_result.get('status')}")

        except Exception as e:
            db.rollback()
            logger.error(f"Critical workflow crash on Email ID {email_id}: {str(e)}", exc_info=True)
            
            # Fallback to safe state to allow manual intervention
            try:
                email = db.query(Email).filter(Email.id == email_id).first()
                if email:
                    email.status = "Failed"
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

# Singleton instance for simple app import sharing
orchestrator = WorkflowOrchestrator()