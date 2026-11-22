"""
FocusBoard Project Service (Phase B4).
Encapsulates business logic, RBAC, tenant isolation, dynamic progress computation,
lifecycle transitions, duplication, dependencies, templates, and dashboard metrics.
"""

from datetime import datetime, timezone
import json
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc

from app.core.logging import logger
from app.models.collaboration import Workspace, WorkspaceMember, Activity
from app.models.organization import OrganizationMember
from app.models.project import Project, ProjectMember, ProjectTemplate, ProjectDependency
from app.models.task import Task
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
    ProjectDependencyCreate,
    ProjectDuplicateRequest,
)

VALID_STATUSES = {"PLANNING", "ACTIVE", "ON_HOLD", "COMPLETED", "CANCELLED", "ARCHIVED"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_HEALTHS = {"ON_TRACK", "AT_RISK", "OFF_TRACK", "BLOCKED"}
VALID_VISIBILITIES = {"WORKSPACE", "PRIVATE", "RESTRICTED"}
VALID_DEPENDENCY_TYPES = {"FINISH_TO_START", "START_TO_START", "FINISH_TO_FINISH", "START_TO_FINISH"}


def _slugify(text: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "project"


class ProjectService:

    @staticmethod
    def _verify_workspace_membership(
        db: Session, workspace_id: int, user_id: int, min_role: Optional[str] = None
    ) -> Tuple[Workspace, Optional[WorkspaceMember]]:
        """Verifies workspace exists and caller has authorized membership."""
        ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.is_active == True).first()
        if not ws:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")

        # Workspace owner has full access
        if ws.owner_id == user_id:
            return ws, None

        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        ).first()

        # Check organization-level owner/admin fallback
        if ws.organization_id:
            org_mem = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == ws.organization_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_active == True,
            ).first()
            if org_mem and org_mem.role.lower() in ["owner", "admin"]:
                return ws, member

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not an active member of this workspace.",
            )

        if min_role:
            role_hierarchy = {"member": 1, "admin": 2, "owner": 3}
            user_level = role_hierarchy.get(member.role.lower(), 1)
            required_level = role_hierarchy.get(min_role.lower(), 1)
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Action requires workspace role '{min_role}' or higher.",
                )

        return ws, member

    @classmethod
    def get_project_or_404(
        cls, db: Session, project_id: int, user_id: int, require_manage: bool = False
    ) -> Project:
        """Retrieves project and enforces multi-tenant boundary and visibility rules."""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.is_deleted == False,
        ).first()

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        # Verify workspace membership
        ws, ws_member = cls._verify_workspace_membership(db, project.workspace_id, user_id)

        # Check project-level membership
        proj_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.status == "ACTIVE",
        ).first()

        is_owner = (project.owner_id == user_id) or (project.created_by == user_id) or (ws.owner_id == user_id)
        is_ws_admin = ws_member and ws_member.role.lower() in ["admin", "owner"]
        is_proj_admin = proj_member and proj_member.role.upper() == "PROJECT_ADMIN"

        # Visibility restrictions
        if project.visibility.upper() in ["PRIVATE", "RESTRICTED"]:
            if not (is_owner or is_ws_admin or proj_member):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: This project is private or restricted.",
                )

        if require_manage and not (is_owner or is_ws_admin or is_proj_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to modify or manage this project.",
            )

        return project

    @staticmethod
    def _log_project_activity(
        db: Session, workspace_id: int, actor_id: int, event_type: str, description: str, project_id: int
    ):
        """Records audit event in activity log."""
        try:
            act = Activity(
                workspace_id=workspace_id,
                project_id=project_id,
                actor_id=actor_id,
                event_type=event_type,
                description=description,
                created_at=datetime.utcnow(),
            )
            db.add(act)
            db.commit()
        except Exception as exc:
            logger.error("Failed to log activity: %s", exc)
            db.rollback()

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    @classmethod
    def create_project(cls, db: Session, user: User, proj_in: ProjectCreate) -> Project:
        """Creates a new project within a workspace and establishes ownership."""
        ws, _ = cls._verify_workspace_membership(db, proj_in.workspace_id, user.id)

        status_val = (proj_in.status or "ACTIVE").upper()
        if status_val not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status '{proj_in.status}'.")

        priority_val = (proj_in.priority or "MEDIUM").upper()
        if priority_val not in VALID_PRIORITIES:
            raise HTTPException(status_code=400, detail=f"Invalid priority '{proj_in.priority}'.")

        health_val = (proj_in.health or "ON_TRACK").upper()
        if health_val not in VALID_HEALTHS:
            raise HTTPException(status_code=400, detail=f"Invalid health '{proj_in.health}'.")

        visibility_val = (proj_in.visibility or "WORKSPACE").upper()
        if visibility_val not in VALID_VISIBILITIES:
            raise HTTPException(status_code=400, detail=f"Invalid visibility '{proj_in.visibility}'.")

        # Date validation
        if proj_in.start_date and proj_in.due_date and proj_in.start_date > proj_in.due_date:
            raise HTTPException(status_code=400, detail="start_date cannot be later than due_date.")

        # Slug generation
        base_slug = proj_in.slug or _slugify(proj_in.name)
        slug = base_slug
        idx = 1
        while db.query(Project).filter(Project.workspace_id == ws.id, Project.slug == slug).first():
            slug = f"{base_slug}-{idx}"
            idx += 1

        owner_id = proj_in.owner_id or user.id
        # Verify owner exists
        target_owner = db.query(User).filter(User.id == owner_id, User.is_active == True).first()
        if not target_owner:
            raise HTTPException(status_code=400, detail="Assigned project owner not found or inactive.")

        project = Project(
            organization_id=ws.organization_id,
            workspace_id=ws.id,
            name=proj_in.name.strip(),
            slug=slug,
            description=proj_in.description or "",
            created_by=user.id,
            owner_id=owner_id,
            status=status_val,
            health=health_val,
            priority=priority_val,
            visibility=visibility_val,
            start_date=proj_in.start_date,
            due_date=proj_in.due_date,
            deadline=proj_in.deadline or (proj_in.due_date.isoformat() if proj_in.due_date else None),
            color=proj_in.color or "#4F46E5",
            icon=proj_in.icon or "folder",
            category=proj_in.category or "General",
            tags_json=json.dumps(proj_in.tags or []),
            settings_json=json.dumps(proj_in.settings or {}),
            is_archived=False,
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(project)
        db.flush()

        # Add creator as PROJECT_ADMIN
        admin_member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role="PROJECT_ADMIN",
            status="ACTIVE",
            joined_at=datetime.utcnow(),
        )
        db.add(admin_member)

        # If owner is different, also add owner as PROJECT_ADMIN
        if owner_id != user.id:
            owner_member = ProjectMember(
                project_id=project.id,
                user_id=owner_id,
                role="PROJECT_ADMIN",
                status="ACTIVE",
                joined_at=datetime.utcnow(),
            )
            db.add(owner_member)

        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, ws.id, user.id, "PROJECT_CREATED", f"Project '{project.name}' was created.", project.id
        )
        return project

    @classmethod
    def list_projects(
        cls,
        db: Session,
        user: User,
        workspace_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        health_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        owner_id: Optional[int] = None,
        member_id: Optional[int] = None,
        include_archived: bool = False,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 50,
    ) -> List[Project]:
        """Lists tenant-isolated projects matching filters, pagination, and sorting."""
        # Find all workspaces the user has access to
        memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).all()
        user_workspace_ids = {m.workspace_id for m in memberships}

        # Include workspaces owned by the user
        owned_workspaces = db.query(Workspace.id).filter(Workspace.owner_id == user.id, Workspace.is_active == True).all()
        user_workspace_ids.update(w[0] for w in owned_workspaces)

        # Include org admin workspaces
        user_org_memberships = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.role.in_(["owner", "admin"]),
            OrganizationMember.is_active == True,
        ).all()
        user_org_ids = [m.organization_id for m in user_org_memberships]
        if user_org_ids:
            org_workspaces = db.query(Workspace.id).filter(
                Workspace.organization_id.in_(user_org_ids),
                Workspace.is_active == True,
            ).all()
            user_workspace_ids.update(w[0] for w in org_workspaces)

        if not user_workspace_ids:
            return []

        query = db.query(Project).filter(
            Project.is_deleted == False,
            Project.workspace_id.in_(list(user_workspace_ids)),
        )

        if workspace_id:
            if workspace_id not in user_workspace_ids:
                raise HTTPException(status_code=403, detail="Access denied to requested workspace.")
            query = query.filter(Project.workspace_id == workspace_id)

        if organization_id:
            query = query.filter(Project.organization_id == organization_id)

        if not include_archived:
            query = query.filter(Project.is_archived == False)

        if status_filter:
            query = query.filter(Project.status == status_filter.upper())

        if health_filter:
            query = query.filter(Project.health == health_filter.upper())

        if priority_filter:
            query = query.filter(Project.priority == priority_filter.upper())

        if category:
            query = query.filter(func.lower(Project.category) == category.lower().strip())

        if owner_id:
            query = query.filter(Project.owner_id == owner_id)

        if tag:
            query = query.filter(Project.tags_json.like(f"%{tag}%"))

        if member_id:
            query = query.join(ProjectMember, ProjectMember.project_id == Project.id).filter(
                ProjectMember.user_id == member_id,
                ProjectMember.status == "ACTIVE",
            )

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                    Project.category.ilike(search_term),
                    Project.tags_json.ilike(search_term),
                )
            )

        # Safe sorting mapping
        sort_columns = {
            "name": Project.name,
            "created_at": Project.created_at,
            "updated_at": Project.updated_at,
            "start_date": Project.start_date,
            "due_date": Project.due_date,
            "priority": Project.priority,
            "status": Project.status,
            "health": Project.health,
        }
        col = sort_columns.get(sort_by, Project.created_at)
        direction = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(direction(col))

        projects = query.offset(skip).limit(limit).all()
        return projects

    @classmethod
    def update_project(
        cls, db: Session, project_id: int, user: User, proj_in: ProjectUpdate
    ) -> Project:
        """Updates project metadata, enforcing validation and logging activity."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)

        if proj_in.name is not None:
            project.name = proj_in.name.strip()
        if proj_in.description is not None:
            project.description = proj_in.description
        if proj_in.slug is not None:
            project.slug = proj_in.slug.strip()
        if proj_in.color is not None:
            project.color = proj_in.color
        if proj_in.icon is not None:
            project.icon = proj_in.icon
        if proj_in.category is not None:
            project.category = proj_in.category.strip()
        if proj_in.deadline is not None:
            project.deadline = proj_in.deadline

        if proj_in.status is not None:
            s_val = proj_in.status.upper()
            if s_val not in VALID_STATUSES:
                raise HTTPException(status_code=400, detail=f"Invalid status '{proj_in.status}'.")
            project.status = s_val

        if proj_in.priority is not None:
            p_val = proj_in.priority.upper()
            if p_val not in VALID_PRIORITIES:
                raise HTTPException(status_code=400, detail=f"Invalid priority '{proj_in.priority}'.")
            project.priority = p_val

        if proj_in.health is not None:
            h_val = proj_in.health.upper()
            if h_val not in VALID_HEALTHS:
                raise HTTPException(status_code=400, detail=f"Invalid health '{proj_in.health}'.")
            project.health = h_val

        if proj_in.visibility is not None:
            v_val = proj_in.visibility.upper()
            if v_val not in VALID_VISIBILITIES:
                raise HTTPException(status_code=400, detail=f"Invalid visibility '{proj_in.visibility}'.")
            project.visibility = v_val

        if proj_in.start_date is not None:
            project.start_date = proj_in.start_date
        if proj_in.due_date is not None:
            project.due_date = proj_in.due_date
        if project.start_date and project.due_date and project.start_date > project.due_date:
            raise HTTPException(status_code=400, detail="start_date cannot be later than due_date.")

        if proj_in.tags is not None:
            project.tags_json = json.dumps(proj_in.tags)
        if proj_in.settings is not None:
            project.settings_json = json.dumps(proj_in.settings)

        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_UPDATED", f"Project '{project.name}' details were updated.", project.id
        )
        return project

    @classmethod
    def delete_project(cls, db: Session, project_id: int, user: User) -> dict:
        """Executes safe soft-deletion, preserving task integrity."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)

        project.is_deleted = True
        project.deleted_at = datetime.utcnow()
        project.updated_at = datetime.utcnow()
        db.commit()

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_DELETED", f"Project '{project.name}' was soft-deleted.", project.id
        )
        return {"message": "Project soft-deleted successfully.", "project_id": project_id}

    # =========================================================================
    # Lifecycle & Status
    # =========================================================================

    @classmethod
    def update_project_status(
        cls, db: Session, project_id: int, user: User, new_status: str
    ) -> Project:
        """Executes lifecycle transition with business rule enforcement."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        status_val = new_status.upper()
        if status_val not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status '{new_status}'.")

        old_status = project.status
        project.status = status_val
        if status_val == "ARCHIVED":
            project.is_archived = True
            project.archived_at = datetime.utcnow()
        elif old_status == "ARCHIVED" and status_val != "ARCHIVED":
            project.is_archived = False
            project.archived_at = None

        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_STATUS_CHANGED",
            f"Project status changed from {old_status} to {status_val}.", project.id
        )
        return project

    @classmethod
    def archive_project(cls, db: Session, project_id: int, user: User) -> Project:
        """Archives project so it disappears from default active listings."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        project.is_archived = True
        project.archived_at = datetime.utcnow()
        project.status = "ARCHIVED"
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_ARCHIVED", f"Project '{project.name}' was archived.", project.id
        )
        return project

    @classmethod
    def restore_project(cls, db: Session, project_id: int, user: User) -> Project:
        """Restores an archived project back to active state."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        project.is_archived = False
        project.archived_at = None
        project.status = "ACTIVE"
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_RESTORED", f"Project '{project.name}' was restored.", project.id
        )
        return project

    # =========================================================================
    # Ownership, Priority, Health, Settings
    # =========================================================================

    @classmethod
    def transfer_ownership(
        cls, db: Session, project_id: int, user: User, new_owner_id: int
    ) -> Project:
        """Transfers primary project ownership to another active member."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        target_user = db.query(User).filter(User.id == new_owner_id, User.is_active == True).first()
        if not target_user:
            raise HTTPException(status_code=400, detail="Target user not found or inactive.")

        # Ensure target user belongs to workspace
        cls._verify_workspace_membership(db, project.workspace_id, new_owner_id)

        project.owner_id = new_owner_id
        project.updated_at = datetime.utcnow()

        # Ensure new owner has PROJECT_ADMIN role in project
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == new_owner_id,
        ).first()
        if member:
            member.role = "PROJECT_ADMIN"
            member.status = "ACTIVE"
        else:
            new_mem = ProjectMember(
                project_id=project_id,
                user_id=new_owner_id,
                role="PROJECT_ADMIN",
                status="ACTIVE",
                joined_at=datetime.utcnow(),
            )
            db.add(new_mem)

        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_OWNER_TRANSFERRED",
            f"Project ownership transferred to {target_user.name}.", project.id
        )
        return project

    @classmethod
    def update_priority(cls, db: Session, project_id: int, user: User, priority: str) -> Project:
        """Updates project priority."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        p_val = priority.upper()
        if p_val not in VALID_PRIORITIES:
            raise HTTPException(status_code=400, detail=f"Invalid priority '{priority}'.")

        project.priority = p_val
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_PRIORITY_CHANGED",
            f"Project priority updated to {p_val}.", project.id
        )
        return project

    @classmethod
    def update_health(cls, db: Session, project_id: int, user: User, health: str) -> Project:
        """Updates project health."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        h_val = health.upper()
        if h_val not in VALID_HEALTHS:
            raise HTTPException(status_code=400, detail=f"Invalid health '{health}'.")

        project.health = h_val
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_HEALTH_CHANGED",
            f"Project health updated to {h_val}.", project.id
        )
        return project

    @classmethod
    def update_settings(cls, db: Session, project_id: int, user: User, settings: Dict[str, Any]) -> Project:
        """Updates project configuration dictionary."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        project.settings_json = json.dumps(settings)
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_SETTINGS_UPDATED",
            "Project settings were updated.", project.id
        )
        return project

    # =========================================================================
    # Dynamic Progress Calculation
    # =========================================================================

    @classmethod
    def calculate_progress(cls, db: Session, project_id: int, user_id: int) -> dict:
        """Computes real completion rate from live project tasks."""
        project = cls.get_project_or_404(db, project_id, user_id)
        tasks = db.query(Task).filter(Task.project_id == project.id).all()

        total = len(tasks)
        completed = 0
        in_progress = 0
        todo = 0

        for t in tasks:
            st = (t.status or "").lower()
            if st in ["completed", "done"]:
                completed += 1
            elif st in ["in progress", "inprogress", "doing"]:
                in_progress += 1
            else:
                todo += 1

        percent = round((completed / total) * 100, 1) if total > 0 else 0.0
        return {
            "project_id": project.id,
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "todo_tasks": todo,
            "progress_percent": percent,
            "status": project.status,
            "health": project.health,
        }

    # =========================================================================
    # Memberships
    # =========================================================================

    @classmethod
    def list_members(cls, db: Session, project_id: int, user_id: int) -> List[dict]:
        """Lists active members of the project."""
        project = cls.get_project_or_404(db, project_id, user_id)
        members = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.status == "ACTIVE",
        ).all()

        result = []
        for m in members:
            u = db.query(User).filter(User.id == m.user_id).first()
            result.append({
                "id": m.id,
                "project_id": m.project_id,
                "user_id": m.user_id,
                "role": m.role,
                "status": m.status,
                "joined_at": m.joined_at,
                "user": {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "display_name": u.display_name,
                    "avatar_url": u.avatar_url,
                } if u else None,
            })
        return result

    @classmethod
    def add_member(
        cls, db: Session, project_id: int, user: User, mem_in: ProjectMemberCreate
    ) -> ProjectMember:
        """Adds a member to the project with designated role."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        # Ensure user belongs to workspace
        cls._verify_workspace_membership(db, project.workspace_id, mem_in.user_id)

        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == mem_in.user_id,
        ).first()

        role_val = (mem_in.role or "PROJECT_MEMBER").upper()
        if role_val not in ["PROJECT_ADMIN", "PROJECT_MEMBER", "PROJECT_VIEWER"]:
            role_val = "PROJECT_MEMBER"

        if existing:
            existing.status = "ACTIVE"
            existing.role = role_val
            existing.updated_at = datetime.utcnow()
            member = existing
        else:
            member = ProjectMember(
                project_id=project.id,
                user_id=mem_in.user_id,
                role=role_val,
                status="ACTIVE",
                joined_at=datetime.utcnow(),
            )
            db.add(member)

        db.commit()
        db.refresh(member)

        target_u = db.query(User).filter(User.id == mem_in.user_id).first()
        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_MEMBER_ADDED",
            f"Added {target_u.name if target_u else 'User'} as {role_val}.", project.id
        )
        return member

    @classmethod
    def update_member_role(
        cls, db: Session, project_id: int, user: User, target_user_id: int, mem_in: ProjectMemberUpdate
    ) -> ProjectMember:
        """Updates a member's project-level role."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == target_user_id,
            ProjectMember.status == "ACTIVE",
        ).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found in project.")

        role_val = mem_in.role.upper()
        if role_val not in ["PROJECT_ADMIN", "PROJECT_MEMBER", "PROJECT_VIEWER"]:
            raise HTTPException(status_code=400, detail="Invalid project role.")

        member.role = role_val
        member.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(member)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_MEMBER_ROLE_UPDATED",
            f"Updated role of member {target_user_id} to {role_val}.", project.id
        )
        return member

    @classmethod
    def remove_member(cls, db: Session, project_id: int, user: User, target_user_id: int) -> dict:
        """Removes a member from the project."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == target_user_id,
            ProjectMember.status == "ACTIVE",
        ).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found in project.")

        if target_user_id == project.owner_id:
            raise HTTPException(status_code=400, detail="Cannot remove the project owner. Transfer ownership first.")

        member.status = "INACTIVE"
        db.commit()

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_MEMBER_REMOVED",
            f"Removed member {target_user_id} from project.", project.id
        )
        return {"message": "Project member removed successfully."}

    # =========================================================================
    # Duplication
    # =========================================================================

    @classmethod
    def duplicate_project(
        cls, db: Session, project_id: int, user: User, req: ProjectDuplicateRequest
    ) -> Project:
        """Duplicates a project with selected options (tasks, settings, tags)."""
        source = cls.get_project_or_404(db, project_id, user.id)
        target_ws_id = req.destination_workspace_id or source.workspace_id

        # Verify access to target workspace
        ws, _ = cls._verify_workspace_membership(db, target_ws_id, user.id)

        copy_name = req.name or f"Copy of {source.name}"
        copy_slug = _slugify(copy_name)
        idx = 1
        while db.query(Project).filter(Project.workspace_id == target_ws_id, Project.slug == copy_slug).first():
            copy_slug = f"{_slugify(copy_name)}-{idx}"
            idx += 1

        new_project = Project(
            organization_id=ws.organization_id,
            workspace_id=target_ws_id,
            name=copy_name,
            slug=copy_slug,
            description=source.description,
            created_by=user.id,
            owner_id=user.id,
            status="PLANNING",
            health="ON_TRACK",
            priority=source.priority,
            visibility=source.visibility,
            start_date=source.start_date,
            due_date=source.due_date,
            deadline=source.deadline,
            color=source.color,
            icon=source.icon,
            category=source.category,
            tags_json=source.tags_json,
            settings_json=source.settings_json if req.duplicate_settings else "{}",
            is_archived=False,
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_project)
        db.flush()

        # Add creator as admin
        creator_mem = ProjectMember(
            project_id=new_project.id,
            user_id=user.id,
            role="PROJECT_ADMIN",
            status="ACTIVE",
            joined_at=datetime.utcnow(),
        )
        db.add(creator_mem)

        # Duplicate members if requested
        if req.duplicate_members:
            source_members = db.query(ProjectMember).filter(
                ProjectMember.project_id == source.id,
                ProjectMember.status == "ACTIVE",
                ProjectMember.user_id != user.id,
            ).all()
            for sm in source_members:
                # Check if member belongs to target workspace
                m_check = db.query(WorkspaceMember).filter(
                    WorkspaceMember.workspace_id == target_ws_id,
                    WorkspaceMember.user_id == sm.user_id,
                ).first()
                if m_check:
                    db.add(ProjectMember(
                        project_id=new_project.id,
                        user_id=sm.user_id,
                        role=sm.role,
                        status="ACTIVE",
                        joined_at=datetime.utcnow(),
                    ))

        # Duplicate tasks if requested
        if req.duplicate_tasks:
            import uuid
            source_tasks = db.query(Task).filter(Task.project_id == source.id).all()
            for st in source_tasks:
                copy_task = Task(
                    id=str(uuid.uuid4()),
                    title=st.title,
                    description=st.description,
                    category=st.category,
                    status="Todo",  # Fresh start
                    priority=st.priority,
                    due_date=st.due_date,
                    estimated_duration_minutes=st.estimated_duration_minutes,
                    user_id=user.id,
                    workspace_id=target_ws_id,
                    project_id=new_project.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(copy_task)

        db.commit()
        db.refresh(new_project)

        cls._log_project_activity(
            db, target_ws_id, user.id, "PROJECT_DUPLICATED",
            f"Duplicated from project '{source.name}' (ID: {source.id}).", new_project.id
        )
        return new_project

    # =========================================================================
    # Dependencies with Cycle Detection
    # =========================================================================

    @classmethod
    def add_dependency(
        cls, db: Session, project_id: int, user: User, dep_in: ProjectDependencyCreate
    ) -> ProjectDependency:
        """Adds a project dependency with self-dependency & cycle prevention."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)

        if project_id == dep_in.depends_on_project_id:
            raise HTTPException(status_code=400, detail="A project cannot depend on itself.")

        depends_on = cls.get_project_or_404(db, dep_in.depends_on_project_id, user.id)

        # Check for existing dependency
        existing = db.query(ProjectDependency).filter(
            ProjectDependency.project_id == project_id,
            ProjectDependency.depends_on_project_id == dep_in.depends_on_project_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="This dependency already exists.")

        # Cycle detection using DFS: check if project_id is reachable from depends_on_project_id
        visited = set()
        queue = [dep_in.depends_on_project_id]
        while queue:
            curr = queue.pop(0)
            if curr == project_id:
                raise HTTPException(
                    status_code=400,
                    detail="Circular dependency detected: adding this dependency would create a cycle.",
                )
            if curr not in visited:
                visited.add(curr)
                # Find all projects that curr depends on
                sub_deps = db.query(ProjectDependency.depends_on_project_id).filter(
                    ProjectDependency.project_id == curr
                ).all()
                for sd in sub_deps:
                    if sd[0] not in visited:
                        queue.append(sd[0])

        dep_type = (dep_in.dependency_type or "FINISH_TO_START").upper()
        if dep_type not in VALID_DEPENDENCY_TYPES:
            dep_type = "FINISH_TO_START"

        dep = ProjectDependency(
            project_id=project_id,
            depends_on_project_id=dep_in.depends_on_project_id,
            dependency_type=dep_type,
            created_at=datetime.utcnow(),
        )
        db.add(dep)
        db.commit()
        db.refresh(dep)

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_DEPENDENCY_ADDED",
            f"Added dependency on '{depends_on.name}' ({dep_type}).", project.id
        )
        return dep

    @classmethod
    def list_dependencies(cls, db: Session, project_id: int, user_id: int) -> List[dict]:
        """Lists all dependencies for a project."""
        project = cls.get_project_or_404(db, project_id, user_id)
        deps = db.query(ProjectDependency).filter(ProjectDependency.project_id == project.id).all()
        result = []
        for d in deps:
            dp = db.query(Project).filter(Project.id == d.depends_on_project_id).first()
            result.append({
                "id": d.id,
                "project_id": d.project_id,
                "depends_on_project_id": d.depends_on_project_id,
                "dependency_type": d.dependency_type,
                "created_at": d.created_at,
                "depends_on_project_name": dp.name if dp else "Unknown Project",
            })
        return result

    @classmethod
    def remove_dependency(cls, db: Session, project_id: int, user: User, dependency_id: int) -> dict:
        """Removes a dependency."""
        project = cls.get_project_or_404(db, project_id, user.id, require_manage=True)
        dep = db.query(ProjectDependency).filter(
            ProjectDependency.id == dependency_id,
            ProjectDependency.project_id == project.id,
        ).first()
        if not dep:
            raise HTTPException(status_code=404, detail="Dependency not found.")

        db.delete(dep)
        db.commit()

        cls._log_project_activity(
            db, project.workspace_id, user.id, "PROJECT_DEPENDENCY_REMOVED",
            f"Removed dependency ID {dependency_id}.", project.id
        )
        return {"message": "Dependency removed successfully."}

    # =========================================================================
    # Templates
    # =========================================================================

    @classmethod
    def create_template(cls, db: Session, user: User, tmpl_in: ProjectTemplateCreate) -> ProjectTemplate:
        """Creates a reusable project template."""
        org_id = None
        if tmpl_in.workspace_id:
            ws, _ = cls._verify_workspace_membership(db, tmpl_in.workspace_id, user.id)
            org_id = ws.organization_id

        tmpl = ProjectTemplate(
            organization_id=org_id,
            workspace_id=tmpl_in.workspace_id,
            created_by_id=user.id,
            name=tmpl_in.name.strip(),
            description=tmpl_in.description or "",
            category=tmpl_in.category or "General",
            default_settings_json=json.dumps(tmpl_in.default_settings or {}),
            default_tasks_json=json.dumps(tmpl_in.default_tasks or []),
            visibility=(tmpl_in.visibility or "ORGANIZATION").upper(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(tmpl)
        db.commit()
        db.refresh(tmpl)
        return tmpl

    @classmethod
    def list_templates(cls, db: Session, user: User) -> List[ProjectTemplate]:
        """Lists accessible templates."""
        return db.query(ProjectTemplate).filter(ProjectTemplate.is_active == True).all()

    @classmethod
    def get_template(cls, db: Session, template_id: int, user: User) -> ProjectTemplate:
        """Gets template details."""
        tmpl = db.query(ProjectTemplate).filter(
            ProjectTemplate.id == template_id,
            ProjectTemplate.is_active == True,
        ).first()
        if not tmpl:
            raise HTTPException(status_code=404, detail="Template not found.")
        return tmpl

    @classmethod
    def update_template(
        cls, db: Session, template_id: int, user: User, tmpl_in: ProjectTemplateUpdate
    ) -> ProjectTemplate:
        """Updates template."""
        tmpl = cls.get_template(db, template_id, user)
        if tmpl_in.name is not None:
            tmpl.name = tmpl_in.name.strip()
        if tmpl_in.description is not None:
            tmpl.description = tmpl_in.description
        if tmpl_in.category is not None:
            tmpl.category = tmpl_in.category
        if tmpl_in.default_settings is not None:
            tmpl.default_settings_json = json.dumps(tmpl_in.default_settings)
        if tmpl_in.default_tasks is not None:
            tmpl.default_tasks_json = json.dumps(tmpl_in.default_tasks)
        if tmpl_in.visibility is not None:
            tmpl.visibility = tmpl_in.visibility.upper()

        tmpl.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tmpl)
        return tmpl

    @classmethod
    def delete_template(cls, db: Session, template_id: int, user: User) -> dict:
        """Soft-deactivates template."""
        tmpl = cls.get_template(db, template_id, user)
        tmpl.is_active = False
        tmpl.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Template deleted successfully."}

    @classmethod
    def instantiate_from_template(
        cls, db: Session, template_id: int, user: User, workspace_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> Project:
        """Creates a real project populated with template default settings and tasks."""
        tmpl = cls.get_template(db, template_id, user)
        ws, _ = cls._verify_workspace_membership(db, workspace_id, user.id)

        proj_name = name or tmpl.name
        proj_create = ProjectCreate(
            workspace_id=workspace_id,
            name=proj_name,
            description=description or tmpl.description,
            category=tmpl.category,
            settings=tmpl.default_settings,
        )
        project = cls.create_project(db, user, proj_create)

        # Create template tasks
        import uuid
        for dt in tmpl.default_tasks:
            t = Task(
                id=str(uuid.uuid4()),
                title=dt.get("title", "New Task"),
                description=dt.get("description", ""),
                category=dt.get("category", "General"),
                status=dt.get("status", "Todo"),
                priority=dt.get("priority", "Medium"),
                due_date=dt.get("due_date"),
                user_id=user.id,
                workspace_id=workspace_id,
                project_id=project.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(t)

        db.commit()
        db.refresh(project)
        return project

    # =========================================================================
    # Summary & Activity
    # =========================================================================

    @classmethod
    def get_project_activity(
        cls, db: Session, project_id: int, user_id: int, limit: int = 50
    ) -> List[dict]:
        """Fetches real activity logs for a project."""
        project = cls.get_project_or_404(db, project_id, user_id)
        activities = db.query(Activity).filter(
            Activity.project_id == project.id,
        ).order_by(Activity.created_at.desc()).limit(limit).all()

        result = []
        for a in activities:
            actor = db.query(User).filter(User.id == a.actor_id).first()
            result.append({
                "id": a.id,
                "workspace_id": a.workspace_id,
                "project_id": a.project_id,
                "actor_id": a.actor_id,
                "event_type": a.event_type,
                "description": a.description,
                "created_at": a.created_at,
                "actor_name": actor.name if actor else "System",
            })
        return result

    @classmethod
    def get_project_summary(cls, db: Session, project_id: int, user_id: int) -> dict:
        """Aggregates metrics for the project dashboard."""
        project = cls.get_project_or_404(db, project_id, user_id)
        progress = cls.calculate_progress(db, project_id, user_id)

        # Count active members
        members_count = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.status == "ACTIVE",
        ).count()

        # Count dependencies
        deps_count = db.query(ProjectDependency).filter(
            ProjectDependency.project_id == project.id,
        ).count()

        # Count overdue tasks
        tasks = db.query(Task).filter(Task.project_id == project.id).all()
        now_dt = datetime.utcnow()
        overdue_count = 0
        for t in tasks:
            if t.status.lower() not in ["completed", "done"] and t.due_date:
                try:
                    d_dt = datetime.fromisoformat(t.due_date.replace("Z", "+00:00")).replace(tzinfo=None)
                    if d_dt < now_dt:
                        overdue_count += 1
                except Exception:
                    pass

        recent_act = cls.get_project_activity(db, project_id, user_id, limit=5)

        return {
            "project_id": project.id,
            "name": project.name,
            "status": project.status,
            "health": project.health,
            "priority": project.priority,
            "progress_percent": progress["progress_percent"],
            "total_tasks": progress["total_tasks"],
            "completed_tasks": progress["completed_tasks"],
            "overdue_tasks": overdue_count,
            "active_members_count": max(members_count, 1),
            "dependencies_count": deps_count,
            "recent_activity": recent_act,
        }
