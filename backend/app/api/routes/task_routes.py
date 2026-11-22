from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskResponse])
def get_user_tasks(
    status: Optional[str] = Query(None, description="Filter by status (Todo, In Progress, Completed)"),
    priority: Optional[str] = Query(None, description="Filter by priority (Low, Medium, High)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search keyword in title or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all tasks owned strictly by the authenticated user with optional filtering."""
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if status and status.lower() != "all":
        query = query.filter(Task.status.ilike(status))
    if priority and priority.lower() != "all":
        query = query.filter(Task.priority.ilike(priority))
    if category and category.lower() != "all":
        query = query.filter(Task.category.ilike(category))
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term)
            )
        )

    return query.order_by(Task.created_at.desc()).all()

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task owned exclusively by the authenticated user."""
    title = task_in.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task title cannot be empty."
        )

    task_id = task_in.id or f"task-{int(datetime.now(timezone.utc).timestamp()*1000)}-{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone.utc)
    completed_at = now if (task_in.status or "").lower() == "completed" else None

    task = Task(
        id=task_id,
        title=title,
        description=task_in.description.strip() if task_in.description else "",
        category=task_in.category or "Design",
        status=task_in.status or "Todo",
        priority=task_in.priority or "Medium",
        due_date=task_in.due_date or "",
        user_id=current_user.id,
        created_at=now,
        updated_at=now,
        completed_at=completed_at
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a single task owned by the user. Returns 404 if not found or owned by another user."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task details. Preserves ownership; automatically tracks completed_at timestamp."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    now = datetime.now(timezone.utc)

    if task_in.title is not None:
        title = task_in.title.strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Task title cannot be empty."
            )
        task.title = title

    if task_in.description is not None:
        task.description = task_in.description.strip()
    if task_in.category is not None:
        task.category = task_in.category
    if task_in.priority is not None:
        task.priority = task_in.priority
    if task_in.due_date is not None:
        task.due_date = task_in.due_date

    # Status & completed_at lifecycle tracking
    if task_in.status is not None and task_in.status != task.status:
        old_status = task.status
        task.status = task_in.status
        if task.status.lower() == "completed":
            task.completed_at = now
        elif old_status.lower() == "completed" and task.status.lower() != "completed":
            task.completed_at = None

    task.updated_at = now
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a task owned by the user. Returns 404 if not found or owned by another user."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    db.delete(task)
    db.commit()
    return None
