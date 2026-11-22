# FocusBoard Developer Platform & Public API Guide

The FocusBoard Developer Platform (Phase 40) enables third-party developers and enterprise customers to integrate custom workflows, query workspace entities, and manage automation through a secure public API.

---

## 1. Authentication & API Key Management

FocusBoard APIs support Bearer tokens and Scoped Developer API Keys:

- Headers:
  ```http
  Authorization: Bearer <access_token>
  X-Workspace-ID: <workspace_id>
  ```
- Scopes:
  - `tasks:read`, `tasks:write`
  - `projects:read`, `projects:write`
  - `automation:read`, `automation:write`
  - `webhooks:read`, `webhooks:write`

---

## 2. Core Endpoints

### Automation Intelligence
- `GET /api/v1/automation/overview`: Workspace automation analytics.
- `GET /api/v1/automation/workflows`: List registered workflows.
- `POST /api/v1/automation/workflows`: Create workflow with node-edge definition.
- `PATCH /api/v1/automation/workflows/{id}`: Update configuration and increment minor version.
- `POST /api/v1/automation/workflows/{id}/trigger`: Trigger manual or dry-run execution.
- `GET /api/v1/automation/executions`: Query historical runs.
- `GET /api/v1/automation/executions/{id}/logs`: Retrieve step-level execution logs.
- `GET /api/v1/automation/approvals`: List pending human review requests.
- `POST /api/v1/automation/approvals/{id}/decision`: Submit `APPROVED` or `REJECTED`.
- `POST /api/v1/automation/assistant/generate`: Synthesize workflows from natural language.

### Integration Platform
- `GET /api/v1/integration-platform/providers`: Catalog of available OAuth connectors.
- `GET /api/v1/integration-platform/marketplace/listings`: Browse published apps.
- `POST /api/v1/integration-platform/marketplace/install`: Install app with explicit permission consent.
- `GET /api/v1/integration-platform/connectors`: Monitor connection status of OAuth providers.
- `POST /api/v1/integration-platform/connectors/connect`: Connect an OAuth provider.
- `POST /api/v1/integration-platform/connectors/{id}/disconnect`: Disconnect an OAuth provider.
- `POST /api/v1/integration-platform/webhooks/test`: Test dispatch and cryptographic signature verification.
- `GET /api/v1/integration-platform/analytics`: Real-time API traffic, latency, and webhook metrics.
