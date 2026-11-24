"""
Pydantic Schemas for Goals, OKRs & Milestones Management (Module B50).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    goal_level: str = "ORGANIZATIONAL"  # ORGANIZATIONAL, TEAM, INDIVIDUAL, PROJECT
    parent_goal_id: Optional[str] = None
    team_id: Optional[int] = None
    workspace_id: Optional[int] = None
    owner_id: Optional[int] = None
    priority: str = "HIGH"
    status: str = "ACTIVE"
    category: str = "STRATEGY"
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goal_level: Optional[str] = None
    parent_goal_id: Optional[str] = None
    team_id: Optional[int] = None
    owner_id: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    tags: Optional[List[str]] = None


class GoalStatusTransition(BaseModel):
    status: str
    reason: Optional[str] = None


class KeyResultCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    measurement_type: str = "NUMERIC_INCREASE"
    starting_value: float = 0.0
    current_value: Optional[float] = None
    target_value: float = 100.0
    unit: str = "%"
    weight: float = 1.0
    tracking_method: str = "MANUAL"
    due_date: Optional[str] = None
    owner_id: Optional[int] = None


class KeyResultUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    measurement_type: Optional[str] = None
    starting_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    weight: Optional[float] = None
    tracking_method: Optional[str] = None
    due_date: Optional[str] = None
    owner_id: Optional[int] = None


class KeyResultProgressUpdate(BaseModel):
    current_value: float
    comment: Optional[str] = None


class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    key_result_id: Optional[str] = None
    project_id: Optional[int] = None
    priority: str = "MEDIUM"
    status: str = "NOT_STARTED"
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    owner_id: Optional[int] = None
    notes: Optional[str] = None


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    key_result_id: Optional[str] = None
    project_id: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    progress_percent: Optional[float] = None
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    blocked_reason: Optional[str] = None
    notes: Optional[str] = None


class MilestoneDependencyCreate(BaseModel):
    depends_on_milestone_id: str


class GoalCheckInCreate(BaseModel):
    progress_percent: Optional[float] = None
    confidence_score: int = Field(default=4, ge=1, le=5)
    summary: str = Field(..., min_length=3)
    blockers: Optional[str] = None
    next_steps: Optional[str] = None
    support_needed: Optional[str] = None


class GoalCheckInReview(BaseModel):
    feedback: str = Field(..., min_length=2)


class GoalProjectLinkCreate(BaseModel):
    project_id: int


class KeyResultTaskLinkCreate(BaseModel):
    task_id: str
    weight: float = 1.0


class GoalCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class GoalSettingsUpdate(BaseModel):
    check_in_frequency: Optional[str] = "WEEKLY"
    auto_recalculate_progress: Optional[bool] = True
    enable_ai_recommendations: Optional[bool] = True
    rules_config: Optional[Dict[str, Any]] = None
