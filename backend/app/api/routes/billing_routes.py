import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.billing import Plan, Subscription
from app.schemas.billing import (
    PlanResponse,
    SubscriptionResponse,
    CheckoutRequest,
    CheckoutResponse,
    ChangePlanRequest,
    UsageSummaryResponse,
    UsageMetricResponse,
)
from app.api.dependencies import get_current_user
from app.services.entitlement_service import (
    seed_default_plans,
    get_or_create_subscription,
    get_tenant_id_for_user,
    get_current_period_usage,
)
from app.services.billing_service import (
    create_checkout,
    switch_plan,
    cancel_subscription,
    process_webhook_event,
)

router = APIRouter(prefix="/billing", tags=["Billing & SaaS Subscriptions"])

@router.get("/plans", response_model=List[PlanResponse])
def get_plans(db: Session = Depends(get_db)):
    """List all available subscription plans with parsed features and limits."""
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price_cents.asc()).all()
    if not plans:
        seed_default_plans(db)
        plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price_cents.asc()).all()

    results = []
    for p in plans:
        results.append(PlanResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            price_cents=p.price_cents,
            billing_interval=p.billing_interval,
            is_active=p.is_active,
            features=json.loads(p.features_json) if p.features_json else [],
            limits=json.loads(p.limits_json) if p.limits_json else {},
        ))
    return results

@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(
    workspace_id: Optional[int] = Query(None, description="Optional workspace tenant ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve active subscription for authenticated user or workspace tenant."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    sub = get_or_create_subscription(db, tenant_id)
    p = sub.plan

    plan_resp = PlanResponse(
        id=p.id,
        name=p.name,
        slug=p.slug,
        description=p.description,
        price_cents=p.price_cents,
        billing_interval=p.billing_interval,
        is_active=p.is_active,
        features=json.loads(p.features_json) if p.features_json else [],
        limits=json.loads(p.limits_json) if p.limits_json else {},
    )

    return SubscriptionResponse(
        id=sub.id,
        tenant_id=sub.tenant_id,
        plan=plan_resp,
        billing_provider=sub.billing_provider,
        status=sub.status,
        billing_interval=sub.billing_interval,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        trial_start=sub.trial_start,
        trial_end=sub.trial_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        canceled_at=sub.canceled_at,
    )

@router.post("/checkout", response_model=CheckoutResponse)
def checkout(
    req: CheckoutRequest,
    request: Request,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate checkout session for upgrading subscription plan."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    session_data = create_checkout(
        db=db,
        user=current_user,
        tenant_id=tenant_id,
        plan_id=req.plan_id,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
        request=request
    )
    return CheckoutResponse(
        checkout_url=session_data["checkout_url"],
        session_id=session_data["session_id"],
        provider=session_data.get("provider", "mock")
    )

@router.post("/change-plan", response_model=SubscriptionResponse)
def change_plan(
    req: ChangePlanRequest,
    request: Request,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Switch subscription plan directly."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    sub = switch_plan(
        db=db,
        user=current_user,
        tenant_id=tenant_id,
        new_plan_id=req.plan_id,
        request=request
    )
    p = sub.plan
    plan_resp = PlanResponse(
        id=p.id,
        name=p.name,
        slug=p.slug,
        description=p.description,
        price_cents=p.price_cents,
        billing_interval=p.billing_interval,
        is_active=p.is_active,
        features=json.loads(p.features_json) if p.features_json else [],
        limits=json.loads(p.limits_json) if p.limits_json else {},
    )
    return SubscriptionResponse(
        id=sub.id,
        tenant_id=sub.tenant_id,
        plan=plan_resp,
        billing_provider=sub.billing_provider,
        status=sub.status,
        billing_interval=sub.billing_interval,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        trial_start=sub.trial_start,
        trial_end=sub.trial_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        canceled_at=sub.canceled_at,
    )

@router.post("/cancel", response_model=SubscriptionResponse)
def cancel(
    request: Request,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel subscription at current period end."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    sub = cancel_subscription(db, current_user, tenant_id, request)
    p = sub.plan
    plan_resp = PlanResponse(
        id=p.id,
        name=p.name,
        slug=p.slug,
        description=p.description,
        price_cents=p.price_cents,
        billing_interval=p.billing_interval,
        is_active=p.is_active,
        features=json.loads(p.features_json) if p.features_json else [],
        limits=json.loads(p.limits_json) if p.limits_json else {},
    )
    return SubscriptionResponse(
        id=sub.id,
        tenant_id=sub.tenant_id,
        plan=plan_resp,
        billing_provider=sub.billing_provider,
        status=sub.status,
        billing_interval=sub.billing_interval,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        trial_start=sub.trial_start,
        trial_end=sub.trial_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        canceled_at=sub.canceled_at,
    )

@router.get("/usage", response_model=UsageSummaryResponse)
def get_usage(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve metered resource usage against subscription quotas."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    sub = get_or_create_subscription(db, tenant_id)
    plan = sub.plan
    limits = json.loads(plan.limits_json) if plan.limits_json else {}

    tracked_metrics = ["tasks", "projects", "workspaces", "ai_requests", "ai_daily_plans", "export_operations"]
    metrics_summary = {}

    for metric in tracked_metrics:
        current = get_current_period_usage(db, tenant_id, metric, sub.current_period_start, sub.current_period_end)
        limit = limits.get(metric, 0)
        remaining = -1 if limit == -1 else max(0, limit - current)
        metrics_summary[metric] = UsageMetricResponse(
            metric_name=metric,
            current_usage=current,
            limit=limit,
            remaining=remaining,
            reset_date=sub.current_period_end
        )

    return UsageSummaryResponse(
        tenant_id=tenant_id,
        plan_slug=plan.slug,
        plan_name=plan.name,
        metrics=metrics_summary
    )

@router.post("/webhooks/{provider}")
def billing_webhook(
    provider: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Provider webhook receiver (Stripe / Mock)."""
    return process_webhook_event(db, payload)
