from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# -------------------------------------------------------------
# User Reference Schema
# -------------------------------------------------------------
class CommentUserSummary(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# -------------------------------------------------------------
# Reaction Schemas
# -------------------------------------------------------------
class CommentReactionCreate(BaseModel):
    reaction_type: str = Field(..., min_length=1, max_length=32)

class CommentReactionResponse(BaseModel):
    id: int
    comment_id: int
    user_id: int
    reaction_type: str
    created_at: datetime
    user: Optional[CommentUserSummary] = None

    model_config = ConfigDict(from_attributes=True)

class CommentReactionSummary(BaseModel):
    reaction_type: str
    count: int
    user_reacted: bool = False

# -------------------------------------------------------------
# Mention Schemas
# -------------------------------------------------------------
class CommentMentionResponse(BaseModel):
    id: int
    comment_id: int
    mentioned_user_id: int
    mentioned_by_user_id: int
    entity_type: str
    entity_id: str
    created_at: datetime
    mentioned_user: Optional[CommentUserSummary] = None

    model_config = ConfigDict(from_attributes=True)

class MentionUserAutocomplete(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    avatar_url: Optional[str] = None
    role: Optional[str] = None

# -------------------------------------------------------------
# Comment Schemas
# -------------------------------------------------------------
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    content_format: Optional[str] = Field("markdown", pattern="^(markdown|plain|rich)$")
    entity_type: Optional[str] = Field("TASK", pattern="^(TASK|PROJECT|BOARD|TEAM|WORKSPACE|ORGANIZATION)$")
    entity_id: Optional[str] = None
    task_id: Optional[str] = None
    project_id: Optional[int] = None
    workspace_id: Optional[int] = None
    parent_comment_id: Optional[int] = None

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

class CommentReplyCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    content_format: Optional[str] = Field("markdown", pattern="^(markdown|plain|rich)$")

class CommentResponse(BaseModel):
    id: int
    organization_id: int
    workspace_id: Optional[int] = None
    entity_type: str
    entity_id: str
    task_id: Optional[str] = None
    project_id: Optional[int] = None
    parent_comment_id: Optional[int] = None
    author_id: int
    content: str
    content_format: str
    is_edited: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    author: Optional[CommentUserSummary] = None
    replies: Optional[List["CommentResponse"]] = []
    mentions: Optional[List[CommentMentionResponse]] = []
    reactions: Optional[List[CommentReactionResponse]] = []

    model_config = ConfigDict(from_attributes=True)

# -------------------------------------------------------------
# Activity Feed Schemas
# -------------------------------------------------------------
class ActivityEventResponse(BaseModel):
    id: int
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    task_id: Optional[str] = None
    actor_id: int
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    parent_entity_id: Optional[str] = None
    target_user_id: Optional[int] = None
    description: str
    metadata_json: Optional[str] = None
    created_at: datetime
    actor: Optional[CommentUserSummary] = None

    model_config = ConfigDict(from_attributes=True)
