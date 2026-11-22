from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.schemas.user import UserResponse

class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = ""

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None

class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    role: str
    joined_at: datetime
    user: UserResponse

class WorkspaceResponse(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    members_count: Optional[int] = 1

class InvitationCreate(BaseModel):
    email: EmailStr
    role: Optional[str] = "MEMBER"

class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workspace_id: int
    invitee_email: str
    token: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = ""
    deadline: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[str] = None

class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workspace_id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: str
    author_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    author: Optional[UserResponse] = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workspace_id: int
    project_id: Optional[int] = None
    task_id: Optional[str] = None
    actor_id: int
    event_type: str
    description: str
    created_at: datetime
    actor: Optional[UserResponse] = None

class AssignTaskRequest(BaseModel):
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None

class TeamAnalyticsResponse(BaseModel):
    total_shared_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    active_projects_count: int
    members_count: int
