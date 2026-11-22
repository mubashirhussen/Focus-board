from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    category: Optional[str] = "Design"
    status: Optional[str] = "Todo"
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = ""

class TaskCreate(TaskBase):
    id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    description: Optional[str] = ""
    category: str
    status: str
    priority: str
    due_date: Optional[str] = ""
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    user_id: int
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None

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
