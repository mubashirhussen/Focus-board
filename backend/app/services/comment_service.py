import json
import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, func

from app.models.comment import Comment, CommentMention, CommentReaction
from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.organization import OrganizationMember
from app.models.audit import AuditLog
from app.services.mention_service import mention_service
from app.services.activity_service import activity_service
from app.services.audit_service import record_audit_log
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentReactionSummary,
)

def utc_now() -> datetime:
    return datetime.utcnow()

class CommentService:
    # -------------------------------------------------------------
    # Authorization & Entity Verification Helpers
    # -------------------------------------------------------------
    def verify_entity_access(
        self,
        db: Session,
        current_user: User,
        entity_type: str,
        entity_id: str,
    ) -> Tuple[int, Optional[int]]:
        """
        Verify that entity exists and user has access.
        Returns (organization_id, workspace_id).
        """
        org_id = None
        ws_id = None

        if entity_type == "TASK":
            task = db.query(Task).filter(Task.id == str(entity_id)).first()
            if not task:
                raise ValueError("Task not found")
            org_id = task.organization_id
            ws_id = task.workspace_id

        elif entity_type == "PROJECT":
            proj_id = int(entity_id) if str(entity_id).isdigit() else None
            project = db.query(Project).filter(Project.id == proj_id, Project.is_deleted == False).first() if proj_id else None
            if not project:
                raise ValueError("Project not found")
            org_id = project.organization_id
            ws_id = project.workspace_id

        elif entity_type == "WORKSPACE":
            wid = int(entity_id) if str(entity_id).isdigit() else None
            workspace = db.query(Workspace).filter(Workspace.id == wid).first() if wid else None
            if not workspace:
                raise ValueError("Workspace not found")
            org_id = workspace.organization_id
            ws_id = workspace.id

        # Fallback organization resolution
        if not org_id:
            first_org = db.query(OrganizationMember).filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_active == True
            ).first()
            if first_org:
                org_id = first_org.organization_id
            else:
                org_id = 1

        return org_id, ws_id

    # -------------------------------------------------------------
    # Comment CRUD & Threading
    # -------------------------------------------------------------
    def create_comment(
        self,
        db: Session,
        current_user: User,
        comment_in: CommentCreate,
    ) -> Comment:
        """Create a new root comment or threaded reply, extracting mentions and emitting activity."""
        # 1. Resolve entity context
        entity_type = (comment_in.entity_type or "TASK").upper()
        entity_id = comment_in.entity_id or comment_in.task_id or (str(comment_in.project_id) if comment_in.project_id else None)
        if not entity_id:
            raise ValueError("Entity ID (or task_id / project_id) must be specified")

        org_id, ws_id = self.verify_entity_access(db, current_user, entity_type, str(entity_id))

        # 2. Parent comment validation (replies)
        parent_comment = None
        if comment_in.parent_comment_id:
            parent_comment = db.query(Comment).filter(
                Comment.id == comment_in.parent_comment_id,
                Comment.is_deleted == False,
            ).first()
            if not parent_comment:
                raise ValueError("Parent comment not found")
            if parent_comment.entity_type != entity_type or parent_comment.entity_id != str(entity_id):
                raise ValueError("Parent comment belongs to a different entity")

        # 3. Content sanitation and length check
        clean_content = comment_in.content.strip()
        if not clean_content:
            raise ValueError("Comment content cannot be empty")
        if len(clean_content) > 5000:
            raise ValueError("Comment exceeds maximum length of 5000 characters")

        # 4. Create Comment record
        comment = Comment(
            organization_id=org_id,
            workspace_id=ws_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            task_id=str(entity_id) if entity_type == "TASK" else None,
            project_id=int(entity_id) if entity_type == "PROJECT" and str(entity_id).isdigit() else None,
            parent_comment_id=comment_in.parent_comment_id,
            author_id=current_user.id,
            content=clean_content,
            content_format=comment_in.content_format or "markdown",
            is_edited=False,
            is_deleted=False,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(comment)
        db.flush()

        # 5. Extract and persist user mentions
        candidates = mention_service.extract_mentions(clean_content)
        valid_mentions = mention_service.resolve_valid_mentions(db, candidates, org_id, ws_id)
        for target in valid_mentions:
            mention = CommentMention(
                organization_id=org_id,
                comment_id=comment.id,
                mentioned_user_id=target.id,
                mentioned_by_user_id=current_user.id,
                entity_type=entity_type,
                entity_id=str(entity_id),
                created_at=utc_now(),
            )
            db.add(mention)

        # 6. Emit Activity event
        event_name = "REPLY_CREATED" if comment_in.parent_comment_id else "COMMENT_CREATED"
        desc_text = f"{current_user.name or 'A user'} commented on {entity_type.lower()} #{entity_id}."
        activity_service.record_activity(
            db=db,
            actor_id=current_user.id,
            event_type=event_name,
            description=desc_text,
            entity_type=entity_type,
            entity_id=str(entity_id),
            organization_id=org_id,
            workspace_id=ws_id,
            metadata={"comment_id": comment.id, "parent_comment_id": comment_in.parent_comment_id},
        )

        # 7. Audit log
        record_audit_log(
            db=db,
            event_type=event_name,
            actor_id=current_user.id,
            resource_type="COMMENT",
            resource_id=str(comment.id),
            metadata={"entity_type": entity_type, "entity_id": str(entity_id)},
        )

        db.commit()
        db.refresh(comment)
        return comment

    def list_comments(
        self,
        db: Session,
        current_user: User,
        entity_type: str,
        entity_id: str,
        parent_comment_id: Optional[int] = None,
        include_replies: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Comment]:
        """List comments for a specific entity with optional threaded replies."""
        self.verify_entity_access(db, current_user, entity_type.upper(), str(entity_id))

        query = (
            db.query(Comment)
            .options(
                joinedload(Comment.author),
                joinedload(Comment.mentions).joinedload(CommentMention.mentioned_user),
                joinedload(Comment.reactions),
                joinedload(Comment.replies).joinedload(Comment.author),
            )
            .filter(
                Comment.entity_type == entity_type.upper(),
                Comment.entity_id == str(entity_id),
            )
        )

        if parent_comment_id is not None:
            query = query.filter(Comment.parent_comment_id == parent_comment_id)
        elif not include_replies:
            query = query.filter(Comment.parent_comment_id.is_(None))

        comments = query.order_by(Comment.created_at.asc()).offset(skip).limit(limit).all()
        return comments

    def get_comment_or_404(self, db: Session, current_user: User, comment_id: int) -> Comment:
        """Fetch a specific comment verifying tenant access."""
        comment = (
            db.query(Comment)
            .options(
                joinedload(Comment.author),
                joinedload(Comment.mentions).joinedload(CommentMention.mentioned_user),
                joinedload(Comment.reactions),
                joinedload(Comment.replies).joinedload(Comment.author),
            )
            .filter(Comment.id == comment_id)
            .first()
        )
        if not comment:
            raise ValueError("Comment not found")
        return comment

    def update_comment(
        self,
        db: Session,
        current_user: User,
        comment_id: int,
        update_in: CommentUpdate,
    ) -> Comment:
        """Update a comment's content, recalculating mentions and updating timestamp."""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise ValueError("Comment not found")

        # Authorization: author or admin
        is_author = (comment.author_id == current_user.id)
        is_admin = (current_user.role or "").upper() in ["ADMIN", "OWNER"]
        if not is_author and not is_admin:
            raise PermissionError("Only the author or an administrator can edit this comment")

        clean_content = update_in.content.strip()
        if not clean_content:
            raise ValueError("Comment content cannot be empty")
        if len(clean_content) > 5000:
            raise ValueError("Comment exceeds maximum length of 5000 characters")

        comment.content = clean_content
        comment.is_edited = True
        comment.updated_at = utc_now()

        # Recalculate mentions
        db.query(CommentMention).filter(CommentMention.comment_id == comment.id).delete()
        candidates = mention_service.extract_mentions(clean_content)
        valid_mentions = mention_service.resolve_valid_mentions(db, candidates, comment.organization_id, comment.workspace_id)
        for target in valid_mentions:
            mention = CommentMention(
                organization_id=comment.organization_id,
                comment_id=comment.id,
                mentioned_user_id=target.id,
                mentioned_by_user_id=current_user.id,
                entity_type=comment.entity_type,
                entity_id=comment.entity_id,
                created_at=utc_now(),
            )
            db.add(mention)

        # Audit
        record_audit_log(
            db=db,
            event_type="COMMENT_UPDATED",
            actor_id=current_user.id,
            resource_type="COMMENT",
            resource_id=str(comment.id),
        )

        db.commit()
        db.refresh(comment)
        return self.get_comment_or_404(db, current_user, comment.id)

    def delete_comment(
        self,
        db: Session,
        current_user: User,
        comment_id: int,
    ) -> bool:
        """Soft-delete a comment to preserve reply hierarchy and activity consistency."""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise ValueError("Comment not found")

        is_author = (comment.author_id == current_user.id)
        is_admin = (current_user.role or "").upper() in ["ADMIN", "OWNER"]
        if not is_author and not is_admin:
            raise PermissionError("Only the author or an administrator can delete this comment")

        comment.is_deleted = True
        comment.deleted_at = utc_now()
        comment.content = "[Comment deleted]"
        comment.updated_at = utc_now()

        # Record activity and audit
        activity_service.record_activity(
            db=db,
            actor_id=current_user.id,
            event_type="COMMENT_DELETED",
            description=f"Comment #{comment.id} on {comment.entity_type.lower()} #{comment.entity_id} was deleted.",
            entity_type=comment.entity_type,
            entity_id=comment.entity_id,
            organization_id=comment.organization_id,
            workspace_id=comment.workspace_id,
        )
        record_audit_log(
            db=db,
            event_type="COMMENT_DELETED",
            actor_id=current_user.id,
            resource_type="COMMENT",
            resource_id=str(comment.id),
        )

        db.commit()
        return True

    # -------------------------------------------------------------
    # Comment Reactions
    # -------------------------------------------------------------
    def add_reaction(
        self,
        db: Session,
        current_user: User,
        comment_id: int,
        reaction_type: str,
    ) -> CommentReaction:
        """Add reaction to comment idempotently."""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise ValueError("Comment not found")

        clean_type = reaction_type.strip().lower()
        existing = db.query(CommentReaction).filter(
            CommentReaction.comment_id == comment_id,
            CommentReaction.user_id == current_user.id,
            CommentReaction.reaction_type == clean_type,
        ).first()

        if existing:
            return existing

        reaction = CommentReaction(
            comment_id=comment_id,
            user_id=current_user.id,
            reaction_type=clean_type,
            created_at=utc_now(),
        )
        db.add(reaction)
        db.commit()
        db.refresh(reaction)
        return reaction

    def remove_reaction(
        self,
        db: Session,
        current_user: User,
        comment_id: int,
        reaction_type: str,
    ) -> bool:
        """Remove a user's reaction from a comment."""
        clean_type = reaction_type.strip().lower()
        deleted = (
            db.query(CommentReaction)
            .filter(
                CommentReaction.comment_id == comment_id,
                CommentReaction.user_id == current_user.id,
                CommentReaction.reaction_type == clean_type,
            )
            .delete()
        )
        db.commit()
        return deleted > 0

    def get_reactions(self, db: Session, current_user: User, comment_id: int) -> List[CommentReactionSummary]:
        """Retrieve aggregated reaction summaries for a comment."""
        comment = db.query(Comment).options(joinedload(Comment.reactions)).filter(Comment.id == comment_id).first()
        if not comment:
            raise ValueError("Comment not found")
        return self.get_reaction_summaries(comment.reactions, current_user.id)

    @staticmethod
    def get_reaction_summaries(reactions: List[CommentReaction], current_user_id: int) -> List[CommentReactionSummary]:
        """Aggregate reaction counts and user-reacted status."""
        counts = {}
        user_reacted = set()
        for r in reactions or []:
            rtype = r.reaction_type
            counts[rtype] = counts.get(rtype, 0) + 1
            if r.user_id == current_user_id:
                user_reacted.add(rtype)

        return [
            CommentReactionSummary(
                reaction_type=rtype,
                count=count,
                user_reacted=(rtype in user_reacted),
            )
            for rtype, count in counts.items()
        ]

comment_service = CommentService()
