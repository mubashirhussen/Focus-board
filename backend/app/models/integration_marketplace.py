import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class IntegrationProvider(Base):
    __tablename__ = "integration_providers"

    id = Column(String(64), primary_key=True)  # e.g. "google_calendar", "slack", "github", "jira", "linear", "ms_teams", "webhook"
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), default="Productivity", nullable=False, index=True)
    # Productivity, Communication, Development, Project Management, Storage, AI, Webhook
    icon = Column(String(64), default="Layers", nullable=False)
    auth_type = Column(String(32), default="OAUTH2", nullable=False)  # OAUTH2, API_KEY, WEBHOOK, BASIC
    supported_features_json = Column(Text, default="[]", nullable=False)
    required_scopes_json = Column(Text, default="[]", nullable=False)
    documentation_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(String(64), primary_key=True, default=lambda: f"mkt_{uuid.uuid4().hex[:12]}")
    title = Column(String(128), nullable=False)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(64), default="Productivity", nullable=False, index=True)
    developer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    developer_name = Column(String(128), default="FocusBoard Official", nullable=False)
    version = Column(String(16), default="1.0.0", nullable=False)
    status = Column(String(32), default="PUBLISHED", nullable=False, index=True)
    # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, PUBLISHED, SUSPENDED, REJECTED
    is_official = Column(Boolean, default=True, nullable=False)
    permissions_json = Column(Text, default='["tasks:read"]', nullable=False)
    install_count = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=4.9, nullable=False)
    icon = Column(String(64), default="Layers", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    developer = relationship("User", foreign_keys=[developer_id])
    installations = relationship("MarketplaceInstallation", back_populates="listing", cascade="all, delete-orphan")

class MarketplaceInstallation(Base):
    __tablename__ = "marketplace_installations"

    id = Column(String(64), primary_key=True, default=lambda: f"inst_{uuid.uuid4().hex[:12]}")
    listing_id = Column(String(64), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    installed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)  # ACTIVE, REVOKED, SUSPENDED
    granted_scopes_json = Column(Text, default='["tasks:read"]', nullable=False)
    installed_at = Column(DateTime, default=utc_now, nullable=False)

    listing = relationship("MarketplaceListing", back_populates="installations")
    workspace = relationship("Workspace")
    installed_by = relationship("User", foreign_keys=[installed_by_id])

    __table_args__ = (
        Index("ix_mkt_install_workspace_listing", "workspace_id", "listing_id", unique=True),
    )

class OAuthConnector(Base):
    __tablename__ = "oauth_connectors"

    id = Column(String(64), primary_key=True, default=lambda: f"conn_{uuid.uuid4().hex[:12]}")
    provider_id = Column(String(64), ForeignKey("integration_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_status = Column(String(32), default="AVAILABLE", nullable=False, index=True)
    # AVAILABLE, CONNECTED, DISCONNECTED, NEEDS_REAUTHORIZATION, ERROR, DISABLED
    account_identifier = Column(String(255), nullable=True)
    granted_scopes_json = Column(Text, default="[]", nullable=False)
    encrypted_token_data = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    provider = relationship("IntegrationProvider")
    workspace = relationship("Workspace")
    user = relationship("User")

    __table_args__ = (
        Index("ix_oauth_conn_provider_workspace", "provider_id", "workspace_id", unique=True),
    )
