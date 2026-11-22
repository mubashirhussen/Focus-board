import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.notification import Notification, NotificationPreference, NotificationDelivery
from app.models.task import Task
from app.models.user import User
from app.models.comment import Comment
from app.models.team import Team, TeamInvitation
from app.models.collaboration import Workspace, WorkspaceInvitation
from app.models.project import Project
from app.services.email_service import email_service
from app.services.push_service import push_service

def utc_now() -> datetime:
    return datetime.utcnow()

class NotificationService:
    # -------------------------------------------------------------
    # User Preferences
    # -------------------------------------------------------------
    def get_or_create_preferences(self, db: Session, user_id: int) -> NotificationPreference:
        """Retrieve user notification preferences or instantiate default record."""
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                enable_in_app=True,
                enable_email=False,
                enable_push=True,
                enable_due_soon=True,
                enable_overdue=True,
                enable_daily_plan=True,
                enable_task_assigned=True,
                enable_comments=True,
                enable_mentions=True,
                enable_project_updates=True,
                enable_team_updates=True,
                enable_invitations=True,
                daily_reminder_time="09:00",
                timezone="UTC",
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    def should_deliver(self, pref: NotificationPreference, category: str, channel: str) -> bool:
        """Determine whether user preferences allow notification delivery on this channel."""
        if channel == "IN_APP" and not pref.enable_in_app:
            return False
        if channel == "EMAIL" and not pref.enable_email:
            return False
        if channel == "PUSH" and not pref.enable_push:
            return False

        # Category level checks
        if category == "TASK" and not pref.enable_task_assigned:
            return False
        if category == "COLLABORATION" and not (pref.enable_comments or pref.enable_mentions):
            return False
        if category == "PROJECT" and not pref.enable_project_updates:
            return False
        if category == "TEAM" and not pref.enable_team_updates:
            return False
        if category == "INVITATION" and not pref.enable_invitations:
            return False
        if category == "CALENDAR" and not (pref.enable_due_soon or pref.enable_overdue):
            return False

        return True

    # -------------------------------------------------------------
    # Notification Creation & Dispatch
    # -------------------------------------------------------------
    def create_notification(
        self,
        db: Session,
        user_id: int,
        type: str,
        title: str,
        message: str,
        category: str = "TASK",
        priority: str = "NORMAL",
        actor_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        task_id: Optional[str] = None,
        project_id: Optional[int] = None,
        team_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        comment_id: Optional[int] = None,
        invitation_id: Optional[int] = None,
        delivery_channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Optional[Notification]:
        """Centralized notification generator with preference checks, deduplication, and multi-channel delivery."""
        # 1. Idempotency & Deduplication
        if idempotency_key:
            existing_delivery = db.query(NotificationDelivery).filter(
                or_(
                    NotificationDelivery.idempotency_key == idempotency_key,
                    NotificationDelivery.idempotency_key.like(f"{idempotency_key}%"),
                )
            ).first()
            if existing_delivery:
                return db.query(Notification).filter(Notification.id == existing_delivery.notification_id).first()

        # Deduplicate identical recent notifications (same user, type, entity within 5 minutes)
        if entity_type and entity_id:
            recent_duplicate = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.type == type,
                Notification.entity_type == entity_type,
                Notification.entity_id == str(entity_id),
                Notification.created_at >= utc_now() - timedelta(minutes=5),
            ).first()
            if recent_duplicate:
                return recent_duplicate

        pref = self.get_or_create_preferences(db, user_id)

        # 2. Determine target channels
        effective_channel = delivery_channel or ("BOTH" if pref.enable_email else "IN_APP")
        channels_to_deliver = []
        if self.should_deliver(pref, category, "IN_APP"):
            channels_to_deliver.append("IN_APP")
        if self.should_deliver(pref, category, "EMAIL"):
            channels_to_deliver.append("EMAIL")
        if self.should_deliver(pref, category, "PUSH"):
            channels_to_deliver.append("PUSH")

        if not channels_to_deliver and priority not in ["HIGH", "URGENT"]:
            # Suppressed by user preference
            return None

        now = utc_now()
        meta_str = json.dumps(metadata or {})

        notif = Notification(
            user_id=user_id,
            category=category,
            type=type,
            title=title.strip(),
            message=message.strip(),
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            task_id=task_id or (str(entity_id) if entity_type == "TASK" else None),
            project_id=project_id,
            team_id=team_id,
            workspace_id=workspace_id,
            comment_id=comment_id,
            invitation_id=invitation_id,
            priority=priority,
            scheduled_at=now,
            sent_at=now,
            status="SENT",
            delivery_channel=effective_channel,
            is_archived=False,
            metadata_json=meta_str,
            created_at=now,
            updated_at=now,
        )
        db.add(notif)
        db.flush()

        # 3. Create delivery records and dispatch
        for ch in (channels_to_deliver or ["IN_APP"]):
            delivery_key = f"{idempotency_key}_{ch}" if idempotency_key else None
            deliv = NotificationDelivery(
                notification_id=notif.id,
                recipient_user_id=user_id,
                channel=ch,
                status="DELIVERED",
                attempt_count=1,
                last_attempt_at=now,
                delivered_at=now,
                idempotency_key=delivery_key,
                created_at=now,
                updated_at=now,
            )
            db.add(deliv)

            # Optional email dispatch
            if ch == "EMAIL":
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.email:
                    email_service.send_notification_email(user.email, title, message)

        db.commit()
        db.refresh(notif)
        return notif

    # -------------------------------------------------------------
    # Event Integration Hooks
    # -------------------------------------------------------------
    def notify_task_assigned(self, db: Session, task: Task, assignee_id: int, actor_id: int):
        """Notify user of task assignment."""
        if assignee_id == actor_id:
            return  # No self-notification
        actor = db.query(User).filter(User.id == actor_id).first()
        actor_name = actor.name if actor else "A team member"
        self.create_notification(
            db=db,
            user_id=assignee_id,
            category="TASK",
            type="TASK_ASSIGNED",
            title=f"Task Assigned: {task.title}",
            message=f"{actor_name} assigned you to '{task.title}'.",
            priority="HIGH",
            actor_id=actor_id,
            entity_type="TASK",
            entity_id=task.id,
            task_id=task.id,
            workspace_id=task.workspace_id,
            project_id=task.project_id,
        )

    def notify_task_completed(self, db: Session, task: Task, actor_id: int):
        """Notify task creator/assignee of completion."""
        actor = db.query(User).filter(User.id == actor_id).first()
        actor_name = actor.name if actor else "A team member"
        target_id = task.user_id
        if target_id and target_id != actor_id:
            self.create_notification(
                db=db,
                user_id=target_id,
                category="TASK",
                type="TASK_COMPLETED",
                title=f"Task Completed: {task.title}",
                message=f"'{task.title}' was marked as completed by {actor_name}.",
                actor_id=actor_id,
                entity_type="TASK",
                entity_id=task.id,
                task_id=task.id,
                workspace_id=task.workspace_id,
            )

    def notify_mention(self, db: Session, comment: Comment, actor_id: int, mentioned_user_id: int):
        """Notify user when mentioned in a comment."""
        if mentioned_user_id == actor_id:
            return
        actor = db.query(User).filter(User.id == actor_id).first()
        actor_name = actor.name if actor else "Someone"
        self.create_notification(
            db=db,
            user_id=mentioned_user_id,
            category="COLLABORATION",
            type="COMMENT_MENTION",
            title=f"Mentioned by {actor_name}",
            message=f"{actor_name} mentioned you on {comment.entity_type.lower()} #{comment.entity_id}: '{comment.content[:80]}...'",
            priority="HIGH",
            actor_id=actor_id,
            entity_type=comment.entity_type,
            entity_id=comment.entity_id,
            comment_id=comment.id,
            task_id=comment.task_id,
            workspace_id=comment.workspace_id,
        )

    def notify_comment(self, db: Session, comment: Comment, actor_id: int, recipient_ids: List[int]):
        """Notify participants on a comment thread."""
        actor = db.query(User).filter(User.id == actor_id).first()
        actor_name = actor.name if actor else "Someone"
        for uid in set(recipient_ids):
            if uid == actor_id:
                continue
            self.create_notification(
                db=db,
                user_id=uid,
                category="COLLABORATION",
                type="COMMENT_ADDED",
                title=f"New Comment on {comment.entity_type.title()}",
                message=f"{actor_name} commented: '{comment.content[:80]}...'",
                actor_id=actor_id,
                entity_type=comment.entity_type,
                entity_id=comment.entity_id,
                comment_id=comment.id,
                task_id=comment.task_id,
                workspace_id=comment.workspace_id,
            )

    def notify_team_invitation(self, db: Session, team: Team, invitation: TeamInvitation, inviter_id: int):
        """Notify user of a team invitation."""
        if invitation.invitee_user_id:
            inviter = db.query(User).filter(User.id == inviter_id).first()
            inviter_name = inviter.name if inviter else "Team Owner"
            self.create_notification(
                db=db,
                user_id=invitation.invitee_user_id,
                category="INVITATION",
                type="TEAM_INVITATION",
                title=f"Invitation to join '{team.name}'",
                message=f"{inviter_name} invited you to join team '{team.name}' as {invitation.role}.",
                priority="HIGH",
                actor_id=inviter_id,
                entity_type="TEAM",
                entity_id=str(team.id),
                team_id=team.id,
                invitation_id=invitation.id,
            )

    # -------------------------------------------------------------
    # Notification Queries & Summary
    # -------------------------------------------------------------
    def list_notifications(
        self,
        db: Session,
        user_id: int,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        unread_only: bool = False,
        is_archived: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Notification]:
        """Retrieve user-scoped notifications with full filtering."""
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status != "CANCELLED",
            Notification.is_archived == is_archived,
        )

        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        if category:
            query = query.filter(Notification.category == category.upper())
        if priority:
            query = query.filter(Notification.priority == priority.upper())
        if search:
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Notification.title).like(term),
                    func.lower(Notification.message).like(term),
                )
            )

        return query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()

    def get_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Compute aggregated notification badge and category metrics."""
        base_query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status != "CANCELLED"
        )
        total_count = base_query.count()
        unread_count = base_query.filter(Notification.read_at.is_(None), Notification.is_archived == False).count()
        read_count = base_query.filter(Notification.read_at.is_not(None), Notification.is_archived == False).count()
        archived_count = base_query.filter(Notification.is_archived == True).count()

        # Group by category
        cat_rows = (
            db.query(Notification.category, func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.status != "CANCELLED")
            .group_by(Notification.category)
            .all()
        )
        by_category = {cat: cnt for cat, cnt in cat_rows}

        # Group by priority
        prio_rows = (
            db.query(Notification.priority, func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.status != "CANCELLED")
            .group_by(Notification.priority)
            .all()
        )
        by_priority = {prio: cnt for prio, cnt in prio_rows}

        return {
            "total_count": total_count,
            "unread_count": unread_count,
            "read_count": read_count,
            "archived_count": archived_count,
            "by_category": by_category,
            "by_priority": by_priority,
        }

    # -------------------------------------------------------------
    # Read / Unread / Deletion / Bulk Operations
    # -------------------------------------------------------------
    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> Notification:
        """Mark an individual notification as read."""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if not notif:
            raise ValueError("Notification not found")
        if not notif.read_at:
            notif.read_at = utc_now()
            db.commit()
            db.refresh(notif)
        return notif

    def mark_as_unread(self, db: Session, notification_id: int, user_id: int) -> Notification:
        """Mark an individual notification as unread."""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if not notif:
            raise ValueError("Notification not found")
        notif.read_at = None
        db.commit()
        db.refresh(notif)
        return notif

    def mark_all_as_read(self, db: Session, user_id: int, category: Optional[str] = None) -> int:
        """Mark all notifications matching user (and optional category) as read."""
        now = utc_now()
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read_at.is_(None)
        )
        if category:
            query = query.filter(Notification.category == category.upper())
        affected = query.update({"read_at": now}, synchronize_session=False)
        db.commit()
        return affected

    def delete_notification(self, db: Session, notification_id: int, user_id: int) -> bool:
        """Permanently delete a notification owned by the user."""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if not notif:
            raise ValueError("Notification not found")
        db.delete(notif)
        db.commit()
        return True

    def bulk_mark_as_read(self, db: Session, user_id: int, notification_ids: List[int]) -> int:
        """Bulk mark specific notification IDs as read."""
        if not notification_ids:
            return 0
        now = utc_now()
        affected = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
            Notification.read_at.is_(None)
        ).update({"read_at": now}, synchronize_session=False)
        db.commit()
        return affected

    def bulk_delete(self, db: Session, user_id: int, notification_ids: List[int]) -> int:
        """Bulk delete specific notification IDs."""
        if not notification_ids:
            return 0
        affected = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id
        ).delete(synchronize_session=False)
        db.commit()
        return affected

    def archive_notification(self, db: Session, notification_id: int, user_id: int) -> Notification:
        """Archive a notification."""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if not notif:
            raise ValueError("Notification not found")
        notif.is_archived = True
        notif.archived_at = utc_now()
        db.commit()
        db.refresh(notif)
        return notif

    # -------------------------------------------------------------
    # Task Deadline Reminders (Backward Compatibility)
    # -------------------------------------------------------------
    def check_and_generate_task_reminders(self, db: Session, user_id: int) -> List[Notification]:
        """Evaluate user active tasks for due dates and generate reminders respecting preferences."""
        pref = self.get_or_create_preferences(db, user_id)
        if not pref.enable_in_app and not pref.enable_email:
            return []

        channel = "BOTH" if (pref.enable_in_app and pref.enable_email) else ("EMAIL" if pref.enable_email else "IN_APP")
        today_str = utc_now().strftime("%Y-%m-%d")

        tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status != "Completed"
        ).all()

        created_notifs = []
        for t in tasks:
            if not t.due_date:
                continue

            notif_type = None
            title = ""
            msg = ""

            if t.due_date < today_str and pref.enable_overdue:
                notif_type = "TASK_OVERDUE"
                title = f"Task Overdue: {t.title}"
                msg = f"Your task '{t.title}' was due on {t.due_date}. Please review or update its status."
            elif t.due_date == today_str and pref.enable_due_soon:
                notif_type = "TASK_DUE_TODAY"
                title = f"Task Due Today: {t.title}"
                msg = f"Your task '{t.title}' is due today ({today_str}). Plan your focus time accordingly."
            else:
                try:
                    t_date = datetime.strptime(t.due_date, "%Y-%m-%d").date()
                    curr_date = datetime.strptime(today_str, "%Y-%m-%d").date()
                    diff = (t_date - curr_date).days
                    if diff == 1 and pref.enable_due_soon:
                        notif_type = "TASK_DUE_SOON"
                        title = f"Task Due Tomorrow: {t.title}"
                        msg = f"Reminder: '{t.title}' is due tomorrow ({t.due_date})."
                except ValueError:
                    pass

            if not notif_type:
                continue

            existing = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.task_id == t.id,
                Notification.type == notif_type,
                Notification.created_at >= utc_now().replace(hour=0, minute=0, second=0)
            ).first()

            if not existing:
                notif = self.create_notification(
                    db=db,
                    user_id=user_id,
                    type=notif_type,
                    title=title,
                    message=msg,
                    category="CALENDAR",
                    task_id=t.id,
                    delivery_channel=channel
                )
                if notif:
                    created_notifs.append(notif)

        return created_notifs

    def on_task_completed(self, db: Session, task_id: str, user_id: int):
        """Cancel future or pending deadline notifications for a completed task."""
        db.query(Notification).filter(
            Notification.task_id == task_id,
            Notification.user_id == user_id,
            Notification.type.in_(["TASK_OVERDUE", "TASK_DUE_TODAY", "TASK_DUE_SOON"]),
            Notification.read_at.is_(None)
        ).update({"status": "CANCELLED"}, synchronize_session=False)
        db.commit()

    def on_task_deleted(self, db: Session, task_id: str, user_id: int):
        """Cancel all pending notifications when a task is deleted."""
        db.query(Notification).filter(
            Notification.task_id == task_id,
            Notification.user_id == user_id
        ).update({"status": "CANCELLED"}, synchronize_session=False)
        db.commit()

notification_service = NotificationService()
