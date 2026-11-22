import uuid
import json
import hashlib
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request, status, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.collaboration import Project, Workspace, WorkspaceMember
from app.models.developer_platform import DeveloperCredential, IdempotencyRecord
from app.schemas.developer import (
    PublicTaskCreate,
    PublicTaskUpdate,
    PublicTaskResponse,
    PublicProjectResponse,
)
from app.schemas.enterprise_analytics import PortfolioHealthResponse
from app.services.developer_service import DeveloperService
from app.services.enterprise_analytics_service import EnterpriseAnalyticsService

router = APIRouter(prefix="/public/v1", tags=["FocusBoard Public API (v1)"])

def authenticate_public_api(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Tuple[User, DeveloperCredential, List[str]]:
    """Dependency to authenticate external requests via X-API-Key."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header. Provide an API key starting with 'fb_live_'"
        )
    return DeveloperService.verify_api_key(
        db=db,
        api_key_header=x_api_key,
        endpoint=str(request.url.path),
        method=request.method
    )

# TASKS
@router.get("/tasks", response_model=List[PublicTaskResponse])
def public_list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    project_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: Tuple[User, DeveloperCredential, List[str]] = Depends(authenticate_public_api),
    db: Session = Depends(get_db),
):
    user, cred, scopes = auth
    DeveloperService.check_scope("tasks:read", scopes)

    query = db.query(Task).filter(Task.user_id == user.id)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if project_id:
        query = query.filter(Task.project_id == project_id)

    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
    return tasks

@router.post("/tasks", response_model=PublicTaskResponse, status_code=status.HTTP_201_CREATED)
def public_create_task(
    payload: PublicTaskCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    auth: Tuple[User, DeveloperCredential, List[str]] = Depends(authenticate_public_api),
    db: Session = Depends(get_db),
):
    user, cred, scopes = auth
    DeveloperService.check_scope("tasks:write", scopes)

    now = datetime.now(timezone.utc)

    # Idempotency check
    if idempotency_key:
        req_hash = hashlib.sha256(json.dumps(payload.dict(), sort_keys=True).encode("utf-8")).hexdigest()
        existing_record = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.idempotency_key == idempotency_key,
            IdempotencyRecord.user_id == user.id
        ).first()

        if existing_record:
            exp_tz = existing_record.expires_at if existing_record.expires_at.tzinfo else existing_record.expires_at.replace(tzinfo=timezone.utc)
            if exp_tz > now:
                # Return cached response
                cached_data = json.loads(existing_record.response_body)
                return PublicTaskResponse(**cached_data)

    # Resolve workspace
    app = cred.application
    workspace_id = app.workspace_id if app else None
    if not workspace_id:
        member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
        workspace_id = member.workspace_id if member else None

    task_id = f"task-{int(now.timestamp() * 1000)}-{uuid.uuid4().hex[:6]}"
    task = Task(
        id=task_id,
        user_id=user.id,
        workspace_id=workspace_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        priority=payload.priority,
        category=payload.category,
        project_id=payload.project_id,
        status="pending",
        created_at=now,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Trigger Webhook
    if workspace_id:
        DeveloperService.trigger_webhook_event(
            db=db,
            workspace_id=workspace_id,
            event_type="task.created",
            payload={
                "event": "task.created",
                "task_id": task.id,
                "title": task.title,
                "status": task.status,
                "user_id": user.id,
                "timestamp": now.isoformat()
            }
        )

    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "category": task.category,
        "due_date": task.due_date,
        "project_id": task.project_id,
        "user_id": task.user_id,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }

    # Store Idempotency
    if idempotency_key:
        idem = IdempotencyRecord(
            idempotency_key=idempotency_key,
            user_id=user.id,
            endpoint="/public/v1/tasks",
            request_hash=req_hash,
            response_code=201,
            response_body=json.dumps(task_dict, default=str),
            created_at=now,
            expires_at=now + timedelta(hours=24)
        )
        db.add(idem)
        db.commit()

    return task

@router.get("/tasks/{task_id}", response_model=PublicTaskResponse)
def public_get_task(
    task_id: str,
    auth: Tuple[User, DeveloperCredential, List[str]] = Depends(authenticate_public_api),
    db: Session = Depends(get_db),
):
    user, cred, scopes = auth
    DeveloperService.check_scope("tasks:read", scopes)

    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/tasks/{task_id}", response_model=PublicTaskResponse)
def public_update_task(
    task_id: str,
    payload: PublicTaskUpdate,
    auth: Tuple[User, DeveloperCredential, List[str]] = Depends(authenticate_public_api),
    db: Session = Depends(get_db),
):
    user, cred, scopes = auth
    DeveloperService.check_scope("tasks:write", scopes)

    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.due_date is not None:
        task.due_date = payload.due_date
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.status is not None:
        task.status = payload.status
    if payload.category is not None:
        task.category = payload.category
    if payload.project_id is not None:
        task.project_id = payload.project_id

    now = datetime.now(timezone.utc)
    task.updated_at = now
    db.commit()
    db.refresh(task)

    # Trigger Webhook
    if task.workspace_id:
        event_name = "task.completed" if task.status in ("completed", "done") else "task.updated"
        DeveloperService.trigger_webhook_event(
            db=db,
            workspace_id=task.workspace_id,
            event_type=event_name,
            payload={
                "event": event_name,
                "task_id": task.id,
                "title": task.title,
                "status": task.status,
                "timestamp": now.isoformat()
            }
        )

    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def public_delete_task(
    task_id: str,
    auth: Tuple[User, DeveloperCredential, List[str]] = Depends(authenticate_public_api),
    db: Session = Depends(get_db),
):
    user, cred, scopes = auth
    DeveloperService.check_scope("tasks:write", scopes)

    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    ws_id = task.workspace_id
    db.delete(task)
    db.commit()

    if ws_id:
        DeveloperService.trigger_webhook_event(
            db=db,
            workspace_id=ws_id,
            event_type="task.deleted",
            payload={"event": "task.deleted", "task_id": task_id}
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# PROJECTS
@router.get("/projects", response_model=List[PublicProjectResponse])
def public_list_projects(
    auth: Tuple[User, DeveloperCredential, List[str]] = Depends(authenticate_public_api),
    db: Session = Depends(get_db),
):
    user, cred, scopes = auth
    DeveloperService.check_scope("projects:read", scopes)

    app = cred.application
    workspace_id = app.workspace_id if app else None
    if not workspace_id:
        member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
        workspace_id = member.workspace_id if member else None

    if not workspace_id:
        return []

    return db.query(Project).filter(Project.workspace_id == workspace_id).all()

# ANALYTICS
@router.get("/analytics/portfolio", response_model=PortfolioHealthResponse)
def public_get_portfolio_analytics(
    auth: Tuple[User, DeveloperCredential, List[str]] = Depends(authenticate_public_api),
    db: Session = Depends(get_db),
):
    user, cred, scopes = auth
    DeveloperService.check_scope("analytics:read", scopes)

    app = cred.application
    workspace_id = app.workspace_id if app else None
    if not workspace_id:
        member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
        workspace_id = member.workspace_id if member else None

    if not workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found for this user/application")

    return EnterpriseAnalyticsService.get_portfolio_health(db, workspace_id)
