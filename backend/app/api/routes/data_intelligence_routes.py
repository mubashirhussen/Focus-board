from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.data_intelligence import (
    AnalyticsDatasetResponse,
    AnalyticsMetricDefinitionResponse,
    AnalyticsDataPipelineResponse,
    AnalyticsPipelineExecutionResponse,
    AnalyticsDashboardResponse,
    AnalyticsDashboardCreate,
    AnalyticsCustomReportResponse,
    AnalyticsCustomReportCreate,
    DataQualityRuleResponse,
    AIAnalyticsQueryRequest,
    AIAnalyticsQueryResponse,
    DataIntelligenceOverviewResponse,
)
from app.services import data_intelligence_service

router = APIRouter(prefix="/data-intelligence", tags=["FocusBoard Data Intelligence & BI Platform"])

# --- Overview ---
@router.get("/overview", response_model=DataIntelligenceOverviewResponse)
def get_data_intelligence_overview(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full Data Intelligence overview: datasets, pipelines, quality scores, and summaries."""
    return data_intelligence_service.get_data_intelligence_overview(db, workspace_id=workspace_id)

# --- Datasets ---
@router.get("/datasets", response_model=List[AnalyticsDatasetResponse])
def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List data catalog datasets with schema fields and freshness."""
    overview = data_intelligence_service.get_data_intelligence_overview(db)
    return overview["datasets"]

# --- Pipelines ---
@router.get("/pipelines", response_model=List[AnalyticsDataPipelineResponse])
def list_pipelines(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List data pipelines."""
    data_intelligence_service.seed_default_data_sources_and_metrics(db)
    from app.models.data_intelligence import AnalyticsDataPipeline
    return db.query(AnalyticsDataPipeline).all()

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
    return data_intelligence_service.list_dashboards(db, workspace_id=workspace_id)

@router.post("/dashboards", response_model=AnalyticsDashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    payload: AnalyticsDashboardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new analytical dashboard with configured widgets."""
    return data_intelligence_service.create_dashboard(db, payload, owner_id=current_user.id)

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
    return data_intelligence_service.list_reports(db, workspace_id=workspace_id)

@router.post("/reports", response_model=AnalyticsCustomReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: AnalyticsCustomReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom report."""
    return data_intelligence_service.create_custom_report(db, payload, user_id=current_user.id)

@router.post("/reports/{report_id}/run")
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

# --- Data Quality ---
@router.get("/quality/rules", response_model=List[DataQualityRuleResponse])
def list_quality_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run live quality audit and return rule evaluation results."""
    return data_intelligence_service.run_data_quality_audit(db)

# --- AI Data Intelligence Assistant ---
@router.post("/assistant/query", response_model=AIAnalyticsQueryResponse)
def query_ai_assistant(
    payload: AIAnalyticsQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask natural language analytical questions grounded in real live data."""
    return data_intelligence_service.query_ai_data_assistant(db, payload)
