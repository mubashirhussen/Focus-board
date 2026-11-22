from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.task import TaskResponse


# --- Column Schemas ---

class BoardColumnBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    status_value: str = Field(..., min_length=1, max_length=50)
    position: int = 0
    color: str = Field(default="#6366f1", max_length=32)
    description: Optional[str] = None
    wip_limit: Optional[int] = None
    is_visible: bool = True

class BoardColumnCreate(BoardColumnBase):
    pass

class BoardColumnUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status_value: Optional[str] = Field(None, min_length=1, max_length=50)
    position: Optional[int] = None
    color: Optional[str] = None
    description: Optional[str] = None
    wip_limit: Optional[int] = None
    is_visible: Optional[bool] = None

class BoardColumnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    board_id: str
    name: str
    status_value: str
    position: int
    color: str
    description: Optional[str] = None
    wip_limit: Optional[int] = None
    is_visible: bool
    task_count: int = 0
    created_at: datetime
    updated_at: datetime

class BoardColumnReorderItem(BaseModel):
    id: str
    position: int

class BoardColumnReorderRequest(BaseModel):
    items: List[BoardColumnReorderItem]


# --- Board Schemas ---

class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    board_type: str = Field(default="kanban", max_length=50)
    visibility: str = Field(default="workspace", max_length=50)
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    organization_id: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

class BoardCreate(BoardBase):
    initial_columns: Optional[List[BoardColumnCreate]] = None

class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    board_type: Optional[str] = None
    visibility: Optional[str] = None
    is_default: Optional[bool] = None
    is_archived: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class BoardSettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class BoardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    board_type: str
    visibility: str
    owner_id: int
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    organization_id: Optional[int] = None
    settings: Dict[str, Any] = {}
    is_default: bool
    is_archived: bool
    archived_at: Optional[datetime] = None
    columns: List[BoardColumnResponse] = []
    created_at: datetime
    updated_at: datetime

class BoardColumnData(BaseModel):
    column: BoardColumnResponse
    tasks: List[TaskResponse]
    task_count: int

class BoardDataResponse(BaseModel):
    board: BoardResponse
    columns: List[BoardColumnData]
    summary: Dict[str, Any]


# --- Task Movement Between Columns ---

class TaskPositionUpdate(BaseModel):
    destination_column_id: Optional[str] = None
    destination_status: Optional[str] = None
    destination_position: int = 0
    source_column_id: Optional[str] = None

class TaskBulkMoveRequest(BaseModel):
    task_ids: List[str]
    destination_column_id: Optional[str] = None
    destination_status: Optional[str] = None


# --- View Schemas ---

class ViewBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    view_type: str = Field(default="kanban", max_length=50)  # kanban, list, calendar, timeline, table
    visibility: str = Field(default="workspace", max_length=50)
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    board_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    sort_config: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    group_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    column_config: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    is_default: bool = False

class ViewCreate(ViewBase):
    pass

class ViewUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    view_type: Optional[str] = None
    visibility: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    sort_config: Optional[List[Dict[str, Any]]] = None
    group_config: Optional[Dict[str, Any]] = None
    column_config: Optional[List[Dict[str, Any]]] = None
    is_default: Optional[bool] = None

class ViewDuplicateRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=150)
    visibility: Optional[str] = None

class ViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    view_type: str
    visibility: str
    owner_id: int
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    organization_id: Optional[int] = None
    board_id: Optional[str] = None
    filters: Dict[str, Any] = {}
    sort_config: List[Dict[str, Any]] = []
    group_config: Dict[str, Any] = {}
    column_config: List[Dict[str, Any]] = []
    is_default: bool
    created_at: datetime
    updated_at: datetime

class ViewDataResponse(BaseModel):
    view: ViewResponse
    tasks: List[TaskResponse]
    groups: Optional[Dict[str, List[TaskResponse]]] = None
    group_counts: Optional[Dict[str, int]] = None
    total: int


# --- Saved Filter Schemas ---

class SavedFilterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    filter_type: str = Field(default="task", max_length=50)
    query_config: Dict[str, Any] = Field(default_factory=dict)
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    is_shared: bool = False

class SavedFilterCreate(SavedFilterBase):
    pass

class SavedFilterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None
    is_shared: Optional[bool] = None

class SavedFilterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    name: str
    description: Optional[str] = None
    filter_type: str
    query_config: Dict[str, Any] = {}
    is_shared: bool
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class FilterApplyRequest(BaseModel):
    query_config: Optional[Dict[str, Any]] = None
    filter_id: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
