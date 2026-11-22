from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict

class SearchResultItem(BaseModel):
    id: str
    type: str  # TASK, PROJECT, WORKSPACE
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None
    url_path: str

    model_config = ConfigDict(from_attributes=True)

class SearchFacets(BaseModel):
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}

class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    page: int
    page_size: int
    facets: SearchFacets

    model_config = ConfigDict(from_attributes=True)
