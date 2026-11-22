# FocusBoard — External Integrations, Calendar Synchronization & Workflow Automations

## 1. Integrations Hub
The Integration Hub allows users to connect third-party platforms to FocusBoard:
- **Google Calendar**: Two-way synchronization for scheduled tasks, deadlines, and smart meeting conflict detection.
- **Slack Notifications**: Automated notifications for task updates and team assignments.
- **GitHub Issues**: Cross-link engineering tasks with repository branches and PRs.

---

## 2. Google Calendar Synchronization Engine
- **OAuth 2.0 Authentication**: Generates state tokens with CSRF nonces, securely exchanges authorization codes, and encrypts access/refresh tokens at rest.
- **Bidirectional Event Mapping**: Persists mappings in `calendar_sync_mappings` (`integration_id`, `task_id`, `external_calendar_id`, `external_event_id`) to prevent duplicate calendar events.
- **Side-by-side View**: External calendar events appear alongside FocusBoard tasks in the unified agenda timeline.
- **Conflict & Collision Detection**:
  - `detect_calendar_conflicts()`: Identifies overlapping events and tasks scheduled outside working hours (default 9:00 AM - 6:00 PM).

---

## 3. Event-Driven Workflow Automation Engine
- **Triggers**:
  - `task_created`
  - `task_completed`
  - `task_overdue`
  - `calendar_sync_completed`
- **Condition Matching**: Filters events by field (e.g. `priority == 'High'`, `category == 'Design'`).
- **Actions**: Generates in-app notifications, logs audit records, or dispatches emails.
- **Loop & Recursion Protection**: Enforces a strict execution depth cap (`MAX_EXECUTION_DEPTH = 3`) to prevent recursive execution cascades.
