"""
Service Desk & SLA Management Models (Module B52).
Persists tickets, categories, SLA policies, breach records, escalation rules, assignments, and conversations.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def utc_now() -> datetime:
    return datetime.utcnow()


class ServiceDeskCategory(Base):
    __tablename__ = "service_desk_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    default_priority = Column(String(20), default="MEDIUM", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    organization = relationship("Organization")
    tickets = relationship("ServiceDeskTicket", back_populates="category_rel")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_service_desk_category_org_name"),
    )


class ServiceDeskSLAPolicy(Base):
    __tablename__ = "service_desk_sla_policies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    first_response_target_minutes = Column(Integer, default=60, nullable=False)  # 1 hour default
    resolution_target_minutes = Column(Integer, default=480, nullable=False)    # 8 hours default
    business_hours_start = Column(String(10), default="09:00", nullable=False)
    business_hours_end = Column(String(10), default="17:00", nullable=False)
    work_days = Column(String(50), default="MON,TUE,WED,THU,FRI", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    applies_to_categories_json = Column(Text, default="[]", nullable=False)
    applies_to_priorities_json = Column(Text, default="[]", nullable=False)
    allow_pause_on_waiting = Column(Boolean, default=True, nullable=False)
    at_risk_threshold_percentage = Column(Float, default=80.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization")
    tickets = relationship("ServiceDeskTicket", back_populates="sla_policy")


class ServiceDeskTicket(Base):
    __tablename__ = "service_desk_tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_number = Column(String(32), unique=True, index=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    subject = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("service_desk_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    category_name = Column(String(64), default="Technical Support", nullable=False, index=True)
    subcategory = Column(String(64), nullable=True)
    priority = Column(String(20), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, URGENT, CRITICAL
    status = Column(String(32), default="NEW", nullable=False, index=True)  # NEW, OPEN, ASSIGNED, IN_PROGRESS, WAITING_FOR_REQUESTER, WAITING_FOR_THIRD_PARTY, ESCALATED, RESOLVED, CLOSED, REOPENED, CANCELLED
    source = Column(String(32), default="PORTAL", nullable=False)  # PORTAL, EMAIL, API, SYSTEM, SLACK
    
    sla_policy_id = Column(Integer, ForeignKey("service_desk_sla_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    sla_policy_version = Column(Integer, default=1, nullable=False)
    first_response_due_at = Column(DateTime, nullable=True)
    resolution_due_at = Column(DateTime, nullable=True)
    first_response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    reopened_at = Column(DateTime, nullable=True)

    sla_response_status = Column(String(20), default="ON_TRACK", nullable=False)  # ON_TRACK, AT_RISK, BREACHED, COMPLETED
    sla_resolution_status = Column(String(20), default="ON_TRACK", nullable=False)  # ON_TRACK, AT_RISK, BREACHED, PAUSED, COMPLETED
    sla_paused_at = Column(DateTime, nullable=True)
    total_sla_pause_minutes = Column(Float, default=0.0, nullable=False)
    resolution_notes = Column(Text, nullable=True)

    related_project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    related_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    tags_json = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    organization = relationship("Organization")
    workspace = relationship("Workspace")
    requester = relationship("User", foreign_keys=[requester_id])
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id])
    assigned_team = relationship("Team", foreign_keys=[assigned_team_id])
    category_rel = relationship("ServiceDeskCategory", back_populates="tickets")
    sla_policy = relationship("ServiceDeskSLAPolicy", back_populates="tickets")
    project = relationship("Project", foreign_keys=[related_project_id])
    task = relationship("Task", foreign_keys=[related_task_id])

    comments = relationship("ServiceDeskComment", back_populates="ticket", cascade="all, delete-orphan", order_by="ServiceDeskComment.created_at")
    attachments = relationship("ServiceDeskAttachment", back_populates="ticket", cascade="all, delete-orphan")
    assignment_history = relationship("ServiceDeskAssignmentHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="ServiceDeskAssignmentHistory.created_at")
    activity_logs = relationship("ServiceDeskActivityLog", back_populates="ticket", cascade="all, delete-orphan", order_by="ServiceDeskActivityLog.created_at")
    escalation_records = relationship("ServiceDeskEscalationRecord", back_populates="ticket", cascade="all, delete-orphan")
    sla_breaches = relationship("ServiceDeskSLABreach", back_populates="ticket", cascade="all, delete-orphan")


class ServiceDeskComment(Base):
    __tablename__ = "service_desk_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("service_desk_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_internal_note = Column(Boolean, default=False, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    ticket = relationship("ServiceDeskTicket", back_populates="comments")
    author = relationship("User")


class ServiceDeskAttachment(Base):
    __tablename__ = "service_desk_attachments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("service_desk_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    content_type = Column(String(100), default="application/octet-stream", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    ticket = relationship("ServiceDeskTicket", back_populates="attachments")
    uploader = relationship("User")


class ServiceDeskAssignmentHistory(Base):
    __tablename__ = "service_desk_assignment_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("service_desk_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    previous_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    new_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    previous_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    new_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    ticket = relationship("ServiceDeskTicket", back_populates="assignment_history")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    previous_agent = relationship("User", foreign_keys=[previous_agent_id])
    new_agent = relationship("User", foreign_keys=[new_agent_id])
    previous_team = relationship("Team", foreign_keys=[previous_team_id])
    new_team = relationship("Team", foreign_keys=[new_team_id])


class ServiceDeskActivityLog(Base):
    __tablename__ = "service_desk_activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("service_desk_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(64), nullable=False)  # CREATED, STATUS_CHANGED, PRIORITY_CHANGED, ASSIGNED, ESCALATED, RESOLVED, REOPENED, COMMENTED
    previous_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    ticket = relationship("ServiceDeskTicket", back_populates="activity_logs")
    user = relationship("User")


class ServiceDeskEscalationRule(Base):
    __tablename__ = "service_desk_escalation_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    trigger_type = Column(String(32), default="SLA_BREACH", nullable=False)  # SLA_BREACH, SLA_AT_RISK, TIME_ELAPSED, PRIORITY_HIGH
    threshold_minutes = Column(Integer, default=60, nullable=False)
    target_action = Column(String(32), default="NOTIFY_ADMIN", nullable=False)  # NOTIFY_ADMIN, REASSIGN_TEAM, BUMP_PRIORITY
    target_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    target_priority = Column(String(20), nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    organization = relationship("Organization")
    target_agent = relationship("User", foreign_keys=[target_agent_id])
    target_team = relationship("Team", foreign_keys=[target_team_id])


class ServiceDeskEscalationRecord(Base):
    __tablename__ = "service_desk_escalation_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("service_desk_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("service_desk_escalation_rules.id", ondelete="SET NULL"), nullable=True)
    triggered_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_taken = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    ticket = relationship("ServiceDeskTicket", back_populates="escalation_records")
    rule = relationship("ServiceDeskEscalationRule")
    triggered_by = relationship("User")


class ServiceDeskSLABreach(Base):
    __tablename__ = "service_desk_sla_breaches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("service_desk_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("service_desk_sla_policies.id", ondelete="SET NULL"), nullable=True)
    breach_type = Column(String(32), nullable=False)  # FIRST_RESPONSE, RESOLUTION
    target_deadline = Column(DateTime, nullable=False)
    breached_at = Column(DateTime, default=utc_now, nullable=False)
    minutes_overdue = Column(Float, default=0.0, nullable=False)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    ticket = relationship("ServiceDeskTicket", back_populates="sla_breaches")
    policy = relationship("ServiceDeskSLAPolicy")
