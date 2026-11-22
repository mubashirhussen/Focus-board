"""
FocusBoard Project Management Schemas (Phase B4).
Provides comprehensive validation and serialization models for projects,
lifecycle transitions, memberships, templates, dependencies, progress, and dashboard metrics.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    slug: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    health: Optional[str] = "ON_TRACK"
    visibility: Optional[str] = "WORKSPACE"
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    deadline: Optional[str] = None
    color: Optional[str] = "#4F46E5"
    icon: Optional[str] = "folder"
    category: Optional[str] = "General"
    tags: Optional[List[str]] = []
    settings: Optional[Dict[str, Any]] = {}

class ProjectCreate(ProjectBase):
    workspace_id: int
    owner_id: Optional[int] = None
    status: Optional[str] = "ACTIVE"

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    health: Optional[str] = None
    visibility: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    deadline: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int] = None
    workspace_id: int
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    created_by: int
    owner_id: Optional[int] = None
    status: str
    health: str
    priority: str
    visibility: str
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    deadline: Optional[str] = None
    color: Optional[str] = "#4F46E5"
    icon: Optional[str] = "folder"
    category: str = "General"
    tags: List[str] = []
    settings: Dict[str, Any] = {}
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    tasks_count: Optional[int] = 0
    completed_tasks_count: Optional[int] = 0
    progress_percent: Optional[float] = 0.0
    owner: Optional[Dict[str, Any]] = None

class ProjectStatusUpdate(BaseModel):
    status: str

class ProjectOwnerUpdate(BaseModel):
    new_owner_id: int

class ProjectPriorityUpdate(BaseModel):
    priority: str

class ProjectHealthUpdate(BaseModel):
    health: str

class ProjectSettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class ProjectMemberCreate(BaseModel):
    user_id: int
    role: Optional[str] = "PROJECT_MEMBER"

class ProjectMemberUpdate(BaseModel):
    role: str

class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    role: str
    status: str
    joined_at: datetime
    user: Optional[Dict[str, Any]] = None

class ProjectProgressResponse(BaseModel):
    project_id: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    todo_tasks: int
    progress_percent: float
    status: str
    health: str

class ProjectTemplateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = "General"
    default_settings: Optional[Dict[str, Any]] = {}
    default_tasks: Optional[List[Dict[str, Any]]] = []
    visibility: Optional[str] = "ORGANIZATION"
    workspace_id: Optional[int] = None

class ProjectTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    default_settings: Optional[Dict[str, Any]] = None
    default_tasks: Optional[List[Dict[str, Any]]] = None
    visibility: Optional[str] = None

class ProjectTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_by_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    category: str
    default_settings: Dict[str, Any] = {}
    default_tasks: List[Dict[str, Any]] = []
    visibility: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ProjectFromTemplateRequest(BaseModel):
    workspace_id: int
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectDuplicateRequest(BaseModel):
    destination_workspace_id: Optional[int] = None
    name: Optional[str] = None
    duplicate_tasks: bool = True
    duplicate_settings: bool = True
    duplicate_members: bool = False

class ProjectDependencyCreate(BaseModel):
    depends_on_project_id: int
    dependency_type: Optional[str] = "FINISH_TO_START"

class ProjectDependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    depends_on_project_id: int
    dependency_type: str
    created_at: datetime
    depends_on_project_name: Optional[str] = None

class ProjectActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    project_id: Optional[int] = None
    actor_id: int
    event_type: str
    description: str
    created_at: datetime
    actor_name: Optional[str] = None

class ProjectSummaryResponse(BaseModel):
    project_id: int
    name: str
    status: str
    health: str
    priority: str
    progress_percent: float
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    active_members_count: int
    dependencies_count: int
    recent_activity: List[ProjectActivityResponse] = []
