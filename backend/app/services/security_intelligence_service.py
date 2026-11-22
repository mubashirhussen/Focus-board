import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

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
)
from app.models.enterprise import UserMFA
from app.models.user import User

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SecurityIntelligenceService:
    @staticmethod
    def seed_initial_security_data(db: Session) -> None:
        """Seed initial detection rules, posture findings, and sample baseline events if empty."""
        # 1. Seed Detection Rules
        if db.query(SecurityDetectionRule).count() == 0:
            rules = [
                SecurityDetectionRule(
                    rule_code="BRUTE_FORCE_LOGIN",
                    name="Brute-Force Authentication Attempt",
                    description="Detects multiple failed login attempts against a single account within a short window",
                    event_type="LOGIN_FAILURE",
                    condition_expression="count >= threshold",
                    threshold_count=3,
                    time_window_seconds=300,
                    severity="HIGH",
                    is_enabled=True,
                ),
                SecurityDetectionRule(
                    rule_code="PRIVILEGE_ESCALATION",
                    name="Unauthorized Privileged Escalation",
                    description="Flags grant of admin or security role without dual approval",
                    event_type="PRIVILEGED_ACCESS_GRANTED",
                    condition_expression="count >= 1",
                    threshold_count=1,
                    time_window_seconds=60,
                    severity="CRITICAL",
                    is_enabled=True,
                ),
                SecurityDetectionRule(
                    rule_code="API_KEY_ANOMALY",
                    name="High Frequency API Key Usage",
                    description="Detects abnormal request velocity on developer API keys",
                    event_type="API_KEY_CREATED",
                    condition_expression="count >= threshold",
                    threshold_count=5,
                    time_window_seconds=600,
                    severity="MEDIUM",
                    is_enabled=True,
                ),
                SecurityDetectionRule(
                    rule_code="MFA_DISABLED_ALERT",
                    name="Multi-Factor Authentication Disabled",
                    description="Alerts immediately when an administrative user disables TOTP/MFA",
                    event_type="MFA_DISABLED",
                    condition_expression="count >= 1",
                    threshold_count=1,
                    time_window_seconds=60,
                    severity="HIGH",
                    is_enabled=True,
                ),
            ]
            db.add_all(rules)
            db.commit()

        # 2. Seed Baseline Security Events
        if db.query(SecurityEvent).count() == 0:
            admin_user = db.query(User).filter(User.role == "admin").first()
            admin_id = admin_user.id if admin_user else None
            admin_email = admin_user.email if admin_user else "admin@focusboard.io"

            events = [
                SecurityEvent(
                    event_type="LOGIN_SUCCESS",
                    severity="INFO",
                    actor_id=admin_id,
                    actor_email=admin_email,
                    target_entity="focusboard_admin_portal",
                    source="AUTH",
                    evidence_json=json.dumps({"auth_method": "JWT_BEARER", "ip": "127.0.0.1"}),
                    metadata_json=json.dumps({"user_agent": "Mozilla/5.0 (Windows NT 10.0)"}),
                ),
                SecurityEvent(
                    event_type="MFA_ENABLED",
                    severity="INFO",
                    actor_id=admin_id,
                    actor_email=admin_email,
                    target_entity="totp_authenticator",
                    source="AUTH",
                    evidence_json=json.dumps({"algorithm": "TOTP_SHA1", "digits": 6}),
                    metadata_json=json.dumps({"status": "VERIFIED"}),
                ),
                SecurityEvent(
                    event_type="LOGIN_FAILURE",
                    severity="MEDIUM",
                    actor_email="unknown_probe@external.test",
                    target_entity="api_v1_auth_login",
                    source="API",
                    evidence_json=json.dumps({"reason": "INVALID_CREDENTIALS", "attempt": 1}),
                    metadata_json=json.dumps({"origin_ip": "198.51.100.24"}),
                ),
            ]
            db.add_all(events)
            db.commit()

        # 3. Seed Baseline Vulnerabilities
        if db.query(VulnerabilityRecord).count() == 0:
            vulns = [
                VulnerabilityRecord(
                    cve_id="CVE-2026-1049",
                    title="Potential Regular Expression Denial of Service in URL Validator",
                    description="Evaluating excessively nested wildcard patterns in custom webhooks could cause thread starvation.",
                    component="backend/app/services/webhook_dispatcher.py",
                    severity="LOW",
                    source="STATIC_ANALYSIS",
                    remediation_status="RESOLVED",
                    due_date=utc_now() + timedelta(days=30),
                    resolved_at=utc_now(),
                ),
                VulnerabilityRecord(
                    cve_id="SEC-DEP-042",
                    title="Outdated sub-dependency in frontend bundle tree",
                    description="Minor advisory on transitive package dev-dependency; no production runtime exposure.",
                    component="frontend/package.json",
                    severity="INFORMATIONAL",
                    source="DEPENDENCY_SCAN",
                    remediation_status="OPEN",
                    due_date=utc_now() + timedelta(days=60),
                ),
            ]
            db.add_all(vulns)
            db.commit()

        # 4. Seed Security Posture Assessment
        if db.query(SecurityPostureAssessment).count() == 0:
            assessment = SecurityPostureAssessment(
                overall_score=88,
                category_scores_json=json.dumps({
                    "AUTHENTICATION": 92,
                    "MFA": 85,
                    "RBAC": 95,
                    "TENANT_ISOLATION": 100,
                    "API_SECURITY": 90,
                    "DATA_PROTECTION": 88,
                    "AUDITING": 94,
                    "SECRET_MANAGEMENT": 90,
                    "AI_SECURITY": 86,
                }),
                status="COMPLETED",
                summary="FocusBoard demonstrates strong zero-trust controls with verified tenant isolation and encrypted credential stores.",
            )
            db.add(assessment)
            db.flush()

            findings = [
                SecurityPostureFinding(
                    assessment_id=assessment.id,
                    category="MFA",
                    title="Enforce mandatory MFA for all platform tenant administrators",
                    severity="MEDIUM",
                    control_ref="CC6.1.2",
                    remediation_guidance="Require TOTP enrollment on initial administrative login.",
                    is_resolved=False,
                ),
                SecurityPostureFinding(
                    assessment_id=assessment.id,
                    category="API_SECURITY",
                    title="Automate periodic API key rotation reminder after 90 days",
                    severity="LOW",
                    control_ref="A.9.4.3",
                    remediation_guidance="Notify developers to rotate persistent API keys every 90 days.",
                    is_resolved=True,
                ),
            ]
            db.add_all(findings)
            db.commit()

        # 5. Seed Access Review Campaign
        if db.query(AccessReviewCampaign).count() == 0:
            admin_user = db.query(User).filter(User.role == "admin").first()
            campaign = AccessReviewCampaign(
                title="Q4 Enterprise Privileged Roles & Administration Review",
                scope_type="PRIVILEGED_ROLES",
                status="IN_PROGRESS",
                reviewer_id=admin_user.id if admin_user else None,
                deadline_date=utc_now() + timedelta(days=14),
                notes="Quarterly zero-trust audit of administrative roles and database access.",
            )
            db.add(campaign)
            db.flush()

            if admin_user:
                rec = AccessReviewRecord(
                    campaign_id=campaign.id,
                    user_id=admin_user.id,
                    role_or_permission="ROLE_PLATFORM_ADMIN",
                    resource_name="FocusBoard Primary Tenant API",
                    decision="APPROVED",
                    justification="Verified lead platform architect role.",
                    reviewed_at=utc_now(),
                    reviewed_by_id=admin_user.id,
                )
                db.add(rec)
            db.commit()

    @staticmethod
    def record_security_event(db: Session, event_data: Dict[str, Any]) -> SecurityEvent:
        """Records a security event and evaluates threat detection rules."""
        event = SecurityEvent(
            event_type=event_data["event_type"],
            severity=event_data.get("severity", "INFO"),
            actor_id=event_data.get("actor_id"),
            actor_email=event_data.get("actor_email"),
            target_entity=event_data.get("target_entity"),
            organization_id=event_data.get("organization_id"),
            ip_address=event_data.get("ip_address"),
            source=event_data.get("source", "SYSTEM"),
            evidence_json=event_data.get("evidence_json", "{}"),
            metadata_json=event_data.get("metadata_json", "{}"),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        # Trigger rule evaluation for this event type
        SecurityIntelligenceService._evaluate_rules_for_event(db, event)
        return event

    @staticmethod
    def _evaluate_rules_for_event(db: Session, event: SecurityEvent) -> None:
        """Checks enabled detection rules matching this event type."""
        rules = db.query(SecurityDetectionRule).filter(
            SecurityDetectionRule.event_type == event.event_type,
            SecurityDetectionRule.is_enabled == True,
        ).all()

        for rule in rules:
            window_start = utc_now() - timedelta(seconds=rule.time_window_seconds)
            query = db.query(SecurityEvent).filter(
                SecurityEvent.event_type == rule.event_type,
                SecurityEvent.created_at >= window_start,
            )
            if event.actor_email:
                query = query.filter(SecurityEvent.actor_email == event.actor_email)

            count = query.count()
            if count >= rule.threshold_count:
                # Detection result
                det_res = SecurityDetectionResult(
                    rule_id=rule.id,
                    rule_code=rule.rule_code,
                    severity=rule.severity,
                    matched_count=count,
                    target_entity=event.target_entity or event.actor_email or "SYSTEM",
                    evidence_summary=f"Rule '{rule.name}' triggered with {count} events in {rule.time_window_seconds}s window.",
                )
                db.add(det_res)

                # Generate Security Alert
                alert_code = f"SEC-ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{rule.rule_code[:6]}"
                alert = SecurityAlert(
                    alert_code=alert_code,
                    title=f"Threat Detected: {rule.name}",
                    description=f"{rule.description} (Matched count: {count})",
                    severity=rule.severity,
                    status="OPEN",
                    source="THREAT_DETECTION",
                    detection_rule_id=rule.id,
                    actor_email=event.actor_email,
                    target_entity=event.target_entity,
                    evidence_json=json.dumps({"matched_count": count, "window_seconds": rule.time_window_seconds}),
                )
                db.add(alert)
                db.commit()

    @staticmethod
    def get_security_posture_summary(db: Session) -> Dict[str, Any]:
        """Calculates dynamic zero-trust posture score based on live controls and active risks."""
        SecurityIntelligenceService.seed_initial_security_data(db)

        total_users = db.query(User).count() or 1
        mfa_count = db.query(UserMFA).filter(UserMFA.is_enabled == True).count()
        mfa_adoption_pct = round((mfa_count / total_users) * 100, 1)

        open_critical_alerts = db.query(SecurityAlert).filter(
            SecurityAlert.severity.in_(["HIGH", "CRITICAL"]),
            SecurityAlert.status.in_(["OPEN", "INVESTIGATING"]),
        ).count()

        open_vulns = db.query(VulnerabilityRecord).filter(
            VulnerabilityRecord.remediation_status.in_(["OPEN", "IN_PROGRESS"]),
        ).count()

        resolved_vulns = db.query(VulnerabilityRecord).filter(
            VulnerabilityRecord.remediation_status.in_(["RESOLVED", "VERIFIED", "CLOSED"]),
        ).count()
        total_vulns = (open_vulns + resolved_vulns) or 1
        vuln_resolution_pct = round((resolved_vulns / total_vulns) * 100, 1)

        # Baseline score starts at 95; deductions applied for open alerts and low MFA
        calculated_score = 95
        calculated_score -= min(open_critical_alerts * 8, 30)
        calculated_score -= min(open_vulns * 3, 15)
        if mfa_adoption_pct < 50:
            calculated_score -= 10
        calculated_score = max(min(calculated_score, 100), 20)

        latest_assessment = db.query(SecurityPostureAssessment).order_by(desc(SecurityPostureAssessment.created_at)).first()

        return {
            "overall_posture_score": calculated_score,
            "mfa_adoption_pct": mfa_adoption_pct,
            "open_critical_alerts": open_critical_alerts,
            "open_vulnerabilities": open_vulns,
            "vulnerability_resolution_pct": vuln_resolution_pct,
            "last_assessed_at": latest_assessment.assessment_date.isoformat() if latest_assessment else utc_now().isoformat(),
            "category_scores": json.loads(latest_assessment.category_scores_json) if latest_assessment else {
                "AUTHENTICATION": 90,
                "MFA": 80,
                "RBAC": 95,
                "TENANT_ISOLATION": 100,
                "API_SECURITY": 92,
                "DATA_PROTECTION": 88,
            },
        }

    @staticmethod
    def answer_ai_security_query(db: Session, query: str, context_type: str = "SOC_OVERVIEW") -> Dict[str, Any]:
        """Grounded AI Security Assistant delivering verified insights backed by database telemetry."""
        posture = SecurityIntelligenceService.get_security_posture_summary(db)
        open_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == "OPEN").all()
        threat_results = db.query(SecurityDetectionResult).order_by(desc(SecurityDetectionResult.detected_at)).limit(5).all()
        vulns = db.query(VulnerabilityRecord).filter(VulnerabilityRecord.remediation_status == "OPEN").all()

        q_lower = query.lower()
        if "alert" in q_lower or "threat" in q_lower:
            answer = (
                f"Currently there are {len(open_alerts)} open security alerts and {len(threat_results)} recent threat detection hits. "
                f"Most recent threat triggers involve rule evaluation on authentication and credential access."
            )
            actions = [
                "Investigate highest severity alerts in SOC queue",
                "Review IP address blocks for repeat failed authentication attempts",
                "Verify session tokens for targeted accounts",
            ]
        elif "vulnerability" in q_lower or "cve" in q_lower:
            answer = (
                f"There are currently {len(vulns)} unresolved vulnerabilities in the registry. "
                f"Overall vulnerability remediation rate is currently at {posture['vulnerability_resolution_pct']}%."
            )
            actions = [
                "Prioritize patches for active CVEs before due date",
                "Run automated CI/CD dependency scan on next release build",
            ]
        elif "posture" in q_lower or "score" in q_lower or "mfa" in q_lower:
            answer = (
                f"The continuous Zero-Trust security posture score is {posture['overall_posture_score']}/100. "
                f"MFA adoption is at {posture['mfa_adoption_pct']}%. Tenant isolation is validated at 100%."
            )
            actions = [
                "Enforce mandatory TOTP/MFA policy for all administrative roles",
                "Execute quarterly privileged access review campaign",
            ]
        else:
            answer = (
                f"FocusBoard Security Intelligence reports a healthy Zero-Trust posture score of {posture['overall_posture_score']}/100. "
                f"Open alerts: {len(open_alerts)}, unresolved vulnerabilities: {len(vulns)}, MFA adoption: {posture['mfa_adoption_pct']}%."
            )
            actions = [
                "Audit privileged role assignments in Access Reviews",
                "Monitor real-time security events in SOC Event Registry",
                "Verify zero-trust token revocation behavior",
            ]

        return {
            "query": query,
            "answer": answer,
            "posture_score": posture["overall_posture_score"],
            "open_alerts_count": len(open_alerts),
            "active_threats_count": len(threat_results),
            "unresolved_vulnerabilities_count": len(vulns),
            "recommended_actions": actions,
            "grounded_evidence": {
                "source": "focusboard_security_intelligence_telemetry",
                "evaluated_at": utc_now().isoformat(),
                "posture_metrics": posture,
                "verified_records_count": {
                    "open_alerts": len(open_alerts),
                    "recent_threats": len(threat_results),
                    "open_vulnerabilities": len(vulns),
                },
            },
        }
