"""
FocusBoard Project Management API Routes (Phase B4).
Provides end-to-end REST endpoints for projects, lifecycle, memberships,
dependencies, templates, duplication, progress, and dashboard metrics.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.routes.auth_routes import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectStatusUpdate,
    ProjectOwnerUpdate,
    ProjectPriorityUpdate,
    ProjectHealthUpdate,
    ProjectSettingsUpdate,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse,
    ProjectProgressResponse,
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
    ProjectTemplateResponse,
    ProjectFromTemplateRequest,
    ProjectDuplicateRequest,
    ProjectDependencyCreate,
    ProjectDependencyResponse,
    ProjectActivityResponse,
    ProjectSummaryResponse,
)
from app.services.project_service import ProjectService

router = APIRouter(tags=["Project Management & Lifecycle"])


def _serialize_project(project, db: Session, user_id: int) -> dict:
    """Helper to enrich project with live counts, progress, and owner metadata."""
    progress = ProjectService.calculate_progress(db, project.id, user_id)
    owner = None
    if project.owner:
        owner = {
            "id": project.owner.id,
            "name": project.owner.name,
            "email": project.owner.email,
            "display_name": project.owner.display_name,
            "avatar_url": project.owner.avatar_url,
        }
    return {
        "id": project.id,
        "organization_id": project.organization_id,
        "workspace_id": project.workspace_id,
        "name": project.name,
        "slug": project.slug,
        "description": project.description,
        "created_by": project.created_by,
        "owner_id": project.owner_id,
        "status": project.status,
        "health": project.health,
        "priority": project.priority,
        "visibility": project.visibility,
        "start_date": project.start_date,
        "due_date": project.due_date,
        "deadline": project.deadline,
        "color": project.color,
        "icon": project.icon,
        "category": project.category,
        "tags": project.tags,
        "settings": project.settings,
        "is_archived": project.is_archived,
        "archived_at": project.archived_at,
        "is_deleted": project.is_deleted,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "tasks_count": progress["total_tasks"],
        "completed_tasks_count": progress["completed_tasks"],
        "progress_percent": progress["progress_percent"],
        "owner": owner,
    }


# =========================================================================
# Project CRUD & Search
# =========================================================================

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    proj_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new project within a workspace and designates creator/owner."""
    project = ProjectService.create_project(db, current_user, proj_in)
    return _serialize_project(project, db, current_user.id)


@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    health: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    member_id: Optional[int] = Query(None),
    include_archived: bool = Query(False),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists tenant-isolated projects with multi-criteria filtering and sorting."""
    projects = ProjectService.list_projects(
        db=db,
        user=current_user,
        workspace_id=workspace_id,
        organization_id=organization_id,
        status_filter=status,
        health_filter=health,
        priority_filter=priority,
        category=category,
        tag=tag,
        owner_id=owner_id,
        member_id=member_id,
        include_archived=include_archived,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )
    return [_serialize_project(p, db, current_user.id) for p in projects]


@router.get("/projects/search", response_model=List[ProjectResponse])
def search_projects(
    q: str = Query(..., min_length=1),
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Searches tenant-isolated projects by name, description, tags, or category."""
    projects = ProjectService.list_projects(
        db=db,
        user=current_user,
        workspace_id=workspace_id,
        search=q,
        limit=20,
    )
    return [_serialize_project(p, db, current_user.id) for p in projects]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project_details(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves project details, metadata, and task completion metrics."""
    project = ProjectService.get_project_or_404(db, project_id, current_user.id)
    return _serialize_project(project, db, current_user.id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    proj_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates project details, settings, and metadata."""
    project = ProjectService.update_project(db, project_id, current_user, proj_in)
    return _serialize_project(project, db, current_user.id)


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Safely soft-deletes a project without deleting unrelated task records."""
    return ProjectService.delete_project(db, project_id, current_user)


# =========================================================================
# Archiving & Restoration
# =========================================================================

@router.post("/projects/{project_id}/archive", response_model=ProjectResponse)
def archive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archives project so it disappears from default active project views."""
    project = ProjectService.archive_project(db, project_id, current_user)
    return _serialize_project(project, db, current_user.id)


@router.post("/projects/{project_id}/restore", response_model=ProjectResponse)
def restore_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restores an archived project back to ACTIVE status."""
    project = ProjectService.restore_project(db, project_id, current_user)
    return _serialize_project(project, db, current_user.id)


# =========================================================================
# Status, Ownership, Priority, Health, Settings, Progress
# =========================================================================

@router.patch("/projects/{project_id}/status", response_model=ProjectResponse)
def update_project_status(
    project_id: int,
    status_in: ProjectStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes a lifecycle transition (PLANNING, ACTIVE, ON_HOLD, COMPLETED, CANCELLED, ARCHIVED)."""
    project = ProjectService.update_project_status(db, project_id, current_user, status_in.status)
    return _serialize_project(project, db, current_user.id)


@router.patch("/projects/{project_id}/owner", response_model=ProjectResponse)
def transfer_project_ownership(
    project_id: int,
    owner_in: ProjectOwnerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transfers project ownership to another active member."""
    project = ProjectService.transfer_ownership(db, project_id, current_user, owner_in.new_owner_id)
    return _serialize_project(project, db, current_user.id)


@router.patch("/projects/{project_id}/priority", response_model=ProjectResponse)
def update_project_priority(
    project_id: int,
    priority_in: ProjectPriorityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates project priority level (LOW, MEDIUM, HIGH, CRITICAL)."""
    project = ProjectService.update_priority(db, project_id, current_user, priority_in.priority)
    return _serialize_project(project, db, current_user.id)


@router.patch("/projects/{project_id}/health", response_model=ProjectResponse)
def update_project_health(
    project_id: int,
    health_in: ProjectHealthUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates project health state (ON_TRACK, AT_RISK, OFF_TRACK, BLOCKED)."""
    project = ProjectService.update_health(db, project_id, current_user, health_in.health)
    return _serialize_project(project, db, current_user.id)


@router.get("/projects/{project_id}/settings")
def get_project_settings(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves project configuration dictionary."""
    project = ProjectService.get_project_or_404(db, project_id, current_user.id)
    return project.settings


@router.patch("/projects/{project_id}/settings")
def update_project_settings(
    project_id: int,
    settings_in: ProjectSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates project configuration dictionary."""
    project = ProjectService.update_settings(db, project_id, current_user, settings_in.settings)
    return project.settings


@router.get("/projects/{project_id}/progress", response_model=ProjectProgressResponse)
def get_project_progress(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculates live project task progress, velocity, and completion rates."""
    return ProjectService.calculate_progress(db, project_id, current_user.id)


# =========================================================================
# Memberships
# =========================================================================

@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse])
def get_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists members assigned to the project."""
    return ProjectService.list_members(db, project_id, current_user.id)


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    mem_in: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adds a member to the project with an assigned role."""
    member = ProjectService.add_member(db, project_id, current_user, mem_in)
    u = db.query(User).filter(User.id == member.user_id).first()
    return {
        "id": member.id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": member.role,
        "status": member.status,
        "joined_at": member.joined_at,
        "user": {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
        } if u else None,
    }


@router.patch("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
def update_project_member_role(
    project_id: int,
    user_id: int,
    mem_in: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates a project member's role."""
    member = ProjectService.update_member_role(db, project_id, current_user, user_id, mem_in)
    u = db.query(User).filter(User.id == member.user_id).first()
    return {
        "id": member.id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": member.role,
        "status": member.status,
        "joined_at": member.joined_at,
        "user": {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
        } if u else None,
    }


@router.delete("/projects/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a member from the project."""
    return ProjectService.remove_member(db, project_id, current_user, user_id)


# =========================================================================
# Duplication
# =========================================================================

@router.post("/projects/{project_id}/duplicate", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def duplicate_project(
    project_id: int,
    dup_in: ProjectDuplicateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicates a project with selected components (tasks, settings, labels)."""
    duplicated = ProjectService.duplicate_project(db, project_id, current_user, dup_in)
    return _serialize_project(duplicated, db, current_user.id)


# =========================================================================
# Dependencies
# =========================================================================

@router.post("/projects/{project_id}/dependencies", response_model=ProjectDependencyResponse, status_code=status.HTTP_201_CREATED)
def create_project_dependency(
    project_id: int,
    dep_in: ProjectDependencyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a project dependency with cycle detection and self-dependency prevention."""
    dep = ProjectService.add_dependency(db, project_id, current_user, dep_in)
    dp = db.query(Project).filter(Project.id == dep.depends_on_project_id).first()
    return {
        "id": dep.id,
        "project_id": dep.project_id,
        "depends_on_project_id": dep.depends_on_project_id,
        "dependency_type": dep.dependency_type,
        "created_at": dep.created_at,
        "depends_on_project_name": dp.name if dp else "Unknown Project",
    }


@router.get("/projects/{project_id}/dependencies", response_model=List[ProjectDependencyResponse])
def list_project_dependencies(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all dependencies for a project."""
    return ProjectService.list_dependencies(db, project_id, current_user.id)


@router.delete("/projects/{project_id}/dependencies/{dependency_id}")
def delete_project_dependency(
    project_id: int,
    dependency_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a dependency relationship."""
    return ProjectService.remove_dependency(db, project_id, current_user, dependency_id)


# =========================================================================
# Activity & Dashboard Summary
# =========================================================================

@router.get("/projects/{project_id}/activity", response_model=List[ProjectActivityResponse])
def get_project_activity_feed(
    project_id: int,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the live audit and activity feed for a project."""
    return ProjectService.get_project_activity(db, project_id, current_user.id, limit=limit)


@router.get("/projects/{project_id}/summary", response_model=ProjectSummaryResponse)
def get_project_dashboard_summary(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns aggregated summary metrics for the project dashboard."""
    return ProjectService.get_project_summary(db, project_id, current_user.id)


# =========================================================================
# Project Templates
# =========================================================================

@router.get("/project-templates", response_model=List[ProjectTemplateResponse])
def list_project_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists reusable project templates."""
    templates = ProjectService.list_templates(db, current_user)
    return [
        {
            "id": t.id,
            "organization_id": t.organization_id,
            "workspace_id": t.workspace_id,
            "created_by_id": t.created_by_id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "default_settings": t.default_settings,
            "default_tasks": t.default_tasks,
            "visibility": t.visibility,
            "is_active": t.is_active,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in templates
    ]


@router.post("/project-templates", response_model=ProjectTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_project_template(
    tmpl_in: ProjectTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new project template."""
    tmpl = ProjectService.create_template(db, current_user, tmpl_in)
    return {
        "id": tmpl.id,
        "organization_id": tmpl.organization_id,
        "workspace_id": tmpl.workspace_id,
        "created_by_id": tmpl.created_by_id,
        "name": tmpl.name,
        "description": tmpl.description,
        "category": tmpl.category,
        "default_settings": tmpl.default_settings,
        "default_tasks": tmpl.default_tasks,
        "visibility": tmpl.visibility,
        "is_active": tmpl.is_active,
        "created_at": tmpl.created_at,
        "updated_at": tmpl.updated_at,
    }


@router.get("/project-templates/{template_id}", response_model=ProjectTemplateResponse)
def get_project_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves template details."""
    tmpl = ProjectService.get_template(db, template_id, current_user)
    return {
        "id": tmpl.id,
        "organization_id": tmpl.organization_id,
        "workspace_id": tmpl.workspace_id,
        "created_by_id": tmpl.created_by_id,
        "name": tmpl.name,
        "description": tmpl.description,
        "category": tmpl.category,
        "default_settings": tmpl.default_settings,
        "default_tasks": tmpl.default_tasks,
        "visibility": tmpl.visibility,
        "is_active": tmpl.is_active,
        "created_at": tmpl.created_at,
        "updated_at": tmpl.updated_at,
    }


@router.patch("/project-templates/{template_id}", response_model=ProjectTemplateResponse)
def update_project_template(
    template_id: int,
    tmpl_in: ProjectTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates template details."""
    tmpl = ProjectService.update_template(db, template_id, current_user, tmpl_in)
    return {
        "id": tmpl.id,
        "organization_id": tmpl.organization_id,
        "workspace_id": tmpl.workspace_id,
        "created_by_id": tmpl.created_by_id,
        "name": tmpl.name,
        "description": tmpl.description,
        "category": tmpl.category,
        "default_settings": tmpl.default_settings,
        "default_tasks": tmpl.default_tasks,
        "visibility": tmpl.visibility,
        "is_active": tmpl.is_active,
        "created_at": tmpl.created_at,
        "updated_at": tmpl.updated_at,
    }


@router.delete("/project-templates/{template_id}")
def delete_project_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a project template."""
    return ProjectService.delete_template(db, template_id, current_user)


@router.post("/projects/from-template/{template_id}", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_from_template(
    template_id: int,
    req: ProjectFromTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a real project populated with template default settings and tasks."""
    project = ProjectService.instantiate_from_template(
        db, template_id, current_user, req.workspace_id, req.name, req.description
    )
    return _serialize_project(project, db, current_user.id)
