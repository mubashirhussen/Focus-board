# FocusBoard Deployment Pipeline Specification

## 1. Pipeline Overview
The FocusBoard deployment pipeline bridges continuous testing with controlled staging and production releases. It enforces strict environmental isolation and automated smoke test validation.

---

## 2. Pipeline Stages

### Stage 1: Continuous Integration (CI)
- Trigger: Push or Pull Request.
- Checks:
  - Frontend: `npm test`, `npm run build`
  - Backend: `pytest backend/tests` (44 tests), `scripts.run_migrations`
  - Security: Bandit analysis, `npm audit`
  - Containerization: Multi-stage Docker build validation

### Stage 2: Staging Deployment
- Trigger: Automatic on merge to `master`.
- Target: Staging cluster (e.g. `https://staging.focusboard.app`, `https://api-staging.focusboard.app`).
- Action:
  1. Headless Alembic migration against staging PostgreSQL database.
  2. Rolling container update.
  3. Post-deploy smoke test: `python scripts/smoke_test.py --backend-url https://api-staging.focusboard.app --frontend-url https://staging.focusboard.app`.

### Stage 3: Controlled Production Deployment
- Trigger: Manual dispatch (`workflow_dispatch`) with target `production`.
- Gate: Requires explicit manual reviewer approval in GitHub Environment `production`.
- Action:
  1. Automated backup snapshot of production database.
  2. Safe forward migration via `scripts/run_migrations.py`.
  3. Zero-downtime rolling update of backend and frontend containers.
  4. Production smoke tests verifying liveness, readiness, and API routes.

---

## 3. Smoke Test Verification
FocusBoard includes a standalone, non-destructive deployment smoke test runner (`scripts/smoke_test.py`):
```bash
python scripts/smoke_test.py --backend-url http://localhost:8000 --frontend-url http://localhost:5173
```
Verifies:
1. Backend Liveness (`/health`)
2. Backend Readiness & Database connection (`/ready`)
3. OpenAPI Documentation (`/docs`)
4. Security Gateway 401 rejection on protected routes
5. Frontend single-page application root availability
