from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.user import UserCreate, UserResponse

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    session_id: Optional[str] = None
    user: Optional[UserResponse] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    session_id: Optional[str] = None
    type: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_name: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationResponse(BaseModel):
    message: str
    is_verified: bool = False

class LogoutResponse(BaseModel):
    message: str
    revoked_sessions: int = 0

class UserSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_name: Optional[str] = None
    created_at: datetime
    last_active_at: datetime
    is_current: bool = False

class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
