from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

class OrganizationCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    plan: Optional[str] = "starter"
    settings: Optional[Dict[str, Any]] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    plan: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    plan: Optional[str] = "starter"
    logo_url: Optional[str] = None
    owner_id: int
    is_active: bool = True
    status: str = "active"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OwnershipTransferRequest(BaseModel):
    new_owner_user_id: int

class OrganizationMemberResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role: str
    title: Optional[str] = None
    joined_at: datetime
    is_active: bool = True
    user: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class OrganizationMemberUpdate(BaseModel):
    role: Optional[str] = None
    title: Optional[str] = None

class OrganizationInvitationCreate(BaseModel):
    email: EmailStr
    role: Optional[str] = "member"

class OrganizationInvitationResponse(BaseModel):
    id: int
    organization_id: int
    email: str
    role: str
    status: str
    invited_by_id: Optional[int] = None
    expires_at: datetime
    created_at: datetime
    invite_token: Optional[str] = None

    class Config:
        from_attributes = True

class AcceptInvitationRequest(BaseModel):
    token: str

class DeclineInvitationRequest(BaseModel):
    token: str

class WorkspaceCreateInOrg(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: Optional[str] = "organization"

class WorkspaceResponseInOrg(BaseModel):
    id: int
    organization_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    visibility: str = "organization"
    owner_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True
