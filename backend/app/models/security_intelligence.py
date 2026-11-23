import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# 1. Centralized Security Event Registry
class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String(64), primary_key=True, default=lambda: f"sev_{uuid.uuid4().hex[:12]}")
    event_type = Column(String(64), nullable=False, index=True)
    # LOGIN_SUCCESS, LOGIN_FAILURE, MFA_ENABLED, MFA_DISABLED, PASSWORD_RESET,
    # SESSION_REVOKED, USER_INVITED, USER_ROLE_CHANGED, PRIVILEGED_ACCESS_GRANTED,
    # PRIVILEGED_ACCESS_REVOKED, API_KEY_CREATED, API_KEY_REVOKED, OAUTH_CONNECTION_CREATED,
    # WEBHOOK_CREATED, SECURITY_POLICY_CHANGED, ACCESS_REVIEW_COMPLETED, SUSPICIOUS_ACTIVITY
    severity = Column(String(32), default="INFO", nullable=False, index=True) # INFO, LOW, MEDIUM, HIGH, CRITICAL
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    target_entity = Column(String(255), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(String(64), nullable=True)
    source = Column(String(64), default="SYSTEM", nullable=False) # SYSTEM, AUTH, API, RBAC, INTEGRATION, AUTOMATION
    evidence_json = Column(Text, server_default="{}", nullable=False)
    metadata_json = Column(Text, server_default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    actor = relationship("User", foreign_keys=[actor_id])

# 2. Configurable Threat Detection Rules
class SecurityDetectionRule(Base):
    __tablename__ = "security_detection_rules"

    id = Column(String(64), primary_key=True, default=lambda: f"srule_{uuid.uuid4().hex[:12]}")
    rule_code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    condition_expression = Column(String(255), nullable=False)
    threshold_count = Column(Integer, default=5, nullable=False)
    time_window_seconds = Column(Integer, default=300, nullable=False)
    severity = Column(String(32), default="HIGH", nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

# 3. Detection Engine Results
class SecurityDetectionResult(Base):
    __tablename__ = "security_detection_results"

    id = Column(String(64), primary_key=True, default=lambda: f"sres_{uuid.uuid4().hex[:12]}")
    rule_id = Column(String(64), ForeignKey("security_detection_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = Column(String(64), nullable=False)
    severity = Column(String(32), default="HIGH", nullable=False)
    matched_count = Column(Integer, default=1, nullable=False)
    target_entity = Column(String(255), nullable=True)
    evidence_summary = Column(Text, nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)

    rule = relationship("SecurityDetectionRule")

# 4. Centralized Security Alerts
class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id = Column(String(64), primary_key=True, default=lambda: f"salt_{uuid.uuid4().hex[:12]}")
    alert_code = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), default="HIGH", nullable=False, index=True) # INFO, LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), default="OPEN", nullable=False, index=True) # OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, DISMISSED
    source = Column(String(64), default="THREAT_DETECTION", nullable=False)
    detection_rule_id = Column(String(64), ForeignKey("security_detection_rules.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_email = Column(String(255), nullable=True)
    target_entity = Column(String(255), nullable=True)
    evidence_json = Column(Text, server_default="{}", nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

# 5. Identity Risk Records
class IdentityRiskRecord(Base):
    __tablename__ = "identity_risk_records"

    id = Column(String(64), primary_key=True, default=lambda: f"irsk_{uuid.uuid4().hex[:12]}")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_type = Column(String(64), nullable=False, index=True)
    # EXCESSIVE_FAILED_LOGINS, UNUSUAL_ACCESS_PATTERN, UNPROTECTED_ADMIN_NO_MFA, PRIVILEGED_ESCALATION, API_KEY_ABUSE, INACTIVE_PRIVILEGED_ACCOUNT
    severity = Column(String(32), default="MEDIUM", nullable=False)
    risk_score = Column(Integer, default=50, nullable=False) # 0 to 100
    status = Column(String(32), default="ACTIVE", nullable=False, index=True) # ACTIVE, MITIGATED, DISMISSED
    details = Column(Text, nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User")

# 6. Access Review Campaigns
class AccessReviewCampaign(Base):
    __tablename__ = "access_review_campaigns"

    id = Column(String(64), primary_key=True, default=lambda: f"arc_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    scope_type = Column(String(64), nullable=False) # ORGANIZATION, WORKSPACE, PRIVILEGED_ROLES, INTEGRATIONS, API_KEYS
    status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, IN_PROGRESS, APPROVED, REJECTED, COMPLETED
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deadline_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    reviewer = relationship("User", foreign_keys=[reviewer_id])
    records = relationship("AccessReviewRecord", back_populates="campaign", cascade="all, delete-orphan")

# 7. Access Review Records
class AccessReviewRecord(Base):
    __tablename__ = "access_review_records"

    id = Column(String(64), primary_key=True, default=lambda: f"arr_{uuid.uuid4().hex[:12]}")
    campaign_id = Column(String(64), ForeignKey("access_review_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_or_permission = Column(String(128), nullable=False)
    resource_name = Column(String(128), nullable=False)
    decision = Column(String(32), default="PENDING", nullable=False) # PENDING, APPROVED, REVOKED, ESCALATED
    justification = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    campaign = relationship("AccessReviewCampaign", back_populates="records")
    user = relationship("User", foreign_keys=[user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

# 8. Vulnerability Records
class VulnerabilityRecord(Base):
    __tablename__ = "vulnerability_records"

    id = Column(String(64), primary_key=True, default=lambda: f"vuln_{uuid.uuid4().hex[:12]}")
    cve_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    component = Column(String(128), nullable=False)
    severity = Column(String(32), default="MEDIUM", nullable=False, index=True) # INFORMATIONAL, LOW, MEDIUM, HIGH, CRITICAL
    source = Column(String(64), default="DEPENDENCY_SCAN", nullable=False) # DEPENDENCY_SCAN, CONTAINER_SCAN, STATIC_ANALYSIS, CODE_REVIEW, PENETRATION_TEST
    remediation_status = Column(String(32), default="OPEN", nullable=False, index=True) # OPEN, ASSIGNED, IN_PROGRESS, BLOCKED, RESOLVED, VERIFIED, CLOSED
    remediation_owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    remediation_owner = relationship("User", foreign_keys=[remediation_owner_id])

# 9. Security Posture Assessment
class SecurityPostureAssessment(Base):
    __tablename__ = "security_posture_assessments"

    id = Column(String(64), primary_key=True, default=lambda: f"spa_{uuid.uuid4().hex[:12]}")
    assessment_date = Column(DateTime, default=utc_now, nullable=False)
    overall_score = Column(Integer, default=85, nullable=False) # 0 to 100
    category_scores_json = Column(Text, server_default="{}", nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    assessed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    summary = Column(Text, nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    findings = relationship("SecurityPostureFinding", back_populates="assessment", cascade="all, delete-orphan")

# 10. Security Posture Findings
class SecurityPostureFinding(Base):
    __tablename__ = "security_posture_findings"

    id = Column(String(64), primary_key=True, default=lambda: f"spf_{uuid.uuid4().hex[:12]}")
    assessment_id = Column(String(64), ForeignKey("security_posture_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(64), nullable=False) # AUTHENTICATION, MFA, RBAC, TENANT_ISOLATION, API_SECURITY, DATA_PROTECTION, AUDITING, SECRET_MANAGEMENT, AI_SECURITY
    title = Column(String(255), nullable=False)
    severity = Column(String(32), default="MEDIUM", nullable=False)
    control_ref = Column(String(64), nullable=False)
    remediation_guidance = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)

    assessment = relationship("SecurityPostureAssessment", back_populates="findings")

# 11. Security Remediation Action Items
class SecurityRemediation(Base):
    __tablename__ = "security_remediations"

    id = Column(String(64), primary_key=True, default=lambda: f"srem_{uuid.uuid4().hex[:12]}")
    finding_type = Column(String(64), nullable=False) # VULNERABILITY, POSTURE_FINDING, INCIDENT_ACTION, AUDIT_FINDING
    finding_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    priority = Column(String(32), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), default="OPEN", nullable=False, index=True) # OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, VERIFIED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    verified_at = Column(DateTime, nullable=True)

# 12. Zero Trust Policies
class ZeroTrustPolicy(Base):
    __tablename__ = "zero_trust_policies"

    id = Column(String(64), primary_key=True, default=lambda: f"ztp_{uuid.uuid4().hex[:12]}")
    name = Column(String(128), nullable=False)
    policy_type = Column(String(64), nullable=False, index=True)
    # MFA_ENFORCEMENT, IP_ALLOWLIST, SESSION_TIMEOUT, RISK_THRESHOLD, LEAST_PRIVILEGE
    target_resource = Column(String(128), default="*", nullable=False)
    conditions_json = Column(Text, server_default="{}", nullable=False)
    action = Column(String(32), default="BLOCK", nullable=False) # BLOCK, REQUIRE_MFA, AUDIT_ONLY, ALLOW
    is_enabled = Column(Boolean, default=True, nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

# 13. Zero Trust Access Evaluations
class ZeroTrustEvaluation(Base):
    __tablename__ = "zero_trust_evaluations"

    id = Column(String(64), primary_key=True, default=lambda: f"zte_{uuid.uuid4().hex[:12]}")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resource = Column(String(128), nullable=False)
    action_requested = Column(String(64), nullable=False)
    decision = Column(String(32), nullable=False) # ALLOW, DENY, REQUIRE_MFA
    risk_score = Column(Integer, default=0, nullable=False)
    reasons_json = Column(Text, server_default="[]", nullable=False)
    context_json = Column(Text, server_default="{}", nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    evaluated_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
