"""
FocusBoard Module B53: Client & Guest Portal Models.
Provides models for external client/guest accounts, tokenized invitations, granular project sharing,
visibility rules, versioned deliverables, approvals, client comments, feedback, secure documents,
client progress reports, activity logs, and portal settings.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, Float
from sqlalchemy.orm import relationship
from app.db.database import Base


def utc_now() -> datetime:
    """Return offset-naive UTC datetime for SQLite/PostgreSQL compatibility."""
    return datetime.utcnow()


class GuestProfile(Base):
    __tablename__ = "guest_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(120), nullable=True)
    phone = Column(String(50), nullable=True)
    title = Column(String(100), nullable=True)
    guest_type = Column(String(32), default="CLIENT", nullable=False)  # CLIENT, STAKEHOLDER, AUDITOR, CONTRACTOR
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, SUSPENDED, REVOKED
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_access_at = Column(DateTime, nullable=True)
    settings_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization")
    invited_by = relationship("User", foreign_keys=[invited_by_id])

    __table_args__ = (
        Index("ix_guest_profile_org_user", "organization_id", "user_id"),
    )


class GuestInvitation(Base):
    __tablename__ = "guest_invitations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    guest_email = Column(String(255), nullable=False, index=True)
    guest_name = Column(String(100), nullable=False)
    company_name = Column(String(120), nullable=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # PENDING, ACCEPTED, EXPIRED, REVOKED, DECLINED
    role = Column(String(32), default="CLIENT_VIEWER", nullable=False)  # CLIENT_VIEWER, CLIENT_COLLABORATOR, CLIENT_APPROVER, CUSTOM
    permissions_json = Column(Text, default="{}", nullable=False)
    project_ids_json = Column(Text, default="[]", nullable=False)
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    accepted_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    accepted_user = relationship("User", foreign_keys=[accepted_user_id])


class GuestProjectAccess(Base):
    __tablename__ = "guest_project_access"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    guest_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), default="CLIENT_VIEWER", nullable=False)
    permissions_json = Column(Text, default="{}", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    granted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization")
    guest_user = relationship("User", foreign_keys=[guest_user_id])
    project = relationship("Project")
    granted_by = relationship("User", foreign_keys=[granted_by_id])

    __table_args__ = (
        Index("ix_guest_proj_unique", "guest_user_id", "project_id", unique=True),
    )


class ClientProjectVisibility(Base):
    __tablename__ = "client_project_visibility"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    is_shared = Column(Boolean, default=True, nullable=False)
    show_description = Column(Boolean, default=True, nullable=False)
    show_progress = Column(Boolean, default=True, nullable=False)
    progress_mode = Column(String(32), default="AUTOMATIC", nullable=False)  # AUTOMATIC, MANUAL
    manual_progress_percent = Column(Float, default=0.0, nullable=False)
    show_milestones = Column(Boolean, default=True, nullable=False)
    show_tasks = Column(Boolean, default=True, nullable=False)
    show_deliverables = Column(Boolean, default=True, nullable=False)
    show_documents = Column(Boolean, default=True, nullable=False)
    allow_comments = Column(Boolean, default=True, nullable=False)
    allow_feedback = Column(Boolean, default=True, nullable=False)
    allow_uploads = Column(Boolean, default=False, nullable=False)
    allow_approvals = Column(Boolean, default=True, nullable=False)
    custom_banner_message = Column(Text, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project")
    organization = relationship("Organization")
    updated_by = relationship("User", foreign_keys=[updated_by_id])


class ClientSharedTask(Base):
    __tablename__ = "client_shared_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_title = Column(String(255), nullable=True)
    client_description = Column(Text, nullable=True)
    client_status = Column(String(32), default="IN_PROGRESS", nullable=False)  # PLANNED, IN_PROGRESS, UNDER_REVIEW, COMPLETED
    client_priority = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    due_date = Column(DateTime, nullable=True)
    is_visible = Column(Boolean, default=True, nullable=False)
    allow_client_comments = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    task = relationship("Task")
    project = relationship("Project")


class ClientDeliverable(Base):
    __tablename__ = "client_deliverables"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0, nullable=False)
    file_type = Column(String(64), nullable=True)
    version_number = Column(Integer, default=1, nullable=False)
    status = Column(String(32), default="SUBMITTED", nullable=False, index=True)  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, CHANGES_REQUESTED, WITHDRAWN
    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    submitted_at = Column(DateTime, default=utc_now, nullable=False)
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project")
    task = relationship("Task")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    versions = relationship("ClientDeliverableVersion", back_populates="deliverable", cascade="all, delete-orphan")


class ClientDeliverableVersion(Base):
    __tablename__ = "client_deliverable_versions"

    id = Column(Integer, primary_key=True, index=True)
    deliverable_id = Column(Integer, ForeignKey("client_deliverables.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0, nullable=False)
    changelog = Column(Text, nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    deliverable = relationship("ClientDeliverable", back_populates="versions")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])


class ClientFeedback(Base):
    __tablename__ = "client_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    guest_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(32), default="GENERAL", nullable=False)  # GENERAL, BUG, IMPROVEMENT, QUESTION
    status = Column(String(32), default="NEW", nullable=False, index=True)  # NEW, UNDER_REVIEW, ACCEPTED, REJECTED, RESOLVED
    response_text = Column(Text, nullable=True)
    responded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project")
    guest_user = relationship("User", foreign_keys=[guest_user_id])
    responded_by = relationship("User", foreign_keys=[responded_by_id])


class ClientComment(Base):
    __tablename__ = "client_comments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    deliverable_id = Column(Integer, ForeignKey("client_deliverables.id", ondelete="CASCADE"), nullable=True, index=True)
    feedback_id = Column(Integer, ForeignKey("client_feedbacks.id", ondelete="CASCADE"), nullable=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_client_visible = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project")
    task = relationship("Task")
    deliverable = relationship("ClientDeliverable")
    feedback = relationship("ClientFeedback")
    author = relationship("User", foreign_keys=[author_id])


class ClientDocumentAccess(Base):
    __tablename__ = "client_document_access"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    file_type = Column(String(64), nullable=True)
    is_downloadable = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    shared_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project")
    shared_by = relationship("User", foreign_keys=[shared_by_id])


class ClientReport(Base):
    __tablename__ = "client_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    status_override = Column(String(32), nullable=True)  # ON_TRACK, AT_RISK, DELAYED, COMPLETED
    progress_percent = Column(Float, default=0.0, nullable=False)
    milestones_summary_json = Column(Text, default="[]", nullable=False)
    tasks_summary_json = Column(Text, default="[]", nullable=False)
    deliverables_summary_json = Column(Text, default="[]", nullable=False)
    client_action_items_json = Column(Text, default="[]", nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project")
    created_by = relationship("User", foreign_keys=[created_by_id])


class GuestActivityLog(Base):
    __tablename__ = "guest_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)  # INVITATION_ACCEPTED, PROJECT_VIEWED, DOCUMENT_DOWNLOADED, DELIVERABLE_REVIEWED, COMMENT_POSTED, DELIVERABLE_APPROVED, CHANGES_REQUESTED, ACCESS_REVOKED
    resource_type = Column(String(32), nullable=True)  # PROJECT, TASK, DELIVERABLE, DOCUMENT, FEEDBACK
    resource_id = Column(String(64), nullable=True)
    details_json = Column(Text, default="{}", nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    guest_user = relationship("User", foreign_keys=[guest_user_id])
    project = relationship("Project")


class ClientPortalSettings(Base):
    __tablename__ = "client_portal_settings"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    is_portal_enabled = Column(Boolean, default=True, nullable=False)
    allow_guest_invitations = Column(Boolean, default=True, nullable=False)
    default_role = Column(String(32), default="CLIENT_VIEWER", nullable=False)
    default_token_expiration_days = Column(Integer, default=7, nullable=False)
    allow_guest_comments = Column(Boolean, default=True, nullable=False)
    allow_guest_uploads = Column(Boolean, default=False, nullable=False)
    require_approval_reason = Column(Boolean, default=True, nullable=False)
    custom_portal_title = Column(String(100), default="Client Collaboration Portal", nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization")
