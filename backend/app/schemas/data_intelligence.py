from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Data Sources ---
class DataSourceBase(BaseModel):
    name: str
    source_type: str = Field(default="INTERNAL_DB", description="INTERNAL_DB, POSTGRESQL, SNOWFLAKE, BIGQUERY, API, CSV_UPLOAD")
    connection_status: str = Field(default="CONNECTED", description="CONNECTED, DISCONNECTED, ERROR, TESTING")
    config_json: str = "{}"
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    connection_status: Optional[str] = None
    config_json: Optional[str] = None
    workspace_id: Optional[int] = None

class DataSourceResponse(DataSourceBase):
    id: str
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DataSourceTestResponse(BaseModel):
    data_source_id: str
    connection_status: str
    latency_ms: float
    message: str

# --- Datasets ---
class AnalyticsDatasetBase(BaseModel):
    name: str
    slug: str
    category: str = "PRODUCTIVITY"
    description: str
    data_source: str
    source_type: str = "DATABASE"
    classification: str = "INTERNAL"  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    freshness_status: str = "FRESH"
    record_count: int = 0
    schema_json: str = "[]"
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

    model_config = ConfigDict(protected_namespaces=())

class AnalyticsDatasetCreate(AnalyticsDatasetBase):
    pass

class AnalyticsDatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    classification: Optional[str] = None
    freshness_status: Optional[str] = None
    schema_json: Optional[str] = None

class AnalyticsDatasetResponse(AnalyticsDatasetBase):
    id: str
    last_refreshed_at: datetime
    created_at: datetime
    schema_fields: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)

# Dataset Import & Profiling
class DatasetImportRequest(BaseModel):
    dataset_name: str
    dataset_slug: str
    category: str = "OPERATIONS"
    format: str = "CSV"  # CSV, JSON
    raw_content: str
    workspace_id: Optional[int] = None

class DatasetImportResponse(BaseModel):
    dataset_id: str
    slug: str
    imported_rows: int
    detected_columns: List[str]
    status: str
    message: str

class DatasetProfileResponse(BaseModel):
    dataset_slug: str
    total_records: int
    column_count: int
    columns_profile: Dict[str, Any]
    generated_at: datetime

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
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

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
    pipeline_config_json: str = "{}"
    schedule_cron: str = "0 * * * *"
    status: str = "ACTIVE"
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class AnalyticsDataPipelineCreate(AnalyticsDataPipelineBase):
    pass

class AnalyticsDataPipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pipeline_config_json: Optional[str] = None
    schedule_cron: Optional[str] = None
    status: Optional[str] = None

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
    logs_json: str = "[]"
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
    organization_id: Optional[int] = None

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
    organization_id: Optional[int] = None

class AnalyticsCustomReportCreate(AnalyticsCustomReportBase):
    workspace_id: Optional[int] = None

class AnalyticsCustomReportResponse(AnalyticsCustomReportBase):
    id: str
    workspace_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    last_run_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReportExecutionResultResponse(BaseModel):
    report_id: str
    title: str
    category: str
    format: str
    total_records: int
    data_summary: Dict[str, Any]
    generated_at: str

class ReportExportResponse(BaseModel):
    report_id: str
    title: str
    format: str
    file_name: str
    content_type: str
    raw_content: str
    exported_at: datetime

# --- Data Quality Rules & Issues ---
class DataQualityRuleBase(BaseModel):
    dataset_slug: str
    rule_name: str
    rule_type: str = "COMPLETENESS"  # COMPLETENESS, VALIDITY, FRESHNESS, CONSISTENCY, UNIQUENESS
    severity: str = "WARNING"
    condition_expr: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

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

# --- Lineage & Insights ---
class DataLineageNodeResponse(BaseModel):
    id: str
    source_asset_id: str
    target_asset_id: str
    lineage_type: str
    transformation_details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DataLineageGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    total_assets: int

class DataInsightBase(BaseModel):
    title: str
    description: str
    insight_type: str = "TREND"
    severity: str = "INFO"
    confidence_score: float = 0.9
    supporting_data_json: str = "{}"
    status: str = "ACTIVE"
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class DataInsightCreate(DataInsightBase):
    pass

class DataInsightResponse(DataInsightBase):
    id: str
    created_at: datetime

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
    recent_insights: List[DataInsightResponse] = []
