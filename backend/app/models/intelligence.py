from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class ProductivityEvent(Base):
    __tablename__ = "productivity_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # task_created, task_completed, task_reopened, task_rescheduled, etc.
    event_metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("ix_prod_event_user_type", "user_id", "event_type", "timestamp"),
    )

class IntelligencePreference(Base):
    __tablename__ = "intelligence_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    insights_enabled = Column(Boolean, default=True, nullable=False)
    coaching_enabled = Column(Boolean, default=True, nullable=False)
    work_start_hour = Column(Integer, default=9, nullable=False)
    work_end_hour = Column(Integer, default=18, nullable=False)
    working_days_json = Column(Text, default="[1,2,3,4,5]", nullable=False)  # Mon-Fri
    time_zone = Column(String(50), default="UTC", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")

class InsightFeedback(Base):
    __tablename__ = "insight_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_id = Column(String(64), nullable=False, index=True)
    feedback_type = Column(String(32), nullable=False)  # helpful, not_helpful, dismissed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("ix_insight_feedback_unique", "user_id", "insight_id", unique=True),
    )
