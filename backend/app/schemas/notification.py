from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    category: str = "TASK"
    type: str
    title: str
    message: str
    actor_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    task_id: Optional[str] = None
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    comment_id: Optional[int] = None
    invitation_id: Optional[int] = None
    priority: str = "NORMAL"
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: str
    delivery_channel: str
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    created_at: datetime

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

class UnreadCountResponse(BaseModel):
    unread_count: int

class NotificationSummaryResponse(BaseModel):
    total_count: int
    unread_count: int
    read_count: int
    archived_count: int
    by_category: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}

class NotificationCreateRequest(BaseModel):
    category: Optional[str] = Field("TASK", pattern="^(TASK|PROJECT|TEAM|WORKSPACE|COLLABORATION|INVITATION|CALENDAR|SYSTEM|AUTOMATION)$")
    type: str
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    priority: Optional[str] = Field("NORMAL", pattern="^(LOW|NORMAL|HIGH|URGENT)$")
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    task_id: Optional[str] = None
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    workspace_id: Optional[int] = None
    delivery_channel: Optional[str] = Field("IN_APP", pattern="^(IN_APP|EMAIL|PUSH|BOTH)$")
    metadata: Optional[Dict[str, Any]] = None

class BulkNotificationActionRequest(BaseModel):
    notification_ids: List[int]

class NotificationPreferenceBase(BaseModel):
    enable_in_app: bool = True
    enable_email: bool = False
    enable_push: bool = True
    enable_due_soon: bool = True
    enable_overdue: bool = True
    enable_daily_plan: bool = True
    enable_task_assigned: bool = True
    enable_comments: bool = True
    enable_mentions: bool = True
    enable_project_updates: bool = True
    enable_team_updates: bool = True
    enable_invitations: bool = True
    daily_reminder_time: str = "09:00"
    timezone: str = "UTC"

class NotificationPreferenceResponse(NotificationPreferenceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    category_overrides: Dict[str, Any] = {}

class NotificationPreferenceUpdate(BaseModel):
    enable_in_app: Optional[bool] = None
    enable_email: Optional[bool] = None
    enable_push: Optional[bool] = None
    enable_due_soon: Optional[bool] = None
    enable_overdue: Optional[bool] = None
    enable_daily_plan: Optional[bool] = None
    enable_task_assigned: Optional[bool] = None
    enable_comments: Optional[bool] = None
    enable_mentions: Optional[bool] = None
    enable_project_updates: Optional[bool] = None
    enable_team_updates: Optional[bool] = None
    enable_invitations: Optional[bool] = None
    daily_reminder_time: Optional[str] = None
    timezone: Optional[str] = None
    category_overrides: Optional[Dict[str, Any]] = None
