from datetime import datetime, timezone, date
import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.board import Board, BoardColumn, BoardView
from app.models.task import Task
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember, Activity
from app.models.project import Project, ProjectMember
from app.models.organization import Organization, OrganizationMember
from app.schemas.board import (
    BoardCreate,
    BoardUpdate,
    BoardResponse,
    BoardDataResponse,
    BoardColumnCreate,
    BoardColumnUpdate,
    BoardColumnResponse,
    BoardColumnData,
    BoardColumnReorderRequest,
    TaskPositionUpdate,
    TaskBulkMoveRequest,
)
from app.schemas.task import TaskResponse
from app.services.task_service import build_task_response, parse_is_overdue, rollup_subtask_progress


DEFAULT_COLUMNS = [
    {"name": "To Do", "status_value": "Todo", "color": "#64748b", "position": 0},
    {"name": "In Progress", "status_value": "In Progress", "color": "#3b82f6", "position": 1},
    {"name": "In Review", "status_value": "Review", "color": "#f59e0b", "position": 2},
    {"name": "Done", "status_value": "Completed", "color": "#10b981", "position": 3},
]

def log_board_activity(
    db: Session,
    board: Board,
    user_id: int,
    action: str,
    details: str
):
    """Log activity to workspace activity feed if board belongs to a workspace."""
    if board.workspace_id:
        try:
            act = Activity(
                workspace_id=board.workspace_id,
                user_id=user_id,
                action=action,
                details=details,
                project_id=board.project_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(act)
        except Exception:
            pass

def authorize_board_access(
    db: Session,
    board: Board,
    user: User,
    action: str = "read"
) -> bool:
    """Validate tenant boundaries and RBAC for board operations."""
    if board.owner_id == user.id:
        return True

    # If visibility is explicitly private, only owner can view or edit
    if board.visibility == "private" and board.owner_id != user.id:
        return False

    # Check workspace membership
    if board.workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == board.workspace_id).first()
        if ws and ws.owner_id == user.id:
            return True
        mem = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == board.workspace_id,
            WorkspaceMember.user_id == user.id
        ).first()
        if mem:
            return True

    # Check project membership
    if board.project_id:
        proj = db.query(Project).filter(Project.id == board.project_id).first()
        if proj and proj.owner_id == user.id:
            return True
        pm = db.query(ProjectMember).filter(
            ProjectMember.project_id == board.project_id,
            ProjectMember.user_id == user.id
        ).first()
        if pm:
            return True

    # Check organization membership
    if board.organization_id:
        org = db.query(Organization).filter(Organization.id == board.organization_id).first()
        if org and org.owner_id == user.id:
            return True
        om = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == board.organization_id,
            OrganizationMember.user_id == user.id
        ).first()
        if om:
            return True

    return False

def get_board_or_404(
    db: Session,
    board_id: str,
    user: User,
    include_archived: bool = True
) -> Board:
    """Retrieve board ensuring tenant isolation; return 404 on violation."""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found.")
    if not include_archived and board.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found.")
    if not authorize_board_access(db, board, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found.")
    return board

def build_column_response(col: BoardColumn, task_count: int = 0) -> BoardColumnResponse:
    """Format BoardColumn into standard API response with computed task count."""
    return BoardColumnResponse(
        id=col.id,
        board_id=col.board_id,
        name=col.name,
        status_value=col.status_value,
        position=col.position,
        color=col.color,
        description=col.description,
        wip_limit=col.wip_limit,
        is_visible=col.is_visible,
        task_count=task_count,
        created_at=col.created_at,
        updated_at=col.updated_at
    )

def build_board_response(board: Board) -> BoardResponse:
    """Format Board into standard API response with ordered columns."""
    columns_resp = [build_column_response(c) for c in (board.columns or [])]
    return BoardResponse(
        id=board.id,
        name=board.name,
        description=board.description,
        board_type=board.board_type,
        visibility=board.visibility,
        owner_id=board.owner_id,
        workspace_id=board.workspace_id,
        project_id=board.project_id,
        organization_id=board.organization_id,
        settings=board.settings,
        is_default=board.is_default,
        is_archived=board.is_archived,
        archived_at=board.archived_at,
        columns=columns_resp,
        created_at=board.created_at,
        updated_at=board.updated_at
    )

def create_board(
    db: Session,
    board_in: BoardCreate,
    current_user: User
) -> BoardResponse:
    """Create a new board, its default columns, and an associated default Kanban view."""
    name = board_in.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Board name cannot be empty."
        )

    # Validate workspace membership if linked
    if board_in.workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == board_in.workspace_id).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found.")
        is_mem = (ws.owner_id == current_user.id) or db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == board_in.workspace_id,
            WorkspaceMember.user_id == current_user.id
        ).first() is not None
        if not is_mem:
            raise HTTPException(status_code=403, detail="Not authorized for this workspace.")

    now = datetime.now(timezone.utc)
    board_id = f"board-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"

    board = Board(
        id=board_id,
        organization_id=board_in.organization_id,
        workspace_id=board_in.workspace_id,
        project_id=board_in.project_id,
        owner_id=current_user.id,
        name=name,
        description=board_in.description.strip() if board_in.description else None,
        board_type=board_in.board_type or "kanban",
        visibility=board_in.visibility or "workspace",
        is_default=False,
        is_archived=False,
        created_at=now,
        updated_at=now
    )
    board.settings = board_in.settings or {}
    db.add(board)
    db.flush()

    # Generate columns (custom or default)
    columns_to_add = board_in.initial_columns if board_in.initial_columns else DEFAULT_COLUMNS
    for idx, c in enumerate(columns_to_add):
        col_id = f"col-{int(now.timestamp()*1000)}-{idx}-{uuid.uuid4().hex[:4]}"
        if isinstance(c, BoardColumnCreate):
            col = BoardColumn(
                id=col_id,
                board_id=board.id,
                name=c.name.strip(),
                status_value=c.status_value.strip(),
                position=c.position if c.position is not None else idx,
                color=c.color or "#6366f1",
                description=c.description,
                wip_limit=c.wip_limit,
                is_visible=c.is_visible,
                created_at=now,
                updated_at=now
            )
        else:
            col = BoardColumn(
                id=col_id,
                board_id=board.id,
                name=c["name"],
                status_value=c["status_value"],
                position=c["position"],
                color=c["color"],
                created_at=now,
                updated_at=now
            )
        db.add(col)

    # Generate default BoardView
    view_id = f"view-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"
    default_view = BoardView(
        id=view_id,
        board_id=board.id,
        workspace_id=board.workspace_id,
        project_id=board.project_id,
        organization_id=board.organization_id,
        owner_id=current_user.id,
        name="Default Kanban",
        view_type="kanban",
        visibility=board.visibility,
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db.add(default_view)

    db.commit()
    db.refresh(board)
    log_board_activity(db, board, current_user.id, "BOARD_CREATED", f"Created board '{board.name}'.")
    return build_board_response(board)

def list_boards(
    db: Session,
    current_user: User,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    search: Optional[str] = None,
    is_archived: bool = False
) -> List[BoardResponse]:
    """Retrieve boards accessible to the authenticated user."""
    query = db.query(Board).filter(Board.is_archived == is_archived)

    if workspace_id:
        query = query.filter(Board.workspace_id == workspace_id)
    elif project_id:
        query = query.filter(Board.project_id == project_id)
    elif organization_id:
        query = query.filter(Board.organization_id == organization_id)
    else:
        # Default: user's personal or accessible boards
        query = query.filter(
            or_(
                Board.owner_id == current_user.id,
                Board.visibility != "private"
            )
        )

    if search:
        query = query.filter(Board.name.ilike(f"%{search.strip()}%"))

    boards = query.order_by(Board.created_at.desc()).all()
    # Enforce tenant isolation
    authorized = [b for b in boards if authorize_board_access(db, b, current_user)]
    return [build_board_response(b) for b in authorized]

def update_board(
    db: Session,
    board_id: str,
    board_in: BoardUpdate,
    current_user: User
) -> BoardResponse:
    """Update board metadata, visibility, or settings."""
    board = get_board_or_404(db, board_id, current_user)
    now = datetime.now(timezone.utc)

    if board_in.name is not None:
        name = board_in.name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Board name cannot be empty.")
        board.name = name

    if board_in.description is not None:
        board.description = board_in.description.strip()
    if board_in.board_type is not None:
        board.board_type = board_in.board_type
    if board_in.visibility is not None:
        board.visibility = board_in.visibility
    if board_in.is_default is not None:
        board.is_default = board_in.is_default
    if board_in.settings is not None:
        board.settings = board_in.settings

    if board_in.is_archived is not None and board_in.is_archived != board.is_archived:
        board.is_archived = board_in.is_archived
        board.archived_at = now if board.is_archived else None

    board.updated_at = now
    db.commit()
    db.refresh(board)
    log_board_activity(db, board, current_user.id, "BOARD_UPDATED", f"Updated board '{board.name}'.")
    return build_board_response(board)

def delete_board(db: Session, board_id: str, current_user: User) -> None:
    """Delete board record and its columns/views; preserves project/workspace tasks safely."""
    board = get_board_or_404(db, board_id, current_user)
    log_board_activity(db, board, current_user.id, "BOARD_DELETED", f"Deleted board '{board.name}'.")
    db.delete(board)
    db.commit()

def archive_board(db: Session, board_id: str, current_user: User) -> BoardResponse:
    """Archive board."""
    board = get_board_or_404(db, board_id, current_user)
    board.is_archived = True
    board.archived_at = datetime.now(timezone.utc)
    board.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(board)
    return build_board_response(board)

def restore_board(db: Session, board_id: str, current_user: User) -> BoardResponse:
    """Restore archived board."""
    board = get_board_or_404(db, board_id, current_user)
    board.is_archived = False
    board.archived_at = None
    board.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(board)
    return build_board_response(board)

# --- Board Columns Management ---

def create_board_column(
    db: Session,
    board_id: str,
    col_in: BoardColumnCreate,
    current_user: User
) -> BoardColumnResponse:
    """Add a new column to the board."""
    board = get_board_or_404(db, board_id, current_user)
    now = datetime.now(timezone.utc)
    col_id = f"col-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"

    # Determine position if not set
    position = col_in.position
    if position == 0 and board.columns:
        position = max(c.position for c in board.columns) + 1

    col = BoardColumn(
        id=col_id,
        board_id=board.id,
        name=col_in.name.strip(),
        status_value=col_in.status_value.strip(),
        position=position,
        color=col_in.color or "#6366f1",
        description=col_in.description,
        wip_limit=col_in.wip_limit,
        is_visible=col_in.is_visible,
        created_at=now,
        updated_at=now
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    return build_column_response(col)

def list_board_columns(
    db: Session,
    board_id: str,
    current_user: User
) -> List[BoardColumnResponse]:
    """Retrieve all columns for a board with task counts."""
    board = get_board_or_404(db, board_id, current_user)
    columns = db.query(BoardColumn).filter(
        BoardColumn.board_id == board.id
    ).order_by(BoardColumn.position.asc()).all()

    # Calculate task counts for each column
    tasks_query = db.query(Task).filter(Task.is_deleted == False, Task.is_archived == False)
    if board.workspace_id:
        tasks_query = tasks_query.filter(Task.workspace_id == board.workspace_id)
    elif board.project_id:
        tasks_query = tasks_query.filter(Task.project_id == board.project_id)
    else:
        tasks_query = tasks_query.filter(Task.user_id == current_user.id)

    tasks = tasks_query.all()
    results = []
    for col in columns:
        count = sum(1 for t in tasks if (t.status or "").lower() == col.status_value.lower())
        results.append(build_column_response(col, task_count=count))

    return results

def update_board_column(
    db: Session,
    board_id: str,
    column_id: str,
    col_in: BoardColumnUpdate,
    current_user: User
) -> BoardColumnResponse:
    """Update column attributes (name, status mapping, color, WIP limit)."""
    board = get_board_or_404(db, board_id, current_user)
    col = db.query(BoardColumn).filter(
        BoardColumn.id == column_id,
        BoardColumn.board_id == board.id
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found.")

    now = datetime.now(timezone.utc)
    if col_in.name is not None:
        col.name = col_in.name.strip()
    if col_in.status_value is not None:
        col.status_value = col_in.status_value.strip()
    if col_in.position is not None:
        col.position = col_in.position
    if col_in.color is not None:
        col.color = col_in.color
    if col_in.description is not None:
        col.description = col_in.description
    if col_in.wip_limit is not None:
        col.wip_limit = col_in.wip_limit
    if col_in.is_visible is not None:
        col.is_visible = col_in.is_visible

    col.updated_at = now
    db.commit()
    db.refresh(col)
    return build_column_response(col)

def delete_board_column(
    db: Session,
    board_id: str,
    column_id: str,
    target_column_id: Optional[str],
    current_user: User
) -> None:
    """Delete a column; remaps tasks to target column if tasks exist."""
    board = get_board_or_404(db, board_id, current_user)
    col = db.query(BoardColumn).filter(
        BoardColumn.id == column_id,
        BoardColumn.board_id == board.id
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found.")

    # Check if tasks are mapped to this column's status
    tasks_query = db.query(Task).filter(
        Task.is_deleted == False,
        Task.status.ilike(col.status_value)
    )
    if board.workspace_id:
        tasks_query = tasks_query.filter(Task.workspace_id == board.workspace_id)
    elif board.project_id:
        tasks_query = tasks_query.filter(Task.project_id == board.project_id)
    else:
        tasks_query = tasks_query.filter(Task.user_id == current_user.id)

    tasks_in_col = tasks_query.all()
    if tasks_in_col:
        if target_column_id:
            target_col = db.query(BoardColumn).filter(
                BoardColumn.id == target_column_id,
                BoardColumn.board_id == board.id
            ).first()
            if not target_col:
                raise HTTPException(status_code=400, detail="Target reassignment column not found.")
            for t in tasks_in_col:
                t.status = target_col.status_value
                t.updated_at = datetime.now(timezone.utc)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{col.name}' contains {len(tasks_in_col)} task(s). Specify target_column_id to reassign tasks."
            )

    db.delete(col)
    db.commit()

def reorder_board_columns(
    db: Session,
    board_id: str,
    reorder_in: BoardColumnReorderRequest,
    current_user: User
) -> List[BoardColumnResponse]:
    """Reorder column display sequence on the board."""
    board = get_board_or_404(db, board_id, current_user)
    for item in reorder_in.items:
        col = db.query(BoardColumn).filter(
            BoardColumn.id == item.id,
            BoardColumn.board_id == board.id
        ).first()
        if col:
            col.position = item.position
            col.updated_at = datetime.now(timezone.utc)

    db.commit()
    return list_board_columns(db, board_id, current_user)

# --- Board Data & Task Movement ---

def get_board_data(
    db: Session,
    board_id: str,
    current_user: User
) -> BoardDataResponse:
    """Retrieve full board data: columns, tasks grouped into columns, and summary metrics."""
    board = get_board_or_404(db, board_id, current_user)
    columns = db.query(BoardColumn).filter(
        BoardColumn.board_id == board.id,
        BoardColumn.is_visible == True
    ).order_by(BoardColumn.position.asc()).all()

    # Load non-deleted tasks
    tasks_query = db.query(Task).filter(Task.is_deleted == False, Task.is_archived == False)
    if board.workspace_id:
        tasks_query = tasks_query.filter(Task.workspace_id == board.workspace_id)
    elif board.project_id:
        tasks_query = tasks_query.filter(Task.project_id == board.project_id)
    else:
        tasks_query = tasks_query.filter(
            or_(
                Task.user_id == current_user.id,
                Task.assignee_id == current_user.id
            )
        )

    all_tasks = tasks_query.order_by(Task.sort_order.asc(), Task.created_at.desc()).all()

    columns_data = []
    total_tasks = len(all_tasks)
    completed_tasks = 0
    overdue_tasks = 0
    wip_violations = []

    for col in columns:
        col_tasks = [t for t in all_tasks if (t.status or "").lower() == col.status_value.lower()]
        count = len(col_tasks)
        if col.wip_limit and count > col.wip_limit:
            wip_violations.append({"column_id": col.id, "name": col.name, "limit": col.wip_limit, "count": count})

        if col.status_value.lower() == "completed":
            completed_tasks += count

        for t in col_tasks:
            if parse_is_overdue(t):
                overdue_tasks += 1

        task_responses = [build_task_response(t) for t in col_tasks]
        col_resp = build_column_response(col, task_count=count)
        columns_data.append(BoardColumnData(column=col_resp, tasks=task_responses, task_count=count))

    summary = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0,
        "wip_violations": wip_violations,
    }

    return BoardDataResponse(
        board=build_board_response(board),
        columns=columns_data,
        summary=summary
    )

def move_task_position(
    db: Session,
    board_id: str,
    task_id: str,
    move_in: TaskPositionUpdate,
    current_user: User
) -> TaskResponse:
    """Move a task to a new column and position (Kanban drag-and-drop)."""
    board = get_board_or_404(db, board_id, current_user)
    task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    new_status = move_in.destination_status
    if move_in.destination_column_id:
        target_col = db.query(BoardColumn).filter(
            BoardColumn.id == move_in.destination_column_id,
            BoardColumn.board_id == board.id
        ).first()
        if not target_col:
            raise HTTPException(status_code=400, detail="Destination column not found.")
        new_status = target_col.status_value

    now = datetime.now(timezone.utc)
    old_status = task.status

    if new_status and new_status != old_status:
        task.status = new_status
        if new_status.lower() == "completed":
            task.completed_at = now
            task.progress_percent = 100.0
        elif old_status.lower() == "completed" and new_status.lower() != "completed":
            task.completed_at = None

    task.sort_order = move_in.destination_position
    task.updated_at = now
    db.commit()
    db.refresh(task)

    if task.parent_task_id:
        rollup_subtask_progress(db, task.parent_task_id)

    log_board_activity(db, board, current_user.id, "TASK_MOVED", f"Moved task '{task.title}' to {task.status}.")
    return build_task_response(task)

def bulk_move_tasks(
    db: Session,
    board_id: str,
    bulk_in: TaskBulkMoveRequest,
    current_user: User
) -> Dict[str, Any]:
    """Bulk move multiple tasks to a column/status."""
    board = get_board_or_404(db, board_id, current_user)
    new_status = bulk_in.destination_status
    if bulk_in.destination_column_id:
        target_col = db.query(BoardColumn).filter(
            BoardColumn.id == bulk_in.destination_column_id,
            BoardColumn.board_id == board.id
        ).first()
        if not target_col:
            raise HTTPException(status_code=400, detail="Destination column not found.")
        new_status = target_col.status_value

    if not new_status:
        raise HTTPException(status_code=400, detail="Destination status or column required.")

    tasks = db.query(Task).filter(
        Task.id.in_(bulk_in.task_ids),
        Task.is_deleted == False
    ).all()

    now = datetime.now(timezone.utc)
    for t in tasks:
        old_status = t.status
        t.status = new_status
        if new_status.lower() == "completed":
            t.completed_at = now
            t.progress_percent = 100.0
        elif old_status.lower() == "completed" and new_status.lower() != "completed":
            t.completed_at = None
        t.updated_at = now

    db.commit()
    return {"status": "success", "moved_count": len(tasks), "new_status": new_status}
