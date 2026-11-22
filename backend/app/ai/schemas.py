from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

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
    planning_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
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

class TaskBreakdownRequest(BaseModel):
    task_id: Optional[str] = None
    task_title: str = Field(..., min_length=2, max_length=255)
    task_description: Optional[str] = ""
    category: Optional[str] = "Design"
    target_deadline: Optional[str] = None

class SubtaskProposal(BaseModel):
    title: str
    estimated_minutes: int
    order: int
    preparation: str
    completion_criteria: str

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

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[ChatMessage]] = []

class ActionProposal(BaseModel):
    proposal_id: str
    action_type: str  # "update_priority" | "create_subtask" | "reschedule"
    task_id: Optional[str] = None
    description: str
    payload: Dict[str, Any]

class ChatResponse(BaseModel):
    reply: str
    task_references: List[str] = []
    proposed_actions: List[ActionProposal] = []

class ApproveActionRequest(BaseModel):
    action_type: str
    task_id: Optional[str] = None
    payload: Dict[str, Any]
