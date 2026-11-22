from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.search import (
    SearchResultItem,
    SearchResponse,
    SearchSuggestionsResponse,
    SearchHistoryItemResponse,
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchResponse,
    AdvancedFilterRequest,
)
from app.api.dependencies import get_current_user
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["Global Search & Intelligence"])

# -------------------------------------------------------------
# 1. Global Search Engine
# -------------------------------------------------------------
@router.get("", response_model=SearchResponse)
def global_search(
    q: Optional[str] = Query(None, description="Search term for title, description, or content"),
    type: Optional[str] = Query("ALL", description="Filter by resource type: ALL, TASK, PROJECT, BOARD, TEAM, WORKSPACE, MEMBER, COMMENT"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    workspace_id: Optional[int] = Query(None, description="Scope search to specific workspace"),
    project_id: Optional[int] = Query(None, description="Scope search to specific project"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query("relevance", description="Sort by: relevance, created_at, title"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search across Tasks, Projects, Boards, Teams, Workspaces, Members, and Comments.
    Enforces strict multi-tenant authorization, relevance ranking, facets, and pagination.
    """
    return search_service.global_search(
        db=db,
        current_user=current_user,
        q=q,
        type=type,
        status=status,
        priority=priority,
        category=category,
        workspace_id=workspace_id,
        project_id=project_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

# -------------------------------------------------------------
# 2. Autocomplete Suggestions & Typeahead
# -------------------------------------------------------------
@router.get("/suggestions", response_model=SearchSuggestionsResponse)
def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Typeahead prefix/query"),
    limit: int = Query(5, ge=1, le=20, description="Max suggestions per entity group"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Instant search suggestions grouped by entity category with permission filtering."""
    return search_service.get_suggestions(
        db=db,
        current_user=current_user,
        q=q,
        limit_per_type=limit,
    )

# -------------------------------------------------------------
# 3. Entity-Specific Searches
# -------------------------------------------------------------
@router.get("/tasks", response_model=List[SearchResultItem])
def search_tasks(
    q: Optional[str] = Query(None, description="Search term"),
    status: Optional[str] = Query(None, description="Filter status"),
    priority: Optional[str] = Query(None, description="Filter priority"),
    category: Optional[str] = Query(None, description="Filter category"),
    assignee_id: Optional[int] = Query(None, description="Filter assignee"),
    workspace_id: Optional[int] = Query(None, description="Filter workspace"),
    project_id: Optional[int] = Query(None, description="Filter project"),
    due_date: Optional[str] = Query(None, description="Filter due date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search tasks accessible to authenticated user."""
    return search_service.search_tasks(
        db=db,
        current_user=current_user,
        q=q,
        status=status,
        priority=priority,
        category=category,
        assignee_id=assignee_id,
        workspace_id=workspace_id,
        project_id=project_id,
        due_date=due_date,
        limit=limit,
    )

@router.get("/projects", response_model=List[SearchResultItem])
def search_projects(
    q: Optional[str] = Query(None, description="Search term"),
    status: Optional[str] = Query(None, description="Filter status"),
    priority: Optional[str] = Query(None, description="Filter priority"),
    category: Optional[str] = Query(None, description="Filter category"),
    workspace_id: Optional[int] = Query(None, description="Filter workspace"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search projects accessible to authenticated user."""
    return search_service.search_projects(
        db=db,
        current_user=current_user,
        q=q,
        status=status,
        priority=priority,
        category=category,
        workspace_id=workspace_id,
        limit=limit,
    )

@router.get("/teams", response_model=List[SearchResultItem])
def search_teams(
    q: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search teams accessible to authenticated user."""
    return search_service.search_teams(
        db=db,
        current_user=current_user,
        q=q,
        limit=limit,
    )

@router.get("/workspaces", response_model=List[SearchResultItem])
def search_workspaces(
    q: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search workspaces accessible to authenticated user."""
    return search_service.search_workspaces(
        db=db,
        current_user=current_user,
        q=q,
        limit=limit,
    )

@router.get("/boards", response_model=List[SearchResultItem])
def search_boards(
    q: Optional[str] = Query(None, description="Search term"),
    workspace_id: Optional[int] = Query(None, description="Filter workspace"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search boards accessible to authenticated user."""
    return search_service.search_boards(
        db=db,
        current_user=current_user,
        q=q,
        workspace_id=workspace_id,
        limit=limit,
    )

@router.get("/members", response_model=List[SearchResultItem])
def search_members(
    q: Optional[str] = Query(None, description="Search name, username, or email"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search members strictly within shared organizations, workspaces, or teams."""
    return search_service.search_members(
        db=db,
        current_user=current_user,
        q=q,
        limit=limit,
    )

@router.get("/comments", response_model=List[SearchResultItem])
def search_comments(
    q: Optional[str] = Query(None, description="Search text in comment discussions"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search comment discussions within accessible scope."""
    return search_service.search_comments(
        db=db,
        current_user=current_user,
        q=q,
        limit=limit,
    )

# -------------------------------------------------------------
# 4. Advanced Filter Engine
# -------------------------------------------------------------
@router.post("/filter", response_model=SearchResponse)
def advanced_filter(
    filter_req: AdvancedFilterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute multi-field composite filters across tasks or projects."""
    return search_service.apply_advanced_filter(
        db=db,
        current_user=current_user,
        filter_req=filter_req,
    )

# -------------------------------------------------------------
# 5. Search History Management
# -------------------------------------------------------------
@router.get("/history", response_model=List[SearchHistoryItemResponse])
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve search history for the authenticated user."""
    return search_service.get_history(db=db, user_id=current_user.id, limit=limit)

@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a single history item owned by the user."""
    try:
        search_service.delete_history_item(db=db, history_id=history_id, user_id=current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found.")
    return None

@router.delete("/history", status_code=status.HTTP_200_OK)
def clear_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all search history for the authenticated user."""
    affected = search_service.clear_history(db=db, user_id=current_user.id)
    return {"message": "Search history cleared.", "affected": affected}

# -------------------------------------------------------------
# 6. Saved Searches & Filter Presets
# -------------------------------------------------------------
@router.get("/saved", response_model=List[SavedSearchResponse])
def list_saved_searches(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (TASK, PROJECT, GLOBAL)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List saved searches owned by user or shared within organization."""
    return search_service.list_saved_searches(
        db=db,
        current_user=current_user,
        entity_type=entity_type,
    )

@router.post("/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
def create_saved_search(
    saved_in: SavedSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new saved search or filter preset."""
    return search_service.create_saved_search(
        db=db,
        current_user=current_user,
        saved_in=saved_in,
    )

@router.get("/saved/{saved_id}", response_model=SavedSearchResponse)
def get_saved_search(
    saved_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a single saved search respecting ownership or organization sharing."""
    try:
        return search_service.get_saved_search(db=db, saved_id=saved_id, current_user=current_user)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found.")

@router.put("/saved/{saved_id}", response_model=SavedSearchResponse)
def update_saved_search(
    saved_id: int,
    saved_update: SavedSearchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a saved search owned by the authenticated user."""
    try:
        return search_service.update_saved_search(
            db=db,
            saved_id=saved_id,
            update_in=saved_update,
            current_user=current_user,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found.")

@router.delete("/saved/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_search(
    saved_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a saved search owned by the authenticated user."""
    try:
        search_service.delete_saved_search(db=db, saved_id=saved_id, current_user=current_user)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found.")
    return None
