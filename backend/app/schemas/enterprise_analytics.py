from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Milestones
class ProjectMilestoneCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = Field("PENDING", pattern="^(PENDING|IN_PROGRESS|COMPLETED|DELAYED)$")

class ProjectMilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(PENDING|IN_PROGRESS|COMPLETED|DELAYED)$")
    completed_at: Optional[datetime] = None

class ProjectMilestoneResponse(BaseModel):
    id: str
    project_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Risks
class ProjectRiskCreate(BaseModel):
    category: str = Field(..., pattern="^(SCHEDULE|WORKLOAD|DEPENDENCY|EXECUTION)$")
    severity: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    title: str = Field(..., max_length=255)
    description: str
    mitigation_plan: Optional[str] = None

class ProjectRiskUpdate(BaseModel):
    category: Optional[str] = Field(None, pattern="^(SCHEDULE|WORKLOAD|DEPENDENCY|EXECUTION)$")
    severity: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|MITIGATED|RESOLVED)$")
    mitigation_plan: Optional[str] = None

class ProjectRiskResponse(BaseModel):
    id: str
    project_id: int
    category: str
    severity: str
    title: str
    description: str
    status: str
    mitigation_plan: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Resource Capacity
class ResourceCapacityCreate(BaseModel):
    user_id: int
    weekly_hours_capacity: float = Field(..., ge=1.0, le=168.0)
    effective_date: Optional[datetime] = None

class ResourceCapacityResponse(BaseModel):
    id: str
    user_id: int
    workspace_id: int
    weekly_hours_capacity: float
    effective_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Workload Member
class TeamMemberWorkload(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    assigned_tasks_count: int
    completed_tasks_count: int
    weekly_capacity_hours: float
    estimated_allocated_hours: float
    utilization_rate: float  # (allocated / capacity) * 100
    status: str  # OPTIMAL, OVERLOADED, UNDERUTILIZED

class TeamWorkloadResponse(BaseModel):
    workspace_id: int
    total_members: int
    total_active_tasks: int
    total_capacity_hours: float
    total_allocated_hours: float
    average_utilization_rate: float
    members: List[TeamMemberWorkload]

# Project Health & Signals
class ProjectHealthResponse(BaseModel):
    project_id: int
    project_name: str
    status: str
    deadline: Optional[Union[datetime, str]] = None
    health_score: int  # 0 to 100
    health_status: str  # HEALTHY, AT_RISK, CRITICAL, INSUFFICIENT_DATA
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    in_progress_tasks: int
    completion_rate: float  # Percentage
    velocity_trend: str  # INCREASING, STABLE, DECLINING, UNKNOWN
    signals: List[str]
    forecast: Dict[str, Any]
    active_risks_count: int
    milestones_total: int
    milestones_completed: int

class PortfolioHealthResponse(BaseModel):
    workspace_id: int
    total_projects: int
    healthy_count: int
    at_risk_count: int
    critical_count: int
    insufficient_data_count: int
    average_health_score: float
    average_completion_rate: float
    risk_distribution: Dict[str, int]
    projects: List[ProjectHealthResponse]

class ExecutiveKPISummary(BaseModel):
    workspace_id: int
    total_projects: int
    active_projects: int
    total_tasks: int
    completed_tasks_total: int
    completed_tasks_30d: int
    overdue_tasks: int
    on_time_delivery_rate: float
    active_risks_count: int
    critical_risks_count: int
    portfolio_health_average: float
    workload_saturation_rate: float

# Analytics Reports
class AnalyticsReportCreate(BaseModel):
    title: str = Field(..., max_length=255)
    report_type: str = Field(..., pattern="^(PORTFOLIO_HEALTH|EXECUTIVE_KPI|TEAM_WORKLOAD|RISK_ASSESSMENT)$")
    parameters: Optional[Dict[str, Any]] = None
    format: str = Field("JSON", pattern="^(JSON|CSV)$")

class AnalyticsReportResponse(BaseModel):
    id: str
    user_id: int
    workspace_id: int
    title: str
    report_type: str
    parameters_json: str
    summary_json: str
    format: str
    created_at: datetime

    class Config:
        from_attributes = True
