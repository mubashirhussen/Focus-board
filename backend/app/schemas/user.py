from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    username: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = "member"
    timezone: Optional[str] = "UTC"
    locale: Optional[str] = "en"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    role: str = "member"
    is_active: bool = True
    is_verified: bool = False
    status: str = "active"
    timezone: Optional[str] = "UTC"
    locale: Optional[str] = "en"
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
