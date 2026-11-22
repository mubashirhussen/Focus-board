from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Types: DUE_DATE, SCHEDULED_START, CUSTOM, RECURRING
    reminder_type = Column(String(50), default="DUE_DATE", nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scheduling & Timezone
    scheduled_at = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Status: PENDING, DELIVERED, SNOOZED, CANCELLED, FAILED
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    # Delivery Channels: IN_APP, EMAIL, BOTH
    delivery_channel = Column(String(50), default="IN_APP", nullable=False)
    
    # Delivery lifecycle & retry
    delivery_attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    snoozed_until = Column(DateTime, nullable=True, index=True)
    delivered_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    last_attempt_at = Column(DateTime, nullable=True)
    error_metadata = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    task = relationship("Task", foreign_keys=[task_id], back_populates="reminders")
    project = relationship("Project", foreign_keys=[project_id])

    __table_args__ = (
        Index("ix_reminders_user_status", "user_id", "status"),
        Index("ix_reminders_user_scheduled", "user_id", "scheduled_at"),
        Index("ix_reminders_due_processing", "status", "scheduled_at"),
    )

class TaskRecurrenceRule(Base):
    __tablename__ = "task_recurrence_rules"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Frequency: DAILY, WEEKLY, MONTHLY, YEARLY
    frequency = Column(String(50), default="WEEKLY", nullable=False)
    interval = Column(Integer, default=1, nullable=False)
    weekdays_json = Column(String(255), default="[]", nullable=False)  # e.g. '["MO", "WE", "FR"]'
    month_day = Column(Integer, nullable=True)
    
    # End conditions
    end_date = Column(DateTime, nullable=True)
    max_occurrences = Column(Integer, nullable=True)
    occurrences_created = Column(Integer, default=0, nullable=False)
    
    # Next execution
    next_run_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="recurrence_rule")
    user = relationship("User", foreign_keys=[user_id])
