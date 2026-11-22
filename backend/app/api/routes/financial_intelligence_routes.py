from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
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
)
from app.services.financial_intelligence_service import FinancialIntelligenceService

router = APIRouter(prefix="/finance", tags=["SaaS Financial Intelligence & FinOps"])

@router.get("/overview", response_model=FinancialOverviewResponse)
def get_financial_overview(
    tenant_id: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive financial intelligence overview: MRR, ARR, Retention (GRR/NRR), Unit Economics, and FinOps."""
    return FinancialIntelligenceService.get_overview(db, tenant_id=tenant_id)

# --- Transactions ---
@router.get("/transactions", response_model=List[FinancialTransactionResponse])
def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial billing transactions (charges, refunds, adjustments)."""
    txs = FinancialIntelligenceService.list_transactions(db, limit=limit)
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
    tx = FinancialIntelligenceService.record_transaction(db, tx_in=tx_in)
    resp = FinancialTransactionResponse.model_validate(tx)
    resp.amount = round(tx.amount_cents / 100.0, 2)
    return resp

# --- FinOps & Cost Records ---
@router.get("/costs", response_model=List[CostRecordResponse])
def list_cost_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List infrastructure, cloud, and AI inference cost records."""
    costs = FinancialIntelligenceService.list_costs(db)
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
    cost = FinancialIntelligenceService.record_cost(db, cost_in=cost_in)
    resp = CostRecordResponse.model_validate(cost)
    resp.amount = round(cost.amount_cents / 100.0, 2)
    return resp

# --- Budgets ---
@router.get("/budgets", response_model=List[FinancialBudgetResponse])
def list_budgets(
    tenant_id: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial budgets with actual spending and alert threshold indicators."""
    overview = FinancialIntelligenceService.get_overview(db, tenant_id=tenant_id)
    return overview.active_budgets

@router.post("/budgets", response_model=FinancialBudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: FinancialBudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a spending budget cap with threshold notification percentage."""
    budget = FinancialIntelligenceService.create_budget(db, budget_in=budget_in)
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
    budget = FinancialIntelligenceService.update_budget(db, budget_id=budget_id, update_data=update_data)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    resp = FinancialBudgetResponse.model_validate(budget)
    resp.budget_amount = round(budget.budget_amount_cents / 100.0, 2)
    return resp

# --- Forecasts ---
@router.get("/forecasts", response_model=List[FinancialForecastResponse])
def list_forecasts(
    tenant_id: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial multi-scenario forward projections (Baseline, Growth, Conservative)."""
    overview = FinancialIntelligenceService.get_overview(db, tenant_id=tenant_id)
    return overview.projected_forecasts

@router.post("/forecasts", response_model=FinancialForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(
    forecast_in: FinancialForecastCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a strategic financial forecast scenario."""
    fc = FinancialIntelligenceService.create_forecast(db, forecast_in=forecast_in)
    resp = FinancialForecastResponse.model_validate(fc)
    resp.projected_mrr = round(fc.projected_mrr_cents / 100.0, 2)
    resp.projected_arr = round(fc.projected_arr_cents / 100.0, 2)
    return resp

# --- Export Report ---
@router.post("/reports/export", response_model=FinancialReportExportResponse)
def export_financial_report(
    req: FinancialReportExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export financial intelligence report (Executive Summary, Transactions, FinOps) as CSV."""
    return FinancialIntelligenceService.export_report(db, req=req)
