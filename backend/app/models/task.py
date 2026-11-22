from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="Design", nullable=False)
    status = Column(String(50), default="Todo", nullable=False, index=True)
    priority = Column(String(50), default="Medium", nullable=False, index=True)
    due_date = Column(String(50), nullable=True)
    
    # Task Scheduling & Time Blocking (Phase 20)
    scheduled_start = Column(DateTime, nullable=True, index=True)
    scheduled_end = Column(DateTime, nullable=True)
    estimated_duration_minutes = Column(Integer, default=30, nullable=True)
    
    # Ownership & Timestamps
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)

    # Multi-User Collaboration Extensions (Phase 16)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    project = relationship("Project", foreign_keys=[project_id], back_populates="tasks")
    comments = relationship("TaskComment", cascade="all, delete-orphan")

    # Composite indexes for multi-tenant query performance
    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_priority", "user_id", "priority"),
        Index("ix_tasks_workspace_status", "workspace_id", "status"),
    )
