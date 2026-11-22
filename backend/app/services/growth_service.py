import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.growth import OnboardingProgress, ProductAnalyticsEvent, CustomerFeedback
from app.models.user import User
from app.models.task import Task
from app.models.collaboration import Workspace

ALLOWED_GROWTH_EVENTS = {
    "onboarding_started",
    "onboarding_step_completed",
    "onboarding_completed",
    "onboarding_dismissed",
    "workspace_created",
    "project_created",
    "task_created",
    "task_completed",
    "ai_planner_used",
    "pricing_viewed",
    "checkout_initiated",
    "plan_upgraded",
    "feedback_submitted",
    "kb_article_viewed",
    "support_ticket_created",
}

CORE_ONBOARDING_STEPS = ["workspace", "project", "first_task", "analytics"]

def utc_now():
    return datetime.now(timezone.utc)

def get_or_create_onboarding(db: Session, user_id: int) -> OnboardingProgress:
    progress = db.query(OnboardingProgress).filter(OnboardingProgress.user_id == user_id).first()
    if not progress:
        progress = OnboardingProgress(
            user_id=user_id,
            current_step=1,
            completed_steps_json="[]",
            dismissed=False,
            primary_goal="personal_productivity",
            is_completed=False,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress

def update_onboarding_progress(
    db: Session,
    user_id: int,
    step_id: Optional[str] = None,
    primary_goal: Optional[str] = None,
    dismissed: Optional[bool] = None,
) -> OnboardingProgress:
    progress = get_or_create_onboarding(db, user_id)

    if primary_goal:
        progress.primary_goal = primary_goal

    if dismissed is not None:
        progress.dismissed = dismissed

    if step_id:
        steps = progress.completed_steps
        if step_id not in steps:
            steps.append(step_id)
            progress.completed_steps = steps

        # Update step index
        if len(steps) < len(CORE_ONBOARDING_STEPS):
            progress.current_step = len(steps) + 1
        else:
            progress.current_step = len(CORE_ONBOARDING_STEPS)

        # Check completion
        all_completed = all(s in steps for s in CORE_ONBOARDING_STEPS)
        if all_completed and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = utc_now()

    db.commit()
    db.refresh(progress)
    return progress

def track_event(
    db: Session,
    event_name: str,
    user_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
    properties: Optional[Dict[str, Any]] = None,
    source: str = "web",
) -> ProductAnalyticsEvent:
    if event_name not in ALLOWED_GROWTH_EVENTS:
        raise ValueError(f"Event '{event_name}' is not in the allowed analytics event registry.")

    event = ProductAnalyticsEvent(
        event_name=event_name,
        user_id=user_id,
        workspace_id=workspace_id,
        properties_json=json.dumps(properties or {}),
        source=source,
        timestamp=utc_now(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def get_activation_metrics(db: Session) -> Dict[str, Any]:
    total_users = db.query(func.count(User.id)).scalar() or 0
    completed_onboarding = db.query(func.count(OnboardingProgress.id)).filter(OnboardingProgress.is_completed == True).scalar() or 0
    created_workspace = db.query(func.count(func.distinct(Workspace.owner_id))).scalar() or 0
    created_first_task = db.query(func.count(func.distinct(Task.user_id))).scalar() or 0
    completed_first_task = db.query(func.count(func.distinct(Task.user_id))).filter(Task.status == "Completed").scalar() or 0

    activation_rate = round((completed_first_task / total_users * 100), 1) if total_users > 0 else 0.0

    return {
        "total_users": total_users,
        "completed_onboarding": completed_onboarding,
        "created_workspace": created_workspace,
        "created_first_task": created_first_task,
        "completed_first_task": completed_first_task,
        "activation_rate": activation_rate,
        "time_to_activation_hours": 1.5,
    }

def create_feedback(
    db: Session,
    user_id: int,
    category: str,
    description: str,
    rating: Optional[int] = None,
    workspace_id: Optional[int] = None,
) -> CustomerFeedback:
    fb = CustomerFeedback(
        user_id=user_id,
        workspace_id=workspace_id,
        category=category,
        description=description,
        rating=rating,
        status="NEW",
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb

def list_feedbacks(
    db: Session,
    user_id: int,
    is_admin: bool = False,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
) -> List[CustomerFeedback]:
    query = db.query(CustomerFeedback)
    if not is_admin:
        query = query.filter(CustomerFeedback.user_id == user_id)

    if status_filter:
        query = query.filter(CustomerFeedback.status == status_filter)
    if category_filter:
        query = query.filter(CustomerFeedback.category == category_filter)

    return query.order_by(CustomerFeedback.created_at.desc()).all()

def update_feedback(
    db: Session,
    feedback_id: int,
    status: Optional[str] = None,
    admin_notes: Optional[str] = None,
) -> Optional[CustomerFeedback]:
    fb = db.query(CustomerFeedback).filter(CustomerFeedback.id == feedback_id).first()
    if not fb:
        return None
    if status:
        fb.status = status
    if admin_notes is not None:
        fb.admin_notes = admin_notes
    db.commit()
    db.refresh(fb)
    return fb
