import json
import csv
import io
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request

from app.models.enterprise import OrganizationPolicy, CustomRole, OrganizationDomain, EnterpriseInvitation
from app.models.audit import AuditLog
from app.models.user import User
from app.services.audit_service import record_audit_log

DEFAULT_POLICIES = {
    "mfa_required": {"enabled": False, "is_enabled": False, "grace_period_days": 14},
    "mfa_enforced": {"enabled": False, "is_enabled": False, "grace_period_days": 14},
    "domain_restriction": {"enabled": False, "is_enabled": False, "allowed_domains": []},
    "workspace_creation": {"restricted_to_admins": False},
    "ai_governance": {"enabled": True, "is_enabled": True, "strict_review_required": True, "zero_retention": True},
    "ai_data_privacy_zero_retention": {"enabled": True, "is_enabled": True, "zero_retention": True},
    "export_policy": {"allow_data_export": True},
}

SYNONYMOUS_POLICIES = {
    "mfa_enforced": "mfa_required",
    "mfa_required": "mfa_enforced",
    "ai_governance": "ai_data_privacy_zero_retention",
    "ai_data_privacy_zero_retention": "ai_governance",
}

class EnterpriseService:
    def get_policies(self, db: Session, tenant_id: str) -> Dict[str, Any]:
        records = db.query(OrganizationPolicy).filter(OrganizationPolicy.tenant_id == tenant_id).all()
        policies = {k: dict(v) for k, v in DEFAULT_POLICIES.items()}
        for r in records:
            val = json.loads(r.policy_value_json) if r.policy_value_json else {}
            # Ensure both enabled and is_enabled are normalized
            is_en = val.get("is_enabled", val.get("enabled", False))
            val["is_enabled"] = is_en
            val["enabled"] = is_en
            policies[r.policy_type] = val

            # Keep synonymous keys in sync
            syn = SYNONYMOUS_POLICIES.get(r.policy_type)
            if syn and syn not in policies:
                policies[syn] = dict(val)

        return policies

    def update_policy(self, db: Session, tenant_id: str, policy_type: str, policy_value: Dict[str, Any], user_id: int):
        # Normalize enabled/is_enabled
        is_en = policy_value.get("is_enabled", policy_value.get("enabled", False))
        policy_value["is_enabled"] = is_en
        policy_value["enabled"] = is_en

        now = datetime.now(timezone.utc)
        keys_to_update = [policy_type]
        syn = SYNONYMOUS_POLICIES.get(policy_type)
        if syn and syn not in keys_to_update:
            keys_to_update.append(syn)

        for p_key in keys_to_update:
            record = db.query(OrganizationPolicy).filter(
                OrganizationPolicy.tenant_id == tenant_id,
                OrganizationPolicy.policy_type == p_key
            ).first()

            if record:
                record.policy_value_json = json.dumps(policy_value)
                record.updated_by = user_id
                record.updated_at = now
            else:
                record = OrganizationPolicy(
                    tenant_id=tenant_id,
                    policy_type=p_key,
                    policy_value_json=json.dumps(policy_value),
                    updated_by=user_id,
                    updated_at=now,
                )
                db.add(record)

        db.commit()

        # Audit log the policy modification
        record_audit_log(
            db=db,
            event_type="POLICY_UPDATE",
            actor_id=user_id,
            resource_type="GOVERNANCE_POLICY",
            resource_id=policy_type,
            metadata={"new_value": policy_value}
        )

    def is_mfa_enforced(self, db: Session, tenant_id: str) -> bool:
        """Check whether MFA is currently mandated by tenant policy."""
        policies = self.get_policies(db, tenant_id)
        mfa_pol = policies.get("mfa_enforced") or policies.get("mfa_required") or {}
        return bool(mfa_pol.get("is_enabled") or mfa_pol.get("enabled"))

    def is_domain_restriction_enforced(self, db: Session, tenant_id: str) -> bool:
        """Check whether corporate domain restrictions are active."""
        policies = self.get_policies(db, tenant_id)
        dom_pol = policies.get("domain_restriction") or {}
        return bool(dom_pol.get("is_enabled") or dom_pol.get("enabled"))

    def is_ai_zero_retention_enforced(self, db: Session, tenant_id: str) -> bool:
        """Check whether AI data zero-retention is enforced."""
        policies = self.get_policies(db, tenant_id)
        ai_pol = policies.get("ai_governance") or policies.get("ai_data_privacy_zero_retention") or {}
        return bool(ai_pol.get("zero_retention") or ai_pol.get("is_enabled") or ai_pol.get("enabled"))

    def create_invitation(
        self,
        db: Session,
        tenant_id: str,
        email: str,
        role: str,
        inviter_id: int
    ) -> EnterpriseInvitation:
        """Create enterprise invitation with corporate domain enforcement."""
        email_clean = email.strip().lower()
        if "@" not in email_clean:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address format.")

        domain_part = email_clean.split("@")[1]

        # Enforce corporate domain restriction if enabled
        if self.is_domain_restriction_enforced(db, tenant_id):
            verified_domains = db.query(OrganizationDomain).filter(
                OrganizationDomain.tenant_id == tenant_id,
                OrganizationDomain.is_verified == True
            ).all()

            allowed = [d.domain.lower() for d in verified_domains]
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Corporate Domain Restriction is active, but no verified corporate domains exist. Add and verify a domain first."
                )
            if domain_part not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invitation rejected: domain '@{domain_part}' does not match any approved, verified corporate domains ({', '.join(allowed)})."
                )

        now = datetime.now(timezone.utc)
        invitation = EnterpriseInvitation(
            tenant_id=tenant_id,
            email=email_clean,
            role=role,
            status="PENDING",
            token=f"inv-{secrets.token_hex(16)}",
            created_by=inviter_id,
            created_at=now,
            expires_at=now + timedelta(days=7),
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    def list_invitations(self, db: Session, tenant_id: str) -> List[EnterpriseInvitation]:
        return db.query(EnterpriseInvitation).filter(EnterpriseInvitation.tenant_id == tenant_id).all()

    def add_domain(self, db: Session, tenant_id: str, domain: str) -> OrganizationDomain:
        token = f"focusboard-verify-{secrets.token_hex(16)}"
        now = datetime.now(timezone.utc)
        domain_rec = OrganizationDomain(
            tenant_id=tenant_id,
            domain=domain.lower().strip(),
            verification_token=token,
            is_verified=False,
            created_at=now,
        )
        db.add(domain_rec)
        db.commit()
        db.refresh(domain_rec)
        return domain_rec

    def verify_domain(self, db: Session, tenant_id: str, domain_id: int) -> bool:
        rec = db.query(OrganizationDomain).filter(
            OrganizationDomain.id == domain_id,
            OrganizationDomain.tenant_id == tenant_id
        ).first()
        if not rec:
            return False
        rec.is_verified = True
        rec.verified_at = datetime.now(timezone.utc)
        db.commit()
        return True

    def export_audit_logs_csv(
        self,
        db: Session,
        actor_user: User,
        request: Optional[Request] = None
    ) -> str:
        """Generate sanitized compliance audit export in CSV format."""
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Event ID", "Actor ID", "Event Type", "Resource Type", "Resource ID", "IP Address", "Timestamp"])

        for l in logs:
            writer.writerow([
                l.id,
                l.actor_id or "System",
                l.event_type,
                l.resource_type or "",
                l.resource_id or "",
                l.ip_address or "127.0.0.1",
                l.created_at.isoformat() if l.created_at else ""
            ])

        # Log audit of the export itself
        record_audit_log(
            db=db,
            event_type="AUDIT_EXPORT_CSV",
            actor_id=actor_user.id,
            resource_type="AUDIT_LOG",
            request=request,
            metadata={"exported_count": len(logs)}
        )

        return output.getvalue()

enterprise_service = EnterpriseService()
