from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.cx_intelligence import (
    FeedbackCreateRequest,
    FeedbackUpdateRequest,
    FeedbackResponse,
    CategoryCreateRequest,
    CategoryResponse,
    SurveyCreateRequest,
    SurveyUpdateRequest,
    SurveyResponse,
    SurveySubmitRequest,
    SurveyResponseItem,
    InsightResponse,
    RecommendationResponse,
    RecommendationConvertRequest,
    JourneyEventCreate,
    JourneyEventResponse,
    CXMetricsResponse,
    CXDashboardResponse,
)
from app.services import cx_intelligence_service

router = APIRouter(prefix="/cx", tags=["Customer Experience Intelligence & Feedback"])

# ==============================================================================
# FEEDBACK ENDPOINTS
# ==============================================================================

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit new customer feedback with automated sentiment scoring and priority tagging."""
    fb = cx_intelligence_service.create_customer_feedback(
        db,
        user_id=current_user.id,
        payload=payload,
    )
    return FeedbackResponse.from_orm(fb)

@router.get("/feedback", response_model=List[FeedbackResponse])
def list_feedback(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    feedback_status: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Query feedbacks with multi-attribute filtering, search, and pagination."""
    # Non-admins only see their own feedback unless in workspace
    is_admin = current_user.role in ["Admin", "Owner"]
    filter_user_id = None if (is_admin or workspace_id) else current_user.id

    items = cx_intelligence_service.list_customer_feedbacks(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
        user_id=filter_user_id,
        status_filter=feedback_status,
        category_filter=category,
        sentiment_filter=sentiment,
        priority_filter=priority,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [FeedbackResponse.from_orm(f) for f in items]

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
def get_feedback(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed information about a specific feedback item."""
    fb = cx_intelligence_service.get_customer_feedback(db, feedback_id)
    if not fb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    if current_user.role not in ["Admin", "Owner"] and fb.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return FeedbackResponse.from_orm(fb)

@router.patch("/feedback/{feedback_id}", response_model=FeedbackResponse)
@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: int,
    payload: FeedbackUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update feedback lifecycle status, priority, assignment, or resolution notes."""
    fb = cx_intelligence_service.update_customer_feedback(
        db,
        feedback_id=feedback_id,
        payload=payload,
        actor_id=current_user.id,
    )
    if not fb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    return FeedbackResponse.from_orm(fb)

@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a customer feedback record."""
    if current_user.role not in ["Admin", "Owner"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")
    success = cx_intelligence_service.delete_customer_feedback(db, feedback_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    return None

# ==============================================================================
# CATEGORIES
# ==============================================================================

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List customer feedback categories."""
    cats = cx_intelligence_service.list_feedback_categories(db, organization_id=organization_id)
    return [CategoryResponse.from_orm(c) for c in cats]

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new feedback taxonomy category."""
    cat = cx_intelligence_service.create_feedback_category(db, payload)
    return CategoryResponse.from_orm(cat)

# ==============================================================================
# METRICS & DASHBOARD
# ==============================================================================

@router.get("/metrics", response_model=CXMetricsResponse)
def get_metrics(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute mathematical CSAT %, NPS, CES, resolution rate and sentiment distributions."""
    return cx_intelligence_service.calculate_cx_metrics(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )

@router.get("/dashboard", response_model=CXDashboardResponse)
def get_dashboard(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full Customer Experience Intelligence dashboard summary payload."""
    return cx_intelligence_service.get_cx_dashboard(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
        days=days,
    )

# ==============================================================================
# INSIGHTS & ACTIONABLE RECOMMENDATIONS
# ==============================================================================

@router.get("/insights", response_model=List[InsightResponse])
def list_insights(
    workspace_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List active customer intelligence insights."""
    from app.models.cx_intelligence import CXInsight
    query = db.query(CXInsight).filter(CXInsight.status == "ACTIVE")
    if workspace_id:
        query = query.filter(CXInsight.workspace_id == workspace_id)
    return [InsightResponse.from_orm(i) for i in query.all()]

@router.post("/insights/detect", response_model=List[InsightResponse])
def detect_insights(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger automated topic clustering and recurring issue insight generation."""
    insights = cx_intelligence_service.detect_recurring_issues_and_generate_insights(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
    )
    return [InsightResponse.from_orm(i) for i in insights]

@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    workspace_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List pending CX recommendations."""
    from app.models.cx_intelligence import CXRecommendation
    query = db.query(CXRecommendation).filter(CXRecommendation.status.in_(["PENDING", "CONVERTED"]))
    if workspace_id:
        query = query.filter(CXRecommendation.workspace_id == workspace_id)
    return [RecommendationResponse.from_orm(r) for r in query.all()]

@router.post("/recommendations/{recommendation_id}/convert", response_model=RecommendationResponse)
def convert_recommendation(
    recommendation_id: str,
    payload: RecommendationConvertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert an actionable CX recommendation into a real FocusBoard task."""
    try:
        rec, _ = cx_intelligence_service.convert_recommendation_to_task(
            db,
            recommendation_id=recommendation_id,
            user_id=current_user.id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            priority=payload.priority or "HIGH",
        )
        return RecommendationResponse.from_orm(rec)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# ==============================================================================
# SURVEYS
# ==============================================================================

@router.post("/surveys", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
def create_survey(
    payload: SurveyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new survey (CSAT, NPS, CES, or custom)."""
    survey = cx_intelligence_service.create_survey(db, payload, creator_id=current_user.id)
    return SurveyResponse.from_orm(survey)

@router.get("/surveys", response_model=List[SurveyResponse])
def list_surveys(
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    survey_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List customer surveys."""
    surveys = cx_intelligence_service.list_surveys(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
        status=survey_status,
    )
    return [SurveyResponse.from_orm(s) for s in surveys]

@router.get("/surveys/{survey_id}", response_model=SurveyResponse)
def get_survey(
    survey_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get survey details with questions."""
    survey = cx_intelligence_service.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return SurveyResponse.from_orm(survey)

@router.post("/surveys/{survey_id}/responses", response_model=SurveyResponseItem, status_code=status.HTTP_201_CREATED)
def submit_survey_response(
    survey_id: str,
    payload: SurveySubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit response to a customer survey."""
    try:
        resp = cx_intelligence_service.submit_survey_response(
            db,
            survey_id=survey_id,
            payload=payload,
            user_id=current_user.id if current_user else None,
        )
        return SurveyResponseItem.from_orm(resp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# ==============================================================================
# CUSTOMER JOURNEY TRACKING
# ==============================================================================

@router.post("/journey/events", response_model=JourneyEventResponse, status_code=status.HTTP_201_CREATED)
def track_journey_event(
    payload: JourneyEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record customer lifecycle journey milestone event."""
    ev = cx_intelligence_service.track_customer_journey_event(
        db,
        payload=payload,
        user_id=current_user.id,
    )
    return JourneyEventResponse(
        id=ev.id,
        user_id=ev.user_id,
        workspace_id=ev.workspace_id,
        organization_id=ev.organization_id,
        stage=ev.stage,
        event_name=ev.event_name,
        sentiment=ev.sentiment,
        metadata=ev.metadata_dict,
        created_at=ev.created_at,
    )

@router.get("/journey/events", response_model=List[JourneyEventResponse])
def list_journey_events(
    stage: Optional[str] = None,
    workspace_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List lifecycle journey events."""
    events = cx_intelligence_service.list_journey_events(
        db,
        workspace_id=workspace_id,
        stage=stage,
        limit=limit,
    )
    return [
        JourneyEventResponse(
            id=e.id,
            user_id=e.user_id,
            workspace_id=e.workspace_id,
            organization_id=e.organization_id,
            stage=e.stage,
            event_name=e.event_name,
            sentiment=e.sentiment,
            metadata=e.metadata_dict,
            created_at=e.created_at,
        )
        for e in events
    ]
