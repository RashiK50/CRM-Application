import os
import sys

# Dynamic path helper to inject the root directory into Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.llm_classifier import LLMClassifierService

# Ensure valid environment key profile is set
os.environ["GEMINI_API_KEY"] = "your-actual-api-key-here"

classifier = LLMClassifierService()
sample_body = "Our production server is not responding since 08:50 UTC. We are losing approximately $10,000/minute. We need support immediately. This is a P0 incident."

result = classifier.classify_email(email_body=sample_body)

print("Category Verdict:", result.category)
print("Urgency Level:", result.urgency)
print("Extracted Entities:", result.detected_entities.model_dump())

assert result.urgency in ["Critical", "High", "Medium", "Low"]
print("Test Passed successfully!")