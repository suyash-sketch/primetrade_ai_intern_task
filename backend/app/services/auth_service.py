from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password

def authenticate_user(
    db: Session, email: str, password: str
) -> Optional[User]:
    """
    Attempts to authenticate a user.
    Returns the User object if successful, or None if credentials fail.
    """
    # 1. Fetch user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
        
    # 2. Verify password against the stored bcrypt hash
    if not verify_password(password, user.hashed_password):
        return None
        
    return user