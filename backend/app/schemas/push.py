from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class PushSubscribeRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    device_info: Optional[str] = None

class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    device_info: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PushTestRequest(BaseModel):
    title: Optional[str] = "FocusBoard Notification"
    message: Optional[str] = "PWA Web Push is working seamlessly!"
