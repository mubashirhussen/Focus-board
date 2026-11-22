from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DistributionItem(BaseModel):
    name: str
    count: int
    percentage: float

class AnalyticsDistribution(BaseModel):
    by_status: List[DistributionItem] = []
    by_priority: List[DistributionItem] = []
    by_category: List[DistributionItem] = []
    by_assignee: List[DistributionItem] = []

class TrendItem(BaseModel):
    date: str
    completed: int = 0
    created: int = 0
    in_progress: int = 0
    completion_rate: float = 0.0

class TrendComparisonResponse(BaseModel):
    current_period: List[TrendItem] = []
    previous_period: List[TrendItem] = []
    percentage_change: float = 0.0
    trend_direction: str = "neutral"  # up, down, neutral

class AnalyticsSummary(BaseModel):
    total: int = 0
    completed: int = 0
    in_progress: int = 0
    todo: int = 0
    overdue: int = 0
    due_today: int = 0
    due_this_week: int = 0
    completion_rate: int = 0
    on_time_completion_rate: int = 0
    high_priority_pending: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    total_teams: int = 0
    total_workspaces: int = 0

class ProductivityInsight(BaseModel):
    type: str  # info, success, warning
    title: str
    message: str

class AnalyticsInsightsResponse(BaseModel):
    insights: List[ProductivityInsight] = []
    most_active_category: Optional[str] = None
    fastest_completion_day: Optional[str] = None
    velocity_score: float = 0.0

class PersonalProductivityResponse(BaseModel):
    total_assigned: int = 0
    total_created: int = 0
    total_completed: int = 0
    in_progress: int = 0
    pending: int = 0
    overdue: int = 0
    completed_on_time: int = 0
    completed_late: int = 0
    completion_rate: float = 0.0
    on_time_rate: float = 0.0
    personal_workload: int = 0
    priority_distribution: List[DistributionItem] = []
    status_distribution: List[DistributionItem] = []

class ProjectAnalyticsItem(BaseModel):
    id: int
    name: str
    status: str
    priority: str
    health: str  # healthy, at_risk, critical
    total_tasks: int = 0
    completed_tasks: int = 0
    open_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0
    progress_percent: float = 0.0

class ProjectAnalyticsResponse(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    health_breakdown: Dict[str, int] = {"healthy": 0, "at_risk": 0, "critical": 0}
    projects: List[ProjectAnalyticsItem] = []

class TeamMemberWorkload(BaseModel):
    user_id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    assigned_tasks: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0

class TeamAnalyticsResponse(BaseModel):
    team_id: int
    team_name: str
    total_members: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    open_tasks: int = 0
    completion_rate: float = 0.0
    member_workload: List[TeamMemberWorkload] = []

class WorkspaceAnalyticsResponse(BaseModel):
    workspace_id: int
    workspace_name: str
    total_projects: int = 0
    active_projects: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0
    project_distribution: List[DistributionItem] = []

class OrganizationAnalyticsResponse(BaseModel):
    organization_id: int
    organization_name: str
    total_workspaces: int = 0
    total_projects: int = 0
    total_teams: int = 0
    total_members: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    global_completion_rate: float = 0.0
    health_breakdown: Dict[str, int] = {}

class DeadlineAnalyticsResponse(BaseModel):
    due_today: int = 0
    due_this_week: int = 0
    upcoming: int = 0
    overdue: int = 0
    no_deadline: int = 0
    completed_on_time: int = 0
    completed_late: int = 0
    deadline_risk_score: float = 0.0

class ActivityAnalyticsResponse(BaseModel):
    total_activities: int = 0
    activities_by_type: Dict[str, int] = {}
    activities_by_day: List[Dict[str, Any]] = []

class KPISummaryResponse(BaseModel):
    completion_rate: float = 0.0
    on_time_rate: float = 0.0
    overdue_rate: float = 0.0
    project_health_ratio: float = 0.0
    active_workload_count: int = 0
    velocity_per_week: float = 0.0
