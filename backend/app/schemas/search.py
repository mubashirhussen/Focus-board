from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class SearchResultItem(BaseModel):
    id: str
    type: str  # TASK, PROJECT, BOARD, TEAM, WORKSPACE, MEMBER, COMMENT
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    score: Optional[float] = 1.0
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    url_path: str

    model_config = ConfigDict(from_attributes=True)

class SearchFacets(BaseModel):
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}

class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    page: int
    page_size: int
    total_pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    facets: SearchFacets = SearchFacets()

    model_config = ConfigDict(from_attributes=True)

class SearchSuggestionItem(BaseModel):
    id: str
    type: str
    title: str
    subtitle: Optional[str] = None
    url_path: str

    model_config = ConfigDict(from_attributes=True)

class SearchSuggestionsResponse(BaseModel):
    query: str
    suggestions: List[SearchSuggestionItem]
    grouped: Dict[str, List[SearchSuggestionItem]] = {}

class SearchHistoryItemResponse(BaseModel):
    id: int
    query: str
    entity_type: str
    result_count: int
    last_searched_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    entity_type: Optional[str] = "TASK"
    query: Optional[str] = None
    filter_definition: Optional[Dict[str, Any]] = {}
    sorting_config: Optional[Dict[str, Any]] = {}
    is_shared: Optional[bool] = False

class SavedSearchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    query: Optional[str] = None
    filter_definition: Optional[Dict[str, Any]] = None
    sorting_config: Optional[Dict[str, Any]] = None
    is_shared: Optional[bool] = None

class SavedSearchResponse(BaseModel):
    id: int
    user_id: int
    organization_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    entity_type: str
    query: Optional[str] = None
    filter_definition: Dict[str, Any] = {}
    sorting_config: Dict[str, Any] = {}
    is_shared: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AdvancedFilterCondition(BaseModel):
    field: str
    operator: str  # eq, ne, contains, not_contains, starts_with, ends_with, is_empty, is_not_empty, gt, gte, lt, lte, between, in, not_in, before, after
    value: Any = None

class AdvancedFilterRequest(BaseModel):
    entity_type: Optional[str] = "TASK"  # TASK, PROJECT
    conditions: List[AdvancedFilterCondition] = []
    match_type: Optional[str] = "ALL"  # ALL or ANY
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    page: Optional[int] = 1
    page_size: Optional[int] = 20
