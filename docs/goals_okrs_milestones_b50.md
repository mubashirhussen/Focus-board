# FocusBoard Module B50: Goals, OKRs & Milestones Management

## 1. Executive Summary & Architecture Overview

The **Goals, OKRs & Milestones Management** module (Module ID: **B50**) provides an enterprise-grade strategic execution and performance tracking platform for FocusBoard. It bridges organizational vision with day-to-day task execution by establishing bidirectional links between high-level objectives, measurable key results, time-bound milestones, and tactical projects/tasks.

### System Architecture
```
┌────────────────────────────────────────────────────────┐
│               Strategic Goal Hierarchy                 │
│       Company Objectives  ──►  Team OKRs  ──►  Personal│
└───────────────────────────┬────────────────────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
  ┌─────────────────────────┐  ┌─────────────────────────┐
  │ Measurable Key Results  │  │  Milestones Roadmap     │
  │ • Numeric Incr / Decr   │  │ • Prerequisite DAG      │
  │ • Percentage / Binary   │  │ • Explicit Dependencies │
  │ • Task-Completion Links │  │ • Critical Path Gates   │
  └────────────┬────────────┘  └────────────┬────────────┘
               │                            │
               ▼                            ▼
  ┌─────────────────────────┐  ┌─────────────────────────┐
  │   Tactical Tasks & Link │  │ Predictive Risk Signals │
  │   (Automated Sync)      │  │ (Module B47 Integration)│
  └─────────────────────────┘  └─────────────────────────┘
```

---

## 2. Strategic Goal Hierarchy & Lifecycle States

### Goal Levels
1. **ORGANIZATIONAL**: Company-wide strategic objectives owned by executives and department heads.
2. **TEAM**: Departmental or squad-level OKRs aligned with organizational parent goals.
3. **INDIVIDUAL**: Professional individual performance goals linked directly to team objectives.

### Lifecycle Statuses
- **DRAFT**: Inception and goal planning stage; not yet actively tracked.
- **ACTIVE**: In flight with periodic key result updates and weekly check-ins.
- **ON_TRACK**: Progress aligns with or exceeds expected linear timeline velocity.
- **AT_RISK**: Progress lagging behind expected velocity (10% to 25%) or blocked milestones detected.
- **BEHIND**: Severe velocity deficit (>25%) or overdue deadline.
- **COMPLETED**: All key results achieved (100% progress) or manually marked completed.
- **CANCELLED**: Deprecated or strategically halted.
- **ARCHIVED**: Historical record kept for organizational audit and performance retrospectives.

---

## 3. Measurable Key Results & Progress Calculation Engine

Key results support 7 distinct mathematical measurement types:

| Type | Formula / Logic | Target Semantics |
|---|---|---|
| `NUMERIC_INCREASE` | `((current - start) / (target - start)) * 100` | Capped at 100%, floored at 0% |
| `NUMERIC_DECREASE` | `((start - current) / (start - target)) * 100` | Latency reduction, bug count decrease |
| `PERCENTAGE` | `((current - start) / (target - start)) * 100` | Adoption rates, test coverage, SLO compliance |
| `BINARY` | `100% if current >= 1 else 0%` | Go/No-Go decisions, compliance certifications |
| `MILESTONE` | Completed milestones / total milestones linked | Multi-stage roadmap progress |
| `TASK_COMPLETION` | Completed linked tasks / total linked tasks | Live dynamic sync from Task entities |
| `MANUAL` | Direct percentage score entry | Qualitative assessments |

All calculation routines implement safe denominator handling with zero-division protection (`abs(target - start) < 1e-9`).

---

## 4. Milestone Management & Dependency Graph (DAG)

Milestones represent critical delivery gates along a project or goal timeline:
- **Dependency Graph**: Milestones can depend on one or more prerequisite milestones.
- **Cycle Detection**: The service enforces strict acyclic validation (DAG) preventing circular dependencies (`A -> B -> A`).
- **Execution Gates**: A milestone cannot be marked completed if any of its prerequisite milestones remain incomplete.

---

## 5. Work-Linking & Automated Tactical Synchronization

- **Goal-to-Project Links (`GoalProjectLink`)**: Links overarching strategic goals to active execution projects.
- **Key-Result-to-Task Links (`KeyResultTaskLink`)**: Directly attaches individual tasks to a key result. When tasks are updated, completed, or reopened, the key result's current value and progress percentage automatically recalculate.

---

## 6. Check-Ins & Leadership Review Workflow

1. **Progress Reports**: Weekly or bi-weekly qualitative status updates.
2. **Confidence Scores**: 1 to 5 scale (1 = Critically At Risk, 5 = High Confidence).
3. **Blockers & Mitigation**: Structured blocker disclosure enabling proactive unblocking.
4. **Manager Reviews**: Authorized team leads and executives can approve, review, or request revisions on check-ins.

---

## 7. Explainable Health Classification Engine

The system computes health status using multi-factor velocity modeling:
$$\text{Expected Progress} = \left(\frac{\text{Days Elapsed}}{\text{Total Duration}}\right) \times 100$$
$$\Delta = \text{Actual Progress} - \text{Expected Progress}$$

- $\Delta \ge -10\% \implies \text{ON\_TRACK}$
- $-25\% \le \Delta < -10\% \implies \text{AT\_RISK}$
- $\Delta < -25\% \implies \text{BEHIND}$

### Cross-Module Risk Inputs
- **B47 Predictive Intelligence**: Flags high-risk projects linked to the goal.
- **B48 Time Tracking**: Identifies effort deficits vs budget projections.
- **B49 Resource Management**: Highlights overloaded team members assigned to key results.

---

## 8. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/goals` | List organizational and team goals with filters |
| `POST` | `/api/v1/goals` | Create a new strategic goal |
| `GET` | `/api/v1/goals/{id}` | Retrieve goal details, key results, and linked projects |
| `PUT` | `/api/v1/goals/{id}` | Update goal attributes |
| `DELETE` | `/api/v1/goals/{id}` | Soft delete or archive goal |
| `POST` | `/api/v1/goals/{id}/key-results` | Add a measurable key result |
| `POST` | `/api/v1/goals/key-results/{id}/progress` | Record KR progress with audit history |
| `POST` | `/api/v1/goals/{id}/milestones` | Create a goal milestone |
| `POST` | `/api/v1/goals/milestones/{id}/complete` | Mark milestone complete (validates prerequisites) |
| `POST` | `/api/v1/goals/milestones/{id}/dependencies` | Add milestone dependency gate |
| `POST` | `/api/v1/goals/key-results/{id}/tasks` | Link task to key result |
| `POST` | `/api/v1/goals/{id}/check-ins` | Submit qualitative progress check-in |
| `POST` | `/api/v1/goals/check-ins/{id}/review` | Leadership check-in review |
| `GET` | `/api/v1/goals/analytics/overview` | Organizational OKR metrics and status distribution |
