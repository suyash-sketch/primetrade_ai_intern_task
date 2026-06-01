from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskListResponse, TaskRead

def _get_active_task(db : Session, task_id : int, owner_id : int) -> Optional[Task]:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.owner_id == owner_id, Task.is_deleted == False).first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    return task

def create_task(db : Session, task_create : TaskCreate, owner_id : int) -> Task:
    task = Task(
        **task_create.model_dump(),
        owner_id = owner_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_task(db: Session, task_id : int, owner_id : int) -> Task:
    return _get_active_task(db, task_id, owner_id)

def get_tasks(
        db : Session,
        owner_id : int, 
        page : int = 1,
        page_size : int = 10,
        status_filter : Optional[str] = None,
        priority_filter : Optional[str] = None,
        search : Optional[str] = None
) -> TaskListResponse:
    
    query = db.query(Task).filter(
        Task.owner_id == owner_id,
        Task.is_deleted == False
    )

    if status_filter:
        query = query.filter(Task.status == status_filter)

    if priority_filter:
        query = query.filter(Task.priority == priority_filter)
    
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    total = query.count()

    task = (
        query
        .order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    task_reads = [TaskRead.model_validate(task) for t in task]

    return TaskListResponse.build(
        tasks= task_reads,
        total = total,
        page = page,
        page_size= page_size
    )

def update_task(db : Session, task_id : int, task_update : TaskUpdate, owner_id : int) -> Task:
    task = _get_active_task(db, task_id, owner_id)

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task

def delete_task(db : Session, task_id : int, owner_id : int) -> None:
    task = _get_active_task(db, task_id, owner_id)
    task.is_deleted = True
    db.commit()


def admin_get_all_tasks(
        db : Session,
        page : int = 1,
        page_size : int = 10,
        status_filter : Optional[str] = None,
        include_deleted : bool = False
) -> TaskListResponse:
    
    query = db.query(Task)

    if not include_deleted:
        query = query.filter(Task.is_deleted == False)

    if status_filter:
        query = query.filter(Task.status == status_filter)

    total = query.count()
    tasks = (
        query
        .order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    task_reads = [TaskRead.model_validate(t) for t in tasks]
    return TaskListResponse.build(
        tasks=task_reads,
        total=total,
        page=page,
        page_size=page_size,
    )


