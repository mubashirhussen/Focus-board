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
    
    # Ownership & Timestamps
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)

    # Relationship to user
    user = relationship("User", back_populates="tasks")

    # Composite indexes for multi-tenant query performance
    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_priority", "user_id", "priority"),
    )
