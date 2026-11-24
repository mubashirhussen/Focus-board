from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScheduleSettingsUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    planning_mode: Optional[str] = "CPM_DRIVEN"
    working_days: Optional[List[str]] = None
    working_hours_per_day: Optional[float] = 8.0
    calendar_holidays: Optional[List[str]] = None
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    auto_recalculate: Optional[bool] = True


class TaskDependencyCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    depends_on_task_id: str
    dependency_type: Optional[str] = "FINISH_TO_START"
    lag_duration: Optional[float] = 0.0
    lag_unit: Optional[str] = "DAYS"


class BaselineCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None


class BudgetUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_budget: float = Field(ge=0.0)
    currency: Optional[str] = "USD"
    notes: Optional[str] = None
    is_approved: Optional[bool] = None


class CostRecordCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    description: str
    amount: float = Field(gt=0.0)
    category_id: Optional[int] = None
    record_type: Optional[str] = "ACTUAL"
    currency: Optional[str] = "USD"


class ScenarioCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None


class ScenarioTaskChangeCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    proposed_start_date: Optional[str] = None
    proposed_due_date: Optional[str] = None
    proposed_duration_days: Optional[float] = None
    proposed_priority: Optional[str] = None
    proposed_assignee_id: Optional[int] = None
