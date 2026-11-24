"""
Pydantic Schemas for FocusBoard Module B53: Client & Guest Portal.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class GuestInvitationCreate(BaseModel):
    guest_email: EmailStr
    guest_name: str = Field(..., min_length=2, max_length=100)
    company_name: Optional[str] = Field(None, max_length=120)
    role: str = Field("CLIENT_VIEWER", max_length=32)
    project_ids: Optional[List[int]] = None
    custom_permissions: Optional[Dict[str, bool]] = None
    message: Optional[str] = None
    expiration_days: int = Field(7, ge=1, le=30)


class GuestInvitationResponse(BaseModel):
    id: int
    organization_id: int
    guest_email: str
    guest_name: str
    company_name: Optional[str] = None
    status: str
    role: str
    expires_at: datetime
    created_at: datetime
    raw_token: Optional[str] = None

    class Config:
        from_attributes = True


class GuestInvitationAcceptRequest(BaseModel):
    token: str = Field(..., min_length=10)


class GuestProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    company_name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    status: str
    guest_type: str
    last_access_at: Optional[datetime] = None
    created_at: datetime
    active_projects_count: int = 0


class GuestProjectShareRequest(BaseModel):
    guest_user_id: int
    role: str = "CLIENT_VIEWER"
    custom_permissions: Optional[Dict[str, bool]] = None
    expires_at: Optional[datetime] = None


class ProjectVisibilityUpdateRequest(BaseModel):
    is_shared: Optional[bool] = None
    show_description: Optional[bool] = None
    show_progress: Optional[bool] = None
    progress_mode: Optional[str] = None
    manual_progress_percent: Optional[float] = None
    show_milestones: Optional[bool] = None
    show_tasks: Optional[bool] = None
    show_deliverables: Optional[bool] = None
    show_documents: Optional[bool] = None
    allow_comments: Optional[bool] = None
    allow_feedback: Optional[bool] = None
    allow_uploads: Optional[bool] = None
    allow_approvals: Optional[bool] = None
    custom_banner_message: Optional[str] = None


class ClientDeliverableCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: int = 0
    file_type: Optional[str] = None
    task_id: Optional[str] = None


class ClientDeliverableReviewRequest(BaseModel):
    decision: str = Field(..., max_length=32)  # APPROVED or CHANGES_REQUESTED
    comments: Optional[str] = None


class ClientFeedbackCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=5)
    category: str = "GENERAL"


class ClientFeedbackRespondRequest(BaseModel):
    response_text: str = Field(..., min_length=2)
    status: str = "RESOLVED"


class ClientCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    task_id: Optional[str] = None
    deliverable_id: Optional[int] = None
    feedback_id: Optional[int] = None


class ClientReportCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    summary: Optional[str] = None
    status_override: Optional[str] = None


class ClientPortalSettingsUpdate(BaseModel):
    is_portal_enabled: Optional[bool] = None
    allow_guest_invitations: Optional[bool] = None
    default_role: Optional[str] = None
    default_token_expiration_days: Optional[int] = None
    allow_guest_comments: Optional[bool] = None
    allow_guest_uploads: Optional[bool] = None
    require_approval_reason: Optional[bool] = None
    custom_portal_title: Optional[str] = None
