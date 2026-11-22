# FocusBoard Customer Support & Operations Guide
## Phase 29 Enterprise Support Automation, SLA Governance & Knowledge Base

FocusBoard provides a built-in enterprise customer operations suite that bridges self-service documentation, support ticketing with automated SLAs, agent internal notes, and public roadmap feedback.

---

## 1. Support Ticketing & SLA Deadlines

Every support ticket created in FocusBoard (`POST /api/v1/support/tickets`) receives an automatic **Service Level Agreement (SLA) deadline** calculated based on its declared priority:

| Priority | SLA Deadline Window | Target Response / Resolution | Escalation Policy |
| :--- | :--- | :--- | :--- |
| **URGENT** | **1 Hour** | Critical production outages / data export blocks | Pager duty & Admin notification |
| **HIGH** | **4 Hours** | Major feature regressions or billing issues | High-priority queue banner |
| **NORMAL** | **24 Hours** | General technical guidance and configuration | Standard agent triage |
| **LOW** | **72 Hours** | Minor polish, questions, or non-blocking feedback | Backlog assignment |

---

## 2. Customer Isolation & Support Agent Internal Notes

FocusBoard enforces strict isolation between public ticket conversations and private agent notes:

1. **Customer View**:
   - Customers can only see their own tickets and public replies from support agents.
   - Internal notes (`is_internal_note: true`) are **completely filtered out** at the database query level by `get_ticket_messages`.
   - Attempts by customers to post internal notes return `HTTP 403 Forbidden`.
2. **Support Agent / Admin View**:
   - Support agents (`Admin` or `Owner` roles) see all tickets across the workspace.
   - Internal notes are rendered with a distinct gold/amber border (`.internal-note`) and labeled `Agent Internal Note`.
   - Agents can post root-cause analyses, handover instructions, and customer history privately without exposing them to the requester.

---

## 3. Self-Service Knowledge Base

The Knowledge Base (`GET /api/v1/support/kb/articles`) provides instant answers to common platform questions, reducing support ticket volume:
- **Pre-Seeded Core Categories**:
  - `Getting Started`: Task lifecycle, status columns, keyboard shortcuts.
  - `Integrations & Sync`: Google Calendar OAuth, Webhook events, offline PWA caching.
  - `Security & Governance`: TOTP MFA configuration, RBAC permissions, audit logging.
- **Interactive Voting**:
  - Users can vote `Helpful` or `Not Helpful` on each article via `POST /api/v1/support/kb/articles/{id}/vote`.
  - Articles maintain real-time telemetry on documentation effectiveness.

---

## 4. Transparent Product Roadmap & Upvoting

The Public Roadmap (`GET /api/v1/support/roadmap`) provides user visibility into current engineering initiatives:
- **Columns**: `Planned`, `In Development`, and `Completed`.
- **Community Upvoting**: Users can upvote features (`POST /api/v1/support/roadmap/{id}/vote`) to signal demand directly to product teams.
