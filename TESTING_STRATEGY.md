# FocusBoard Comprehensive Automated Testing Strategy

## 1. Executive Summary
FocusBoard enforces a multi-tiered Quality Engineering architecture designed to provide rapid feedback, prevent regressions, guarantee multi-tenant security isolation, and ensure compliance across all 25 implementation phases.

---

## 2. Test Architecture & Pyramid

```
                ▲
               / \
              /   \
             / E2E \       Playwright Browser Automation (User Journeys)
            /-------\
           /  Integ  \     FastAPI TestClient + Isolated In-Memory SQLite / Alembic
          /-----------\
         / Component & \   Node Native Test Runner (Validation, Helpers, Stats)
        /   Security    \  Multi-Tenant RBAC Boundary & Performance Benchmarks
       /-----------------\
```

### 2.1 Backend Automated Testing (pytest)
- **Framework**: `pytest 9.2.0`, `pytest-asyncio`, `fastapi.testclient.TestClient`.
- **Database Isolation**: In-memory SQLite with `StaticPool` (`sqlite:///:memory:`) and dynamic dependency override for `get_db`. Each test function runs against a pristine schema that is created and dropped per test fixture.
- **Coverage**:
  - `test_tasks.py`: Task CRUD, user isolation, and completion lifecycle.
  - `test_auth.py`: Registration, Bcrypt password hashing, PyJWT tokens.
  - `test_collaboration.py`: Workspaces, members, roles, project milestones, task assignment, and comments.
  - `test_multi_tenant_security.py`: Cross-tenant boundary testing (direct ID tampering, unauthorized project/task access, search isolation).
  - `test_performance_benchmarks.py`: Latency benchmarks (< 100ms for health & search; < 500ms for Bcrypt auth; batch creations).
  - `test_migrations_validation.py`: Full Alembic upgrade lifecycle from base to head across revisions 001–005.
  - `test_saas_billing.py`: Plan catalogs, subscription upgrades, cancellations, and usage metering.
  - `test_integrations_and_workflows.py`: OAuth flow simulation, webhook triggers, and automated actions.
  - `test_enterprise_rbac_and_governance.py`: Custom role permission verification, security policies, TOTP MFA, and CSV audit exports.
  - `test_product_intelligence.py`: Aggregate velocity metrics, pattern detection, and data-grounded AI coach.
  - `test_search.py`: Multi-tenant full-text search across tasks, workspaces, and projects.
  - `test_security_hardening.py`: OWASP headers, rate limiting, and GDPR export/delete.
  - `test_calendar_sync.py`: Task scheduling, event mappings, and conflict detection.
  - `test_push_and_pwa.py`: VAPID keys and push subscriptions.
  - `test_notifications.py`: Reminder deduplication and preferences.
  - `test_analytics.py`: Aggregate statistics and trend calculations.
  - `test_ai.py`: Knapsack daily planner, priority scoring, task breakdown, and chat.
  - `test_health.py`: Liveness (`/health`) and readiness (`/ready`) probes.

### 2.2 Frontend Automated Testing (Node Test Runner)
- **Framework**: Node 24 Native Test Runner & `node:assert`.
- **Test Suites**:
  - `test_phase2_verification.js`: 28-point state and persistence verification.
  - `tests/frontend/components.test.js`: Form validation, whitespace/XSS sanitization, composite filters, and dynamic stats math.
  - `tests/frontend/accessibility.test.js`: Semantic landmarks, dialog accessibility (`role="dialog"`, `aria-modal="true"`), live status regions, and WCAG 2.1 AA color contrast ratios (> 15:1 for primary text).
  - `tests/frontend/offline_sync.test.js`: Offline mutation queueing, IndexedDB in-memory fallback, and subscriber lifecycle.

### 2.3 End-to-End Browser Automation (Playwright)
- **Framework**: `@playwright/test 1.65.1`.
- **Configuration**: `playwright.config.js` with Desktop Chrome and Mobile Chrome viewports.
- **Coverage**: `e2e/focusboard.spec.js`:
  - Journey 1: Brand header, metrics cards, and navigation.
  - Journey 2: Task CRUD workflow (Create, View, Filter).
  - Journey 3: Navigation across Product Intelligence and Enterprise Admin.
  - Journey 4: SaaS Billing and Plans View.
  - Journey 5: Mobile bottom navigation on 390px viewports.

---

## 3. Local Execution Commands

### Frontend Tests:
```powershell
# Run all frontend tests (unit, a11y, sync, phase 2)
npm test

# Run component unit tests
npm run test:unit

# Run accessibility tests
npm run test:a11y

# Run offline sync tests
npm run test:sync

# Run Playwright E2E browser tests
npm run test:e2e
```

### Backend Tests:
```powershell
# In project root:
$env:PYTHONPATH="backend"
.\backend\venv\Scripts\pytest backend\tests -v

# Run with coverage report:
.\backend\venv\Scripts\pytest backend\tests -v --cov=backend/app --cov-report=term
```
