import os
import sys
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from database import engine, Base, SessionLocal, get_db
from backend.models import Email, Thread, Contact

# Dependency override
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Build isolated tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Add test data
now = datetime.datetime.now(datetime.UTC)
contact = Contact(email="test@example.com", name="Test", account_value=100.0)
thread = Thread(thread_id="thread_test_1", subject="Test", sender_email=contact.email)

# 1 Pending (Received)
e1 = Email(thread_id="thread_test_1", message_id="m1", sender=contact.email, body="b1", timestamp=now, urgency="Normal", status="Received")
# 1 Pending (Processing)
e2 = Email(thread_id="thread_test_1", message_id="m2", sender=contact.email, body="b2", timestamp=now, urgency="Normal", status="Processing")
# 1 Replied
e3 = Email(thread_id="thread_test_1", message_id="m3", sender=contact.email, body="b3", timestamp=now, urgency="Normal", status="Replied")
# 2 Escalated
e4 = Email(thread_id="thread_test_1", message_id="m4", sender=contact.email, body="b4", timestamp=now, urgency="Normal", status="Escalated")
e5 = Email(thread_id="thread_test_1", message_id="m5", sender=contact.email, body="b5", timestamp=now, urgency="Critical", status="Escalated")
# 1 Critical (Also Escalated above, plus this one)
e6 = Email(thread_id="thread_test_1", message_id="m6", sender=contact.email, body="b6", timestamp=now, urgency="Critical", status="Replied")
# 1 Spam Filtered (Ignored)
e7 = Email(thread_id="thread_test_1", message_id="m7", sender=contact.email, body="b7", timestamp=now, urgency="Low", status="Ignored")

db.add_all([contact, thread, e1, e2, e3, e4, e5, e6, e7])
db.commit()
db.close()

client = TestClient(app)

response = client.get("/api/dashboard/stats")
assert response.status_code == 200

data = response.json()
print("Dashboard Stats:", data)

assert data["pending"] == 2
assert data["replied"] == 2
assert data["escalated"] == 2
assert data["critical"] == 2
assert data["spam_filtered"] == 1

print("Dashboard Verification Testing Phase Passed successfully!")
