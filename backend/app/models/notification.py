from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.utcnow()

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), default="TASK", nullable=False, index=True)  # TASK, PROJECT, TEAM, WORKSPACE, COLLABORATION, INVITATION, CALENDAR, SYSTEM, AUTOMATION
    type = Column(String(50), nullable=False, index=True)  # TASK_ASSIGNED, TASK_DUE_SOON, TASK_OVERDUE, COMMENT_MENTION, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type = Column(String(32), nullable=True, index=True)
    entity_id = Column(String(64), nullable=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    team_id = Column(Integer, nullable=True, index=True)
    comment_id = Column(Integer, nullable=True, index=True)
    invitation_id = Column(Integer, nullable=True, index=True)
    priority = Column(String(20), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH, URGENT
    scheduled_at = Column(DateTime, default=utc_now, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True, index=True)
    status = Column(String(50), default="SENT", nullable=False)  # PENDING, SENT, FAILED, CANCELLED
    delivery_channel = Column(String(50), default="IN_APP", nullable=False)  # IN_APP, EMAIL, PUSH, BOTH
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])
    task = relationship("Task")
    deliveries = relationship("NotificationDelivery", back_populates="notification", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read_at"),
        Index("ix_notifications_user_type", "user_id", "type"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_category_read", "user_id", "category", "read_at"),
    )

    @property
    def metadata_dict(self) -> dict:
        try:
            return json.loads(self.metadata_json or "{}")
        except Exception:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, val: dict):
        self.metadata_json = json.dumps(val or {})


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(32), default="IN_APP", nullable=False)  # IN_APP, EMAIL, PUSH, WEBSOCKET
    status = Column(String(32), default="DELIVERED", nullable=False)  # PENDING, PROCESSING, DELIVERED, FAILED, CANCELLED
    attempt_count = Column(Integer, default=1, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_details = Column(Text, nullable=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    notification = relationship("Notification", back_populates="deliveries")
    recipient = relationship("User", foreign_keys=[recipient_user_id])

    __table_args__ = (
        Index("ix_notif_deliveries_channel_status", "channel", "status"),
        Index("ix_notif_deliveries_user_status", "recipient_user_id", "status"),
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    enable_in_app = Column(Boolean, default=True, nullable=False)
    enable_email = Column(Boolean, default=False, nullable=False)
    enable_push = Column(Boolean, default=True, nullable=False)
    enable_due_soon = Column(Boolean, default=True, nullable=False)
    enable_overdue = Column(Boolean, default=True, nullable=False)
    enable_daily_plan = Column(Boolean, default=True, nullable=False)
    enable_task_assigned = Column(Boolean, default=True, nullable=False)
    enable_comments = Column(Boolean, default=True, nullable=False)
    enable_mentions = Column(Boolean, default=True, nullable=False)
    enable_project_updates = Column(Boolean, default=True, nullable=False)
    enable_team_updates = Column(Boolean, default=True, nullable=False)
    enable_invitations = Column(Boolean, default=True, nullable=False)
    category_overrides_json = Column(Text, default="{}", nullable=False)
    daily_reminder_time = Column(String(10), default="09:00", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    user = relationship("User")

    @property
    def category_overrides(self) -> dict:
        try:
            return json.loads(self.category_overrides_json or "{}")
        except Exception:
            return {}

    @category_overrides.setter
    def category_overrides(self, val: dict):
        self.category_overrides_json = json.dumps(val or {})
