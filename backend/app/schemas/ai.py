from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# -------------------------------------------------------------
# Base Assistant & Chat Models
# -------------------------------------------------------------

class TaskPriorityRecommendation(BaseModel):
    task_id: str
    title: str
    current_priority: str
    suggested_priority: str
    priority_score: int  # 0 to 100
    urgency: str  # "Critical", "High", "Moderate", "Normal"
    due_date: Optional[str] = None
    reason: str
    suggested_action: str

class DailyPlanRequest(BaseModel):
    planning_date: Optional[str] = None  # YYYY-MM-DD
    available_hours: float = Field(6.0, ge=1.0, le=14.0)
    preferred_category: Optional[str] = None

class PlannedTaskItem(BaseModel):
    task_id: str
    title: str
    category: str
    priority: str
    estimated_minutes: int
    time_block: str
    selection_reason: str

class DailyPlanResponse(BaseModel):
    planning_date: str
    available_hours: float
    allocated_hours: float
    recommended_tasks: List[PlannedTaskItem]
    deferred_tasks_count: int
    planning_assumptions: str
    break_suggestions: List[str]

class SubtaskProposal(BaseModel):
    title: str
    estimated_minutes: int
    order: int
    preparation: str
    completion_criteria: str
    priority: Optional[str] = "Medium"

class TaskBreakdownRequest(BaseModel):
    task_id: Optional[str] = None
    task_title: str = Field(..., min_length=2, max_length=255)
    task_description: Optional[str] = ""
    category: Optional[str] = "Design"
    target_deadline: Optional[str] = None

class TaskBreakdownResponse(BaseModel):
    task_title: str
    proposed_subtasks: List[SubtaskProposal]
    possible_blockers: List[str]
    summary: str

class WorkloadAnalysisResponse(BaseModel):
    total_active_tasks: int
    overdue_count: int
    due_today_count: int
    high_priority_count: int
    estimated_total_hours: float
    workload_assessment: str  # "Balanced", "Heavy", "Critical"
    bottlenecks: List[str]
    suggested_adjustments: List[str]

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str

class ActionProposal(BaseModel):
    proposal_id: str
    action_type: str  # "update_priority" | "create_subtask" | "reschedule"
    task_id: Optional[str] = None
    description: str
    payload: Dict[str, Any]

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[ChatMessage]] = []
    conversation_id: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    task_references: List[str] = []
    proposed_actions: List[ActionProposal] = []
    tokens_used: int = 0
    provider: Optional[str] = None
    model: Optional[str] = None

class ApproveActionRequest(BaseModel):
    action_type: str
    task_id: Optional[str] = None
    payload: Dict[str, Any]

# -------------------------------------------------------------
# Conversation Models (Phase B13)
# -------------------------------------------------------------

class AIConversationCreate(BaseModel):
    title: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    context_type: str = "GENERAL"  # GENERAL, WORKSPACE, PROJECT, TASK
    context_id: Optional[str] = None

class AIConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    is_archived: Optional[bool] = None

class AIMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model: Optional[str] = None
    provider: Optional[str] = None
    tokens_input: int
    tokens_output: int
    total_tokens: int
    task_references: List[str] = []
    proposed_actions: List[Dict[str, Any]] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AIConversationResponse(BaseModel):
    id: str
    user_id: int
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    title: str
    context_type: str
    context_id: Optional[str] = None
    status: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class AIConversationDetailResponse(AIConversationResponse):
    messages: List[AIMessageResponse] = []

# -------------------------------------------------------------
# Task Assistance Models (Phase B13)
# -------------------------------------------------------------

class TaskDescriptionRequest(BaseModel):
    task_title: str = Field(..., min_length=2, max_length=255)
    category: Optional[str] = "Engineering"
    context: Optional[str] = None
    project_id: Optional[int] = None

class TaskDescriptionResponse(BaseModel):
    task_title: str
    generated_description: str
    acceptance_criteria: List[str] = []
    suggested_labels: List[str] = []

class TaskDecomposeRequest(BaseModel):
    task_id: Optional[str] = None
    task_title: str = Field(..., min_length=2, max_length=255)
    task_description: Optional[str] = None
    category: Optional[str] = "Engineering"

class DecomposedSubtask(BaseModel):
    title: str
    description: str
    estimated_minutes: int
    priority: str
    order: int
    acceptance_criteria: str

class TaskDecomposeResponse(BaseModel):
    task_title: str
    subtasks: List[DecomposedSubtask]
    summary: str

class TaskPlanRequest(BaseModel):
    task_id: Optional[str] = None
    task_title: str = Field(..., min_length=2, max_length=255)
    category: Optional[str] = "General"

class TaskPlanStep(BaseModel):
    order: int
    action: str
    estimated_minutes: int
    checkpoint: str

class TaskPlanResponse(BaseModel):
    task_title: str
    steps: List[TaskPlanStep]
    estimated_total_minutes: int
    potential_blockers: List[str] = []
    recommended_focus: str

class TaskCreateAssistRequest(BaseModel):
    user_prompt: str = Field(..., min_length=3, max_length=2000)
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None

class TaskCreateAssistResponse(BaseModel):
    suggested_title: str
    suggested_description: str
    category: str
    priority: str
    estimated_minutes: int
    suggested_deadline_days: int
    acceptance_criteria: List[str] = []
    labels: List[str] = []

# -------------------------------------------------------------
# Project Assistance Models (Phase B13)
# -------------------------------------------------------------

class ProjectSummaryResponse(BaseModel):
    project_id: int
    project_name: str
    health: str
    progress_percent: float
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    executive_summary: str
    key_highlights: List[str] = []
    recommended_actions: List[str] = []

class ProjectPlanRequest(BaseModel):
    project_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    target_timeline_days: Optional[int] = 30

class ProjectPlanPhase(BaseModel):
    name: str
    suggested_duration_days: int
    suggested_tasks: List[str]
    risk_factors: List[str]

class ProjectPlanResponse(BaseModel):
    project_name: str
    objectives: List[str]
    phases: List[ProjectPlanPhase]
    estimated_total_days: int

class ProjectRiskItem(BaseModel):
    severity: str  # High, Medium, Low
    category: str
    description: str
    mitigation_strategy: str

class ProjectRiskResponse(BaseModel):
    project_id: int
    project_name: str
    risk_level: str  # Low, Moderate, High, Critical
    risk_score: float
    summary: str
    identified_risks: List[ProjectRiskItem]
    recommended_actions: List[str]

# -------------------------------------------------------------
# Analytics Interpretation Models (Phase B13)
# -------------------------------------------------------------

class AnalyticsInterpretRequest(BaseModel):
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    days: int = 14

class AnalyticsInterpretResponse(BaseModel):
    summary: str
    completion_velocity_assessment: str
    workload_distribution_assessment: str
    identified_bottlenecks: List[str] = []
    recommendations: List[str] = []

# -------------------------------------------------------------
# Usage & Cost Models (Phase B13)
# -------------------------------------------------------------

class AIUsageLogItem(BaseModel):
    id: int
    feature: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_cents: float
    latency_ms: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AIUsageSummaryResponse(BaseModel):
    total_requests: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    estimated_cost_cents: float
    usage_by_feature: Dict[str, int] = {}
    usage_by_provider: Dict[str, int] = {}
    recent_logs: List[AIUsageLogItem] = []

# -------------------------------------------------------------
# Smart Prioritization & Next Best Task Models
# -------------------------------------------------------------

class NextBestTaskResponse(BaseModel):
    task_id: Optional[str] = None
    title: str
    category: str = "General"
    priority: str = "High"
    due_date: Optional[str] = None
    estimated_minutes: int = 45
    priority_score: int = 85
    urgency_tier: str = "Critical"  # Critical, High, Moderate, Normal
    explainability_tags: List[str] = []
    rationale: str
    suggested_action: str
    confidence_score: float = 94.0
    ranked_queue: List[TaskPriorityRecommendation] = []

# -------------------------------------------------------------
# Adaptive Focus Mode & Session Models
# -------------------------------------------------------------

class FocusSessionCreate(BaseModel):
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    duration_minutes: int = Field(25, ge=1, le=240)
    completed: bool = False
    notes: Optional[str] = None
    interruptions: int = 0

class FocusSessionResponse(BaseModel):
    id: str
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    duration_minutes: int
    completed: bool
    notes: Optional[str] = None
    interruptions: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FocusSessionStatsResponse(BaseModel):
    total_focus_minutes: int
    completed_sessions_count: int
    today_focus_minutes: int
    current_streak_days: int
    recent_sessions: List[FocusSessionResponse] = []

# -------------------------------------------------------------
# Predictive Project Risk Models
# -------------------------------------------------------------

class PredictiveRiskItem(BaseModel):
    category: str  # Schedule, Dependency, Workload, Scope
    severity: str  # Critical, High, Medium, Low
    description: str
    impact: str
    mitigation_strategy: str

class PredictiveProjectRiskResponse(BaseModel):
    overall_risk_score: float  # 0 to 100
    risk_level: str  # LOW, MODERATE, ELEVATED, CRITICAL
    predicted_completion_date: str
    schedule_variance_days: int  # positive = delayed, negative = ahead
    confidence_interval_days: int
    critical_blockers_count: int
    identified_risks: List[PredictiveRiskItem] = []
    key_recommendations: List[str] = []

# -------------------------------------------------------------
# Team Workload & Capacity Models
# -------------------------------------------------------------

class MemberCapacityItem(BaseModel):
    user_id: int
    name: str
    email: str
    avatar_initials: str
    assigned_tasks_count: int
    allocated_hours: float
    capacity_hours: float = 40.0
    utilization_pct: float
    workload_status: str  # "OPTIMAL", "OVERLOADED", "AVAILABLE"
    top_task_titles: List[str] = []

class TeamCapacityAnalysisResponse(BaseModel):
    workspace_name: str
    total_members: int
    team_utilization_pct: float
    overloaded_members_count: int
    available_capacity_hours: float
    members: List[MemberCapacityItem] = []
    rebalancing_recommendations: List[str] = []

# -------------------------------------------------------------
# Meeting Intelligence & Decision Models
# -------------------------------------------------------------

class MeetingActionItem(BaseModel):
    action_id: str
    title: str
    description: Optional[str] = None
    suggested_assignee: Optional[str] = None
    suggested_due_date: Optional[str] = None
    priority: str = "Medium"
    converted_task_id: Optional[str] = None

class MeetingRecordCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    notes_raw: str = Field(..., min_length=5)
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    participants: Optional[str] = "[]"
    meeting_date: Optional[str] = None

class MeetingIntelligenceAnalysisResponse(BaseModel):
    meeting_id: str
    title: str
    summary: str
    decisions: List[str] = []
    action_items: List[MeetingActionItem] = []
    meeting_date: str

class ConvertActionItemRequest(BaseModel):
    meeting_id: Optional[str] = None
    action_id: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None

class ConvertActionItemResponse(BaseModel):
    task_id: str
    title: str
    status: str
    message: str

class DecisionLogCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    context: str = Field(..., min_length=5)
    rationale: str = Field(..., min_length=5)
    alternatives: Optional[str] = None
    impact: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    status: str = "APPROVED"  # PROPOSED, APPROVED, SUPERSEDED
    owner_name: Optional[str] = "Team Lead"
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None

class DecisionLogResponse(BaseModel):
    id: str
    title: str
    context: str
    rationale: str
    alternatives: Optional[str] = None
    impact: str
    status: str
    owner_name: str
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

