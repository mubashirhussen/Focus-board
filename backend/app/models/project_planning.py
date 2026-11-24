from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    Boolean,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ProjectSchedule(Base):
    __tablename__ = "project_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # CPM_DRIVEN, MANUAL, HYBRID
    planning_mode = Column(String(32), default="CPM_DRIVEN", nullable=False)
    working_days_json = Column(Text, default='["MON","TUE","WED","THU","FRI"]', nullable=False)
    working_hours_per_day = Column(Float, default=8.0, nullable=False)
    calendar_holidays_json = Column(Text, default="[]", nullable=False)
    
    # Critical Path & Duration
    critical_path_duration_days = Column(Float, default=0.0, nullable=False)
    critical_tasks_count = Column(Integer, default=0, nullable=False)
    
    # Schedule Health: ON_TRACK, AT_RISK, DELAYED, CRITICAL, INSUFFICIENT_DATA
    schedule_health = Column(String(32), default="ON_TRACK", nullable=False, index=True)
    schedule_health_reasons_json = Column(Text, default="[]", nullable=False)
    
    # Dates
    planned_start_date = Column(DateTime, nullable=True)
    planned_end_date = Column(DateTime, nullable=True)
    calculated_earliest_finish = Column(DateTime, nullable=True)
    forecast_completion_date = Column(DateTime, nullable=True)
    schedule_variance_days = Column(Float, default=0.0, nullable=False)
    
    # Active Baseline pointer
    active_baseline_id = Column(Integer, nullable=True)
    auto_recalculate = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", backref="schedule")

    @property
    def working_days(self) -> list:
        try:
            return json.loads(self.working_days_json or "[]")
        except Exception:
            return ["MON", "TUE", "WED", "THU", "FRI"]

    @property
    def calendar_holidays(self) -> list:
        try:
            return json.loads(self.calendar_holidays_json or "[]")
        except Exception:
            return []

    @property
    def schedule_health_reasons(self) -> list:
        try:
            return json.loads(self.schedule_health_reasons_json or "[]")
        except Exception:
            return []


class ProjectBaseline(Base):
    __tablename__ = "project_baselines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    total_duration_days = Column(Float, default=0.0, nullable=False)
    total_estimated_effort_hours = Column(Float, default=0.0, nullable=False)
    total_budget = Column(Float, default=0.0, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)

    project = relationship("Project", backref="baselines")
    creator = relationship("User", foreign_keys=[created_by])
    task_snapshots = relationship("BaselineTaskSnapshot", back_populates="baseline", cascade="all, delete-orphan")
    milestone_snapshots = relationship("BaselineMilestoneSnapshot", back_populates="baseline", cascade="all, delete-orphan")


class BaselineTaskSnapshot(Base):
    __tablename__ = "baseline_task_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    baseline_id = Column(Integer, ForeignKey("project_baselines.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    start_date = Column(String(50), nullable=True)
    due_date = Column(String(50), nullable=True)
    duration_days = Column(Float, default=1.0, nullable=False)
    progress_percent = Column(Float, default=0.0, nullable=False)
    estimated_effort_hours = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="Todo", nullable=False)
    priority = Column(String(50), default="Medium", nullable=False)
    assignee_id = Column(Integer, nullable=True)

    baseline = relationship("ProjectBaseline", back_populates="task_snapshots")


class BaselineMilestoneSnapshot(Base):
    __tablename__ = "baseline_milestone_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    baseline_id = Column(Integer, ForeignKey("project_baselines.id", ondelete="CASCADE"), nullable=False, index=True)
    milestone_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    due_date = Column(String(50), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)

    baseline = relationship("ProjectBaseline", back_populates="milestone_snapshots")


class ProjectBudget(Base):
    __tablename__ = "project_budgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    currency = Column(String(8), default="USD", nullable=False)
    total_budget = Column(Float, default=0.0, nullable=False)
    committed_cost = Column(Float, default=0.0, nullable=False)
    actual_cost = Column(Float, default=0.0, nullable=False)
    forecast_cost = Column(Float, default=0.0, nullable=False)
    
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", backref="budget")
    approver = relationship("User", foreign_keys=[approved_by])
    categories = relationship("ProjectBudgetCategory", back_populates="budget", cascade="all, delete-orphan")
    cost_records = relationship("ProjectCostRecord", back_populates="budget", cascade="all, delete-orphan")


class ProjectBudgetCategory(Base):
    __tablename__ = "project_budget_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    budget_id = Column(Integer, ForeignKey("project_budgets.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category_name = Column(String(64), nullable=False) # Personnel, Software, Infrastructure, Equipment, Services, External expenses, Other
    budgeted_amount = Column(Float, default=0.0, nullable=False)
    committed_amount = Column(Float, default=0.0, nullable=False)
    actual_amount = Column(Float, default=0.0, nullable=False)
    forecast_amount = Column(Float, default=0.0, nullable=False)

    budget = relationship("ProjectBudget", back_populates="categories")


class ProjectCostRecord(Base):
    __tablename__ = "project_cost_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    budget_id = Column(Integer, ForeignKey("project_budgets.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("project_budget_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    description = Column(String(255), nullable=False)
    amount = Column(Float, default=0.0, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    record_type = Column(String(32), default="ACTUAL", nullable=False) # ACTUAL, COMMITTED, ESTIMATED
    date_incurred = Column(DateTime, default=utc_now, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    budget = relationship("ProjectBudget", back_populates="cost_records")
    category = relationship("ProjectBudgetCategory")
    creator = relationship("User", foreign_keys=[created_by])


class ProjectScheduleScenario(Base):
    __tablename__ = "project_schedule_scenarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="DRAFT", nullable=False) # DRAFT, SIMULATED, APPLIED, ARCHIVED
    
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    applied_at = Column(DateTime, nullable=True)
    
    assumptions_json = Column(Text, default="{}", nullable=False)
    outcomes_json = Column(Text, default="{}", nullable=False)

    project = relationship("Project", backref="scenarios")
    creator = relationship("User", foreign_keys=[created_by])
    task_changes = relationship("ScenarioTaskChange", back_populates="scenario", cascade="all, delete-orphan")

    @property
    def assumptions(self) -> dict:
        try:
            return json.loads(self.assumptions_json or "{}")
        except Exception:
            return {}

    @property
    def outcomes(self) -> dict:
        try:
            return json.loads(self.outcomes_json or "{}")
        except Exception:
            return {}


class ScenarioTaskChange(Base):
    __tablename__ = "scenario_task_changes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("project_schedule_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    
    proposed_start_date = Column(String(50), nullable=True)
    proposed_due_date = Column(String(50), nullable=True)
    proposed_duration_days = Column(Float, nullable=True)
    proposed_priority = Column(String(50), nullable=True)
    proposed_assignee_id = Column(Integer, nullable=True)

    scenario = relationship("ProjectScheduleScenario", back_populates="task_changes")


class ProjectScheduleForecast(Base):
    __tablename__ = "project_schedule_forecasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    planned_completion_date = Column(DateTime, nullable=True)
    forecast_completion_date = Column(DateTime, nullable=True)
    schedule_variance_days = Column(Float, default=0.0, nullable=False)
    critical_path_duration_days = Column(Float, default=0.0, nullable=False)
    health_status = Column(String(32), default="ON_TRACK", nullable=False)
    confidence_score = Column(Float, default=0.85, nullable=False)
    calculation_factors_json = Column(Text, default="{}", nullable=False)
    calculated_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project", backref="forecasts")

    @property
    def calculation_factors(self) -> dict:
        try:
            return json.loads(self.calculation_factors_json or "{}")
        except Exception:
            return {}
