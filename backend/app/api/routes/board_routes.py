from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.board import (
    BoardCreate,
    BoardUpdate,
    BoardSettingsUpdate,
    BoardResponse,
    BoardDataResponse,
    BoardColumnCreate,
    BoardColumnUpdate,
    BoardColumnResponse,
    BoardColumnReorderRequest,
    TaskPositionUpdate,
    TaskBulkMoveRequest,
)
from app.schemas.task import TaskResponse
from app.services import board_service

router = APIRouter(prefix="/boards", tags=["Boards & Kanban"])

# --- Board Endpoints ---

@router.get("", response_model=List[BoardResponse])
def get_boards(
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    search: Optional[str] = Query(None, description="Search by board name"),
    is_archived: bool = Query(False, description="Filter by archived state"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve boards accessible to the user."""
    return board_service.list_boards(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
        organization_id=organization_id,
        search=search,
        is_archived=is_archived
    )

@router.post("", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
def create_board(
    board_in: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new board with default or custom columns and default Kanban view."""
    return board_service.create_board(db=db, board_in=board_in, current_user=current_user)

@router.get("/{board_id}", response_model=BoardResponse)
def get_board(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve board details and its ordered columns."""
    board = board_service.get_board_or_404(db, board_id, current_user)
    return board_service.build_board_response(board)

@router.patch("/{board_id}", response_model=BoardResponse)
def update_board(
    board_id: str,
    board_in: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update board metadata, visibility, or settings."""
    return board_service.update_board(db=db, board_id=board_id, board_in=board_in, current_user=current_user)

@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete board record safely without deleting project or workspace tasks."""
    board_service.delete_board(db=db, board_id=board_id, current_user=current_user)
    return None

@router.post("/{board_id}/archive", response_model=BoardResponse)
def archive_board(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive board."""
    return board_service.archive_board(db=db, board_id=board_id, current_user=current_user)

@router.post("/{board_id}/restore", response_model=BoardResponse)
def restore_board(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore archived board."""
    return board_service.restore_board(db=db, board_id=board_id, current_user=current_user)

@router.get("/{board_id}/data", response_model=BoardDataResponse)
def get_board_data(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full board data: columns, tasks grouped into columns, task counts, and summary."""
    return board_service.get_board_data(db=db, board_id=board_id, current_user=current_user)

@router.get("/{board_id}/settings", response_model=Dict[str, Any])
def get_board_settings(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve board settings configuration."""
    board = board_service.get_board_or_404(db, board_id, current_user)
    return board.settings

@router.patch("/{board_id}/settings", response_model=BoardResponse)
def update_board_settings(
    board_id: str,
    settings_in: BoardSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update board settings configuration."""
    return board_service.update_board(
        db=db,
        board_id=board_id,
        board_in=BoardUpdate(settings=settings_in.settings),
        current_user=current_user
    )

# --- Board Column Endpoints ---

@router.get("/{board_id}/columns", response_model=List[BoardColumnResponse])
def get_board_columns(
    board_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all columns for a board with real-time task counts."""
    return board_service.list_board_columns(db=db, board_id=board_id, current_user=current_user)

@router.post("/{board_id}/columns", response_model=BoardColumnResponse, status_code=status.HTTP_201_CREATED)
def create_board_column(
    board_id: str,
    col_in: BoardColumnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new column to the board."""
    return board_service.create_board_column(db=db, board_id=board_id, col_in=col_in, current_user=current_user)

@router.patch("/{board_id}/columns/{column_id}", response_model=BoardColumnResponse)
def update_board_column(
    board_id: str,
    column_id: str,
    col_in: BoardColumnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update column attributes (name, status mapping, color, WIP limit, visibility)."""
    return board_service.update_board_column(
        db=db,
        board_id=board_id,
        column_id=column_id,
        col_in=col_in,
        current_user=current_user
    )

@router.delete("/{board_id}/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board_column(
    board_id: str,
    column_id: str,
    target_column_id: Optional[str] = Query(None, description="Column ID to reassign active tasks to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a column; remaps tasks to target column if tasks exist."""
    board_service.delete_board_column(
        db=db,
        board_id=board_id,
        column_id=column_id,
        target_column_id=target_column_id,
        current_user=current_user
    )
    return None

@router.post("/{board_id}/columns/reorder", response_model=List[BoardColumnResponse])
def reorder_board_columns(
    board_id: str,
    reorder_in: BoardColumnReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Persist new column display positions."""
    return board_service.reorder_board_columns(
        db=db,
        board_id=board_id,
        reorder_in=reorder_in,
        current_user=current_user
    )

# --- Board Tasks Movement (Kanban Drag-and-Drop) ---

@router.patch("/{board_id}/tasks/{task_id}/position", response_model=TaskResponse)
def move_task_position(
    board_id: str,
    task_id: str,
    move_in: TaskPositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Move a task to a new column and position (Kanban drag-and-drop)."""
    return board_service.move_task_position(
        db=db,
        board_id=board_id,
        task_id=task_id,
        move_in=move_in,
        current_user=current_user
    )

@router.post("/{board_id}/tasks/bulk-move", status_code=status.HTTP_200_OK)
def bulk_move_tasks(
    board_id: str,
    bulk_in: TaskBulkMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk move tasks to a destination column/status."""
    return board_service.bulk_move_tasks(
        db=db,
        board_id=board_id,
        bulk_in=bulk_in,
        current_user=current_user
    )
