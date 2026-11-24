# FocusBoard Module B51 — Advanced Project Planning & Scheduling
## Technical Architecture & Implementation Documentation

### 1. Executive Overview

Module B51 delivers enterprise-grade project planning, scheduling, and timeline management capabilities within FocusBoard. Built natively into the application, this module provides interactive Gantt visualization, automated Critical Path Method (CPM) calculations, directed acyclic graph (DAG) task dependency management, project baseline snapshotting & variance analysis, comprehensive project budgeting & cost accounting, schedule health forecasting, and non-destructive "what-if" scenario simulations.

---

### 2. Core Architectural Pillars

```
+---------------------------------------------------------------------------------------------------+
|                           PROJECT PLANNING & SCHEDULING WORKSPACE (B51)                           |
+---------------------------------------------------------------------------------------------------+
|  1. Interactive Gantt Chart      - Day/Week/Month zoom, task bars, progress fill, dependency links|
|  2. Task Dependency DAG Engine    - FS, SS, FF, SF with configurable lag and cycle detection       |
|  3. Critical Path Method (CPM)   - Forward/backward pass, ES/EF/LS/LF, Total & Free Float         |
|  4. Baseline Snapshot Engine     - Immutable baseline capture, schedule & budget variance analysis |
|  5. Project Budget & Costs       - Categories, actual & committed costs, variance & burn rate     |
|  6. Schedule Health Forecasting  - Multi-factor classification (ON_TRACK, AT_RISK, DELAYED)       |
|  7. What-If Scenario Simulations - In-memory non-mutating CPM runs with delta outcomes & apply   |
+---------------------------------------------------------------------------------------------------+
```

---

### 3. Database Schema & Data Models

The implementation introduces 10 dedicated models and extends `TaskDependency` in `backend/app/models/project_planning.py`:

1. **`TaskDependency`** (extended):
   - `lag_duration` (Float, default 0.0)
   - `lag_unit` (String, default 'DAYS')
   - `created_by` (Integer ForeignKey to `users.id`)
2. **`ProjectSchedule`**:
   - `project_id` (ForeignKey to `projects.id`, unique)
   - `calendar_mode` (STANDARD, SEVEN_DAY, EXTENDED)
   - `hours_per_day` (Float, default 8.0)
   - `work_days_per_week` (Integer, default 5)
   - `auto_scheduling_enabled` (Boolean, default True)
   - `critical_path_threshold_days` (Float, default 0.0)
   - `baseline_variance_tolerance_days` (Float, default 2.0)
3. **`ProjectBaseline`**:
   - `project_id`, `version_number`, `name`, `description`, `is_active`, `planned_start_date`, `planned_end_date`, `total_planned_budget`, `created_by`
4. **`BaselineTaskSnapshot`**:
   - `baseline_id`, `task_id`, `planned_start_date`, `planned_end_date`, `duration_days`, `progress_percentage`, `estimated_hours`
5. **`BaselineMilestoneSnapshot`**:
   - `baseline_id`, `milestone_id`, `target_date`, `status`
6. **`ProjectBudget`**:
   - `project_id`, `total_budget`, `currency`, `target_margin_percentage`
7. **`ProjectBudgetCategory`**:
   - `budget_id`, `category_name`, `allocated_amount`
8. **`ProjectCostRecord`**:
   - `budget_id`, `cost_type` (ACTUAL, COMMITTED), `category`, `amount`, `incurred_date`, `description`
9. **`ProjectScheduleScenario`**:
   - `project_id`, `name`, `status` (DRAFT, SIMULATED, APPLIED, ARCHIVED), `created_by`
10. **`ScenarioTaskChange`**:
    - `scenario_id`, `task_id`, `new_duration_days`, `start_date_shift_days`, `end_date_shift_days`, `effort_hours_multiplier`
11. **`ProjectScheduleForecast`**:
    - `project_id`, `forecast_finish_date`, `predicted_variance_days`, `schedule_health_status`, `confidence_score`

---

### 4. Critical Path Method (CPM) Mathematical Algorithm

The CPM engine executes deterministic two-pass scheduling on the task network:
- **Forward Pass**:
  $$\text{ES}_j = \max_{i \in \text{Pred}(j)} (\text{EF}_i + \text{lag}_{ij})$$
  $$\text{EF}_j = \text{ES}_j + \text{Duration}_j$$
- **Project Duration**:
  $$D_{\text{project}} = \max_{j} (\text{EF}_j)$$
- **Backward Pass**:
  $$\text{LF}_i = \min_{j \in \text{Succ}(i)} (\text{LS}_j - \text{lag}_{ij})$$
  $$\text{LS}_i = \text{LF}_i - \text{Duration}_i$$
- **Floats**:
  $$\text{Total Float}_i = \text{LS}_i - \text{ES}_i = \text{LF}_i - \text{EF}_i$$
  $$\text{Free Float}_i = \min_{j \in \text{Succ}(i)} (\text{ES}_j - \text{lag}_{ij}) - \text{EF}_i$$
- **Critical Path Identification**: Tasks where $\text{Total Float}_i \le 0$ are marked critical.

---

### 5. Directed Acyclic Graph (DAG) Cycle Detection

Cycle detection is implemented using Depth-First Search (DFS) with recursion stack tracking:
- Any proposed dependency $(u \to v)$ is checked before creation.
- Disallows self-loops ($u = v$).
- Verifies that no path currently exists from $v$ to $u$. If one exists, adding $u \to v$ would complete a cycle, throwing `HTTP 400 Circular dependency detected`.

---

### 6. REST API Endpoints

Mounted under `/api/v1`:
- `GET /projects/{project_id}/planning`: Retrieve full planning workspace overview
- `PUT /projects/{project_id}/planning`: Update scheduling calendar and auto-scheduling preferences
- `GET /projects/{project_id}/planning/dependencies`: Retrieve all task dependencies
- `POST /projects/{project_id}/planning/dependencies`: Create dependency with type, lag, and DAG validation
- `DELETE /planning/dependencies/{dependency_id}`: Remove task dependency
- `GET /projects/{project_id}/critical-path`: Retrieve CPM calculated schedule and critical tasks
- `POST /projects/{project_id}/critical-path/recalculate`: Force recalculation of forward/backward passes
- `GET /projects/{project_id}/baselines`: List baseline versions
- `POST /projects/{project_id}/baselines`: Snapshot current project state into an immutable baseline
- `GET /baselines/{baseline_id}/comparison`: Compare baseline against current live task schedule & budget
- `GET /projects/{project_id}/budget`: Retrieve budget, categories, cost records, and burn rate
- `PUT /projects/{project_id}/budget`: Update total budget allocation and currency
- `POST /projects/{project_id}/budget/costs`: Record actual or committed expenditure
- `GET /projects/{project_id}/forecast`: Retrieve latest schedule health forecast
- `POST /projects/{project_id}/forecast/recalculate`: Recalculate forecast using B47 risks and B48 tracked hours
- `GET /projects/{project_id}/scenarios`: List what-if simulation scenarios
- `POST /projects/{project_id}/scenarios`: Create simulation scenario
- `POST /scenarios/{scenario_id}/changes`: Add task duration and date overrides
- `POST /scenarios/{scenario_id}/simulate`: Run in-memory CPM calculation without touching production data
- `POST /scenarios/{scenario_id}/apply`: Atomically apply approved scenario changes to live project tasks

---

### 7. Verification and Testing

1. **Backend Tests** (`backend/tests/test_project_planning_b51.py`):
   - `test_project_planning_workspace_overview`: 200 OK with complete structure.
   - `test_task_dependency_acyclic_and_cycle_rejection`: Cycle rejection and valid dependency creation.
   - `test_critical_path_method_cpm`: 5.0 day duration and critical path task verification.
   - `test_project_baseline_creation_and_comparison`: Snapshot creation and comparison metrics.
   - `test_project_budget_and_cost_recording`: Actual cost recording and variance calculation.
   - `test_schedule_health_forecasting`: Forecast generation with health status classification.
   - `test_what_if_scenario_simulation_and_application`: In-memory simulation and transactional application.
2. **Frontend Tests** (`tests/frontend/project_planning_b51.test.js`):
   - API client 20 endpoint exposure check.
   - Critical Path Method forward/backward pass math verification.
   - DAG cycle detection with self-loop rejection.
   - Baseline variance and budget utilization formulas.
   - What-if scenario duration and risk delta calculations.
