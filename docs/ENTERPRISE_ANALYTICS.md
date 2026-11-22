# FocusBoard Enterprise Intelligence & Executive Dashboards (Phase 32)

## 1. Overview
The **FocusBoard Enterprise Intelligence & Executive Decision Support System** provides real-time portfolio oversight, strategic project health assessments, explainable delivery signals, predictive forecasts, and team capacity planning.

---

## 2. Architecture & Metrics Roll-up

```
┌────────────────────────────────────────────────────────┐
│              Executive Dashboard Overview              │
├─────────────────┬───────────────────┬──────────────────┤
│ Portfolio Health│ On-Time Delivery  │ Team Saturation  │
│      94.5%      │       91.2%       │      72.4%       │
└────────┬────────┴─────────┬─────────┴────────┬─────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────────┐┌──────────────────┐┌──────────────────┐
│ Portfolio Health ││ Risk Detection   ││ Capacity Engine  │
│  Engine (0-100)  ││ (Schedule, Load, ││ (40h/wk Baseline │
│  & Signals       ││  Blockers)       ││  vs Allocations) │
└──────────────────┘└──────────────────┘└──────────────────┘
```

### Executive KPI Metrics
- **Portfolio Health Average**: Mean health score across all active projects in the workspace.
- **Active Projects vs Total Projects**: Volume of ongoing delivery initiatives.
- **On-Time Delivery Rate**: Ratio of completed tasks to overdue tasks.
- **Workload Saturation Percentage**: Aggregate team allocated hours vs total weekly capacity.
- **Active & Critical Risk Counts**: Live risk items categorized by severity (Critical, High, Medium, Low).

---

## 3. Project Health & Risk Management
- **Deterministic Health Scoring**:
  - `HEALTHY` (Score 80-100): On track with zero blocking risks.
  - `AT_RISK` (Score 50-79): Approaching deadline with overdue tasks or high severity risks.
  - `CRITICAL` (Score 0-49): Overdue deadline or multiple critical blockers.
  - `INSUFFICIENT_DATA`: Project has no tasks tracked yet.
- **Explainable Signals**: Every score breakdown explains exact deductions (e.g. *"2 of 5 open tasks are past their deadline"*, *"Active critical risk: Vendor API migration pending"*).
- **Statistical Forecasting**: Uses 14-day completion velocity to forecast delivery ranges with honest fallback handling.

---

## 4. API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/enterprise-analytics/executive-summary` | `GET` | Roll-up KPIs and saturation metrics |
| `/api/v1/enterprise-analytics/portfolio-health` | `GET` | Health scores, signals, and forecasts |
| `/api/v1/enterprise-analytics/projects/{id}/health` | `GET` | Detailed project health assessment |
| `/api/v1/enterprise-analytics/projects/{id}/milestones`| `GET`, `POST` | Project milestones management |
| `/api/v1/enterprise-analytics/milestones/{id}` | `PATCH`, `DELETE`| Milestone status & date updates |
| `/api/v1/enterprise-analytics/projects/{id}/risks` | `GET`, `POST` | Risk register operations |
| `/api/v1/enterprise-analytics/risks/{id}` | `PATCH` | Risk mitigation & resolution |
| `/api/v1/enterprise-analytics/team-workload` | `GET` | Team capacity and utilization rates |
| `/api/v1/enterprise-analytics/resource-capacity` | `POST` | Set customized weekly hours capacity |
| `/api/v1/enterprise-analytics/reports` | `GET`, `POST` | Generate and list archival reports |
| `/api/v1/enterprise-analytics/reports/{id}/download` | `GET` | Export report in CSV or JSON format |
