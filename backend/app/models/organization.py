from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    plan = Column(String(32), default="starter", nullable=False)
    logo_url = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(32), default="active", nullable=False)  # active, archived, suspended
    settings_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="organization")

    @property
    def settings(self) -> dict:
        try:
            return json.loads(self.settings_json or "{}")
        except Exception:
            return {}

class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), default="member", nullable=False)  # owner, admin, member, viewer
    title = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        Index("ix_org_member_unique", "organization_id", "user_id", unique=True),
    )

class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(32), default="member", nullable=False)  # admin, member, viewer
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), default="pending", nullable=False)  # pending, accepted, declined, revoked
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    organization = relationship("Organization")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
