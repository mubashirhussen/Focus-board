# FocusBoard SaaS Automation Platform Architecture & Guide

FocusBoard Enterprise Automation Intelligence (Phase 39) introduces a production-grade business process automation engine, no-code workflow builder, deterministic condition evaluator, action engine, human-in-the-loop approvals, and natural-language AI workflow synthesis.

---

## 1. Core Architecture

The Automation Engine operates on an event-driven and scheduled execution model:

```
[ Event Trigger / Schedule / Manual ]
                 │
                 ▼
       [ Condition Evaluator ] ────(False)────► [ Alternate Branch / Complete ]
                 │ (True)
                 ▼
       [ Action / Approval ]
                 │
       [ Human Approval Gate ] ───(Approved)──► [ Action Execution Engine ]
                 │                                        │
                 ▼                                        ▼
         [ Execution Log ] ◄────────────────────── [ Next Step / End ]
```

### Models & Schema Hierarchy
1. **AutomationWorkflow**: Workflows belong to workspaces or are pre-seeded as reusable templates. Workflows feature status tracking (`DRAFT`, `ACTIVE`, `PAUSED`, `DISABLED`, `ARCHIVED`), version increments, and variable configurations.
2. **AutomationWorkflowVersion**: Immutable version history capturing snapshot representations of nodes and edges upon every structural workflow modification.
3. **AutomationExecution**: Tracked execution runs with status (`PENDING`, `RUNNING`, `REQUIRES_APPROVAL`, `COMPLETED`, `FAILED`, `CANCELLED`), timing, context data, error messages, and retry counters.
4. **AutomationExecutionLog**: Fine-grained node-level audit logging storing input payload, output response, execution status, and timestamp.
5. **AutomationApproval**: Human-in-the-loop review tickets holding consequential actions (financial, sensitive data, policy changes) until an authorized manager approves or rejects.
6. **AutomationSchedule**: Recurring trigger definitions configured with cron expressions and timezone specifications.

---

## 2. Supported Node Types & Semantics

- **Trigger (`trigger`)**: Initiates workflow based on domain events (`task.created`, `task.overdue`, `task.completed`, `support.ticket.created`, `experiment.completed`, or `MANUAL`).
- **Condition (`condition`)**: Evaluates deterministic expressions:
  - `EQUALS`, `NOT_EQUALS`
  - `CONTAINS`
  - `GREATER_THAN`, `LESS_THAN`
  - `IN_LIST`, `IS_EMPTY`
- **Action (`action`)**: Interacts directly with core FocusBoard models:
  - `notification.send`: Dispatches in-app and delivery-channel alerts.
  - `task.create`: Creates follow-up and escalation tasks with rendered variable interpolation (e.g., `{{title}}`).
  - `support.create_ticket`: Submits automated support tickets.
  - `knowledge.create_doc`: Documents system state in the Knowledge Hub.
- **Approval (`approval`)**: Halts execution, generates an `AutomationApproval` record, notifies approvers, and pauses until a formal `APPROVED` decision is recorded.
- **Delay (`delay`)**: Non-blocking simulated or scheduled postponement.
- **End (`end`)**: Concludes execution gracefully and computes duration metrics.

---

## 3. Human-In-The-Loop Approval Governance

Consequential actions cannot be silently executed by autonomous policies:
1. When an `approval` node is reached, the execution transition to `REQUIRES_APPROVAL`.
2. Execution state and accumulated context are serialized into `context_summary`.
3. An authorized manager reviews the execution via `/api/v1/automation/approvals`.
4. Submitting `APPROVED` automatically resumes traversal to subsequent nodes.
5. Submitting `REJECTED` terminates the execution run with `FAILED` status and registers the reviewer's reason.

---

## 4. AI Workflow Synthesis

The AI Workflow Assistant (`POST /api/v1/automation/assistant/generate`) transforms natural language instructions into structured node-edge graph topologies, ensuring:
- Deterministic node boundaries.
- Variable extraction (thresholds, targets).
- Safe draft state requiring explicit user review and activation before execution.
