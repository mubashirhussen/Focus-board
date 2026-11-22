from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    task_id: Optional[str] = None
    type: str
    title: str
    message: str
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: str
    delivery_channel: str
    created_at: datetime

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

class UnreadCountResponse(BaseModel):
    unread_count: int

class NotificationPreferenceBase(BaseModel):
    enable_in_app: bool = True
    enable_email: bool = False
    enable_due_soon: bool = True
    enable_overdue: bool = True
    enable_daily_plan: bool = True
    daily_reminder_time: str = "09:00"
    timezone: str = "UTC"

class NotificationPreferenceResponse(NotificationPreferenceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

class NotificationPreferenceUpdate(BaseModel):
    enable_in_app: Optional[bool] = None
    enable_email: Optional[bool] = None
    enable_due_soon: Optional[bool] = None
    enable_overdue: Optional[bool] = None
    enable_daily_plan: Optional[bool] = None
    daily_reminder_time: Optional[str] = None
    timezone: Optional[str] = None
