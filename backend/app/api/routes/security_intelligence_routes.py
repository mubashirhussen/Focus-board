from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.security_intelligence import (
    SecurityEvent,
    SecurityDetectionRule,
    SecurityAlert,
    IdentityRiskRecord,
    AccessReviewCampaign,
    AccessReviewRecord,
    VulnerabilityRecord,
    SecurityPostureAssessment,
    SecurityRemediation,
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
    AISecurityAssistantRequest,
    AISecurityAssistantResponse,
)
from app.services.security_intelligence_service import SecurityIntelligenceService

router = APIRouter()

@router.get("/posture", response_model=Dict[str, Any])
def get_security_posture(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve dynamic Zero-Trust security posture score, control categories, and real-time risk telemetry."""
    return SecurityIntelligenceService.get_security_posture_summary(db)

@router.get("/events", response_model=List[SecurityEventResponse])
def list_security_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve centralized security event audit log with optional type and severity filtering."""
    SecurityIntelligenceService.seed_initial_security_data(db)
    query = db.query(SecurityEvent)
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
    data = event_in.model_dump()
    if not data.get("actor_id"):
        data["actor_id"] = current_user.id
    if not data.get("actor_email"):
        data["actor_email"] = current_user.email
    return SecurityIntelligenceService.record_security_event(db, data)

@router.get("/detection-rules", response_model=List[SecurityDetectionRuleResponse])
def list_detection_rules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all configurable threat detection rules."""
    SecurityIntelligenceService.seed_initial_security_data(db)
    return db.query(SecurityDetectionRule).all()

@router.post("/detection-rules", response_model=SecurityDetectionRuleResponse, status_code=status.HTTP_201_CREATED)
def create_detection_rule(
    rule_in: SecurityDetectionRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Define a new threat detection rule."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only platform administrators can configure threat detection rules")
    rule = SecurityDetectionRule(**rule_in.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/alerts", response_model=List[SecurityAlertResponse])
def list_security_alerts(
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active and historical security alerts."""
    SecurityIntelligenceService.seed_initial_security_data(db)
    query = db.query(SecurityAlert)
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
    if update_in.status:
        alert.status = update_in.status
        if update_in.status == "RESOLVED":
            from datetime import datetime, timezone
            alert.resolved_at = datetime.now(timezone.utc)
    if update_in.assigned_to_id is not None:
        alert.assigned_to_id = update_in.assigned_to_id
    db.commit()
    db.refresh(alert)
    return alert

@router.get("/identity-risks", response_model=List[IdentityRiskRecordResponse])
def list_identity_risks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List accounts flagged with identity risks, failed auth velocity, or missing MFA."""
    SecurityIntelligenceService.seed_initial_security_data(db)
    return db.query(IdentityRiskRecord).order_by(desc(IdentityRiskRecord.detected_at)).all()

@router.get("/access-reviews", response_model=List[AccessReviewCampaignResponse])
def list_access_review_campaigns(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all privileged access review campaigns and entitlement records."""
    SecurityIntelligenceService.seed_initial_security_data(db)
    return db.query(AccessReviewCampaign).order_by(desc(AccessReviewCampaign.created_at)).all()

@router.post("/access-reviews", response_model=AccessReviewCampaignResponse, status_code=status.HTTP_201_CREATED)
def create_access_review_campaign(
    campaign_in: AccessReviewCampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Launch a new privileged access review campaign."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required to initiate access review campaigns")
    campaign = AccessReviewCampaign(
        title=campaign_in.title,
        scope_type=campaign_in.scope_type,
        notes=campaign_in.notes,
        deadline_date=campaign_in.deadline_date,
        reviewer_id=current_user.id,
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
    from datetime import datetime, timezone
    rec.decision = decision_in.decision
    rec.justification = decision_in.justification
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.reviewed_by_id = current_user.id
    db.commit()
    db.refresh(rec)
    return rec

@router.get("/vulnerabilities", response_model=List[VulnerabilityRecordResponse])
def list_vulnerabilities(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tracked CVEs and security scan findings."""
    SecurityIntelligenceService.seed_initial_security_data(db)
    query = db.query(VulnerabilityRecord)
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
    vuln = VulnerabilityRecord(**vuln_in.model_dump())
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
    if update_in.remediation_status:
        vuln.remediation_status = update_in.remediation_status
        if update_in.remediation_status in ["RESOLVED", "VERIFIED", "CLOSED"]:
            from datetime import datetime, timezone
            vuln.resolved_at = datetime.now(timezone.utc)
    if update_in.remediation_owner_id is not None:
        vuln.remediation_owner_id = update_in.remediation_owner_id
    db.commit()
    db.refresh(vuln)
    return vuln

@router.get("/remediations", response_model=List[SecurityRemediationResponse])
def list_remediations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List security remediation tasks and corrective action items."""
    return db.query(SecurityRemediation).order_by(desc(SecurityRemediation.created_at)).all()

@router.post("/ai/query", response_model=AISecurityAssistantResponse)
def ask_ai_security_assistant(
    request: AISecurityAssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask natural language questions to the Grounded AI Security Assistant."""
    return SecurityIntelligenceService.answer_ai_security_query(db, request.query, request.context_type)
