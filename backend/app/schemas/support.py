from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# Support Ticket
class SupportTicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    category: Optional[str] = "technical_issue"
    priority: Optional[str] = "NORMAL"
    workspace_id: Optional[int] = None

class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None

class SupportMessageCreate(BaseModel):
    message: str = Field(..., min_length=1)
    is_internal_note: Optional[bool] = False

class SupportMessageResponse(BaseModel):
    id: int
    ticket_id: str
    sender_id: int
    sender_name: Optional[str] = None
    is_internal_note: bool
    message: str
    created_at: datetime

class SupportTicketResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    requester_id: int
    requester_email: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    assigned_agent_name: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    messages_count: int = 0

# Knowledge Base
class KnowledgeBaseCategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    display_order: int
    article_count: int = 0

class KnowledgeBaseArticleCreate(BaseModel):
    category_id: int
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=10)
    status: Optional[str] = "PUBLISHED"

class KnowledgeBaseArticleResponse(BaseModel):
    id: int
    category_id: int
    title: str
    slug: str
    content: str
    status: str
    helpful_count: int
    not_helpful_count: int
    created_at: datetime

class ArticleVoteRequest(BaseModel):
    helpful: bool

# Roadmap
class RoadmapItemCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    status: Optional[str] = "PLANNED"
    category: Optional[str] = "Productivity"

class RoadmapItemResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    category: str
    vote_count: int
    created_at: datetime

# Customer Health Score
class CustomerHealthResponse(BaseModel):
    health_status: str # "HEALTHY", "NEEDS_ATTENTION", "AT_RISK"
    health_score: int # 0-100
    metrics: dict
    recommendations: List[str]
