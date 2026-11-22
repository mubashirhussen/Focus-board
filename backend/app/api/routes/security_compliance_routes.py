from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.security_compliance import (
    ComplianceControlCreate,
    ComplianceControlUpdate,
    ComplianceControlResponse,
    ComplianceEvidenceCreate,
    ComplianceEvidenceResponse,
    SecurityPolicyCreate,
    SecurityPolicyUpdate,
    SecurityPolicyResponse,
    PolicyAcknowledgmentCreate,
    PolicyAcknowledgmentResponse,
    SecurityRiskItemCreate,
    SecurityRiskItemUpdate,
    SecurityRiskItemResponse,
    SecurityIncidentCreate,
    SecurityIncidentUpdate,
    SecurityIncidentResponse,
    SecurityVendorCreate,
    SecurityVendorUpdate,
    SecurityVendorResponse,
    PrivacyRequestCreate,
    PrivacyRequestUpdate,
    PrivacyRequestResponse,
    TrustCenterDocumentResponse,
    SecurityComplianceOverviewResponse,
    TrustCenterOverviewResponse,
)
from app.services.security_compliance_service import SecurityComplianceService

router = APIRouter(prefix="/security", tags=["Enterprise Security & Compliance"])

# --- Public Trust Center Endpoints ---
@router.get("/trust/overview", response_model=TrustCenterOverviewResponse)
def get_trust_center_overview(
    db: Session = Depends(get_db),
):
    """Retrieve public Trust Center posture, compliance readiness, encryption standards, and subprocessors."""
    return SecurityComplianceService.get_trust_center_overview(db)

@router.get("/trust/documents", response_model=List[TrustCenterDocumentResponse])
def get_trust_center_documents(
    db: Session = Depends(get_db),
):
    """Retrieve list of approved public compliance documents and security whitepapers."""
    overview = SecurityComplianceService.get_trust_center_overview(db)
    return overview.public_documents

# --- Authenticated Security & Compliance Management ---
@router.get("/overview", response_model=SecurityComplianceOverviewResponse)
def get_compliance_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get enterprise compliance overview with SOC 2 / ISO 27001 readiness, risks, and incident status."""
    return SecurityComplianceService.get_overview(db)

# --- Controls & Evidence ---
@router.get("/controls", response_model=List[ComplianceControlResponse])
def list_compliance_controls(
    framework: Optional[str] = Query(None, description="SOC2, ISO27001, or GDPR"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List compliance controls with implementation status and evidence count."""
    return SecurityComplianceService.list_controls(db, framework=framework)

@router.put("/controls/{control_id}", response_model=ComplianceControlResponse)
def update_compliance_control(
    control_id: str,
    update_data: ComplianceControlUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update control implementation status, notes, or risk level."""
    ctrl = SecurityComplianceService.update_control(db, control_id=control_id, update_data=update_data)
    if not ctrl:
        raise HTTPException(status_code=404, detail="Compliance control not found")
    resp = ComplianceControlResponse.model_validate(ctrl)
    resp.evidence_count = len(SecurityComplianceService.list_evidence_for_control(db, ctrl.id))
    return resp

@router.post("/controls/{control_id}/evidence", response_model=ComplianceEvidenceResponse, status_code=status.HTTP_201_CREATED)
def add_compliance_evidence(
    control_id: str,
    evidence_in: ComplianceEvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload and attach cryptographic/procedural audit evidence to a compliance control."""
    evidence_in.control_id = control_id
    try:
        evidence = SecurityComplianceService.add_evidence(db, evidence_in=evidence_in, user_id=current_user.id)
        return ComplianceEvidenceResponse.model_validate(evidence)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/controls/{control_id}/evidence", response_model=List[ComplianceEvidenceResponse])
def list_compliance_evidence(
    control_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all evidence attached to a specific compliance control."""
    evidences = SecurityComplianceService.list_evidence_for_control(db, control_id=control_id)
    return [ComplianceEvidenceResponse.model_validate(e) for e in evidences]

# --- Policies & Acknowledgments ---
@router.get("/policies", response_model=List[SecurityPolicyResponse])
def list_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List security and data protection policies with acknowledgment status."""
    return SecurityComplianceService.list_policies(db)

@router.post("/policies", response_model=SecurityPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    policy_in: SecurityPolicyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new security policy."""
    policy = SecurityComplianceService.create_policy(db, policy_in=policy_in, user_id=current_user.id)
    resp = SecurityPolicyResponse.model_validate(policy)
    resp.acknowledgment_count = 0
    return resp

@router.post("/policies/{policy_id}/acknowledge", response_model=PolicyAcknowledgmentResponse)
def acknowledge_policy(
    policy_id: str,
    ack_in: PolicyAcknowledgmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record immutable policy acknowledgment for the authenticated user."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        ack = SecurityComplianceService.acknowledge_policy(
            db, policy_id=policy_id, user_id=current_user.id, ack_in=ack_in, ip_address=client_ip
        )
        return PolicyAcknowledgmentResponse.model_validate(ack)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- Security Risk Management ---
@router.get("/risks", response_model=List[SecurityRiskItemResponse])
def list_risks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List risks in the enterprise risk register sorted by risk score."""
    risks = SecurityComplianceService.list_risks(db)
    return [SecurityRiskItemResponse.model_validate(r) for r in risks]

@router.post("/risks", response_model=SecurityRiskItemResponse, status_code=status.HTTP_201_CREATED)
def create_risk(
    risk_in: SecurityRiskItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a risk to the register with automated severity-likelihood scoring."""
    risk = SecurityComplianceService.create_risk(db, risk_in=risk_in)
    return SecurityRiskItemResponse.model_validate(risk)

@router.put("/risks/{risk_id}", response_model=SecurityRiskItemResponse)
def update_risk(
    risk_id: str,
    update_data: SecurityRiskItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update risk status, mitigation strategy, or residual risk."""
    risk = SecurityComplianceService.update_risk(db, risk_id=risk_id, update_data=update_data)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk item not found")
    return SecurityRiskItemResponse.model_validate(risk)

# --- Incident Management ---
@router.get("/incidents", response_model=List[SecurityIncidentResponse])
def list_incidents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List security incidents across triage and resolution lifecycle."""
    incidents = SecurityComplianceService.list_incidents(db)
    return [SecurityIncidentResponse.model_validate(i) for i in incidents]

@router.post("/incidents", response_model=SecurityIncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident_in: SecurityIncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report or record a security incident."""
    incident = SecurityComplianceService.create_incident(db, incident_in=incident_in)
    return SecurityIncidentResponse.model_validate(incident)

@router.put("/incidents/{incident_id}", response_model=SecurityIncidentResponse)
def update_incident(
    incident_id: str,
    update_data: SecurityIncidentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update incident status (containment, resolution) and root-cause analysis."""
    incident = SecurityComplianceService.update_incident(db, incident_id=incident_id, update_data=update_data)
    if not incident:
        raise HTTPException(status_code=404, detail="Security incident not found")
    return SecurityIncidentResponse.model_validate(incident)

# --- Vendor Risk Management ---
@router.get("/vendors", response_model=List[SecurityVendorResponse])
def list_vendors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List third-party vendors and subprocessor compliance postures."""
    vendors = SecurityComplianceService.list_vendors(db)
    return [SecurityVendorResponse.model_validate(v) for v in vendors]

@router.post("/vendors", response_model=SecurityVendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_in: SecurityVendorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new third-party vendor with compliance certifications."""
    vendor = SecurityComplianceService.create_vendor(db, vendor_in=vendor_in)
    return SecurityVendorResponse.model_validate(vendor)

# --- Privacy Requests ---
@router.get("/privacy-requests", response_model=List[PrivacyRequestResponse])
def list_privacy_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List data subject privacy requests (GDPR/CCPA access, export, erasure)."""
    user_filter = None if current_user.role in ["admin", "superadmin"] else current_user.id
    requests = SecurityComplianceService.list_privacy_requests(db, user_id=user_filter)
    return [PrivacyRequestResponse.model_validate(r) for r in requests]

@router.post("/privacy-requests", response_model=PrivacyRequestResponse, status_code=status.HTTP_201_CREATED)
def create_privacy_request(
    req_in: PrivacyRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a GDPR / CCPA privacy request (ACCESS, EXPORT, DELETION, RECTIFICATION)."""
    req = SecurityComplianceService.create_privacy_request(db, req_in=req_in, user_id=current_user.id)
    return PrivacyRequestResponse.model_validate(req)

@router.put("/privacy-requests/{request_id}", response_model=PrivacyRequestResponse)
def update_privacy_request(
    request_id: str,
    update_data: PrivacyRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update privacy request status (VERIFYING, IN_PROGRESS, COMPLETED, REJECTED)."""
    req = SecurityComplianceService.update_privacy_request(db, request_id=request_id, update_data=update_data)
    if not req:
        raise HTTPException(status_code=404, detail="Privacy request not found")
    return PrivacyRequestResponse.model_validate(req)
