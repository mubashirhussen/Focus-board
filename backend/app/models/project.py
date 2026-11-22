"""
FocusBoard Project Management Models (Phase B4).
Includes Project, ProjectMember, ProjectTemplate, and ProjectDependency models
with multi-tenant isolation, lifecycle states, and tenant relationships.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Ownership & Creator
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Lifecycle & Health
    # PLANNING, ACTIVE, ON_HOLD, COMPLETED, CANCELLED, ARCHIVED
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)
    # ON_TRACK, AT_RISK, OFF_TRACK, BLOCKED
    health = Column(String(32), default="ON_TRACK", nullable=False, index=True)
    # LOW, MEDIUM, HIGH, CRITICAL
    priority = Column(String(32), default="MEDIUM", nullable=False, index=True)
    # WORKSPACE, PRIVATE, RESTRICTED
    visibility = Column(String(32), default="WORKSPACE", nullable=False)
    
    # Dates & Metadata
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    deadline = Column(String(50), nullable=True)  # Legacy string deadline support
    color = Column(String(32), default="#4F46E5", nullable=True)
    icon = Column(String(64), default="folder", nullable=True)
    category = Column(String(64), default="General", nullable=False, index=True)
    tags_json = Column(Text, default="[]", nullable=False)
    settings_json = Column(Text, default="{}", nullable=False)
    
    # Archival & Soft Deletion
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    creator = relationship("User", foreign_keys=[created_by])
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", foreign_keys="[Task.project_id]", back_populates="project")
    dependencies = relationship(
        "ProjectDependency",
        foreign_keys="[ProjectDependency.project_id]",
        cascade="all, delete-orphan",
    )

    @property
    def tags(self) -> list:
        try:
            return json.loads(self.tags_json or "[]")
        except Exception:
            return []

    @property
    def settings(self) -> dict:
        try:
            return json.loads(self.settings_json or "{}")
        except Exception:
            return {}


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # PROJECT_ADMIN, PROJECT_MEMBER, PROJECT_VIEWER
    role = Column(String(32), default="PROJECT_MEMBER", nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    joined_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        Index("ix_project_member_unique", "project_id", "user_id", unique=True),
    )


class ProjectTemplate(Base):
    __tablename__ = "project_templates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(64), default="General", nullable=False)
    default_settings_json = Column(Text, default="{}", nullable=False)
    default_tasks_json = Column(Text, default="[]", nullable=False)
    visibility = Column(String(32), default="ORGANIZATION", nullable=False)  # ORGANIZATION, WORKSPACE, PUBLIC
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    creator = relationship("User", foreign_keys=[created_by_id])

    @property
    def default_settings(self) -> dict:
        try:
            return json.loads(self.default_settings_json or "{}")
        except Exception:
            return {}

    @property
    def default_tasks(self) -> list:
        try:
            return json.loads(self.default_tasks_json or "[]")
        except Exception:
            return []


class ProjectDependency(Base):
    __tablename__ = "project_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    # FINISH_TO_START, START_TO_START, FINISH_TO_FINISH, START_TO_FINISH
    dependency_type = Column(String(32), default="FINISH_TO_START", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project", foreign_keys=[project_id], back_populates="dependencies")
    depends_on_project = relationship("Project", foreign_keys=[depends_on_project_id])

    __table_args__ = (
        Index("ix_project_dep_unique", "project_id", "depends_on_project_id", unique=True),
    )
