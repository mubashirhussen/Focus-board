from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ServiceRegistryItem(Base):
    __tablename__ = "service_registry"

    id = Column(String(64), primary_key=True)  # e.g. "api_core", "db_primary", "workers_queue"
    name = Column(String(120), nullable=False)
    category = Column(String(60), nullable=False)  # CORE, DATABASE, AI, INTEGRATION, WORKERS, STORAGE
    health_endpoint = Column(String(255), nullable=True)
    status = Column(String(32), default="OPERATIONAL", nullable=False)  # OPERATIONAL, DEGRADED, DOWN, UNKNOWN, MAINTENANCE
    response_time_ms = Column(Float, default=0.0, nullable=False)
    last_checked_at = Column(DateTime, default=utc_now, nullable=False)
    dependencies_json = Column(Text, default="[]", nullable=False)
    failure_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_service_registry_status", "status"),
        Index("ix_service_registry_category", "category"),
    )

class PlatformAlertRule(Base):
    __tablename__ = "platform_alert_rules"

    id = Column(String(64), primary_key=True)
    name = Column(String(120), nullable=False)
    metric_name = Column(String(100), nullable=False)  # api_latency, error_rate, db_connections, queue_backlog, webhook_failures
    condition_operator = Column(String(20), default="GREATER_THAN", nullable=False)  # GREATER_THAN, LESS_THAN, EQUALS
    threshold_value = Column(Float, nullable=False)
    severity = Column(String(20), default="WARNING", nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    evaluation_interval_seconds = Column(Integer, default=60, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class PlatformAlert(Base):
    __tablename__ = "platform_alerts"

    id = Column(String(64), primary_key=True)
    rule_id = Column(String(64), ForeignKey("platform_alert_rules.id", ondelete="CASCADE"), nullable=True)
    severity = Column(String(20), default="WARNING", nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, ACKNOWLEDGED, RESOLVED, SUPPRESSED
    summary = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    related_service_id = Column(String(64), ForeignKey("service_registry.id", ondelete="SET NULL"), nullable=True)
    triggered_at = Column(DateTime, default=utc_now, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    rule = relationship("PlatformAlertRule")
    service = relationship("ServiceRegistryItem")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])

    __table_args__ = (
        Index("ix_platform_alerts_status", "status"),
        Index("ix_platform_alerts_severity", "severity"),
    )

class PlatformIncident(Base):
    __tablename__ = "platform_incidents"

    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(10), default="SEV3", nullable=False)  # SEV1, SEV2, SEV3, SEV4
    status = Column(String(30), default="DETECTED", nullable=False)  # DETECTED, INVESTIGATING, IDENTIFIED, MITIGATING, RESOLVED, CLOSED
    affected_services_json = Column(Text, default="[]", nullable=False)
    lead_operator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    root_cause = Column(Text, nullable=True)
    mitigation_summary = Column(Text, nullable=True)
    resolution_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    lead_operator = relationship("User", foreign_keys=[lead_operator_id])
    timeline_entries = relationship("IncidentTimelineEntry", back_populates="incident", cascade="all, delete-orphan")
    action_items = relationship("IncidentActionItem", back_populates="incident", cascade="all, delete-orphan")
    post_mortem = relationship("IncidentPostMortem", back_populates="incident", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_platform_incidents_status", "status"),
        Index("ix_platform_incidents_severity", "severity"),
    )

class IncidentTimelineEntry(Base):
    __tablename__ = "incident_timeline_entries"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("platform_incidents.id", ondelete="CASCADE"), nullable=False)
    entry_type = Column(String(50), default="UPDATE", nullable=False)  # STATUS_CHANGE, NOTE, MITIGATION, ALERT_LINK, RESOLUTION
    message = Column(Text, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    incident = relationship("PlatformIncident", back_populates="timeline_entries")
    actor = relationship("User", foreign_keys=[actor_id])

class IncidentActionItem(Base):
    __tablename__ = "incident_action_items"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("platform_incidents.id", ondelete="CASCADE"), nullable=False)
    action_description = Column(Text, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    incident = relationship("PlatformIncident", back_populates="action_items")
    assignee = relationship("User", foreign_keys=[assignee_id])

class IncidentPostMortem(Base):
    __tablename__ = "incident_post_mortems"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("platform_incidents.id", ondelete="CASCADE"), unique=True, nullable=False)
    impact_summary = Column(Text, nullable=False)
    root_cause_analysis = Column(Text, nullable=False)
    lessons_learned = Column(Text, nullable=False)
    preventative_measures = Column(Text, nullable=False)
    published_at = Column(DateTime, default=utc_now, nullable=False)

    incident = relationship("PlatformIncident", back_populates="post_mortem")

class SLODefinition(Base):
    __tablename__ = "slo_definitions"

    id = Column(String(64), primary_key=True)
    service_id = Column(String(64), ForeignKey("service_registry.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    target_percentage = Column(Float, default=99.9, nullable=False)
    measurement_window_days = Column(Integer, default=30, nullable=False)
    current_sli_percentage = Column(Float, default=99.95, nullable=False)
    error_budget_remaining_percent = Column(Float, default=95.0, nullable=False)
    burn_rate = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    service = relationship("ServiceRegistryItem")

class PlatformMaintenanceWindow(Base):
    __tablename__ = "platform_maintenance_windows"

    id = Column(String(64), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="SCHEDULED", nullable=False)  # SCHEDULED, ACTIVE, COMPLETED, CANCELLED
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    affected_services_json = Column(Text, default="[]", nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    created_by = relationship("User", foreign_keys=[created_by_id])
