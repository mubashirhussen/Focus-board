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
    "mfa_required": {"enabled": False, "grace_period_days": 14},
    "domain_restriction": {"enabled": False, "allowed_domains": []},
    "workspace_creation": {"restricted_to_admins": False},
    "ai_governance": {"enabled": True, "strict_review_required": True},
    "export_policy": {"allow_data_export": True},
}

class EnterpriseService:
    def get_policies(self, db: Session, tenant_id: str) -> Dict[str, Any]:
        records = db.query(OrganizationPolicy).filter(OrganizationPolicy.tenant_id == tenant_id).all()
        policies = dict(DEFAULT_POLICIES)
        for r in records:
            policies[r.policy_type] = json.loads(r.policy_value_json) if r.policy_value_json else {}
        return policies

    def update_policy(self, db: Session, tenant_id: str, policy_type: str, policy_value: Dict[str, Any], user_id: int):
        record = db.query(OrganizationPolicy).filter(
            OrganizationPolicy.tenant_id == tenant_id,
            OrganizationPolicy.policy_type == policy_type
        ).first()

        now = datetime.now(timezone.utc)
        if record:
            record.policy_value_json = json.dumps(policy_value)
            record.updated_by = user_id
            record.updated_at = now
        else:
            record = OrganizationPolicy(
                tenant_id=tenant_id,
                policy_type=policy_type,
                policy_value_json=json.dumps(policy_value),
                updated_by=user_id,
                updated_at=now,
            )
            db.add(record)
        db.commit()

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
