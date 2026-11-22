import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.billing import Plan, Subscription, UsageRecord

DEFAULT_PLANS = [
    {
        "name": "Free",
        "slug": "free",
        "description": "Essential task management and personal productivity for individuals.",
        "price_cents": 0,
        "billing_interval": "month",
        "features": [
            "Basic task management",
            "Personal productivity dashboard",
            "1 Project",
            "15 AI Assistant requests / mo",
            "5 AI Daily Plans / mo",
            "In-app notifications",
        ],
        "limits": {
            "tasks": 50,
            "workspaces": 1,
            "projects": 1,
            "members": 2,
            "ai_requests": 15,
            "ai_daily_plans": 5,
            "export_operations": 5,
            "calendar_sync": False,
            "automations": False,
        }
    },
    {
        "name": "Starter",
        "slug": "starter",
        "description": "Expanded limits and calendar integration for active solo power users.",
        "price_cents": 900,
        "billing_interval": "month",
        "features": [
            "200 Active tasks",
            "3 Collaborative Workspaces",
            "5 Projects",
            "100 AI requests / mo",
            "30 AI Daily Plans / mo",
            "Google Calendar 2-way sync",
            "CSV and Data Export",
        ],
        "limits": {
            "tasks": 200,
            "workspaces": 3,
            "projects": 5,
            "members": 5,
            "ai_requests": 100,
            "ai_daily_plans": 30,
            "export_operations": 25,
            "calendar_sync": True,
            "automations": True,
        }
    },
    {
        "name": "Pro",
        "slug": "pro",
        "description": "Full AI productivity assistant, time-blocking, and workflow automations.",
        "price_cents": 1900,
        "billing_interval": "month",
        "features": [
            "1,000 Active tasks",
            "10 Workspaces",
            "25 Projects",
            "500 AI requests / mo",
            "100 AI Daily Plans / mo",
            "Automated Workflows & Triggers",
            "Calendar conflict detection",
            "Audit Trail log access",
        ],
        "limits": {
            "tasks": 1000,
            "workspaces": 10,
            "projects": 25,
            "members": 15,
            "ai_requests": 500,
            "ai_daily_plans": 100,
            "export_operations": 100,
            "calendar_sync": True,
            "automations": True,
        }
    },
    {
        "name": "Team",
        "slug": "team",
        "description": "Advanced team workspaces, member task assignments, and shared AI workflows.",
        "price_cents": 4900,
        "billing_interval": "month",
        "features": [
            "5,000 Active tasks",
            "25 Workspaces",
            "100 Projects",
            "50 Team members",
            "2,000 AI requests / mo",
            "500 AI Daily Plans / mo",
            "Real-time WebSocket collaboration",
            "Shared Project Activity feed",
        ],
        "limits": {
            "tasks": 5000,
            "workspaces": 25,
            "projects": 100,
            "members": 50,
            "ai_requests": 2000,
            "ai_daily_plans": 500,
            "export_operations": 500,
            "calendar_sync": True,
            "automations": True,
        }
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "description": "Unlimited capacity, custom integrations, administrative security controls.",
        "price_cents": 19900,
        "billing_interval": "month",
        "features": [
            "Unlimited tasks & projects",
            "Unlimited workspaces & members",
            "10,000 AI requests / mo",
            "Unlimited Daily Plans",
            "Enterprise SLA & Custom Webhooks",
            "Dedicated compliance support",
        ],
        "limits": {
            "tasks": -1,
            "workspaces": -1,
            "projects": -1,
            "members": -1,
            "ai_requests": 10000,
            "ai_daily_plans": -1,
            "export_operations": -1,
            "calendar_sync": True,
            "automations": True,
        }
    }
]

def seed_default_plans(db: Session):
    """Seed or update standard plan catalog in the database."""
    for p_data in DEFAULT_PLANS:
        plan = db.query(Plan).filter(Plan.slug == p_data["slug"]).first()
        if not plan:
            plan = Plan(
                name=p_data["name"],
                slug=p_data["slug"],
                description=p_data["description"],
                price_cents=p_data["price_cents"],
                billing_interval=p_data["billing_interval"],
                is_active=True,
                features_json=json.dumps(p_data["features"]),
                limits_json=json.dumps(p_data["limits"]),
            )
            db.add(plan)
    db.commit()

def get_tenant_id_for_user(user_id: int, workspace_id: Optional[int] = None) -> str:
    """Format standardized tenant ID string."""
    if workspace_id:
        return f"ws:{workspace_id}"
    return f"user:{user_id}"

def get_or_create_subscription(db: Session, tenant_id: str) -> Subscription:
    """Ensure every tenant has an active subscription record (defaulting to Free)."""
    sub = db.query(Subscription).filter(
        Subscription.tenant_id == tenant_id,
        Subscription.status.in_(["active", "trialing"])
    ).first()
    
    if sub:
        return sub

    free_plan = db.query(Plan).filter(Plan.slug == "free").first()
    if not free_plan:
        seed_default_plans(db)
        free_plan = db.query(Plan).filter(Plan.slug == "free").first()

    now = datetime.now(timezone.utc)
    new_sub = Subscription(
        tenant_id=tenant_id,
        plan_id=free_plan.id,
        billing_provider="mock",
        status="active",
        billing_interval="month",
        current_period_start=now,
        current_period_end=now + timedelta(days=365 * 10),
        cancel_at_period_end=False,
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

def check_entitlement(
    db: Session,
    tenant_id: str,
    metric_name: str,
    increment: int = 1,
    raise_exception: bool = True
) -> bool:
    """
    Validate that tenant usage does not exceed plan limits before executing an operation.
    Raises HTTP 402 Payment Required if quota is exhausted.
    """
    sub = get_or_create_subscription(db, tenant_id)
    plan = sub.plan
    limits = json.loads(plan.limits_json) if plan.limits_json else {}

    allowed_limit = limits.get(metric_name, 0)

    # -1 represents unlimited
    if allowed_limit == -1 or allowed_limit is True:
        return True

    if allowed_limit is False or allowed_limit == 0:
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"The '{metric_name}' feature is not available on your current plan ({plan.name}). Please upgrade."
            )
        return False

    # Aggregate current period usage
    current_usage = get_current_period_usage(db, tenant_id, metric_name, sub.current_period_start, sub.current_period_end)

    if (current_usage + increment) > allowed_limit:
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Usage quota exceeded for {metric_name} ({current_usage}/{allowed_limit}). Upgrade your plan to continue."
            )
        return False

    return True

def get_current_period_usage(
    db: Session,
    tenant_id: str,
    metric_name: str,
    period_start: datetime,
    period_end: datetime
) -> int:
    """Calculate total usage for given metric within active billing window."""
    total = db.query(func.sum(UsageRecord.usage_quantity)).filter(
        UsageRecord.tenant_id == tenant_id,
        UsageRecord.metric_name == metric_name,
        UsageRecord.created_at >= period_start,
        UsageRecord.created_at <= period_end
    ).scalar()
    return int(total or 0)

def record_usage(
    db: Session,
    tenant_id: str,
    metric_name: str,
    quantity: int = 1,
    user_id: Optional[int] = None
) -> UsageRecord:
    """Record consumption of a metered plan resource."""
    sub = get_or_create_subscription(db, tenant_id)
    rec = UsageRecord(
        tenant_id=tenant_id,
        user_id=user_id,
        metric_name=metric_name,
        usage_quantity=quantity,
        period_start=sub.current_period_start,
        period_end=sub.current_period_end,
    )
    db.add(rec)
    db.commit()
    return rec
