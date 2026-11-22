from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatusUpdate,
    TaskPriorityUpdate,
    TaskAssignUpdate,
    TaskSubtaskCreate,
    TaskDependencyCreate,
    TaskDependencyResponse,
    TaskBulkRequest,
    TaskReorderRequest,
    TaskSummaryResponse,
)
from app.api.dependencies import get_current_user
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# --- Fixed / Collection Endpoints (Must be declared before /{task_id}) ---

@router.get("", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status (Todo, In Progress, Completed, etc.)"),
    priority: Optional[str] = Query(None, description="Filter by priority (Low, Medium, High, Critical)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search keyword in title or description"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee user ID"),
    parent_task_id: Optional[str] = Query(None, description="Filter by parent task ID for subtasks"),
    is_archived: Optional[bool] = Query(False, description="Filter by archived status"),
    is_overdue: Optional[bool] = Query(None, description="Filter by overdue status"),
    due_date_from: Optional[str] = Query(None, description="Filter tasks due on or after date (YYYY-MM-DD)"),
    due_date_to: Optional[str] = Query(None, description="Filter tasks due on or before date (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by (created_at, due_date, sort_order, priority)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve tasks with multi-tenant filtering, pagination, and sorting."""
    return task_service.list_tasks(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
        organization_id=organization_id,
        assignee_id=assignee_id,
        parent_task_id=parent_task_id,
        status=status,
        priority=priority,
        category=category,
        search=search,
        is_archived=is_archived,
        is_overdue=is_overdue,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task with validation and tenant assignment."""
    return task_service.create_task(db=db, task_in=task_in, current_user=current_user)

@router.get("/summary", response_model=TaskSummaryResponse)
def get_task_summary(
    workspace_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated velocity, completion, and distribution metrics for dashboard views."""
    return task_service.get_task_summary(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id
    )

@router.get("/search", response_model=List[TaskResponse])
def search_tasks(
    q: Optional[str] = Query(None, description="Search query string"),
    query: Optional[str] = Query(None, description="Alternate search query string"),
    workspace_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full-text task search matching title or description."""
    search_term = q or query or ""
    return task_service.list_tasks(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
        search=search_term,
        limit=limit
    )

@router.post("/bulk", status_code=status.HTTP_200_OK)
def bulk_task_operations(
    bulk_in: TaskBulkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform atomic bulk operations across multiple tasks (status, priority, assign, delete, archive)."""
    return task_service.execute_bulk_operations(
        db=db,
        bulk_in=bulk_in,
        current_user=current_user
    )

@router.post("/reorder", status_code=status.HTTP_200_OK)
def reorder_tasks(
    reorder_in: TaskReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Persist new task display positions/sort_order for Kanban boards and list views."""
    return task_service.reorder_tasks(
        db=db,
        reorder_in=reorder_in,
        current_user=current_user
    )

# --- Parameterized Task Operations ---

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a single task."""
    task = task_service.get_task_or_404(db, task_id, current_user)
    return task_service.build_task_response(task)

@router.put("/{task_id}", response_model=TaskResponse)
def update_task_put(
    task_id: str,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full or partial update of task fields."""
    return task_service.update_task(
        db=db,
        task_id=task_id,
        task_in=task_in,
        current_user=current_user
    )

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task_patch(
    task_id: str,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Partial update of task fields."""
    return task_service.update_task(
        db=db,
        task_id=task_id,
        task_in=task_in,
        current_user=current_user
    )

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete task and its subtasks."""
    task_service.delete_task(db=db, task_id=task_id, current_user=current_user)
    return None

@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: str,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task lifecycle status and roll up subtask progress."""
    return task_service.update_status(
        db=db,
        task_id=task_id,
        status_in=status_in,
        current_user=current_user
    )

@router.patch("/{task_id}/priority", response_model=TaskResponse)
def update_task_priority(
    task_id: str,
    prio_in: TaskPriorityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task priority."""
    return task_service.update_priority(
        db=db,
        task_id=task_id,
        prio_in=prio_in,
        current_user=current_user
    )

@router.patch("/{task_id}/assign", response_model=TaskResponse)
def assign_task(
    task_id: str,
    assign_in: TaskAssignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign or unassign task to a team member."""
    return task_service.assign_task(
        db=db,
        task_id=task_id,
        assign_in=assign_in,
        current_user=current_user
    )

@router.post("/{task_id}/archive", response_model=TaskResponse)
def archive_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive task."""
    return task_service.archive_task(db=db, task_id=task_id, current_user=current_user)

@router.post("/{task_id}/restore", response_model=TaskResponse)
def restore_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore archived task."""
    return task_service.restore_task(db=db, task_id=task_id, current_user=current_user)

# --- Subtask Endpoints ---

@router.post("/{task_id}/subtasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_subtask(
    task_id: str,
    sub_in: TaskSubtaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a subtask linked to the parent task."""
    return task_service.create_subtask(
        db=db,
        parent_task_id=task_id,
        sub_in=sub_in,
        current_user=current_user
    )

@router.get("/{task_id}/subtasks", response_model=List[TaskResponse])
def get_subtasks(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all subtasks belonging to the parent task."""
    return task_service.get_subtasks(
        db=db,
        parent_task_id=task_id,
        current_user=current_user
    )

# --- Task Dependency Endpoints ---

@router.post("/{task_id}/dependencies", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
def add_task_dependency(
    task_id: str,
    dep_in: TaskDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a dependency on another task with automatic circular cycle detection."""
    return task_service.add_task_dependency(
        db=db,
        task_id=task_id,
        dep_in=dep_in,
        current_user=current_user
    )

@router.get("/{task_id}/dependencies", response_model=List[TaskDependencyResponse])
def get_task_dependencies(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all blocking dependencies for this task."""
    return task_service.get_task_dependencies(
        db=db,
        task_id=task_id,
        current_user=current_user
    )

@router.delete("/{task_id}/dependencies/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_dependency(
    task_id: str,
    dep_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a task dependency."""
    task_service.delete_task_dependency(
        db=db,
        task_id=task_id,
        dep_id=dep_id,
        current_user=current_user
    )
    return None
