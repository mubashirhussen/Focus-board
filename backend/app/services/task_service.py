from datetime import datetime, timezone, date
import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.task import Task, TaskDependency
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember, Activity
from app.models.organization import Organization, OrganizationMember
from app.models.project import Project, ProjectMember
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    TaskPriorityUpdate,
    TaskAssignUpdate,
    TaskSubtaskCreate,
    TaskDependencyCreate,
    TaskBulkRequest,
    TaskReorderRequest,
    TaskSummaryResponse,
    TaskResponse,
    TaskDependencyResponse,
)

def log_task_activity(
    db: Session,
    task: Task,
    user_id: int,
    action: str,
    details: str
):
    """Log task-related activity to activity log."""
    try:
        act = Activity(
            workspace_id=task.workspace_id,
            organization_id=task.organization_id,
            project_id=task.project_id,
            task_id=str(task.id),
            actor_id=user_id,
            event_type=action,
            entity_type="TASK",
            entity_id=str(task.id),
            description=details,
            created_at=datetime.utcnow(),
        )
        db.add(act)
        db.commit()
    except Exception:
        pass

def authorize_task_access(db: Session, task: Task, user: User, action: str = "read") -> bool:
    """Multi-tenant security authorization check."""
    # Direct creator or assignee always has access
    if task.user_id == user.id or task.assignee_id == user.id:
        return True

    # If associated with a workspace, verify membership
    if task.workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
        if ws and ws.owner_id == user.id:
            return True
        membership = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == task.workspace_id,
            WorkspaceMember.user_id == user.id
        ).first()
        if membership:
            return True

    # If associated with a project, verify project membership
    if task.project_id:
        proj = db.query(Project).filter(Project.id == task.project_id).first()
        if proj and proj.owner_id == user.id:
            return True
        proj_mem = db.query(ProjectMember).filter(
            ProjectMember.project_id == task.project_id,
            ProjectMember.user_id == user.id
        ).first()
        if proj_mem:
            return True

    # If associated with an organization, verify org membership
    if task.organization_id:
        org = db.query(Organization).filter(Organization.id == task.organization_id).first()
        if org and org.owner_id == user.id:
            return True
        org_mem = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == task.organization_id,
            OrganizationMember.user_id == user.id
        ).first()
        if org_mem:
            return True

    return False

def get_task_or_404(
    db: Session,
    task_id: str,
    user: User,
    include_deleted: bool = False
) -> Task:
    """Retrieve task and verify tenant authorization. Return 404 on isolation violation."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    if not include_deleted and task.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    if not authorize_task_access(db, task, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    return task

def rollup_subtask_progress(db: Session, parent_task_id: str) -> None:
    """Calculate and roll up subtask completion percentages to parent task."""
    parent = db.query(Task).filter(Task.id == parent_task_id, Task.is_deleted == False).first()
    if not parent:
        return

    subtasks = db.query(Task).filter(
        Task.parent_task_id == parent_task_id,
        Task.is_deleted == False
    ).all()

    if not subtasks:
        parent.progress_percent = 0.0
        return

    total = len(subtasks)
    completed = sum(1 for s in subtasks if (s.status or "").lower() == "completed")
    new_progress = round((completed / total) * 100.0, 1)
    parent.progress_percent = new_progress

    now = datetime.now(timezone.utc)
    if new_progress >= 100.0 and parent.status.lower() != "completed":
        parent.status = "Completed"
        parent.completed_at = now
    elif new_progress < 100.0 and parent.status.lower() == "completed" and total > 0:
        parent.status = "In Progress"
        parent.completed_at = None

    parent.updated_at = now
    db.commit()
    db.refresh(parent)

def parse_is_overdue(task: Task) -> bool:
    """Check if task is overdue based on due_date string and completion status."""
    if (task.status or "").lower() == "completed":
        return False
    if not task.due_date:
        return False
    try:
        # Support YYYY-MM-DD or ISO strings
        due_str = task.due_date.strip().split("T")[0]
        due_d = datetime.strptime(due_str, "%Y-%m-%d").date()
        return due_d < date.today()
    except Exception:
        return False

def build_task_response(task: Task) -> TaskResponse:
    """Construct TaskResponse with computed fields and subtask counts."""
    # Count subtasks
    subtask_count = 0
    completed_subtask_count = 0
    if hasattr(task, "subtasks") and task.subtasks:
        active_subtasks = [s for s in task.subtasks if not s.is_deleted]
        subtask_count = len(active_subtasks)
        completed_subtask_count = sum(1 for s in active_subtasks if (s.status or "").lower() == "completed")

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description or "",
        category=task.category,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date or "",
        start_date=getattr(task, "start_date", "") or "",
        is_all_day=getattr(task, "is_all_day", False) or False,
        timezone_name=getattr(task, "timezone_name", "UTC") or "UTC",
        scheduled_start=task.scheduled_start,
        scheduled_end=task.scheduled_end,
        estimated_duration_minutes=task.estimated_duration_minutes or 30,
        actual_minutes=task.actual_minutes or 0,
        progress_percent=task.progress_percent or 0.0,
        labels=task.labels,
        sort_order=task.sort_order or 0,
        is_archived=task.is_archived or False,
        archived_at=task.archived_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        user_id=task.user_id,
        organization_id=task.organization_id,
        workspace_id=task.workspace_id,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        parent_task_id=task.parent_task_id,
        subtask_count=subtask_count,
        completed_subtask_count=completed_subtask_count,
        is_overdue=parse_is_overdue(task)
    )

def create_task(
    db: Session,
    task_in: TaskCreate,
    current_user: User
) -> TaskResponse:
    """Create a new task with validation and organization/workspace linkage."""
    title = task_in.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task title cannot be empty."
        )

    # Validate parent task if specified
    if task_in.parent_task_id:
        parent = get_task_or_404(db, task_in.parent_task_id, current_user)
        # Inherit workspace/project if not provided
        if not task_in.workspace_id:
            task_in.workspace_id = parent.workspace_id
        if not task_in.project_id:
            task_in.project_id = parent.project_id

    # Validate workspace membership if specified
    if task_in.workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == task_in.workspace_id).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found.")
        is_member = (ws.owner_id == current_user.id) or db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == task_in.workspace_id,
            WorkspaceMember.user_id == current_user.id
        ).first() is not None
        if not is_member:
            raise HTTPException(status_code=403, detail="Not authorized for this workspace.")

    now = datetime.now(timezone.utc)
    task_id = task_in.id or f"task-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"
    completed_at = now if (task_in.status or "").lower() == "completed" else None

    # Date range validation
    if task_in.scheduled_start and task_in.scheduled_end:
        if task_in.scheduled_end < task_in.scheduled_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Scheduled end date cannot be earlier than scheduled start date."
            )

    task = Task(
        id=task_id,
        title=title,
        description=task_in.description.strip() if task_in.description else "",
        category=task_in.category or "Design",
        status=task_in.status or "Todo",
        priority=task_in.priority or "Medium",
        due_date=task_in.due_date or "",
        start_date=getattr(task_in, "start_date", "") or "",
        is_all_day=getattr(task_in, "is_all_day", False) or False,
        timezone_name=getattr(task_in, "timezone_name", "UTC") or "UTC",
        scheduled_start=task_in.scheduled_start,
        scheduled_end=task_in.scheduled_end,
        estimated_duration_minutes=task_in.estimated_duration_minutes or 30,
        actual_minutes=task_in.actual_minutes or 0,
        progress_percent=task_in.progress_percent or 0.0,
        sort_order=task_in.sort_order or 0,
        workspace_id=task_in.workspace_id,
        project_id=task_in.project_id,
        assignee_id=task_in.assignee_id,
        parent_task_id=task_in.parent_task_id,
        user_id=current_user.id,
        created_at=now,
        updated_at=now,
        completed_at=completed_at,
        is_archived=False,
        is_deleted=False
    )
    if task_in.labels:
        task.labels = task_in.labels

    db.add(task)
    db.commit()
    db.refresh(task)

    if task.assignee_id and task.assignee_id != current_user.id:
        try:
            from app.services.notification_service import notification_service
            notification_service.notify_task_assigned(db, task, task.assignee_id, current_user.id)
        except Exception:
            pass

    if task.parent_task_id:
        rollup_subtask_progress(db, task.parent_task_id)

    log_task_activity(db, task, current_user.id, "TASK_CREATED", f"Created task '{task.title}'.")

    try:
        from app.services.automation_engine_service import dispatch_automation_event
        dispatch_automation_event(
            db=db,
            event_type="task.created",
            payload={
                "task_id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "workspace_id": task.workspace_id,
                "project_id": task.project_id,
                "assignee_id": task.assignee_id
            },
            workspace_id=task.workspace_id,
            actor_id=current_user.id
        )
    except Exception:
        pass

    return build_task_response(task)

def update_task(
    db: Session,
    task_id: str,
    task_in: TaskUpdate,
    current_user: User
) -> TaskResponse:
    """Update task metadata, status lifecycle, scheduling, or reassignments."""
    task = get_task_or_404(db, task_id, current_user)
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
    if task_in.sort_order is not None:
        task.sort_order = task_in.sort_order
    if task_in.actual_minutes is not None:
        task.actual_minutes = task_in.actual_minutes
    if task_in.progress_percent is not None:
        task.progress_percent = task_in.progress_percent
    if task_in.labels is not None:
        task.labels = task_in.labels

    # Scheduling updates & date sanity
    start_dt = task_in.scheduled_start if task_in.scheduled_start is not None else task.scheduled_start
    end_dt = task_in.scheduled_end if task_in.scheduled_end is not None else task.scheduled_end
    if start_dt and end_dt and end_dt < start_dt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scheduled end date cannot be earlier than scheduled start date."
        )
    if task_in.scheduled_start is not None:
        task.scheduled_start = task_in.scheduled_start
    if task_in.scheduled_end is not None:
        task.scheduled_end = task_in.scheduled_end
    if task_in.estimated_duration_minutes is not None:
        task.estimated_duration_minutes = task_in.estimated_duration_minutes
    if getattr(task_in, "is_all_day", None) is not None:
        task.is_all_day = task_in.is_all_day
    if getattr(task_in, "start_date", None) is not None:
        task.start_date = task_in.start_date
    if getattr(task_in, "timezone_name", None) is not None:
        task.timezone_name = task_in.timezone_name

    # Reassignments & project linkage
    old_assignee = task.assignee_id
    if task_in.project_id is not None:
        task.project_id = task_in.project_id
    if task_in.assignee_id is not None:
        task.assignee_id = task_in.assignee_id

    # Status & completed_at lifecycle tracking
    status_changed = False
    if task_in.status is not None and task_in.status != task.status:
        status_changed = True
        old_status = task.status
        task.status = task_in.status
        if task.status.lower() == "completed":
            task.completed_at = now
            task.progress_percent = 100.0
        elif old_status.lower() == "completed" and task.status.lower() != "completed":
            task.completed_at = None

    task.updated_at = now
    db.commit()
    db.refresh(task)

    if task_in.assignee_id is not None and task_in.assignee_id != old_assignee and task_in.assignee_id != current_user.id:
        try:
            from app.services.notification_service import notification_service
            notification_service.notify_task_assigned(db, task, task_in.assignee_id, current_user.id)
        except Exception:
            pass

    if status_changed and task.status.lower() == "completed":
        try:
            from app.services.notification_service import notification_service
            notification_service.notify_task_completed(db, task, current_user.id)
            notification_service.on_task_completed(db, task.id, current_user.id)
        except Exception:
            pass

    if status_changed and task.parent_task_id:
        rollup_subtask_progress(db, task.parent_task_id)

    log_task_activity(db, task, current_user.id, "TASK_UPDATED", f"Updated task '{task.title}'.")

    try:
        from app.services.automation_engine_service import dispatch_automation_event
        if status_changed:
            dispatch_automation_event(
                db=db,
                event_type="task.status_changed",
                payload={
                    "task_id": task.id,
                    "title": task.title,
                    "old_status": old_status,
                    "new_status": task.status,
                    "status": task.status,
                    "priority": task.priority,
                    "workspace_id": task.workspace_id,
                    "project_id": task.project_id
                },
                workspace_id=task.workspace_id,
                actor_id=current_user.id
            )
            if task.status.lower() == "completed":
                dispatch_automation_event(
                    db=db,
                    event_type="task.completed",
                    payload={
                        "task_id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "workspace_id": task.workspace_id,
                        "project_id": task.project_id
                    },
                    workspace_id=task.workspace_id,
                    actor_id=current_user.id
                )
        if task_in.assignee_id is not None and task_in.assignee_id != old_assignee:
            dispatch_automation_event(
                db=db,
                event_type="task.assigned",
                payload={
                    "task_id": task.id,
                    "title": task.title,
                    "assignee_id": task.assignee_id,
                    "old_assignee": old_assignee,
                    "workspace_id": task.workspace_id
                },
                workspace_id=task.workspace_id,
                actor_id=current_user.id
            )
    except Exception:
        pass

    return build_task_response(task)

def update_status(
    db: Session,
    task_id: str,
    status_in: TaskStatusUpdate,
    current_user: User
) -> TaskResponse:
    """Specific endpoint for task status transitions."""
    task = get_task_or_404(db, task_id, current_user)
    now = datetime.now(timezone.utc)
    old_status = task.status
    task.status = status_in.status

    if task.status.lower() == "completed":
        task.completed_at = now
        task.progress_percent = 100.0
    elif old_status.lower() == "completed" and task.status.lower() != "completed":
        task.completed_at = None

    task.updated_at = now
    db.commit()
    db.refresh(task)

    if task.status.lower() == "completed" and old_status.lower() != "completed":
        try:
            from app.services.notification_service import notification_service
            notification_service.notify_task_completed(db, task, current_user.id)
            notification_service.on_task_completed(db, task.id, current_user.id)
        except Exception:
            pass

    if task.parent_task_id:
        rollup_subtask_progress(db, task.parent_task_id)

    log_task_activity(db, task, current_user.id, "TASK_STATUS_CHANGED", f"Moved '{task.title}' to {task.status}.")

    try:
        from app.services.automation_engine_service import dispatch_automation_event
        dispatch_automation_event(
            db=db,
            event_type="task.status_changed",
            payload={
                "task_id": task.id,
                "title": task.title,
                "old_status": old_status,
                "new_status": task.status,
                "status": task.status,
                "priority": task.priority,
                "workspace_id": task.workspace_id,
                "project_id": task.project_id
            },
            workspace_id=task.workspace_id,
            actor_id=current_user.id
        )
        if task.status.lower() == "completed" and old_status.lower() != "completed":
            dispatch_automation_event(
                db=db,
                event_type="task.completed",
                payload={
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "workspace_id": task.workspace_id,
                    "project_id": task.project_id
                },
                workspace_id=task.workspace_id,
                actor_id=current_user.id
            )
    except Exception:
        pass

    return build_task_response(task)

def update_priority(
    db: Session,
    task_id: str,
    prio_in: TaskPriorityUpdate,
    current_user: User
) -> TaskResponse:
    """Specific endpoint for task priority adjustment."""
    task = get_task_or_404(db, task_id, current_user)
    task.priority = prio_in.priority
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    log_task_activity(db, task, current_user.id, "TASK_PRIORITY_CHANGED", f"Set priority of '{task.title}' to {task.priority}.")
    return build_task_response(task)

def assign_task(
    db: Session,
    task_id: str,
    assign_in: TaskAssignUpdate,
    current_user: User
) -> TaskResponse:
    """Assign or unassign task."""
    task = get_task_or_404(db, task_id, current_user)
    task.assignee_id = assign_in.assignee_id
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    log_task_activity(db, task, current_user.id, "TASK_ASSIGNED", f"Assigned task '{task.title}'.")
    return build_task_response(task)

def archive_task(db: Session, task_id: str, current_user: User) -> TaskResponse:
    """Archive task."""
    task = get_task_or_404(db, task_id, current_user)
    task.is_archived = True
    task.archived_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return build_task_response(task)

def restore_task(db: Session, task_id: str, current_user: User) -> TaskResponse:
    """Restore archived task."""
    task = get_task_or_404(db, task_id, current_user)
    task.is_archived = False
    task.archived_at = None
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return build_task_response(task)

def delete_task(db: Session, task_id: str, current_user: User) -> None:
    """Soft delete task and cascade soft deletion to subtasks."""
    task = get_task_or_404(db, task_id, current_user)
    now = datetime.now(timezone.utc)
    parent_id = task.parent_task_id

    task.is_deleted = True
    task.deleted_at = now
    task.updated_at = now

    # Also mark any subtasks as soft-deleted
    for sub in task.subtasks:
        sub.is_deleted = True
        sub.deleted_at = now

    db.commit()

    if parent_id:
        rollup_subtask_progress(db, parent_id)

    log_task_activity(db, task, current_user.id, "TASK_DELETED", f"Deleted task '{task.title}'.")

def create_subtask(
    db: Session,
    parent_task_id: str,
    sub_in: TaskSubtaskCreate,
    current_user: User
) -> TaskResponse:
    """Create a new subtask attached directly to the parent task."""
    parent = get_task_or_404(db, parent_task_id, current_user)

    now = datetime.now(timezone.utc)
    subtask_id = f"subtask-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"

    subtask = Task(
        id=subtask_id,
        title=sub_in.title.strip(),
        description=sub_in.description.strip() if sub_in.description else "",
        category=sub_in.category or parent.category,
        status=sub_in.status or "Todo",
        priority=sub_in.priority or "Medium",
        due_date=sub_in.due_date or parent.due_date or "",
        user_id=current_user.id,
        workspace_id=parent.workspace_id,
        project_id=parent.project_id,
        assignee_id=sub_in.assignee_id,
        parent_task_id=parent.id,
        estimated_duration_minutes=sub_in.estimated_duration_minutes or 30,
        sort_order=len(parent.subtasks) if parent.subtasks else 0,
        created_at=now,
        updated_at=now,
        completed_at=now if (sub_in.status or "").lower() == "completed" else None,
        is_archived=False,
        is_deleted=False
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)

    rollup_subtask_progress(db, parent.id)
    return build_task_response(subtask)

def get_subtasks(
    db: Session,
    parent_task_id: str,
    current_user: User
) -> List[TaskResponse]:
    """Retrieve all non-deleted subtasks for a parent task."""
    parent = get_task_or_404(db, parent_task_id, current_user)
    subtasks = db.query(Task).filter(
        Task.parent_task_id == parent.id,
        Task.is_deleted == False
    ).order_by(Task.sort_order.asc(), Task.created_at.asc()).all()
    return [build_task_response(s) for s in subtasks]

# --- Task Dependencies & Cycle Prevention ---

def detect_dependency_cycle(db: Session, source_task_id: str, target_task_id: str) -> bool:
    """
    Detect whether adding dependency (source_task_id depends on target_task_id) creates a cycle.
    A cycle occurs if there is already a path from target_task_id to source_task_id.
    """
    visited = set()
    queue = [target_task_id]

    while queue:
        curr = queue.pop(0)
        if curr == source_task_id:
            return True
        visited.add(curr)
        # Find all tasks that 'curr' depends on
        outgoing = db.query(TaskDependency).filter(TaskDependency.task_id == curr).all()
        for dep in outgoing:
            if dep.depends_on_task_id not in visited:
                queue.append(dep.depends_on_task_id)

    return False

def add_task_dependency(
    db: Session,
    task_id: str,
    dep_in: TaskDependencyCreate,
    current_user: User
) -> TaskDependencyResponse:
    """Create a task dependency with cycle detection."""
    task = get_task_or_404(db, task_id, current_user)
    target = get_task_or_404(db, dep_in.depends_on_task_id, current_user)

    if task.id == target.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A task cannot depend on itself."
        )

    # Check for existing duplicate dependency
    existing = db.query(TaskDependency).filter(
        TaskDependency.task_id == task.id,
        TaskDependency.depends_on_task_id == target.id
    ).first()
    if existing:
        return TaskDependencyResponse(
            id=existing.id,
            task_id=existing.task_id,
            depends_on_task_id=existing.depends_on_task_id,
            dependency_type=existing.dependency_type,
            created_at=existing.created_at,
            depends_on_task_title=target.title,
            depends_on_task_status=target.status
        )

    # Detect cycle
    if detect_dependency_cycle(db, task.id, target.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Circular dependency detected: '{task.title}' cannot depend on '{target.title}'."
        )

    dep_id = f"dep-{int(datetime.now(timezone.utc).timestamp()*1000)}-{uuid.uuid4().hex[:6]}"
    dep = TaskDependency(
        id=dep_id,
        task_id=task.id,
        depends_on_task_id=target.id,
        dependency_type=dep_in.dependency_type or "FINISH_TO_START",
        created_at=datetime.now(timezone.utc)
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)

    log_task_activity(db, task, current_user.id, "DEPENDENCY_ADDED", f"Added dependency on '{target.title}'.")
    return TaskDependencyResponse(
        id=dep.id,
        task_id=dep.task_id,
        depends_on_task_id=dep.depends_on_task_id,
        dependency_type=dep.dependency_type,
        created_at=dep.created_at,
        depends_on_task_title=target.title,
        depends_on_task_status=target.status
    )

def get_task_dependencies(
    db: Session,
    task_id: str,
    current_user: User
) -> List[TaskDependencyResponse]:
    """Retrieve all dependencies for a task."""
    task = get_task_or_404(db, task_id, current_user)
    deps = db.query(TaskDependency).filter(TaskDependency.task_id == task.id).all()
    results = []
    for d in deps:
        target = db.query(Task).filter(Task.id == d.depends_on_task_id).first()
        results.append(TaskDependencyResponse(
            id=d.id,
            task_id=d.task_id,
            depends_on_task_id=d.depends_on_task_id,
            dependency_type=d.dependency_type,
            created_at=d.created_at,
            depends_on_task_title=target.title if target else "Unknown",
            depends_on_task_status=target.status if target else "Unknown"
        ))
    return results

def delete_task_dependency(
    db: Session,
    task_id: str,
    dep_id: str,
    current_user: User
) -> None:
    """Remove a task dependency."""
    task = get_task_or_404(db, task_id, current_user)
    dep = db.query(TaskDependency).filter(
        TaskDependency.id == dep_id,
        TaskDependency.task_id == task.id
    ).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found.")
    db.delete(dep)
    db.commit()

# --- Bulk Operations & Reordering ---

def execute_bulk_operations(
    db: Session,
    bulk_in: TaskBulkRequest,
    current_user: User
) -> Dict[str, Any]:
    """Execute atomic bulk status, priority, assignment, delete, or archive operations."""
    if not bulk_in.task_ids:
        return {"affected_count": 0, "status": "success"}

    tasks = db.query(Task).filter(
        Task.id.in_(bulk_in.task_ids),
        Task.is_deleted == False
    ).all()

    # Filter to authorized tasks
    authorized_tasks = [t for t in tasks if authorize_task_access(db, t, current_user)]
    now = datetime.now(timezone.utc)

    for task in authorized_tasks:
        if bulk_in.action == "update_status" and bulk_in.status:
            task.status = bulk_in.status
            if task.status.lower() == "completed":
                task.completed_at = now
                task.progress_percent = 100.0
            else:
                task.completed_at = None
            task.updated_at = now
        elif bulk_in.action == "update_priority" and bulk_in.priority:
            task.priority = bulk_in.priority
            task.updated_at = now
        elif bulk_in.action == "assign":
            task.assignee_id = bulk_in.assignee_id
            task.updated_at = now
        elif bulk_in.action == "archive":
            task.is_archived = True
            task.archived_at = now
            task.updated_at = now
        elif bulk_in.action == "restore":
            task.is_archived = False
            task.archived_at = None
            task.updated_at = now
        elif bulk_in.action == "delete":
            task.is_deleted = True
            task.deleted_at = now
            task.updated_at = now

    db.commit()
    return {
        "status": "success",
        "action": bulk_in.action,
        "affected_count": len(authorized_tasks)
    }

def reorder_tasks(
    db: Session,
    reorder_in: TaskReorderRequest,
    current_user: User
) -> Dict[str, Any]:
    """Reorder tasks by updating their sort_order."""
    for item in reorder_in.items:
        task = db.query(Task).filter(Task.id == item.id, Task.is_deleted == False).first()
        if task and authorize_task_access(db, task, current_user):
            task.sort_order = item.sort_order
            task.updated_at = datetime.now(timezone.utc)

    db.commit()
    return {"status": "success", "reordered_count": len(reorder_in.items)}

# --- Search, Filter & Summary ---

def list_tasks(
    db: Session,
    current_user: User,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    parent_task_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_archived: Optional[bool] = False,
    is_overdue: Optional[bool] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    limit: int = 100,
    offset: int = 0
) -> List[TaskResponse]:
    """Retrieve tasks with comprehensive multi-criteria filtering, search and pagination."""
    query = db.query(Task).filter(Task.is_deleted == False)

    # Scoped tenancy check
    if workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            return []
        is_member = (ws.owner_id == current_user.id) or db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        ).first() is not None
        if not is_member:
            return []
        query = query.filter(Task.workspace_id == workspace_id)
    elif project_id:
        query = query.filter(Task.project_id == project_id)
    elif organization_id:
        query = query.filter(Task.organization_id == organization_id)
    else:
        # User's personal or assigned tasks if no group context provided
        query = query.filter(
            or_(
                Task.user_id == current_user.id,
                Task.assignee_id == current_user.id
            )
        )

    if project_id and not workspace_id:
        query = query.filter(Task.project_id == project_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if parent_task_id is not None:
        query = query.filter(Task.parent_task_id == parent_task_id)

    if is_archived is not None:
        query = query.filter(Task.is_archived == is_archived)

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

    if due_date_from:
        query = query.filter(Task.due_date >= due_date_from)
    if due_date_to:
        query = query.filter(Task.due_date <= due_date_to)

    # Sorting
    if sort_by == "sort_order":
        order_col = Task.sort_order.desc() if sort_order.lower() == "desc" else Task.sort_order.asc()
    elif sort_by == "due_date":
        order_col = Task.due_date.desc() if sort_order.lower() == "desc" else Task.due_date.asc()
    elif sort_by == "priority":
        order_col = Task.priority.desc() if sort_order.lower() == "desc" else Task.priority.asc()
    else:
        order_col = Task.created_at.desc() if sort_order.lower() == "desc" else Task.created_at.asc()

    tasks = query.order_by(order_col).offset(offset).limit(limit).all()

    responses = [build_task_response(t) for t in tasks]
    if is_overdue is not None:
        responses = [r for r in responses if r.is_overdue == is_overdue]

    return responses

def get_task_summary(
    db: Session,
    current_user: User,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None
) -> TaskSummaryResponse:
    """Calculate aggregate task summary and velocity metrics."""
    query = db.query(Task).filter(Task.is_deleted == False, Task.is_archived == False)

    if workspace_id:
        query = query.filter(Task.workspace_id == workspace_id)
    elif project_id:
        query = query.filter(Task.project_id == project_id)
    else:
        query = query.filter(
            or_(
                Task.user_id == current_user.id,
                Task.assignee_id == current_user.id
            )
        )

    tasks = query.all()
    total = len(tasks)
    completed = sum(1 for t in tasks if (t.status or "").lower() == "completed")
    in_progress = sum(1 for t in tasks if (t.status or "").lower() == "in progress")
    todo = sum(1 for t in tasks if (t.status or "").lower() == "todo")

    today_str = date.today().isoformat()
    overdue = sum(1 for t in tasks if parse_is_overdue(t))
    due_today = sum(1 for t in tasks if t.due_date and t.due_date.startswith(today_str) and (t.status or "").lower() != "completed")

    completion_rate = round((completed / total) * 100.0, 1) if total > 0 else 0.0

    by_priority: Dict[str, int] = {}
    by_category: Dict[str, int] = {}

    for t in tasks:
        prio = t.priority or "Medium"
        by_priority[prio] = by_priority.get(prio, 0) + 1

        cat = t.category or "Design"
        by_category[cat] = by_category.get(cat, 0) + 1

    return TaskSummaryResponse(
        total=total,
        completed=completed,
        in_progress=in_progress,
        todo=todo,
        overdue=overdue,
        due_today=due_today,
        completion_rate=completion_rate,
        by_priority=by_priority,
        by_category=by_category
    )
