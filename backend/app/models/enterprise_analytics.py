import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(String(64), primary_key=True, default=lambda: f"ms_{uuid.uuid4().hex[:12]}")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(32), default="PENDING", nullable=False, index=True)
    # PENDING, IN_PROGRESS, COMPLETED, DELAYED
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project")

class ProjectRisk(Base):
    __tablename__ = "project_risks"

    id = Column(String(64), primary_key=True, default=lambda: f"risk_{uuid.uuid4().hex[:12]}")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(32), nullable=False, index=True)
    # SCHEDULE, WORKLOAD, DEPENDENCY, EXECUTION
    severity = Column(String(32), default="MEDIUM", nullable=False, index=True)
    # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)
    # ACTIVE, MITIGATED, RESOLVED
    mitigation_plan = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    project = relationship("Project")

class ResourceCapacity(Base):
    __tablename__ = "resource_capacities"

    id = Column(String(64), primary_key=True, default=lambda: f"rc_{uuid.uuid4().hex[:12]}")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    weekly_hours_capacity = Column(Float, default=40.0, nullable=False)
    effective_date = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
    workspace = relationship("Workspace")

class AnalyticsReport(Base):
    __tablename__ = "analytics_reports"

    id = Column(String(64), primary_key=True, default=lambda: f"rep_{uuid.uuid4().hex[:12]}")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(64), nullable=False, index=True)
    # PORTFOLIO_HEALTH, EXECUTIVE_KPI, TEAM_WORKLOAD, RISK_ASSESSMENT
    parameters_json = Column(Text, default="{}", nullable=False)
    summary_json = Column(Text, default="{}", nullable=False)
    format = Column(String(16), default="JSON", nullable=False)
    # JSON, CSV
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User")
    workspace = relationship("Workspace")
