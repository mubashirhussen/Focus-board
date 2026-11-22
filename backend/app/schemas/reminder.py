from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class ReminderBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    scheduled_at: datetime
    timezone: str = "UTC"
    reminder_type: str = "DUE_DATE"  # DUE_DATE, SCHEDULED_START, CUSTOM, RECURRING
    delivery_channel: str = "IN_APP"  # IN_APP, EMAIL, BOTH
    task_id: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None

class ReminderCreate(ReminderBase):
    organization_id: Optional[int] = None

class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = None
    delivery_channel: Optional[str] = None
    status: Optional[str] = None

class ReminderSnoozeRequest(BaseModel):
    snooze_minutes: Optional[int] = None
    snooze_until: Optional[datetime] = None

class ReminderResponse(ReminderBase):
    id: int
    user_id: int
    organization_id: Optional[int] = None
    status: str
    delivery_attempts: int
    max_attempts: int
    snoozed_until: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    error_metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReminderProcessResult(BaseModel):
    processed_count: int
    delivered_count: int
    failed_count: int
    timestamp: datetime

# Recurrence Schemas
class RecurrenceRuleBase(BaseModel):
    frequency: str = "WEEKLY"  # DAILY, WEEKLY, MONTHLY, YEARLY
    interval: int = 1
    weekdays: Optional[List[str]] = None  # ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
    month_day: Optional[int] = None
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None

class RecurrenceRuleCreate(RecurrenceRuleBase):
    pass

class RecurrenceRuleUpdate(BaseModel):
    frequency: Optional[str] = None
    interval: Optional[int] = None
    weekdays: Optional[List[str]] = None
    month_day: Optional[int] = None
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    is_active: Optional[bool] = None

class RecurrenceRuleResponse(RecurrenceRuleBase):
    id: int
    task_id: str
    user_id: int
    organization_id: Optional[int] = None
    occurrences_created: int
    next_run_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
