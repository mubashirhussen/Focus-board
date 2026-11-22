import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(String(64), primary_key=True, default=lambda: f"conv_{uuid.uuid4().hex[:12]}")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    context_type = Column(String(32), default="GENERAL", nullable=False)  # GENERAL, WORKSPACE, PROJECT, TASK
    context_id = Column(String(64), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, ARCHIVED
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
    workspace = relationship("Workspace")
    project = relationship("Project")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.created_at")

class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(String(64), primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    conversation_id = Column(String(64), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    model = Column(String(64), nullable=True)
    provider = Column(String(32), nullable=True)
    tokens_input = Column(Integer, default=0, nullable=False)
    tokens_output = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    task_references_json = Column(Text, default="[]", nullable=False)
    proposed_actions_json = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    conversation = relationship("AIConversation", back_populates="messages")

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(String(64), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    feature = Column(String(64), nullable=False, index=True)  # chat, task_description, task_decompose, task_prioritize, etc.
    provider = Column(String(32), nullable=False)
    model = Column(String(64), nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_cents = Column(Float, default=0.0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="SUCCESS", nullable=False)  # SUCCESS, ERROR, RATE_LIMITED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User")
