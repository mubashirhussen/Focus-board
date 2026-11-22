# FocusBoard AI Human Approval System & Sensitive Action Safeguards
## Phase 30 Governance, Approval Gates & Execution Lifecycle

FocusBoard enforces a strict **Human-in-the-Loop (HITL)** governance model ensuring that AI agents can never perform destructive or irreversible actions without explicit, authenticated user approval.

---

## 1. Sensitive Actions Requiring Human Approval

The following actions are classified as sensitive and automatically trigger an approval gate:
- **Task Deletion (`delete_task`)**: Permanent deletion of task records.
- **Bulk Modifications**: Updating multiple tasks or changing project structures.
- **Destructive State Mutations**: Changing workspace membership or administrative settings.

---

## 2. Approval Gate Execution Flow

1. **Step Evaluation**: During plan execution, `execution_engine.py` checks `step.requires_approval` or if the tool is flagged sensitive.
2. **Execution Halt**:
   - The execution status transitions to `AWAITING_APPROVAL`.
   - The step status transitions to `AWAITING_APPROVAL`.
   - An `AIAgentApproval` record is created with:
     - `action_type`: `DESTRUCTIVE_ACTION` or `SENSITIVE_ACTION`.
     - `reason`: High-level explanation of why the agent requested this tool.
     - `target_resource`: JSON representation of target IDs and payloads.
     - `status`: `PENDING`.
3. **User Action**:
   - **Approve (`POST /api/v1/ai-agent/executions/{id}/approve?approval_id=...`)**:
     The step status becomes `APPROVED`, the tool executes with original arguments, and the execution engine resumes remaining steps.
   - **Reject (`POST /api/v1/ai-agent/executions/{id}/reject?approval_id=...`)**:
     The step status becomes `SKIPPED`, the mutation is blocked, and the agent plan continues or concludes safely.
   - **Cancel (`POST /api/v1/ai-agent/executions/{id}/cancel`)**:
     The entire execution is marked `CANCELLED` and all pending approvals are invalidated.

---

## 3. Server-Side Invalidation

- Approvals are strictly bound to the exact proposed payload.
- Any modification to execution parameters immediately invalidates existing pending approvals.
- Non-owners or cross-tenant users attempting to approve an action receive `HTTP 403 Forbidden` or `HTTP 404 Not Found`.
