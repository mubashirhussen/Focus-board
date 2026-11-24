"""
Pydantic Schemas for Predictive Project Intelligence (Module B47).
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskEvidence(BaseModel):
    days_overdue: Optional[int] = None
    days_to_due: Optional[int] = None
    dependency_count: int = 0
    blocked_by_task_ids: List[str] = Field(default_factory=list)
    assignee_workload_hours: Optional[float] = None
    effort_slippage_ratio: Optional[float] = None


class TaskRiskItem(BaseModel):
    task_id: str
    task_title: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[str] = None
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: float  # 0-100
    primary_factors: List[str] = Field(default_factory=list)
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
    suggested_action: Optional[str] = None
    confidence: float = 0.85
    calculated_at: Optional[str] = None


class ProjectHealthDetail(BaseModel):
    project_id: int
    project_name: str
    health_score: float  # 0-100
    health_status: str  # HEALTHY, NEEDS_ATTENTION, AT_RISK, CRITICAL
    completion_rate: float
    total_tasks: int
    completed_tasks: int
    open_tasks: int
    overdue_tasks: int
    critical_unresolved_tasks: int
    blocked_tasks: int
    risk_factors: List[str] = Field(default_factory=list)
    positive_indicators: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    confidence_score: float = 0.90
    calculated_at: Optional[str] = None


class DeadlineForecastDetail(BaseModel):
    project_id: int
    project_name: str
    planned_completion_date: Optional[str] = None
    predicted_completion_date: str
    estimated_delay_days: float = 0.0
    confidence_interval_low: Optional[str] = None
    confidence_interval_high: Optional[str] = None
    confidence_score: float = 0.85
    critical_path_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    delay_factors: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    calculated_at: Optional[str] = None


class MemberWorkloadDetail(BaseModel):
    user_id: int
    name: str
    email: str
    assigned_tasks: int
    open_tasks: int
    overdue_tasks: int
    high_priority_tasks: int
    estimated_hours: float
    capacity_utilization_rate: float  # e.g. 112.5%
    workload_tier: str  # UNDERUTILIZED, BALANCED, OVERLOADED


class WorkloadAnalysisResponse(BaseModel):
    team_members: List[MemberWorkloadDetail] = Field(default_factory=list)
    overloaded_count: int = 0
    underutilized_count: int = 0
    balanced_count: int = 0
    average_utilization: float = 0.0
    rebalancing_proposals: List[Dict[str, Any]] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    id: int
    recommendation_key: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    category: str
    title: str
    description: str
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
    expected_impact: str
    priority: str
    status: str  # PENDING, ACCEPTED, REJECTED, COMPLETED
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[str] = None
    created_at: str


class IntelligenceOverviewResponse(BaseModel):
    overall_health_score: float
    overall_health_status: str
    total_projects: int
    projects_at_risk: int
    total_active_tasks: int
    high_risk_tasks_count: int
    critical_risk_tasks_count: int
    predicted_delays_count: int
    total_delayed_days: float
    resource_utilization_average: float
    overloaded_members_count: int
    active_recommendations_count: int
    last_updated: str


class PredictionAccuracyMetrics(BaseModel):
    total_predictions: int
    resolved_predictions: int
    mean_absolute_error_days: float
    risk_classification_accuracy: float
    forecast_coverage_rate: float
    method_distribution: Dict[str, int] = Field(default_factory=dict)


class PredictionHistoryItem(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    project_id: Optional[int] = None
    prediction_type: str
    original_prediction: Dict[str, Any] = Field(default_factory=dict)
    actual_outcome: Optional[Dict[str, Any]] = None
    accuracy_score: Optional[float] = None
    error_days: Optional[float] = None
    prediction_method: str
    model_version: str
    created_at: str
    resolved_at: Optional[str] = None


class IntelligenceSettingUpdate(BaseModel):
    high_risk_threshold: Optional[float] = None
    overdue_task_weight: Optional[float] = None
    dependency_blocker_weight: Optional[float] = None
    workload_overload_hours: Optional[float] = None
    alert_cooldown_hours: Optional[int] = None
    auto_alerts_enabled: Optional[bool] = None
    forecast_confidence_level: Optional[float] = None


class IntelligenceSettingResponse(BaseModel):
    high_risk_threshold: float
    overdue_task_weight: float
    dependency_blocker_weight: float
    workload_overload_hours: float
    alert_cooldown_hours: int
    auto_alerts_enabled: bool
    forecast_confidence_level: float
    updated_at: str
