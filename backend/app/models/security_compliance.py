import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ComplianceControl(Base):
    __tablename__ = "compliance_controls"

    id = Column(String(64), primary_key=True, default=lambda: f"ctl_{uuid.uuid4().hex[:12]}")
    control_id = Column(String(64), nullable=False, index=True)  # e.g., CC6.1, A.9.1, GDPR-Art32
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    framework = Column(String(32), nullable=False, index=True)  # SOC2, ISO27001, GDPR
    category = Column(String(64), nullable=False, index=True)  # ACCESS_CONTROL, ENCRYPTION, INCIDENT_RESPONSE, etc.
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), default="NOT_ASSESSED", nullable=False, index=True)
    # NOT_ASSESSED, NOT_IMPLEMENTED, PARTIALLY_IMPLEMENTED, IMPLEMENTED, NEEDS_REVIEW, NOT_APPLICABLE
    risk_level = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    remediation_notes = Column(Text, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    evidences = relationship("ComplianceEvidence", back_populates="control", cascade="all, delete-orphan")

class ComplianceEvidence(Base):
    __tablename__ = "compliance_evidences"

    id = Column(String(64), primary_key=True, default=lambda: f"evi_{uuid.uuid4().hex[:12]}")
    control_id = Column(String(64), ForeignKey("compliance_controls.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(String(64), nullable=False)  # CONFIG_RECORD, AUDIT_LOG, POLICY_DOCUMENT, TEST_REPORT, SCREENSHOT
    file_url = Column(String(512), nullable=True)
    content_text = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), default="VALIDATED", nullable=False)  # VALIDATED, PENDING_REVIEW, REJECTED, EXPIRED
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    control = relationship("ComplianceControl", back_populates="evidences")
    uploader = relationship("User", foreign_keys=[uploaded_by])

class SecurityPolicy(Base):
    __tablename__ = "security_policies"

    id = Column(String(64), primary_key=True, default=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    policy_key = Column(String(64), unique=True, nullable=False, index=True)  # e.g., access_control_policy, password_policy
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)  # GOVERNANCE, ACCESS, ENCRYPTION, INCIDENT
    version = Column(String(16), default="1.0", nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(32), default="DRAFT", nullable=False)  # DRAFT, UNDER_REVIEW, APPROVED, PUBLISHED, ARCHIVED
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    review_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    approver = relationship("User", foreign_keys=[approved_by])
    acknowledgments = relationship("PolicyAcknowledgment", back_populates="policy", cascade="all, delete-orphan")

class PolicyAcknowledgment(Base):
    __tablename__ = "policy_acknowledgments"

    id = Column(String(64), primary_key=True, default=lambda: f"ack_{uuid.uuid4().hex[:12]}")
    policy_id = Column(String(64), ForeignKey("security_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(16), nullable=False)
    acknowledged_at = Column(DateTime, default=utc_now, nullable=False)
    ip_address = Column(String(64), nullable=True)

    policy = relationship("SecurityPolicy", back_populates="acknowledgments")
    user = relationship("User")

class SecurityRiskItem(Base):
    __tablename__ = "security_risk_items"

    id = Column(String(64), primary_key=True, default=lambda: f"srisk_{uuid.uuid4().hex[:12]}")
    risk_code = Column(String(64), unique=True, nullable=False, index=True)  # e.g., RSK-001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)  # APP_SEC, INFRASTRUCTURE, DATA_PROTECTION, PRIVACY, AI_SECURITY, VENDOR
    severity = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    likelihood = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH
    impact = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH
    risk_score = Column(Integer, default=50, nullable=False)  # 1 to 100
    mitigation_plan = Column(Text, nullable=True)
    status = Column(String(32), default="IDENTIFIED", nullable=False, index=True)
    # IDENTIFIED, UNDER_ASSESSMENT, MITIGATION_PLANNED, IN_PROGRESS, ACCEPTED, RESOLVED, CLOSED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    review_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])

class SecurityIncident(Base):
    __tablename__ = "security_incidents"

    id = Column(String(64), primary_key=True, default=lambda: f"inc_{uuid.uuid4().hex[:12]}")
    incident_code = Column(String(64), unique=True, nullable=False, index=True)  # e.g., INC-2026-001
    title = Column(String(255), nullable=False)
    severity = Column(String(32), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    category = Column(String(64), nullable=False)  # UNAUTHORIZED_ACCESS, DATA_EXPOSURE, API_ABUSE, PRIVACY_BREACH, MALWARE, AI_EXPLOIT
    status = Column(String(32), default="DETECTED", nullable=False, index=True)
    # DETECTED, TRIAGE, INVESTIGATING, CONTAINMENT, RECOVERY, RESOLVED, CLOSED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    contained_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    corrective_actions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])

class SecurityVendor(Base):
    __tablename__ = "security_vendors"

    id = Column(String(64), primary_key=True, default=lambda: f"vnd_{uuid.uuid4().hex[:12]}")
    name = Column(String(128), nullable=False)
    service_type = Column(String(64), nullable=False)  # CLOUD_HOSTING, AI_PROVIDER, PAYMENT_GATEWAY, EMAIL_SERVICE, ANALYTICS
    data_classification = Column(String(32), default="CONFIDENTIAL", nullable=False)  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    risk_rating = Column(String(32), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH
    security_contact = Column(String(255), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, UNDER_REVIEW, TERMINATED
    review_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class PrivacyRequest(Base):
    __tablename__ = "privacy_requests"

    id = Column(String(64), primary_key=True, default=lambda: f"priv_{uuid.uuid4().hex[:12]}")
    request_type = Column(String(32), nullable=False, index=True)  # ACCESS, EXPORT, DELETION, RECTIFICATION
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), default="RECEIVED", nullable=False, index=True)  # RECEIVED, VERIFYING, IN_PROGRESS, COMPLETED, REJECTED
    requester_email = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])

class TrustCenterDocument(Base):
    __tablename__ = "trust_center_documents"

    id = Column(String(64), primary_key=True, default=lambda: f"tdoc_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)  # OVERVIEW, ENCRYPTION, SOC2, ISO27001, PRIVACY, BUSINESS_CONTINUITY, SUBPROCESSORS
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    version = Column(String(16), default="1.0", nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
