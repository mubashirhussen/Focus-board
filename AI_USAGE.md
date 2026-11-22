# AI Usage & Transparency Log

This document provides transparent disclosure of AI assistance utilized during the development, testing, and full-stack expansion of **FocusBoard**, submitted by candidate **Sheik Mubashir Hussen**.

---

## 1. Candidate Declaration

- **Candidate Name:** Sheik Mubashir Hussen
- **Project:** FocusBoard AI-Powered Collaborative Task Management Platform
- **Assessment Track:** Senior / Trainee Full-Stack Assessment

---

## 2. Scope of AI Tooling & Usage

AI tooling was utilized in an engineering acceleration, architecture validation, and automated test synthesis capacity:

### Phase 1–6 (Frontend Implementation & Verification)
- **Figma Token Extraction**: Parsing Figma frames (`15:2`, `15:30`, `15:58`) to extract exact color values (`#4F46E5`, `#0F172A`, `#F8FAFC`), font line heights, and padding metrics into pure CSS variables.
- **Automated Verification Scripting**: Generation of `test_phase2_verification.js` to execute 28 deterministic assertions verifying state immutability, date formatting, and filter combinations.

### Phase 11–13 (Backend, Security & Infrastructure Expansion)
- **FastAPI Boilerplate & Schemas**: Assisted in drafting Pydantic v2 schemas and SQLAlchemy 2 relationship models.
- **Security Validation**: Verification of OWASP guidelines regarding spreadsheet formula injection (CWE-1236) in CSV exports.
- **Docker Optimization**: Structuring the multi-stage `Dockerfile` and `docker-compose.yml` for production execution.

### Phase 14–16 (AI Assistant, Notifications & Collaboration)
- **Deterministic Prioritization Formula**: Formulation of transparent scoring weights (Base Priority + Urgency + Active Momentum).
- **Daily Schedule Knapsack Optimization**: Structuring time-block allocations with 15-minute rest intervals.
- **Prompt Injection Defense**: Validating adversarial regex patterns to mitigate prompt hijacking in the chat assistant.
- **WebSocket Protocol Design**: Designing the connection manager and pub/sub architecture for workspace collaboration.

---

## 3. Human Engineering Decisions & Authorship

All core architecture, UX decisions, and code reviews were driven by the candidate:

1. **Proposal-Based AI Workflow**: Enforced that the AI assistant cannot directly mutate task records; every modification generates an `ActionProposal` requiring explicit user approval.
2. **Deterministic Baseline Fallback**: Implemented rule-based scoring and planning that functions 100% reliably even when an external AI provider is offline or unconfigured.
3. **Multi-Tenant Security Isolation**: Strictly enforced workspace and user boundaries at the database query level (`Task.workspace_id == workspace_id`).
4. **Task Lifecycle Hooks**: Automated cancellation of pending deadline notifications upon task completion or deletion.
5. **Aesthetic Consistency**: Preserved FocusBoard's human-crafted visual style without generic third-party UI framework dependencies.

---

## 4. Verification & Testing Evidence

Every piece of code generated or assisted was executed, verified, and validated through real compilers and automated test suites:
- Frontend Node test script: `28/28 passing`
- Frontend Vite production build: `dist/ built in 1.69s`
- Backend Pytest test suite: `11/11 test suites passing (100% assertions)`
- Alembic database migrations: `001_initial` and `002_ai_notifications_collaboration` upgraded cleanly
