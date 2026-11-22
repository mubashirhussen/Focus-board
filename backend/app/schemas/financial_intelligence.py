from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Financial Transaction Schemas ---
class FinancialTransactionBase(BaseModel):
    tenant_id: str = Field(default="default", description="Tenant or workspace reference")
    customer_id: Optional[str] = None
    subscription_id: Optional[int] = None
    transaction_type: str = Field(..., description="SUBSCRIPTION_PAYMENT, ONE_TIME, REFUND, CREDIT, ADJUSTMENT")
    amount_cents: int = Field(..., description="Amount in cents (e.g. 24900 = $249.00)")
    currency: str = Field(default="USD")
    status: str = Field(default="SUCCEEDED", description="SUCCEEDED, PENDING, FAILED, REFUNDED")
    invoice_id: Optional[str] = None
    provider_tx_id: Optional[str] = None
    description: Optional[str] = None

class FinancialTransactionCreate(FinancialTransactionBase):
    pass

class FinancialTransactionResponse(FinancialTransactionBase):
    id: str
    amount: float = Field(default=0.0, description="Amount in dollars")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Cost Record (FinOps) Schemas ---
class CostRecordBase(BaseModel):
    tenant_id: str = Field(default="default")
    category: str = Field(..., description="CLOUD_INFRA, AI_TOKENS, DATABASE, STORAGE, THIRD_PARTY_API")
    description: str
    amount_cents: int = Field(..., description="Amount in cents")
    currency: str = Field(default="USD")
    billing_period: str = Field(..., description="YYYY-MM")
    cost_date: Optional[datetime] = None

class CostRecordCreate(CostRecordBase):
    pass

class CostRecordResponse(CostRecordBase):
    id: str
    amount: float = Field(default=0.0, description="Amount in dollars")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Financial Budget Schemas ---
class FinancialBudgetBase(BaseModel):
    tenant_id: str = Field(default="default")
    category: str = Field(..., description="OVERALL, CLOUD, AI, MARKETING")
    budget_amount_cents: int = Field(..., description="Limit in cents")
    currency: str = Field(default="USD")
    period: str = Field(default="MONTHLY", description="MONTHLY, QUARTERLY, ANNUAL")
    alert_threshold_percentage: float = Field(default=80.0)
    status: str = Field(default="ACTIVE", description="ACTIVE, EXCEEDED, ARCHIVED")

class FinancialBudgetCreate(FinancialBudgetBase):
    pass

class FinancialBudgetUpdate(BaseModel):
    category: Optional[str] = None
    budget_amount_cents: Optional[int] = None
    alert_threshold_percentage: Optional[float] = None
    status: Optional[str] = None

class FinancialBudgetResponse(FinancialBudgetBase):
    id: str
    budget_amount: float = 0.0
    actual_spent_cents: int = 0
    actual_spent: float = 0.0
    spent_percentage: float = 0.0
    is_alert_triggered: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Financial Forecast Schemas ---
class FinancialForecastBase(BaseModel):
    scenario_name: str = Field(default="BASELINE", description="BASELINE, GROWTH, CONSERVATIVE")
    target_period: str = Field(..., description="e.g. 2027-Q1 or 2026-12")
    projected_mrr_cents: int
    projected_arr_cents: int
    projected_churn_rate: float = 2.5
    assumptions_json: str = "{}"

class FinancialForecastCreate(FinancialForecastBase):
    pass

class FinancialForecastResponse(FinancialForecastBase):
    id: str
    projected_mrr: float = 0.0
    projected_arr: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Financial Overview Analytics ---
class UnitEconomics(BaseModel):
    arpu: float
    cac: float
    ltv: float
    ltv_to_cac_ratio: float
    cac_payback_months: float

class RetentionMetrics(BaseModel):
    customer_churn_rate: float
    mrr_churn_rate: float
    gross_revenue_retention: float
    net_revenue_retention: float

class FinOpsOverview(BaseModel):
    total_direct_costs: float
    cloud_infrastructure_cost: float
    ai_inference_cost: float
    database_and_storage_cost: float
    gross_margin_percentage: float

class MRRBreakdown(BaseModel):
    total_mrr: float
    total_arr: float
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    churned_mrr: float
    net_new_mrr: float
    paying_tenants_count: int

class FinancialOverviewResponse(BaseModel):
    total_mrr: float
    total_arr: float
    gross_revenue: float
    net_revenue: float
    cash_collected: float
    total_refunds: float
    mrr_breakdown: MRRBreakdown
    retention: RetentionMetrics
    unit_economics: UnitEconomics
    finops: FinOpsOverview
    recent_transactions: List[FinancialTransactionResponse] = []
    active_budgets: List[FinancialBudgetResponse] = []
    projected_forecasts: List[FinancialForecastResponse] = []

class FinancialReportExportRequest(BaseModel):
    report_type: str = Field(default="EXECUTIVE_SUMMARY", description="EXECUTIVE_SUMMARY, TRANSACTIONS, FINOPS_COSTS")
    format: str = Field(default="CSV", description="CSV or JSON")

class FinancialReportExportResponse(BaseModel):
    report_name: str
    generated_at: datetime
    content: str
    format: str
