from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class CalendarEventItem(BaseModel):
    id: str
    title: str
    start: datetime
    end: datetime
    source: str  # "focusboard" or "google_calendar"
    calendar_id: str = "primary"
    description: Optional[str] = None
    task_id: Optional[str] = None
    is_completed: bool = False
    priority: Optional[str] = None

class ScheduleTaskRequest(BaseModel):
    task_id: str
    scheduled_start: datetime
    scheduled_end: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = 30

class CalendarConflictItem(BaseModel):
    task_id: str
    task_title: str
    conflict_type: str  # "OVERLAP", "OUTSIDE_WORKING_HOURS"
    conflicting_event_title: Optional[str] = None
    message: str

class SyncResultResponse(BaseModel):
    status: str
    tasks_synced: int
    events_pulled: int
    timestamp: datetime
