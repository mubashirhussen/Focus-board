"""
FocusBoard Time Tracking & Timesheets Models (Module B48).
Provides database entities for TimeEntry, ActiveTimer, Timesheet,
TimesheetApproval, TimeTrackingSettings, and TimeEntryAuditLog.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True, index=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    
    billable = Column(Boolean, default=True, nullable=False, index=True)
    hourly_rate = Column(Float, default=0.0, nullable=True)
    billable_amount = Column(Float, default=0.0, nullable=True)
    
    # TIMER, MANUAL
    entry_source = Column(String(32), default="TIMER", nullable=False, index=True)
    # DRAFT, SUBMITTED, APPROVED, REJECTED
    approval_status = Column(String(32), default="DRAFT", nullable=False, index=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys=[project_id])
    task = relationship("Task", foreign_keys=[task_id])
    timesheet = relationship("Timesheet", foreign_keys=[timesheet_id], back_populates="time_entries")


class ActiveTimer(Base):
    __tablename__ = "active_timers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    started_at = Column(DateTime, default=utc_now, nullable=False)
    last_resumed_at = Column(DateTime, default=utc_now, nullable=False)
    accumulated_seconds = Column(Integer, default=0, nullable=False)
    
    # RUNNING, PAUSED
    status = Column(String(32), default="RUNNING", nullable=False, index=True)
    description = Column(Text, nullable=True)
    billable = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys=[project_id])
    task = relationship("Task", foreign_keys=[task_id])


class Timesheet(Base):
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    
    total_seconds = Column(Integer, default=0, nullable=False)
    billable_seconds = Column(Integer, default=0, nullable=False)
    non_billable_seconds = Column(Integer, default=0, nullable=False)
    
    # DRAFT, SUBMITTED, APPROVED, REJECTED, REOPENED
    status = Column(String(32), default="DRAFT", nullable=False, index=True)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    time_entries = relationship("TimeEntry", back_populates="timesheet")
    approvals = relationship("TimesheetApproval", back_populates="timesheet", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_timesheet_user_period", "user_id", "period_start", "period_end"),
    )


class TimesheetApproval(Base):
    __tablename__ = "timesheet_approvals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # APPROVED, REJECTED, REOPENED
    decision = Column(String(32), nullable=False)
    review_comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    timesheet = relationship("Timesheet", back_populates="approvals")
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class TimeTrackingSettings(Base):
    __tablename__ = "time_tracking_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    default_daily_hours = Column(Float, default=8.0, nullable=False)
    default_weekly_hours = Column(Float, default=40.0, nullable=False)
    allow_manual_entry = Column(Boolean, default=True, nullable=False)
    allow_overlapping_entries = Column(Boolean, default=False, nullable=False)
    require_timesheet_approval = Column(Boolean, default=True, nullable=False)
    default_billable = Column(Boolean, default=True, nullable=False)
    default_hourly_rate = Column(Float, default=75.0, nullable=False)
    max_entry_duration_hours = Column(Float, default=24.0, nullable=False)
    submission_deadline_day = Column(String(32), default="MONDAY", nullable=False)
    settings_json = Column(Text, default="{}", nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class TimeEntryAuditLog(Base):
    __tablename__ = "time_entry_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    time_entry_id = Column(Integer, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(64), nullable=False)  # CREATED, UPDATED, DELETED, STATUS_CHANGED
    changes_json = Column(Text, default="{}", nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
