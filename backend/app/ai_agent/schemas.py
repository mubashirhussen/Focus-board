from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# 1. Agent Schemas
class AIAgentResponse(BaseModel):
    id: str
    name: str
    description: str
    agent_type: str
    model_name: str
    tools: List[str]
    is_system: bool
    created_at: datetime

# 2. Execution Step Schemas
class AIAgentExecutionStepResponse(BaseModel):
    id: int
    step_index: int
    description: str
    tool_name: str
    arguments: Dict[str, Any]
    requires_approval: bool
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# 3. Approval Schemas
class AIAgentApprovalResponse(BaseModel):
    id: str
    execution_id: str
    step_id: Optional[int] = None
    action_type: str
    reason: str
    target_resource: str
    proposed_payload: Dict[str, Any]
    status: str
    resolved_at: Optional[datetime] = None
    created_at: datetime

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    feedback: Optional[str] = None

# 4. Execution Schemas
class AIAgentExecutionCreate(BaseModel):
    agent_id: str
    prompt: str = Field(..., min_length=3, max_length=2000)
    workspace_id: Optional[int] = None
    auto_execute_safe: bool = True  # Automatically execute non-sensitive steps

class AIAgentExecutionResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    prompt: str
    status: str
    current_step_index: int
    total_steps: int
    error_message: Optional[str] = None
    tokens_used: int
    cost_estimate_cents: int
    steps: List[AIAgentExecutionStepResponse] = []
    pending_approvals: List[AIAgentApprovalResponse] = []
    created_at: datetime
    completed_at: Optional[datetime] = None

# 5. Persistent Memory Preferences
class AIPersistentPreferenceUpdate(BaseModel):
    planning_style: Optional[str] = Field(None, description="balanced, aggressive, relaxed, deep_work")
    preferred_work_hours: Optional[int] = Field(None, ge=1, le=16)
    summary_format: Optional[str] = Field(None, description="bullet_points, narrative, actionable_checklist")
    prioritization_approach: Optional[str] = Field(None, description="deadline_first, impact_first, quick_wins")
    personalization_enabled: Optional[bool] = None

class AIPersistentPreferenceResponse(BaseModel):
    planning_style: str
    preferred_work_hours: int
    summary_format: str
    prioritization_approach: str
    personalization_enabled: bool
    updated_at: datetime
