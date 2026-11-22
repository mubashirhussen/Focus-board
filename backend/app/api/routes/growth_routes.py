from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.growth import (
    OnboardingStepUpdate,
    OnboardingProgressResponse,
    TrackEventRequest,
    TrackEventResponse,
    ActivationFunnelResponse,
    FeedbackCreateRequest,
    FeedbackUpdateRequest,
    FeedbackResponse,
)
from app.services import growth_service

router = APIRouter(prefix="/growth", tags=["SaaS Growth & Product Analytics"])

@router.get("/onboarding", response_model=OnboardingProgressResponse)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve onboarding progress, checklist state, and goal for the current user."""
    progress = growth_service.get_or_create_onboarding(db, current_user.id)
    return OnboardingProgressResponse(
        current_step=progress.current_step,
        completed_steps=progress.completed_steps,
        dismissed=progress.dismissed,
        primary_goal=progress.primary_goal,
        is_completed=progress.is_completed,
        completed_at=progress.completed_at,
    )

@router.post("/onboarding", response_model=OnboardingProgressResponse)
def update_onboarding_status(
    payload: OnboardingStepUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update onboarding step completion, primary goal, or dismissal."""
    progress = growth_service.update_onboarding_progress(
        db,
        user_id=current_user.id,
        step_id=str(payload.step_id),
        primary_goal=payload.primary_goal,
        dismissed=payload.dismissed,
    )
    return OnboardingProgressResponse(
        current_step=progress.current_step,
        completed_steps=progress.completed_steps,
        dismissed=progress.dismissed,
        primary_goal=progress.primary_goal,
        is_completed=progress.is_completed,
        completed_at=progress.completed_at,
    )

@router.post("/events", response_model=TrackEventResponse)
def track_product_event(
    payload: TrackEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Track privacy-safe behavioral product analytics event."""
    try:
        event = growth_service.track_event(
            db,
            event_name=payload.event_name,
            user_id=current_user.id,
            workspace_id=payload.workspace_id,
            properties=payload.properties,
            source=payload.source or "web",
        )
        return TrackEventResponse(
            status="success",
            event_id=event.id,
            event_name=event.event_name,
            timestamp=event.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/activation", response_model=ActivationFunnelResponse)
@router.get("/activation-funnel", response_model=ActivationFunnelResponse)
def get_activation_funnel(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get aggregate product activation metrics and onboarding funnel."""
    metrics = growth_service.get_activation_metrics(db)
    return ActivationFunnelResponse(**metrics)

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_customer_feedback(
    payload: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit in-app customer feedback or feature request."""
    desc = payload.description or payload.feedback_text or "General feedback"
    fb = growth_service.create_feedback(
        db,
        user_id=current_user.id,
        category=payload.category,
        description=desc,
        rating=payload.rating,
        workspace_id=payload.workspace_id,
    )
    return FeedbackResponse(
        id=fb.id,
        user_id=fb.user_id,
        category=fb.category,
        description=fb.description,
        rating=fb.rating,
        status=fb.status,
        admin_notes=fb.admin_notes,
        created_at=fb.created_at,
    )

@router.get("/feedback", response_model=List[FeedbackResponse])
def list_customer_feedbacks(
    category: Optional[str] = None,
    feedback_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List customer feedbacks (admins see all, users see their own)."""
    is_admin = current_user.role in ["Admin", "Owner"]
    items = growth_service.list_feedbacks(
        db,
        user_id=current_user.id,
        is_admin=is_admin,
        status_filter=feedback_status,
        category_filter=category,
    )
    return [
        FeedbackResponse(
            id=f.id,
            user_id=f.user_id,
            category=f.category,
            description=f.description,
            rating=f.rating,
            status=f.status,
            admin_notes=f.admin_notes if is_admin else None,
            created_at=f.created_at,
        )
        for f in items
    ]

@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
@router.patch("/feedback/{feedback_id}", response_model=FeedbackResponse)
def update_feedback_status(
    feedback_id: int,
    payload: FeedbackUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin endpoint to update feedback status and internal notes."""
    if current_user.role not in ["Admin", "Owner"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")

    fb = growth_service.update_feedback(
        db,
        feedback_id=feedback_id,
        status=payload.status,
        admin_notes=payload.admin_notes,
    )
    if not fb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found.")

    return FeedbackResponse(
        id=fb.id,
        user_id=fb.user_id,
        category=fb.category,
        description=fb.description,
        rating=fb.rating,
        status=fb.status,
        admin_notes=fb.admin_notes,
        created_at=fb.created_at,
    )
