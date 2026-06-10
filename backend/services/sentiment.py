from sqlalchemy.orm import Session
from backend.models import Email, Thread, Contact
from typing import Dict, Any, List

class SentimentTrackerService:
    def __init__(self, negative_threshold: float = -0.2):
        self.negative_threshold = negative_threshold

    def process_and_check_alerts(self, db: Session, sender_email: str) -> Dict[str, Any]:
        """
        Calculates moving sentiment trends and triggers alerts if 
        3 consecutive negative emails are detected from the same sender.
        """
        # Fetch the last 5 emails from this sender ordered by timestamp descending
        historical_emails = (
            db.query(Email)
            .filter(Email.sender == sender_email)
            .order_by(Email.timestamp.desc())
            .limit(5)
            .all()
        )

        if not historical_emails:
            return {"moving_average": 0.0, "deterioration_alert": False}

        # Calculate basic moving average score
        total_score = sum(e.sentiment_score for e in historical_emails)
        moving_avg = total_score / len(historical_emails)

        # Update contact profile with the calculated health metrics
        contact = db.query(Contact).filter(Contact.email == sender_email).first()
        if contact:
            contact.churn_risk_score = min(max(0.0, (1.0 - moving_avg) / 2,0), 1.0)
            db.flush()

        # Check for 3 consecutive negative emails (Deterioration Alert Rule)
        consecutive_negative_count = 0
        for email in historical_emails:
            if email.sentiment_score <= self.negative_threshold:
                consecutive_negative_count += 1
                if consecutive_negative_count >= 3:
                    # Escalation trigger condition satisfied
                    self._escalate_contact_threads(db, sender_email)
                    return {"moving_average": moving_avg, "deterioration_alert": True}
            else:
                # Sequence broken because emails are sorted chronologically descending
                break

        return {"moving_average": moving_avg, "deterioration_alert": False}

    def _escalate_contact_threads(self, db: Session, sender_email: str):
        """Escalates all open threads belonging to a deteriorating account."""
        open_threads = (
            db.query(Thread)
            .filter(Thread.sender_email == sender_email, Thread.status == "Open")
            .all()
        )
        for thread in open_threads:
            thread.status = "Escalated"