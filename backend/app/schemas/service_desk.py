"""
Pydantic Schemas for Service Desk & SLA Management (Module B52).
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ServiceDeskCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    default_priority: str = Field("MEDIUM", max_length=20)
    is_active: bool = True
    display_order: int = 0


class ServiceDeskCategoryCreate(ServiceDeskCategoryBase):
    pass


class ServiceDeskCategoryResponse(ServiceDeskCategoryBase):
    id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceDeskSLAPolicyBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    first_response_target_minutes: int = Field(60, ge=1)
    resolution_target_minutes: int = Field(480, ge=1)
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00"
    work_days: str = "MON,TUE,WED,THU,FRI"
    timezone: str = "UTC"
    applies_to_categories_json: Optional[str] = "[]"
    applies_to_priorities_json: Optional[str] = "[]"
    allow_pause_on_waiting: bool = True
    at_risk_threshold_percentage: float = 80.0


class ServiceDeskSLAPolicyCreate(ServiceDeskSLAPolicyBase):
    pass


class ServiceDeskSLAPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    first_response_target_minutes: Optional[int] = None
    resolution_target_minutes: Optional[int] = None
    business_hours_start: Optional[str] = None
    business_hours_end: Optional[str] = None
    work_days: Optional[str] = None
    allow_pause_on_waiting: Optional[bool] = None
    at_risk_threshold_percentage: Optional[float] = None


class ServiceDeskSLAPolicyResponse(ServiceDeskSLAPolicyBase):
    id: int
    organization_id: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceDeskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal_note: bool = False


class ServiceDeskCommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    is_internal_note: bool
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceDeskAssignRequest(BaseModel):
    agent_id: Optional[int] = None
    team_id: Optional[int] = None
    notes: Optional[str] = None


class ServiceDeskStatusTransitionRequest(BaseModel):
    status: str = Field(..., max_length=32)
    resolution_notes: Optional[str] = None


class ServiceDeskEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    bump_priority: Optional[str] = None
    reassign_team_id: Optional[int] = None


class ServiceDeskTicketCreate(BaseModel):
    subject: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=2)
    category_name: str = "Technical Support"
    category_id: Optional[int] = None
    priority: str = "MEDIUM"
    workspace_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    related_project_id: Optional[int] = None
    related_task_id: Optional[int] = None
    tags: Optional[List[str]] = None
    source: str = "PORTAL"


class ServiceDeskTicketResponse(BaseModel):
    id: int
    ticket_number: str
    organization_id: int
    workspace_id: Optional[int] = None
    subject: str
    description: str
    requester_id: int
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    assigned_agent_name: Optional[str] = None
    assigned_team_id: Optional[int] = None
    assigned_team_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: str
    priority: str
    status: str
    source: str
    sla_policy_id: Optional[int] = None
    first_response_due_at: Optional[datetime] = None
    resolution_due_at: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    reopened_at: Optional[datetime] = None
    sla_response_status: str
    sla_resolution_status: str
    total_sla_pause_minutes: float
    resolution_notes: Optional[str] = None
    related_project_id: Optional[int] = None
    related_task_id: Optional[int] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceDeskEscalationRuleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    trigger_type: str = "SLA_BREACH"
    threshold_minutes: int = 60
    target_action: str = "NOTIFY_ADMIN"
    target_agent_id: Optional[int] = None
    target_team_id: Optional[int] = None
    target_priority: Optional[str] = None
    is_enabled: bool = True


class ServiceDeskEscalationRuleResponse(ServiceDeskEscalationRuleCreate):
    id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceDeskDashboardResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    new_tickets: int
    unassigned_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    overdue_tickets: int
    at_risk_tickets: int
    breached_tickets: int
    avg_first_response_minutes: float
    avg_resolution_minutes: float
    sla_compliance_rate: float
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    by_category: Dict[str, int]
