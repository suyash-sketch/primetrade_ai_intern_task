from datetime import datetime
import enum
from sqlalchemy import Column, Boolean, Integer, String, DateTime, func, Index, text
from sqlalchemy.orm import relationship

from app.db.database import Base

class UserRole(str, enum.Enum):
    USER  = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    role = Column(
        String(50),
        nullable=False,
        default=UserRole.USER.value,
        server_default=UserRole.USER.value,
    )

    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    is_deleted = Column(Boolean, nullable=False, default=False, server_default="false")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    tasks = relationship(
        "Task",
        back_populates="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_users_role_active", 
            "role", 
            postgresql_where=text("is_deleted = false")
        ),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"