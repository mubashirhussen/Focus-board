from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Datasets ---
class AnalyticsDatasetBase(BaseModel):
    name: str
    slug: str
    category: str = "PRODUCTIVITY"
    description: str
    data_source: str
    freshness_status: str = "FRESH"
    record_count: int = 0
    schema_json: str = "[]"

    model_config = ConfigDict(protected_namespaces=())

class AnalyticsDatasetCreate(AnalyticsDatasetBase):
    pass

class AnalyticsDatasetResponse(AnalyticsDatasetBase):
    id: str
    last_refreshed_at: datetime
    created_at: datetime
    schema_fields: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)

# --- Metric Definitions ---
class AnalyticsMetricDefinitionBase(BaseModel):
    identifier: str
    name: str
    category: str
    description: str
    calculation_method: str
    unit: str = "count"
    aggregation_method: str = "SUM"
    is_active: bool = True

class AnalyticsMetricDefinitionCreate(AnalyticsMetricDefinitionBase):
    pass

class AnalyticsMetricDefinitionResponse(AnalyticsMetricDefinitionBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

# --- Data Pipelines ---
class AnalyticsDataPipelineBase(BaseModel):
    name: str
    description: str
    source_dataset_slug: str
    target_model: str
    schedule_cron: str = "0 * * * *"
    status: str = "ACTIVE"

class AnalyticsDataPipelineCreate(AnalyticsDataPipelineBase):
    pass

class AnalyticsDataPipelineResponse(AnalyticsDataPipelineBase):
    id: str
    last_run_at: Optional[datetime] = None
    last_run_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AnalyticsPipelineExecutionResponse(BaseModel):
    id: str
    pipeline_id: str
    status: str
    records_processed: int
    duration_ms: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Dashboards & Widgets ---
class AnalyticsWidgetBase(BaseModel):
    title: str
    widget_type: str = "KPI"  # KPI, LINE, BAR, TABLE, PIE
    metric_identifier: str
    config_json: str = "{}"
    position_order: int = 0

class AnalyticsWidgetCreate(AnalyticsWidgetBase):
    pass

class AnalyticsWidgetResponse(AnalyticsWidgetBase):
    id: str
    dashboard_id: str

    model_config = ConfigDict(from_attributes=True)

class AnalyticsDashboardBase(BaseModel):
    title: str
    description: str
    visibility: str = "WORKSPACE"  # PRIVATE, WORKSPACE, ORGANIZATION
    layout_json: str = "[]"

class AnalyticsDashboardCreate(AnalyticsDashboardBase):
    workspace_id: Optional[int] = None
    widgets: List[AnalyticsWidgetCreate] = []

class AnalyticsDashboardResponse(AnalyticsDashboardBase):
    id: str
    workspace_id: Optional[int] = None
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    widgets: List[AnalyticsWidgetResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- Custom Reports ---
class AnalyticsCustomReportBase(BaseModel):
    title: str
    category: str = "PRODUCTIVITY"
    query_config_json: str = "{}"
    format: str = "CSV"
    schedule_cron: Optional[str] = None

class AnalyticsCustomReportCreate(AnalyticsCustomReportBase):
    workspace_id: Optional[int] = None

class AnalyticsCustomReportResponse(AnalyticsCustomReportBase):
    id: str
    workspace_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    last_run_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Data Quality Rules & Issues ---
class DataQualityRuleBase(BaseModel):
    dataset_slug: str
    rule_name: str
    rule_type: str = "COMPLETENESS"  # COMPLETENESS, VALIDITY, FRESHNESS, CONSISTENCY
    severity: str = "WARNING"
    condition_expr: str

class DataQualityRuleCreate(DataQualityRuleBase):
    pass

class DataQualityRuleResponse(DataQualityRuleBase):
    id: str
    status: str
    last_evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DataQualityIssueResponse(BaseModel):
    id: str
    rule_id: str
    dataset_slug: str
    issue_summary: str
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- AI Natural Language Analytics ---
class AIAnalyticsQueryRequest(BaseModel):
    prompt: str = Field(..., description="e.g. Which tasks were completed this week, and what is our overdue rate?")
    workspace_id: Optional[int] = None

class AIAnalyticsQueryResponse(BaseModel):
    question: str
    direct_answer: str
    synthesized_metrics: Dict[str, Any]
    grounded_evidence: List[str]
    suggested_visualization: str  # KPI, BAR, LINE, TABLE
    chart_data: List[Dict[str, Any]] = []

# --- Data Intelligence Overview ---
class DataIntelligenceOverviewResponse(BaseModel):
    total_datasets_count: int
    fresh_datasets_count: int
    active_pipelines_count: int
    data_quality_score_percent: float
    open_quality_issues_count: int
    top_metrics_summary: Dict[str, Any]
    datasets: List[AnalyticsDatasetResponse] = []
    pipelines: List[AnalyticsDataPipelineResponse] = []
    recent_dashboards: List[AnalyticsDashboardResponse] = []
    quality_rules: List[DataQualityRuleResponse] = []
