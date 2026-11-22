# Runbook: Security Incident & Credential Compromise

## 1. Trigger & Severity
- **Trigger**: Suspected credential breach, unauthorized privilege escalation, anomaly in audit logs, or credential leak.
- **Severity**: **SEV-1**.

## 2. Immediate Diagnostic Steps
1. Review tamper-evident audit logs:
   `GET /api/v1/enterprise/audit/export`
2. Check for suspicious IP addresses, failed login bursts, or unexpected role modifications.
3. Identify affected user accounts or organization workspaces.

## 3. Containment & Remediation
- **Step 1: Session Revocation & JWT Invalidation**:
  Rotate `SECRET_KEY` in the backend environment variables immediately. This invalidates all outstanding JWT tokens across the system and forces re-authentication.
- **Step 2: Credential Rotation**:
  Rotate database passwords, cloud API tokens, Stripe keys, and SMTP credentials.
- **Step 3: Enforce MFA**:
  Enable `mfa_enforced` organization policy via Enterprise Admin to require TOTP on subsequent logins.
- **Step 4: Account Suspension**:
  Deactivate compromised accounts by setting `is_active = False` in database.

## 4. Post-Incident Review
Conduct a blameless post-mortem, document attack vector, preserve forensic logs, and notify affected users in accordance with GDPR requirements.
