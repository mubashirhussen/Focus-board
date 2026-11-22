from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    category: Optional[str] = "Design"
    status: Optional[str] = "Todo"
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = ""
    start_date: Optional[str] = ""
    is_all_day: Optional[bool] = False
    timezone_name: Optional[str] = "UTC"
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = 30
    actual_minutes: Optional[int] = 0
    progress_percent: Optional[float] = 0.0
    labels: Optional[List[str]] = Field(default_factory=list)
    sort_order: Optional[int] = 0
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    parent_task_id: Optional[str] = None

class TaskCreate(TaskBase):
    id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    is_all_day: Optional[bool] = None
    timezone_name: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    progress_percent: Optional[float] = None
    labels: Optional[List[str]] = None
    sort_order: Optional[int] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    parent_task_id: Optional[str] = None

class TaskStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)

class TaskPriorityUpdate(BaseModel):
    priority: str = Field(..., min_length=1, max_length=50)

class TaskAssignUpdate(BaseModel):
    assignee_id: Optional[int] = None

class TaskSubtaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    category: Optional[str] = "Development"
    status: Optional[str] = "Todo"
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = ""
    assignee_id: Optional[int] = None
    estimated_duration_minutes: Optional[int] = 30

class TaskDependencyCreate(BaseModel):
    depends_on_task_id: str = Field(..., min_length=1)
    dependency_type: Optional[str] = Field(default="FINISH_TO_START")

class TaskDependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    depends_on_task_id: str
    dependency_type: str
    created_at: datetime
    depends_on_task_title: Optional[str] = None
    depends_on_task_status: Optional[str] = None

class TaskReorderItem(BaseModel):
    id: str
    sort_order: int

class TaskReorderRequest(BaseModel):
    items: List[TaskReorderItem]

class TaskBulkRequest(BaseModel):
    task_ids: List[str]
    action: str # "update_status", "update_priority", "assign", "delete", "archive", "restore"
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None

class TaskSummaryResponse(BaseModel):
    total: int
    completed: int
    in_progress: int
    todo: int
    overdue: int
    due_today: int
    completion_rate: float
    by_priority: Dict[str, int]
    by_category: Dict[str, int]

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    description: Optional[str] = ""
    category: str
    status: str
    priority: str
    due_date: Optional[str] = ""
    start_date: Optional[str] = ""
    is_all_day: Optional[bool] = False
    timezone_name: Optional[str] = "UTC"
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = 30
    actual_minutes: Optional[int] = 0
    progress_percent: float = 0.0
    labels: List[str] = []
    sort_order: int = 0
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    user_id: int
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    parent_task_id: Optional[str] = None
    subtask_count: Optional[int] = 0
    completed_subtask_count: Optional[int] = 0
    is_overdue: Optional[bool] = False

    # Frontend camelCase compatibility aliases
    @property
    def dueDate(self) -> Optional[str]:
        return self.due_date

    @property
    def createdAt(self) -> str:
        return self.created_at.isoformat()

    @property
    def updatedAt(self) -> str:
        return self.updated_at.isoformat()

    @property
    def completedAt(self) -> Optional[str]:
        return self.completed_at.isoformat() if self.completed_at else None
