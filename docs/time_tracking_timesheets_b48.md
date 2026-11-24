# FocusBoard Module B48: Time Tracking & Timesheets Architecture & Implementation

## 1. Overview & Objective
Module B48 implements a production-ready, comprehensive Time Tracking & Timesheets system inside FocusBoard. It bridges user productivity, task execution effort, project budget controls, and enterprise managerial review workflows.

Key Capabilities:
- **Active Timer Engine:** Live timer ticker, single active timer constraint, start/pause/resume/stop/cancel operations, and automatic task `actual_minutes` progression.
- **Manual Time Entries:** Flexible manual logging, max duration enforcement, and tamper-resistant audit logs.
- **Timesheet Workflow:** Automated weekly and monthly aggregation of logged hours with a multi-state review lifecycle (`DRAFT` $\to$ `SUBMITTED` $\to$ `APPROVED` / `REJECTED` $\to$ `REOPENED`).
- **Managerial Governance:** Role-based permissions (`ADMIN`, `OWNER`, `MANAGER`) for team timesheet approvals, feedback comments, and protected entry locks.
- **Financial Analytics & Reporting:** Real-time billable vs non-billable ratios, hourly rate billing amounts, and project-level time distributions.

---

## 2. Database Models & Schema Design
Implemented in `backend/app/models/time_tracking.py` with Alembic migration `036_b48_time_tracking_and_timesheets.py`:

| Table | Responsibility | Key Relationships |
|---|---|---|
| `time_entries` | Immutable / locked record of logged time | `users`, `projects`, `tasks`, `timesheets` |
| `active_timers` | Real-time state of running/paused timers | `users`, `projects`, `tasks` |
| `timesheets` | Weekly / monthly aggregated billing records | `users`, `organizations` |
| `timesheet_approvals` | Immutable review decisions and audit notes | `timesheets`, `users (reviewer)` |
| `time_tracking_settings` | Workspace policy (rates, approval flags, limits) | `organizations`, `users` |
| `time_entry_audit_logs` | Tamper-evident change logs on entries | `time_entries`, `users` |

---

## 3. API Endpoints
All endpoints are mounted under `/api/v1/time-tracking` and aliased at `/time-tracking`:

### Timer Operations
- `GET /time-tracking/timer/active`: Get currently running/paused timer.
- `POST /time-tracking/timer/start`: Start running timer (or switch tasks).
- `POST /time-tracking/timer/pause`: Pause active timer.
- `POST /time-tracking/timer/resume`: Resume paused timer.
- `POST /time-tracking/timer/stop`: Stop timer, record `TimeEntry`, and increment task `actual_minutes`.
- `POST /time-tracking/timer/cancel`: Cancel and discard active timer.

### Time Entries
- `GET /time-tracking/entries`: Query user's logged time entries with filters.
- `POST /time-tracking/entries`: Create manual time entry.
- `PUT /time-tracking/entries/{id}`: Update time entry (prevented if approved).
- `DELETE /time-tracking/entries/{id}`: Delete time entry (prevented if approved).

### Timesheets & Approvals
- `GET /time-tracking/timesheets`: List timesheets (self or team if manager).
- `POST /time-tracking/timesheets`: Generate or fetch weekly/monthly timesheet.
- `GET /time-tracking/timesheets/{id}`: Retrieve full timesheet breakdown with approval logs.
- `POST /time-tracking/timesheets/{id}/submit`: Submit timesheet for manager review.
- `POST /time-tracking/timesheets/{id}/withdraw`: Withdraw submitted timesheet back to draft.
- `POST /time-tracking/timesheets/{id}/approve`: Manager approval with comments.
- `POST /time-tracking/timesheets/{id}/reject`: Manager rejection with comments.
- `POST /time-tracking/timesheets/{id}/reopen`: Manager reopen to draft for corrections.

### Analytics & Reports
- `GET /time-tracking/summary`: Dashboard KPIs (today's hours, this week, billable ratio).
- `GET /time-tracking/reports/project`: Project-level time and billing breakdown.
- `GET /time-tracking/reports/user`: Team member utilization (managers only).
- `GET /time-tracking/reports/billable`: Billable vs non-billable hours & revenue.
- `GET /time-tracking/settings`: Workspace time policies.
- `PUT /time-tracking/settings`: Update time tracking preferences.

---

## 4. Frontend Architecture
- **API Client:** `src/services/timeTrackingApi.js` provides typed HTTP client operations.
- **Dashboard:** `src/pages/TimeTracking/TimeTrackingDashboard.jsx` & `.css` provides:
  1. Live active timer header ticker with project/task selectors and billable toggle.
  2. Overview KPI cards for daily/weekly hours and billable ratios.
  3. Logged entries table with manual entry modal.
  4. Weekly timesheet summary and submission button.
  5. Managerial review interface with approval/rejection modals.
  6. Financial reports and project time distribution.
- **Navigation:** Integrated into `App.jsx`, `Sidebar.jsx`, and `MobileDrawer.jsx`.
