from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.reminder import Reminder
from app.models.task import Task
from app.models.notification import Notification
from app.models.user import User
from app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderSnoozeRequest,
    ReminderProcessResult,
)

class ReminderService:
    def create_reminder(self, db: Session, current_user: User, reminder_in: ReminderCreate) -> Reminder:
        """Create a scheduled reminder scoped to the user and optional task/workspace."""
        if reminder_in.task_id:
            task = db.query(Task).filter(Task.id == reminder_in.task_id, Task.is_deleted == False).first()
            if not task:
                raise ValueError("Referenced task not found")
            # Enforce access permission
            if task.user_id != current_user.id and task.assignee_id != current_user.id:
                if not task.workspace_id and not task.organization_id:
                    raise ValueError("Unauthorized to attach reminder to this task")

        sched_at = reminder_in.scheduled_at
        if sched_at.tzinfo:
            sched_at = sched_at.astimezone(timezone.utc)
        else:
            sched_at = sched_at.replace(tzinfo=timezone.utc)

        reminder = Reminder(
            organization_id=reminder_in.organization_id or getattr(current_user, "organization_id", None),
            workspace_id=reminder_in.workspace_id,
            project_id=reminder_in.project_id,
            task_id=reminder_in.task_id,
            user_id=current_user.id,
            reminder_type=reminder_in.reminder_type,
            title=reminder_in.title,
            description=reminder_in.description,
            scheduled_at=sched_at,
            timezone=reminder_in.timezone or "UTC",
            status="PENDING",
            delivery_channel=reminder_in.delivery_channel or "IN_APP",
            delivery_attempts=0,
            max_attempts=3,
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    def list_reminders(
        self,
        db: Session,
        current_user: User,
        status: Optional[str] = None,
        task_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Reminder]:
        """List current user's reminders with filtering."""
        query = db.query(Reminder).filter(Reminder.user_id == current_user.id)

        if status:
            query = query.filter(Reminder.status == status.upper())
        if task_id:
            query = query.filter(Reminder.task_id == task_id)
        if from_date:
            f_dt = from_date.astimezone(timezone.utc) if from_date.tzinfo else from_date.replace(tzinfo=timezone.utc)
            query = query.filter(Reminder.scheduled_at >= f_dt)
        if to_date:
            t_dt = to_date.astimezone(timezone.utc) if to_date.tzinfo else to_date.replace(tzinfo=timezone.utc)
            query = query.filter(Reminder.scheduled_at <= t_dt)

        return query.order_by(Reminder.scheduled_at.asc()).offset(skip).limit(limit).all()

    def get_reminder(self, db: Session, current_user: User, reminder_id: int) -> Reminder:
        """Fetch a specific reminder enforcing user ownership."""
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id).first()
        if not reminder:
            raise ValueError("Reminder not found")
        return reminder

    def update_reminder(self, db: Session, current_user: User, reminder_id: int, update_in: ReminderUpdate) -> Reminder:
        """Update reminder details and re-synchronize scheduling."""
        reminder = self.get_reminder(db, current_user, reminder_id)

        if update_in.title is not None:
            reminder.title = update_in.title
        if update_in.description is not None:
            reminder.description = update_in.description
        if update_in.timezone is not None:
            reminder.timezone = update_in.timezone
        if update_in.delivery_channel is not None:
            reminder.delivery_channel = update_in.delivery_channel
        if update_in.status is not None:
            reminder.status = update_in.status.upper()

        if update_in.scheduled_at is not None:
            s_dt = update_in.scheduled_at
            if s_dt.tzinfo:
                reminder.scheduled_at = s_dt.astimezone(timezone.utc)
            else:
                reminder.scheduled_at = s_dt.replace(tzinfo=timezone.utc)
            # Reset attempts when re-scheduled
            reminder.delivery_attempts = 0
            reminder.snoozed_until = None
            if reminder.status in ["FAILED", "DELIVERED"]:
                reminder.status = "PENDING"

        db.commit()
        db.refresh(reminder)
        return reminder

    def delete_reminder(self, db: Session, current_user: User, reminder_id: int) -> bool:
        """Delete a reminder safely without affecting the associated task."""
        reminder = self.get_reminder(db, current_user, reminder_id)
        db.delete(reminder)
        db.commit()
        return True

    def snooze_reminder(self, db: Session, current_user: User, reminder_id: int, snooze_in: ReminderSnoozeRequest) -> Reminder:
        """Snooze a pending or delivered reminder for later redelivery."""
        reminder = self.get_reminder(db, current_user, reminder_id)

        if reminder.status == "CANCELLED":
            raise ValueError("Cannot snooze a cancelled reminder")

        now_utc = datetime.now(timezone.utc)
        if snooze_in.snooze_until:
            s_dt = snooze_in.snooze_until
            target = s_dt.astimezone(timezone.utc) if s_dt.tzinfo else s_dt.replace(tzinfo=timezone.utc)
        elif snooze_in.snooze_minutes:
            target = now_utc + timedelta(minutes=snooze_in.snooze_minutes)
        else:
            # Default to 15 minutes snooze
            target = now_utc + timedelta(minutes=15)

        reminder.snoozed_until = target
        reminder.status = "SNOOZED"
        db.commit()
        db.refresh(reminder)
        return reminder

    def acknowledge_reminder(self, db: Session, current_user: User, reminder_id: int) -> Reminder:
        """Mark a reminder as acknowledged / dismissed."""
        reminder = self.get_reminder(db, current_user, reminder_id)
        reminder.acknowledged_at = datetime.now(timezone.utc)
        if reminder.status != "DELIVERED":
            reminder.status = "DELIVERED"
            reminder.delivered_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(reminder)
        return reminder

    def cancel_reminder(self, db: Session, current_user: User, reminder_id: int) -> Reminder:
        """Cancel an active or snoozed reminder."""
        reminder = self.get_reminder(db, current_user, reminder_id)
        reminder.status = "CANCELLED"
        db.commit()
        db.refresh(reminder)
        return reminder

    def process_due_reminders(self, db: Session) -> ReminderProcessResult:
        """Background worker engine: evaluates due reminders and delivers notifications."""
        now_utc = datetime.now(timezone.utc)

        # Pending or Snoozed reminders where scheduled time or snooze deadline has passed
        due_reminders = (
            db.query(Reminder)
            .filter(
                Reminder.status.in_(["PENDING", "SNOOZED"]),
                or_(
                    and_(Reminder.snoozed_until.isnot(None), Reminder.snoozed_until <= now_utc),
                    and_(Reminder.snoozed_until.is_(None), Reminder.scheduled_at <= now_utc),
                )
            )
            .all()
        )

        delivered = 0
        failed = 0

        for r in due_reminders:
            try:
                r.delivery_attempts += 1
                r.last_attempt_at = now_utc

                # 1. In-App Notification delivery
                notif = Notification(
                    user_id=r.user_id,
                    task_id=r.task_id,
                    type="TASK_DUE_SOON" if r.reminder_type == "DUE_DATE" else "SYSTEM",
                    title=f"Reminder: {r.title}",
                    message=r.description or f"Reminder scheduled for task '{r.title}'.",
                    scheduled_at=now_utc,
                    sent_at=now_utc,
                    status="SENT",
                    delivery_channel=r.delivery_channel,
                )
                db.add(notif)

                # 2. Update reminder status
                r.status = "DELIVERED"
                r.delivered_at = now_utc
                delivered += 1
            except Exception as e:
                r.error_metadata = str(e)
                if r.delivery_attempts >= r.max_attempts:
                    r.status = "FAILED"
                failed += 1

        db.commit()

        return ReminderProcessResult(
            processed_count=len(due_reminders),
            delivered_count=delivered,
            failed_count=failed,
            timestamp=now_utc,
        )

reminder_service = ReminderService()
