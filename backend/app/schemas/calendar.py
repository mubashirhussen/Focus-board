from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# Legacy backward-compatible classes
class CalendarEventItem(BaseModel):
    id: str
    title: str
    start: datetime
    end: datetime
    source: str = "focusboard"  # "focusboard" or "google_calendar"
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

# Enhanced B7 Calendar Schemas
class CalendarTaskItem(BaseModel):
    id: str
    task_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    category: str = "Design"
    start: datetime
    end: datetime
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    is_all_day: bool = False
    duration_minutes: int = 30
    is_completed: bool = False
    is_overdue: bool = False
    source: str = "focusboard"
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    project_color: Optional[str] = None
    workspace_id: Optional[int] = None
    assignee_id: Optional[int] = None
    labels: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class CalendarDataResponse(BaseModel):
    view: str  # month, week, day, agenda
    start_range: datetime
    end_range: datetime
    timezone: str = "UTC"
    total_tasks: int
    completed_count: int
    overdue_count: int
    due_today_count: int
    tasks: List[CalendarTaskItem]
    external_events: List[CalendarEventItem] = []
    date_groups: Dict[str, List[CalendarTaskItem]] = {}

class CalendarSummaryResponse(BaseModel):
    total_scheduled: int
    due_today: int
    overdue: int
    upcoming_7_days: int
    upcoming_30_days: int
    completed: int
    tasks_by_status: Dict[str, int]
    tasks_by_priority: Dict[str, int]

class RescheduleTaskRequest(BaseModel):
    task_id: str
    new_start: Optional[datetime] = None
    new_end: Optional[datetime] = None
    new_due_date: Optional[str] = None
    new_start_date: Optional[str] = None
    is_all_day: Optional[bool] = None
    duration_minutes: Optional[int] = None
    timezone: Optional[str] = "UTC"

class TaskDateUpdateRequest(BaseModel):
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    estimated_duration_minutes: Optional[int] = None
    timezone: Optional[str] = None
