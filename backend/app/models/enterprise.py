from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class OrganizationPolicy(Base):
    __tablename__ = "organization_policies"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    policy_type = Column(String(64), nullable=False, index=True)  # mfa_required, domain_restriction, workspace_creation, ai_governance
    policy_value_json = Column(Text, nullable=False, default="{}")
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_org_policy_tenant_type", "tenant_id", "policy_type", unique=True),
    )

class CustomRole(Base):
    __tablename__ = "custom_roles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    permissions_json = Column(Text, nullable=False, default="[]")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_custom_role_tenant_name", "tenant_id", "name", unique=True),
    )

class OrganizationDomain(Base):
    __tablename__ = "organization_domains"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    verification_token = Column(String(64), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_org_domain_unique", "tenant_id", "domain", unique=True),
    )

class EnterpriseInvitation(Base):
    __tablename__ = "enterprise_invitations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(32), default="Member", nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, accepted, revoked
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class UserMFA(Base):
    __tablename__ = "user_mfa"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    secret_hash = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=False, nullable=False)
    recovery_codes_json = Column(Text, nullable=False, default="[]")
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
