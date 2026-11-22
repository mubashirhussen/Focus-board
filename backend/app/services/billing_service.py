from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request

from app.models.billing import Plan, Subscription, BillingCustomer
from app.models.user import User
from app.services.billing_provider import get_billing_provider
from app.services.entitlement_service import get_or_create_subscription
from app.services.audit_service import record_audit_log

def create_checkout(
    db: Session,
    user: User,
    tenant_id: str,
    plan_id: int,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    request: Optional[Request] = None
) -> Dict[str, Any]:
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    provider = get_billing_provider()
    s_url = success_url or "http://localhost:5173/billing?status=success"
    c_url = cancel_url or "http://localhost:5173/billing?status=cancelled"

    session_data = provider.create_checkout_session(
        tenant_id=tenant_id,
        plan_slug=plan.slug,
        price_cents=plan.price_cents,
        success_url=s_url,
        cancel_url=c_url,
        customer_email=user.email
    )

    record_audit_log(
        db=db,
        event_type="BILLING_CHECKOUT_INITIATED",
        actor_id=user.id,
        resource_type="PLAN",
        resource_id=str(plan.id),
        request=request,
        metadata={"plan_slug": plan.slug, "price_cents": plan.price_cents}
    )

    return session_data

def switch_plan(
    db: Session,
    user: User,
    tenant_id: str,
    new_plan_id: int,
    request: Optional[Request] = None
) -> Subscription:
    new_plan = db.query(Plan).filter(Plan.id == new_plan_id, Plan.is_active == True).first()
    if not new_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    sub = get_or_create_subscription(db, tenant_id)
    old_plan_name = sub.plan.name
    now = datetime.now(timezone.utc)

    sub.plan_id = new_plan.id
    sub.status = "active"
    sub.current_period_start = now
    sub.current_period_end = now + timedelta(days=30)
    sub.cancel_at_period_end = False
    sub.canceled_at = None

    db.commit()
    db.refresh(sub)

    record_audit_log(
        db=db,
        event_type="BILLING_PLAN_CHANGED",
        actor_id=user.id,
        resource_type="SUBSCRIPTION",
        resource_id=str(sub.id),
        request=request,
        metadata={"from_plan": old_plan_name, "to_plan": new_plan.name}
    )

    return sub

def cancel_subscription(
    db: Session,
    user: User,
    tenant_id: str,
    request: Optional[Request] = None
) -> Subscription:
    sub = get_or_create_subscription(db, tenant_id)
    sub.cancel_at_period_end = True
    sub.canceled_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(sub)

    record_audit_log(
        db=db,
        event_type="BILLING_SUBSCRIPTION_CANCELED",
        actor_id=user.id,
        resource_type="SUBSCRIPTION",
        resource_id=str(sub.id),
        request=request,
        metadata={"plan_name": sub.plan.name}
    )

    return sub

def process_webhook_event(db: Session, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Authoritative webhook processor updating subscription states."""
    event_type = event_data.get("type", "")
    data_object = event_data.get("data", {}).get("object", {})

    tenant_id = data_object.get("client_reference_id") or data_object.get("metadata", {}).get("tenant_id")

    if event_type == "checkout.session.completed" and tenant_id:
        plan_slug = data_object.get("metadata", {}).get("plan_slug", "starter")
        plan = db.query(Plan).filter(Plan.slug == plan_slug).first()
        if plan:
            sub = get_or_create_subscription(db, tenant_id)
            sub.plan_id = plan.id
            sub.status = "active"
            now = datetime.now(timezone.utc)
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=30)
            db.commit()

    return {"status": "processed", "event_type": event_type}
