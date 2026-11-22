import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AutomationWorkflow(Base):
    __tablename__ = "automation_workflows"

    id = Column(String(64), primary_key=True, default=lambda: f"wf_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    workflow_type = Column(String(64), default="EVENT_DRIVEN", nullable=False, index=True)
    # EVENT_DRIVEN, SCHEDULED, MANUAL, APPROVAL_CHAIN
    status = Column(String(32), default="DRAFT", nullable=False, index=True)
    # DRAFT, ACTIVE, PAUSED, DISABLED, ARCHIVED
    trigger_type = Column(String(64), default="EVENT", nullable=False)
    # EVENT, SCHEDULE, MANUAL, WEBHOOK
    trigger_config_json = Column(Text, default="{}", nullable=False)
    nodes_json = Column(Text, default="[]", nullable=False)
    edges_json = Column(Text, default="[]", nullable=False)
    variables_json = Column(Text, default="{}", nullable=False)
    execution_settings_json = Column(Text, default='{"max_retries": 3, "timeout_seconds": 60, "error_policy": "STOP"}', nullable=False)
    version = Column(String(16), default="1.0", nullable=False)
    is_template = Column(Boolean, default=False, nullable=False, index=True)
    template_category = Column(String(64), nullable=True, index=True)  # TASK, PROJECT, SUPPORT, KNOWLEDGE, INNOVATION, REPORTING
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_executed_at = Column(DateTime, nullable=True)
    execution_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    versions = relationship("AutomationWorkflowVersion", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("AutomationExecution", back_populates="workflow", cascade="all, delete-orphan")
    schedules = relationship("AutomationSchedule", back_populates="workflow", cascade="all, delete-orphan")

class AutomationWorkflowVersion(Base):
    __tablename__ = "automation_workflow_versions"

    id = Column(String(64), primary_key=True, default=lambda: f"wfver_{uuid.uuid4().hex[:12]}")
    workflow_id = Column(String(64), ForeignKey("automation_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(16), nullable=False)
    nodes_json = Column(Text, nullable=False)
    edges_json = Column(Text, nullable=False)
    change_summary = Column(String(255), default="Incremental workflow update", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    workflow = relationship("AutomationWorkflow", back_populates="versions")

class AutomationExecution(Base):
    __tablename__ = "automation_executions"

    id = Column(String(64), primary_key=True, default=lambda: f"wfexec_{uuid.uuid4().hex[:12]}")
    workflow_id = Column(String(64), ForeignKey("automation_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_version = Column(String(16), default="1.0", nullable=False)
    trigger_event = Column(String(64), default="MANUAL", nullable=False, index=True)
    status = Column(String(32), default="QUEUED", nullable=False, index=True)
    # QUEUED, RUNNING, WAITING, COMPLETED, FAILED, CANCELLED, REQUIRES_APPROVAL
    context_json = Column(Text, default="{}", nullable=False)
    current_node_id = Column(String(64), nullable=True)
    results_json = Column(Text, default="{}", nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    correlation_id = Column(String(128), default=lambda: f"corr_{uuid.uuid4().hex[:12]}", nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("AutomationWorkflow", back_populates="executions")
    actor = relationship("User", foreign_keys=[actor_id])
    logs = relationship("AutomationExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    approvals = relationship("AutomationApproval", back_populates="execution", cascade="all, delete-orphan")

class AutomationExecutionLog(Base):
    __tablename__ = "automation_execution_logs"

    id = Column(String(64), primary_key=True, default=lambda: f"wflog_{uuid.uuid4().hex[:12]}")
    execution_id = Column(String(64), ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String(64), nullable=False)
    node_name = Column(String(128), nullable=False)
    node_type = Column(String(64), nullable=False)
    status = Column(String(32), default="SUCCESS", nullable=False)  # STARTED, SUCCESS, FAILED, SKIPPED, WAITING_APPROVAL
    input_data_json = Column(Text, default="{}", nullable=False)
    output_data_json = Column(Text, default="{}", nullable=False)
    error_details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    execution = relationship("AutomationExecution", back_populates="logs")

class AutomationApproval(Base):
    __tablename__ = "automation_approvals"

    id = Column(String(64), primary_key=True, default=lambda: f"wfappr_{uuid.uuid4().hex[:12]}")
    execution_id = Column(String(64), ForeignKey("automation_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String(64), nullable=False)
    approval_type = Column(String(64), default="TASK_ACTION", nullable=False)
    # TASK_ACTION, DOCUMENT_PUBLISH, FINANCIAL_DISBURSEMENT, INTEGRATION_INVOCATION, SENSITIVE_DATA_CHANGE
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    context_summary = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True)
    # PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED
    assigned_approver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_comments = Column(Text, nullable=True)
    decision_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    execution = relationship("AutomationExecution", back_populates="approvals")
    assigned_approver = relationship("User", foreign_keys=[assigned_approver_id])
    decision_by = relationship("User", foreign_keys=[decision_by_id])

class AutomationSchedule(Base):
    __tablename__ = "automation_schedules"

    id = Column(String(64), primary_key=True, default=lambda: f"wfsch_{uuid.uuid4().hex[:12]}")
    workflow_id = Column(String(64), ForeignKey("automation_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    cron_expression = Column(String(64), nullable=False)  # e.g. "0 9 * * 1-5"
    timezone = Column(String(64), default="UTC", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    workflow = relationship("AutomationWorkflow", back_populates="schedules")
