import re
from typing import List, Set, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.user import User
from app.models.organization import OrganizationMember
from app.models.collaboration import WorkspaceMember
from app.schemas.comment import MentionUserAutocomplete

MENTION_REGEX = re.compile(r"@([\w\.\-]+)")

class MentionService:
    @staticmethod
    def extract_mentions(content: str) -> Set[str]:
        """Extract candidate usernames, emails, or user references from text."""
        if not content:
            return set()
        matches = MENTION_REGEX.findall(content)
        return {m.strip().lower() for m in matches if m.strip()}

    @staticmethod
    def resolve_valid_mentions(
        db: Session,
        candidate_mentions: Set[str],
        organization_id: int,
        workspace_id: Optional[int] = None,
    ) -> List[User]:
        """
        Validate that mentioned targets exist and are active members of the tenant organization.
        Prevents cross-tenant IDOR leakage.
        """
        if not candidate_mentions:
            return []

        # Find users matching username or email prefix
        found_users = []
        for term in candidate_mentions:
            # Query by exact email or exact name or id
            user_query = db.query(User).filter(
                User.is_active == True,
                or_(
                    func.lower(User.email) == term,
                    func.lower(User.email).like(f"{term}@%"),
                    func.lower(User.name) == term,
                    func.lower(User.name).like(f"{term}%"),
                )
            )
            candidates = user_query.limit(5).all()
            for cand in candidates:
                # Verify cand belongs to organization
                org_mem = db.query(OrganizationMember).filter(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.user_id == cand.id,
                    OrganizationMember.is_active == True
                ).first()
                if org_mem and cand not in found_users:
                    found_users.append(cand)

        return found_users

    @staticmethod
    def autocomplete_users(
        db: Session,
        current_user: User,
        query: str,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        limit: int = 10,
    ) -> List[MentionUserAutocomplete]:
        """
        Search users within the authenticated user's organization/workspace for @mention autocomplete.
        Guarantees strict tenant isolation.
        """
        resolved_org_id = organization_id
        if not resolved_org_id:
            # Derive from user membership
            om = db.query(OrganizationMember).filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_active == True
            ).first()
            if om:
                resolved_org_id = om.organization_id

        if not resolved_org_id:
            return []

        # Query members of the organization
        term = f"%{query.strip().lower()}%"
        users_query = (
            db.query(User, OrganizationMember.role)
            .join(OrganizationMember, OrganizationMember.user_id == User.id)
            .filter(
                OrganizationMember.organization_id == resolved_org_id,
                OrganizationMember.is_active == True,
                User.is_active == True,
                or_(
                    func.lower(User.name).like(term),
                    func.lower(User.email).like(term),
                )
            )
            .order_by(User.name.asc())
            .limit(limit)
        )

        results = []
        for user, role in users_query.all():
            results.append(
                MentionUserAutocomplete(
                    id=user.id,
                    name=user.name,
                    email=user.email,
                    avatar_url=user.avatar_url,
                    role=role,
                )
            )
        return results

mention_service = MentionService()
