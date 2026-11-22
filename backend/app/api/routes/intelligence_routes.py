from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.intelligence import IntelligencePreference, InsightFeedback
from app.schemas.intelligence import (
    ProductivityMetricsResponse,
    PatternItem,
    InsightItem,
    RecommendationItem,
    CoachRequest,
    CoachResponse,
    FeedbackRequest,
    IntelligencePreferenceUpdate,
    IntelligencePreferenceResponse,
)
from app.api.dependencies import get_current_user
from app.services.intelligence_service import intelligence_engine

router = APIRouter(prefix="/intelligence", tags=["Product Intelligence & AI Insights"])

@router.get("/metrics", response_model=ProductivityMetricsResponse)
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve actual personal productivity metrics and completion rates."""
    return intelligence_engine.calculate_metrics(db, current_user.id)

@router.get("/patterns", response_model=List[PatternItem])
def get_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detect behavioral patterns, workload imbalances, and execution momentum."""
    return intelligence_engine.detect_patterns(db, current_user.id)

@router.get("/insights", response_model=List[InsightItem])
def get_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate ranked, explainable productivity insights backed by task evidence."""
    return intelligence_engine.generate_insights(db, current_user.id)

@router.get("/recommendations", response_model=List[RecommendationItem])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate prioritized task recommendations with suggested focus times and risk indicators."""
    return intelligence_engine.generate_recommendations(db, current_user.id)

@router.post("/insights/{insight_id}/feedback")
def submit_insight_feedback(
    insight_id: str,
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record user feedback on insight quality (helpful, not_helpful, dismissed)."""
    feedback = db.query(InsightFeedback).filter(
        InsightFeedback.user_id == current_user.id,
        InsightFeedback.insight_id == insight_id
    ).first()

    if feedback:
        feedback.feedback_type = req.feedback_type
        feedback.notes = req.notes
    else:
        feedback = InsightFeedback(
            user_id=current_user.id,
            insight_id=insight_id,
            feedback_type=req.feedback_type,
            notes=req.notes
        )
        db.add(feedback)

    db.commit()
    return {"message": "Feedback recorded successfully"}

@router.post("/insights/{insight_id}/dismiss")
def dismiss_insight(
    insight_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dismiss a specific insight so it is hidden from future view."""
    return submit_insight_feedback(
        insight_id=insight_id,
        req=FeedbackRequest(feedback_type="dismissed"),
        db=db,
        current_user=current_user
    )

@router.post("/coach", response_model=CoachResponse)
def query_ai_coach(
    req: CoachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Interactive data-grounded AI Productivity Coach with proposal actions."""
    return intelligence_engine.generate_coach_response(db, current_user.id, req.message)

@router.get("/preferences", response_model=IntelligencePreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve intelligence and personal productivity preferences."""
    pref = db.query(IntelligencePreference).filter(IntelligencePreference.user_id == current_user.id).first()
    if not pref:
        pref = IntelligencePreference(user_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref

@router.put("/preferences", response_model=IntelligencePreferenceResponse)
def update_preferences(
    req: IntelligencePreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update intelligence preferences."""
    pref = db.query(IntelligencePreference).filter(IntelligencePreference.user_id == current_user.id).first()
    if not pref:
        pref = IntelligencePreference(user_id=current_user.id)
        db.add(pref)

    if req.insights_enabled is not None:
        pref.insights_enabled = req.insights_enabled
    if req.coaching_enabled is not None:
        pref.coaching_enabled = req.coaching_enabled
    if req.work_start_hour is not None:
        pref.work_start_hour = req.work_start_hour
    if req.work_end_hour is not None:
        pref.work_end_hour = req.work_end_hour
    if req.time_zone is not None:
        pref.time_zone = req.time_zone

    db.commit()
    db.refresh(pref)
    return pref
