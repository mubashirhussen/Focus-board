from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=True, index=True)
    device_name = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    last_active_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

class AuthAuditLog(Base):
    __tablename__ = "auth_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
