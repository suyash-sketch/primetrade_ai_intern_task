from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserListResponse, UserRead


# ── Internal Helpers ────────────────────────────────────────

def _get_active_user(db: Session, user_id: int) -> User:
    """
    Central ownership / existence check reused by all
    functions that need a user row before acting on it.
    """
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return user


# ── Registration & Identity ─────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Used by the registration route to check for duplicates."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Hashes the password and locks the role to standard 'user' 
    to prevent privilege escalation during registration.
    """
    hashed_pw = get_password_hash(user_in.password)
    
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_pw,
        role=UserRole.USER.value, # Strictly enforce default role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ── Read ────────────────────────────────────────────────────

def get_user_by_id(db: Session, user_id: int) -> User:
    return _get_active_user(db, user_id)


def get_all_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    role_filter: Optional[UserRole] = None,
    search: Optional[str] = None,
) -> UserListResponse:
    
    query = db.query(User).filter(User.is_deleted == False)  

    if role_filter:
        query = query.filter(User.role == role_filter.value)

    if search:
        # ilike = case-insensitive LIKE; OR across email + username
        pattern = f"%{search}%"
        query = query.filter(
            User.email.ilike(pattern) | User.username.ilike(pattern)
        )

    # Calculate total for pagination metadata
    total = query.count()
    
    users = (
        query
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Convert SQLAlchemy models to Pydantic reads
    user_reads = [UserRead.model_validate(u) for u in users]
    
    return UserListResponse.build(
        users=user_reads,
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Update ──────────────────────────────────────────────────

def update_user(db: Session, user: User, update_data: UserUpdate) -> User:
    """
    Handles username changes and password changes safely.
    """
    if update_data.username is not None:
        # Check uniqueness before saving to avoid 500 DB crash
        existing = db.query(User).filter(
            User.username == update_data.username,
            User.id != user.id,
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        user.username = update_data.username

    if update_data.new_password:
        if not verify_password(update_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
        user.hashed_password = get_password_hash(update_data.new_password)

    db.commit()
    db.refresh(user)
    return user


# ── Admin Actions ───────────────────────────────────────────

def change_user_role(db: Session, user_id: int, new_role: UserRole) -> User:
    user = _get_active_user(db, user_id)
    user.role = new_role.value
    db.commit()
    db.refresh(user)
    return user


def toggle_user_active(db: Session, user_id: int) -> User:
    user = _get_active_user(db, user_id)
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


def soft_delete_user(db: Session, user: User) -> None:
    """
    Soft-deletes the user and cascades the soft-delete to all their tasks.
    """
    user.is_deleted = True
    user.is_active = False   # Revoke login capabilities
    
    # Cascade the soft delete manually since SQLAlchemy's 
    # 'cascade="all, delete-orphan"' only works for hard DB deletes.
    for task in user.tasks:
        task.is_deleted = True
        
    db.commit()