# FocusBoard Developer Platform & Ecosystem (Phase 33)

## 1. Overview
The **FocusBoard Developer Platform** allows engineers, partners, and internal tool builders to integrate with FocusBoard programmatically through scoped API keys, real-time webhooks, and official SDKs.

---

## 2. Key Architecture Concepts

### Applications & Scopes
Every external integration is registered under a `DeveloperApplication`:
- `INTERNAL`: Custom company scripts, CI/CD pipelines, Slack bots.
- `PARTNER`: B2B integrations and marketplace connectors.
- `PUBLIC`: Mobile and desktop clients.

### Granular Scopes
| Scope | Capability |
| :--- | :--- |
| `tasks:read` | Query tasks, comments, and task history |
| `tasks:write` | Create, update, block, and delete tasks |
| `projects:read` | View projects, milestones, and status |
| `projects:write` | Create projects and adjust deadlines |
| `analytics:read` | Query executive portfolio health scores |
| `webhooks:manage`| Register and modify webhook endpoints |

---

## 3. Cryptographic API Key Security
- **Key Format**: `fb_live_<48 hex chars>`
- **Storage**: Plaintext keys are **never stored** in the database.
- FocusBoard stores a cryptographic **SHA-256 hash** of the key.
- The user is displayed the plaintext key **only once** upon generation.
- Prefix `fb_live_xxxx...` is stored for easy identification and revocation in the Developer Portal.

---

## 4. Idempotency Support
Mutating endpoints (`POST /api/v1/public/v1/tasks`) support the standard `Idempotency-Key` header:
- Safe against network retries and transient failures.
- Caches response code and body for 24 hours.
- Repeated calls with the same key return the original response without duplicate side effects.
