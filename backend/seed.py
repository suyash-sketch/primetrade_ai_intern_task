# backend/seed.py
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.task import Task 


# backend/seed.py
import logging

from app.db.database import SessionLocal
from app.db.init_db import init_db

# Set up logging so you can see exactly what happens in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    logger.info("Starting database seeding process...")
    
    # 1. Open a manual database session
    db = SessionLocal()
    
    try:
        # 2. Pass the session to your seed function
        init_db(db)
    except Exception as e:
        logger.error(f"An error occurred during seeding: {e}")
    finally:
        # 3. Always close the session to prevent memory leaks or locked tables
        db.close()
        
    logger.info("Seeding process finished.")

if __name__ == "__main__":
    main()