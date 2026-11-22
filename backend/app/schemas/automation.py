from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Workflow Core ---
class AutomationWorkflowBase(BaseModel):
    name: str
    description: str
    workflow_type: str = Field(default="EVENT_DRIVEN", description="EVENT_DRIVEN, SCHEDULED, MANUAL, APPROVAL_CHAIN")
    status: str = Field(default="DRAFT", description="DRAFT, ACTIVE, PAUSED, DISABLED, ARCHIVED")
    trigger_type: str = Field(default="EVENT", description="EVENT, SCHEDULE, MANUAL, WEBHOOK")
    trigger_config_json: str = "{}"
    nodes_json: str = "[]"
    edges_json: str = "[]"
    variables_json: str = "{}"
    execution_settings_json: str = '{"max_retries": 3, "timeout_seconds": 60, "error_policy": "STOP"}'
    version: str = "1.0"
    is_template: bool = False
    template_category: Optional[str] = None

class AutomationWorkflowCreate(AutomationWorkflowBase):
    workspace_id: Optional[int] = None

class AutomationWorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_type: Optional[str] = None
    status: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config_json: Optional[str] = None
    nodes_json: Optional[str] = None
    edges_json: Optional[str] = None
    variables_json: Optional[str] = None
    execution_settings_json: Optional[str] = None
    version: Optional[str] = None
    change_summary: Optional[str] = None

class AutomationWorkflowResponse(AutomationWorkflowBase):
    id: str
    workspace_id: Optional[int] = None
    owner_id: Optional[int] = None
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0
    failure_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Workflow Versions ---
class AutomationWorkflowVersionResponse(BaseModel):
    id: str
    workflow_id: str
    version: str
    nodes_json: str
    edges_json: str
    change_summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Workflow Execution ---
class TriggerWorkflowRequest(BaseModel):
    trigger_event: str = "MANUAL"
    payload: Dict[str, Any] = {}
    dry_run: bool = False

class AutomationExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    workflow_version: str
    trigger_event: str
    status: str
    context_json: str
    current_node_id: Optional[str] = None
    results_json: str
    error_message: Optional[str] = None
    retry_count: int = 0
    duration_ms: int = 0
    correlation_id: str
    actor_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Execution Logs ---
class AutomationExecutionLogResponse(BaseModel):
    id: str
    execution_id: str
    node_id: str
    node_name: str
    node_type: str
    status: str
    input_data_json: str
    output_data_json: str
    error_details: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Approvals ---
class AutomationApprovalResponse(BaseModel):
    id: str
    execution_id: str
    node_id: str
    approval_type: str
    title: str
    description: str
    context_summary: str
    status: str
    assigned_approver_id: Optional[int] = None
    decision_by_id: Optional[int] = None
    decision_comments: Optional[str] = None
    decision_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="APPROVED, REJECTED")
    comments: Optional[str] = None

# --- Schedules ---
class AutomationScheduleBase(BaseModel):
    cron_expression: str = "0 9 * * 1-5"
    timezone: str = "UTC"
    is_active: bool = True

class AutomationScheduleCreate(AutomationScheduleBase):
    workflow_id: str

class AutomationScheduleResponse(AutomationScheduleBase):
    id: str
    workflow_id: str
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- AI Workflow Generator ---
class AIWorkflowGenerateRequest(BaseModel):
    prompt: str = Field(..., description="e.g. When a task becomes overdue, notify owner and create an escalation task.")
    category: str = "TASK"

class AIWorkflowNode(BaseModel):
    id: str
    type: str  # trigger, condition, action, branch, approval, delay, end
    name: str
    config: Dict[str, Any] = {}

class AIWorkflowEdge(BaseModel):
    source: str
    target: str
    condition_branch: Optional[str] = None  # "true", "false", "default"

class AIWorkflowGenerateResponse(BaseModel):
    workflow_name: str
    description: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    nodes: List[AIWorkflowNode]
    edges: List[AIWorkflowEdge]
    explanation: str
    suggested_variables: Dict[str, str] = {}

# --- Dashboard Overview ---
class AutomationDashboardOverviewResponse(BaseModel):
    total_workflows_count: int
    active_workflows_count: int
    draft_workflows_count: int
    paused_workflows_count: int
    total_executions_count: int
    successful_executions_count: int
    failed_executions_count: int
    pending_approvals_count: int
    execution_success_rate: float
    estimated_hours_saved: float
    recent_executions: List[AutomationExecutionResponse] = []
    pending_approvals: List[AutomationApprovalResponse] = []
    templates: List[AutomationWorkflowResponse] = []
