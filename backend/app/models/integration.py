from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class ExternalIntegration(Base):
    __tablename__ = "external_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)  # google_calendar, slack, github
    status = Column(String(50), default="connected", nullable=False)  # connected, disconnected, error
    external_account_email = Column(String(255), nullable=True)
    connection_metadata = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
    credentials = relationship("IntegrationCredential", back_populates="integration", cascade="all, delete-orphan", uselist=False)
    sync_mappings = relationship("CalendarSyncMapping", back_populates="integration", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="integration", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_integrations_user_provider", "user_id", "provider", unique=True),
    )

class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("external_integrations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scopes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    integration = relationship("ExternalIntegration", back_populates="credentials")

class CalendarSyncMapping(Base):
    __tablename__ = "calendar_sync_mappings"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    external_calendar_id = Column(String(255), default="primary", nullable=False)
    external_event_id = Column(String(255), nullable=False, index=True)
    sync_status = Column(String(50), default="SYNCED", nullable=False)
    last_synced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    integration = relationship("ExternalIntegration", back_populates="sync_mappings")
    task = relationship("Task")

    __table_args__ = (
        Index("ix_sync_map_unique", "integration_id", "task_id", unique=True),
    )

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    operation = Column(String(100), nullable=False)  # PUSH_TASK, PULL_EVENTS, REMOVE_EVENT
    status = Column(String(50), nullable=False)  # SUCCESS, FAILED
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    integration = relationship("ExternalIntegration", back_populates="sync_logs")
