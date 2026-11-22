import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class AIAgent(Base):
    __tablename__ = "ai_agents"

    id = Column(String(64), primary_key=True)  # e.g. agent-task-planner
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    agent_type = Column(String(64), nullable=False, index=True)  # TASK_PLANNER, TASK_BREAKDOWN, etc.
    model_name = Column(String(64), default="focusboard-agent-v1", nullable=False)
    system_prompt = Column(Text, nullable=False)
    tools_json = Column(Text, default="[]", nullable=False)  # JSON list of allowed tools
    is_system = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    executions = relationship("AIAgentExecution", back_populates="agent", cascade="all, delete-orphan")

class AIAgentExecution(Base):
    __tablename__ = "ai_agent_executions"

    id = Column(String(64), primary_key=True, default=lambda: f"exec_{uuid.uuid4().hex[:12]}")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(String(64), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String(32), default="PLANNING", nullable=False, index=True)
    # DRAFT, PLANNING, AWAITING_APPROVAL, APPROVED, RUNNING, COMPLETED, FAILED, CANCELLED
    plan_json = Column(Text, default="[]", nullable=False)
    current_step_index = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    cost_estimate_cents = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    agent = relationship("AIAgent", back_populates="executions")
    user = relationship("User")
    steps = relationship("AIAgentExecutionStep", back_populates="execution", cascade="all, delete-orphan", order_by="AIAgentExecutionStep.step_index")
    approvals = relationship("AIAgentApproval", back_populates="execution", cascade="all, delete-orphan")

class AIAgentExecutionStep(Base):
    __tablename__ = "ai_agent_execution_steps"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(64), ForeignKey("ai_agent_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    tool_name = Column(String(64), nullable=False)
    arguments_json = Column(Text, default="{}", nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)
    # PENDING, AWAITING_APPROVAL, APPROVED, RUNNING, COMPLETED, FAILED, SKIPPED
    result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    execution = relationship("AIAgentExecution", back_populates="steps")

class AIAgentApproval(Base):
    __tablename__ = "ai_agent_approvals"

    id = Column(String(64), primary_key=True, default=lambda: f"appr_{uuid.uuid4().hex[:12]}")
    execution_id = Column(String(64), ForeignKey("ai_agent_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(Integer, ForeignKey("ai_agent_execution_steps.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # DELETE_TASK, BULK_UPDATE, EXTERNAL_ACTION, PERMISSIONS_CHANGE
    reason = Column(Text, nullable=False)
    target_resource = Column(String(255), nullable=False)
    proposed_payload_json = Column(Text, default="{}", nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    execution = relationship("AIAgentExecution", back_populates="approvals")
    user = relationship("User")

class AIPersistentPreference(Base):
    __tablename__ = "ai_persistent_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    planning_style = Column(String(32), default="balanced", nullable=False)  # balanced, aggressive, relaxed, deep_work
    preferred_work_hours = Column(Integer, default=6, nullable=False)
    summary_format = Column(String(32), default="bullet_points", nullable=False)  # bullet_points, narrative, actionable_checklist
    prioritization_approach = Column(String(32), default="deadline_first", nullable=False)  # deadline_first, impact_first, quick_wins
    personalization_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
