from datetime import datetime, timezone, date
import uuid
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.board import SavedFilter
from app.models.task import Task
from app.models.user import User
from app.schemas.board import (
    SavedFilterCreate,
    SavedFilterUpdate,
    SavedFilterResponse,
    FilterApplyRequest,
)
from app.schemas.task import TaskResponse
from app.services.task_service import build_task_response, authorize_task_access


ALLOWED_FILTER_FIELDS = {
    "title": str,
    "description": str,
    "category": str,
    "status": str,
    "priority": str,
    "due_date": str,
    "assignee_id": int,
    "user_id": int,
    "workspace_id": int,
    "project_id": int,
    "progress_percent": float,
    "is_archived": bool,
    "is_deleted": bool,
}

ALLOWED_OPERATORS = {
    "equals",
    "not_equals",
    "contains",
    "not_contains",
    "is_empty",
    "is_not_empty",
    "greater_than",
    "less_than",
    "before",
    "after",
    "in",
    "not_in",
}

def build_filter_clause(field_name: str, operator: str, value: Any):
    """Safely compile a single validated condition into a SQLAlchemy BinaryExpression."""
    if field_name not in ALLOWED_FILTER_FIELDS:
        return None

    if operator not in ALLOWED_OPERATORS:
        return None

    col = getattr(Task, field_name, None)
    if col is None:
        return None

    if operator == "equals":
        return col == value
    elif operator == "not_equals":
        return col != value
    elif operator == "contains":
        return col.ilike(f"%{str(value).strip()}%")
    elif operator == "not_contains":
        return ~col.ilike(f"%{str(value).strip()}%")
    elif operator == "is_empty":
        return or_(col == None, col == "")
    elif operator == "is_not_empty":
        return and_(col != None, col != "")
    elif operator == "greater_than" or operator == "after":
        return col > value
    elif operator == "less_than" or operator == "before":
        return col < value
    elif operator == "in":
        if isinstance(value, list) and value:
            return col.in_(value)
    elif operator == "not_in":
        if isinstance(value, list) and value:
            return ~col.in_(value)

    return None

def apply_conditions_to_query(query, query_config: Dict[str, Any]):
    """Recursively apply structured filter conditions safely to an active SQLAlchemy query."""
    if not query_config or not isinstance(query_config, dict):
        return query

    conditions = query_config.get("conditions", [])
    if not conditions or not isinstance(conditions, list):
        return query

    match_type = query_config.get("match_type", "ALL").upper()  # ALL (AND) or ANY (OR)
    clauses = []

    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        field = cond.get("field")
        op = cond.get("operator")
        val = cond.get("value")

        clause = build_filter_clause(field, op, val)
        if clause is not None:
            clauses.append(clause)

    if clauses:
        if match_type == "ANY":
            query = query.filter(or_(*clauses))
        else:
            query = query.filter(and_(*clauses))

    return query

def create_saved_filter(
    db: Session,
    filter_in: SavedFilterCreate,
    current_user: User
) -> SavedFilterResponse:
    """Create a persistent saved filter."""
    now = datetime.now(timezone.utc)
    filter_id = f"filter-{int(now.timestamp()*1000)}-{uuid.uuid4().hex[:6]}"

    saved_filter = SavedFilter(
        id=filter_id,
        user_id=current_user.id,
        name=filter_in.name.strip(),
        description=filter_in.description.strip() if filter_in.description else None,
        filter_type=filter_in.filter_type or "task",
        workspace_id=filter_in.workspace_id,
        project_id=filter_in.project_id,
        is_shared=filter_in.is_shared,
        created_at=now,
        updated_at=now
    )
    saved_filter.query_config = filter_in.query_config or {}

    db.add(saved_filter)
    db.commit()
    db.refresh(saved_filter)
    return SavedFilterResponse.model_validate(saved_filter)

def list_saved_filters(
    db: Session,
    current_user: User,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None
) -> List[SavedFilterResponse]:
    """List saved filters owned by the user or shared within the workspace/project."""
    query = db.query(SavedFilter)

    if workspace_id:
        query = query.filter(
            or_(
                SavedFilter.user_id == current_user.id,
                and_(SavedFilter.workspace_id == workspace_id, SavedFilter.is_shared == True)
            )
        )
    elif project_id:
        query = query.filter(
            or_(
                SavedFilter.user_id == current_user.id,
                and_(SavedFilter.project_id == project_id, SavedFilter.is_shared == True)
            )
        )
    else:
        query = query.filter(SavedFilter.user_id == current_user.id)

    filters = query.order_by(SavedFilter.created_at.desc()).all()
    return [SavedFilterResponse.model_validate(f) for f in filters]

def get_saved_filter_or_404(
    db: Session,
    filter_id: str,
    current_user: User
) -> SavedFilter:
    """Retrieve saved filter with authorization check; shields existence on violation with 404."""
    sf = db.query(SavedFilter).filter(SavedFilter.id == filter_id).first()
    if not sf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found.")

    # Access check: owner or shared in same scope
    if sf.user_id != current_user.id and not sf.is_shared:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found.")

    return sf

def update_saved_filter(
    db: Session,
    filter_id: str,
    filter_in: SavedFilterUpdate,
    current_user: User
) -> SavedFilterResponse:
    """Update saved filter (only owner can modify configuration)."""
    sf = get_saved_filter_or_404(db, filter_id, current_user)
    if sf.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit another user's filter.")

    now = datetime.now(timezone.utc)
    if filter_in.name is not None:
        sf.name = filter_in.name.strip()
    if filter_in.description is not None:
        sf.description = filter_in.description.strip()
    if filter_in.query_config is not None:
        sf.query_config = filter_in.query_config
    if filter_in.is_shared is not None:
        sf.is_shared = filter_in.is_shared

    sf.updated_at = now
    db.commit()
    db.refresh(sf)
    return SavedFilterResponse.model_validate(sf)

def delete_saved_filter(db: Session, filter_id: str, current_user: User) -> None:
    """Delete a saved filter."""
    sf = get_saved_filter_or_404(db, filter_id, current_user)
    if sf.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete another user's filter.")

    db.delete(sf)
    db.commit()

def apply_filter(
    db: Session,
    apply_in: FilterApplyRequest,
    current_user: User
) -> List[TaskResponse]:
    """Execute dynamic or saved filter against tasks."""
    query_config = {}
    if apply_in.filter_id:
        sf = get_saved_filter_or_404(db, apply_in.filter_id, current_user)
        query_config = sf.query_config
    elif apply_in.query_config:
        query_config = apply_in.query_config

    query = db.query(Task).filter(Task.is_deleted == False)

    if apply_in.workspace_id:
        query = query.filter(Task.workspace_id == apply_in.workspace_id)
    elif apply_in.project_id:
        query = query.filter(Task.project_id == apply_in.project_id)
    else:
        query = query.filter(
            or_(
                Task.user_id == current_user.id,
                Task.assignee_id == current_user.id
            )
        )

    # Apply compiled filter conditions
    query = apply_conditions_to_query(query, query_config)

    tasks = query.order_by(Task.created_at.desc()).limit(200).all()
    # Filter to authorized tasks
    authorized = [t for t in tasks if authorize_task_access(db, t, current_user)]
    return [build_task_response(t) for t in authorized]
