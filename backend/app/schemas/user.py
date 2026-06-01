import math
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")
    return value

def validate_username(value: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_]{3,50}$", value):
        raise ValueError(
            "Username must be 3–50 characters and contain only "
            "letters, numbers, and underscores"
        )
    return value

class UserCreate(BaseModel):
    email: EmailStr = Field(..., examples=["alice@example.com"])
    username: str = Field(..., min_length=3, max_length=50, examples=["alice_dev"])
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("username", mode="before")
    @classmethod
    def username_format(cls, value: str) -> str:
        return validate_username(value.strip())

    @field_validator("email", mode="before")
    @classmethod
    def email_lowercase(cls, value: str) -> str:
        return value.lower()
    
class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserListResponse(BaseModel):
    users: list[UserRead]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def build(cls, users: list, total: int, page: int, page_size: int) -> "UserListResponse":
        return cls(
            users=users,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    current_password: Optional[str] = Field(None)
    new_password: Optional[str] = Field(None, min_length=8)

    @field_validator("username", mode="before")
    @classmethod
    def username_format(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            return validate_username(value.strip())
        return value

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            return validate_password_strength(value)
        return value

class UserRoleUpdate(BaseModel):
    role: UserRole

class UserInDB(UserRead):
    hashed_password: str
    is_deleted: bool
    model_config = ConfigDict(from_attributes=True)