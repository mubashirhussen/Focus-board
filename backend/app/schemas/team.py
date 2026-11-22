from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# -------------------------------------------------------------
# Team Schemas
# -------------------------------------------------------------

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    visibility: str = Field("ORGANIZATION", pattern="^(ORGANIZATION|WORKSPACE|PRIVATE)$")
    avatar_url: Optional[str] = None

class TeamCreate(TeamBase):
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    slug: Optional[str] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(ORGANIZATION|WORKSPACE|PRIVATE)$")
    workspace_id: Optional[int] = None
    avatar_url: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived|suspended)$")

class TeamSettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class OwnershipTransferRequest(BaseModel):
    new_owner_id: int

class TeamResponse(TeamBase):
    id: int
    organization_id: int
    workspace_id: Optional[int] = None
    slug: str
    owner_id: int
    created_by: Optional[int] = None
    status: str
    is_archived: bool
    archived_at: Optional[datetime] = None
    settings: Dict[str, Any] = {}
    member_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TeamSummaryResponse(BaseModel):
    team_id: int
    team_name: str
    owner_id: int
    total_members: int
    active_members: int
    pending_invitations: int
    active_projects_count: int
    assigned_tasks_count: int
    completed_tasks_count: int
    is_archived: bool

# -------------------------------------------------------------
# Team Member Schemas
# -------------------------------------------------------------

class TeamMemberCreate(BaseModel):
    user_id: int
    role: str = Field("MEMBER", pattern="^(OWNER|ADMIN|MEMBER|VIEWER)$")
    title: Optional[str] = None

class TeamMemberUpdateRole(BaseModel):
    role: str = Field(..., pattern="^(OWNER|ADMIN|MEMBER|VIEWER)$")
    title: Optional[str] = None

class TeamMemberUserSummary(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    avatar_url: Optional[str] = None

class TeamMemberResponse(BaseModel):
    id: int
    team_id: int
    user_id: int
    role: str
    status: str
    title: Optional[str] = None
    joined_at: datetime
    user: Optional[TeamMemberUserSummary] = None

    model_config = ConfigDict(from_attributes=True)

# -------------------------------------------------------------
# Team Invitation Schemas
# -------------------------------------------------------------

class TeamInvitationCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    role: str = Field("MEMBER", pattern="^(ADMIN|MEMBER|VIEWER)$")
    message: Optional[str] = None

class TeamInvitationResponse(BaseModel):
    id: int
    team_id: int
    organization_id: int
    workspace_id: Optional[int] = None
    inviter_id: int
    invitee_email: str
    role: str
    status: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TeamInvitationCreateResult(TeamInvitationResponse):
    token: Optional[str] = None

class InvitationAcceptResponse(BaseModel):
    status: str = "success"
    message: str
    team_id: int
    role: str

class InvitationActionResponse(BaseModel):
    status: str
    message: str
