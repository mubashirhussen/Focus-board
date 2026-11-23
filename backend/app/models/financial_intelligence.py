import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id = Column(String(64), primary_key=True, default=lambda: f"tx_{uuid.uuid4().hex[:12]}")
    tenant_id = Column(String(64), nullable=False, index=True)  # e.g., "user:1", "ws:1", "default"
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(String(100), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type = Column(String(32), nullable=False, index=True)
    # SUBSCRIPTION_PAYMENT, ONE_TIME, REFUND, CREDIT, ADJUSTMENT, SEAT_EXPANSION, AI_TOKEN_ADDON
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    status = Column(String(32), default="SUCCEEDED", nullable=False, index=True)
    # SUCCEEDED, PENDING, FAILED, REFUNDED
    invoice_id = Column(String(64), nullable=True, index=True)
    provider_tx_id = Column(String(128), nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    subscription = relationship("Subscription")

class FinancialMetricSnapshot(Base):
    __tablename__ = "financial_metric_snapshots"

    id = Column(String(64), primary_key=True, default=lambda: f"snap_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    period_date = Column(String(32), nullable=False, index=True)  # YYYY-MM
    mrr_cents = Column(Integer, default=0, nullable=False)
    arr_cents = Column(Integer, default=0, nullable=False)
    gross_revenue_cents = Column(Integer, default=0, nullable=False)
    net_revenue_cents = Column(Integer, default=0, nullable=False)
    new_mrr_cents = Column(Integer, default=0, nullable=False)
    expansion_mrr_cents = Column(Integer, default=0, nullable=False)
    contraction_mrr_cents = Column(Integer, default=0, nullable=False)
    churned_mrr_cents = Column(Integer, default=0, nullable=False)
    active_subscriptions = Column(Integer, default=0, nullable=False)
    paying_customers = Column(Integer, default=0, nullable=False)
    churned_customers = Column(Integer, default=0, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class CostRecord(Base):
    __tablename__ = "cost_records"

    id = Column(String(64), primary_key=True, default=lambda: f"cost_{uuid.uuid4().hex[:12]}")
    tenant_id = Column(String(64), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    # CLOUD_INFRA, AI_TOKENS, DATABASE, STORAGE, THIRD_PARTY_API, COMPUTE, AI_SERVICES
    description = Column(String(255), nullable=False)
    amount_cents = Column(Integer, default=0, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    billing_period = Column(String(32), nullable=False)  # YYYY-MM
    cost_date = Column(DateTime, default=utc_now, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class FinancialBudget(Base):
    __tablename__ = "financial_budgets"

    id = Column(String(64), primary_key=True, default=lambda: f"bdg_{uuid.uuid4().hex[:12]}")
    tenant_id = Column(String(64), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    # OVERALL, CLOUD, AI, MARKETING, AI_TOKENS
    budget_amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    period = Column(String(32), default="MONTHLY", nullable=False)
    # MONTHLY, QUARTERLY, ANNUAL
    alert_threshold_percentage = Column(Float, default=80.0, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False)
    # ACTIVE, EXCEEDED, ARCHIVED
    created_at = Column(DateTime, default=utc_now, nullable=False)

class FinancialForecast(Base):
    __tablename__ = "financial_forecasts"

    id = Column(String(64), primary_key=True, default=lambda: f"fc_{uuid.uuid4().hex[:12]}")
    tenant_id = Column(String(64), default="default", nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    scenario_name = Column(String(32), default="BASELINE", nullable=False)
    # BASELINE, GROWTH, CONSERVATIVE, AGGRESSIVE
    target_period = Column(String(32), nullable=False)  # e.g., "2027-Q1" or "2026-12"
    projected_mrr_cents = Column(Integer, nullable=False)
    projected_arr_cents = Column(Integer, nullable=False)
    projected_churn_rate = Column(Float, default=2.5, nullable=False)
    assumptions_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class FinancialDataSource(Base):
    __tablename__ = "financial_data_sources"

    id = Column(String(64), primary_key=True, default=lambda: f"fds_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    source_type = Column(String(64), nullable=False)  # INTERNAL, STRIPE, AWS_CUR, QUICKBOOKS, CSV_IMPORT
    status = Column(String(32), default="CONNECTED", nullable=False)  # CONNECTED, DISCONNECTED, ERROR
    sync_status = Column(String(32), default="IDLE", nullable=False)  # IDLE, SYNCING, SUCCESS, FAILED
    last_synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    config_json = Column(Text, default="{}", nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

class FinancialImport(Base):
    __tablename__ = "financial_imports"

    id = Column(String(64), primary_key=True, default=lambda: f"fimp_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    import_type = Column(String(32), default="TRANSACTIONS", nullable=False)  # TRANSACTIONS, COSTS
    status = Column(String(32), default="PREVIEW", nullable=False)  # PREVIEW, COMMITTED, ROLLED_BACK, FAILED
    total_rows = Column(Integer, default=0, nullable=False)
    valid_rows = Column(Integer, default=0, nullable=False)
    error_rows = Column(Integer, default=0, nullable=False)
    total_amount_cents = Column(Integer, default=0, nullable=False)
    summary_json = Column(Text, default="{}", nullable=False)
    imported_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class FinancialInsight(Base):
    __tablename__ = "financial_insights"

    id = Column(String(64), primary_key=True, default=lambda: f"fins_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    insight_type = Column(String(64), nullable=False)  # BUDGET_OVERRUN, COST_SPIKE, REVENUE_GROWTH, CHURN_SURGE, MARGIN_CONTRACTION
    severity = Column(String(32), default="INFO", nullable=False)  # INFO, WARNING, CRITICAL
    supporting_metrics_json = Column(Text, default="{}", nullable=False)
    recommended_action = Column(Text, nullable=True)
    status = Column(String(32), default="OPEN", nullable=False)  # OPEN, RESOLVED, DISMISSED
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

class FinancialRecommendation(Base):
    __tablename__ = "financial_recommendations"

    id = Column(String(64), primary_key=True, default=lambda: f"frec_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False)  # COST_OPTIMIZATION, REVENUE_EXPANSION, BUDGET_ALIGNMENT
    potential_savings_cents = Column(Integer, default=0, nullable=False)
    impact = Column(String(32), default="MEDIUM", nullable=False)  # HIGH, MEDIUM, LOW
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, ACCEPTED, REJECTED
    action_taken_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class FinancialScenario(Base):
    __tablename__ = "financial_scenarios"

    id = Column(String(64), primary_key=True, default=lambda: f"fscen_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    scenario_type = Column(String(32), default="BASE", nullable=False)  # BASE, BEST, WORST, CUSTOM
    revenue_growth_rate = Column(Float, default=0.05, nullable=False)
    cost_factor = Column(Float, default=1.0, nullable=False)
    projected_mrr_cents = Column(Integer, default=0, nullable=False)
    projected_arr_cents = Column(Integer, default=0, nullable=False)
    projected_margin_pct = Column(Float, default=80.0, nullable=False)
    assumptions_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
