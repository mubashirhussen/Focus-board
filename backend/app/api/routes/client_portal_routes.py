"""
FocusBoard Module B53: Client & Guest Portal API Routes.
Mounts endpoints for guest management, tokenized invitations, granular project sharing,
deliverables review, feedback, comments, documents, progress reports, settings, and audit logs.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.client_portal import GuestInvitation
from app.schemas.client_portal import (
    GuestInvitationCreate,
    GuestInvitationResponse,
    GuestInvitationAcceptRequest,
    GuestProfileResponse,
    GuestProjectShareRequest,
    ProjectVisibilityUpdateRequest,
    ClientDeliverableCreate,
    ClientDeliverableReviewRequest,
    ClientFeedbackCreate,
    ClientFeedbackRespondRequest,
    ClientCommentCreate,
    ClientReportCreate,
    ClientPortalSettingsUpdate,
)
from app.services import client_portal_service as service

router = APIRouter(prefix="/client-portal", tags=["Client & Guest Portal"])


def get_user_org_id(db: Session, current_user: User) -> int:
    """Helper to determine organization context for current user."""
    # Check membership
    mem = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).first()
    if mem:
        return mem.organization_id

    # Check owned org
    org = db.query(Organization).filter(
        Organization.owner_id == current_user.id
    ).first()
    if org:
        return org.id

    # Fallback or create default org
    first_org = db.query(Organization).first()
    if first_org:
        return first_org.id
    raise HTTPException(status_code=400, detail="User does not belong to any organization")


# =========================================================================
# 1. GUEST INVITATION WORKFLOWS
# =========================================================================

@router.post("/invitations", response_model=GuestInvitationResponse)
def create_invitation(
    payload: GuestInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite an external client or stakeholder."""
    org_id = get_user_org_id(db, current_user)
    try:
        res = service.create_guest_invitation(
            db=db,
            organization_id=org_id,
            invited_by_id=current_user.id,
            guest_email=payload.guest_email,
            guest_name=payload.guest_name,
            company_name=payload.company_name,
            role=payload.role,
            project_ids=payload.project_ids,
            custom_permissions=payload.custom_permissions,
            message=payload.message,
            expiration_days=payload.expiration_days,
        )
        inv = res["invitation"]
        return GuestInvitationResponse(
            id=inv.id,
            organization_id=inv.organization_id,
            guest_email=inv.guest_email,
            guest_name=inv.guest_name,
            company_name=inv.company_name,
            status=inv.status,
            role=inv.role,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            raw_token=res["raw_token"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invitations")
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending and historical invitations for the organization."""
    org_id = get_user_org_id(db, current_user)
    invites = db.query(GuestInvitation).filter(
        GuestInvitation.organization_id == org_id
    ).order_by(GuestInvitation.created_at.desc()).all()

    return [{
        "id": inv.id,
        "guest_email": inv.guest_email,
        "guest_name": inv.guest_name,
        "company_name": inv.company_name,
        "status": inv.status,
        "role": inv.role,
        "expires_at": inv.expires_at,
        "created_at": inv.created_at,
    } for inv in invites]


@router.post("/invitations/{invitation_id}/revoke")
def revoke_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a pending guest invitation."""
    org_id = get_user_org_id(db, current_user)
    try:
        inv = service.revoke_guest_invitation(db, invitation_id, org_id, current_user.id)
        return {"status": "REVOKED", "invitation_id": inv.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invitations/{invitation_id}/resend")
def resend_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regenerate token and renew invitation expiration."""
    org_id = get_user_org_id(db, current_user)
    try:
        res = service.resend_guest_invitation(db, invitation_id, org_id)
        return {
            "status": "RESENT",
            "invitation_id": res["invitation"].id,
            "raw_token": res["raw_token"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invitations/accept")
def accept_invitation(
    payload: GuestInvitationAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept guest invitation and bind project access to current authenticated account."""
    try:
        res = service.accept_guest_invitation(db, payload.token, current_user)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 2. GUEST MANAGEMENT (ADMIN)
# =========================================================================

@router.get("/guests", response_model=List[GuestProfileResponse])
def list_guests(
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all guests in current organization."""
    org_id = get_user_org_id(db, current_user)
    return service.list_organization_guests(db, org_id, search, status)


@router.post("/guests/{guest_user_id}/suspend")
def suspend_guest(
    guest_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Instantly suspend guest access across all projects."""
    org_id = get_user_org_id(db, current_user)
    try:
        prof = service.suspend_guest_access(db, guest_user_id, org_id, current_user.id)
        return {"status": "SUSPENDED", "user_id": prof.user_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/guests/{guest_user_id}/reactivate")
def reactivate_guest(
    guest_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reactivate suspended guest access."""
    org_id = get_user_org_id(db, current_user)
    try:
        prof = service.reactivate_guest_access(db, guest_user_id, org_id, current_user.id)
        return {"status": "ACTIVE", "user_id": prof.user_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/guests/{guest_user_id}")
def revoke_guest(
    guest_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently revoke guest access from the organization."""
    org_id = get_user_org_id(db, current_user)
    service.revoke_guest_from_organization(db, guest_user_id, org_id, current_user.id)
    return {"status": "REVOKED", "user_id": guest_user_id}


# =========================================================================
# 3. CLIENT PORTAL DASHBOARD (EXTERNAL VIEW)
# =========================================================================

@router.get("/dashboard")
def get_client_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """External client dashboard showing all authorized shared projects."""
    return service.get_client_dashboard(db, current_user.id)


@router.get("/projects/{project_id}")
def get_client_project_overview(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Client project overview with safe field allowlists."""
    try:
        return service.get_client_project_overview(db, project_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =========================================================================
# 4. PROJECT SHARING & VISIBILITY CONTROLS
# =========================================================================

@router.get("/projects/{project_id}/visibility")
def get_project_visibility(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project client sharing settings."""
    org_id = get_user_org_id(db, current_user)
    vis = service.get_or_create_project_visibility(db, project_id, org_id)
    return vis


@router.put("/projects/{project_id}/visibility")
def update_project_visibility(
    project_id: int,
    payload: ProjectVisibilityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project client sharing settings."""
    org_id = get_user_org_id(db, current_user)
    updates = payload.dict(exclude_unset=True)
    vis = service.update_project_visibility(db, project_id, org_id, updates, current_user.id)
    return vis


@router.post("/projects/{project_id}/share")
def share_project(
    project_id: int,
    payload: GuestProjectShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicitly share a project with an external guest."""
    org_id = get_user_org_id(db, current_user)
    try:
        access = service.share_project_with_guest(
            db=db,
            project_id=project_id,
            organization_id=org_id,
            guest_user_id=payload.guest_user_id,
            role=payload.role,
            custom_permissions=payload.custom_permissions,
            expires_at=payload.expires_at,
            granted_by_id=current_user.id,
        )
        return {"status": "SHARED", "project_id": access.project_id, "guest_user_id": access.guest_user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/projects/{project_id}/guests/{guest_user_id}")
def unshare_project(
    project_id: int,
    guest_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove guest access from a project."""
    org_id = get_user_org_id(db, current_user)
    service.remove_guest_project_access(db, project_id, guest_user_id, org_id)
    return {"status": "UNSHARED", "project_id": project_id, "guest_user_id": guest_user_id}


# =========================================================================
# 5. DELIVERABLES & APPROVALS
# =========================================================================

@router.get("/projects/{project_id}/deliverables")
def list_deliverables(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List deliverables for project."""
    try:
        return service.list_client_deliverables(db, project_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/projects/{project_id}/deliverables")
def create_deliverable(
    project_id: int,
    payload: ClientDeliverableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload or submit a client deliverable."""
    org_id = get_user_org_id(db, current_user)
    deliv = service.create_client_deliverable(
        db=db,
        project_id=project_id,
        organization_id=org_id,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        file_name=payload.file_name,
        file_url=payload.file_url,
        file_size=payload.file_size,
        file_type=payload.file_type,
        task_id=payload.task_id,
    )
    return {"status": "CREATED", "deliverable_id": deliv.id}


@router.post("/deliverables/{deliverable_id}/review")
def review_deliverable(
    deliverable_id: int,
    payload: ClientDeliverableReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or request changes on a client deliverable."""
    try:
        deliv = service.review_client_deliverable(
            db=db,
            deliverable_id=deliverable_id,
            user_id=current_user.id,
            decision=payload.decision,
            comments=payload.comments,
        )
        return {
            "status": deliv.status,
            "deliverable_id": deliv.id,
            "reviewed_at": deliv.reviewed_at,
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 6. CLIENT FEEDBACK & COMMENTS
# =========================================================================

@router.get("/projects/{project_id}/feedback")
def list_feedback(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List client feedback for project."""
    try:
        return service.list_client_feedback(db, project_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/projects/{project_id}/feedback")
def submit_feedback(
    project_id: int,
    payload: ClientFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit client feedback."""
    try:
        fb = service.submit_client_feedback(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
            title=payload.title,
            content=payload.content,
            category=payload.category,
        )
        return {"status": "CREATED", "feedback_id": fb.id}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/projects/{project_id}/comments")
def list_comments(
    project_id: int,
    task_id: Optional[str] = None,
    deliverable_id: Optional[int] = None,
    feedback_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List client-visible comments."""
    try:
        return service.list_client_comments(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
            task_id=task_id,
            deliverable_id=deliverable_id,
            feedback_id=feedback_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/projects/{project_id}/comments")
def post_comment(
    project_id: int,
    payload: ClientCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post client-visible comment."""
    try:
        c = service.create_client_comment(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
            content=payload.content,
            task_id=payload.task_id,
            deliverable_id=payload.deliverable_id,
            feedback_id=payload.feedback_id,
        )
        return {"status": "CREATED", "comment_id": c.id}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# =========================================================================
# 7. DOCUMENTS & PROGRESS REPORTS
# =========================================================================

@router.get("/projects/{project_id}/documents")
def list_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents shared with client."""
    try:
        return service.list_client_documents(db, project_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/projects/{project_id}/reports")
def list_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List client progress reports."""
    try:
        return service.list_client_reports(db, project_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/projects/{project_id}/reports")
def create_report(
    project_id: int,
    payload: ClientReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and publish client progress report."""
    org_id = get_user_org_id(db, current_user)
    try:
        rep = service.generate_client_report(
            db=db,
            project_id=project_id,
            organization_id=org_id,
            user_id=current_user.id,
            title=payload.title,
            summary=payload.summary,
            status_override=payload.status_override,
        )
        return {"status": "PUBLISHED", "report_id": rep.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 8. PORTAL SETTINGS & AUDIT LOGS
# =========================================================================

@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve organization client portal settings."""
    org_id = get_user_org_id(db, current_user)
    return service.get_or_create_portal_settings(db, org_id)


@router.put("/settings")
def update_settings(
    payload: ClientPortalSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update organization client portal settings."""
    org_id = get_user_org_id(db, current_user)
    updates = payload.dict(exclude_unset=True)
    return service.update_portal_settings(db, org_id, updates)


@router.get("/audit-logs")
def list_audit_logs(
    project_id: Optional[int] = None,
    guest_user_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List guest access audit logs."""
    org_id = get_user_org_id(db, current_user)
    return service.list_guest_activity_logs(db, org_id, project_id, guest_user_id, limit)
