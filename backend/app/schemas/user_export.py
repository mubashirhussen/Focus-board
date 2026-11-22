from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class UserProfileData(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

class UserDataExportResponse(BaseModel):
    exported_at: datetime
    user_profile: UserProfileData
    tasks: List[Dict[str, Any]]
    notifications: List[Dict[str, Any]]
    notification_preferences: Optional[Dict[str, Any]] = None
    workspace_memberships: List[Dict[str, Any]]
    comments: List[Dict[str, Any]]
    audit_summary: Dict[str, int]
