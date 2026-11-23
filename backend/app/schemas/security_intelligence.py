from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# Security Event Schemas
class SecurityEventCreate(BaseModel):
    event_type: str
    severity: str = "INFO"
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    target_entity: Optional[str] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    ip_address: Optional[str] = None
    source: str = "SYSTEM"
    evidence_json: Optional[str] = "{}"
    metadata_json: Optional[str] = "{}"

class SecurityEventResponse(BaseModel):
    id: str
    event_type: str
    severity: str
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    target_entity: Optional[str] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    ip_address: Optional[str] = None
    source: str
    evidence_json: str
    metadata_json: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Detection Rule Schemas
class SecurityDetectionRuleCreate(BaseModel):
    rule_code: str
    name: str
    description: str
    event_type: str
    condition_expression: str
    threshold_count: int = 5
    time_window_seconds: int = 300
    severity: str = "HIGH"
    is_enabled: bool = True
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class SecurityDetectionRuleResponse(BaseModel):
    id: str
    rule_code: str
    name: str
    description: str
    event_type: str
    condition_expression: str
    threshold_count: int
    time_window_seconds: int
    severity: str
    is_enabled: bool
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Security Alert Schemas
class SecurityAlertCreate(BaseModel):
    alert_code: str
    title: str
    description: str
    severity: str = "HIGH"
    status: str = "OPEN"
    source: str = "THREAT_DETECTION"
    detection_rule_id: Optional[str] = None
    actor_email: Optional[str] = None
    target_entity: Optional[str] = None
    evidence_json: Optional[str] = "{}"
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class SecurityAlertUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to_id: Optional[int] = None

class SecurityAlertResponse(BaseModel):
    id: str
    alert_code: str
    title: str
    description: str
    severity: str
    status: str
    source: str
    detection_rule_id: Optional[str] = None
    assigned_to_id: Optional[int] = None
    actor_email: Optional[str] = None
    target_entity: Optional[str] = None
    evidence_json: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Identity Risk Schemas
class IdentityRiskRecordCreate(BaseModel):
    user_id: int
    risk_type: str
    severity: str = "MEDIUM"
    risk_score: int = 50
    details: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class IdentityRiskRecordResponse(BaseModel):
    id: str
    user_id: int
    risk_type: str
    severity: str
    risk_score: int
    status: str
    details: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Access Review Campaign Schemas
class AccessReviewCampaignCreate(BaseModel):
    title: str
    scope_type: str
    notes: Optional[str] = None
    deadline_date: Optional[datetime] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class AccessReviewRecordUpdate(BaseModel):
    decision: str
    justification: Optional[str] = None

class AccessReviewRecordResponse(BaseModel):
    id: str
    campaign_id: str
    user_id: int
    role_or_permission: str
    resource_name: str
    decision: str
    justification: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class AccessReviewCampaignResponse(BaseModel):
    id: str
    title: str
    scope_type: str
    status: str
    reviewer_id: Optional[int] = None
    deadline_date: Optional[datetime] = None
    notes: Optional[str] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    records: List[AccessReviewRecordResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Vulnerability Schemas
class VulnerabilityRecordCreate(BaseModel):
    cve_id: str
    title: str
    description: str
    component: str
    severity: str = "MEDIUM"
    source: str = "DEPENDENCY_SCAN"
    remediation_status: str = "OPEN"
    due_date: Optional[datetime] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class VulnerabilityRecordUpdate(BaseModel):
    remediation_status: Optional[str] = None
    remediation_owner_id: Optional[int] = None

class VulnerabilityRecordResponse(BaseModel):
    id: str
    cve_id: str
    title: str
    description: str
    component: str
    severity: str
    source: str
    remediation_status: str
    remediation_owner_id: Optional[int] = None
    due_date: Optional[datetime] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Posture & Findings Schemas
class SecurityPostureFindingResponse(BaseModel):
    id: str
    assessment_id: str
    category: str
    title: str
    severity: str
    control_ref: str
    remediation_guidance: str
    is_resolved: bool

    model_config = ConfigDict(from_attributes=True)

class SecurityPostureAssessmentResponse(BaseModel):
    id: str
    assessment_date: datetime
    overall_score: int
    category_scores_json: str
    status: str
    assessed_by_id: Optional[int] = None
    summary: str
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_at: datetime
    findings: List[SecurityPostureFindingResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Remediation Schemas
class SecurityRemediationCreate(BaseModel):
    finding_type: str
    finding_id: str
    title: str
    priority: str = "MEDIUM"
    due_date: Optional[datetime] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class SecurityRemediationUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None

class SecurityRemediationResponse(BaseModel):
    id: str
    finding_type: str
    finding_id: str
    title: str
    priority: str
    status: str
    owner_id: Optional[int] = None
    due_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_at: datetime
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Zero Trust Schemas
class ZeroTrustPolicyCreate(BaseModel):
    name: str
    policy_type: str
    target_resource: str = "*"
    conditions_json: Optional[str] = "{}"
    action: str = "BLOCK"
    is_enabled: bool = True
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class ZeroTrustPolicyUpdate(BaseModel):
    name: Optional[str] = None
    target_resource: Optional[str] = None
    action: Optional[str] = None
    is_enabled: Optional[bool] = None
    conditions_json: Optional[str] = None

class ZeroTrustPolicyResponse(BaseModel):
    id: str
    name: str
    policy_type: str
    target_resource: str
    conditions_json: str
    action: str
    is_enabled: bool
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ZeroTrustEvaluationRequest(BaseModel):
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    resource: str
    action_requested: str = "ACCESS"
    ip_address: Optional[str] = None
    mfa_authenticated: bool = False
    context_data: Optional[Dict[str, Any]] = None
    workspace_id: Optional[int] = None

class ZeroTrustEvaluationResponse(BaseModel):
    id: str
    decision: str  # ALLOW, DENY, REQUIRE_MFA
    risk_score: int
    reasons: List[str] = []
    matched_policies: List[str] = []
    context: Dict[str, Any] = {}
    evaluated_at: datetime

# Containment & Threat Scan Schemas
class ContainmentActionRequest(BaseModel):
    user_id: Optional[int] = None
    target_entity: Optional[str] = None
    reason: str
    workspace_id: Optional[int] = None

class ContainmentActionResponse(BaseModel):
    status: str
    action: str
    target: str
    event_id: str
    alert_id: Optional[str] = None
    message: str

class ThreatScanResponse(BaseModel):
    status: str
    rules_evaluated: int
    alerts_generated: int
    active_threats_detected: int
    scanned_at: datetime

# AI Security Assistant Query
class AISecurityAssistantRequest(BaseModel):
    query: str
    context_type: Optional[str] = "SOC_OVERVIEW"
    workspace_id: Optional[int] = None

class AISecurityAssistantResponse(BaseModel):
    query: str
    answer: str
    posture_score: int
    open_alerts_count: int
    active_threats_count: int
    unresolved_vulnerabilities_count: int
    recommended_actions: List[str] = []
    grounded_evidence: Dict[str, Any] = {}
