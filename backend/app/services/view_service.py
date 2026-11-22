from datetime import datetime, timezone
import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.board import BoardView, Board
from app.models.task import Task
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.project import Project, ProjectMember
from app.schemas.board import (
    ViewCreate,
    ViewUpdate,
    ViewResponse,
    ViewDuplicateRequest,
    ViewDataResponse,
)
from app.schemas.task import TaskResponse
from app.services.task_service import build_task_response, authorize_task_access
from app.services.filter_service import apply_conditions_to_query


VALID_VIEW_TYPES = {"kanban", "list", "calendar", "timeline", "table"}

def authorize_view_access(
    db: Session,
    view: BoardView,
    user: User,
    action: str = "read"
) -> bool:
    """Validate tenant boundaries and RBAC for view access."""
    if view.owner_id == user.id:
        return True

    if view.visibility == "private" and view.owner_id != user.id:
        return False

    if view.workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == view.workspace_id).first()
        if ws and ws.owner_id == user.id:
            return True
        mem = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == view.workspace_id,
            WorkspaceMember.user_id == user.id
        ).first()
        if mem:
            return True

    if view.project_id:
        proj = db.query(Project).filter(Project.id == view.project_id).first()
        if proj and proj.owner_id == user.id:
            return True
        pm = db.query(ProjectMember).filter(
            ProjectMember.project_id == view.project_id,
            ProjectMember.user_id == user.id
        ).first()
        if pm:
            return True

    return False

def get_view_or_404(
    db: Session,
    view_id: str,
    user: User
) -> BoardView:
    """Retrieve view with authorization check; shields existence on violation with 404."""
    view = db.query(BoardView).filter(BoardView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="View not found.")
    if not authorize_view_access(db, view, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="View not found.")
    return view

def build_view_response(view: BoardView) -> ViewResponse:
    """Format BoardView into standard API response."""
    return ViewResponse(
        id=view.id,
        name=view.name,
        view_type=view.view_type,
        visibility=view.visibility,
        owner_id=view.owner_id,
        workspace_id=view.workspace_id,
        project_id=view.project_id,
        organization_id=view.organization_id,
        board_id=view.board_id,
        filters=view.filters,
        sort_config=view.sort_config,
        group_config=view.group_config,
        column_config=view.column_config,
        is_default=view.is_default,
        created_at=view.created_at,
        updated_at=view.updated_at
    )

def create_view(
    db: Session,
    view_in: ViewCreate,
    current_user: User
) -> ViewResponse:
    """Create a persistent view (Kanban, List, Calendar, Timeline, Table)."""
    name = view_in.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="View name cannot be empty.")

    view_type = (view_in.view_type or "kanban").lower()
    if view_type not in VALID_VIEW_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid view type '{view_type}'. Valid types: {VALID_VIEW_TYPES}")

    now = datetime.now(timezone.utc)
    view_id = f"view-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"

    # If is_default, clear other defaults in same scope
    if view_in.is_default:
        clear_defaults(db, view_in.workspace_id, view_in.project_id, current_user.id)

    view = BoardView(
        id=view_id,
        name=name,
        view_type=view_type,
        visibility=view_in.visibility or "workspace",
        workspace_id=view_in.workspace_id,
        project_id=view_in.project_id,
        board_id=view_in.board_id,
        owner_id=current_user.id,
        is_default=view_in.is_default,
        created_at=now,
        updated_at=now
    )
    view.filters = view_in.filters or {}
    view.sort_config = view_in.sort_config or []
    view.group_config = view_in.group_config or {}
    view.column_config = view_in.column_config or []

    db.add(view)
    db.commit()
    db.refresh(view)
    return build_view_response(view)

def clear_defaults(db: Session, workspace_id: Optional[int], project_id: Optional[int], user_id: int):
    """Clear is_default flag on views in the same scope."""
    query = db.query(BoardView)
    if workspace_id:
        query = query.filter(BoardView.workspace_id == workspace_id)
    elif project_id:
        query = query.filter(BoardView.project_id == project_id)
    else:
        query = query.filter(BoardView.owner_id == user_id)

    query.update({"is_default": False})

def list_views(
    db: Session,
    current_user: User,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    board_id: Optional[str] = None,
    view_type: Optional[str] = None
) -> List[ViewResponse]:
    """Retrieve views accessible to the authenticated user."""
    query = db.query(BoardView)

    if board_id:
        query = query.filter(BoardView.board_id == board_id)
    elif workspace_id:
        query = query.filter(
            or_(
                BoardView.workspace_id == workspace_id,
                BoardView.owner_id == current_user.id
            )
        )
    elif project_id:
        query = query.filter(
            or_(
                BoardView.project_id == project_id,
                BoardView.owner_id == current_user.id
            )
        )
    else:
        query = query.filter(BoardView.owner_id == current_user.id)

    if view_type:
        query = query.filter(BoardView.view_type == view_type.lower())

    views = query.order_by(BoardView.created_at.desc()).all()
    authorized = [v for v in views if authorize_view_access(db, v, current_user)]
    return [build_view_response(v) for v in authorized]

def update_view(
    db: Session,
    view_id: str,
    view_in: ViewUpdate,
    current_user: User
) -> ViewResponse:
    """Update view metadata, filters, sort, group, and column visibility."""
    view = get_view_or_404(db, view_id, current_user)
    if view.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit a view owned by another user.")

    now = datetime.now(timezone.utc)
    if view_in.name is not None:
        name = view_in.name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="View name cannot be empty.")
        view.name = name

    if view_in.view_type is not None:
        vt = view_in.view_type.lower()
        if vt not in VALID_VIEW_TYPES:
            raise HTTPException(status_code=422, detail=f"Invalid view type '{vt}'.")
        view.view_type = vt

    if view_in.visibility is not None:
        view.visibility = view_in.visibility
    if view_in.filters is not None:
        view.filters = view_in.filters
    if view_in.sort_config is not None:
        view.sort_config = view_in.sort_config
    if view_in.group_config is not None:
        view.group_config = view_in.group_config
    if view_in.column_config is not None:
        view.column_config = view_in.column_config

    if view_in.is_default is not None:
        if view_in.is_default:
            clear_defaults(db, view.workspace_id, view.project_id, current_user.id)
        view.is_default = view_in.is_default

    view.updated_at = now
    db.commit()
    db.refresh(view)
    return build_view_response(view)

def delete_view(db: Session, view_id: str, current_user: User) -> None:
    """Delete view record safely without affecting tasks."""
    view = get_view_or_404(db, view_id, current_user)
    if view.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete a view owned by another user.")
    db.delete(view)
    db.commit()

def duplicate_view(
    db: Session,
    view_id: str,
    dup_in: ViewDuplicateRequest,
    current_user: User
) -> ViewResponse:
    """Duplicate an existing view with a new name while copying configurations."""
    src = get_view_or_404(db, view_id, current_user)
    now = datetime.now(timezone.utc)
    new_id = f"view-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"

    clone = BoardView(
        id=new_id,
        name=dup_in.new_name.strip(),
        view_type=src.view_type,
        visibility=dup_in.visibility or src.visibility,
        workspace_id=src.workspace_id,
        project_id=src.project_id,
        board_id=src.board_id,
        owner_id=current_user.id,
        is_default=False,
        filters_json=src.filters_json,
        sort_json=src.sort_json,
        group_json=src.group_json,
        column_config_json=src.column_config_json,
        created_at=now,
        updated_at=now
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return build_view_response(clone)

def set_default_view(db: Session, view_id: str, current_user: User) -> ViewResponse:
    """Mark view as the default for its scope."""
    view = get_view_or_404(db, view_id, current_user)
    clear_defaults(db, view.workspace_id, view.project_id, current_user.id)
    view.is_default = True
    view.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(view)
    return build_view_response(view)

def get_view_data(
    db: Session,
    view_id: str,
    current_user: User
) -> ViewDataResponse:
    """Execute view filters, sorting, and dynamic grouping across tasks."""
    view = get_view_or_404(db, view_id, current_user)
    query = db.query(Task).filter(Task.is_deleted == False)

    # Tenancy scoping
    if view.board_id:
        board = db.query(Board).filter(Board.id == view.board_id).first()
        if board:
            if board.workspace_id:
                query = query.filter(Task.workspace_id == board.workspace_id)
            elif board.project_id:
                query = query.filter(Task.project_id == board.project_id)
            else:
                query = query.filter(Task.user_id == board.owner_id)
    elif view.workspace_id:
        query = query.filter(Task.workspace_id == view.workspace_id)
    elif view.project_id:
        query = query.filter(Task.project_id == view.project_id)
    else:
        query = query.filter(
            or_(
                Task.user_id == current_user.id,
                Task.assignee_id == current_user.id
            )
        )

    # 1. Apply View Filters
    query = apply_conditions_to_query(query, view.filters)

    # 2. Apply View Sorting
    sort_rules = view.sort_config
    if sort_rules and isinstance(sort_rules, list):
        for s in sort_rules:
            if isinstance(s, dict):
                f_name = s.get("field")
                direction = s.get("order", "asc").lower()
                col = getattr(Task, f_name, None)
                if col is not None:
                    query = query.order_by(col.desc() if direction == "desc" else col.asc())
    else:
        query = query.order_by(Task.sort_order.asc(), Task.created_at.desc())

    tasks = query.limit(300).all()
    task_responses = [build_task_response(t) for t in tasks if authorize_task_access(db, t, current_user)]

    # 3. Apply View Grouping
    group_cfg = view.group_config
    group_field = group_cfg.get("field") if group_cfg and isinstance(group_cfg, dict) else None

    groups = None
    group_counts = None

    if group_field:
        groups = {}
        group_counts = {}
        for tr in task_responses:
            val = getattr(tr, group_field, None)
            key = str(val) if val is not None else "Unassigned"
            if key not in groups:
                groups[key] = []
                group_counts[key] = 0
            groups[key].append(tr)
            group_counts[key] += 1

    return ViewDataResponse(
        view=build_view_response(view),
        tasks=task_responses,
        groups=groups,
        group_counts=group_counts,
        total=len(task_responses)
    )
