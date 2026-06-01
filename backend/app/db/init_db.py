import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """
    Seeds the database with required initial data.
    """
    
    # 1. Check if the initial admin already exists
    # (Assuming you added FIRST_SUPERUSER_EMAIL to config.py / .env)
    admin_email = getattr(settings, "FIRST_SUPERUSER_EMAIL", "admin@primetrade.ai")
    
    user = db.query(User).filter(User.email == admin_email).first()
    
    if not user:
        logger.info(f"Seeding initial superuser: {admin_email}")
        
        # 2. We bypass user_service.create_user here because that 
        # function strictly enforces the standard "user" role.
        admin_user = User(
            email=admin_email,
            username="superadmin",
            hashed_password=get_password_hash(
                getattr(settings, "FIRST_SUPERUSER_PASSWORD", "Admin@123!")
            ),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        logger.info("Superuser created successfully.")
    else:
        logger.info("Superuser already exists. Skipping seed.")