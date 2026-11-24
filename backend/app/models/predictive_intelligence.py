"""
FocusBoard Predictive Project Intelligence Models (Module B47).
Provides database entities for project health scoring, task risk prediction,
deadline forecasting, workload analytics, AI recommendations, prediction history, and settings.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectHealthSnapshot(Base):
    __tablename__ = "project_health_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Health score 0-100
    health_score = Column(Float, nullable=False, default=100.0)
    # HEALTHY, NEEDS_ATTENTION, AT_RISK, CRITICAL
    health_status = Column(String(32), nullable=False, default="HEALTHY", index=True)
    
    risk_factors_json = Column(Text, default="[]", nullable=False)
    positive_indicators_json = Column(Text, default="[]", nullable=False)
    recommended_actions_json = Column(Text, default="[]", nullable=False)
    
    confidence_score = Column(Float, default=0.9, nullable=False)
    metrics_json = Column(Text, default="{}", nullable=False)
    
    calculated_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    project = relationship("Project")

    @property
    def risk_factors(self) -> list:
        try:
            return json.loads(self.risk_factors_json or "[]")
        except Exception:
            return []

    @property
    def positive_indicators(self) -> list:
        try:
            return json.loads(self.positive_indicators_json or "[]")
        except Exception:
            return []

    @property
    def recommended_actions(self) -> list:
        try:
            return json.loads(self.recommended_actions_json or "[]")
        except Exception:
            return []

    @property
    def metrics(self) -> dict:
        try:
            return json.loads(self.metrics_json or "{}")
        except Exception:
            return {}


class TaskRiskPrediction(Base):
    __tablename__ = "task_risk_predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # LOW, MEDIUM, HIGH, CRITICAL
    risk_level = Column(String(32), nullable=False, default="LOW", index=True)
    risk_score = Column(Float, nullable=False, default=0.0)
    
    primary_factors_json = Column(Text, default="[]", nullable=False)
    supporting_evidence_json = Column(Text, default="{}", nullable=False)
    suggested_action = Column(Text, nullable=True)
    confidence = Column(Float, default=0.85, nullable=False)
    
    calculated_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    task = relationship("Task")
    project = relationship("Project")

    @property
    def primary_factors(self) -> list:
        try:
            return json.loads(self.primary_factors_json or "[]")
        except Exception:
            return []

    @property
    def supporting_evidence(self) -> dict:
        try:
            return json.loads(self.supporting_evidence_json or "{}")
        except Exception:
            return {}


class DeadlineForecast(Base):
    __tablename__ = "deadline_forecasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    planned_completion_date = Column(DateTime, nullable=True)
    predicted_completion_date = Column(DateTime, nullable=False)
    estimated_delay_days = Column(Float, default=0.0, nullable=False)
    
    confidence_interval_low = Column(DateTime, nullable=True)
    confidence_interval_high = Column(DateTime, nullable=True)
    confidence_score = Column(Float, default=0.85, nullable=False)
    
    delay_factors_json = Column(Text, default="[]", nullable=False)
    critical_path_tasks_json = Column(Text, default="[]", nullable=False)
    recommended_actions_json = Column(Text, default="[]", nullable=False)
    
    calculated_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    project = relationship("Project")

    @property
    def delay_factors(self) -> list:
        try:
            return json.loads(self.delay_factors_json or "[]")
        except Exception:
            return []

    @property
    def critical_path_tasks(self) -> list:
        try:
            return json.loads(self.critical_path_tasks_json or "[]")
        except Exception:
            return []

    @property
    def recommended_actions(self) -> list:
        try:
            return json.loads(self.recommended_actions_json or "[]")
        except Exception:
            return []


class WorkloadSnapshot(Base):
    __tablename__ = "workload_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    assigned_tasks_count = Column(Integer, default=0, nullable=False)
    open_tasks_count = Column(Integer, default=0, nullable=False)
    overdue_tasks_count = Column(Integer, default=0, nullable=False)
    estimated_minutes_total = Column(Integer, default=0, nullable=False)
    capacity_utilization_rate = Column(Float, default=0.0, nullable=False)
    # UNDERUTILIZED, BALANCED, OVERLOADED
    workload_tier = Column(String(32), default="BALANCED", nullable=False, index=True)
    
    calculated_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User")
    project = relationship("Project")


class AIProjectRecommendation(Base):
    __tablename__ = "ai_project_recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recommendation_key = Column(String(64), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # RESOURCE_REBALANCE, DEADLINE_ADJUSTMENT, DEPENDENCY_BLOCKER, PRIORITY_ESCALATION, RISK_MITIGATION
    category = Column(String(64), default="RISK_MITIGATION", nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    supporting_evidence_json = Column(Text, default="{}", nullable=False)
    expected_impact = Column(String(255), nullable=False)
    priority = Column(String(32), default="MEDIUM", nullable=False, index=True)
    
    # PENDING, ACCEPTED, REJECTED, COMPLETED
    status = Column(String(32), default="PENDING", nullable=False, index=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    project = relationship("Project")
    task = relationship("Task")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    @property
    def supporting_evidence(self) -> dict:
        try:
            return json.loads(self.supporting_evidence_json or "{}")
        except Exception:
            return {}


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_type = Column(String(32), nullable=False, index=True)  # PROJECT, TASK
    entity_id = Column(String(64), nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    prediction_type = Column(String(64), nullable=False, index=True)  # HEALTH_SCORE, TASK_RISK, DEADLINE_FORECAST
    
    original_prediction_json = Column(Text, nullable=False)
    updated_prediction_json = Column(Text, nullable=True)
    actual_outcome_json = Column(Text, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    error_days = Column(Float, nullable=True)
    
    prediction_method = Column(String(64), default="STATISTICAL", nullable=False)  # RULE_BASED, STATISTICAL, ML_MODEL
    model_version = Column(String(32), default="v1.0", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    @property
    def original_prediction(self) -> dict:
        try:
            return json.loads(self.original_prediction_json or "{}")
        except Exception:
            return {}

    @property
    def actual_outcome(self) -> dict:
        try:
            return json.loads(self.actual_outcome_json or "{}")
        except Exception:
            return {}


class IntelligenceSetting(Base):
    __tablename__ = "intelligence_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    high_risk_threshold = Column(Float, default=70.0, nullable=False)
    overdue_task_weight = Column(Float, default=0.35, nullable=False)
    dependency_blocker_weight = Column(Float, default=0.25, nullable=False)
    workload_overload_hours = Column(Float, default=40.0, nullable=False)
    alert_cooldown_hours = Column(Integer, default=24, nullable=False)
    auto_alerts_enabled = Column(Boolean, default=True, nullable=False)
    forecast_confidence_level = Column(Float, default=0.85, nullable=False)
    settings_json = Column(Text, default="{}", nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    @property
    def extra_settings(self) -> dict:
        try:
            return json.loads(self.settings_json or "{}")
        except Exception:
            return {}
