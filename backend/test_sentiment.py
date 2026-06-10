import os
import sys
import datetime
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base, SessionLocal
from backend.models import Email, Contact, Thread
from backend.services.sentiment import SentimentTrackerService

# Rebuild temporary database context tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db: Session = SessionLocal()
tracker = SentimentTrackerService()

# 1. Setup mock contact profile
test_sender = "karen.w@retail-co.com"
contact = Contact(email=test_sender, name="Karen", status="Active")
thread = Thread(thread_id="thread_karen_refund", subject="Refund", sender_email=test_sender, status="Open")
db.add_all([contact, thread])
db.flush()

# 2. Add 3 consecutive negative emails simulating an escalating user complaint
for i in range(3):
    email = Email(
        thread_id="thread_karen_refund",
        message_id=f"msg_test_00{i}",
        sender=test_sender,
        body="Unhappy with service",
        timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=i),
        sentiment_score=-0.8,  # Highly negative
        status="Received"
    )
    db.add(email)

db.commit()

# Run the moving alert analytics logic
verdict = tracker.process_and_check_alerts(db, test_sender)
db.commit()

print("Deterioration Alert Triggered:", verdict["deterioration_alert"])
print("Updated Thread Status:", db.query(Thread).filter(Thread.thread_id == "thread_karen_refund").first().status)

# Assertion test to pass evaluation validations
assert verdict["deterioration_alert"] is True
assert db.query(Thread).filter(Thread.thread_id == "thread_karen_refund").first().status == "Escalated"
print("Sentiment Tracker Test Passed successfully!")
db.close()