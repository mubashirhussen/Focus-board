from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Service Registry ---
class ServiceRegistryItemBase(BaseModel):
    name: str
    category: str = "CORE"
    health_endpoint: Optional[str] = None
    status: str = "OPERATIONAL"
    dependencies_json: str = "[]"
    failure_details: Optional[str] = None

class ServiceRegistryItemCreate(ServiceRegistryItemBase):
    id: str

class ServiceRegistryItemResponse(ServiceRegistryItemBase):
    id: str
    response_time_ms: float = 0.0
    last_checked_at: datetime
    dependencies_list: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Alert Rules & Alerts ---
class PlatformAlertRuleBase(BaseModel):
    name: str
    metric_name: str
    condition_operator: str = "GREATER_THAN"
    threshold_value: float
    severity: str = "WARNING"
    evaluation_interval_seconds: int = 60
    is_active: bool = True

class PlatformAlertRuleCreate(PlatformAlertRuleBase):
    pass

class PlatformAlertRuleResponse(PlatformAlertRuleBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PlatformAlertBase(BaseModel):
    rule_id: Optional[str] = None
    severity: str = "WARNING"
    status: str = "ACTIVE"
    summary: str
    details: Optional[str] = None
    related_service_id: Optional[str] = None

class PlatformAlertCreate(PlatformAlertBase):
    pass

class PlatformAlertResponse(PlatformAlertBase):
    id: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Incident Management ---
class IncidentTimelineEntryResponse(BaseModel):
    id: str
    incident_id: str
    entry_type: str
    message: str
    actor_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentActionItemCreate(BaseModel):
    action_description: str
    assignee_id: Optional[int] = None

class IncidentActionItemResponse(BaseModel):
    id: str
    incident_id: str
    action_description: str
    assignee_id: Optional[int] = None
    is_completed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentPostMortemCreate(BaseModel):
    impact_summary: str
    root_cause_analysis: str
    lessons_learned: str
    preventative_measures: str

class IncidentPostMortemResponse(IncidentPostMortemCreate):
    id: str
    incident_id: str
    published_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PlatformIncidentBase(BaseModel):
    title: str
    description: str
    severity: str = "SEV3"
    status: str = "DETECTED"
    affected_services_json: str = "[]"
    root_cause: Optional[str] = None
    mitigation_summary: Optional[str] = None
    resolution_summary: Optional[str] = None

class PlatformIncidentCreate(PlatformIncidentBase):
    lead_operator_id: Optional[int] = None

class PlatformIncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    affected_services_json: Optional[str] = None
    lead_operator_id: Optional[int] = None
    root_cause: Optional[str] = None
    mitigation_summary: Optional[str] = None
    resolution_summary: Optional[str] = None

class PlatformIncidentResponse(PlatformIncidentBase):
    id: str
    lead_operator_id: Optional[int] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    affected_services_list: List[str] = []
    timeline_entries: List[IncidentTimelineEntryResponse] = []
    action_items: List[IncidentActionItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- SLOs ---
class SLODefinitionBase(BaseModel):
    service_id: str
    name: str
    target_percentage: float = 99.9
    measurement_window_days: int = 30
    current_sli_percentage: float = 99.95
    error_budget_remaining_percent: float = 95.0
    burn_rate: float = 1.0

class SLODefinitionCreate(SLODefinitionBase):
    pass

class SLODefinitionResponse(SLODefinitionBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Maintenance Windows ---
class PlatformMaintenanceWindowBase(BaseModel):
    title: str
    description: str
    status: str = "SCHEDULED"
    scheduled_start: datetime
    scheduled_end: datetime
    affected_services_json: str = "[]"

class PlatformMaintenanceWindowCreate(PlatformMaintenanceWindowBase):
    pass

class PlatformMaintenanceWindowResponse(PlatformMaintenanceWindowBase):
    id: str
    created_by_id: Optional[int] = None
    created_at: datetime
    affected_services_list: List[str] = []

    model_config = ConfigDict(from_attributes=True)

# --- Support Diagnostics & Overview ---
class SupportDiagnosticRequest(BaseModel):
    workspace_id: int
    check_type: str = "FULL"  # FULL, INTEGRATIONS, WEBHOOKS, PERMISSIONS, STORAGE

class SupportDiagnosticResponse(BaseModel):
    workspace_id: int
    health_status: str
    checks_performed: List[Dict[str, Any]]
    active_integrations_count: int
    recent_errors_count: int
    recommendations: List[str]
    timestamp: datetime

class PlatformOperationsOverviewResponse(BaseModel):
    overall_health: str  # OPERATIONAL, DEGRADED, CRITICAL, MAINTENANCE
    system_uptime_percentage: float
    average_api_latency_ms: float
    error_rate_percentage: float
    total_services_count: int
    degraded_services_count: int
    active_alerts_count: int
    active_incidents_count: int
    services: List[ServiceRegistryItemResponse] = []
    recent_alerts: List[PlatformAlertResponse] = []
    active_incidents: List[PlatformIncidentResponse] = []
    slo_metrics: List[SLODefinitionResponse] = []
