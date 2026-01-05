
import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.crud.currency import initialize_default_currencies
from app.models.user import User

def fix():
    print("Starting currency fix...")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            print(f"Initializing for user: {user.email}")
            initialize_default_currencies(db, user.id)
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix()
