from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- Feedback Schemas ---
class FeedbackCreateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    feedback_text: Optional[str] = None  # fallback for description
    category: Optional[str] = "general_feedback"
    feedback_type: Optional[str] = "GENERAL"
    rating: Optional[int] = Field(None, ge=1, le=5)
    source: Optional[str] = "IN_APP"
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None
    project_id: Optional[int] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

class FeedbackUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    feedback_type: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None  # NEW, REVIEWING, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CLOSED, ARCHIVED
    priority: Optional[str] = None  # LOW, MEDIUM, HIGH, URGENT
    assigned_user_id: Optional[int] = None
    admin_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class FeedbackResponse(BaseModel):
    id: int
    title: Optional[str] = None
    user_id: int
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None
    project_id: Optional[int] = None
    category: str
    feedback_type: str
    source: str
    description: str
    rating: Optional[int] = None
    sentiment: str
    sentiment_score: float
    sentiment_confidence: float
    priority: str
    priority_score: float
    status: str
    assigned_user_id: Optional[int] = None
    tags: List[str] = []
    admin_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    language: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Feedback Categories ---
class CategoryCreateRequest(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    organization_id: Optional[int] = None

class CategoryResponse(BaseModel):
    id: int
    organization_id: Optional[int] = None
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Surveys ---
class SurveyQuestionCreate(BaseModel):
    question_text: str
    question_type: str = "RATING_5"  # RATING_5, NPS_10, CES_7, TEXT, MULTIPLE_CHOICE
    options: Optional[List[str]] = []
    is_required: bool = True
    order_index: int = 0

class SurveyQuestionResponse(BaseModel):
    id: str
    survey_id: str
    question_text: str
    question_type: str
    options: List[str] = []
    is_required: bool
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True

class SurveyCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    survey_type: str = "CSAT"  # CSAT, NPS, CES, CUSTOM
    status: Optional[str] = "ACTIVE"
    target_audience: Optional[str] = "ALL"
    trigger_event: Optional[str] = None
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None
    settings: Optional[Dict[str, Any]] = {}
    questions: Optional[List[SurveyQuestionCreate]] = []

class SurveyUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    target_audience: Optional[str] = None
    trigger_event: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class SurveyResponse(BaseModel):
    id: str
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    survey_type: str
    status: str
    target_audience: str
    trigger_event: Optional[str] = None
    settings: Dict[str, Any] = {}
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    questions: List[SurveyQuestionResponse] = []

    class Config:
        from_attributes = True

class SurveySubmitRequest(BaseModel):
    score: Optional[float] = None
    feedback_text: Optional[str] = None
    respondent_reference: Optional[str] = None
    answers: Optional[Dict[str, Any]] = {}

class SurveyResponseItem(BaseModel):
    id: str
    survey_id: str
    user_id: Optional[int] = None
    respondent_reference: Optional[str] = None
    score: Optional[float] = None
    feedback_text: Optional[str] = None
    answers: Dict[str, Any] = {}
    sentiment: str
    sentiment_score: float
    submitted_at: datetime

    class Config:
        from_attributes = True

# --- Insights & Recommendations ---
class InsightCreateRequest(BaseModel):
    title: str
    description: str
    insight_type: str = "TREND"
    severity: str = "MEDIUM"
    priority: str = "MEDIUM"
    confidence: float = 0.85
    recommended_action: Optional[str] = None
    supporting_metrics: Optional[Dict[str, Any]] = {}
    supporting_feedback_ids: Optional[List[int]] = []
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None

class InsightResponse(BaseModel):
    id: str
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None
    title: str
    description: str
    insight_type: str
    severity: str
    priority: str
    confidence: float
    supporting_metrics: Dict[str, Any] = {}
    supporting_feedback_ids: List[int] = []
    recommended_action: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: str
    insight_id: Optional[str] = None
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None
    title: str
    description: str
    action_type: str
    status: str
    task_id: Optional[str] = None
    created_at: datetime
    converted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RecommendationConvertRequest(BaseModel):
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    priority: Optional[str] = "HIGH"
    assignee_id: Optional[int] = None

# --- Journey Events ---
class JourneyEventCreate(BaseModel):
    stage: str  # ONBOARDING, ADOPTION, RETENTION, EXPANSION, CHURN_RISK, ADVOCACY
    event_name: str
    sentiment: Optional[str] = "NEUTRAL"
    metadata: Optional[Dict[str, Any]] = {}
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None

class JourneyEventResponse(BaseModel):
    id: str
    user_id: Optional[int] = None
    workspace_id: Optional[int] = None
    organization_id: Optional[int] = None
    stage: str
    event_name: str
    sentiment: str
    metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True

# --- Metrics, Analytics & Dashboard ---
class CXMetricsResponse(BaseModel):
    csat: float = 0.0                      # % satisfied (>=4 stars or favorable rating)
    nps: float = 0.0                       # % promoters - % detractors (-100 to +100)
    ces: float = 0.0                       # Average effort score (1 to 7)
    average_rating: float = 0.0            # 1.0 to 5.0
    total_feedback_count: int = 0
    resolution_rate: float = 0.0           # % resolved
    sentiment_distribution: Dict[str, int] = {"positive": 0, "neutral": 0, "negative": 0, "mixed": 0}
    rating_distribution: Dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

class CXDashboardResponse(BaseModel):
    metrics: CXMetricsResponse
    recent_feedback: List[FeedbackResponse] = []
    top_categories: List[Dict[str, Any]] = []
    trends: List[Dict[str, Any]] = []
    active_insights: List[InsightResponse] = []
    recommendations: List[RecommendationResponse] = []
