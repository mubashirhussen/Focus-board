import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class DeveloperApplication(Base):
    __tablename__ = "developer_applications"

    id = Column(String(64), primary_key=True, default=lambda: f"app_{uuid.uuid4().hex[:12]}")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    app_type = Column(String(32), default="INTERNAL", nullable=False)
    # INTERNAL, PARTNER, PUBLIC
    redirect_uri = Column(String(512), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)
    # DRAFT, ACTIVE, SUSPENDED, REVOKED
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
    workspace = relationship("Workspace")
    credentials = relationship("DeveloperCredential", back_populates="application", cascade="all, delete-orphan")
    webhooks = relationship("WebhookSubscription", back_populates="application", cascade="all, delete-orphan")

class DeveloperCredential(Base):
    __tablename__ = "developer_credentials"

    id = Column(String(64), primary_key=True, default=lambda: f"cred_{uuid.uuid4().hex[:12]}")
    application_id = Column(String(64), ForeignKey("developer_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False, index=True)  # e.g. "fb_live_a1b2"
    hashed_key = Column(String(128), nullable=False, unique=True, index=True)  # SHA-256 hash of plaintext key
    name = Column(String(128), nullable=False)
    scopes_json = Column(Text, default='["tasks:read"]', nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    application = relationship("DeveloperApplication", back_populates="credentials")
    user = relationship("User")

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(String(64), primary_key=True, default=lambda: f"wh_{uuid.uuid4().hex[:12]}")
    application_id = Column(String(64), ForeignKey("developer_applications.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    target_url = Column(String(512), nullable=False)
    secret_key = Column(String(128), nullable=False)  # Secret for HMAC-SHA256 signature
    events_json = Column(Text, default='["task.created","task.updated","task.completed"]', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    last_delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    application = relationship("DeveloperApplication", back_populates="webhooks")
    user = relationship("User")
    workspace = relationship("Workspace")
    deliveries = relationship("WebhookDelivery", back_populates="subscription", cascade="all, delete-orphan")

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(64), primary_key=True, default=lambda: f"deliv_{uuid.uuid4().hex[:12]}")
    subscription_id = Column(String(64), ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    payload_json = Column(Text, nullable=False)
    response_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=1, nullable=False)
    delivered_at = Column(DateTime, default=utc_now, nullable=False)
    is_success = Column(Boolean, default=False, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    subscription = relationship("WebhookSubscription", back_populates="deliveries")

class APIUsageRecord(Base):
    __tablename__ = "api_usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    credential_id = Column(String(64), ForeignKey("developer_credentials.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(16), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(64), primary_key=True, default=lambda: f"idem_{uuid.uuid4().hex[:12]}")
    idempotency_key = Column(String(128), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_code = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
