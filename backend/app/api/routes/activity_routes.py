from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.activity_service import activity_service
from app.schemas.comment import ActivityEventResponse

router = APIRouter(prefix="/activities", tags=["Activity Feeds & Timeline"])

@router.get("", response_model=List[ActivityEventResponse])
def get_activity_feed(
    entity_type: Optional[str] = Query(None, description="Filter: TASK, PROJECT, BOARD, TEAM, WORKSPACE, ORGANIZATION"),
    entity_id: Optional[str] = Query(None, description="Entity identifier"),
    organization_id: Optional[int] = Query(None, description="Organization ID"),
    workspace_id: Optional[int] = Query(None, description="Workspace ID"),
    project_id: Optional[int] = Query(None, description="Project ID"),
    task_id: Optional[str] = Query(None, description="Task ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_id: Optional[int] = Query(None, description="Filter by actor user ID"),
    from_date: Optional[datetime] = Query(None, description="Earliest activity date"),
    to_date: Optional[datetime] = Query(None, description="Latest activity date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve activity feed with entity, tenant, and date filters."""
    try:
        return activity_service.get_feed(
            db=db,
            current_user=current_user,
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            task_id=task_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor_id=actor_id,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/task/{task_id}", response_model=List[ActivityEventResponse])
def get_task_activity(
    task_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve timeline activity for a specific task."""
    try:
        return activity_service.get_feed(
            db=db, current_user=current_user, entity_type="TASK", entity_id=task_id, skip=skip, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/project/{project_id}", response_model=List[ActivityEventResponse])
def get_project_activity(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve collaboration timeline for a project."""
    try:
        return activity_service.get_feed(
            db=db, current_user=current_user, entity_type="PROJECT", entity_id=str(project_id), skip=skip, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/board/{board_id}", response_model=List[ActivityEventResponse])
def get_board_activity(
    board_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve board movement and column activities."""
    try:
        return activity_service.get_feed(
            db=db, current_user=current_user, entity_type="BOARD", entity_id=str(board_id), skip=skip, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/team/{team_id}", response_model=List[ActivityEventResponse])
def get_team_activity(
    team_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve team collaboration and membership history."""
    try:
        return activity_service.get_feed(
            db=db, current_user=current_user, entity_type="TEAM", entity_id=str(team_id), skip=skip, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/workspace/{workspace_id}", response_model=List[ActivityEventResponse])
def get_workspace_activity(
    workspace_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve workspace audit and activity feed."""
    try:
        return activity_service.get_feed(
            db=db, current_user=current_user, entity_type="WORKSPACE", entity_id=str(workspace_id), skip=skip, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/organization/{org_id}", response_model=List[ActivityEventResponse])
def get_organization_activity(
    org_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve organization-wide activity feed."""
    try:
        return activity_service.get_feed(
            db=db, current_user=current_user, entity_type="ORGANIZATION", entity_id=str(org_id), skip=skip, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
