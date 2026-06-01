from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskRead, TaskListResponse
from app.services import task_service

from app.core.dependencies import get_current_user 

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) # 🔒 Protected route
):
    return task_service.create_task(db=db, task_in=task_in, owner_id=current_user.id)


@router.get("/", response_model=TaskListResponse)
def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user) #  Scoped to this user
):
    return task_service.get_tasks(
        db=db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search=search
    )


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return task_service.get_task(db=db, task_id=task_id, owner_id=current_user.id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return task_service.update_task(db=db, task_id=task_id, task_in=task_in, owner_id=current_user.id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task_service.delete_task(db=db, task_id=task_id, owner_id=current_user.id)
    return None
