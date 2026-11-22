from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str  # task_created, task_completed, task_overdue, calendar_sync_completed
    trigger_config: Dict[str, Any] = {}
    conditions: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    is_active: bool = True

class WorkflowResponse(BaseModel):
    id: int
    tenant_id: str
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any] = {}
    conditions: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    is_active: bool
    execution_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkflowExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    trigger_event: str
    status: str
    result_details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
