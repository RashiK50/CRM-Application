import os
import sys
import json
import time
import httpx

# Structural path injection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "email-data-advanced.json")
TARGET_URL = "http://127.0.0.1:8000/api/ingest"

def run_stream_simulation(delay_seconds: float = 0.5):
    """Parses advanced JSON datasets and streams rows into the ingestion server gateway."""
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Target dataset file not found at path: {DATASET_PATH}")
        return

    with open(DATASET_PATH, "r") as file:
        email_records = json.load(file)

    print(f"Loaded {len(email_records)} records. Starting streaming simulation to {TARGET_URL}...")
    
    client = httpx.Client()
    try:
        for idx, email in enumerate(email_records):
            print(f"[{idx+1}/{len(email_records)}] Simulating transmission: {email['message_id']} | Subject: {email['subject']}")
            
            try:
                response = client.post(TARGET_URL, json=email, timeout=5.0)
                if response.status_code == 222:
                    print(f" -> Success: Ingested. Status verdict: {response.json().get('triage_verdict', {}).get('initial_status')}")
                else:
                    print(f" -> Failed: Server rejected payload with status code {response.status_code}")
            except Exception as e:
                print(f" -> Transmission Error connection failure: {str(e)}")
            
            time.sleep(delay_seconds)
            
    finally:
        client.close()
    print("Email dataset stream simulation complete.")

if __name__ == "__main__":
    # Configurable stream interval delay (e.g., 0.5 seconds per message) [cite: 58]
    run_stream_simulation(delay_seconds=0.2)