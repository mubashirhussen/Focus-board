from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.board import (
    ViewCreate,
    ViewUpdate,
    ViewResponse,
    ViewDuplicateRequest,
    ViewDataResponse,
)
from app.services import view_service

router = APIRouter(prefix="/views", tags=["Views"])

@router.get("", response_model=List[ViewResponse])
def get_views(
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    board_id: Optional[str] = Query(None, description="Filter by board ID"),
    view_type: Optional[str] = Query(None, description="Filter by view type (kanban, list, calendar, timeline, table)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve views accessible to the user (owned or shared)."""
    return view_service.list_views(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
        board_id=board_id,
        view_type=view_type
    )

@router.post("", response_model=ViewResponse, status_code=status.HTTP_201_CREATED)
def create_view(
    view_in: ViewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a persistent view configuration."""
    return view_service.create_view(db=db, view_in=view_in, current_user=current_user)

@router.get("/{view_id}", response_model=ViewResponse)
def get_view(
    view_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details and configuration of a view."""
    view = view_service.get_view_or_404(db, view_id, current_user)
    return view_service.build_view_response(view)

@router.patch("/{view_id}", response_model=ViewResponse)
def update_view(
    view_id: str,
    view_in: ViewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update view metadata, filters, sort, group, or column configuration."""
    return view_service.update_view(db=db, view_id=view_id, view_in=view_in, current_user=current_user)

@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_view(
    view_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a view configuration safely without affecting tasks."""
    view_service.delete_view(db=db, view_id=view_id, current_user=current_user)
    return None

@router.post("/{view_id}/duplicate", response_model=ViewResponse, status_code=status.HTTP_201_CREATED)
def duplicate_view(
    view_id: str,
    dup_in: ViewDuplicateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Duplicate an existing view with a new name and copied filters/configurations."""
    return view_service.duplicate_view(db=db, view_id=view_id, dup_in=dup_in, current_user=current_user)

@router.patch("/{view_id}/default", response_model=ViewResponse)
def set_default_view(
    view_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark this view as the default for its scope."""
    return view_service.set_default_view(db=db, view_id=view_id, current_user=current_user)

@router.get("/{view_id}/data", response_model=ViewDataResponse)
def get_view_data(
    view_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute view filters, sorting, and dynamic grouping across tasks."""
    return view_service.get_view_data(db=db, view_id=view_id, current_user=current_user)
