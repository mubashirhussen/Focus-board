import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.security_compliance import (
    ComplianceControl,
    ComplianceEvidence,
    SecurityPolicy,
    PolicyAcknowledgment,
    SecurityRiskItem,
    SecurityIncident,
    SecurityVendor,
    PrivacyRequest,
    TrustCenterDocument,
)
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
    TrustCenterDocumentCreate,
    TrustCenterDocumentUpdate,
    TrustCenterDocumentResponse,
    SecurityComplianceOverviewResponse,
    TrustCenterOverviewResponse,
    FrameworkReadiness,
)

BASELINE_CONTROLS = [
    # SOC 2 Controls
    {
        "control_id": "CC6.1",
        "title": "Logical and Physical Access Security Controls",
        "framework": "SOC2",
        "category": "ACCESS_CONTROL",
        "description": "The entity implements logical access security software, infrastructure, and architectures over protected information assets.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Enforced via JWT bearer authentication, bcrypt hashing, and API gateway rate limiting.",
    },
    {
        "control_id": "CC6.2",
        "title": "User Registration and Access Administration",
        "framework": "SOC2",
        "category": "IDENTITY_MANAGEMENT",
        "description": "Prior to issuing system credentials and granting access, user registration and authorization is verified.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Automated email verification and enterprise organization policy controls.",
    },
    {
        "control_id": "CC6.3",
        "title": "Role-Based Access Control and Least Privilege",
        "framework": "SOC2",
        "category": "ACCESS_CONTROL",
        "description": "The entity authorizes, modifies, or revokes access to protected assets based on roles and least privilege principles.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Granular RBAC implemented across Workspaces, Projects, and Admin management.",
    },
    {
        "control_id": "CC6.6",
        "title": "Boundary Protection & Encryption in Transit",
        "framework": "SOC2",
        "category": "ENCRYPTION",
        "description": "The entity protects against unauthorized access across network perimeters and encrypts sensitive data in transit.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Enforced HTTPS/TLS 1.3 with strict transport security and CORS validation.",
    },
    {
        "control_id": "CC7.1",
        "title": "Vulnerability Detection & Monitoring",
        "framework": "SOC2",
        "category": "INCIDENT_RESPONSE",
        "description": "To meet commitments, the entity uses detection and monitoring procedures to identify vulnerabilities.",
        "status": "PARTIALLY_IMPLEMENTED",
        "risk_level": "MEDIUM",
        "remediation_notes": "Automated dependency vulnerability audits via CI/CD and container scanning.",
    },
    {
        "control_id": "CC8.1",
        "title": "Change Management and CI/CD Quality Controls",
        "framework": "SOC2",
        "category": "CHANGE_MANAGEMENT",
        "description": "The entity authorizes, designs, configures, tests, approves, and implements changes to software.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Automated regression testing suites, Alembic migrations, and PR approval requirements.",
    },
    # ISO 27001 Controls
    {
        "control_id": "A.9.1",
        "title": "Business Requirements of Access Control",
        "framework": "ISO27001",
        "category": "ACCESS_CONTROL",
        "description": "An access control policy shall be established, documented and reviewed based on business requirements.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Formalized Access Control Policy with mandatory annual review.",
    },
    {
        "control_id": "A.10.1",
        "title": "Cryptographic Controls and Key Management",
        "framework": "ISO27001",
        "category": "ENCRYPTION",
        "description": "A policy on the use of cryptographic controls for protection of information shall be implemented.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "AES-256 GCM authenticated encryption at rest for sensitive tokens; TLS 1.3 in transit.",
    },
    {
        "control_id": "A.12.1",
        "title": "Operational Procedures and Responsibilities",
        "framework": "ISO27001",
        "category": "GOVERNANCE",
        "description": "Operating procedures shall be documented and made available to all users who need them.",
        "status": "PARTIALLY_IMPLEMENTED",
        "risk_level": "MEDIUM",
        "remediation_notes": "Standard operating procedures documented in Developer Portal and DevSecOps playbooks.",
    },
    {
        "control_id": "A.12.6",
        "title": "Management of Technical Vulnerabilities",
        "framework": "ISO27001",
        "category": "INCIDENT_RESPONSE",
        "description": "Information about technical vulnerabilities of information systems shall be obtained in a timely manner.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Automated continuous security scanning and real-time alerts.",
    },
    # GDPR Controls
    {
        "control_id": "Art.15",
        "title": "Right of Access by the Data Subject",
        "framework": "GDPR",
        "category": "PRIVACY",
        "description": "The data subject shall have the right to obtain confirmation as to whether or not personal data are being processed.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Self-service profile and data export tools in Account Settings and Privacy Request portal.",
    },
    {
        "control_id": "Art.17",
        "title": "Right to Erasure ('Right to be Forgotten')",
        "framework": "GDPR",
        "category": "PRIVACY",
        "description": "The data subject shall have the right to obtain erasure of personal data without undue delay.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Tenant-aware cascade deletion and automated privacy erasure workflow.",
    },
    {
        "control_id": "Art.32",
        "title": "Security of Processing",
        "framework": "GDPR",
        "category": "DATA_PROTECTION",
        "description": "Implement appropriate technical and organizational measures to ensure security appropriate to the risk.",
        "status": "IMPLEMENTED",
        "risk_level": "LOW",
        "remediation_notes": "Pseudonymization, TLS encryption, least-privilege DB roles, and immutable audit logs.",
    },
]

BASELINE_POLICIES = [
    {
        "policy_key": "access_control_policy",
        "title": "Access Control and Credential Management Policy",
        "category": "ACCESS",
        "version": "1.0",
        "status": "APPROVED",
        "content": "# Access Control Policy\n\nAll system access is governed by the principle of least privilege. Strong password requirements and session timeouts are strictly enforced.",
    },
    {
        "policy_key": "data_protection_policy",
        "title": "Data Protection & Privacy Policy",
        "category": "GOVERNANCE",
        "version": "1.0",
        "status": "APPROVED",
        "content": "# Data Protection Policy\n\nFocusBoard respects data sovereignty. Personal data is isolated by tenant boundary and encrypted in transit and at rest.",
    },
    {
        "policy_key": "incident_response_policy",
        "title": "Security Incident Response Plan",
        "category": "INCIDENT",
        "version": "1.0",
        "status": "APPROVED",
        "content": "# Incident Response Plan\n\nSecurity events are triaged across P1-P4 severities with defined containment, remediation, and 72-hour notification procedures.",
    },
]

BASELINE_TRUST_DOCUMENTS = [
    {
        "slug": "soc2-readiness-overview",
        "title": "SOC 2 Type II Compliance Readiness Statement",
        "category": "SOC2",
        "summary": "Detailed mapping of FocusBoard security controls to AICPA Trust Services Criteria.",
        "content": "FocusBoard actively aligns technical and organizational controls with SOC 2 Security, Availability, and Confidentiality principles.",
        "is_public": True,
        "version": "1.0",
    },
    {
        "slug": "iso27001-statement-of-applicability",
        "title": "ISO/IEC 27001 Statement of Applicability",
        "category": "ISO27001",
        "summary": "Index of Annex A security controls implemented within FocusBoard SaaS infrastructure.",
        "content": "Our Information Security Management System (ISMS) adheres to ISO/IEC 27001 standards covering cryptography, access, and operations.",
        "is_public": True,
        "version": "1.0",
    },
    {
        "slug": "subprocessor-directory",
        "title": "Approved Third-Party Subprocessor Directory",
        "category": "SUBPROCESSORS",
        "summary": "Complete inventory of third-party cloud hosting and infrastructure partners.",
        "content": "Subprocessors include Amazon Web Services (Hosting & Database), Cloudflare (CDN/WAF), Stripe (Payments), and OpenAI (AI Copilot).",
        "is_public": True,
        "version": "1.0",
    },
    {
        "slug": "encryption-standards",
        "title": "Encryption and Cryptographic Architecture",
        "category": "ENCRYPTION",
        "summary": "Technical specifications for in-transit and at-rest cryptographic safeguards.",
        "content": "FocusBoard enforces TLS 1.3 with AES-GCM cipher suites for all network ingress/egress and AES-256 for all persistent storage.",
        "is_public": True,
        "version": "1.0",
    },
]

BASELINE_SUBPROCESSORS = [
    {
        "name": "Amazon Web Services (AWS)",
        "purpose": "Cloud Hosting & Primary Database Infrastructure",
        "location": "United States / EU",
        "certifications": ["SOC 2 Type II", "ISO 27001", "PCI-DSS Level 1"],
    },
    {
        "name": "Cloudflare",
        "purpose": "DDoS Mitigation, CDN & WAF Edge Protection",
        "location": "Global",
        "certifications": ["SOC 2 Type II", "ISO 27001", "PCI-DSS"],
    },
    {
        "name": "Stripe",
        "purpose": "Payment Processing & Billing Engine",
        "location": "United States",
        "certifications": ["PCI-DSS Level 1", "SOC 1", "SOC 2"],
    },
    {
        "name": "OpenAI / Anthropic",
        "purpose": "AI Copilot & Task Planning Inference (Zero Data Retention)",
        "location": "United States",
        "certifications": ["SOC 2 Type II"],
    },
]

class SecurityComplianceService:
    @staticmethod
    def ensure_baseline_data(db: Session):
        """Seed baseline compliance controls, policies, and trust center documents if missing."""
        if db.query(ComplianceControl).count() == 0:
            for item in BASELINE_CONTROLS:
                ctrl = ComplianceControl(
                    control_id=item["control_id"],
                    title=item["title"],
                    description=item["description"],
                    framework=item["framework"],
                    category=item["category"],
                    status=item["status"],
                    risk_level=item["risk_level"],
                    remediation_notes=item["remediation_notes"],
                    last_reviewed_at=datetime.now(timezone.utc),
                )
                db.add(ctrl)
            db.commit()

        if db.query(SecurityPolicy).count() == 0:
            for item in BASELINE_POLICIES:
                pol = SecurityPolicy(
                    policy_key=item["policy_key"],
                    title=item["title"],
                    category=item["category"],
                    version=item["version"],
                    status=item["status"],
                    content=item["content"],
                    approved_at=datetime.now(timezone.utc),
                    review_date=datetime.now(timezone.utc) + timedelta(days=365),
                )
                db.add(pol)
            db.commit()

        if db.query(TrustCenterDocument).count() == 0:
            for item in BASELINE_TRUST_DOCUMENTS:
                doc = TrustCenterDocument(
                    slug=item["slug"],
                    title=item["title"],
                    category=item["category"],
                    summary=item["summary"],
                    content=item["content"],
                    is_public=item["is_public"],
                    version=item["version"],
                )
                db.add(doc)
            db.commit()

    @staticmethod
    def get_overview(db: Session) -> SecurityComplianceOverviewResponse:
        SecurityComplianceService.ensure_baseline_data(db)
        controls = db.query(ComplianceControl).all()

        total_controls = len(controls)
        implemented = sum(1 for c in controls if c.status == "IMPLEMENTED")
        in_progress = sum(1 for c in controls if c.status in ["PARTIALLY_IMPLEMENTED", "NEEDS_REVIEW"])
        not_started = sum(1 for c in controls if c.status in ["NOT_ASSESSED", "NOT_IMPLEMENTED"])

        overall_readiness = round((implemented / total_controls * 100.0), 1) if total_controls > 0 else 0.0

        frameworks_list = []
        for fw in ["SOC2", "ISO27001", "GDPR"]:
            fw_controls = [c for c in controls if c.framework == fw]
            fw_total = len(fw_controls)
            fw_impl = sum(1 for c in fw_controls if c.status == "IMPLEMENTED")
            fw_in_prog = sum(1 for c in fw_controls if c.status in ["PARTIALLY_IMPLEMENTED", "NEEDS_REVIEW"])
            pct = round((fw_impl / fw_total * 100.0), 1) if fw_total > 0 else 0.0
            frameworks_list.append(
                FrameworkReadiness(
                    framework=fw,
                    total_controls=fw_total,
                    implemented_controls=fw_impl,
                    in_progress_controls=fw_in_prog,
                    readiness_percentage=pct,
                )
            )

        active_risks = db.query(SecurityRiskItem).filter(
            SecurityRiskItem.status.notin_(["RESOLVED", "CLOSED"])
        ).all()
        critical_risks_count = sum(1 for r in active_risks if r.severity == "CRITICAL" or r.risk_score >= 12)

        open_incidents_count = db.query(SecurityIncident).filter(
            SecurityIncident.status.notin_(["RESOLVED", "CLOSED"])
        ).count()

        pending_privacy_count = db.query(PrivacyRequest).filter(
            PrivacyRequest.status.in_(["RECEIVED", "VERIFYING", "IN_PROGRESS"])
        ).count()

        approved_policies_count = db.query(SecurityPolicy).filter(
            SecurityPolicy.status.in_(["APPROVED", "PUBLISHED"])
        ).count()

        verified_vendors_count = db.query(SecurityVendor).filter(
            SecurityVendor.status == "ACTIVE"
        ).count()

        return SecurityComplianceOverviewResponse(
            total_controls=total_controls,
            implemented_controls=implemented,
            in_progress_controls=in_progress,
            not_started_controls=not_started,
            overall_readiness_percentage=overall_readiness,
            frameworks=frameworks_list,
            active_risks_count=len(active_risks),
            critical_risks_count=critical_risks_count,
            open_incidents_count=open_incidents_count,
            pending_privacy_requests_count=pending_privacy_count,
            approved_policies_count=approved_policies_count,
            verified_vendors_count=verified_vendors_count,
        )

    # --- Controls ---
    @staticmethod
    def list_controls(db: Session, framework: Optional[str] = None) -> List[ComplianceControlResponse]:
        SecurityComplianceService.ensure_baseline_data(db)
        query = db.query(ComplianceControl)
        if framework:
            query = query.filter(ComplianceControl.framework == framework)
        controls = query.order_by(ComplianceControl.control_id.asc()).all()

        result = []
        for c in controls:
            ev_count = db.query(ComplianceEvidence).filter(ComplianceEvidence.control_id == c.id).count()
            resp = ComplianceControlResponse.model_validate(c)
            resp.evidence_count = ev_count
            result.append(resp)
        return result

    @staticmethod
    def update_control(db: Session, control_id: str, update_data: ComplianceControlUpdate) -> Optional[ComplianceControl]:
        ctrl = db.query(ComplianceControl).filter(ComplianceControl.id == control_id).first()
        if not ctrl:
            # Also try matching by control_id e.g. CC6.1
            ctrl = db.query(ComplianceControl).filter(ComplianceControl.control_id == control_id).first()
        if not ctrl:
            return None
        for k, v in update_data.model_dump(exclude_unset=True).items():
            setattr(ctrl, k, v)
        ctrl.last_reviewed_at = datetime.now(timezone.utc)
        ctrl.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(ctrl)
        return ctrl

    # --- Evidence ---
    @staticmethod
    def add_evidence(db: Session, evidence_in: ComplianceEvidenceCreate, user_id: Optional[int] = None) -> ComplianceEvidence:
        ctrl = db.query(ComplianceControl).filter(ComplianceControl.id == evidence_in.control_id).first()
        if not ctrl:
            ctrl = db.query(ComplianceControl).filter(ComplianceControl.control_id == evidence_in.control_id).first()
        if not ctrl:
            raise ValueError(f"ComplianceControl {evidence_in.control_id} not found")

        evidence = ComplianceEvidence(
            control_id=ctrl.id,
            name=evidence_in.name,
            description=evidence_in.description,
            evidence_type=evidence_in.evidence_type,
            file_url=evidence_in.file_url,
            content_text=evidence_in.content_text,
            uploaded_by=user_id,
            status=evidence_in.status,
            expires_at=evidence_in.expires_at,
        )
        db.add(evidence)
        if ctrl.status in ["NOT_ASSESSED", "NOT_IMPLEMENTED"]:
            ctrl.status = "PARTIALLY_IMPLEMENTED"
            ctrl.last_reviewed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(evidence)
        return evidence

    @staticmethod
    def list_evidence_for_control(db: Session, control_id: str) -> List[ComplianceEvidence]:
        ctrl = db.query(ComplianceControl).filter(ComplianceControl.id == control_id).first()
        if not ctrl:
            ctrl = db.query(ComplianceControl).filter(ComplianceControl.control_id == control_id).first()
        if not ctrl:
            return []
        return db.query(ComplianceEvidence).filter(ComplianceEvidence.control_id == ctrl.id).all()

    # --- Policies ---
    @staticmethod
    def list_policies(db: Session) -> List[SecurityPolicyResponse]:
        SecurityComplianceService.ensure_baseline_data(db)
        policies = db.query(SecurityPolicy).all()
        result = []
        for pol in policies:
            ack_count = db.query(PolicyAcknowledgment).filter(PolicyAcknowledgment.policy_id == pol.id).count()
            resp = SecurityPolicyResponse.model_validate(pol)
            resp.acknowledgment_count = ack_count
            result.append(resp)
        return result

    @staticmethod
    def create_policy(db: Session, policy_in: SecurityPolicyCreate, user_id: Optional[int] = None) -> SecurityPolicy:
        pol = SecurityPolicy(
            policy_key=policy_in.policy_key,
            title=policy_in.title,
            category=policy_in.category,
            version=policy_in.version,
            status=policy_in.status,
            content=policy_in.content,
            approved_by=user_id if policy_in.status in ["APPROVED", "PUBLISHED"] else None,
            approved_at=datetime.now(timezone.utc) if policy_in.status in ["APPROVED", "PUBLISHED"] else None,
            review_date=datetime.now(timezone.utc) + timedelta(days=365) if policy_in.status in ["APPROVED", "PUBLISHED"] else None,
        )
        db.add(pol)
        db.commit()
        db.refresh(pol)
        return pol

    @staticmethod
    def acknowledge_policy(db: Session, policy_id: str, user_id: int, ack_in: PolicyAcknowledgmentCreate, ip_address: Optional[str] = None) -> PolicyAcknowledgment:
        pol = db.query(SecurityPolicy).filter(SecurityPolicy.id == policy_id).first()
        if not pol:
            pol = db.query(SecurityPolicy).filter(SecurityPolicy.policy_key == policy_id).first()
        if not pol:
            raise ValueError(f"SecurityPolicy {policy_id} not found")

        existing = db.query(PolicyAcknowledgment).filter(
            PolicyAcknowledgment.policy_id == pol.id,
            PolicyAcknowledgment.user_id == user_id,
            PolicyAcknowledgment.version == ack_in.version,
        ).first()
        if existing:
            return existing

        ack = PolicyAcknowledgment(
            policy_id=pol.id,
            user_id=user_id,
            version=ack_in.version,
            ip_address=ip_address,
        )
        db.add(ack)
        db.commit()
        db.refresh(ack)
        return ack

    # --- Risks ---
    @staticmethod
    def calculate_risk_score(severity: str, likelihood: str) -> int:
        multiplier = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        sev = multiplier.get(severity.upper(), 2)
        like = multiplier.get(likelihood.upper(), 2)
        return sev * like

    @staticmethod
    def list_risks(db: Session) -> List[SecurityRiskItem]:
        return db.query(SecurityRiskItem).order_by(SecurityRiskItem.risk_score.desc()).all()

    @staticmethod
    def create_risk(db: Session, risk_in: SecurityRiskItemCreate) -> SecurityRiskItem:
        score = SecurityComplianceService.calculate_risk_score(risk_in.severity, risk_in.likelihood)
        item = SecurityRiskItem(
            risk_code=risk_in.risk_code,
            title=risk_in.title,
            description=risk_in.description,
            category=risk_in.category,
            severity=risk_in.severity,
            likelihood=risk_in.likelihood,
            impact=risk_in.impact,
            risk_score=score,
            mitigation_plan=risk_in.mitigation_plan,
            status=risk_in.status,
            owner_id=risk_in.owner_id,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_risk(db: Session, risk_id: str, update_data: SecurityRiskItemUpdate) -> Optional[SecurityRiskItem]:
        item = db.query(SecurityRiskItem).filter(SecurityRiskItem.id == risk_id).first()
        if not item:
            item = db.query(SecurityRiskItem).filter(SecurityRiskItem.risk_code == risk_id).first()
        if not item:
            return None
        for k, v in update_data.model_dump(exclude_unset=True).items():
            setattr(item, k, v)
        item.risk_score = SecurityComplianceService.calculate_risk_score(item.severity, item.likelihood)
        item.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item

    # --- Incidents ---
    @staticmethod
    def list_incidents(db: Session) -> List[SecurityIncident]:
        return db.query(SecurityIncident).order_by(SecurityIncident.detected_at.desc()).all()

    @staticmethod
    def create_incident(db: Session, incident_in: SecurityIncidentCreate) -> SecurityIncident:
        incident = SecurityIncident(
            incident_code=incident_in.incident_code,
            title=incident_in.title,
            severity=incident_in.severity,
            category=incident_in.category,
            status=incident_in.status,
            summary=incident_in.summary,
            owner_id=incident_in.owner_id,
            root_cause=incident_in.root_cause,
            corrective_actions=incident_in.corrective_actions,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def update_incident(db: Session, incident_id: str, update_data: SecurityIncidentUpdate) -> Optional[SecurityIncident]:
        inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not inc:
            inc = db.query(SecurityIncident).filter(SecurityIncident.incident_code == incident_id).first()
        if not inc:
            return None
        for k, v in update_data.model_dump(exclude_unset=True).items():
            setattr(inc, k, v)
        if update_data.status in ["RESOLVED", "CLOSED"] and not inc.resolved_at:
            inc.resolved_at = datetime.now(timezone.utc)
        elif update_data.status == "CONTAINMENT" and not inc.contained_at:
            inc.contained_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(inc)
        return inc

    # --- Vendors ---
    @staticmethod
    def list_vendors(db: Session) -> List[SecurityVendor]:
        return db.query(SecurityVendor).all()

    @staticmethod
    def create_vendor(db: Session, vendor_in: SecurityVendorCreate) -> SecurityVendor:
        vendor = SecurityVendor(
            name=vendor_in.name,
            service_type=vendor_in.service_type,
            data_classification=vendor_in.data_classification,
            risk_rating=vendor_in.risk_rating,
            security_contact=vendor_in.security_contact,
            status=vendor_in.status,
            review_date=datetime.now(timezone.utc) + timedelta(days=180),
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor

    # --- Privacy Requests ---
    @staticmethod
    def list_privacy_requests(db: Session, user_id: Optional[int] = None) -> List[PrivacyRequest]:
        query = db.query(PrivacyRequest)
        if user_id:
            query = query.filter(PrivacyRequest.user_id == user_id)
        return query.order_by(PrivacyRequest.requested_at.desc()).all()

    @staticmethod
    def create_privacy_request(db: Session, req_in: PrivacyRequestCreate, user_id: Optional[int] = None) -> PrivacyRequest:
        req = PrivacyRequest(
            request_type=req_in.request_type,
            requester_email=req_in.requester_email,
            details=req_in.details,
            status=req_in.status,
            user_id=user_id or req_in.user_id,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def update_privacy_request(db: Session, request_id: str, update_data: PrivacyRequestUpdate) -> Optional[PrivacyRequest]:
        req = db.query(PrivacyRequest).filter(PrivacyRequest.id == request_id).first()
        if not req:
            return None
        for k, v in update_data.model_dump(exclude_unset=True).items():
            setattr(req, k, v)
        if update_data.status in ["COMPLETED", "REJECTED"] and not req.completed_at:
            req.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(req)
        return req

    # --- Trust Center Public Posture ---
    @staticmethod
    def get_trust_center_overview(db: Session) -> TrustCenterOverviewResponse:
        SecurityComplianceService.ensure_baseline_data(db)

        controls = db.query(ComplianceControl).all()
        soc2_controls = [c for c in controls if c.framework == "SOC2"]
        iso_controls = [c for c in controls if c.framework == "ISO27001"]
        gdpr_controls = [c for c in controls if c.framework == "GDPR"]

        soc2_pct = round((sum(1 for c in soc2_controls if c.status == "IMPLEMENTED") / len(soc2_controls) * 100.0), 1) if soc2_controls else 100.0
        iso_pct = round((sum(1 for c in iso_controls if c.status == "IMPLEMENTED") / len(iso_controls) * 100.0), 1) if iso_controls else 100.0
        gdpr_pct = round((sum(1 for c in gdpr_controls if c.status == "IMPLEMENTED") / len(gdpr_controls) * 100.0), 1) if gdpr_controls else 100.0

        docs = db.query(TrustCenterDocument).filter(TrustCenterDocument.is_public == True).all()

        return TrustCenterOverviewResponse(
            status="OPERATIONAL",
            posture_statement="FocusBoard maintains active compliance readiness alignment with SOC 2 Trust Services Criteria, ISO/IEC 27001 ISMS principles, and GDPR privacy safeguards. We apply continuous security automation and least-privilege architecture.",
            encryption_in_transit="TLS 1.3 / HTTPS (ECDHE-RSA-AES128-GCM-SHA256)",
            encryption_at_rest="AES-256 GCM authenticated encryption",
            mfa_enforced=True,
            soc2_readiness_percentage=soc2_pct,
            iso27001_readiness_percentage=iso_pct,
            gdpr_readiness_percentage=gdpr_pct,
            public_documents=[TrustCenterDocumentResponse.model_validate(d) for d in docs],
            approved_subprocessors=BASELINE_SUBPROCESSORS,
        )
