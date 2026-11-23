import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ExternalIntegration(Base):
    __tablename__ = "external_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)  # google_calendar, slack, github, jira, linear, webhook
    status = Column(String(50), default="connected", nullable=False)  # connected, disconnected, error, needs_reauthorization
    external_account_email = Column(String(255), nullable=True)
    connection_metadata = Column(Text, nullable=True)
    config_json = Column(Text, default="{}", nullable=False)
    health_status = Column(String(32), default="HEALTHY", nullable=False)  # HEALTHY, DEGRADED, ERROR
    last_error_message = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
    workspace = relationship("Workspace")
    credentials = relationship("IntegrationCredential", back_populates="integration", cascade="all, delete-orphan", uselist=False)
    sync_mappings = relationship("CalendarSyncMapping", back_populates="integration", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="integration", cascade="all, delete-orphan")
    entity_mappings = relationship("IntegrationEntityMapping", back_populates="integration", cascade="all, delete-orphan")
    sync_jobs = relationship("IntegrationSyncJob", back_populates="integration", cascade="all, delete-orphan")

    @property
    def access_token(self):
        return self.credentials.encrypted_access_token if self.credentials else None

    @property
    def refresh_token(self):
        return self.credentials.encrypted_refresh_token if self.credentials else None

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
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    integration = relationship("ExternalIntegration", back_populates="credentials")

class CalendarSyncMapping(Base):
    __tablename__ = "calendar_sync_mappings"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    external_calendar_id = Column(String(255), default="primary", nullable=False)
    external_event_id = Column(String(255), nullable=False, index=True)
    sync_status = Column(String(50), default="SYNCED", nullable=False)
    last_synced_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    integration = relationship("ExternalIntegration", back_populates="sync_mappings")
    task = relationship("Task")

    __table_args__ = (
        Index("ix_sync_map_unique", "integration_id", "task_id", unique=True),
    )

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    operation = Column(String(100), nullable=False)  # PUSH_TASK, PULL_EVENTS, REMOVE_EVENT, FULL_SYNC
    status = Column(String(50), nullable=False)  # SUCCESS, FAILED
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    integration = relationship("ExternalIntegration", back_populates="sync_logs")

class IntegrationEntityMapping(Base):
    __tablename__ = "integration_entity_mappings"

    id = Column(String(64), primary_key=True, default=lambda: f"iem_{uuid.uuid4().hex[:12]}")
    integration_id = Column(Integer, ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    provider = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)  # task, project, comment, calendar_event, issue
    internal_id = Column(String(64), nullable=False, index=True)
    external_id = Column(String(255), nullable=False, index=True)
    external_url = Column(String(512), nullable=True)
    sync_status = Column(String(32), default="SYNCED", nullable=False)  # SYNCED, PENDING, CONFLICT, ERROR
    metadata_json = Column(Text, default="{}", nullable=False)
    last_synced_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    integration = relationship("ExternalIntegration", back_populates="entity_mappings")

    __table_args__ = (
        Index("ix_iem_provider_internal", "provider", "internal_id"),
        Index("ix_iem_provider_external", "provider", "external_id"),
    )

class IntegrationSyncJob(Base):
    __tablename__ = "integration_sync_jobs"

    id = Column(String(64), primary_key=True, default=lambda: f"sync_{uuid.uuid4().hex[:12]}")
    integration_id = Column(Integer, ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    provider = Column(String(64), nullable=False, index=True)
    sync_type = Column(String(32), default="INCREMENTAL", nullable=False)  # FULL, INCREMENTAL, MANUAL, SCHEDULED
    direction = Column(String(32), default="BIDIRECTIONAL", nullable=False)  # INBOUND, OUTBOUND, BIDIRECTIONAL
    status = Column(String(32), default="COMPLETED", nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    records_synced = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    conflict_resolution = Column(String(32), default="LATEST_UPDATE_WINS", nullable=False)  # INTERNAL_WINS, EXTERNAL_WINS, LATEST_UPDATE_WINS
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    integration = relationship("ExternalIntegration", back_populates="sync_jobs")
