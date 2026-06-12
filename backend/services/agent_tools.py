from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import Email, Contact
import asyncio
from backend.services.web_scraper import WebIntelligenceService

web_scraper = WebIntelligenceService()

class AgentTools:
    
    @staticmethod
    def scrape_public_sentiment(company_name: str) -> str:
        """Unified web intelligence: checks review sites and social listening."""
        return asyncio.run(web_scraper.get_web_intelligence(company_name))
    
    @staticmethod
    def get_thread_history(db: Session, thread_id: str) -> List[Dict[str, str]]:
        """Retrieves previous turns in the conversation."""
        emails = db.query(Email).filter(Email.thread_id == thread_id).order_by(Email.timestamp.asc()).all()
        return [{"sender": e.sender, "body": e.body} for e in emails[:-1]]

    @staticmethod
    def check_crm_profile(db: Session, email: str) -> Dict[str, Any]:
        """Fetches internal customer tiers and current health risk profiles."""
        contact = db.query(Contact).filter(Contact.email == email).first()
        if contact:
            return {"status": contact.status, "value": float(contact.account_value), "risk": contact.churn_risk_score}
        return {"status": "Active", "value": 0.00, "risk": 0.0}