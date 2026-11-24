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
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

from app.api.dependencies import get_current_user
from app.services.intelligence_service import intelligence_engine
from app.services.predictive_intelligence_service import predictive_intelligence_service
from app.schemas.predictive_intelligence import (
    IntelligenceOverviewResponse,
    ProjectHealthDetail,
    DeadlineForecastDetail,
    TaskRiskItem,
    WorkloadAnalysisResponse,
    RecommendationItem,
    IntelligenceSettingUpdate,
    IntelligenceSettingResponse,
)

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

# =============================================================================
# MODULE B47: PREDICTIVE PROJECT INTELLIGENCE ENDPOINTS
# =============================================================================

@router.get("/overview", response_model=IntelligenceOverviewResponse)
def get_predictive_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregated portfolio overview: health, risks, delays, workload & recommendations."""
    return predictive_intelligence_service.get_overview(db, current_user)

@router.get("/projects", response_model=List[ProjectHealthDetail])
def get_projects_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve predictive health scores and indicators for all accessible projects."""
    return predictive_intelligence_service.get_projects_health(db, current_user)

@router.get("/projects/{project_id}/health", response_model=ProjectHealthDetail)
def get_project_health(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deep-dive project health score, metrics breakdown, and corrective actions."""
    res = predictive_intelligence_service.get_project_health_detail(db, project_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return res

@router.get("/projects/{project_id}/forecast", response_model=DeadlineForecastDetail)
def get_project_forecast(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deadline forecast, confidence interval, and critical path blockers for a project."""
    res = predictive_intelligence_service.get_project_forecast_detail(db, project_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return res

@router.get("/projects/{project_id}/risks", response_model=List[TaskRiskItem])
def get_project_task_risks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Task-level risk predictions and evidence for all tasks inside a project."""
    return predictive_intelligence_service.get_project_risks_detail(db, project_id, current_user)

@router.get("/tasks/{task_id}/risk", response_model=TaskRiskItem)
def get_task_risk(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Specific task risk prediction, evidence, and suggested mitigation action."""
    res = predictive_intelligence_service.get_task_risk_detail(db, task_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res

@router.get("/workload", response_model=WorkloadAnalysisResponse)
def get_team_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Team capacity utilization, workload distribution, and non-destructive rebalance proposals."""
    return predictive_intelligence_service.get_workload_analysis(db, current_user)

@router.get("/project-recommendations", response_model=List[RecommendationItem])
def get_project_recommendations(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve AI-driven project and task recommendations with evidence."""
    return predictive_intelligence_service.get_recommendations(db, current_user, status=status)

@router.post("/recommendations/{recommendation_id}/accept")
def accept_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept an AI recommendation and mark it for execution."""
    res = predictive_intelligence_service.review_recommendation(db, recommendation_id, current_user, "ACCEPTED")
    if not res:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"message": "Recommendation accepted successfully", "data": res}

@router.post("/recommendations/{recommendation_id}/reject")
def reject_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject an AI recommendation with review audit."""
    res = predictive_intelligence_service.review_recommendation(db, recommendation_id, current_user, "REJECTED")
    if not res:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"message": "Recommendation rejected", "data": res}

@router.post("/recommendations/{recommendation_id}/complete")
def complete_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an accepted AI recommendation as completed."""
    res = predictive_intelligence_service.review_recommendation(db, recommendation_id, current_user, "COMPLETED")
    if not res:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"message": "Recommendation marked as completed", "data": res}

@router.get("/history")
def get_prediction_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical prediction snapshots and calculated evaluation metrics."""
    return predictive_intelligence_service.get_history(db, current_user)

@router.get("/settings", response_model=IntelligenceSettingResponse)
def get_intelligence_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve predictive intelligence risk thresholds and automated alert settings."""
    s = predictive_intelligence_service.get_or_create_settings(db, current_user)
    return {
        "high_risk_threshold": s.high_risk_threshold,
        "overdue_task_weight": s.overdue_task_weight,
        "dependency_blocker_weight": s.dependency_blocker_weight,
        "workload_overload_hours": s.workload_overload_hours,
        "alert_cooldown_hours": s.alert_cooldown_hours,
        "auto_alerts_enabled": s.auto_alerts_enabled,
        "forecast_confidence_level": s.forecast_confidence_level,
        "updated_at": s.updated_at.isoformat(),
    }

@router.put("/settings", response_model=IntelligenceSettingResponse)
def update_intelligence_settings(
    req: IntelligenceSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update predictive intelligence risk thresholds and automated alert parameters."""
    s = predictive_intelligence_service.get_or_create_settings(db, current_user)
    if req.high_risk_threshold is not None:
        s.high_risk_threshold = req.high_risk_threshold
    if req.overdue_task_weight is not None:
        s.overdue_task_weight = req.overdue_task_weight
    if req.dependency_blocker_weight is not None:
        s.dependency_blocker_weight = req.dependency_blocker_weight
    if req.workload_overload_hours is not None:
        s.workload_overload_hours = req.workload_overload_hours
    if req.alert_cooldown_hours is not None:
        s.alert_cooldown_hours = req.alert_cooldown_hours
    if req.auto_alerts_enabled is not None:
        s.auto_alerts_enabled = req.auto_alerts_enabled
    if req.forecast_confidence_level is not None:
        s.forecast_confidence_level = req.forecast_confidence_level
    s.updated_at = utc_now()
    db.commit()
    db.refresh(s)
    return {
        "high_risk_threshold": s.high_risk_threshold,
        "overdue_task_weight": s.overdue_task_weight,
        "dependency_blocker_weight": s.dependency_blocker_weight,
        "workload_overload_hours": s.workload_overload_hours,
        "alert_cooldown_hours": s.alert_cooldown_hours,
        "auto_alerts_enabled": s.auto_alerts_enabled,
        "forecast_confidence_level": s.forecast_confidence_level,
        "updated_at": s.updated_at.isoformat(),
    }

@router.post("/recalculate/{project_id}")
def recalculate_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger on-demand recalculation of project health, forecasts, task risks & recommendations."""
    res = predictive_intelligence_service.recalculate_project_intelligence(db, project_id, current_user)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project intelligence recalculated successfully", "data": res}

