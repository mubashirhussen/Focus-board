# FocusBoard Security Intelligence & Zero-Trust Architecture Guide (Phase 43)

## 1. Overview
Phase 43 elevates FocusBoard into an enterprise-grade, security-first platform operating under strict Zero-Trust principles ("Never Trust, Always Verify").

The Security Operations Center (SOC) provides continuous visibility into:
- Continuous Zero-Trust Security Posture Assessment (Score out of 100).
- Centralized Security Event Registry & Audit Logging.
- Configurable Threat Detection Rules & Automated Alert Generation.
- Identity Security, MFA Adoption, and Privileged Entitlement Reviews.
- Vulnerability Management & CVE Tracking.
- Grounded AI Security Analyst grounded in real application telemetry.

---

## 2. Architecture & Data Models

| Model | Table Name | Purpose |
|---|---|---|
| `SecurityEvent` | `security_events` | Immutable security audit log tracking logins, privilege escalation, MFA, API key events. |
| `SecurityDetectionRule` | `security_detection_rules` | Rule engine with threshold counts and sliding time windows. |
| `SecurityDetectionResult` | `security_detection_results` | Results recorded when a threat rule is triggered by security events. |
| `SecurityAlert` | `security_alerts` | Security alert lifecycle (`OPEN`, `ACKNOWLEDGED`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`). |
| `IdentityRiskRecord` | `identity_risk_records` | Flags accounts with anomalous failed login velocity or missing MFA. |
| `AccessReviewCampaign` | `access_review_campaigns` | Periodic campaigns reviewing administrative and privileged role grants. |
| `AccessReviewRecord` | `access_review_records` | Granular reviewer decisions (`APPROVED`, `REVOKED`, `ESCALATED`) per user role entitlement. |
| `VulnerabilityRecord` | `vulnerability_records` | CVE tracking from static analysis, dependency scanning, or penetration tests. |
| `SecurityPostureAssessment` | `security_posture_assessments` | Periodic posture assessments across authentication, MFA, RBAC, tenant isolation, etc. |
| `SecurityPostureFinding` | `security_posture_findings` | Specific remediation findings linked to security control references. |
| `SecurityRemediation` | `security_remediations` | Action items tracking owner and verification dates. |

---

## 3. Threat Detection Engine

The threat detection engine evaluates events in real time:
- **Brute-Force Detection**: 3+ failed logins within 300 seconds flags suspicious IPs/accounts.
- **Privilege Escalation**: Immediate alert on administrative or security role grants.
- **API Key Anomaly**: High-frequency creation of developer credentials triggers investigation.
- **MFA Disabled**: Immediate alert when an administrator disables multi-factor authentication.

---

## 4. API Endpoints

- `GET /api/v1/security-intelligence/posture` — Dynamic zero-trust posture score and category breakdowns.
- `GET /api/v1/security-intelligence/events` — Filterable audit log of security events.
- `POST /api/v1/security-intelligence/events` — Log application security event and trigger threat rules.
- `GET /api/v1/security-intelligence/alerts` — Active alerts with severity and status filters.
- `PATCH /api/v1/security-intelligence/alerts/{id}` — Triage and mark alerts resolved.
- `GET /api/v1/security-intelligence/access-reviews` — Review campaigns and role entitlement items.
- `PATCH /api/v1/security-intelligence/access-reviews/{campaign_id}/records/{id}` — Approve or revoke role permissions.
- `GET /api/v1/security-intelligence/vulnerabilities` — List tracked CVEs.
- `POST /api/v1/security-intelligence/ai/query` — Grounded AI Security Analyst natural language query.
