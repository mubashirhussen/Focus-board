from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from app.db.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="Design", nullable=False)
    status = Column(String(50), default="Todo", nullable=False, index=True) # Todo, In Progress, Review, Completed, Blocked
    priority = Column(String(50), default="Medium", nullable=False, index=True) # Low, Medium, High, Critical
    due_date = Column(String(50), nullable=True)
    start_date = Column(String(50), nullable=True)
    is_all_day = Column(Boolean, default=False, nullable=False)
    timezone_name = Column(String(50), default="UTC", nullable=True)
    
    # Task Scheduling & Time Blocking (Phase 20)
    scheduled_start = Column(DateTime, nullable=True, index=True)
    scheduled_end = Column(DateTime, nullable=True)
    estimated_duration_minutes = Column(Integer, default=30, nullable=True)
    actual_minutes = Column(Integer, default=0, nullable=False)
    
    # Ownership & Timestamps
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)

    # Multi-Tenant & Hierarchical Extensions (Phase B3-B5)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Subtask Parent-Child Hierarchy (Phase B5)
    parent_task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Ordering, Progress, Labels (Phase B5)
    sort_order = Column(Integer, default=0, nullable=False, index=True)
    progress_percent = Column(Float, default=0.0, nullable=False)
    labels_json = Column(Text, default="[]", nullable=False)
    
    # Archival & Soft Deletion Lifecycle (Phase B5)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    project = relationship("Project", foreign_keys=[project_id], back_populates="tasks")
    comments = relationship("TaskComment", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")
    recurrence_rule = relationship("TaskRecurrenceRule", back_populates="task", uselist=False, cascade="all, delete-orphan")
    
    # Subtasks hierarchy
    subtasks = relationship(
        "Task",
        cascade="all, delete-orphan",
        backref=backref("parent_task", remote_side=[id]),
        foreign_keys=[parent_task_id],
        order_by="Task.sort_order"
    )
    
    # Task dependencies relationships
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    dependents = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on_task",
        cascade="all, delete-orphan"
    )

    @property
    def labels(self):
        try:
            return json.loads(self.labels_json) if self.labels_json else []
        except Exception:
            return []

    @labels.setter
    def labels(self, val):
        if isinstance(val, list):
            self.labels_json = json.dumps(val)
        elif isinstance(val, str):
            self.labels_json = json.dumps([x.strip() for x in val.split(",") if x.strip()])
        else:
            self.labels_json = "[]"

    # Composite indexes for multi-tenant query performance
    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_priority", "user_id", "priority"),
        Index("ix_tasks_workspace_status", "workspace_id", "status"),
        Index("ix_tasks_parent_order", "parent_task_id", "sort_order"),
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(String(32), default="FINISH_TO_START", nullable=False) # FINISH_TO_START, START_TO_START, FINISH_TO_FINISH, START_TO_FINISH
    lag_duration = Column(Float, default=0.0, nullable=False)
    lag_unit = Column(String(16), default="DAYS", nullable=False) # DAYS, HOURS
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id], back_populates="dependents")

    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency_pair"),
        Index("ix_task_dep_pair", "task_id", "depends_on_task_id"),
    )
