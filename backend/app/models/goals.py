"""
FocusBoard Goals, OKRs & Milestones Models (Module B50).
Provides database entities for Goal, KeyResult, KeyResultProgressHistory,
GoalMilestone, MilestoneDependency, GoalProjectLink, KeyResultTaskLink,
GoalCheckIn, GoalComment, and GoalSettings.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Goal(Base):
    """
    Strategic, Team, or Individual Goal (Objective in OKR framework).
    Supports hierarchical parent-child relationships and health tracking.
    """
    __tablename__ = "goals"

    id = Column(String(64), primary_key=True, default=lambda: f"goal_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_goal_id = Column(String(64), ForeignKey("goals.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # ORGANIZATIONAL, TEAM, INDIVIDUAL, PROJECT
    goal_level = Column(String(32), default="ORGANIZATIONAL", nullable=False, index=True)
    
    # Lifecycle: DRAFT, ACTIVE, ON_TRACK, AT_RISK, BEHIND, COMPLETED, CANCELLED, ARCHIVED
    status = Column(String(32), default="DRAFT", nullable=False, index=True)
    
    # Health: ON_TRACK, AT_RISK, BEHIND, COMPLETED, INSUFFICIENT_DATA
    health_status = Column(String(32), default="ON_TRACK", nullable=False, index=True)
    health_reason = Column(Text, nullable=True)
    
    # Priority: CRITICAL, HIGH, MEDIUM, LOW
    priority = Column(String(32), default="HIGH", nullable=False, index=True)
    
    progress_percent = Column(Float, default=0.0, nullable=False)
    start_date = Column(DateTime, nullable=True)
    target_date = Column(DateTime, nullable=True, index=True)
    completed_date = Column(DateTime, nullable=True)
    
    category = Column(String(64), default="STRATEGY", nullable=False)
    tags_json = Column(Text, default="[]", nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    team = relationship("Team", foreign_keys=[team_id])
    parent = relationship("Goal", remote_side=[id], foreign_keys=[parent_goal_id], backref="subgoals")
    key_results = relationship("KeyResult", back_populates="goal", cascade="all, delete-orphan")
    milestones = relationship("GoalMilestone", back_populates="goal", cascade="all, delete-orphan")
    project_links = relationship("GoalProjectLink", back_populates="goal", cascade="all, delete-orphan")
    check_ins = relationship("GoalCheckIn", back_populates="goal", cascade="all, delete-orphan")
    comments = relationship("GoalComment", back_populates="goal", cascade="all, delete-orphan")


class KeyResult(Base):
    """
    Measurable Key Result attached to a Goal/Objective.
    Supports multiple mathematical measurement types and manual or automatic tracking.
    """
    __tablename__ = "key_results"

    id = Column(String(64), primary_key=True, default=lambda: f"kr_{uuid.uuid4().hex[:12]}")
    goal_id = Column(String(64), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Measurement types:
    # NUMERIC_INCREASE, NUMERIC_DECREASE, PERCENTAGE, BINARY, MILESTONE, TASK_COMPLETION, MANUAL
    measurement_type = Column(String(32), default="NUMERIC_INCREASE", nullable=False, index=True)
    
    starting_value = Column(Float, default=0.0, nullable=False)
    current_value = Column(Float, default=0.0, nullable=False)
    target_value = Column(Float, default=100.0, nullable=False)
    unit = Column(String(32), default="%", nullable=False)
    
    progress_percent = Column(Float, default=0.0, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    
    # Status: ACTIVE, ON_TRACK, AT_RISK, BEHIND, COMPLETED, CANCELLED
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)
    
    # Tracking method: MANUAL, AUTOMATIC
    tracking_method = Column(String(32), default="MANUAL", nullable=False)
    
    due_date = Column(DateTime, nullable=True)
    last_updated_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    goal = relationship("Goal", back_populates="key_results")
    owner = relationship("User", foreign_keys=[owner_id])
    progress_history = relationship("KeyResultProgressHistory", back_populates="key_result", cascade="all, delete-orphan")
    task_links = relationship("KeyResultTaskLink", back_populates="key_result", cascade="all, delete-orphan")


class KeyResultProgressHistory(Base):
    """
    Immutable audit history of Key Result updates.
    """
    __tablename__ = "key_result_progress_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_result_id = Column(String(64), ForeignKey("key_results.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    previous_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    previous_progress = Column(Float, nullable=False)
    new_progress = Column(Float, nullable=False)

    # MANUAL, AUTOMATIC_TASK, AUTOMATIC_MILESTONE, AUTOMATIC_TIME
    update_source = Column(String(32), default="MANUAL", nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    key_result = relationship("KeyResult", back_populates="progress_history")
    user = relationship("User", foreign_keys=[user_id])


class GoalMilestone(Base):
    """
    Strategic Milestone connected to a Goal, Key Result, and/or Project.
    """
    __tablename__ = "goal_milestones"

    id = Column(String(64), primary_key=True, default=lambda: f"mstone_{uuid.uuid4().hex[:12]}")
    goal_id = Column(String(64), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    key_result_id = Column(String(64), ForeignKey("key_results.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Status: NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED, CANCELLED
    status = Column(String(32), default="NOT_STARTED", nullable=False, index=True)
    priority = Column(String(32), default="MEDIUM", nullable=False)
    progress_percent = Column(Float, default=0.0, nullable=False)

    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True, index=True)
    completed_date = Column(DateTime, nullable=True)
    
    blocked_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    goal = relationship("Goal", back_populates="milestones")
    owner = relationship("User", foreign_keys=[owner_id])
    project = relationship("Project", foreign_keys=[project_id])


class MilestoneDependency(Base):
    """
    Explicit milestone prerequisite dependency.
    """
    __tablename__ = "milestone_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    milestone_id = Column(String(64), ForeignKey("goal_milestones.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_milestone_id = Column(String(64), ForeignKey("goal_milestones.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("milestone_id", "depends_on_milestone_id", name="uq_milestone_dependency"),
    )


class GoalProjectLink(Base):
    """
    Associates FocusBoard Projects with an overarching Strategic Goal.
    """
    __tablename__ = "goal_project_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(String(64), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("goal_id", "project_id", name="uq_goal_project_link"),
    )

    goal = relationship("Goal", back_populates="project_links")
    project = relationship("Project", foreign_keys=[project_id])


class KeyResultTaskLink(Base):
    """
    Connects specific FocusBoard Tasks to a Key Result for automated progress tracking.
    """
    __tablename__ = "key_result_task_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_result_id = Column(String(64), ForeignKey("key_results.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    weight = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("key_result_id", "task_id", name="uq_key_result_task_link"),
    )

    key_result = relationship("KeyResult", back_populates="task_links")
    task = relationship("Task", foreign_keys=[task_id])


class GoalCheckIn(Base):
    """
    Periodic progress check-in submitted by goal owners and reviewed by leadership.
    """
    __tablename__ = "goal_check_ins"

    id = Column(String(64), primary_key=True, default=lambda: f"chk_{uuid.uuid4().hex[:12]}")
    goal_id = Column(String(64), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    progress_percent = Column(Float, default=0.0, nullable=False)
    confidence_score = Column(Integer, default=4, nullable=False)  # 1 (low) to 5 (high)
    
    summary = Column(Text, nullable=False)
    blockers = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    support_needed = Column(Text, nullable=True)

    # SUBMITTED, REVIEWED
    status = Column(String(32), default="SUBMITTED", nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    goal = relationship("Goal", back_populates="check_ins")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class GoalComment(Base):
    """
    Collaborative discussion and feedback comment on a Goal.
    """
    __tablename__ = "goal_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(String(64), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    goal = relationship("Goal", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id])


class GoalSettings(Base):
    """
    Organization-wide settings for Goals & OKR management.
    """
    __tablename__ = "goal_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # WEEKLY, BIWEEKLY, MONTHLY
    check_in_frequency = Column(String(32), default="WEEKLY", nullable=False)
    auto_recalculate_progress = Column(Boolean, default=True, nullable=False)
    enable_ai_recommendations = Column(Boolean, default=True, nullable=False)
    rules_config_json = Column(Text, default="{}", nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
