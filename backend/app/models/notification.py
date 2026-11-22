from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String(50), nullable=False, index=True)  # TASK_DUE_SOON, TASK_DUE_TODAY, TASK_OVERDUE, DAILY_PLAN, TASK_COMPLETED, SYSTEM
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    scheduled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True, index=True)
    status = Column(String(50), default="SENT", nullable=False)  # PENDING, SENT, FAILED, CANCELLED
    delivery_channel = Column(String(50), default="IN_APP", nullable=False)  # IN_APP, EMAIL, BOTH
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
    task = relationship("Task")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read_at"),
        Index("ix_notifications_user_type", "user_id", "type"),
    )

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    enable_in_app = Column(Boolean, default=True, nullable=False)
    enable_email = Column(Boolean, default=False, nullable=False)
    enable_due_soon = Column(Boolean, default=True, nullable=False)
    enable_overdue = Column(Boolean, default=True, nullable=False)
    enable_daily_plan = Column(Boolean, default=True, nullable=False)
    daily_reminder_time = Column(String(10), default="09:00", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    user = relationship("User")
