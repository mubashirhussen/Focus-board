from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class ProductivityMetricsResponse(BaseModel):
    tasks_total: int
    tasks_completed: int
    tasks_pending: int
    tasks_overdue: int
    completion_rate: float
    completed_on_time: int
    rescheduled_count: int
    priority_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]

class PatternItem(BaseModel):
    pattern_type: str
    title: str
    description: str
    evidence_count: int
    strength: str  # HIGH, MEDIUM, LOW

class InsightItem(BaseModel):
    id: str
    type: str  # DEADLINE_ALERT, WORKLOAD_CONCENTRATION, BOTTLENECK, MOMENTUM
    title: str
    description: str
    evidence: str
    urgency: str  # HIGH, MEDIUM, LOW
    recommended_action: str
    task_id: Optional[str] = None
    is_dismissed: bool = False

class RecommendationItem(BaseModel):
    id: str
    task_id: str
    title: str
    priority: str
    reason: str
    suggested_time: Optional[datetime] = None
    estimated_duration_minutes: int
    deadline_risk: str  # IMMINENT, MODERATE, LOW

class CoachRequest(BaseModel):
    message: str

class CoachResponse(BaseModel):
    reply: str
    suggested_actions: List[Dict[str, Any]] = []
    data_context_summary: str

class FeedbackRequest(BaseModel):
    feedback_type: str  # helpful, not_helpful, dismissed
    notes: Optional[str] = None

class IntelligencePreferenceUpdate(BaseModel):
    insights_enabled: Optional[bool] = None
    coaching_enabled: Optional[bool] = None
    work_start_hour: Optional[int] = None
    work_end_hour: Optional[int] = None
    time_zone: Optional[str] = None

class IntelligencePreferenceResponse(BaseModel):
    insights_enabled: bool
    coaching_enabled: bool
    work_start_hour: int
    work_end_hour: int
    time_zone: str

    model_config = ConfigDict(from_attributes=True)
