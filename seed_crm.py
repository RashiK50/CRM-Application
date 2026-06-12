import sys
import os

# Ensure Python can find your 'backend' module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal

# ⚠️ IMPORTANT: Change 'Customer' to whatever your actual database model is named!
# It might be 'User', 'Profile', 'Client', etc. Look inside backend/models.py to be sure.
from backend.models import Contact

def update_ceo_profile():
    db = SessionLocal()
    target_email = "ceo@startup-launch.com"
    
    try:
        print(f"🔍 Searching database for {target_email}...")
        
        # 1. Query the database
        user = db.query(Contact).filter(Contact.email == target_email).first()
        
        if user:
            print("👤 User found! Pushing new VIP values...")
            # ⚠️ IMPORTANT: Check your model to ensure these column names match 
            # (e.g., 'value' vs 'lifetime_value', 'risk' vs 'churn_risk')
            user.status = "VIP"
            user.value = 45000.00
            user.risk = 0.85
        else:
            print("👤 User not found. Creating brand new profile...")
            user = Customer(
                email=target_email,
                name="Startup CEO",
                status="VIP",
                value=45000.00,
                risk=0.85
            )
            db.add(user)
            
        # 2. Push and save the transaction
        db.commit()
        
        # Verify the push worked
        db.refresh(user)
        print(f"✅ SUCCESS! Database locked. Account Value is now: ${user.value}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR: Database push failed: {str(e)}")
        print("Did you make sure your column names match your models.py file?")
    finally:
        db.close()

if __name__ == "__main__":
    update_ceo_profile()