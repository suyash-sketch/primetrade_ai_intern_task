import math
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title : str = Field(...,min_length=2 ,max_length=255)
    description : Optional[str] = Field(None, max_length=2000)
    status : Optional[TaskStatus] = Field(TaskStatus.TODO)
    priority : Optional[TaskPriority] = Field(TaskPriority.MEDIUM)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title : Optional[str] = Field(None,min_length=2 ,max_length=255)
    description : Optional[str] = Field(None, max_length=2000)
    status : Optional[TaskStatus] = None
    priority : Optional[TaskPriority] = None

    # Prevent explicit nulls from crashing the DB.
    # Allows fields to be omitted, but rejects {"status": null}
    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, values):
        for field in ['title', 'status', 'priority']:
            if field in values and values[field] is None:
                raise ValueError(f"{field} cannot be set to null")
        return values
    

class TaskRead(TaskBase):
    id : int
    owner_id : int
    created_at : datetime
    updated_at : Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TaskListResponse(BaseModel):
    tasks : list[TaskRead]
    total : int
    page : int
    page_size : int
    total_pages : int

    @classmethod
    def build(cls, tasks : list, total : int, page : int, page_size : int):
        return cls(
            tasks = tasks,
            total = total,
            page = page,
            page_size = page_size,
            total_pages = math.ceil(total / page_size) if total else 0,
        )

