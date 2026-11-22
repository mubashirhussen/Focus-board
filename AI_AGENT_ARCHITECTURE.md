# FocusBoard AI Agent Architecture & Autonomous Task Orchestration
## Phase 30 Architecture, Tool Registry & Multi-Step Planning

FocusBoard's Phase 30 transforms the platform into an **AI-Native SaaS** where autonomous productivity agents reason about real user objectives, construct deterministic execution plans, call registered application tools, and enforce strict human approval gates before executing sensitive or destructive operations.

---

## 1. Core Architecture Overview

```
[ User Goal / Prompt ]
       │
       ▼
[ AI Agent Selector ] (Planner, Breakdown, Project Architect, Insights, Automation, Support)
       │
       ▼
[ Agent Planning Engine ] ──> Structured Multi-Step Plan (Steps with Tool Calls & Required Approvals)
       │
       ▼
[ Execution Engine ] ───────> Safe Tools Auto-Executed (create_project, create_task, get_analytics)
       │
       ├─ [ Sensitive Tool (delete_task)? ] ──> Halts Execution & Emits AIAgentApproval
       │                                             │
       │                                             ├─ [ User Approves ] ──> Resumes Execution
       │                                             └─ [ User Rejects ]  ──> Skips Step Safely
       ▼
[ Completed Execution ] ───> Live Status, Tool Logs, Telemetry (Tokens & Cost Cents)
```

---

## 2. Built-In System Agents

| Agent ID | Agent Name | Primary Specialty | Authorized Tools |
| :--- | :--- | :--- | :--- |
| `agent-task-planner` | **Autonomous Task Planner** | Backlog analysis, task sequencing, workload adjustments, daily plan, deadlines. | `list_tasks`, `get_task`, `search_tasks`, `create_task`, `update_task`, `delete_task`, `create_daily_plan` |
| `agent-task-breakdown` | **Smart Task Deconstructor** | Converts complex assignments into modular subtasks with clear milestones. | `get_task`, `create_task`, `update_task`, `list_tasks` |
| `agent-project-planner` | **Project Architect Agent** | Analyzes projects, milestones, task structures, and sprint backlogs. | `list_projects`, `create_project`, `create_task`, `list_tasks` |
| `agent-productivity-insights` | **Behavioral Insights Agent** | Analyzes actual task activity, overdue patterns, and weekly velocity. | `get_productivity_analytics`, `list_tasks` |
| `agent-workflow-automation` | **Workflow Orchestrator** | Executes approved workflows, interacts with FocusBoard tools. | `list_tasks`, `create_task`, `update_task`, `delete_task`, `create_project`, `list_projects` |
| `agent-customer-support` | **Customer Success Agent** | Searches KB, answers questions, drafts replies, files SLA tickets. | `search_knowledge_base`, `create_support_ticket` |

---

## 3. Secure Tool Registry (`backend/app/ai_agent/tools.py`)

Agents are strictly restricted to registered, server-validated tools:
1. `list_tasks`: Retrieves user's active tasks filtered by status or priority.
2. `get_task`: Retrieves full task details by task ID.
3. `search_tasks`: Keyword search over task titles and descriptions.
4. `create_task`: Adds a scheduled task in the user's workspace.
5. `update_task`: Mutates status, priority, or deadline.
6. `delete_task`: **Sensitive Action** (Permanently deletes a task; requires human approval).
7. `list_projects`: Lists projects in the active workspace.
8. `create_project`: Creates a new project container.
9. `get_productivity_analytics`: Queries actual completion velocity and overdue metrics.
10. `create_daily_plan`: Generates an optimal daily work schedule based on workload.
11. `search_knowledge_base`: Retrieves self-service articles and troubleshooting guides.
12. `create_support_ticket`: Submits an SLA-backed customer support ticket.

**Security Constraints**:
- No arbitrary code execution or shell commands.
- Server-side tenant isolation: agents can only read or mutate records belonging to the authenticated user's workspace.
- Prompt injection defense: user task content is treated as untrusted data and cannot override tool permissions.
