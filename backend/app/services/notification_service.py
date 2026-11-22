from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.notification import Notification, NotificationPreference
from app.models.task import Task
from app.models.user import User
from app.services.email_service import email_service

class NotificationService:
    def get_or_create_preferences(self, db: Session, user_id: int) -> NotificationPreference:
        """Retrieve user notification preferences or instantiate default record."""
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    def create_notification(
        self,
        db: Session,
        user_id: int,
        type: str,
        title: str,
        message: str,
        task_id: Optional[str] = None,
        delivery_channel: str = "IN_APP"
    ) -> Notification:
        """Create and persist an in-app and/or email notification."""
        now = datetime.now(timezone.utc)
        notif = Notification(
            user_id=user_id,
            task_id=task_id,
            type=type,
            title=title,
            message=message,
            scheduled_at=now,
            sent_at=now,
            status="SENT",
            delivery_channel=delivery_channel,
            created_at=now,
            updated_at=now
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        # Handle optional email delivery
        if delivery_channel in ("EMAIL", "BOTH"):
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.email:
                email_service.send_notification_email(user.email, title, message)

        return notif

    def check_and_generate_task_reminders(self, db: Session, user_id: int) -> List[Notification]:
        """
        Evaluate user active tasks for due dates and create reminders:
        - Deduplicates against existing reminders sent for same task and date.
        - Respects user notification preferences.
        """
        pref = self.get_or_create_preferences(db, user_id)
        if not pref.enable_in_app and not pref.enable_email:
            return []

        channel = "BOTH" if (pref.enable_in_app and pref.enable_email) else ("EMAIL" if pref.enable_email else "IN_APP")
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

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

            # Duplicate prevention: check if this notification was already generated today
            existing = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.task_id == t.id,
                Notification.type == notif_type,
                Notification.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            ).first()

            if not existing:
                notif = self.create_notification(
                    db=db,
                    user_id=user_id,
                    type=notif_type,
                    title=title,
                    message=msg,
                    task_id=t.id,
                    delivery_channel=channel
                )
                created_notifs.append(notif)

        return created_notifs

    def on_task_completed(self, db: Session, task_id: str, user_id: int):
        """Cancel future or pending deadline notifications for a completed task."""
        db.query(Notification).filter(
            Notification.task_id == task_id,
            Notification.user_id == user_id,
            Notification.type.in_(["TASK_OVERDUE", "TASK_DUE_TODAY", "TASK_DUE_SOON"]),
            Notification.read_at == None
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
