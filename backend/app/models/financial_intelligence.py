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
    tenant_id = Column(String(64), nullable=False, index=True)  # e.g., "user:1", "ws:1"
    customer_id = Column(String(100), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type = Column(String(32), nullable=False, index=True)
    # SUBSCRIPTION_PAYMENT, ONE_TIME, REFUND, CREDIT, ADJUSTMENT
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
    category = Column(String(64), nullable=False, index=True)
    # CLOUD_INFRA, AI_TOKENS, DATABASE, STORAGE, THIRD_PARTY_API
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
    category = Column(String(64), nullable=False, index=True)
    # OVERALL, CLOUD, AI, MARKETING
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
    scenario_name = Column(String(32), default="BASELINE", nullable=False)
    # BASELINE, GROWTH, CONSERVATIVE
    target_period = Column(String(32), nullable=False)  # e.g., "2027-Q1"
    projected_mrr_cents = Column(Integer, nullable=False)
    projected_arr_cents = Column(Integer, nullable=False)
    projected_churn_rate = Column(Float, default=2.5, nullable=False)
    assumptions_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
