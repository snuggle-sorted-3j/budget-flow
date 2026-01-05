import sys
import os

# Add the current directory to sys.path to import app
sys.path.append(os.path.join(os.getcwd(), "app"))
# Also add the root app directory
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.database import engine, Base
from app.core.config import settings

def migrate():
    print(f"Connecting to database at {settings.DATABASE_URL.split('@')[-1]}")
    with engine.connect() as conn:
        print("Checking for opening_balance column in accounts table...")
        
        # Check if column exists
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='accounts' AND column_name='opening_balance'"))
        if not result.fetchone():
            print("Adding opening_balance column...")
            conn.execute(text("ALTER TABLE accounts ADD COLUMN opening_balance DECIMAL(15,2) DEFAULT 0 NOT NULL"))
            conn.commit()
            print("Added opening_balance.")
        else:
            print("opening_balance column already exists.")
            
        print("Checking for opening_balance_date column in accounts table...")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='accounts' AND column_name='opening_balance_date'"))
        if not result.fetchone():
            print("Adding opening_balance_date column...")
            conn.execute(text("ALTER TABLE accounts ADD COLUMN opening_balance_date DATE"))
            conn.commit()
            print("Added opening_balance_date.")
        else:
            print("opening_balance_date column already exists.")
            
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
