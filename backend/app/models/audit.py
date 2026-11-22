from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # e.g., AUTH_LOGIN, AUTH_REGISTER, TASK_DELETE, etc.
    resource_type = Column(String(64), nullable=True, index=True)  # USER, TASK, WORKSPACE, PROJECT, etc.
    resource_id = Column(String(64), nullable=True, index=True)
    request_id = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    before_state_json = Column(Text, nullable=True)
    after_state_json = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False, index=True)

    actor = relationship("User", foreign_keys=[actor_id])

    __table_args__ = (
        Index("ix_audit_logs_event_actor", "event_type", "actor_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )
