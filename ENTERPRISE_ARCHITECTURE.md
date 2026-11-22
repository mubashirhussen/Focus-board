# FocusBoard Enterprise Architecture & Governance Specification

## 1. Overview
The **Enterprise Administration, RBAC & Governance** module (Phase 23) equips FocusBoard with enterprise-ready access governance, granular role-based authorization, domain verification, two-factor authentication, and compliance audit trail exports.

---

## 2. Core Security & Governance Subsystems

### 2.1 Granular Role-Based Access Control (RBAC)
Located in `backend/app/services/rbac_service.py` and `backend/app/models/enterprise.py`:
- Granular capability-based permissions format: `<domain>.<action>`:
  - `organization.read`, `organization.update`, `organization.policies`
  - `workspace.create`, `workspace.read`, `workspace.update`, `workspace.delete`
  - `project.create`, `project.read`, `project.update`, `project.delete`
  - `task.create`, `task.read`, `task.update`, `task.delete`
  - `billing.read`, `billing.manage`
  - `integration.manage`
  - `audit.read`, `audit.export`
- Dynamic role evaluation:
  - Built-in roles: `Owner` (all permissions), `Admin`, `Member`, `Viewer`.
  - Custom roles: Persisted in `CustomRole` table with custom permission sets.
  - Decorator / Dependency: `require_permission(permission_name)` inspects user role, custom role assignments, and organizational boundaries.

### 2.2 Organization Governance & Security Policies
Model: `OrganizationPolicy` in `backend/app/models/enterprise.py`:
- `mfa_enforced`: Mandates TOTP two-factor authentication for all workspace members.
- `domain_restriction`: Restricts membership and invitations to pre-approved corporate domains.
- `workspace_creation_limit`: Caps the maximum allowable workspaces across the organization.
- `ai_governance`: Enforces strict data zero-retention policies for AI task planning and assistant interactions.

### 2.3 Verified Corporate Domains
Model: `OrganizationDomain` in `backend/app/models/enterprise.py`:
- Allows organizations to register their corporate domains (e.g. `acme-corp.com`).
- Generates unique DNS TXT verification tokens: `focusboard-domain-verification=fb-token-...`.
- Verification endpoint validates token presence before enabling domain-level user auto-provisioning.

### 2.4 Pure-Python RFC 6238 TOTP Multi-Factor Authentication
Located in `backend/app/services/mfa_service.py`:
- **Zero Heavy C-Dependencies**: Pure Python implementation using standard library `hmac`, `hashlib`, `struct`, `base64`, and `secrets`.
- Compatible with all standard authenticator apps (Google Authenticator, Microsoft Authenticator, 1Password, Authy).
- Generates standard `otpauth://totp/...` URIs.
- Includes 8 single-use, cryptographically hashed emergency backup recovery codes.

### 2.5 Compliance Audit Trail & Forensics Export
- Endpoint: `GET /api/v1/enterprise/audit/export`.
- Exports all security-relevant events (`auth.login`, `auth.mfa_enabled`, `policy.update`, `role.create`, `domain.verify`, etc.) to sanitized CSV.
- **Forensic Self-Auditing**: The act of downloading an audit export is itself recorded immediately in the immutable audit log.

---

## 3. Database Schema (Alembic Migration 005)
- `organization_policies`
- `custom_roles`
- `organization_domains`
- `enterprise_invitations`
- `user_mfa`
- `productivity_events`
- `intelligence_preferences`
- `insight_feedback`
