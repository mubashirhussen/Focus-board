from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.comment_service import comment_service
from app.services.mention_service import mention_service
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentReplyCreate,
    CommentResponse,
    CommentReactionCreate,
    CommentReactionResponse,
    CommentReactionSummary,
    MentionUserAutocomplete,
)

router = APIRouter(prefix="/comments", tags=["Comments & Mentions"])

# -------------------------------------------------------------
# Mention Autocomplete (Before dynamic /{comment_id} routes)
# -------------------------------------------------------------

@router.get("/mentions/autocomplete", response_model=List[MentionUserAutocomplete])
def autocomplete_mentions(
    q: str = Query(..., min_length=1, description="Search username or display name"),
    organization_id: Optional[int] = Query(None, description="Scope to organization"),
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search tenant members for @mention autocomplete."""
    return mention_service.autocomplete_users(
        db=db,
        current_user=current_user,
        query=q,
        organization_id=organization_id,
        workspace_id=workspace_id,
        limit=limit,
    )

# -------------------------------------------------------------
# Comment CRUD & Listing
# -------------------------------------------------------------

@router.get("", response_model=List[CommentResponse])
def list_comments(
    entity_type: Optional[str] = Query("TASK", description="Entity type: TASK, PROJECT, WORKSPACE, BOARD, TEAM"),
    entity_id: Optional[str] = Query(None, description="Entity identifier"),
    task_id: Optional[str] = Query(None, description="Task identifier alias"),
    project_id: Optional[int] = Query(None, description="Project identifier alias"),
    parent_comment_id: Optional[int] = Query(None, description="Filter by parent comment"),
    include_replies: bool = Query(True, description="Include replies in response"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve comments for a specific entity with optional replies and reaction summaries."""
    eff_entity_type = entity_type or "TASK"
    eff_entity_id = entity_id or task_id or (str(project_id) if project_id else None)
    if not eff_entity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="entity_id, task_id, or project_id must be provided"
        )
    try:
        return comment_service.list_comments(
            db=db,
            current_user=current_user,
            entity_type=eff_entity_type,
            entity_id=eff_entity_id,
            parent_comment_id=parent_comment_id,
            include_replies=include_replies,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new root comment or reply, extracting mentions and persisting activity."""
    try:
        return comment_service.create_comment(db=db, current_user=current_user, comment_in=comment_in)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single comment with its replies, mentions, and reactions."""
    try:
        return comment_service.get_comment_or_404(db=db, current_user=current_user, comment_id=comment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    update_in: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit comment content (author or admin only)."""
    try:
        return comment_service.update_comment(
            db=db, current_user=current_user, comment_id=comment_id, update_in=update_in
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete comment preserving discussion thread consistency."""
    try:
        comment_service.delete_comment(db=db, current_user=current_user, comment_id=comment_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# -------------------------------------------------------------
# Threaded Replies
# -------------------------------------------------------------

@router.get("/{comment_id}/replies", response_model=List[CommentResponse])
def get_comment_replies(
    comment_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve child reply comments for a parent comment thread."""
    try:
        parent = comment_service.get_comment_or_404(db=db, current_user=current_user, comment_id=comment_id)
        return comment_service.list_comments(
            db=db,
            current_user=current_user,
            entity_type=parent.entity_type,
            entity_id=parent.entity_id,
            parent_comment_id=comment_id,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{comment_id}/replies", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def post_comment_reply(
    comment_id: int,
    reply_in: CommentReplyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a threaded reply to a parent comment."""
    try:
        parent = comment_service.get_comment_or_404(db=db, current_user=current_user, comment_id=comment_id)
        comm_in = CommentCreate(
            content=reply_in.content,
            content_format=reply_in.content_format or "markdown",
            entity_type=parent.entity_type,
            entity_id=parent.entity_id,
            parent_comment_id=comment_id,
        )
        return comment_service.create_comment(db=db, current_user=current_user, comment_in=comm_in)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# -------------------------------------------------------------
# Comment Reactions
# -------------------------------------------------------------

@router.get("/{comment_id}/reactions", response_model=List[CommentReactionSummary])
def get_reactions(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve reaction counts and user-reacted states."""
    try:
        return comment_service.get_reactions(db=db, current_user=current_user, comment_id=comment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{comment_id}/reactions", response_model=CommentReactionResponse, status_code=status.HTTP_201_CREATED)
def add_reaction(
    comment_id: int,
    react_in: CommentReactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an emoji/reaction to a comment."""
    try:
        return comment_service.add_reaction(
            db=db, current_user=current_user, comment_id=comment_id, reaction_type=react_in.reaction_type
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{comment_id}/reactions/{reaction_type}", status_code=status.HTTP_204_NO_CONTENT)
def remove_reaction(
    comment_id: int,
    reaction_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a previously placed reaction."""
    try:
        comment_service.remove_reaction(
            db=db, current_user=current_user, comment_id=comment_id, reaction_type=reaction_type
        )
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
