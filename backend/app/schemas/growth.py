from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# Onboarding
class OnboardingStepUpdate(BaseModel):
    step_id: Union[str, int]
    primary_goal: Optional[str] = None
    dismissed: Optional[bool] = None

class OnboardingProgressResponse(BaseModel):
    current_step: int
    completed_steps: List[str]
    dismissed: bool
    primary_goal: str
    is_completed: bool
    completed_at: Optional[datetime] = None

# Analytics Events
class TrackEventRequest(BaseModel):
    event_name: str
    workspace_id: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None
    source: Optional[str] = "web"

class TrackEventResponse(BaseModel):
    status: str
    event_id: int
    event_name: str
    timestamp: datetime

# Growth Metrics & Funnel
class ActivationFunnelResponse(BaseModel):
    total_users: int
    completed_onboarding: int
    created_workspace: int
    created_first_task: int
    completed_first_task: int
    activation_rate: float
    time_to_activation_hours: float

# Customer Feedback
class FeedbackCreateRequest(BaseModel):
    category: str
    description: Optional[str] = None
    feedback_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    workspace_id: Optional[int] = None

class FeedbackUpdateRequest(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    category: str
    description: str
    rating: Optional[int] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
