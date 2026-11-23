from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.schemas.data_intelligence import (
    DataSourceCreate,
    DataSourceResponse,
    DataSourceTestResponse,
    AnalyticsDatasetResponse,
    AnalyticsDatasetCreate,
    DatasetImportRequest,
    DatasetImportResponse,
    DatasetProfileResponse,
    AnalyticsMetricDefinitionResponse,
    AnalyticsDataPipelineResponse,
    AnalyticsDataPipelineCreate,
    AnalyticsPipelineExecutionResponse,
    AnalyticsDashboardResponse,
    AnalyticsDashboardCreate,
    AnalyticsCustomReportResponse,
    AnalyticsCustomReportCreate,
    ReportExecutionResultResponse,
    ReportExportResponse,
    DataQualityRuleResponse,
    DataLineageGraphResponse,
    DataInsightCreate,
    DataInsightResponse,
    AIAnalyticsQueryRequest,
    AIAnalyticsQueryResponse,
    DataIntelligenceOverviewResponse,
)
from app.services import data_intelligence_service

router = APIRouter(prefix="/data-intelligence", tags=["FocusBoard Data Intelligence & BI Platform"])

def resolve_tenant_org_id(db: Session, current_user: User, explicit_org_id: Optional[int] = None) -> Optional[int]:
    """
    Resolve and enforce organization / workspace tenant boundary for current_user.
    If explicit_org_id is provided, validates that user belongs to that workspace/organization.
    Raises 403 Forbidden if unauthorized.
    """
    if explicit_org_id is not None:
        if getattr(current_user, "role", None) in ["Admin", "Owner", "admin"]:
            return explicit_org_id
        # Check workspace membership
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == explicit_org_id,
            WorkspaceMember.user_id == current_user.id
        ).first()
        if member:
            return explicit_org_id
        # Check workspace ownership
        ws = db.query(Workspace).filter(
            Workspace.id == explicit_org_id,
            Workspace.owner_id == current_user.id
        ).first()
        if ws:
            return explicit_org_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have authorization for this organization or workspace context."
        )

    # Resolve user's primary workspace if present
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).first()
    if member:
        return member.workspace_id
    ws = db.query(Workspace).filter(Workspace.owner_id == current_user.id).first()
    if ws:
        return ws.id
    return None

# --- Overview ---
@router.get("/overview", response_model=DataIntelligenceOverviewResponse)
def get_data_intelligence_overview(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full Data Intelligence overview: datasets, pipelines, quality scores, and summaries."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.get_data_intelligence_overview(db, workspace_id=workspace_id, organization_id=org_id)

# --- Data Sources ---
@router.get("/sources", response_model=List[DataSourceResponse])
def list_data_sources(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List registered data sources and integrations."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.list_data_sources(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/sources", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(
    payload: DataSourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new external or internal data source."""
    org_id = resolve_tenant_org_id(db, current_user, payload.workspace_id or payload.organization_id)
    return data_intelligence_service.create_data_source(db, payload, organization_id=org_id, workspace_id=payload.workspace_id)

@router.post("/sources/{source_id}/test", response_model=DataSourceTestResponse)
def test_data_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate connection and latency to data source."""
    try:
        return data_intelligence_service.test_data_source(db, source_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

# --- Datasets ---
@router.get("/datasets", response_model=List[AnalyticsDatasetResponse])
def list_datasets(
    workspace_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List data catalog datasets with schema fields and freshness."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.list_datasets(db, organization_id=org_id, workspace_id=workspace_id, category=category)

@router.post("/datasets", response_model=AnalyticsDatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: AnalyticsDatasetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new catalog dataset."""
    org_id = resolve_tenant_org_id(db, current_user, payload.workspace_id or payload.organization_id)
    return data_intelligence_service.create_dataset(db, payload, organization_id=org_id, workspace_id=payload.workspace_id)

@router.post("/datasets/import", response_model=DatasetImportResponse, status_code=status.HTTP_201_CREATED)
def import_dataset(
    payload: DatasetImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ingest CSV or JSON records into catalog datasets."""
    org_id = resolve_tenant_org_id(db, current_user, payload.workspace_id)
    try:
        return data_intelligence_service.import_dataset_records(db, payload, organization_id=org_id, workspace_id=payload.workspace_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.get("/datasets/{slug}/profile", response_model=DatasetProfileResponse)
def get_dataset_profile(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate statistical profile for a dataset."""
    try:
        return data_intelligence_service.profile_dataset(db, slug)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

# --- Pipelines ---
@router.get("/pipelines", response_model=List[AnalyticsDataPipelineResponse])
def list_pipelines(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List data pipelines."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.list_pipelines(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/pipelines", response_model=AnalyticsDataPipelineResponse, status_code=status.HTTP_201_CREATED)
def create_pipeline(
    payload: AnalyticsDataPipelineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new data aggregation pipeline with node configuration."""
    org_id = resolve_tenant_org_id(db, current_user, payload.workspace_id or payload.organization_id)
    return data_intelligence_service.create_pipeline(db, payload, organization_id=org_id, workspace_id=payload.workspace_id)

@router.post("/pipelines/{pipeline_id}/run", response_model=AnalyticsPipelineExecutionResponse)
def run_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger execution of an analytical aggregation pipeline."""
    try:
        return data_intelligence_service.run_pipeline(db, pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# --- Dashboards ---
@router.get("/dashboards", response_model=List[AnalyticsDashboardResponse])
def list_dashboards(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List analytical dashboards."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.list_dashboards(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/dashboards", response_model=AnalyticsDashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    payload: AnalyticsDashboardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new analytical dashboard with configured widgets."""
    org_id = resolve_tenant_org_id(db, current_user, payload.workspace_id or payload.organization_id)
    return data_intelligence_service.create_dashboard(db, payload, owner_id=current_user.id, organization_id=org_id)

@router.get("/dashboards/{dashboard_id}", response_model=AnalyticsDashboardResponse)
def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single dashboard with widgets."""
    dash = data_intelligence_service.get_dashboard(db, dashboard_id)
    if not dash:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return dash

@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete analytical dashboard."""
    success = data_intelligence_service.delete_dashboard(db, dashboard_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    return None

# --- Reports ---
@router.get("/reports", response_model=List[AnalyticsCustomReportResponse])
def list_reports(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List custom analytical reports."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.list_reports(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/reports", response_model=AnalyticsCustomReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: AnalyticsCustomReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom report."""
    org_id = resolve_tenant_org_id(db, current_user, payload.workspace_id or payload.organization_id)
    return data_intelligence_service.create_custom_report(db, payload, user_id=current_user.id, organization_id=org_id)

@router.post("/reports/{report_id}/run", response_model=ReportExecutionResultResponse)
def execute_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run an analytical report query and return summarized results."""
    try:
        return data_intelligence_service.run_custom_report(db, report_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/reports/{report_id}/export", response_model=ReportExportResponse)
def export_report(
    report_id: str,
    format: str = Query("CSV"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export custom report as CSV or JSON."""
    try:
        return data_intelligence_service.export_custom_report(db, report_id, export_format=format)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# --- Data Quality ---
@router.get("/quality/rules", response_model=List[DataQualityRuleResponse])
def list_quality_rules(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run live quality audit and return rule evaluation results."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.run_data_quality_audit(db, organization_id=org_id, workspace_id=workspace_id)

# --- Lineage ---
@router.get("/lineage", response_model=DataLineageGraphResponse)
def get_data_lineage(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve end-to-end data lineage graph from sources to dashboards."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.get_data_lineage_graph(db, organization_id=org_id, workspace_id=workspace_id)

# --- Insights ---
@router.get("/insights", response_model=List[DataInsightResponse])
def list_data_insights(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List automated evidence-based data insights and anomalies."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return data_intelligence_service.list_data_insights(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/insights", response_model=DataInsightResponse, status_code=status.HTTP_201_CREATED)
def create_data_insight(
    payload: DataInsightCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new data insight or anomaly alert."""
    org_id = resolve_tenant_org_id(db, current_user, payload.workspace_id or payload.organization_id)
    return data_intelligence_service.create_data_insight(db, payload, organization_id=org_id, workspace_id=payload.workspace_id)

# --- AI Data Intelligence Assistant ---
@router.post("/assistant/query", response_model=AIAnalyticsQueryResponse)
def query_ai_assistant(
    payload: AIAnalyticsQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask natural language analytical questions grounded in real live data."""
    _ = resolve_tenant_org_id(db, current_user, payload.workspace_id)
    return data_intelligence_service.query_ai_data_assistant(db, payload)
