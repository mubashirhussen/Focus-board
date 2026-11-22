from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price_cents = Column(Integer, default=0, nullable=False)
    billing_interval = Column(String(20), default="month", nullable=False)  # month, year
    is_active = Column(Boolean, default=True, nullable=False)
    features_json = Column(Text, nullable=False, default="[]")
    limits_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)  # e.g., "user:1" or "ws:1"
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    billing_provider = Column(String(50), default="mock", nullable=False)  # mock, stripe
    provider_subscription_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), default="active", nullable=False, index=True)  # trialing, active, past_due, canceled, expired
    billing_interval = Column(String(20), default="month", nullable=False)
    current_period_start = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    plan = relationship("Plan", back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_tenant_status", "tenant_id", "status"),
    )

class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), unique=True, index=True, nullable=False)
    provider = Column(String(50), default="mock", nullable=False)
    provider_customer_id = Column(String(100), index=True, nullable=False)
    billing_email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    metric_name = Column(String(64), nullable=False, index=True)  # ai_requests, ai_breakdowns, daily_plans, tasks, projects, etc.
    usage_quantity = Column(Integer, default=1, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("ix_usage_tenant_metric", "tenant_id", "metric_name", "created_at"),
    )
