from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Financial Transaction Schemas ---
class FinancialTransactionBase(BaseModel):
    tenant_id: str = Field(default="default", description="Tenant or workspace reference")
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    customer_id: Optional[str] = None
    subscription_id: Optional[int] = None
    transaction_type: str = Field(..., description="SUBSCRIPTION_PAYMENT, ONE_TIME, REFUND, CREDIT, ADJUSTMENT, SEAT_EXPANSION, AI_TOKEN_ADDON")
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
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    category: str = Field(..., description="CLOUD_INFRA, AI_TOKENS, DATABASE, STORAGE, THIRD_PARTY_API, COMPUTE, AI_SERVICES")
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
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    category: str = Field(..., description="OVERALL, CLOUD, AI, MARKETING, AI_TOKENS")
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
    tenant_id: Optional[str] = "default"
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    scenario_name: str = Field(default="BASELINE", description="BASELINE, GROWTH, CONSERVATIVE, AGGRESSIVE")
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

# --- Data Sources Schemas ---
class FinancialDataSourceCreate(BaseModel):
    name: str
    source_type: str = Field(..., description="INTERNAL, STRIPE, AWS_CUR, QUICKBOOKS, CSV_IMPORT")
    config_json: Optional[str] = "{}"
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None

class FinancialDataSourceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    config_json: Optional[str] = None

class FinancialDataSourceResponse(BaseModel):
    id: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    name: str
    source_type: str
    status: str
    sync_status: str
    last_synced_at: Optional[datetime] = None
    error_message: Optional[str] = None
    config_json: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FinancialDataSourceTestResponse(BaseModel):
    data_source_id: str
    connected: bool
    latency_ms: float
    message: str

class FinancialDataSourceSyncResponse(BaseModel):
    data_source_id: str
    sync_status: str
    synced_records_count: int
    message: str

# --- CSV Import Schemas ---
class FinancialImportPreviewRequest(BaseModel):
    filename: str
    import_type: str = Field(default="TRANSACTIONS", description="TRANSACTIONS or COSTS")
    csv_content: str
    workspace_id: Optional[int] = None

class FinancialImportPreviewResponse(BaseModel):
    filename: str
    import_type: str
    total_rows: int
    valid_rows: int
    error_rows: int
    total_amount: float
    errors: List[str] = []
    sample_preview: List[Dict[str, Any]] = []

class FinancialImportCommitRequest(BaseModel):
    filename: str
    import_type: str = Field(default="TRANSACTIONS", description="TRANSACTIONS or COSTS")
    csv_content: str
    workspace_id: Optional[int] = None

class FinancialImportResponse(BaseModel):
    id: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    filename: str
    import_type: str
    status: str
    total_rows: int
    valid_rows: int
    error_rows: int
    total_amount_cents: int
    total_amount: float = 0.0
    summary_json: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Financial Insight & Anomaly Schemas ---
class FinancialInsightResponse(BaseModel):
    id: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    title: str
    description: str
    insight_type: str
    severity: str
    supporting_metrics_json: str
    recommended_action: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FinancialInsightUpdate(BaseModel):
    status: str = Field(..., description="OPEN, RESOLVED, DISMISSED")

# --- Financial Recommendation Schemas ---
class FinancialRecommendationResponse(BaseModel):
    id: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    title: str
    description: str
    category: str
    potential_savings_cents: int
    potential_savings: float = 0.0
    impact: str
    status: str
    action_taken_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FinancialRecommendationActionRequest(BaseModel):
    action: str = Field(..., description="ACCEPT or REJECT")

# --- Financial Scenario Schemas ---
class FinancialScenarioCreate(BaseModel):
    name: str
    scenario_type: str = Field(default="BASE", description="BASE, BEST, WORST, CUSTOM")
    revenue_growth_rate: float = Field(default=0.05, description="e.g. 0.10 for +10%")
    cost_factor: float = Field(default=1.0, description="e.g. 1.05 for +5% cost")
    workspace_id: Optional[int] = None

class FinancialScenarioResponse(BaseModel):
    id: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    name: str
    scenario_type: str
    revenue_growth_rate: float
    cost_factor: float
    projected_mrr_cents: int
    projected_arr_cents: int
    projected_mrr: float = 0.0
    projected_arr: float = 0.0
    projected_margin_pct: float
    assumptions_json: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FinancialScenarioCompareResponse(BaseModel):
    current_mrr: float
    current_arr: float
    current_margin_pct: float
    scenarios: List[FinancialScenarioResponse]

# --- AI Financial Assistant Schemas ---
class FinancialAIAnalyzeRequest(BaseModel):
    question: Optional[str] = "Provide comprehensive financial executive summary and margin health evaluation."
    workspace_id: Optional[int] = None

class FinancialAIAnalyzeResponse(BaseModel):
    summary: str
    mrr_arr_assessment: str
    margin_and_cogs_evaluation: str
    budget_risk_factors: List[str]
    strategic_recommendations: List[str]
    grounded_metrics: Dict[str, Any]
    generated_at: datetime

# --- Report Export Schemas ---
class FinancialReportExportRequest(BaseModel):
    report_type: str = Field(default="EXECUTIVE_SUMMARY", description="EXECUTIVE_SUMMARY, TRANSACTIONS, FINOPS_COSTS, BUDGETS")
    format: str = Field(default="CSV", description="CSV or JSON")
    workspace_id: Optional[int] = None

class FinancialReportExportResponse(BaseModel):
    report_name: str
    generated_at: datetime
    content: str
    format: str
