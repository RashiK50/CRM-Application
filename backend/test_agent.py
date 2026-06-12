import os
import sys
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base, SessionLocal
from backend.models import Email, Thread, Contact
from backend.services.agent import AutonomousAgentService

# Build isolated tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()
agent = AutonomousAgentService()

# Ingest an urgent incident context record [cite: 136-137]
contact = Contact(email="bob.jones@enterprise.net", name="Bob", account_value=12000.00)
thread = Thread(thread_id="thread_bob_outage", subject="Outage Incident", sender_email=contact.email)
email = Email(
    thread_id="thread_bob_outage",
    message_id="msg_bob_060",
    sender=contact.email,
    body="SLA Breach Notice. Our legal team is now involved. Fix this.",
    timestamp=datetime.datetime.utcnow(),
    urgency="Critical",
    status="Received"
)
db.add_all([contact, thread, email])
db.commit()

# Execute graph triage operations
result = agent.execute_triage(email_id=email.id, dry_run=False)

print("Agent Routing Result Status:", result["status"])
print("Generated Reasoning Paths Trace Steps:")
for step in result["reasoning_trace"]:
    print(" -", step)

# Verify constraints pass technical evaluation bounds [cite: 133, 229]
assert result["status"] == "Escalated"
print("Agent Verification Testing Phase Passed successfully!")
db.close()