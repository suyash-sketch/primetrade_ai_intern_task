import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, Index, text

from sqlalchemy.orm import relationship

from app.db.database import Base

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    
    # Status / Priority stored as standard Strings.
    # Pydantic schemas will enforce the Enum validation.
    status = Column(
        String(50), 
        nullable=False, 
        default=TaskStatus.TODO.value, 
        server_default= TaskStatus.TODO.value
        )
    
    priority = Column(
        String(50),
        nullable=False,
        default=TaskPriority.MEDIUM.value,
        server_default= TaskPriority.MEDIUM.value
    )

    is_deleted = Column(Boolean, default=False, nullable=False, server_default="false")


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="tasks")


    __table_args__ = (
        Index("ix_tasks_owner_status", "owner_id", "status" ),
        Index("ix_tasks_owner_active", "owner_id", postgresql_where = text("is_deleted = false")),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}"