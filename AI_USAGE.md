# AI Usage & Transparency Log

This document provides transparent disclosure of AI assistance utilized during the development, testing, and full-stack expansion of **FocusBoard**, submitted by candidate **Sheik Mubashir Hussen**.

---

## 1. Candidate Declaration

- **Candidate Name:** Sheik Mubashir Hussen
- **Project:** FocusBoard Full-Stack Task Management & Analytics Platform
- **Assessment Track:** Senior / Trainee Full-Stack Assessment

---

## 2. Scope of AI Tooling & Usage

AI tooling was utilized strictly in an engineering accelerator and automated testing capacity:

### Phase 1–6 (Frontend Implementation & Verification)
- **Figma Token Extraction**: Parsing Figma frames (`15:2`, `15:30`, `15:58`) to extract exact color values (`#4F46E5`, `#0F172A`, `#F8FAFC`), font line heights, and padding metrics into pure CSS variables.
- **Automated Verification Scripting**: Generation of `test_phase2_verification.js` to execute 28 deterministic assertions verifying state immutability, date formatting, and filter combinations.
- **Documentation Structuring**: Generating clean Markdown outlines for the project README and rubric alignment checklists.

### Phase 11–13 (Backend, Security & Infrastructure Expansion)
- **FastAPI Boilerplate & Schemas**: Assisted in drafting Pydantic v2 schemas and SQLAlchemy 2 relationship models.
- **Security Best Practices**: Validation of OWASP recommendations regarding spreadsheet formula injection (CWE-1236) in CSV exports, enforcing single-quote prefixing for cells starting with `=`, `+`, `-`, or `@`.
- **Docker Multi-Stage Optimization**: Structuring the multi-stage `Dockerfile` and `docker-compose.yml` configuration to ensure lightweight alpine containers and non-root execution.

---

## 3. Human Engineering Decisions & Authorship

All core architecture, UX decisions, and code reviews were driven by the candidate:

1. **State Isolation & Offline Resilience**: Architected `TaskContext.jsx` with an adaptive fallback mechanism ensuring that users in guest or offline mode experience full functionality via `localStorage` without breakage if the API is offline.
2. **Multi-Tenant Database Constraints**: Handled user data isolation at the SQLAlchemy query filter level (`Task.user_id == current_user.id`) rather than in-memory filtering.
3. **No External Framework Bloat**: Preserved plain CSS3 modular styles and design tokens instead of introducing Tailwind or third-party UI component libraries.
4. **Bcrypt Implementation**: Chose native `bcrypt` over passlib wrapper to guarantee compatibility across modern Python 3.10+ environments.
5. **Observability Middleware**: Designed custom request correlation ID middleware ensuring `X-Request-ID` is traced from HTTP headers to log records.

---

## 4. Verification & Testing

Every piece of code generated or assisted was executed, verified, and validated through real compilers and automated test suites:
- Frontend Node test script: `28/28 passing`
- Frontend Vite production build: `dist/ built in 2.03s`
- Backend Pytest test suite: `4/4 suites passing`
- Alembic database migration: `001_initial upgraded cleanly`
