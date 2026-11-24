"""
Pydantic Schemas for Time Tracking & Timesheets (Module B48).
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TimerStartRequest(BaseModel):
    project_id: Optional[int] = None
    task_id: Optional[str] = None
    description: Optional[str] = None
    billable: bool = True


class ActiveTimerDetail(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    started_at: str
    last_resumed_at: str
    accumulated_seconds: int
    elapsed_seconds: int
    status: str  # RUNNING, PAUSED
    description: Optional[str] = None
    billable: bool


class TimeEntryCreate(BaseModel):
    project_id: Optional[int] = None
    task_id: Optional[str] = None
    description: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    billable: bool = True
    hourly_rate: Optional[float] = None


class TimeEntryUpdate(BaseModel):
    project_id: Optional[int] = None
    task_id: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    billable: Optional[bool] = None
    hourly_rate: Optional[float] = None


class TimeEntryResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    timesheet_id: Optional[int] = None
    description: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: int
    duration_formatted: str
    billable: bool
    hourly_rate: Optional[float] = None
    billable_amount: Optional[float] = None
    entry_source: str
    approval_status: str
    created_at: str


class TimesheetCreate(BaseModel):
    period_start: str
    period_end: str


class TimesheetReviewRequest(BaseModel):
    review_comments: Optional[str] = None


class TimesheetApprovalItem(BaseModel):
    id: int
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    decision: str
    review_comments: Optional[str] = None
    created_at: str


class TimesheetResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    period_start: str
    period_end: str
    total_seconds: int
    total_hours: float
    billable_seconds: int
    billable_hours: float
    non_billable_seconds: int
    non_billable_hours: float
    status: str  # DRAFT, SUBMITTED, APPROVED, REJECTED, REOPENED
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_comments: Optional[str] = None
    created_at: str
    entries_count: int = 0


class TimesheetDetailResponse(TimesheetResponse):
    time_entries: List[TimeEntryResponse] = Field(default_factory=list)
    approvals: List[TimesheetApprovalItem] = Field(default_factory=list)


class TimeTrackingSummaryResponse(BaseModel):
    today_seconds: int
    today_hours: float
    this_week_seconds: int
    this_week_hours: float
    billable_seconds: int
    billable_hours: float
    non_billable_seconds: int
    non_billable_hours: float
    active_timer: Optional[ActiveTimerDetail] = None
    recent_entries: List[TimeEntryResponse] = Field(default_factory=list)
    pending_timesheets_count: int = 0


class ProjectTimeReportItem(BaseModel):
    project_id: Optional[int] = None
    project_name: str
    total_seconds: int
    total_hours: float
    billable_hours: float
    billable_amount: float
    entries_count: int


class UserTimeReportItem(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    total_seconds: int
    total_hours: float
    billable_hours: float
    entries_count: int


class BillableReportResponse(BaseModel):
    total_billable_hours: float
    total_non_billable_hours: float
    total_billable_amount: float
    currency: str = "USD"
    projects_breakdown: List[ProjectTimeReportItem] = Field(default_factory=list)


class TimeTrackingSettingsUpdate(BaseModel):
    default_daily_hours: Optional[float] = None
    default_weekly_hours: Optional[float] = None
    allow_manual_entry: Optional[bool] = None
    allow_overlapping_entries: Optional[bool] = None
    require_timesheet_approval: Optional[bool] = None
    default_billable: Optional[bool] = None
    default_hourly_rate: Optional[float] = None
    max_entry_duration_hours: Optional[float] = None
    submission_deadline_day: Optional[str] = None


class TimeTrackingSettingsResponse(BaseModel):
    default_daily_hours: float
    default_weekly_hours: float
    allow_manual_entry: bool
    allow_overlapping_entries: bool
    require_timesheet_approval: bool
    default_billable: bool
    default_hourly_rate: float
    max_entry_duration_hours: float
    submission_deadline_day: str
    updated_at: str
