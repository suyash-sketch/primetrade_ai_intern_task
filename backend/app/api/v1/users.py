from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate, UserRoleUpdate, UserListResponse, UserCreate
from app.services.user_service import (
    get_all_users,
    get_user_by_id,
    update_user,
    change_user_role,
    toggle_user_active,
    soft_delete_user,
    get_user_by_email,
    get_password_hash,
    create_user
)

router = APIRouter(prefix="/users", tags=["users"])

@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Public registration endpoint. Defaults the new user to the 'user' role.
    """
    existing_user = get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    return create_user(db=db, user_in=user_in)

@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user



@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user profile",
)
def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates username or password. 
    If updating password, `current_password` must be provided.
    """
    if update_data.new_password and not update_data.current_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="current_password is required when changing your password",
        )
    return update_user(db=db, user=current_user, update_data=update_data)

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete my account",
)
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-deletes the current user and cascades the deletion to their tasks."""
    soft_delete_user(db=db, user=current_user)
    return None

@router.get(
    "/",
    response_model=UserListResponse,
    summary="[Admin] List all users",
)
def list_all_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role_filter: Optional[UserRole] = None,
    search: Optional[str] = None,
    _admin: User = Depends(require_admin), # Security guard
    db: Session = Depends(get_db),
):
    """Returns a paginated list of all non-deleted users."""
    return get_all_users(
        db=db,
        page=page,
        page_size=page_size,
        role_filter=role_filter,
        search=search,
    )

@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="[Admin] Get specific user by ID",
)
def get_user(
    user_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Fetch any user's profile."""
    return get_user_by_id(db=db, user_id=user_id)

@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    summary="[Admin] Update user role",
)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Promote or demote a user. Admins cannot alter their own role."""
    if current_admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot alter your own role.",
        )
    return change_user_role(db=db, user_id=user_id, new_role=role_data.role)

@router.patch(
    "/{user_id}/suspend",
    response_model=UserRead,
    summary="[Admin] Toggle user active status",
)
def toggle_user_suspension(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Suspend or unsuspend a user account. Admins cannot suspend themselves."""
    if current_admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot suspend your own account.",
        )
    return toggle_user_active(db=db, user_id=user_id)

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Delete user account",
)
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Soft-deletes a user and their tasks."""
    if current_admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )
    user = get_user_by_id(db=db, user_id=user_id)
    soft_delete_user(db=db, user=user)
    return None