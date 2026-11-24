# FocusBoard Module B47 — AI-Powered Predictive Project Intelligence

## 1. Overview
The **Predictive Project Intelligence** module (B47) brings enterprise-grade predictive analytics, project health scoring, deadline forecasting, task risk detection, team workload balancing, and explainable AI recommendations into FocusBoard.

## 2. Module Architecture
The module is divided into decoupled, deterministic analytical engines:

1. **Project Health Scoring Engine** (`app.services.predictive_intelligence_service`):
   - Computes a reproducible, continuous health score from $0$ to $100$.
   - Categorizes status into:
     - `HEALTHY` (80–100)
     - `NEEDS_ATTENTION` (60–79)
     - `AT_RISK` (40–59)
     - `CRITICAL` (0–39)
   - Evaluates:
     - Task completion velocity ($completed / total$)
     - Overdue task ratio ($overdue / open\_tasks \times 35.0$)
     - High/Critical priority unresolved ratio ($critical / open\_tasks \times 25.0$)
     - Dependency blockage ratio ($blocked / open\_tasks \times 20.0$)
     - Deadline pressure & effort slippage penalty ($15.0$)
     - Positive performance indicators and recommended corrective actions.

2. **Task Risk Prediction Engine**:
   - Classifies every active task into `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
   - Analyzes due date proximity, days overdue, dependency prerequisites, assignee concurrent workload, and priority multipliers.
   - Completed or cancelled tasks are strictly evaluated as `LOW` risk (0.0).

3. **Deadline Forecasting Engine**:
   - Computes empirical team velocity (tasks completed per day).
   - Projects realistic delivery dates with an $85\%$ confidence interval $[low, high]$.
   - Measures delivery variance ($\Delta$ days) against planned milestones.
   - Identifies critical path items.

4. **Resource and Workload Analysis Engine**:
   - Aggregates assigned, open, and overdue tasks per member.
   - Calculates weekly capacity utilization percentage against standard or configured hours ($40\text{h}$).
   - Identifies `OVERLOADED` ($>100\%$), `BALANCED` ($40\%-100\%$), and `UNDERUTILIZED` ($<40\%$) members.
   - Proposes non-destructive workload rebalancing.

5. **AI Recommendation Engine**:
   - Converts analytical signals into explainable recommendations.
   - Enforces state machine: `PENDING` $\rightarrow$ `ACCEPTED` $\rightarrow$ `COMPLETED` (or `REJECTED`).
   - Grounded strictly in actual project data; does not hallucinate.

6. **Automated Risk Alert Engine**:
   - Generates deduplicated alerts via the notification subsystem when projects enter `AT_RISK` or `CRITICAL`, or high-risk tasks are identified.
   - Respects configurable cooldown hours (default 24h) to prevent alert fatigue.

7. **Historical Prediction and Accuracy Tracking**:
   - Persists predictions in `prediction_history`.
   - Evaluates Mean Absolute Error (MAE) and classification precision on resolved outcomes.

## 3. Database Schema & Migrations
- Migration: `035_b47_predictive_project_intelligence.py`
- Tables added:
  - `project_health_snapshots`
  - `task_risk_predictions`
  - `deadline_forecasts`
  - `workload_snapshots`
  - `ai_project_recommendations`
  - `prediction_history`
  - `intelligence_settings`

## 4. API Endpoints
All endpoints are available under `/api/v1/intelligence/...` and directly under `/intelligence/...`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/intelligence/overview` | Portfolio health, risks, delays, workload & recommendations summary |
| `GET` | `/intelligence/projects` | Health scores and indicators for all accessible projects |
| `GET` | `/intelligence/projects/{id}/health` | Deep health breakdown and corrective actions |
| `GET` | `/intelligence/projects/{id}/forecast` | Delivery date forecast, variance, and critical path |
| `GET` | `/intelligence/projects/{id}/risks` | Task-level risk predictions for a project |
| `GET` | `/intelligence/tasks/{id}/risk` | Specific task risk score, factors, and suggested action |
| `GET` | `/intelligence/workload` | Team capacity utilization and rebalancing proposals |
| `GET` | `/intelligence/project-recommendations` | AI recommendations with status filter |
| `POST` | `/intelligence/recommendations/{id}/accept` | Accept an AI recommendation |
| `POST` | `/intelligence/recommendations/{id}/reject` | Reject an AI recommendation |
| `POST` | `/intelligence/recommendations/{id}/complete` | Mark an accepted recommendation as completed |
| `GET` | `/intelligence/history` | Historical prediction snapshots and model accuracy metrics |
| `GET` | `/intelligence/settings` | Get risk thresholds and alert settings |
| `PUT` | `/intelligence/settings` | Update risk thresholds and alert settings |
| `POST` | `/intelligence/recalculate/{id}` | On-demand recalculation of project intelligence |

## 5. Verification & Testing
- Backend unit and API tests:
  ```powershell
  $env:PYTHONPATH="backend"
  .\backend\venv\Scripts\pytest.exe backend/tests/test_predictive_project_intelligence.py
  ```
- Frontend unit tests and build:
  ```powershell
  npm test
  npm run build
  ```
