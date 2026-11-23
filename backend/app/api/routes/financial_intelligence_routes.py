from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.schemas.financial_intelligence import (
    FinancialTransactionCreate,
    FinancialTransactionResponse,
    CostRecordCreate,
    CostRecordResponse,
    FinancialBudgetCreate,
    FinancialBudgetUpdate,
    FinancialBudgetResponse,
    FinancialForecastCreate,
    FinancialForecastResponse,
    FinancialOverviewResponse,
    FinancialReportExportRequest,
    FinancialReportExportResponse,
    FinancialDataSourceCreate,
    FinancialDataSourceResponse,
    FinancialDataSourceTestResponse,
    FinancialDataSourceSyncResponse,
    FinancialImportPreviewRequest,
    FinancialImportPreviewResponse,
    FinancialImportCommitRequest,
    FinancialImportResponse,
    FinancialInsightResponse,
    FinancialInsightUpdate,
    FinancialRecommendationResponse,
    FinancialRecommendationActionRequest,
    FinancialScenarioCreate,
    FinancialScenarioResponse,
    FinancialScenarioCompareResponse,
    FinancialAIAnalyzeRequest,
    FinancialAIAnalyzeResponse,
)
from app.services.financial_intelligence_service import FinancialIntelligenceService

router = APIRouter(prefix="/finance", tags=["SaaS Financial Intelligence & FinOps"])

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
            detail="Access denied: You do not have authorization for this organization context."
        )

    # Resolve user's primary workspace if present
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).first()
    if member:
        return member.workspace_id
    ws = db.query(Workspace).filter(Workspace.owner_id == current_user.id).first()
    if ws:
        return ws.id
    return None

# --- Financial Overview ---
@router.get("/overview", response_model=FinancialOverviewResponse)
def get_financial_overview(
    tenant_id: str = Query("default"),
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive financial intelligence overview: MRR, ARR, Retention (GRR/NRR), Unit Economics, and FinOps."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    return FinancialIntelligenceService.get_overview(db, tenant_id=tenant_id, organization_id=org_id, workspace_id=workspace_id)

# --- Transactions ---
@router.get("/transactions", response_model=List[FinancialTransactionResponse])
def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial billing transactions (charges, refunds, adjustments)."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    txs = FinancialIntelligenceService.list_transactions(db, organization_id=org_id, workspace_id=workspace_id, limit=limit)
    res = []
    for t in txs:
        resp = FinancialTransactionResponse.model_validate(t)
        resp.amount = round(t.amount_cents / 100.0, 2)
        res.append(resp)
    return res

@router.post("/transactions", response_model=FinancialTransactionResponse, status_code=status.HTTP_201_CREATED)
def record_transaction(
    tx_in: FinancialTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a financial ledger transaction."""
    org_id = resolve_tenant_org_id(db, current_user, tx_in.organization_id or tx_in.workspace_id)
    tx = FinancialIntelligenceService.record_transaction(db, tx_in=tx_in, user_id=current_user.id, organization_id=org_id)
    resp = FinancialTransactionResponse.model_validate(tx)
    resp.amount = round(tx.amount_cents / 100.0, 2)
    return resp

# --- FinOps & Cost Records ---
@router.get("/costs", response_model=List[CostRecordResponse])
def list_cost_records(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List infrastructure, cloud, and AI inference cost records."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    costs = FinancialIntelligenceService.list_costs(db, organization_id=org_id, workspace_id=workspace_id)
    res = []
    for c in costs:
        resp = CostRecordResponse.model_validate(c)
        resp.amount = round(c.amount_cents / 100.0, 2)
        res.append(resp)
    return res

@router.post("/costs", response_model=CostRecordResponse, status_code=status.HTTP_201_CREATED)
def record_cost(
    cost_in: CostRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ingest a direct infrastructure or AI inference cost entry."""
    org_id = resolve_tenant_org_id(db, current_user, cost_in.organization_id or cost_in.workspace_id)
    cost = FinancialIntelligenceService.record_cost(db, cost_in=cost_in, user_id=current_user.id, organization_id=org_id)
    resp = CostRecordResponse.model_validate(cost)
    resp.amount = round(cost.amount_cents / 100.0, 2)
    return resp

# --- Budgets ---
@router.get("/budgets", response_model=List[FinancialBudgetResponse])
def list_budgets(
    tenant_id: str = Query("default"),
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial budgets with actual spending and alert threshold indicators."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    overview = FinancialIntelligenceService.get_overview(db, tenant_id=tenant_id, organization_id=org_id, workspace_id=workspace_id)
    return overview.active_budgets

@router.post("/budgets", response_model=FinancialBudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: FinancialBudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a spending budget cap with threshold notification percentage."""
    org_id = resolve_tenant_org_id(db, current_user, budget_in.organization_id or budget_in.workspace_id)
    budget = FinancialIntelligenceService.create_budget(db, budget_in=budget_in, user_id=current_user.id, organization_id=org_id)
    resp = FinancialBudgetResponse.model_validate(budget)
    resp.budget_amount = round(budget.budget_amount_cents / 100.0, 2)
    resp.actual_spent = 0.0
    resp.actual_spent_cents = 0
    resp.spent_percentage = 0.0
    resp.is_alert_triggered = False
    return resp

@router.put("/budgets/{budget_id}", response_model=FinancialBudgetResponse)
def update_budget(
    budget_id: str,
    update_data: FinancialBudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update financial budget limit or alert threshold."""
    org_id = resolve_tenant_org_id(db, current_user)
    budget = FinancialIntelligenceService.update_budget(db, budget_id=budget_id, update_data=update_data, organization_id=org_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    resp = FinancialBudgetResponse.model_validate(budget)
    resp.budget_amount = round(budget.budget_amount_cents / 100.0, 2)
    return resp

# --- Forecasts ---
@router.get("/forecasts", response_model=List[FinancialForecastResponse])
def list_forecasts(
    tenant_id: str = Query("default"),
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial multi-scenario forward projections (Baseline, Growth, Conservative)."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    overview = FinancialIntelligenceService.get_overview(db, tenant_id=tenant_id, organization_id=org_id, workspace_id=workspace_id)
    return overview.projected_forecasts

@router.post("/forecasts", response_model=FinancialForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(
    forecast_in: FinancialForecastCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a strategic financial forecast scenario."""
    org_id = resolve_tenant_org_id(db, current_user, forecast_in.organization_id or forecast_in.workspace_id)
    fc = FinancialIntelligenceService.create_forecast(db, forecast_in=forecast_in, organization_id=org_id)
    resp = FinancialForecastResponse.model_validate(fc)
    resp.projected_mrr = round(fc.projected_mrr_cents / 100.0, 2)
    resp.projected_arr = round(fc.projected_arr_cents / 100.0, 2)
    return resp

# --- Reports Export ---
@router.post("/reports/export", response_model=FinancialReportExportResponse)
def export_financial_report(
    req: FinancialReportExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and export executive summary, transactions ledger, or FinOps CSV reports."""
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    return FinancialIntelligenceService.export_report(db, req=req, organization_id=org_id, workspace_id=req.workspace_id)

# --- Financial Data Sources Management ---
@router.get("/data-sources", response_model=List[FinancialDataSourceResponse])
def list_data_sources(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List configured financial data sources (Stripe, AWS CUR, QuickBooks, CSV)."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    sources = FinancialIntelligenceService.list_data_sources(db, organization_id=org_id, workspace_id=workspace_id)
    return [FinancialDataSourceResponse.model_validate(s) for s in sources]

@router.post("/data-sources", response_model=FinancialDataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(
    ds_in: FinancialDataSourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register and connect an external financial data source."""
    org_id = resolve_tenant_org_id(db, current_user, ds_in.organization_id or ds_in.workspace_id)
    ds = FinancialIntelligenceService.create_data_source(db, ds_in=ds_in, user_id=current_user.id, organization_id=org_id)
    return FinancialDataSourceResponse.model_validate(ds)

@router.post("/data-sources/{data_source_id}/test-connection", response_model=FinancialDataSourceTestResponse)
def test_data_source_connection(
    data_source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify live connectivity and API credential authorization for data source."""
    org_id = resolve_tenant_org_id(db, current_user)
    return FinancialIntelligenceService.test_data_source_connection(db, data_source_id=data_source_id, organization_id=org_id)

@router.post("/data-sources/{data_source_id}/sync", response_model=FinancialDataSourceSyncResponse)
def sync_data_source(
    data_source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger on-demand telemetry ingestion synchronization for data source."""
    org_id = resolve_tenant_org_id(db, current_user)
    return FinancialIntelligenceService.sync_data_source(db, data_source_id=data_source_id, user_id=current_user.id, organization_id=org_id)

@router.delete("/data-sources/{data_source_id}")
def delete_data_source(
    data_source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect and remove a financial data source."""
    org_id = resolve_tenant_org_id(db, current_user)
    success = FinancialIntelligenceService.delete_data_source(db, data_source_id=data_source_id, organization_id=org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data source not found.")
    return {"status": "SUCCESS", "message": f"Data source {data_source_id} removed."}

# --- CSV Import & Ingestion ---
@router.post("/imports/preview", response_model=FinancialImportPreviewResponse)
def preview_financial_import(
    req: FinancialImportPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate and preview CSV financial data rows before committing."""
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    return FinancialIntelligenceService.preview_import(db, req=req, organization_id=org_id, workspace_id=req.workspace_id)

@router.post("/imports/commit", response_model=FinancialImportResponse, status_code=status.HTTP_201_CREATED)
def commit_financial_import(
    req: FinancialImportCommitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Commit verified CSV transactions or costs into ledger."""
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    return FinancialIntelligenceService.commit_import(db, req=req, user_id=current_user.id, organization_id=org_id, workspace_id=req.workspace_id)

@router.get("/imports", response_model=List[FinancialImportResponse])
def list_financial_imports(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial import histories."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    imports = FinancialIntelligenceService.list_imports(db, organization_id=org_id, workspace_id=workspace_id)
    res = []
    for imp in imports:
        r = FinancialImportResponse.model_validate(imp)
        r.total_amount = round(imp.total_amount_cents / 100.0, 2)
        res.append(r)
    return res

# --- Financial Insights & Anomalies ---
@router.get("/insights", response_model=List[FinancialInsightResponse])
def list_financial_insights(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List detected financial anomalies and performance insights."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    insights = FinancialIntelligenceService.list_insights(db, organization_id=org_id, workspace_id=workspace_id)
    return [FinancialInsightResponse.model_validate(i) for i in insights]

@router.post("/insights/generate", response_model=List[FinancialInsightResponse])
def generate_financial_insights(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run real-time anomaly detection across budget caps, churn, and margins."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    insights = FinancialIntelligenceService.generate_insights(db, organization_id=org_id, workspace_id=workspace_id)
    return [FinancialInsightResponse.model_validate(i) for i in insights]

@router.patch("/insights/{insight_id}", response_model=FinancialInsightResponse)
def update_financial_insight(
    insight_id: str,
    update_in: FinancialInsightUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update insight status (OPEN, RESOLVED, DISMISSED)."""
    org_id = resolve_tenant_org_id(db, current_user)
    ins = FinancialIntelligenceService.update_insight_status(db, insight_id=insight_id, status=update_in.status, organization_id=org_id)
    if not ins:
        raise HTTPException(status_code=404, detail="Financial insight not found.")
    return FinancialInsightResponse.model_validate(ins)

# --- Financial Recommendations ---
@router.get("/recommendations", response_model=List[FinancialRecommendationResponse])
def list_financial_recommendations(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List high-impact cost optimization and revenue expansion recommendations."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    recs = FinancialIntelligenceService.list_recommendations(db, organization_id=org_id, workspace_id=workspace_id)
    res = []
    for r in recs:
        resp = FinancialRecommendationResponse.model_validate(r)
        resp.potential_savings = round(r.potential_savings_cents / 100.0, 2)
        res.append(resp)
    return res

@router.post("/recommendations/{recommendation_id}/action", response_model=FinancialRecommendationResponse)
def act_on_financial_recommendation(
    recommendation_id: str,
    act_in: FinancialRecommendationActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept or reject financial recommendation."""
    org_id = resolve_tenant_org_id(db, current_user)
    rec = FinancialIntelligenceService.act_on_recommendation(db, recommendation_id=recommendation_id, action=act_in.action, organization_id=org_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    resp = FinancialRecommendationResponse.model_validate(rec)
    resp.potential_savings = round(rec.potential_savings_cents / 100.0, 2)
    return resp

# --- Financial Scenarios ---
@router.get("/scenarios", response_model=List[FinancialScenarioResponse])
def list_financial_scenarios(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial forward scenarios (Base, Best, Worst, Custom)."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    scens = FinancialIntelligenceService.list_scenarios(db, organization_id=org_id, workspace_id=workspace_id)
    res = []
    for s in scens:
        sr = FinancialScenarioResponse.model_validate(s)
        sr.projected_mrr = round(s.projected_mrr_cents / 100.0, 2)
        sr.projected_arr = round(s.projected_arr_cents / 100.0, 2)
        res.append(sr)
    return res

@router.post("/scenarios", response_model=FinancialScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_financial_scenario(
    scen_in: FinancialScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new strategic financial scenario with projected growth rate and cost multipliers."""
    org_id = resolve_tenant_org_id(db, current_user, scen_in.workspace_id)
    scen = FinancialIntelligenceService.create_scenario(db, scen_in=scen_in, organization_id=org_id)
    sr = FinancialScenarioResponse.model_validate(scen)
    sr.projected_mrr = round(scen.projected_mrr_cents / 100.0, 2)
    sr.projected_arr = round(scen.projected_arr_cents / 100.0, 2)
    return sr

@router.get("/scenarios/compare", response_model=FinancialScenarioCompareResponse)
def compare_financial_scenarios(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare all strategic scenarios against current baseline run rate."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or workspace_id)
    return FinancialIntelligenceService.compare_scenarios(db, organization_id=org_id, workspace_id=workspace_id)

# --- AI Financial Assistant ---
@router.post("/ai/analyze", response_model=FinancialAIAnalyzeResponse)
def ai_financial_analysis(
    req: FinancialAIAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate grounded financial analysis using real telemetry records and unit economics."""
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    return FinancialIntelligenceService.ai_analyze(db, req=req, organization_id=org_id, workspace_id=req.workspace_id)
