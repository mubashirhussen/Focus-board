"""
FocusBoard Module B53: Client & Guest Portal Service.
Handles guest invitations, cryptographically secure token hashing, project-level access grants,
visibility rules, versioned deliverables, approvals, client comments, feedback, secure documents,
client-facing reports, and privacy-conscious audit trails.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import json
import secrets
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from app.models.client_portal import (
    GuestProfile,
    GuestInvitation,
    GuestProjectAccess,
    ClientProjectVisibility,
    ClientSharedTask,
    ClientDeliverable,
    ClientDeliverableVersion,
    ClientFeedback,
    ClientComment,
    ClientDocumentAccess,
    ClientReport,
    GuestActivityLog,
    ClientPortalSettings,
)
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.organization import Organization


def utc_now() -> datetime:
    """Return offset-naive UTC datetime for SQLite/PostgreSQL compatibility."""
    return datetime.utcnow()


def to_naive(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# =========================================================================
# 1. SECURITY & TOKEN HELPERS
# =========================================================================

def generate_invitation_token() -> str:
    """Generate cryptographically secure 32-byte URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 hash of invitation token for safe database persistence."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


# Default guest role permissions
ROLE_PERMISSIONS: Dict[str, Dict[str, bool]] = {
    "CLIENT_VIEWER": {
        "can_view_summary": True,
        "can_view_tasks": True,
        "can_view_milestones": True,
        "can_view_documents": True,
        "can_download_files": True,
        "can_comment": False,
        "can_upload_deliverables": False,
        "can_submit_feedback": False,
        "can_approve_deliverables": False,
        "can_view_reports": True,
    },
    "CLIENT_COLLABORATOR": {
        "can_view_summary": True,
        "can_view_tasks": True,
        "can_view_milestones": True,
        "can_view_documents": True,
        "can_download_files": True,
        "can_comment": True,
        "can_upload_deliverables": True,
        "can_submit_feedback": True,
        "can_approve_deliverables": False,
        "can_view_reports": True,
    },
    "CLIENT_APPROVER": {
        "can_view_summary": True,
        "can_view_tasks": True,
        "can_view_milestones": True,
        "can_view_documents": True,
        "can_download_files": True,
        "can_comment": True,
        "can_upload_deliverables": False,
        "can_submit_feedback": True,
        "can_approve_deliverables": True,
        "can_view_reports": True,
    },
    "CUSTOM": {
        "can_view_summary": True,
        "can_view_tasks": True,
        "can_view_milestones": True,
        "can_view_documents": True,
        "can_download_files": True,
        "can_comment": True,
        "can_upload_deliverables": False,
        "can_submit_feedback": True,
        "can_approve_deliverables": False,
        "can_view_reports": True,
    },
}


# =========================================================================
# 2. GUEST INVITATION WORKFLOW
# =========================================================================

def create_guest_invitation(
    db: Session,
    organization_id: int,
    invited_by_id: int,
    guest_email: str,
    guest_name: str,
    company_name: Optional[str] = None,
    role: str = "CLIENT_VIEWER",
    project_ids: Optional[List[int]] = None,
    custom_permissions: Optional[Dict[str, bool]] = None,
    message: Optional[str] = None,
    expiration_days: int = 7,
) -> Dict[str, Any]:
    """Create a single-use tokenized guest invitation."""
    email_clean = guest_email.strip().lower()
    role_clean = role if role in ROLE_PERMISSIONS else "CLIENT_VIEWER"

    perms = dict(ROLE_PERMISSIONS.get(role_clean, ROLE_PERMISSIONS["CLIENT_VIEWER"]))
    if role_clean == "CUSTOM" and custom_permissions:
        perms.update(custom_permissions)

    raw_token = generate_invitation_token()
    token_h = hash_token(raw_token)
    expires_at = utc_now() + timedelta(days=max(1, min(expiration_days, 30)))

    # Revoke any prior pending invitation for same email and organization
    prior_invites = db.query(GuestInvitation).filter(
        GuestInvitation.organization_id == organization_id,
        GuestInvitation.guest_email == email_clean,
        GuestInvitation.status == "PENDING",
    ).all()
    for inv in prior_invites:
        inv.status = "REVOKED"
        inv.revoked_at = utc_now()

    invitation = GuestInvitation(
        organization_id=organization_id,
        invited_by_id=invited_by_id,
        guest_email=email_clean,
        guest_name=guest_name.strip(),
        company_name=company_name.strip() if company_name else None,
        token_hash=token_h,
        status="PENDING",
        role=role_clean,
        permissions_json=json.dumps(perms),
        project_ids_json=json.dumps(project_ids or []),
        message=message,
        expires_at=expires_at,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return {
        "invitation": invitation,
        "raw_token": raw_token,
    }


def accept_guest_invitation(
    db: Session,
    raw_token: str,
    user: User,
) -> Dict[str, Any]:
    """Validate token, accept invitation, link guest profile and grant project access."""
    token_h = hash_token(raw_token)
    invitation = db.query(GuestInvitation).filter(
        GuestInvitation.token_hash == token_h
    ).first()

    if not invitation:
        raise ValueError("Invalid invitation token")

    if invitation.status == "REVOKED":
        raise ValueError("This invitation has been revoked")

    if invitation.status == "ACCEPTED":
        raise ValueError("This invitation has already been accepted")

    if to_naive(invitation.expires_at) < utc_now():
        invitation.status = "EXPIRED"
        db.commit()
        raise ValueError("This invitation has expired")

    # Enforce email match
    if user.email.strip().lower() != invitation.guest_email.strip().lower():
        raise ValueError("The authenticated user email does not match the invitation recipient")

    # Mark invitation accepted
    invitation.status = "ACCEPTED"
    invitation.accepted_at = utc_now()
    invitation.accepted_user_id = user.id

    # Create or update GuestProfile
    profile = db.query(GuestProfile).filter(
        GuestProfile.user_id == user.id,
        GuestProfile.organization_id == invitation.organization_id,
    ).first()

    if not profile:
        profile = GuestProfile(
            user_id=user.id,
            organization_id=invitation.organization_id,
            company_name=invitation.company_name,
            guest_type="CLIENT",
            status="ACTIVE",
            invited_by_id=invitation.invited_by_id,
            last_access_at=utc_now(),
        )
        db.add(profile)
    else:
        profile.status = "ACTIVE"
        profile.last_access_at = utc_now()
        if invitation.company_name:
            profile.company_name = invitation.company_name

    # Grant project access
    try:
        project_ids = json.loads(invitation.project_ids_json or "[]")
    except Exception:
        project_ids = []

    granted_projects = []
    for pid in project_ids:
        # Check if project belongs to organization
        proj = db.query(Project).filter(
            Project.id == pid,
            Project.organization_id == invitation.organization_id,
        ).first()
        if not proj:
            continue

        existing_access = db.query(GuestProjectAccess).filter(
            GuestProjectAccess.guest_user_id == user.id,
            GuestProjectAccess.project_id == pid,
        ).first()

        if existing_access:
            existing_access.is_active = True
            existing_access.role = invitation.role
            existing_access.permissions_json = invitation.permissions_json
            existing_access.updated_at = utc_now()
        else:
            new_access = GuestProjectAccess(
                organization_id=invitation.organization_id,
                guest_user_id=user.id,
                project_id=pid,
                role=invitation.role,
                permissions_json=invitation.permissions_json,
                is_active=True,
                granted_by_id=invitation.invited_by_id,
            )
            db.add(new_access)
        granted_projects.append(pid)

    # Log activity
    log = GuestActivityLog(
        organization_id=invitation.organization_id,
        guest_user_id=user.id,
        action="INVITATION_ACCEPTED",
        resource_type="INVITATION",
        resource_id=str(invitation.id),
        details_json=json.dumps({"granted_projects": granted_projects}),
    )
    db.add(log)

    db.commit()
    return {
        "status": "ACCEPTED",
        "organization_id": invitation.organization_id,
        "granted_projects": granted_projects,
        "role": invitation.role,
    }


def revoke_guest_invitation(
    db: Session,
    invitation_id: int,
    organization_id: int,
    user_id: int,
) -> GuestInvitation:
    """Revoke a pending guest invitation."""
    invitation = db.query(GuestInvitation).filter(
        GuestInvitation.id == invitation_id,
        GuestInvitation.organization_id == organization_id,
    ).first()

    if not invitation:
        raise ValueError("Invitation not found")

    if invitation.status == "ACCEPTED":
        raise ValueError("Cannot revoke an already accepted invitation")

    invitation.status = "REVOKED"
    invitation.revoked_at = utc_now()
    db.commit()
    db.refresh(invitation)
    return invitation


def resend_guest_invitation(
    db: Session,
    invitation_id: int,
    organization_id: int,
    expiration_days: int = 7,
) -> Dict[str, Any]:
    """Regenerate token and reset expiration for an invitation."""
    invitation = db.query(GuestInvitation).filter(
        GuestInvitation.id == invitation_id,
        GuestInvitation.organization_id == organization_id,
    ).first()

    if not invitation:
        raise ValueError("Invitation not found")

    raw_token = generate_invitation_token()
    invitation.token_hash = hash_token(raw_token)
    invitation.status = "PENDING"
    invitation.expires_at = utc_now() + timedelta(days=max(1, min(expiration_days, 30)))
    invitation.updated_at = utc_now()
    db.commit()
    db.refresh(invitation)

    return {
        "invitation": invitation,
        "raw_token": raw_token,
    }


# =========================================================================
# 3. GUEST ACCOUNT LIFECYCLE MANAGEMENT
# =========================================================================

def list_organization_guests(
    db: Session,
    organization_id: int,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List guest profiles in an organization with project access counts."""
    query = db.query(GuestProfile).filter(GuestProfile.organization_id == organization_id)
    if status:
        query = query.filter(GuestProfile.status == status)

    profiles = query.all()
    results = []

    for prof in profiles:
        user = prof.user
        if search:
            s = search.lower()
            name_match = (user.name and s in user.name.lower()) or (user.display_name and s in user.display_name.lower())
            email_match = s in user.email.lower()
            company_match = prof.company_name and s in prof.company_name.lower()
            if not (name_match or email_match or company_match):
                continue

        # Count active projects
        proj_count = db.query(func.count(GuestProjectAccess.id)).filter(
            GuestProjectAccess.guest_user_id == prof.user_id,
            GuestProjectAccess.organization_id == organization_id,
            GuestProjectAccess.is_active == True,
        ).scalar() or 0

        results.append({
            "id": prof.id,
            "user_id": prof.user_id,
            "name": user.full_name,
            "email": user.email,
            "company_name": prof.company_name,
            "title": prof.title,
            "phone": prof.phone,
            "status": prof.status,
            "guest_type": prof.guest_type,
            "last_access_at": prof.last_access_at,
            "created_at": prof.created_at,
            "active_projects_count": proj_count,
        })

    return results


def suspend_guest_access(
    db: Session,
    guest_user_id: int,
    organization_id: int,
    admin_user_id: int,
) -> GuestProfile:
    """Suspend a guest account, instantly disabling all project access."""
    prof = db.query(GuestProfile).filter(
        GuestProfile.user_id == guest_user_id,
        GuestProfile.organization_id == organization_id,
    ).first()
    if not prof:
        raise ValueError("Guest profile not found")

    prof.status = "SUSPENDED"
    prof.updated_at = utc_now()

    # Deactivate all active project grants
    access_grants = db.query(GuestProjectAccess).filter(
        GuestProjectAccess.guest_user_id == guest_user_id,
        GuestProjectAccess.organization_id == organization_id,
    ).all()
    for grant in access_grants:
        grant.is_active = False
        grant.updated_at = utc_now()

    log = GuestActivityLog(
        organization_id=organization_id,
        guest_user_id=guest_user_id,
        action="ACCESS_SUSPENDED",
        details_json=json.dumps({"suspended_by": admin_user_id}),
    )
    db.add(log)
    db.commit()
    db.refresh(prof)
    return prof


def reactivate_guest_access(
    db: Session,
    guest_user_id: int,
    organization_id: int,
    admin_user_id: int,
) -> GuestProfile:
    """Reactivate a suspended guest account and restore project access."""
    prof = db.query(GuestProfile).filter(
        GuestProfile.user_id == guest_user_id,
        GuestProfile.organization_id == organization_id,
    ).first()
    if not prof:
        raise ValueError("Guest profile not found")

    prof.status = "ACTIVE"
    prof.updated_at = utc_now()

    access_grants = db.query(GuestProjectAccess).filter(
        GuestProjectAccess.guest_user_id == guest_user_id,
        GuestProjectAccess.organization_id == organization_id,
    ).all()
    for grant in access_grants:
        grant.is_active = True
        grant.updated_at = utc_now()

    log = GuestActivityLog(
        organization_id=organization_id,
        guest_user_id=guest_user_id,
        action="ACCESS_REACTIVATED",
        details_json=json.dumps({"reactivated_by": admin_user_id}),
    )
    db.add(log)
    db.commit()
    db.refresh(prof)
    return prof


def revoke_guest_from_organization(
    db: Session,
    guest_user_id: int,
    organization_id: int,
    admin_user_id: int,
) -> None:
    """Permanently revoke guest access from the organization and all projects."""
    prof = db.query(GuestProfile).filter(
        GuestProfile.user_id == guest_user_id,
        GuestProfile.organization_id == organization_id,
    ).first()
    if prof:
        prof.status = "REVOKED"
        prof.updated_at = utc_now()

    # Deactivate all project access
    db.query(GuestProjectAccess).filter(
        GuestProjectAccess.guest_user_id == guest_user_id,
        GuestProjectAccess.organization_id == organization_id,
    ).update({"is_active": False, "updated_at": utc_now()})

    log = GuestActivityLog(
        organization_id=organization_id,
        guest_user_id=guest_user_id,
        action="ACCESS_REVOKED",
        details_json=json.dumps({"revoked_by": admin_user_id}),
    )
    db.add(log)
    db.commit()


# =========================================================================
# 4. PROJECT SHARING & GRANULAR VISIBILITY
# =========================================================================

def get_or_create_project_visibility(
    db: Session,
    project_id: int,
    organization_id: int,
) -> ClientProjectVisibility:
    """Get or initialize default client project visibility rules."""
    vis = db.query(ClientProjectVisibility).filter(
        ClientProjectVisibility.project_id == project_id
    ).first()
    if not vis:
        vis = ClientProjectVisibility(
            project_id=project_id,
            organization_id=organization_id,
            is_shared=True,
            show_description=True,
            show_progress=True,
            progress_mode="AUTOMATIC",
            manual_progress_percent=0.0,
            show_milestones=True,
            show_tasks=True,
            show_deliverables=True,
            show_documents=True,
            allow_comments=True,
            allow_feedback=True,
            allow_uploads=False,
            allow_approvals=True,
        )
        db.add(vis)
        db.commit()
        db.refresh(vis)
    return vis


def update_project_visibility(
    db: Session,
    project_id: int,
    organization_id: int,
    updates: Dict[str, Any],
    user_id: int,
) -> ClientProjectVisibility:
    """Update client project visibility settings."""
    vis = get_or_create_project_visibility(db, project_id, organization_id)
    allowed_fields = [
        "is_shared", "show_description", "show_progress", "progress_mode",
        "manual_progress_percent", "show_milestones", "show_tasks",
        "show_deliverables", "show_documents", "allow_comments",
        "allow_feedback", "allow_uploads", "allow_approvals",
        "custom_banner_message"
    ]
    for k, v in updates.items():
        if k in allowed_fields:
            setattr(vis, k, v)
    vis.updated_by_id = user_id
    vis.updated_at = utc_now()
    db.commit()
    db.refresh(vis)
    return vis


def share_project_with_guest(
    db: Session,
    project_id: int,
    organization_id: int,
    guest_user_id: int,
    role: str = "CLIENT_VIEWER",
    custom_permissions: Optional[Dict[str, bool]] = None,
    expires_at: Optional[datetime] = None,
    granted_by_id: Optional[int] = None,
) -> GuestProjectAccess:
    """Explicitly share a project with a guest user."""
    # Ensure project exists in org
    proj = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id,
    ).first()
    if not proj:
        raise ValueError("Project not found in organization")

    # Ensure guest has active profile
    prof = db.query(GuestProfile).filter(
        GuestProfile.user_id == guest_user_id,
        GuestProfile.organization_id == organization_id,
    ).first()
    if not prof or prof.status != "ACTIVE":
        raise ValueError("Guest account is not active or does not exist")

    perms = dict(ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["CLIENT_VIEWER"]))
    if role == "CUSTOM" and custom_permissions:
        perms.update(custom_permissions)

    access = db.query(GuestProjectAccess).filter(
        GuestProjectAccess.guest_user_id == guest_user_id,
        GuestProjectAccess.project_id == project_id,
    ).first()

    if access:
        access.role = role
        access.permissions_json = json.dumps(perms)
        access.is_active = True
        access.expires_at = to_naive(expires_at)
        access.granted_by_id = granted_by_id
        access.updated_at = utc_now()
    else:
        access = GuestProjectAccess(
            organization_id=organization_id,
            guest_user_id=guest_user_id,
            project_id=project_id,
            role=role,
            permissions_json=json.dumps(perms),
            is_active=True,
            expires_at=to_naive(expires_at),
            granted_by_id=granted_by_id,
        )
        db.add(access)

    db.commit()
    db.refresh(access)
    return access


def remove_guest_project_access(
    db: Session,
    project_id: int,
    guest_user_id: int,
    organization_id: int,
) -> None:
    """Revoke a guest's access to a specific project."""
    access = db.query(GuestProjectAccess).filter(
        GuestProjectAccess.project_id == project_id,
        GuestProjectAccess.guest_user_id == guest_user_id,
        GuestProjectAccess.organization_id == organization_id,
    ).first()
    if access:
        access.is_active = False
        access.updated_at = utc_now()
        db.commit()


# =========================================================================
# 5. CLIENT PORTAL QUERIES (STRICT SERVER-SIDE FILTERING)
# =========================================================================

def verify_guest_project_access(
    db: Session,
    project_id: int,
    user_id: int,
    required_permission: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify that a user has active guest access to a project and check permission."""
    # Check if user is an internal organization admin or project owner (bypass guest restriction)
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise ValueError("Project not found")

    access = db.query(GuestProjectAccess).filter(
        GuestProjectAccess.project_id == project_id,
        GuestProjectAccess.guest_user_id == user_id,
        GuestProjectAccess.is_active == True,
    ).first()

    if not access:
        # Check if internal user
        if proj.created_by == user_id or proj.owner_id == user_id:
            return {"role": "INTERNAL_ADMIN", "permissions": {k: True for k in ROLE_PERMISSIONS["CLIENT_APPROVER"]}}
        raise PermissionError("Access denied: You are not authorized to view this project")

    # Check expiration
    if access.expires_at and to_naive(access.expires_at) < utc_now():
        access.is_active = False
        db.commit()
        raise PermissionError("Access expired: Your access to this project has ended")

    try:
        perms = json.loads(access.permissions_json or "{}")
    except Exception:
        perms = ROLE_PERMISSIONS.get(access.role, ROLE_PERMISSIONS["CLIENT_VIEWER"])

    if required_permission and not perms.get(required_permission, False):
        raise PermissionError(f"Permission denied: Missing '{required_permission}' permission")

    return {
        "role": access.role,
        "permissions": perms,
        "organization_id": access.organization_id,
    }


def get_client_dashboard(
    db: Session,
    user_id: int,
) -> Dict[str, Any]:
    """Retrieve external client dashboard containing only explicitly authorized projects."""
    access_grants = db.query(GuestProjectAccess).filter(
        GuestProjectAccess.guest_user_id == user_id,
        GuestProjectAccess.is_active == True,
    ).all()

    shared_projects = []
    total_deliverables = 0
    pending_approvals = 0

    for grant in access_grants:
        # Check project visibility
        vis = get_or_create_project_visibility(db, grant.project_id, grant.organization_id)
        if not vis.is_shared:
            continue

        proj = grant.project
        if not proj or proj.is_deleted or proj.is_archived:
            continue

        # Calculate progress
        if vis.progress_mode == "MANUAL":
            progress = vis.manual_progress_percent
        else:
            total_tasks = db.query(func.count(ClientSharedTask.id)).filter(
                ClientSharedTask.project_id == proj.id,
                ClientSharedTask.is_visible == True,
            ).scalar() or 0
            completed_tasks = db.query(func.count(ClientSharedTask.id)).filter(
                ClientSharedTask.project_id == proj.id,
                ClientSharedTask.is_visible == True,
                ClientSharedTask.client_status == "COMPLETED",
            ).scalar() or 0
            progress = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

        # Deliverables count
        delivs = db.query(ClientDeliverable).filter(
            ClientDeliverable.project_id == proj.id
        ).all()
        proj_deliv_count = len(delivs)
        proj_pending = sum(1 for d in delivs if d.status in ["SUBMITTED", "UNDER_REVIEW"])

        total_deliverables += proj_deliv_count
        pending_approvals += proj_pending

        shared_projects.append({
            "project_id": proj.id,
            "name": proj.name,
            "description": proj.description if vis.show_description else None,
            "status": proj.status,
            "progress_percent": progress if vis.show_progress else None,
            "start_date": proj.start_date,
            "due_date": proj.due_date,
            "role": grant.role,
            "deliverables_count": proj_deliv_count,
            "pending_approvals_count": proj_pending,
            "custom_banner": vis.custom_banner_message,
        })

    # Update last access timestamp on guest profile
    db.query(GuestProfile).filter(GuestProfile.user_id == user_id).update({"last_access_at": utc_now()})
    db.commit()

    return {
        "projects": shared_projects,
        "total_shared_projects": len(shared_projects),
        "total_deliverables": total_deliverables,
        "pending_approvals": pending_approvals,
    }


def get_client_project_overview(
    db: Session,
    project_id: int,
    user_id: int,
) -> Dict[str, Any]:
    """Retrieve detailed project overview with safe field allowlists."""
    access_info = verify_guest_project_access(db, project_id, user_id, "can_view_summary")
    vis = get_or_create_project_visibility(db, project_id, access_info.get("organization_id", 0))

    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise ValueError("Project not found")

    # Progress calculation
    if vis.progress_mode == "MANUAL":
        progress = vis.manual_progress_percent
    else:
        total_tasks = db.query(func.count(ClientSharedTask.id)).filter(
            ClientSharedTask.project_id == proj.id,
            ClientSharedTask.is_visible == True,
        ).scalar() or 0
        completed_tasks = db.query(func.count(ClientSharedTask.id)).filter(
            ClientSharedTask.project_id == proj.id,
            ClientSharedTask.is_visible == True,
            ClientSharedTask.client_status == "COMPLETED",
        ).scalar() or 0
        progress = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # Log project view
    log = GuestActivityLog(
        organization_id=proj.organization_id or 0,
        project_id=project_id,
        guest_user_id=user_id,
        action="PROJECT_VIEWED",
        resource_type="PROJECT",
        resource_id=str(project_id),
    )
    db.add(log)
    db.commit()

    return {
        "project_id": proj.id,
        "name": proj.name,
        "description": proj.description if vis.show_description else None,
        "status": proj.status,
        "health": proj.health,
        "progress_percent": progress if vis.show_progress else None,
        "start_date": proj.start_date,
        "due_date": proj.due_date,
        "custom_banner_message": vis.custom_banner_message,
        "visibility_settings": {
            "show_tasks": vis.show_tasks,
            "show_milestones": vis.show_milestones,
            "show_deliverables": vis.show_deliverables,
            "show_documents": vis.show_documents,
            "allow_comments": vis.allow_comments,
            "allow_feedback": vis.allow_feedback,
            "allow_uploads": vis.allow_uploads,
            "allow_approvals": vis.allow_approvals,
        },
        "user_permissions": access_info["permissions"],
    }


# =========================================================================
# 6. CLIENT DELIVERABLES & APPROVALS WORKFLOW
# =========================================================================

def list_client_deliverables(
    db: Session,
    project_id: int,
    user_id: int,
) -> List[Dict[str, Any]]:
    """List deliverables for a shared project."""
    verify_guest_project_access(db, project_id, user_id, "can_view_documents")
    deliverables = db.query(ClientDeliverable).filter(
        ClientDeliverable.project_id == project_id
    ).order_by(desc(ClientDeliverable.submitted_at)).all()

    results = []
    for d in deliverables:
        results.append({
            "id": d.id,
            "project_id": d.project_id,
            "task_id": d.task_id,
            "title": d.title,
            "description": d.description,
            "file_name": d.file_name,
            "file_url": d.file_url,
            "file_size": d.file_size,
            "file_type": d.file_type,
            "version_number": d.version_number,
            "status": d.status,
            "submitted_by": d.submitted_by.full_name if d.submitted_by else None,
            "submitted_at": d.submitted_at,
            "reviewed_by": d.reviewed_by.full_name if d.reviewed_by else None,
            "reviewed_at": d.reviewed_at,
            "review_comments": d.review_comments,
        })
    return results


def create_client_deliverable(
    db: Session,
    project_id: int,
    organization_id: int,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    file_name: Optional[str] = None,
    file_url: Optional[str] = None,
    file_size: int = 0,
    file_type: Optional[str] = None,
    task_id: Optional[str] = None,
) -> ClientDeliverable:
    """Create a client-facing deliverable and initial version record."""
    deliv = ClientDeliverable(
        project_id=project_id,
        organization_id=organization_id,
        task_id=task_id,
        title=title.strip(),
        description=description,
        file_name=file_name,
        file_url=file_url,
        file_size=file_size,
        file_type=file_type,
        version_number=1,
        status="SUBMITTED",
        submitted_by_id=user_id,
        submitted_at=utc_now(),
    )
    db.add(deliv)
    db.flush()

    ver = ClientDeliverableVersion(
        deliverable_id=deliv.id,
        version_number=1,
        file_name=file_name,
        file_url=file_url,
        file_size=file_size,
        changelog="Initial deliverable submission",
        submitted_by_id=user_id,
    )
    db.add(ver)

    log = GuestActivityLog(
        organization_id=organization_id,
        project_id=project_id,
        guest_user_id=user_id,
        action="DELIVERABLE_SUBMITTED",
        resource_type="DELIVERABLE",
        resource_id=str(deliv.id),
        details_json=json.dumps({"title": title, "version": 1}),
    )
    db.add(log)
    db.commit()
    db.refresh(deliv)
    return deliv


def review_client_deliverable(
    db: Session,
    deliverable_id: int,
    user_id: int,
    decision: str,  # APPROVED or CHANGES_REQUESTED
    comments: Optional[str] = None,
) -> ClientDeliverable:
    """Submit approval or request changes on a client deliverable."""
    deliv = db.query(ClientDeliverable).filter(ClientDeliverable.id == deliverable_id).first()
    if not deliv:
        raise ValueError("Deliverable not found")

    # Verify guest has approval permission on this project
    verify_guest_project_access(db, deliv.project_id, user_id, "can_approve_deliverables")

    decision_clean = decision.upper()
    if decision_clean not in ["APPROVED", "CHANGES_REQUESTED"]:
        raise ValueError("Decision must be either 'APPROVED' or 'CHANGES_REQUESTED'")

    if decision_clean == "CHANGES_REQUESTED" and not comments:
        raise ValueError("Comments are required when requesting changes")

    deliv.status = decision_clean
    deliv.reviewed_by_id = user_id
    deliv.reviewed_at = utc_now()
    deliv.review_comments = comments
    deliv.updated_at = utc_now()

    log_action = "DELIVERABLE_APPROVED" if decision_clean == "APPROVED" else "CHANGES_REQUESTED"
    log = GuestActivityLog(
        organization_id=deliv.organization_id,
        project_id=deliv.project_id,
        guest_user_id=user_id,
        action=log_action,
        resource_type="DELIVERABLE",
        resource_id=str(deliv.id),
        details_json=json.dumps({"decision": decision_clean, "comments": comments}),
    )
    db.add(log)
    db.commit()
    db.refresh(deliv)
    return deliv


# =========================================================================
# 7. CLIENT FEEDBACK & CONTROLLED COMMENTS
# =========================================================================

def list_client_feedback(
    db: Session,
    project_id: int,
    user_id: int,
) -> List[Dict[str, Any]]:
    """List client feedback for a project."""
    verify_guest_project_access(db, project_id, user_id, "can_view_summary")
    feedbacks = db.query(ClientFeedback).filter(
        ClientFeedback.project_id == project_id
    ).order_by(desc(ClientFeedback.created_at)).all()

    return [{
        "id": f.id,
        "title": f.title,
        "content": f.content,
        "category": f.category,
        "status": f.status,
        "author": f.guest_user.full_name if f.guest_user else "Client",
        "response_text": f.response_text,
        "responded_by": f.responded_by.full_name if f.responded_by else None,
        "responded_at": f.responded_at,
        "created_at": f.created_at,
    } for f in feedbacks]


def submit_client_feedback(
    db: Session,
    project_id: int,
    user_id: int,
    title: str,
    content: str,
    category: str = "GENERAL",
) -> ClientFeedback:
    """Submit client feedback."""
    access_info = verify_guest_project_access(db, project_id, user_id, "can_submit_feedback")
    fb = ClientFeedback(
        project_id=project_id,
        organization_id=access_info.get("organization_id", 0),
        guest_user_id=user_id,
        title=title.strip(),
        content=content.strip(),
        category=category.upper(),
        status="NEW",
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


def list_client_comments(
    db: Session,
    project_id: int,
    user_id: int,
    task_id: Optional[str] = None,
    deliverable_id: Optional[int] = None,
    feedback_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List client-visible comments for an item."""
    verify_guest_project_access(db, project_id, user_id, "can_view_summary")
    query = db.query(ClientComment).filter(
        ClientComment.project_id == project_id,
        ClientComment.is_client_visible == True,
    )
    if task_id:
        query = query.filter(ClientComment.task_id == task_id)
    if deliverable_id:
        query = query.filter(ClientComment.deliverable_id == deliverable_id)
    if feedback_id:
        query = query.filter(ClientComment.feedback_id == feedback_id)

    comments = query.order_by(ClientComment.created_at.asc()).all()
    return [{
        "id": c.id,
        "author_id": c.author_id,
        "author_name": c.author.full_name if c.author else "User",
        "content": c.content,
        "created_at": c.created_at,
    } for c in comments]


def create_client_comment(
    db: Session,
    project_id: int,
    user_id: int,
    content: str,
    task_id: Optional[str] = None,
    deliverable_id: Optional[int] = None,
    feedback_id: Optional[int] = None,
) -> ClientComment:
    """Post a client comment."""
    access_info = verify_guest_project_access(db, project_id, user_id, "can_comment")
    comment = ClientComment(
        project_id=project_id,
        organization_id=access_info.get("organization_id", 0),
        author_id=user_id,
        content=content.strip(),
        task_id=task_id,
        deliverable_id=deliverable_id,
        feedback_id=feedback_id,
        is_client_visible=True,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


# =========================================================================
# 8. CLIENT REPORTS & SHARED DOCUMENTS
# =========================================================================

def list_client_documents(
    db: Session,
    project_id: int,
    user_id: int,
) -> List[Dict[str, Any]]:
    """List approved documents shared with client."""
    verify_guest_project_access(db, project_id, user_id, "can_view_documents")
    docs = db.query(ClientDocumentAccess).filter(
        ClientDocumentAccess.project_id == project_id
    ).all()
    results = []
    now = utc_now()
    for doc in docs:
        if doc.expires_at and to_naive(doc.expires_at) < now:
            continue
        results.append({
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "file_name": doc.file_name,
            "file_url": doc.file_url,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "is_downloadable": doc.is_downloadable,
            "expires_at": doc.expires_at,
            "created_at": doc.created_at,
        })
    return results


def generate_client_report(
    db: Session,
    project_id: int,
    organization_id: int,
    user_id: int,
    title: str,
    summary: Optional[str] = None,
    status_override: Optional[str] = None,
) -> ClientReport:
    """Generate a client-facing progress report from approved tasks and deliverables."""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise ValueError("Project not found")

    tasks = db.query(ClientSharedTask).filter(
        ClientSharedTask.project_id == project_id,
        ClientSharedTask.is_visible == True,
    ).all()
    tasks_summary = [{
        "title": t.client_title or t.task.title,
        "status": t.client_status,
        "priority": t.client_priority,
        "due_date": str(t.due_date) if t.due_date else None,
    } for t in tasks]

    delivs = db.query(ClientDeliverable).filter(
        ClientDeliverable.project_id == project_id
    ).all()
    delivs_summary = [{
        "title": d.title,
        "version": d.version_number,
        "status": d.status,
        "reviewed_at": str(d.reviewed_at) if d.reviewed_at else None,
    } for d in delivs]

    total = len(tasks)
    completed = sum(1 for t in tasks if t.client_status == "COMPLETED")
    progress = round((completed / total * 100), 1) if total > 0 else 0.0

    report = ClientReport(
        project_id=project_id,
        organization_id=organization_id,
        title=title.strip(),
        summary=summary,
        status_override=status_override or proj.status,
        progress_percent=progress,
        tasks_summary_json=json.dumps(tasks_summary),
        deliverables_summary_json=json.dumps(delivs_summary),
        is_published=True,
        published_at=utc_now(),
        created_by_id=user_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_client_reports(
    db: Session,
    project_id: int,
    user_id: int,
) -> List[Dict[str, Any]]:
    """List published reports for a project."""
    verify_guest_project_access(db, project_id, user_id, "can_view_reports")
    reports = db.query(ClientReport).filter(
        ClientReport.project_id == project_id,
        ClientReport.is_published == True,
    ).order_by(desc(ClientReport.published_at)).all()

    return [{
        "id": r.id,
        "title": r.title,
        "summary": r.summary,
        "status_override": r.status_override,
        "progress_percent": r.progress_percent,
        "tasks_count": len(json.loads(r.tasks_summary_json or "[]")),
        "deliverables_count": len(json.loads(r.deliverables_summary_json or "[]")),
        "published_at": r.published_at,
    } for r in reports]


# =========================================================================
# 9. PORTAL SETTINGS & AUDIT LOGS
# =========================================================================

def get_or_create_portal_settings(
    db: Session,
    organization_id: int,
) -> ClientPortalSettings:
    """Retrieve or create organization portal settings."""
    settings = db.query(ClientPortalSettings).filter(
        ClientPortalSettings.organization_id == organization_id
    ).first()
    if not settings:
        settings = ClientPortalSettings(
            organization_id=organization_id,
            is_portal_enabled=True,
            allow_guest_invitations=True,
            default_role="CLIENT_VIEWER",
            default_token_expiration_days=7,
            allow_guest_comments=True,
            allow_guest_uploads=False,
            require_approval_reason=True,
            custom_portal_title="Client Collaboration Portal",
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_portal_settings(
    db: Session,
    organization_id: int,
    updates: Dict[str, Any],
) -> ClientPortalSettings:
    """Update organization portal governance settings."""
    settings = get_or_create_portal_settings(db, organization_id)
    allowed = [
        "is_portal_enabled", "allow_guest_invitations", "default_role",
        "default_token_expiration_days", "allow_guest_comments",
        "allow_guest_uploads", "require_approval_reason", "custom_portal_title"
    ]
    for k, v in updates.items():
        if k in allowed:
            setattr(settings, k, v)
    settings.updated_at = utc_now()
    db.commit()
    db.refresh(settings)
    return settings


def list_guest_activity_logs(
    db: Session,
    organization_id: int,
    project_id: Optional[int] = None,
    guest_user_id: Optional[int] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List audit activity logs for guests."""
    query = db.query(GuestActivityLog).filter(
        GuestActivityLog.organization_id == organization_id
    )
    if project_id:
        query = query.filter(GuestActivityLog.project_id == project_id)
    if guest_user_id:
        query = query.filter(GuestActivityLog.guest_user_id == guest_user_id)

    logs = query.order_by(desc(GuestActivityLog.created_at)).limit(limit).all()
    return [{
        "id": l.id,
        "action": l.action,
        "guest_name": l.guest_user.full_name if l.guest_user else "Guest",
        "project_id": l.project_id,
        "resource_type": l.resource_type,
        "resource_id": l.resource_id,
        "details": json.loads(l.details_json or "{}"),
        "created_at": l.created_at,
    } for l in logs]
