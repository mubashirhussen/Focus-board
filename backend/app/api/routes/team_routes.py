from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.team_service import team_service
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamSummaryResponse,
    TeamSettingsUpdate,
    OwnershipTransferRequest,
    TeamMemberCreate,
    TeamMemberUpdateRole,
    TeamMemberResponse,
    TeamInvitationCreate,
    TeamInvitationResponse,
    TeamInvitationCreateResult,
    InvitationAcceptResponse,
    InvitationActionResponse,
)

router = APIRouter(prefix="/teams", tags=["Teams & Collaboration"])

# -------------------------------------------------------------
# Teams CRUD & Listing
# -------------------------------------------------------------

@router.get("", response_model=List[TeamResponse])
def list_teams(
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    search: Optional[str] = Query(None, description="Search team name or description"),
    is_archived: Optional[bool] = Query(False, description="Filter by archived status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List teams accessible to the current user."""
    return team_service.list_teams(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        workspace_id=workspace_id,
        search=search,
        is_archived=is_archived,
        skip=skip,
        limit=limit,
    )

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new team within the organization."""
    try:
        return team_service.create_team(db=db, current_user=current_user, team_in=team_in)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# -------------------------------------------------------------
# Invitation Acceptance & Decline (Registered before /{team_id})
# -------------------------------------------------------------

@router.post("/invitations/{token}/accept", response_model=InvitationAcceptResponse)
def accept_team_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept an invitation to join a team using a secure token."""
    try:
        member = team_service.accept_invitation(db=db, raw_token=token, current_user=current_user)
        return InvitationAcceptResponse(
            status="success",
            message="Invitation accepted successfully",
            team_id=member.team_id,
            role=member.role,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower() or "invalid" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

@router.post("/invitations/{token}/decline", response_model=InvitationActionResponse)
def decline_team_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Decline a team invitation using a secure token."""
    try:
        team_service.decline_invitation(db=db, raw_token=token, current_user=current_user)
        return InvitationActionResponse(status="success", message="Invitation declined successfully")
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower() or "invalid" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

# -------------------------------------------------------------
# Single Team Operations
# -------------------------------------------------------------

@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details for a single team with permission checks."""
    try:
        return team_service.get_team_or_404(db=db, team_id=team_id, current_user=current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_in: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update team metadata (ADMIN or OWNER only)."""
    try:
        return team_service.update_team(db=db, team_id=team_id, current_user=current_user, team_in=team_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete a team (OWNER only)."""
    try:
        team_service.delete_team(db=db, team_id=team_id, current_user=current_user)
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{team_id}/archive", response_model=TeamResponse)
def archive_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive a team to pause activities."""
    try:
        return team_service.archive_team(db=db, team_id=team_id, current_user=current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{team_id}/restore", response_model=TeamResponse)
def restore_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Restore an archived team."""
    try:
        return team_service.restore_team(db=db, team_id=team_id, current_user=current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/{team_id}/summary", response_model=TeamSummaryResponse)
def get_team_summary(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated metrics and collaboration statistics for the team."""
    try:
        return team_service.get_team_summary(db=db, team_id=team_id, current_user=current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{team_id}/transfer-ownership", response_model=TeamResponse)
def transfer_team_ownership(
    team_id: int,
    req: OwnershipTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transfer ownership of the team to another active member."""
    try:
        return team_service.transfer_ownership(db=db, team_id=team_id, current_user=current_user, new_owner_id=req.new_owner_id)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/{team_id}/settings", response_model=Dict[str, Any])
def get_team_settings(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get team configuration settings."""
    try:
        team = team_service.get_team_or_404(db=db, team_id=team_id, current_user=current_user)
        return team.settings
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.patch("/{team_id}/settings", response_model=TeamResponse)
def update_team_settings(
    team_id: int,
    settings_in: TeamSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update team configuration settings."""
    try:
        return team_service.update_settings(db=db, team_id=team_id, current_user=current_user, settings_in=settings_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# -------------------------------------------------------------
# Team Members Management
# -------------------------------------------------------------

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
def list_team_members(
    team_id: int,
    search: Optional[str] = Query(None, description="Search member name or email"),
    role: Optional[str] = Query(None, description="Filter by role: OWNER, ADMIN, MEMBER, VIEWER"),
    status_filter: Optional[str] = Query("ACTIVE", alias="status", description="Filter by status: ACTIVE, INACTIVE"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List team members with optional search and role filtering."""
    try:
        return team_service.list_members(
            db=db,
            team_id=team_id,
            current_user=current_user,
            search=search,
            role=role,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: int,
    member_in: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Directly add an organization member to the team."""
    try:
        return team_service.add_member(db=db, team_id=team_id, current_user=current_user, member_in=member_in)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        elif "already" in msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.patch("/{team_id}/members/{user_id}/role", response_model=TeamMemberResponse)
def update_team_member_role(
    team_id: int,
    user_id: int,
    role_in: TeamMemberUpdateRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a team member's role (with last-owner demotion protection)."""
    try:
        return team_service.update_member_role(
            db=db,
            team_id=team_id,
            target_user_id=user_id,
            current_user=current_user,
            role_in=role_in,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from the team or allow a user to leave the team."""
    try:
        team_service.remove_member(db=db, team_id=team_id, target_user_id=user_id, current_user=current_user)
        return None
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# -------------------------------------------------------------
# Team Invitations Management
# -------------------------------------------------------------

@router.get("/{team_id}/invitations", response_model=List[TeamInvitationResponse])
def list_team_invitations(
    team_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter: PENDING, ACCEPTED, DECLINED, REVOKED, EXPIRED"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending and historical team invitations (ADMIN or OWNER only)."""
    try:
        return team_service.list_invitations(db=db, team_id=team_id, current_user=current_user, status=status_filter)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{team_id}/invitations", response_model=TeamInvitationCreateResult, status_code=status.HTTP_201_CREATED)
def create_team_invitation(
    team_id: int,
    invite_in: TeamInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Issue a secure invitation to an email address to join the team."""
    try:
        invitation, raw_token = team_service.create_invitation(
            db=db,
            team_id=team_id,
            current_user=current_user,
            invite_in=invite_in,
        )
        res = TeamInvitationCreateResult.model_validate(invitation)
        res.token = raw_token
        return res
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        elif "already" in msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{team_id}/invitations/{invitation_id}/resend", response_model=TeamInvitationCreateResult)
def resend_team_invitation(
    team_id: int,
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resend a pending invitation with refreshed expiration and new token."""
    try:
        invitation, raw_token = team_service.resend_invitation(
            db=db,
            team_id=team_id,
            invitation_id=invitation_id,
            current_user=current_user,
        )
        res = TeamInvitationCreateResult.model_validate(invitation)
        res.token = raw_token
        return res
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{team_id}/invitations/{invitation_id}", response_model=InvitationActionResponse)
def revoke_team_invitation(
    team_id: int,
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a pending team invitation."""
    try:
        team_service.revoke_invitation(db=db, team_id=team_id, invitation_id=invitation_id, current_user=current_user)
        return InvitationActionResponse(status="success", message="Invitation revoked successfully")
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
