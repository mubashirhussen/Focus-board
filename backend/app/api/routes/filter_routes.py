from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.board import (
    SavedFilterCreate,
    SavedFilterUpdate,
    SavedFilterResponse,
    FilterApplyRequest,
)
from app.schemas.task import TaskResponse
from app.services import filter_service

router = APIRouter(prefix="/filters", tags=["Saved Filters"])

@router.get("", response_model=List[SavedFilterResponse])
def get_saved_filters(
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve saved filters owned by the user or shared within the workspace/project."""
    return filter_service.list_saved_filters(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id
    )

@router.post("", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
def create_saved_filter(
    filter_in: SavedFilterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save a custom filter configuration."""
    return filter_service.create_saved_filter(db=db, filter_in=filter_in, current_user=current_user)

@router.post("/apply", response_model=List[TaskResponse])
def apply_filter(
    apply_in: FilterApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute dynamic or saved filter against tasks with validated operators."""
    return filter_service.apply_filter(db=db, apply_in=apply_in, current_user=current_user)

@router.get("/{filter_id}", response_model=SavedFilterResponse)
def get_saved_filter(
    filter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details of a saved filter."""
    sf = filter_service.get_saved_filter_or_404(db, filter_id, current_user)
    return SavedFilterResponse.model_validate(sf)

@router.patch("/{filter_id}", response_model=SavedFilterResponse)
def update_saved_filter(
    filter_id: str,
    filter_in: SavedFilterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update saved filter configuration."""
    return filter_service.update_saved_filter(
        db=db,
        filter_id=filter_id,
        filter_in=filter_in,
        current_user=current_user
    )

@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_filter(
    filter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a saved filter."""
    filter_service.delete_saved_filter(db=db, filter_id=filter_id, current_user=current_user)
    return None
