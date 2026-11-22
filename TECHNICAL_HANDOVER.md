# FocusBoard: Technical Handover & System Architecture

## 1. System Architecture
FocusBoard is designed as a modular monolith:

- **Frontend**: React 19 + Vite 8 single-page application.
  - State: Centralized React Context (`AuthContext`, `TaskContext`) + LocalStorage/IndexedDB sync.
  - PWA: `public/sw.js` service worker + `manifest.webmanifest`.
- **Backend**: FastAPI (Python 3.10) with Pydantic v2 schemas and native Bcrypt/PyJWT security.
- **Database**: PostgreSQL 16 managed via SQLAlchemy 2.0 ORM and Alembic migrations (revisions 001 through 005).
- **Containerization**: Multi-stage Docker build with Nginx Alpine for the frontend and non-root Python for the backend.

---

## 2. Database Migrations History
- `001_initial`: Users and Tasks core schema.
- `002_ai_notifications_collaboration`: Workspaces, Members, Projects, Task Comments, Activities, and Notifications.
- `003_audit_trail`: Tamper-evident Audit Logs.
- `004_saas_billing_integrations_pwa`: Plans, Subscriptions, External Integrations, Push Subscriptions, and Task Scheduling.
- `005_intelligence_and_enterprise`: Productivity Events, Preferences, Enterprise Policies, Custom Roles, Domain Verification, and User MFA.

---

## 3. Operational Commands Reference

```powershell
# 1. Run all frontend test suites
npm test

# 2. Compile frontend production bundle
npm run build

# 3. Run all backend tests (48 tests)
$env:PYTHONPATH="backend"; .\backend\venv\Scripts\pytest backend\tests -v

# 4. Run automated migration verification
python -m scripts.run_migrations

# 5. Execute deployment smoke test
python scripts/smoke_test.py --backend-url http://localhost:8000 --frontend-url http://localhost:5173

# 6. Execute synthetic load test
python scripts/load_test.py --base-url http://localhost:8000 --requests 100 --concurrency 10
```
