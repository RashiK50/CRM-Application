import re
from typing import Dict, Any

class HeuristicFilterService:
    def __init__(self):
        self.urgency_keywords = re.compile(
            r'(urgent|p0|immediate|action required|critical|deadline|asap)', 
            re.IGNORECASE
        )
        self.security_keywords = re.compile(
            r'(ransomware|2 btc|wallet|exfiltrated|suspicious login|pyongyang|hack)', 
            re.IGNORECASE
        )
        self.legal_keywords = re.compile(
            r'(cease and desist|legal action|trademark|gdpr|article 20|lawsuit)', 
            re.IGNORECASE
        )
        self.spam_keywords = re.compile(
            r'(boost your seo|front page of google|inheritance|\$50,000,000|nigeria|click here to claim)', 
            re.IGNORECASE
        )
        self.internal_domains = ["@internal.com", "@mycompany.com"]

    def analyze_email(self, sender: str, subject: str, body: str) -> Dict[str, Any]:
        """Performs structural evaluation over raw text arrays."""
        combined_text = f"{subject} {body}"
        
        is_internal = any(domain in sender.lower() for domain in self.internal_domains)
        is_security = bool(self.security_keywords.search(combined_text))
        is_spam = bool(self.spam_keywords.search(combined_text))
        is_legal = bool(self.legal_keywords.search(combined_text))
        
        # Urgency Calibration
        urgency = "Low"
        if is_security or is_legal or "p0" in combined_text.lower():
            urgency = "Critical"
        elif self.urgency_keywords.search(combined_text):
            urgency = "High"
        elif is_internal:
            urgency = "Medium"
            
        # Initial status mapping
        status = "Received"
        if is_spam:
            status = "Ignored"
        elif is_security or is_legal:
            status = "Escalated"

        return {
            "is_internal": is_internal,
            "is_security_threat": is_security,
            "is_legal_threat": is_legal,
            "is_spam": is_spam,
            "urgency": urgency,
            "initial_status": status,
            "requires_human": is_security or is_legal or is_internal
        }