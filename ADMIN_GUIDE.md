# FocusBoard: Enterprise Administration & Governance Guide

## 1. Overview
The Enterprise Administration portal enables organization owners and security officers to configure security guardrails, manage fine-grained roles, verify corporate email domains, and audit compliance logs.

---

## 2. Security Governance Policies
Access via **Enterprise Admin > Security Policies**:
- **Enforce Multi-Factor Authentication (MFA)**: Mandates that all workspace members set up RFC 6238 TOTP authentication before accessing organizational resources.
- **Corporate Domain Restriction**: Restricts workspace invitations and self-registrations to pre-approved corporate email domains.
- **AI Privacy & Zero-Retention**: Enforces zero-retention policies so prompt payloads and task telemetry are never stored for third-party model training.

---

## 3. Custom RBAC Roles Manager
Create custom roles with specific capability-based permission sets:
- `organization.*` (Read, Update, Policies)
- `workspace.*` (Create, Read, Update, Delete)
- `project.*` (Create, Read, Update, Delete)
- `task.*` (Create, Read, Update, Delete)
- `billing.*` (Read, Manage)
- `audit.*` (Read, Export)

---

## 4. Corporate Domain Verification
1. Navigate to **Verified Domains**.
2. Enter your company domain (e.g. `acme-corp.com`).
3. Add the generated DNS TXT record (`focusboard-domain-verification=fb-token-...`) at your DNS registrar.
4. Click **Verify DNS Record** to activate automatic domain member matching.

---

## 5. Compliance Audit Log Export
- Navigate to **Compliance Audit Trail**.
- Click **Export Audit Log (CSV)** to download a sanitized, RFC-compliant CSV record of all authentication, administrative, and policy modifications.
- Note: The export action itself is recorded immutably in the compliance trail.
