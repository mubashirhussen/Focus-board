"""
FocusBoard Multi-Tenant Organizations, Workspaces & RBAC Routes (Phase B3).
Provides multi-tenant organization management, scoped workspaces, member roles & permissions,
invitations flow, ownership transfer, and cross-tenant isolation enforcement.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.routes.auth_routes import get_current_user
from app.core.logging import logger
from app.core.security import generate_secure_token, hash_token
from app.db.session import get_db
from app.models.collaboration import Workspace
from app.models.organization import Organization, OrganizationMember, OrganizationInvitation
from app.models.user import User
from app.schemas.organization import (
    AcceptInvitationRequest,
    DeclineInvitationRequest,
    OrganizationCreate,
    OrganizationInvitationCreate,
    OrganizationInvitationResponse,
    OrganizationMemberResponse,
    OrganizationMemberUpdate,
    OrganizationResponse,
    OrganizationUpdate,
    OwnershipTransferRequest,
    WorkspaceCreateInOrg,
    WorkspaceResponseInOrg,
)

router = APIRouter(tags=["Multi-Tenant Organizations & RBAC"])


def _slugify(text: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "org"


def _require_org_membership(org_id: int, user_id: int, db: Session, min_role: Optional[str] = None) -> OrganizationMember:
    """Verifies user belongs to organization and satisfies minimum role level."""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user_id,
        OrganizationMember.is_active == True,
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not an active member of this organization.",
        )

    role_hierarchy = {"viewer": 1, "member": 2, "admin": 3, "owner": 4}
    if min_role:
        user_level = role_hierarchy.get(member.role.lower(), 1)
        required_level = role_hierarchy.get(min_role.lower(), 1)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{min_role}' or higher required.",
            )
    return member


# =========================================================================
# Organization CRUD
# =========================================================================

@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new organization. Creator is automatically designated as OWNER."""
    base_slug = org_in.slug or _slugify(org_in.name)
    slug = base_slug
    idx = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{idx}"
        idx += 1

    org = Organization(
        name=org_in.name.strip(),
        slug=slug,
        description=org_in.description or "",
        plan=org_in.plan or "starter",
        owner_id=current_user.id,
        settings_json=json.dumps(org_in.settings or {}),
        is_active=True,
    )
    db.add(org)
    db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role="owner",
        title="Organization Owner",
        is_active=True,
    )
    db.add(member)
    db.commit()
    db.refresh(org)

    logger.info("Organization created: id=%d slug=%s by user=%d", org.id, org.slug, current_user.id)
    return org


@router.get("/organizations", response_model=List[OrganizationResponse])
def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all organizations where the current user is an active member."""
    memberships = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True,
    ).all()
    
    org_ids = [m.organization_id for m in memberships]
    if not org_ids:
        return []

    return db.query(Organization).filter(
        Organization.id.in_(org_ids),
        Organization.is_active == True,
    ).order_by(Organization.created_at.desc()).all()


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization_details(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves organization details. User must be a member of the organization."""
    _require_org_membership(org_id, current_user.id, db)
    org = db.query(Organization).filter(Organization.id == org_id, Organization.is_active == True).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return org


@router.patch("/organizations/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    org_in: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates organization profile and settings. Requires ADMIN or OWNER role."""
    _require_org_membership(org_id, current_user.id, db, min_role="admin")
    org = db.query(Organization).filter(Organization.id == org_id, Organization.is_active == True).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    if org_in.name is not None:
        org.name = org_in.name.strip()
    if org_in.description is not None:
        org.description = org_in.description
    if org_in.plan is not None:
        org.plan = org_in.plan
    if org_in.logo_url is not None:
        org.logo_url = org_in.logo_url
    if org_in.settings is not None:
        org.settings_json = json.dumps(org_in.settings)

    db.commit()
    db.refresh(org)
    logger.info("Organization id=%d updated by user=%d", org.id, current_user.id)
    return org


@router.delete("/organizations/{org_id}")
def delete_or_archive_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft-deletes (archives) an organization. Requires OWNER role."""
    _require_org_membership(org_id, current_user.id, db, min_role="owner")
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    
    org.is_active = False
    db.commit()
    logger.info("Organization id=%d archived by owner=%d", org.id, current_user.id)
    return {"message": "Organization has been archived successfully."}


# =========================================================================
# Ownership Transfer
# =========================================================================

@router.post("/organizations/{org_id}/transfer-ownership")
def transfer_organization_ownership(
    org_id: int,
    req: OwnershipTransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transfers primary organization ownership to another existing active member."""
    # Current user must be owner
    current_member = _require_org_membership(org_id, current_user.id, db, min_role="owner")
    org = db.query(Organization).filter(Organization.id == org_id, Organization.is_active == True).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    target_member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == req.new_owner_user_id,
        OrganizationMember.is_active == True,
    ).first()

    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target user is not an active member of this organization.",
        )

    # Transfer ownership
    org.owner_id = target_member.user_id
    target_member.role = "owner"
    current_member.role = "admin"  # Demote previous owner to admin

    db.commit()
    logger.info("Ownership of org=%d transferred from %d to %d", org_id, current_user.id, target_member.user_id)
    return {"message": "Organization ownership transferred successfully.", "new_owner_id": target_member.user_id}


# =========================================================================
# Members Management
# =========================================================================

@router.get("/organizations/{org_id}/members", response_model=List[OrganizationMemberResponse])
def list_organization_members(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all members of the organization."""
    _require_org_membership(org_id, current_user.id, db)
    members = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.is_active == True,
    ).all()

    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append(
            OrganizationMemberResponse(
                id=m.id,
                organization_id=m.organization_id,
                user_id=m.user_id,
                role=m.role,
                title=m.title,
                joined_at=m.joined_at,
                is_active=m.is_active,
                user={
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url,
                } if user else None,
            )
        )
    return result


@router.patch("/organizations/{org_id}/members/{user_id}", response_model=OrganizationMemberResponse)
def update_member_role(
    org_id: int,
    user_id: int,
    mem_in: OrganizationMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates a member's role or title. Requires ADMIN or OWNER. Cannot demote the last OWNER."""
    _require_org_membership(org_id, current_user.id, db, min_role="admin")
    
    target_member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user_id,
        OrganizationMember.is_active == True,
    ).first()

    if not target_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    if target_member.role == "owner" and mem_in.role and mem_in.role != "owner":
        # Check if another owner exists
        owner_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.role == "owner",
            OrganizationMember.is_active == True,
        ).count()
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the only owner. Transfer ownership first.",
            )

    if mem_in.role:
        target_member.role = mem_in.role.lower()
    if mem_in.title is not None:
        target_member.title = mem_in.title

    db.commit()
    db.refresh(target_member)
    user = db.query(User).filter(User.id == target_member.user_id).first()

    return OrganizationMemberResponse(
        id=target_member.id,
        organization_id=target_member.organization_id,
        user_id=target_member.user_id,
        role=target_member.role,
        title=target_member.title,
        joined_at=target_member.joined_at,
        is_active=target_member.is_active,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
        } if user else None,
    )


@router.delete("/organizations/{org_id}/members/{user_id}")
def remove_organization_member(
    org_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a member from organization (or allows member self-leave). Cannot remove the last owner."""
    if current_user.id != user_id:
        # Admin or owner kick
        _require_org_membership(org_id, current_user.id, db, min_role="admin")
    else:
        _require_org_membership(org_id, current_user.id, db)

    target_member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user_id,
        OrganizationMember.is_active == True,
    ).first()

    if not target_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    if target_member.role == "owner":
        owner_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.role == "owner",
            OrganizationMember.is_active == True,
        ).count()
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The sole owner cannot leave or be removed without transferring ownership.",
            )

    target_member.is_active = False
    db.commit()
    logger.info("User id=%d removed from org id=%d by user=%d", user_id, org_id, current_user.id)
    return {"message": "Member removed successfully."}


# =========================================================================
# Invitations
# =========================================================================

@router.post("/organizations/{org_id}/invitations", response_model=OrganizationInvitationResponse, status_code=status.HTTP_201_CREATED)
def invite_member_to_organization(
    org_id: int,
    inv_in: OrganizationInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invites a user to join the organization. Requires ADMIN or OWNER."""
    _require_org_membership(org_id, current_user.id, db, min_role="admin")
    clean_email = inv_in.email.lower().strip()

    # Check if already a member
    existing_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_user:
        existing_mem = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == existing_user.id,
            OrganizationMember.is_active == True,
        ).first()
        if existing_mem:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this organization.")

    # Check for pending invitation
    pending = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id == org_id,
        func.lower(OrganizationInvitation.email) == clean_email,
        OrganizationInvitation.status == "pending",
    ).first()
    if pending and pending.expires_at > datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An active invitation already exists for this email.")

    raw_token = generate_secure_token(32)
    inv = OrganizationInvitation(
        organization_id=org_id,
        email=clean_email,
        role=inv_in.role or "member",
        token_hash=hash_token(raw_token),
        invited_by_id=current_user.id,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    logger.info("Invitation created: org=%d email=%s by user=%d (invite token: %s)", org_id, clean_email, current_user.id, raw_token)
    return OrganizationInvitationResponse(
        id=inv.id,
        organization_id=inv.organization_id,
        email=inv.email,
        role=inv.role,
        status=inv.status,
        invited_by_id=inv.invited_by_id,
        expires_at=inv.expires_at,
        created_at=inv.created_at,
        invite_token=raw_token,
    )


@router.get("/organizations/{org_id}/invitations", response_model=List[OrganizationInvitationResponse])
def list_organization_invitations(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists pending invitations for an organization. Requires ADMIN or OWNER."""
    _require_org_membership(org_id, current_user.id, db, min_role="admin")
    return db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id == org_id,
        OrganizationInvitation.status == "pending",
        OrganizationInvitation.expires_at > datetime.utcnow(),
    ).all()


@router.delete("/organizations/{org_id}/invitations/{invitation_id}")
def revoke_organization_invitation(
    org_id: int,
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes an outstanding invitation. Requires ADMIN or OWNER."""
    _require_org_membership(org_id, current_user.id, db, min_role="admin")
    inv = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.id == invitation_id,
        OrganizationInvitation.organization_id == org_id,
    ).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    inv.status = "revoked"
    db.commit()
    return {"message": "Invitation revoked successfully."}


@router.post("/invitations/accept")
def accept_organization_invitation(
    req: AcceptInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accepts an organization invitation and adds user as a member."""
    t_hash = hash_token(req.token)
    inv = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.token_hash == t_hash,
        OrganizationInvitation.status == "pending",
    ).first()

    if not inv or inv.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation token.")

    # Check if user already a member
    existing_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == inv.organization_id,
        OrganizationMember.user_id == current_user.id,
    ).first()

    if existing_mem:
        existing_mem.is_active = True
        existing_mem.role = inv.role
    else:
        new_mem = OrganizationMember(
            organization_id=inv.organization_id,
            user_id=current_user.id,
            role=inv.role,
            is_active=True,
        )
        db.add(new_mem)

    inv.status = "accepted"
    db.commit()
    logger.info("User id=%d accepted invitation to org id=%d", current_user.id, inv.organization_id)
    return {"message": "Invitation accepted successfully. Welcome to the organization!"}


@router.post("/invitations/decline")
def decline_organization_invitation(
    req: DeclineInvitationRequest,
    db: Session = Depends(get_db)
):
    """Declines an invitation."""
    t_hash = hash_token(req.token)
    inv = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.token_hash == t_hash,
        OrganizationInvitation.status == "pending",
    ).first()

    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    inv.status = "declined"
    db.commit()
    return {"message": "Invitation declined."}


# =========================================================================
# Workspaces Scoped to Organization
# =========================================================================

@router.post("/organizations/{org_id}/workspaces", response_model=WorkspaceResponseInOrg, status_code=status.HTTP_201_CREATED)
def create_organization_workspace(
    org_id: int,
    ws_in: WorkspaceCreateInOrg,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a workspace scoped to an organization. Requires MEMBER or above."""
    _require_org_membership(org_id, current_user.id, db, min_role="member")
    
    ws = Workspace(
        name=ws_in.name.strip(),
        description=ws_in.description or "",
        organization_id=org_id,
        owner_id=current_user.id,
        visibility=ws_in.visibility or "organization",
        is_active=True,
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)

    logger.info("Workspace created in org=%d: id=%d name=%s by user=%d", org_id, ws.id, ws.name, current_user.id)
    return ws


@router.get("/organizations/{org_id}/workspaces", response_model=List[WorkspaceResponseInOrg])
def list_organization_workspaces(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all active workspaces belonging to the organization."""
    _require_org_membership(org_id, current_user.id, db)
    return db.query(Workspace).filter(
        Workspace.organization_id == org_id,
        Workspace.is_active == True,
    ).order_by(Workspace.created_at.desc()).all()
