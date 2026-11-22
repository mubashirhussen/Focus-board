from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class PlanResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    price_cents: int
    billing_interval: str
    is_active: bool
    features: List[str] = []
    limits: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

class SubscriptionResponse(BaseModel):
    id: int
    tenant_id: str
    plan: PlanResponse
    billing_provider: str
    status: str
    billing_interval: str
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CheckoutRequest(BaseModel):
    plan_id: int
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    provider: str

class ChangePlanRequest(BaseModel):
    plan_id: int

class UsageMetricResponse(BaseModel):
    metric_name: str
    current_usage: int
    limit: int  # -1 represents unlimited
    remaining: int
    reset_date: datetime

class UsageSummaryResponse(BaseModel):
    tenant_id: str
    plan_slug: str
    plan_name: str
    metrics: Dict[str, UsageMetricResponse]
