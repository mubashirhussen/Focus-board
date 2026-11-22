from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Application
class DeveloperApplicationCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = None
    app_type: str = Field("INTERNAL", pattern="^(INTERNAL|PARTNER|PUBLIC)$")
    redirect_uri: Optional[str] = None

class DeveloperApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None
    app_type: Optional[str] = Field(None, pattern="^(INTERNAL|PARTNER|PUBLIC)$")
    redirect_uri: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(DRAFT|ACTIVE|SUSPENDED|REVOKED)$")

class DeveloperApplicationResponse(BaseModel):
    id: str
    user_id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    app_type: str
    redirect_uri: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Credentials / API Keys
class DeveloperCredentialCreate(BaseModel):
    application_id: str
    name: str = Field(..., max_length=128)
    scopes: List[str] = Field(default_factory=lambda: ["tasks:read"])
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)

class DeveloperCredentialResponse(BaseModel):
    id: str
    application_id: str
    user_id: int
    key_prefix: str
    name: str
    scopes: List[str]
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DeveloperCredentialCreatedResponse(DeveloperCredentialResponse):
    plaintext_key: str  # Only returned once upon creation!

# Webhook Subscriptions
class WebhookSubscriptionCreate(BaseModel):
    application_id: Optional[str] = None
    target_url: str = Field(..., max_length=512)
    events: List[str] = Field(default_factory=lambda: ["task.created", "task.updated", "task.completed"])

class WebhookSubscriptionUpdate(BaseModel):
    target_url: Optional[str] = Field(None, max_length=512)
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None

class WebhookSubscriptionResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    user_id: int
    workspace_id: int
    target_url: str
    events: List[str]
    is_active: bool
    failure_count: int
    last_delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WebhookSubscriptionCreatedResponse(WebhookSubscriptionResponse):
    secret_key: str  # Only displayed once or used to verify HMAC

class WebhookDeliveryResponse(BaseModel):
    id: str
    subscription_id: str
    event_type: str
    payload_json: str
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    attempt_count: int
    delivered_at: datetime
    is_success: bool
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

# Public API Request / Response schemas
class PublicTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    category: str = Field("General", max_length=50)
    project_id: Optional[int] = None

class PublicTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    category: Optional[str] = None
    project_id: Optional[int] = None

class PublicTaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    category: str
    due_date: Optional[str] = None
    project_id: Optional[int] = None
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PublicProjectResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    status: str
    deadline: Optional[Union[datetime, str]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DeveloperPortalStats(BaseModel):
    total_applications: int
    active_credentials: int
    total_webhooks: int
    api_calls_last_30d: int
    api_success_rate: float
