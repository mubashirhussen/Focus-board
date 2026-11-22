from datetime import datetime, timezone
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc

from app.db.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.collaboration import Workspace, WorkspaceMember, Project
from app.schemas.search import SearchResponse, SearchResultItem, SearchFacets
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/search", tags=["Global Search"])

@router.get("", response_model=SearchResponse)
def global_search(
    q: Optional[str] = Query(None, description="Search term for title, description, or name"),
    type: Optional[str] = Query("ALL", description="Filter by resource type: ALL, TASK, PROJECT, WORKSPACE"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    workspace_id: Optional[int] = Query(None, description="Scope search to specific workspace"),
    project_id: Optional[int] = Query(None, description="Scope search to specific project"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search across Tasks, Projects, and Workspaces with strict multi-tenant authorization.
    Users only see resources they own or have explicit membership in.
    """
    # 1. Determine user accessible workspaces
    memberships = db.query(WorkspaceMember.workspace_id).filter(WorkspaceMember.user_id == current_user.id).all()
    accessible_workspace_ids = [m[0] for m in memberships]

    # If workspace_id filter is requested, verify user has access
    if workspace_id is not None:
        if workspace_id not in accessible_workspace_ids:
            return SearchResponse(
                results=[],
                total=0,
                page=page,
                page_size=page_size,
                facets=SearchFacets(by_type={}, by_status={})
            )
        target_workspace_ids = [workspace_id]
    else:
        target_workspace_ids = accessible_workspace_ids

    search_term = f"%{q.strip()}%" if q and q.strip() else None
    target_type = (type or "ALL").upper()

    all_results: List[SearchResultItem] = []
    by_type_counts: Dict[str, int] = {"TASK": 0, "PROJECT": 0, "WORKSPACE": 0}
    by_status_counts: Dict[str, int] = {}

    # 2. Search Tasks
    if target_type in ["ALL", "TASK"]:
        task_query = db.query(Task)
        
        # Authorization constraint: User owns the task OR it belongs to an accessible workspace
        if target_workspace_ids:
            task_auth_condition = or_(
                Task.user_id == current_user.id,
                Task.workspace_id.in_(target_workspace_ids)
            )
        else:
            task_auth_condition = (Task.user_id == current_user.id)
            
        task_query = task_query.filter(task_auth_condition)

        if workspace_id is not None:
            task_query = task_query.filter(Task.workspace_id == workspace_id)
        if project_id is not None:
            task_query = task_query.filter(Task.project_id == project_id)
        if status and status.lower() != "all":
            task_query = task_query.filter(Task.status.ilike(status))
        if priority and priority.lower() != "all":
            task_query = task_query.filter(Task.priority.ilike(priority))
        if category and category.lower() != "all":
            task_query = task_query.filter(Task.category.ilike(category))

        if search_term:
            task_query = task_query.filter(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                    Task.category.ilike(search_term),
                )
            )

        tasks = task_query.all()
        by_type_counts["TASK"] = len(tasks)
        for t in tasks:
            st = t.status or "Unknown"
            by_status_counts[st] = by_status_counts.get(st, 0) + 1
            all_results.append(SearchResultItem(
                id=str(t.id),
                type="TASK",
                title=t.title,
                description=t.description,
                status=t.status,
                priority=t.priority,
                category=t.category,
                workspace_id=t.workspace_id,
                project_id=t.project_id,
                created_at=t.created_at,
                url_path=f"/?task_id={t.id}" if not t.workspace_id else f"/workspaces/{t.workspace_id}?task_id={t.id}"
            ))

    # 3. Search Projects
    if target_type in ["ALL", "PROJECT"] and target_workspace_ids:
        project_query = db.query(Project).filter(Project.workspace_id.in_(target_workspace_ids))

        if workspace_id is not None:
            project_query = project_query.filter(Project.workspace_id == workspace_id)
        if status and status.lower() != "all":
            project_query = project_query.filter(Project.status.ilike(status))
        if search_term:
            project_query = project_query.filter(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                )
            )

        projects = project_query.all()
        by_type_counts["PROJECT"] = len(projects)
        for p in projects:
            st = p.status or "ACTIVE"
            by_status_counts[st] = by_status_counts.get(st, 0) + 1
            all_results.append(SearchResultItem(
                id=str(p.id),
                type="PROJECT",
                title=p.name,
                description=p.description,
                status=p.status,
                priority=None,
                category="Project",
                workspace_id=p.workspace_id,
                project_id=p.id,
                created_at=p.created_at,
                url_path=f"/workspaces/{p.workspace_id}?project_id={p.id}"
            ))

    # 4. Search Workspaces
    if target_type in ["ALL", "WORKSPACE"] and target_workspace_ids:
        ws_query = db.query(Workspace).filter(Workspace.id.in_(target_workspace_ids))
        if search_term:
            ws_query = ws_query.filter(
                or_(
                    Workspace.name.ilike(search_term),
                    Workspace.description.ilike(search_term),
                )
            )
        workspaces = ws_query.all()
        by_type_counts["WORKSPACE"] = len(workspaces)
        for w in workspaces:
            all_results.append(SearchResultItem(
                id=str(w.id),
                type="WORKSPACE",
                title=w.name,
                description=w.description,
                status="ACTIVE",
                priority=None,
                category="Workspace",
                workspace_id=w.id,
                project_id=None,
                created_at=w.created_at,
                url_path=f"/workspaces/{w.id}"
            ))

    # Sort results
    reverse = (sort_order.lower() == "desc")
    all_results.sort(key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=reverse)

    total = len(all_results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = all_results[start_idx:end_idx]

    return SearchResponse(
        results=paginated_results,
        total=total,
        page=page,
        page_size=page_size,
        facets=SearchFacets(by_type=by_type_counts, by_status=by_status_counts)
    )
