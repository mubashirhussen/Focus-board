from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Compliance Control Schemas ---
class ComplianceControlBase(BaseModel):
    control_id: str = Field(..., description="e.g. CC6.1, A.9.1, GDPR-Art32")
    title: str
    description: str
    framework: str = Field(..., description="SOC2, ISO27001, or GDPR")
    category: str = Field(..., description="ACCESS_CONTROL, ENCRYPTION, INCIDENT_RESPONSE, etc.")
    owner_id: Optional[int] = None
    status: str = Field(default="NOT_ASSESSED", description="NOT_ASSESSED, NOT_IMPLEMENTED, PARTIALLY_IMPLEMENTED, IMPLEMENTED, NEEDS_REVIEW, NOT_APPLICABLE")
    risk_level: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    remediation_notes: Optional[str] = None
    next_review_at: Optional[datetime] = None

class ComplianceControlCreate(ComplianceControlBase):
    pass

class ComplianceControlUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    risk_level: Optional[str] = None
    remediation_notes: Optional[str] = None
    next_review_at: Optional[datetime] = None

class ComplianceControlResponse(ComplianceControlBase):
    id: str
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)

# --- Compliance Evidence Schemas ---
class ComplianceEvidenceBase(BaseModel):
    name: str
    description: Optional[str] = None
    evidence_type: str = Field(..., description="CONFIG_RECORD, AUDIT_LOG, POLICY_DOCUMENT, TEST_REPORT, SCREENSHOT")
    file_url: Optional[str] = None
    content_text: Optional[str] = None
    status: str = Field(default="VALIDATED", description="VALIDATED, PENDING_REVIEW, REJECTED, EXPIRED")
    expires_at: Optional[datetime] = None

class ComplianceEvidenceCreate(ComplianceEvidenceBase):
    control_id: str

class ComplianceEvidenceResponse(ComplianceEvidenceBase):
    id: str
    control_id: str
    uploaded_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Security Policy Schemas ---
class SecurityPolicyBase(BaseModel):
    policy_key: str = Field(..., description="e.g. access_control_policy, incident_response_policy")
    title: str
    category: str = Field(..., description="GOVERNANCE, ACCESS, ENCRYPTION, INCIDENT")
    version: str = Field(default="1.0")
    content: str
    status: str = Field(default="DRAFT", description="DRAFT, UNDER_REVIEW, APPROVED, PUBLISHED, ARCHIVED")

class SecurityPolicyCreate(SecurityPolicyBase):
    pass

class SecurityPolicyUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class SecurityPolicyResponse(SecurityPolicyBase):
    id: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    review_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    acknowledgment_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class PolicyAcknowledgmentCreate(BaseModel):
    version: str

class PolicyAcknowledgmentResponse(BaseModel):
    id: str
    policy_id: str
    user_id: int
    version: str
    acknowledged_at: datetime
    ip_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- Security Risk Item Schemas ---
class SecurityRiskItemBase(BaseModel):
    risk_code: str = Field(..., description="e.g. RSK-001")
    title: str
    description: str
    category: str = Field(..., description="APP_SEC, INFRASTRUCTURE, DATA_PROTECTION, PRIVACY, AI_SECURITY, VENDOR")
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    likelihood: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    impact: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    mitigation_plan: Optional[str] = None
    status: str = Field(default="IDENTIFIED", description="IDENTIFIED, UNDER_ASSESSMENT, MITIGATION_PLANNED, IN_PROGRESS, ACCEPTED, RESOLVED, CLOSED")
    owner_id: Optional[int] = None

class SecurityRiskItemCreate(SecurityRiskItemBase):
    pass

class SecurityRiskItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    likelihood: Optional[str] = None
    impact: Optional[str] = None
    mitigation_plan: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None

class SecurityRiskItemResponse(SecurityRiskItemBase):
    id: str
    risk_score: int
    review_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Security Incident Schemas ---
class SecurityIncidentBase(BaseModel):
    incident_code: str = Field(..., description="e.g. INC-2026-001")
    title: str
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    category: str = Field(default="UNAUTHORIZED_ACCESS", description="UNAUTHORIZED_ACCESS, DATA_EXPOSURE, API_ABUSE, PRIVACY_BREACH, MALWARE, AI_EXPLOIT")
    status: str = Field(default="DETECTED", description="DETECTED, TRIAGE, INVESTIGATING, CONTAINMENT, RECOVERY, RESOLVED, CLOSED")
    summary: str
    owner_id: Optional[int] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None

class SecurityIncidentCreate(SecurityIncidentBase):
    pass

class SecurityIncidentUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None

class SecurityIncidentResponse(SecurityIncidentBase):
    id: str
    detected_at: datetime
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Vendor Risk Schemas ---
class SecurityVendorBase(BaseModel):
    name: str
    service_type: str = Field(..., description="CLOUD_HOSTING, AI_PROVIDER, PAYMENT_GATEWAY, EMAIL_SERVICE, ANALYTICS")
    data_classification: str = Field(default="CONFIDENTIAL", description="PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED")
    risk_rating: str = Field(default="LOW", description="LOW, MEDIUM, HIGH")
    security_contact: Optional[str] = None
    status: str = Field(default="ACTIVE", description="ACTIVE, UNDER_REVIEW, TERMINATED")

class SecurityVendorCreate(SecurityVendorBase):
    pass

class SecurityVendorUpdate(BaseModel):
    service_type: Optional[str] = None
    data_classification: Optional[str] = None
    risk_rating: Optional[str] = None
    security_contact: Optional[str] = None
    status: Optional[str] = None

class SecurityVendorResponse(SecurityVendorBase):
    id: str
    review_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Privacy Request Schemas ---
class PrivacyRequestBase(BaseModel):
    request_type: str = Field(..., description="ACCESS, EXPORT, DELETION, RECTIFICATION")
    requester_email: str
    details: Optional[str] = None
    status: str = Field(default="RECEIVED", description="RECEIVED, VERIFYING, IN_PROGRESS, COMPLETED, REJECTED")
    rejection_reason: Optional[str] = None

class PrivacyRequestCreate(PrivacyRequestBase):
    user_id: Optional[int] = None

class PrivacyRequestUpdate(BaseModel):
    status: Optional[str] = None
    details: Optional[str] = None
    rejection_reason: Optional[str] = None

class PrivacyRequestResponse(PrivacyRequestBase):
    id: str
    user_id: Optional[int] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Trust Center Schemas ---
class TrustCenterDocumentBase(BaseModel):
    title: str
    slug: str
    category: str = Field(..., description="OVERVIEW, ENCRYPTION, SOC2, ISO27001, PRIVACY, BUSINESS_CONTINUITY, SUBPROCESSORS")
    summary: str
    content: str
    is_public: bool = True
    version: str = Field(default="1.0")

class TrustCenterDocumentCreate(TrustCenterDocumentBase):
    pass

class TrustCenterDocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None
    version: Optional[str] = None

class TrustCenterDocumentResponse(TrustCenterDocumentBase):
    id: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FrameworkReadiness(BaseModel):
    framework: str
    total_controls: int
    implemented_controls: int
    in_progress_controls: int
    readiness_percentage: float

class SecurityComplianceOverviewResponse(BaseModel):
    total_controls: int
    implemented_controls: int
    in_progress_controls: int
    not_started_controls: int
    overall_readiness_percentage: float
    frameworks: List[FrameworkReadiness]
    active_risks_count: int
    critical_risks_count: int
    open_incidents_count: int
    pending_privacy_requests_count: int
    approved_policies_count: int
    verified_vendors_count: int

class TrustCenterOverviewResponse(BaseModel):
    status: str = "OPERATIONAL"
    posture_statement: str
    encryption_in_transit: str = "TLS 1.3 / HTTPS (ECDHE-RSA-AES128-GCM-SHA256)"
    encryption_at_rest: str = "AES-256 GCM authenticated encryption"
    mfa_enforced: bool = True
    soc2_readiness_percentage: float
    iso27001_readiness_percentage: float
    gdpr_readiness_percentage: float
    public_documents: List[TrustCenterDocumentResponse]
    approved_subprocessors: List[Dict[str, Any]]
