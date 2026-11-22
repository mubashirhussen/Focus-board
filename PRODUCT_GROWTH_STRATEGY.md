# FocusBoard Product-Led Growth (PLG) & User Activation Strategy
## Phase 28 Architecture, Funnel Telemetry & Onboarding Lifecycle

FocusBoard implements a native **Product-Led Growth (PLG)** engine engineered to accelerate user time-to-value (TTV), maximize activation rates, and convert free-tier workspaces into long-term enterprise customers through deterministic product experiences.

---

## 1. Core Onboarding & Activation Funnel

FocusBoard's activation funnel is strictly deterministic, measured from account creation through core workflow completion:

```
[ Signup ] ──> [ Workspace Created ] ──> [ Project Configured ] ──> [ First Task Created ] ──> [ First Task Completed ]
```

### Deterministic Milestones
| Milestone | Event Identifier | Required Database Evidence |
| :--- | :--- | :--- |
| **1. Signup** | `onboarding_started` | User record created in `users` |
| **2. Workspace Creation** | `workspace_created` | Record in `workspaces` with user as owner/admin |
| **3. Project Configuration** | `project_created` | Project record linked to workspace |
| **4. Task Creation** | `task_created` | Task record created in `tasks` |
| **5. Task Completion (Activation)**| `task_completed` | Task updated to `COMPLETED` status |

**Activation Definition**: A user is considered **Activated** when they complete their first task within 72 hours of signup. This indicates that the core value loop (Capture -> Plan -> Execute) has been achieved.

---

## 2. Interactive Onboarding Experience

1. **Goal Selection Modal (`OnboardingModal.jsx`)**:
   - Step 1: Users declare their intent (`personal_productivity` vs `team_productivity`).
   - Step 2: Workspace environment configuration (Personal Sandbox vs Team Space).
   - Step 3: Fast-track creation of the first high-priority task.
2. **Persistent Checklist Widget (`OnboardingChecklist.jsx`)**:
   - Pinned to the user's dashboard until completed or explicitly dismissed.
   - Real-time progress bar (0% - 100%) tracking completion across core milestones.
   - Clickable tasks navigate directly to the relevant workspace views.

---

## 3. Behavioral Telemetry & Privacy-Safe Event Tracking

Telemetry is collected through the backend route `POST /api/v1/growth/events`:
- **Allowed Events Registry**: Only pre-registered event names in `ALLOWED_GROWTH_EVENTS` are permitted (e.g. `onboarding_started`, `task_created`, `kb_article_viewed`, `feedback_submitted`). Unregistered events are rejected with HTTP 400.
- **Strict Privacy Isolation**:
  - No task titles, descriptions, focus notes, or personal identifiers are stored in `properties_json`.
  - Stored metadata is strictly behavioral (e.g. step number, role type, source client).

---

## 4. In-App Feedback Loop & Roadmap Pipeline

Qualitative feedback is collected directly from users via `FeedbackModal.jsx`:
- **Categories**: Feature Requests, Bug Reports, UX Enhancements, General Comments.
- **Rating**: 1 to 5 star rating.
- **Triage**: Admins review and prioritize feedback via `PATCH /api/v1/growth/feedback/{id}`, adding internal notes and transitioning items to public roadmap entries.
