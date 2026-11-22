import re
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from app.models.team import Team, TeamMember, TeamInvitation
from app.models.organization import Organization, OrganizationMember
from app.models.collaboration import Workspace, Activity
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamSettingsUpdate,
    TeamMemberCreate,
    TeamMemberUpdateRole,
    TeamInvitationCreate,
    TeamSummaryResponse,
)

ROLE_HIERARCHY = {
    "OWNER": 4,
    "ADMIN": 3,
    "MEMBER": 2,
    "VIEWER": 1,
}

def utc_now() -> datetime:
    return datetime.utcnow()

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug or "team"

class TeamService:
    # ---------------------------------------------------------
    # Permissions & Access Helpers
    # ---------------------------------------------------------
    def get_user_role(self, db: Session, team_id: int, user_id: int) -> Optional[str]:
        """Get the user's role in a team, or None if not a member."""
        member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.status == "ACTIVE"
        ).first()
        return member.role if member else None

    def require_team_access(self, db: Session, team_id: int, current_user: User, min_role: str = "VIEWER") -> Tuple[Team, str]:
        """Verify team exists and user has at least min_role. Returns (Team, role)."""
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError("Team not found")

        # Check membership
        role = self.get_user_role(db, team_id, current_user.id)
        if not role:
            # If team is organization-visible and user is organization admin/owner, grant admin access
            org_member = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == team.organization_id,
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_active == True
            ).first()
            if org_member and org_member.role.lower() in ["owner", "admin"]:
                role = "ADMIN"
            elif team.visibility == "ORGANIZATION" and org_member:
                role = "VIEWER"

        if not role:
            raise ValueError("Team not found")  # IDOR protection

        required_rank = ROLE_HIERARCHY.get(min_role.upper(), 1)
        user_rank = ROLE_HIERARCHY.get(role.upper(), 0)
        if user_rank < required_rank:
            raise PermissionError(f"Insufficient permissions: requires {min_role} role")

        return team, role

    # ---------------------------------------------------------
    # Team CRUD & Lifecycle
    # ---------------------------------------------------------
    def create_team(self, db: Session, current_user: User, team_in: TeamCreate) -> Team:
        """Create a new team, generating a slug and adding creator as OWNER."""
        # 1. Resolve organization
        org_id = team_in.organization_id or getattr(current_user, "organization_id", None)
        if not org_id:
            first_org = db.query(OrganizationMember).filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_active == True
            ).first()
            if first_org:
                org_id = first_org.organization_id
            else:
                org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
                if org:
                    org_id = org.id
                else:
                    # Auto-provision a default organization for the user
                    org_name = f"{current_user.name or 'Default'} Organization"
                    base_slug = slugify(org_name)
                    slug = base_slug
                    counter = 1
                    while db.query(Organization).filter(Organization.slug == slug).first():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    org = Organization(
                        name=org_name,
                        slug=slug,
                        description="Default organization",
                        plan="starter",
                        owner_id=current_user.id,
                        is_active=True,
                    )
                    db.add(org)
                    db.flush()

                    org_member = OrganizationMember(
                        organization_id=org.id,
                        user_id=current_user.id,
                        role="owner",
                        title="Organization Owner",
                        is_active=True,
                        joined_at=utc_now(),
                    )
                    db.add(org_member)
                    db.flush()
                    org_id = org.id

        # Verify organization membership
        org = db.query(Organization).filter(Organization.id == org_id, Organization.is_active == True).first()
        if not org:
            raise ValueError("Organization not found or inactive")

        # 2. Slug generation
        base_slug = team_in.slug or slugify(team_in.name)
        slug = base_slug
        counter = 1
        while db.query(Team).filter(Team.organization_id == org_id, Team.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # 3. Create Team
        team = Team(
            organization_id=org_id,
            workspace_id=team_in.workspace_id,
            name=team_in.name.strip(),
            slug=slug,
            description=team_in.description,
            owner_id=current_user.id,
            created_by=current_user.id,
            visibility=team_in.visibility or "ORGANIZATION",
            status="active",
            avatar_url=team_in.avatar_url,
            is_archived=False,
        )
        db.add(team)
        db.flush()

        # 4. Add creator as OWNER in TeamMember
        owner_member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role="OWNER",
            status="ACTIVE",
            title="Team Owner",
            joined_at=utc_now(),
        )
        db.add(owner_member)

        # 5. Record activity
        if team.workspace_id:
            act = Activity(
                workspace_id=team.workspace_id,
                actor_id=current_user.id,
                event_type="TEAM_CREATED",
                description=f"Created team '{team.name}'.",
                created_at=utc_now()
            )
            db.add(act)

        db.commit()
        db.refresh(team)
        return team

    def list_teams(
        self,
        db: Session,
        current_user: User,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        search: Optional[str] = None,
        is_archived: Optional[bool] = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Team]:
        """Retrieve all teams accessible to the current user."""
        query = db.query(Team).options(joinedload(Team.members))

        if is_archived is not None:
            query = query.filter(Team.is_archived == is_archived)

        if organization_id:
            query = query.filter(Team.organization_id == organization_id)
        if workspace_id:
            query = query.filter(Team.workspace_id == workspace_id)

        if search:
            search_fmt = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Team.name).like(search_fmt),
                    func.lower(Team.description).like(search_fmt)
                )
            )

        # Access check: member of team OR org owner/admin
        user_team_ids = [
            m.team_id for m in db.query(TeamMember.team_id).filter(
                TeamMember.user_id == current_user.id,
                TeamMember.status == "ACTIVE"
            ).all()
        ]

        query = query.filter(
            or_(
                Team.id.in_(user_team_ids),
                Team.owner_id == current_user.id,
                and_(Team.visibility == "ORGANIZATION", Team.status == "active")
            )
        )

        teams = query.order_by(Team.created_at.desc()).offset(skip).limit(limit).all()
        for t in teams:
            t.member_count = len([m for m in t.members if m.status == "ACTIVE"])
        return teams

    def get_team_or_404(self, db: Session, team_id: int, current_user: User) -> Team:
        """Fetch a specific team enforcing access permissions."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="VIEWER")
        team.member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.status == "ACTIVE").count()
        return team

    def update_team(self, db: Session, team_id: int, current_user: User, team_in: TeamUpdate) -> Team:
        """Update team attributes."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="ADMIN")

        if team_in.name is not None:
            team.name = team_in.name.strip()
        if team_in.description is not None:
            team.description = team_in.description
        if team_in.visibility is not None:
            team.visibility = team_in.visibility
        if team_in.workspace_id is not None:
            team.workspace_id = team_in.workspace_id
        if team_in.avatar_url is not None:
            team.avatar_url = team_in.avatar_url
        if team_in.status is not None:
            team.status = team_in.status

        team.updated_at = utc_now()
        db.commit()
        db.refresh(team)
        team.member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.status == "ACTIVE").count()
        return team

    def update_settings(self, db: Session, team_id: int, current_user: User, settings_in: TeamSettingsUpdate) -> Team:
        """Update team settings configuration."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="ADMIN")
        curr = team.settings
        curr.update(settings_in.settings)
        team.settings = curr
        team.updated_at = utc_now()
        db.commit()
        db.refresh(team)
        return team

    def archive_team(self, db: Session, team_id: int, current_user: User) -> Team:
        """Archive a team."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="ADMIN")
        team.is_archived = True
        team.archived_at = utc_now()
        team.status = "archived"
        db.commit()
        db.refresh(team)
        return team

    def restore_team(self, db: Session, team_id: int, current_user: User) -> Team:
        """Restore an archived team."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="ADMIN")
        team.is_archived = False
        team.archived_at = None
        team.status = "active"
        db.commit()
        db.refresh(team)
        return team

    def delete_team(self, db: Session, team_id: int, current_user: User) -> bool:
        """Permanently delete a team (requires OWNER role)."""
        team, role = self.require_team_access(db, team_id, current_user, min_role="OWNER")
        db.delete(team)
        db.commit()
        return True

    def transfer_ownership(self, db: Session, team_id: int, current_user: User, new_owner_id: int) -> Team:
        """Transfer ownership of a team to another active member."""
        team, role = self.require_team_access(db, team_id, current_user, min_role="OWNER")
        if new_owner_id == current_user.id:
            return team

        new_owner_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == new_owner_id,
            TeamMember.status == "ACTIVE"
        ).first()

        if not new_owner_member:
            raise ValueError("Target user must be an active member of the team to receive ownership")

        # Promote new owner
        new_owner_member.role = "OWNER"
        team.owner_id = new_owner_id

        # Demote previous owner to ADMIN
        prev_owner_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if prev_owner_member:
            prev_owner_member.role = "ADMIN"

        team.updated_at = utc_now()
        db.commit()
        db.refresh(team)
        return team

    def get_team_summary(self, db: Session, team_id: int, current_user: User) -> TeamSummaryResponse:
        """Return team statistics and collaboration metrics."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="VIEWER")

        members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
        total_members = len(members)
        active_members = len([m for m in members if m.status == "ACTIVE"])
        member_ids = [m.user_id for m in members]

        pending_invitations = db.query(TeamInvitation).filter(
            TeamInvitation.team_id == team_id,
            TeamInvitation.status == "PENDING"
        ).count()

        # Compute projects in team's workspace
        active_projects_count = 0
        if team.workspace_id:
            active_projects_count = db.query(Project).filter(
                Project.workspace_id == team.workspace_id,
                Project.is_deleted == False
            ).count()

        # Compute assigned tasks
        assigned_tasks = db.query(Task).filter(
            Task.assignee_id.in_(member_ids),
            Task.is_deleted == False
        ).all() if member_ids else []

        assigned_tasks_count = len(assigned_tasks)
        completed_tasks_count = len([t for t in assigned_tasks if t.status.lower() in ["completed", "done"]])

        return TeamSummaryResponse(
            team_id=team.id,
            team_name=team.name,
            owner_id=team.owner_id,
            total_members=total_members,
            active_members=active_members,
            pending_invitations=pending_invitations,
            active_projects_count=active_projects_count,
            assigned_tasks_count=assigned_tasks_count,
            completed_tasks_count=completed_tasks_count,
            is_archived=team.is_archived,
        )

    # ---------------------------------------------------------
    # Team Membership Management
    # ---------------------------------------------------------
    def add_member(self, db: Session, team_id: int, current_user: User, member_in: TeamMemberCreate) -> TeamMember:
        """Add an organization user directly to the team."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="ADMIN")

        target_user = db.query(User).filter(User.id == member_in.user_id, User.is_active == True).first()
        if not target_user:
            raise ValueError("User not found")

        # Verify user belongs to same organization (auto-enroll if needed)
        org_member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == team.organization_id,
            OrganizationMember.user_id == target_user.id
        ).first()
        if not org_member:
            org_member = OrganizationMember(
                organization_id=team.organization_id,
                user_id=target_user.id,
                role="member",
                title=member_in.title or "Team Member",
                is_active=True,
                joined_at=utc_now()
            )
            db.add(org_member)
            db.flush()

        # Check existing membership
        existing = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == target_user.id
        ).first()
        if existing:
            if existing.status == "ACTIVE":
                raise ValueError("User is already an active member of this team")
            existing.status = "ACTIVE"
            existing.role = member_in.role
            existing.title = member_in.title
            existing.updated_at = utc_now()
            db.commit()
            db.refresh(existing)
            return existing

        member = TeamMember(
            team_id=team_id,
            user_id=target_user.id,
            role=member_in.role,
            status="ACTIVE",
            title=member_in.title,
            joined_at=utc_now(),
            invited_by_id=current_user.id,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    def list_members(
        self,
        db: Session,
        team_id: int,
        current_user: User,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = "ACTIVE",
        skip: int = 0,
        limit: int = 50,
    ) -> List[TeamMember]:
        """List team members with search and role filtering."""
        self.require_team_access(db, team_id, current_user, min_role="VIEWER")

        query = db.query(TeamMember).options(joinedload(TeamMember.user)).filter(TeamMember.team_id == team_id)

        if status:
            query = query.filter(TeamMember.status == status.upper())
        if role:
            query = query.filter(TeamMember.role == role.upper())

        if search:
            search_fmt = f"%{search.strip().lower()}%"
            query = query.join(TeamMember.user).filter(
                or_(
                    func.lower(User.name).like(search_fmt),
                    func.lower(User.email).like(search_fmt),
                    func.lower(TeamMember.title).like(search_fmt)
                )
            )

        return query.order_by(TeamMember.joined_at.asc()).offset(skip).limit(limit).all()

    def update_member_role(
        self,
        db: Session,
        team_id: int,
        target_user_id: int,
        current_user: User,
        role_in: TeamMemberUpdateRole,
    ) -> TeamMember:
        """Update a member's role with last-owner protection."""
        team, caller_role = self.require_team_access(db, team_id, current_user, min_role="ADMIN")

        target_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == target_user_id,
            TeamMember.status == "ACTIVE"
        ).first()

        if not target_member:
            raise ValueError("Team member not found")

        # Caller must be OWNER to modify an OWNER's role
        if target_member.role == "OWNER" and caller_role != "OWNER":
            raise PermissionError("Only team owner can modify an owner's role")

        # Last-owner protection
        if target_member.role == "OWNER" and role_in.role != "OWNER":
            other_owners = db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id != target_user_id,
                TeamMember.role == "OWNER",
                TeamMember.status == "ACTIVE"
            ).count()
            if other_owners == 0:
                raise ValueError("Cannot demote the last owner. Transfer ownership or promote another owner first.")

        target_member.role = role_in.role
        if role_in.title is not None:
            target_member.title = role_in.title
        target_member.updated_at = utc_now()

        db.commit()
        db.refresh(target_member)
        return target_member

    def remove_member(self, db: Session, team_id: int, target_user_id: int, current_user: User) -> bool:
        """Remove member from team with last-owner protection."""
        team, caller_role = self.require_team_access(db, team_id, current_user, min_role="MEMBER")

        # Allow self-departure or require ADMIN/OWNER
        is_self = (target_user_id == current_user.id)
        if not is_self and caller_role not in ["OWNER", "ADMIN"]:
            raise PermissionError("Insufficient permissions to remove other members")

        target_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == target_user_id
        ).first()

        if not target_member:
            raise ValueError("Team member not found")

        # Last-owner protection
        if target_member.role == "OWNER":
            other_owners = db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id != target_user_id,
                TeamMember.role == "OWNER",
                TeamMember.status == "ACTIVE"
            ).count()
            if other_owners == 0:
                raise ValueError("Cannot remove the last owner of the team")

        db.delete(target_member)
        db.commit()
        return True

    # ---------------------------------------------------------
    # Team Invitations Lifecycle
    # ---------------------------------------------------------
    def create_invitation(
        self,
        db: Session,
        team_id: int,
        current_user: User,
        invite_in: TeamInvitationCreate,
    ) -> Tuple[TeamInvitation, str]:
        """Create a secure team invitation and return (TeamInvitation, raw_token)."""
        team, _ = self.require_team_access(db, team_id, current_user, min_role="ADMIN")

        email_clean = invite_in.email.strip().lower()

        # Check if already a member
        existing_user = db.query(User).filter(func.lower(User.email) == email_clean).first()
        if existing_user:
            m = db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == existing_user.id,
                TeamMember.status == "ACTIVE"
            ).first()
            if m:
                raise ValueError(f"User {email_clean} is already a member of this team")

        # Check pending invitation
        pending = db.query(TeamInvitation).filter(
            TeamInvitation.team_id == team_id,
            func.lower(TeamInvitation.invitee_email) == email_clean,
            TeamInvitation.status == "PENDING",
            TeamInvitation.expires_at > utc_now()
        ).first()
        if pending:
            raise ValueError(f"A pending invitation for {email_clean} already exists")

        # Generate secure token
        raw_token = secrets.token_urlsafe(32)
        token_hashed = hash_token(raw_token)

        invitation = TeamInvitation(
            team_id=team_id,
            organization_id=team.organization_id,
            workspace_id=team.workspace_id,
            inviter_id=current_user.id,
            invitee_email=email_clean,
            invitee_user_id=existing_user.id if existing_user else None,
            role=invite_in.role,
            token_hash=token_hashed,
            status="PENDING",
            expires_at=utc_now() + timedelta(days=7),
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation, raw_token

    def list_invitations(
        self,
        db: Session,
        team_id: int,
        current_user: User,
        status: Optional[str] = None,
    ) -> List[TeamInvitation]:
        """List team invitations for authorized administrators."""
        self.require_team_access(db, team_id, current_user, min_role="ADMIN")
        query = db.query(TeamInvitation).filter(TeamInvitation.team_id == team_id)
        if status:
            query = query.filter(TeamInvitation.status == status.upper())
        return query.order_by(TeamInvitation.created_at.desc()).all()

    def accept_invitation(self, db: Session, raw_token: str, current_user: User) -> TeamMember:
        """Accept team invitation, verifying token and creating team membership."""
        token_hashed = hash_token(raw_token)
        invitation = db.query(TeamInvitation).filter(
            TeamInvitation.token_hash == token_hashed
        ).first()

        if not invitation:
            raise ValueError("Invalid invitation token")

        if invitation.status != "PENDING":
            raise ValueError(f"Invitation is no longer pending (current status: {invitation.status})")

        expires_at = invitation.expires_at
        if expires_at and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        if expires_at and expires_at < datetime.utcnow():
            invitation.status = "EXPIRED"
            db.commit()
            raise ValueError("Invitation has expired")

        # Verify email match if invitee was targeted
        if invitation.invitee_email and invitation.invitee_email.lower() != current_user.email.lower():
            # Allow acceptance if user belongs to same organization
            org_member = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == invitation.organization_id,
                OrganizationMember.user_id == current_user.id
            ).first()
            if not org_member:
                raise ValueError("Invitation was issued to a different email address")

        # Ensure user belongs to the team's organization
        org_member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == current_user.id
        ).first()
        if not org_member:
            # Auto-join organization as member
            org_member = OrganizationMember(
                organization_id=invitation.organization_id,
                user_id=current_user.id,
                role="member",
                joined_at=utc_now()
            )
            db.add(org_member)

        # Create or reactivate TeamMember
        member = db.query(TeamMember).filter(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == current_user.id
        ).first()

        if member:
            member.status = "ACTIVE"
            member.role = invitation.role
            member.updated_at = utc_now()
        else:
            member = TeamMember(
                team_id=invitation.team_id,
                user_id=current_user.id,
                role=invitation.role,
                status="ACTIVE",
                joined_at=utc_now(),
                invited_by_id=invitation.inviter_id,
            )
            db.add(member)

        invitation.status = "ACCEPTED"
        invitation.accepted_at = utc_now()
        invitation.invitee_user_id = current_user.id

        db.commit()
        db.refresh(member)
        return member

    def decline_invitation(self, db: Session, raw_token: str, current_user: User) -> bool:
        """Decline team invitation."""
        token_hashed = hash_token(raw_token)
        invitation = db.query(TeamInvitation).filter(TeamInvitation.token_hash == token_hashed).first()
        if not invitation:
            raise ValueError("Invalid invitation token")

        if invitation.status != "PENDING":
            raise ValueError(f"Invitation cannot be declined (status: {invitation.status})")

        invitation.status = "DECLINED"
        invitation.updated_at = utc_now()
        db.commit()
        return True

    def revoke_invitation(self, db: Session, team_id: int, invitation_id: int, current_user: User) -> bool:
        """Revoke a pending team invitation."""
        self.require_team_access(db, team_id, current_user, min_role="ADMIN")
        invitation = db.query(TeamInvitation).filter(
            TeamInvitation.id == invitation_id,
            TeamInvitation.team_id == team_id
        ).first()

        if not invitation:
            raise ValueError("Invitation not found")

        invitation.status = "REVOKED"
        invitation.revoked_at = utc_now()
        db.commit()
        return True

    def resend_invitation(self, db: Session, team_id: int, invitation_id: int, current_user: User) -> Tuple[TeamInvitation, str]:
        """Extend expiration and generate fresh token for pending invitation."""
        self.require_team_access(db, team_id, current_user, min_role="ADMIN")
        invitation = db.query(TeamInvitation).filter(
            TeamInvitation.id == invitation_id,
            TeamInvitation.team_id == team_id
        ).first()

        if not invitation:
            raise ValueError("Invitation not found")

        raw_token = secrets.token_urlsafe(32)
        invitation.token_hash = hash_token(raw_token)
        invitation.status = "PENDING"
        invitation.expires_at = utc_now() + timedelta(days=7)
        invitation.updated_at = utc_now()

        db.commit()
        db.refresh(invitation)
        return invitation, raw_token

team_service = TeamService()
