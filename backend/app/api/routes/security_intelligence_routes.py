from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.security_intelligence import (
    SecurityEvent,
    SecurityDetectionRule,
    SecurityDetectionResult,
    SecurityAlert,
    IdentityRiskRecord,
    AccessReviewCampaign,
    AccessReviewRecord,
    VulnerabilityRecord,
    SecurityPostureAssessment,
    SecurityPostureFinding,
    SecurityRemediation,
    ZeroTrustPolicy,
    ZeroTrustEvaluation,
)
from app.schemas.security_intelligence import (
    SecurityEventCreate,
    SecurityEventResponse,
    SecurityDetectionRuleCreate,
    SecurityDetectionRuleResponse,
    SecurityAlertCreate,
    SecurityAlertUpdate,
    SecurityAlertResponse,
    IdentityRiskRecordCreate,
    IdentityRiskRecordResponse,
    AccessReviewCampaignCreate,
    AccessReviewCampaignResponse,
    AccessReviewRecordUpdate,
    AccessReviewRecordResponse,
    VulnerabilityRecordCreate,
    VulnerabilityRecordUpdate,
    VulnerabilityRecordResponse,
    SecurityPostureAssessmentResponse,
    SecurityRemediationCreate,
    SecurityRemediationUpdate,
    SecurityRemediationResponse,
    ZeroTrustPolicyCreate,
    ZeroTrustPolicyUpdate,
    ZeroTrustPolicyResponse,
    ZeroTrustEvaluationRequest,
    ZeroTrustEvaluationResponse,
    ContainmentActionRequest,
    ContainmentActionResponse,
    ThreatScanResponse,
    AISecurityAssistantRequest,
    AISecurityAssistantResponse,
)
from app.services.security_intelligence_service import SecurityIntelligenceService

router = APIRouter()

def resolve_tenant_org_id(db: Session, current_user: User, explicit_org_id: Optional[int] = None) -> Optional[int]:
    """
    Resolve and enforce organization / workspace tenant boundary for current_user.
    If explicit_org_id is provided, validates that user belongs to that workspace/organization.
    Raises 403 Forbidden if unauthorized.
    """
    if explicit_org_id is not None:
        if getattr(current_user, "role", None) in ["Admin", "Owner", "admin"]:
            return explicit_org_id
        # Check workspace membership
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == explicit_org_id,
            WorkspaceMember.user_id == current_user.id
        ).first()
        if member:
            return explicit_org_id
        # Check workspace ownership
        ws = db.query(Workspace).filter(
            Workspace.id == explicit_org_id,
            Workspace.owner_id == current_user.id
        ).first()
        if ws:
            return explicit_org_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have authorization for this organization or workspace context."
        )

    # Resolve user's primary workspace if present
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).first()
    if member:
        return member.workspace_id
    ws = db.query(Workspace).filter(Workspace.owner_id == current_user.id).first()
    if ws:
        return ws.id
    return None

# 1. Posture & Overview
@router.get("/posture", response_model=Dict[str, Any])
def get_security_posture(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve dynamic Zero-Trust security posture score, control categories, and real-time risk telemetry."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return SecurityIntelligenceService.get_security_posture_summary(db, workspace_id=org_id)

# 2. Events & Audit Logging
@router.get("/events", response_model=List[SecurityEventResponse])
def list_security_events(
    workspace_id: Optional[int] = Query(None),
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve centralized security event audit log with tenant boundary filtering."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    SecurityIntelligenceService.seed_initial_security_data(db, workspace_id=org_id)
    query = db.query(SecurityEvent)
    if org_id:
        query = query.filter(or_(SecurityEvent.workspace_id == org_id, SecurityEvent.workspace_id.is_(None)))
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    return query.order_by(desc(SecurityEvent.created_at)).limit(limit).all()

@router.post("/events", response_model=SecurityEventResponse, status_code=status.HTTP_201_CREATED)
def record_security_event(
    event_in: SecurityEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log an application security event and trigger real-time threat rule evaluation."""
    target_ws = event_in.workspace_id or event_in.organization_id
    org_id = resolve_tenant_org_id(db, current_user, target_ws)
    data = event_in.model_dump()
    if not data.get("actor_id"):
        data["actor_id"] = current_user.id
    if not data.get("actor_email"):
        data["actor_email"] = current_user.email
    data["workspace_id"] = org_id
    data["organization_id"] = org_id
    return SecurityIntelligenceService.record_security_event(db, data)

# 3. Detection Rules
@router.get("/detection-rules", response_model=List[SecurityDetectionRuleResponse])
def list_detection_rules(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all configurable threat detection rules."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    SecurityIntelligenceService.seed_initial_security_data(db, workspace_id=org_id)
    query = db.query(SecurityDetectionRule)
    if org_id:
        query = query.filter(
            or_(SecurityDetectionRule.workspace_id == org_id, SecurityDetectionRule.workspace_id.is_(None))
        )
    return query.all()

@router.post("/detection-rules", response_model=SecurityDetectionRuleResponse, status_code=status.HTTP_201_CREATED)
def create_detection_rule(
    rule_in: SecurityDetectionRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Define a new threat detection rule."""
    if getattr(current_user, "role", None) not in ["admin", "Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Only platform administrators can configure threat detection rules")
    target_ws = rule_in.workspace_id or rule_in.organization_id
    org_id = resolve_tenant_org_id(db, current_user, target_ws)
    rule_data = rule_in.model_dump()
    rule_data["workspace_id"] = org_id
    rule_data["organization_id"] = org_id
    rule = SecurityDetectionRule(**rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

# 4. Alerts Lifecycle
@router.get("/alerts", response_model=List[SecurityAlertResponse])
def list_security_alerts(
    workspace_id: Optional[int] = Query(None),
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active and historical security alerts."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    SecurityIntelligenceService.seed_initial_security_data(db, workspace_id=org_id)
    query = db.query(SecurityAlert)
    if org_id:
        query = query.filter(or_(SecurityAlert.workspace_id == org_id, SecurityAlert.workspace_id.is_(None)))
    if status_filter:
        query = query.filter(SecurityAlert.status == status_filter)
    if severity:
        query = query.filter(SecurityAlert.severity == severity)
    return query.order_by(desc(SecurityAlert.created_at)).all()

@router.patch("/alerts/{alert_id}", response_model=SecurityAlertResponse)
def update_security_alert(
    alert_id: str,
    update_in: SecurityAlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge, triage, assign, or resolve a security alert."""
    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Security alert not found")
    if alert.workspace_id:
        resolve_tenant_org_id(db, current_user, alert.workspace_id)
    if update_in.status:
        alert.status = update_in.status
        if update_in.status == "RESOLVED":
            alert.resolved_at = datetime.now(timezone.utc)
    if update_in.assigned_to_id is not None:
        alert.assigned_to_id = update_in.assigned_to_id
    db.commit()
    db.refresh(alert)
    return alert

# 5. Identity Risks
@router.get("/identity-risks", response_model=List[IdentityRiskRecordResponse])
def list_identity_risks(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List accounts flagged with identity risks, failed auth velocity, or missing MFA."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    SecurityIntelligenceService.seed_initial_security_data(db, workspace_id=org_id)
    query = db.query(IdentityRiskRecord)
    if org_id:
        query = query.filter(
            or_(IdentityRiskRecord.workspace_id == org_id, IdentityRiskRecord.workspace_id.is_(None))
        )
    return query.order_by(desc(IdentityRiskRecord.detected_at)).all()

@router.post("/identity-risks", response_model=IdentityRiskRecordResponse, status_code=status.HTTP_201_CREATED)
def create_identity_risk(
    risk_in: IdentityRiskRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log an identity risk item."""
    target_ws = risk_in.workspace_id or risk_in.organization_id
    org_id = resolve_tenant_org_id(db, current_user, target_ws)
    data = risk_in.model_dump()
    data["workspace_id"] = org_id
    data["organization_id"] = org_id
    record = IdentityRiskRecord(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

# 6. Access Reviews
@router.get("/access-reviews", response_model=List[AccessReviewCampaignResponse])
def list_access_review_campaigns(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all privileged access review campaigns and entitlement records."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    SecurityIntelligenceService.seed_initial_security_data(db, workspace_id=org_id)
    query = db.query(AccessReviewCampaign)
    if org_id:
        query = query.filter(
            or_(AccessReviewCampaign.workspace_id == org_id, AccessReviewCampaign.workspace_id.is_(None))
        )
    return query.order_by(desc(AccessReviewCampaign.created_at)).all()

@router.post("/access-reviews", response_model=AccessReviewCampaignResponse, status_code=status.HTTP_201_CREATED)
def create_access_review_campaign(
    campaign_in: AccessReviewCampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Launch a new privileged access review campaign."""
    if getattr(current_user, "role", None) not in ["admin", "Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Administrator role required to initiate access review campaigns")
    target_ws = campaign_in.workspace_id or campaign_in.organization_id
    org_id = resolve_tenant_org_id(db, current_user, target_ws)
    campaign = AccessReviewCampaign(
        title=campaign_in.title,
        scope_type=campaign_in.scope_type,
        notes=campaign_in.notes,
        deadline_date=campaign_in.deadline_date,
        reviewer_id=current_user.id,
        workspace_id=org_id,
        organization_id=org_id,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

@router.patch("/access-reviews/{campaign_id}/records/{record_id}", response_model=AccessReviewRecordResponse)
def record_access_review_decision(
    campaign_id: str,
    record_id: str,
    decision_in: AccessReviewRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit approval or revocation decision for a user role entitlement."""
    rec = db.query(AccessReviewRecord).filter(
        AccessReviewRecord.id == record_id,
        AccessReviewRecord.campaign_id == campaign_id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Access review record not found")
    rec.decision = decision_in.decision
    rec.justification = decision_in.justification
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.reviewed_by_id = current_user.id
    db.commit()
    db.refresh(rec)
    return rec

# 7. Vulnerabilities
@router.get("/vulnerabilities", response_model=List[VulnerabilityRecordResponse])
def list_vulnerabilities(
    workspace_id: Optional[int] = Query(None),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tracked CVEs and security scan findings."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    SecurityIntelligenceService.seed_initial_security_data(db, workspace_id=org_id)
    query = db.query(VulnerabilityRecord)
    if org_id:
        query = query.filter(
            or_(VulnerabilityRecord.workspace_id == org_id, VulnerabilityRecord.workspace_id.is_(None))
        )
    if status_filter:
        query = query.filter(VulnerabilityRecord.remediation_status == status_filter)
    return query.order_by(desc(VulnerabilityRecord.detected_at)).all()

@router.post("/vulnerabilities", response_model=VulnerabilityRecordResponse, status_code=status.HTTP_201_CREATED)
def create_vulnerability(
    vuln_in: VulnerabilityRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new vulnerability from CI/CD scan or pentest."""
    target_ws = vuln_in.workspace_id or vuln_in.organization_id
    org_id = resolve_tenant_org_id(db, current_user, target_ws)
    data = vuln_in.model_dump()
    data["workspace_id"] = org_id
    data["organization_id"] = org_id
    vuln = VulnerabilityRecord(**data)
    db.add(vuln)
    db.commit()
    db.refresh(vuln)
    return vuln

@router.patch("/vulnerabilities/{vuln_id}", response_model=VulnerabilityRecordResponse)
def update_vulnerability_status(
    vuln_id: str,
    update_in: VulnerabilityRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update vulnerability remediation status and owner."""
    vuln = db.query(VulnerabilityRecord).filter(VulnerabilityRecord.id == vuln_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    if vuln.workspace_id:
        resolve_tenant_org_id(db, current_user, vuln.workspace_id)
    if update_in.remediation_status:
        vuln.remediation_status = update_in.remediation_status
        if update_in.remediation_status in ["RESOLVED", "VERIFIED", "CLOSED"]:
            vuln.resolved_at = datetime.now(timezone.utc)
    if update_in.remediation_owner_id is not None:
        vuln.remediation_owner_id = update_in.remediation_owner_id
    db.commit()
    db.refresh(vuln)
    return vuln

# 8. Remediations
@router.get("/remediations", response_model=List[SecurityRemediationResponse])
def list_remediations(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List security remediation tasks and corrective action items."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    query = db.query(SecurityRemediation)
    if org_id:
        query = query.filter(
            or_(SecurityRemediation.workspace_id == org_id, SecurityRemediation.workspace_id.is_(None))
        )
    return query.order_by(desc(SecurityRemediation.created_at)).all()

@router.post("/remediations", response_model=SecurityRemediationResponse, status_code=status.HTTP_201_CREATED)
def create_remediation(
    rem_in: SecurityRemediationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a security remediation action item."""
    target_ws = rem_in.workspace_id or rem_in.organization_id
    org_id = resolve_tenant_org_id(db, current_user, target_ws)
    data = rem_in.model_dump()
    data["workspace_id"] = org_id
    data["organization_id"] = org_id
    data["owner_id"] = current_user.id
    rem = SecurityRemediation(**data)
    db.add(rem)
    db.commit()
    db.refresh(rem)
    return rem

@router.patch("/remediations/{remediation_id}", response_model=SecurityRemediationResponse)
def update_remediation(
    remediation_id: str,
    update_in: SecurityRemediationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update status or resolution notes of a remediation item."""
    rem = db.query(SecurityRemediation).filter(SecurityRemediation.id == remediation_id).first()
    if not rem:
        raise HTTPException(status_code=404, detail="Remediation item not found")
    if rem.workspace_id:
        resolve_tenant_org_id(db, current_user, rem.workspace_id)
    if update_in.status:
        rem.status = update_in.status
        if update_in.status in ["RESOLVED", "VERIFIED"]:
            rem.verified_at = datetime.now(timezone.utc)
    if update_in.resolution_notes is not None:
        rem.resolution_notes = update_in.resolution_notes
    db.commit()
    db.refresh(rem)
    return rem

# 9. Zero Trust Policies & Evaluation
@router.get("/zero-trust/policies", response_model=List[ZeroTrustPolicyResponse])
def list_zero_trust_policies(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List configured Zero Trust enforcement policies."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    SecurityIntelligenceService.seed_initial_security_data(db, workspace_id=org_id)
    query = db.query(ZeroTrustPolicy)
    if org_id:
        query = query.filter(
            or_(ZeroTrustPolicy.workspace_id == org_id, ZeroTrustPolicy.workspace_id.is_(None))
        )
    return query.all()

@router.post("/zero-trust/policies", response_model=ZeroTrustPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_zero_trust_policy(
    policy_in: ZeroTrustPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Define a new Zero Trust access policy."""
    if getattr(current_user, "role", None) not in ["admin", "Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Administrator role required to configure Zero Trust policies")
    target_ws = policy_in.workspace_id or policy_in.organization_id
    org_id = resolve_tenant_org_id(db, current_user, target_ws)
    data = policy_in.model_dump()
    data["workspace_id"] = org_id
    data["organization_id"] = org_id
    policy = ZeroTrustPolicy(**data)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.patch("/zero-trust/policies/{policy_id}", response_model=ZeroTrustPolicyResponse)
def update_zero_trust_policy(
    policy_id: str,
    update_in: ZeroTrustPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a Zero Trust policy."""
    if getattr(current_user, "role", None) not in ["admin", "Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Administrator role required")
    pol = db.query(ZeroTrustPolicy).filter(ZeroTrustPolicy.id == policy_id).first()
    if not pol:
        raise HTTPException(status_code=404, detail="Zero Trust policy not found")
    if update_in.name is not None:
        pol.name = update_in.name
    if update_in.target_resource is not None:
        pol.target_resource = update_in.target_resource
    if update_in.action is not None:
        pol.action = update_in.action
    if update_in.is_enabled is not None:
        pol.is_enabled = update_in.is_enabled
    if update_in.conditions_json is not None:
        pol.conditions_json = update_in.conditions_json
    pol.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pol)
    return pol

@router.post("/zero-trust/evaluate", response_model=ZeroTrustEvaluationResponse)
def evaluate_zero_trust_access(
    req: ZeroTrustEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform real-time Zero-Trust evaluation on an access request."""
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    eval_data = req.model_dump()
    if not eval_data.get("user_id"):
        eval_data["user_id"] = current_user.id
    evaluation = SecurityIntelligenceService.evaluate_zero_trust_access(
        db=db,
        eval_req=eval_data,
        organization_id=org_id,
        workspace_id=org_id,
    )
    import json
    return ZeroTrustEvaluationResponse(
        id=evaluation.id,
        decision=evaluation.decision,
        risk_score=evaluation.risk_score,
        reasons=json.loads(evaluation.reasons_json),
        matched_policies=[],
        context=json.loads(evaluation.context_json),
        evaluated_at=evaluation.evaluated_at,
    )

# 10. Threat Detection & Containment Actions
@router.post("/threat-detection/run", response_model=ThreatScanResponse)
def trigger_threat_scan(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute real-time threat detection scan across recent security telemetry."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    res = SecurityIntelligenceService.run_threat_scan(db, organization_id=org_id, workspace_id=org_id)
    return ThreatScanResponse(**res)

@router.post("/actions/revoke-sessions", response_model=ContainmentActionResponse)
def revoke_user_sessions_action(
    req: ContainmentActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Incident Response: Immediately revoke all sessions/tokens for targeted account."""
    if getattr(current_user, "role", None) not in ["admin", "Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Administrator role required for session revocation")
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    res = SecurityIntelligenceService.revoke_user_sessions(
        db=db,
        user_id=req.user_id,
        target_entity=req.target_entity,
        reason=req.reason,
        organization_id=org_id,
        workspace_id=org_id,
        actor_id=current_user.id,
    )
    return ContainmentActionResponse(**res)

@router.post("/actions/quarantine-entity", response_model=ContainmentActionResponse)
def quarantine_entity_action(
    req: ContainmentActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Incident Response: Quarantine compromised entity and block Zero Trust access."""
    if getattr(current_user, "role", None) not in ["admin", "Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Administrator role required for quarantine actions")
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    res = SecurityIntelligenceService.quarantine_entity(
        db=db,
        user_id=req.user_id,
        target_entity=req.target_entity,
        reason=req.reason,
        organization_id=org_id,
        workspace_id=org_id,
        actor_id=current_user.id,
    )
    return ContainmentActionResponse(**res)

# 11. Grounded AI Security Analyst
@router.post("/ai/query", response_model=AISecurityAssistantResponse)
def ask_ai_security_assistant(
    request: AISecurityAssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask natural language questions to the Grounded AI Security Assistant."""
    org_id = resolve_tenant_org_id(db, current_user, request.workspace_id)
    return SecurityIntelligenceService.answer_ai_security_query(
        db=db,
        query=request.query,
        context_type=request.context_type,
        organization_id=org_id,
        workspace_id=org_id,
    )
