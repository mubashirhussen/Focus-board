# FocusBoard — AI-Powered Collaborative Task Management Platform

FocusBoard is an enterprise-grade task management platform developed by **Sheik Mubashir Hussen**.

Originally initiated as a high-fidelity frontend based on Figma design specifications, the platform has evolved into an **Intelligent Collaborative Productivity Ecosystem** featuring:
- **Phase 11**: Stateless JWT Multi-User Authentication & Tenant Isolation
- **Phase 12**: PostgreSQL Database Support, Alembic Migrations & Multi-Stage Dockerization
- **Phase 13**: Advanced Productivity Analytics & Formula-Safe CSV Export (CWE-1236 mitigation)
- **Phase 14**: AI-Powered Task Planning, Smart Prioritization & Proposal Approval Workflows
- **Phase 15**: Deadline Reminders, Background Job Notifications & Email Integration
- **Phase 16**: Real-Time Team Collaboration, Shared Projects, Task Assignment & WebSocket Activity Feeds
- **Phase 17**: Advanced Search, Global Command Palette (`⌘K`), Keyboard Shortcuts & UX Optimization
- **Phase 18**: Security Hardening, Privacy & GDPR Controls, Immutable Audit Trails, Automated Backup & Disaster Recovery
- **Phase 19**: SaaS Platform Architecture, Subscriptions, Billing Provider Integration & Usage Quotas
- **Phase 20**: External Integrations Hub, Google Calendar 2-Way Sync & Event-Driven Workflow Automations
- **Phase 21**: Mobile PWA, Offline IndexedDB Reconciliation Engine & Web Push Notifications
- **Phase 22**: Product Intelligence, AI Behavioral Pattern Recognition & Productivity Coach
- **Phase 23**: Enterprise Governance, Custom Roles, MFA (TOTP) & Verified Domains
- **Phase 24**: Quality Engineering, Automated Testing, Multi-Job CI/CD & Security Audits
- **Phase 25**: Production Infrastructure, Non-Root Hardening, Zero-Downtime Deployment & Runbooks
- **Phase 26**: Final SaaS Release Audit, Product QA & Customer Handover
- **Phase 27**: SaaS Operations Architecture & Customer Support Foundations
- **Phase 28**: SaaS Growth Engine, Product-Led Growth (PLG), Onboarding, Activation & Customer Feedback
- **Phase 29**: Customer Success, Support Ticketing Automation (SLAs), Knowledge Base & Public Roadmap
- **Phase 30**: AI-Native SaaS, Autonomous Productivity Agents, Multi-Step Orchestration & Human Approval Gates
- **Phase 31**: Global SaaS Platform, Internationalization (i18n), Localization (l10n), Multi-Currency, Timezones & RTL Layouts
- **Phase 32**: Enterprise Intelligence, Business Analytics, Executive Dashboards, Predictive Insights & Decision Systems
- **Phase 33**: SaaS Developer Platform, Scoped API Keys, Versioned Public API, Webhooks Engine & Python/TS SDKs
- **Phase 34**: Enterprise Security, Compliance Readiness, SOC 2 / ISO 27001 Controls, Privacy Governance & Trust Center
- **Phase 35**: SaaS Financial Intelligence, Normalized MRR/ARR, Customer Churn/Retention, Unit Economics & FinOps Direct Costs

---

## Candidate Submission Information

- **Candidate:** Sheik Mubashir Hussen
- **Frontend Stack:** React 19 + Vite 8 + Pure CSS3 + Lucide React
- **Backend Stack:** FastAPI (Python 3.10+) + SQLAlchemy 2 + Alembic + Pydantic v2 + Bcrypt + PyJWT + WebSockets
- **Database:** PostgreSQL (Production / Docker) & SQLite (Local / Automated Testing)
- **Containerization:** Docker & Docker Compose (Frontend, Backend, PostgreSQL)
- **Live Demo:** https://focusboard.vercel.app *(or your configured live deployment)*
- **GitHub Repository:** https://github.com/mubashirhussen/FocusBoard

---

## 1. Architectural Highlights

### AI Productivity Assistant (Phase 14)
- **Deterministic Transparent Prioritization**: Evaluates task base priority, deadline urgency (overdue, due today, due soon), and active status momentum to calculate a 0–100 score with clear rationale.
- **Intelligent Daily Workload Planner**: Allocates tasks into realistic time-blocks with 15-minute inter-task breaks bounded by user capacity (2–10 hours), clearly identifying deferred tasks.
- **Task Deconstruction**: Automatically deconstructs complex assignments into modular 3-step subtasks with preparation notes and completion criteria.
- **Proposal-Based Approval Workflow**: AI proposes task modifications (e.g. promoting priority, rescheduling overdue tasks, creating subtasks), but **never modifies data without explicit user review and approval**.

### Notifications & Reminders (Phase 15)
- **Automated Deadline Detection**: Proactively identifies tasks due soon, due today, or overdue.
- **Deduplication Engine**: Prevents notification spam by enforcing single-instance delivery per task/date/channel.
- **Task Lifecycle Hooks**: Automatically cancels pending deadline reminders upon task completion or deletion.
- **In-App Notification Center**: Real-time bell counter in Header with popover list, unread indicators, and mark-as-read controls.
- **Email Delivery Service**: Configurable SMTP transport with graceful mock/logger fallback.

### Real-Time Collaboration & Teams (Phase 16)
- **Multi-Tenant Shared Workspaces**: Role-based access control (`OWNER`, `ADMIN`, `MEMBER`) preserving personal tasks while enabling collaborative team spaces.
- **Shared Projects & Task Assignment**: Assign tasks to verified workspace members, track project milestones, and monitor workload distribution.
- **Task Discussion Threads**: In-context comments for shared task alignment.
- **Real-Time WebSockets**: Live broadcast of workspace events (`task_created`, `task_assigned`, `comment_added`) over authenticated `/api/v1/ws/workspaces/{id}` channels.
- **Audit Activity Feed**: Complete immutable audit trail of team operations and updates.

### Advanced Search & Global Command Palette (Phase 17)
- **Unified Global Search API (`/api/v1/search`)**: Multi-tenant authorized search indexing tasks, projects, and workspaces with status, priority, category, and workspace facet breakdowns.
- **Command Palette (`⌘K` / `Ctrl+K`)**: Floating quick-action modal with debounced search, keyboard navigation (`↑`/`↓`, `↵`, `Esc`), and contextual action routing.
- **Global Keyboard Shortcuts**:
  - `⌘/Ctrl + K`: Toggle Command Palette
  - `⌘/Ctrl + Shift + F`: Global Search trigger
  - `N`: Quick Create New Task (from anywhere outside text inputs)
  - `?`: Open Keyboard Shortcuts Help Cheatsheet
  - `Esc`: Dismiss open modal, palette, or confirm dialog

### Security Hardening, Privacy & Production Reliability (Phase 18)
- **OWASP Security Headers**: Automatic application of `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, and `Referrer-Policy`.
- **Sliding Window Rate Limiter**: In-memory IP-based rate limiting protecting sensitive endpoints (`/auth/login`, `/auth/register`, `/ai/`, `/search`) with standard `429 Too Many Requests` and `Retry-After` headers.
- **GDPR Privacy & Data Portability**: Machine-readable full data export (`GET /api/v1/auth/export-data`) and permanent account erasure (`DELETE /api/v1/auth/me`) with cascading cleanup.
- **Immutable Security Audit Trail**: Database audit log model (`audit_logs`) capturing authentication, authorization, access views, and mutations with metadata sanitization (redacting passwords and credentials).
- **Automated Backup & Disaster Recovery Runbook**: Online zero-downtime database snapshot scripts (`backend/scripts/backup_db.py`, `restore_db.py`) with GZIP compression, SHA256 verification, and automated retention pruning.

### SaaS Billing, Subscriptions & Quota Metering (Phase 19)
- **Centralized Plan Catalog**: Tiered subscription architecture (`Free`, `Starter`, `Pro`, `Team`, `Enterprise`) with feature flags and quota allocations.
- **Pre-Execution Quota Enforcement**: Atomic verification of plan limits (`check_entitlement()`) preventing unauthorized consumption of metered AI, project, and workspace resources.
- **Provider Abstraction**: Decoupled `BillingProvider` interface supporting Stripe Checkout Sessions and mock providers for testing.
- **Idempotent Webhooks**: Authoritative server-side webhook processing with signature verification.

### External Integrations Hub, Google Calendar & Workflows (Phase 20)
- **Integrations Hub**: Unified catalog connecting external tools (Google Calendar, Slack, GitHub).
- **Google Calendar 2-Way Sync**: Bidirectional event mappings, secure OAuth 2.0 credential encryption at rest, and automated conflict detection for overlapping tasks or scheduling outside working hours.
- **Event-Driven Workflow Engine**: Deterministic trigger-condition-action automations (`task_created`, `task_completed`, `task_overdue`, `calendar_sync_completed`) with recursion depth controls ($\le 3$).

### Mobile PWA, Offline IndexedDB Sync & Web Push (Phase 21)
- **Installable Progressive Web App (PWA)**: Web app manifest with maskable icons and custom `#4F46E5` theme.
- **Service Worker Caching**: Stale-while-revalidate for application shell assets with selective offline caching.
- **Offline IndexedDB Storage & Sync**: Local task storage with persistent FIFO mutation queue (`CREATE`, `UPDATE`, `DELETE`) and automatic background reconciliation on network restoration.
- **Web Push Notifications**: VAPID key support delivering background reminders directly to mobile and desktop devices.
- **Mobile Ergonomics**: Touch-friendly bottom navigation bar and responsive layouts optimized across 320px–1440px viewports.

---

## 2. Directory Structure

```
focusboard/
├── docker-compose.yml              # Production orchestration (Postgres, Backend, Frontend)
├── Dockerfile                      # Multi-stage Node + Nginx Alpine frontend container
├── nginx.conf                      # Production Nginx SPA configuration & compression
├── package.json                    # React frontend dependencies & scripts
│
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py                 # FastAPI application, CORS, WebSockets, Middleware
│   │   ├── core/
│   │   │   ├── config.py           # Environment settings (AI, JWT, DB, SMTP, CORS)
│   │   │   └── security.py         # Native Bcrypt hashing & PyJWT token handling
│   │   ├── db/
│   │   │   └── database.py         # SQLAlchemy engine, session maker, get_db dependency
│   │   ├── models/                 # SQLAlchemy ORM Models
│   │   │   ├── user.py             # User model
│   │   │   ├── task.py             # Task model with workspace & assignee FKs
│   │   │   ├── notification.py     # Notification & Preference models
│   │   │   └── collaboration.py    # Workspace, Member, Project, Comment, Activity models
│   │   ├── schemas/                # Pydantic v2 Validation Schemas
│   │   ├── ai/                     # AI Productivity Module
│   │   │   ├── prioritizer.py      # Transparent baseline scoring engine
│   │   │   ├── planner.py          # Daily schedule knapsack/time-block optimizer
│   │   │   ├── safety.py           # Prompt injection detection & sanitization
│   │   │   └── service.py          # AI service & proposal execution engine
│   │   ├── services/
│   │   │   ├── notification_service.py # Reminder generation & deduplication
│   │   │   └── email_service.py    # SMTP email transport
│   │   └── api/routes/             # API Endpoints
│   │       ├── auth_routes.py      # /api/v1/auth (register, login, me)
│   │       ├── task_routes.py      # /api/v1/tasks (CRUD & status lifecycle)
│   │       ├── analytics_routes.py # /api/v1/analytics (summary, trends, CSV)
│   │       ├── ai_routes.py        # /api/v1/ai (priorities, planner, breakdown, chat, approve)
│   │       ├── notification_routes.py # /api/v1/notifications
│   │       ├── workspace_routes.py # /api/v1/workspaces (teams, projects, comments)
│   │       ├── websocket_routes.py # /api/v1/ws/workspaces/{id}
│   │       └── health_routes.py    # /health & /ready probes
│   ├── alembic/                    # Database Migrations (001_initial, 002_ai_notifications_collaboration)
│   └── tests/                      # 11 Automated Pytest Suites
│
└── src/                            # React 19 Frontend Application
    ├── components/
    │   ├── auth/                   # AuthModal, UserProfileMenu
    │   ├── notifications/          # NotificationBell popover
    │   ├── FocusNotes/             # 3-slide visual carousel
    │   ├── TaskList/ & TaskForm/   # Task rendering and modal editor
    │   └── Header/ & Sidebar/      # App navigation & responsive layout
    ├── pages/
    │   ├── Dashboard/              # Executive task overview
    │   ├── Analytics/              # Productivity analytics & CSV export
    │   ├── AIAssistant/            # AI Planner, Prioritizer, Chat & Proposals
    │   └── TeamWorkspace/          # Workspaces, Projects, Comments & Activity
    ├── context/                    # AuthContext, TaskContext
    └── services/                   # Frontend API Layer (aiApi, notificationApi, collaborationApi)
```

---

## 3. Quick Start & Execution

### Option A: Run with Docker Compose
```bash
docker-compose up --build -d
```
- **Frontend Application**: `http://localhost:3000`
- **FastAPI Documentation**: `http://localhost:8000/docs`
- **Health Check Probe**: `http://localhost:8000/health`

---

### Option B: Run Locally

#### 1. Start the Backend API
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

#### 2. Start the Frontend
```bash
# In project root
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 4. Verification & Testing

FocusBoard includes comprehensive automated test coverage across all features:

### Backend Pytest Suite (48/48 Passed)
```bash
cd backend
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest tests -v
```
- `test_resilience.py`: Distributed trace correlation, Prometheus metrics exporter, readiness error isolation, and 404 security handling.
- `test_multi_tenant_security.py`: Cross-tenant boundary isolation, direct ID tampering denial, search & analytics data leakage prevention.
- `test_performance_benchmarks.py`: Health check latency (<100ms), Bcrypt authentication throughput, 50-task batch creation, paginated collection latency, and search latency.
- `test_migrations_validation.py`: Full automated Alembic migration validation from base to revision 005 HEAD.
- `test_product_intelligence.py`: Aggregate productivity metrics, pattern detection, ranked insights, task evidence, insight dismissal, feedback rating, and data-grounded AI coach.
- `test_enterprise_rbac_and_governance.py`: Security policies (MFA, domain restriction, AI governance), custom RBAC role creation and permission evaluation, domain verification tokens, RFC 6238 pure Python TOTP MFA, and compliance audit trail CSV export.
- `test_saas_billing.py`: Plan tier catalogs, subscription lifecycle, checkout, plan change, cancellation, and tenant usage metering.
- `test_integrations_and_workflows.py`: Integrations catalog, Google Calendar OAuth connect, workflow trigger/action lifecycle.
- `test_calendar_sync.py`: Task scheduling, calendar events synchronization, and conflict detection.
- `test_push_and_pwa.py`: VAPID push keys, browser push subscriptions, and background sync.
- `test_security_hardening.py`: OWASP headers, audit logging, rate limiting, and GDPR data export/deletion.
- `test_search.py`: Multi-tenant unified full-text search across tasks, workspaces, and projects.
- `test_ai.py`: Priority scoring, daily schedule generation, task breakdown, workload analysis, chat assistant, and proposal approval.
- `test_notifications.py`: Reminder creation, unread count, mark read, preferences, and deduplication.
- `test_collaboration.py`: Workspace creation, cross-workspace security isolation, invitations, project milestones, and comments.
- `test_tasks.py`: Task CRUD, user isolation enforcement, and lifecycle tracking.
- `test_auth.py`: Registration, duplicate rejection, and login.
- `test_analytics.py`: Aggregate statistics, completion trends, and formula injection sanitization.
- `test_health.py`: Liveness probe (`/health`), readiness probe (`/ready`), and correlation ID propagation.

### Frontend Test & Production Build
```bash
# Run all frontend tests (unit, components, accessibility, sync, state)
npm test

# Run component interaction tests
npm run test:unit

# Run accessibility (a11y) automated tests
npm run test:a11y

# Run offline & IndexedDB sync tests
npm run test:sync

# Run Playwright E2E browser tests
npm run test:e2e

# Compile Vite production bundle
npm run build
```

### Deployment Smoke Tests
```bash
# Verify live deployment health and readiness without mutating state
python scripts/smoke_test.py --backend-url http://localhost:8000 --frontend-url http://localhost:5173
```

### Performance & Concurrency Load Tests
```bash
# Execute synthetic concurrency load test against API endpoints
python scripts/load_test.py --base-url http://localhost:8000 --requests 100 --concurrency 10
```

---

## 5. Architectural, Handover & SRE Documentation

### Customer & Operational Handover
- [PRODUCT_OVERVIEW.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/PRODUCT_OVERVIEW.md)
- [USER_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/USER_GUIDE.md)
- [ADMIN_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/ADMIN_GUIDE.md)
- [TECHNICAL_HANDOVER.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/TECHNICAL_HANDOVER.md)
- [KNOWN_LIMITATIONS.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/KNOWN_LIMITATIONS.md)

### SRE, Scaling & Incident Response
- [SRE_ARCHITECTURE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/SRE_ARCHITECTURE.md)
- [SLO_SLI_FRAMEWORK.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/SLO_SLI_FRAMEWORK.md)
- [SCALING_STRATEGY.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/SCALING_STRATEGY.md)
- [CAPACITY_PLANNING.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/CAPACITY_PLANNING.md)
- [COST_OPTIMIZATION.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/COST_OPTIMIZATION.md)
- [INCIDENT_RESPONSE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/INCIDENT_RESPONSE.md)
- [OPERATIONS_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/OPERATIONS_GUIDE.md)
- [PERFORMANCE_REPORT.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/PERFORMANCE_REPORT.md)
- [RELIABILITY_REPORT.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/RELIABILITY_REPORT.md)
- Operational Runbooks in [RUNBOOKS/](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/RUNBOOKS/)

### Enterprise Security, Governance & Financial Intelligence
- [SECURITY_GOVERNANCE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/docs/SECURITY_GOVERNANCE.md)
- [TRUST_CENTER_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/docs/TRUST_CENTER_GUIDE.md)
- [FINANCIAL_INTELLIGENCE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/docs/FINANCIAL_INTELLIGENCE.md)

### Strategic Intelligence, Innovation Lab & Knowledge Graph (Phases 36–38)
- [STRATEGIC_INTELLIGENCE_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/docs/STRATEGIC_INTELLIGENCE_GUIDE.md): Executive decision support, competitor benchmarking, RICE opportunity prioritization, SWOT, and market sizing (TAM/SAM/SOM).
- [INNOVATION_LAB_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/docs/INNOVATION_LAB_GUIDE.md): Breakthrough R&D pipeline (Stages: Capture, Hypothesis, Experiment, Prototype, Validation) with one-click roadmap promotion.
- [KNOWLEDGE_INTELLIGENCE_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/docs/KNOWLEDGE_INTELLIGENCE_GUIDE.md): Organizational knowledge graph, document versioning, hybrid semantic search, and grounded AI assistant citations.

### CI/CD & Production Infrastructure
- [TESTING_STRATEGY.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/TESTING_STRATEGY.md)
- [CI_CD_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/CI_CD_GUIDE.md)
- [RELEASE_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/RELEASE_GUIDE.md)
- [DEPLOYMENT_PIPELINE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/DEPLOYMENT_PIPELINE.md)
- [QUALITY_REPORT.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/QUALITY_REPORT.md)
- [PRODUCTION_DEPLOYMENT_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [DOMAIN_AND_TLS_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/DOMAIN_AND_TLS_GUIDE.md)
- [PRODUCTION_ENVIRONMENT.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/PRODUCTION_ENVIRONMENT.md)
- [PRODUCTION_MONITORING.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/PRODUCTION_MONITORING.md)
- [DISASTER_RECOVERY_GUIDE.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/DISASTER_RECOVERY_GUIDE.md)
- [LAUNCH_CHECKLIST.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/LAUNCH_CHECKLIST.md)
- [PRODUCTION_STATUS_REPORT.md](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/first_mobile/PRODUCTION_STATUS_REPORT.md)

---

## 5. License & Credits

Developed with care and precision by **Sheik Mubashir Hussen**.
Figma design specifications referenced under assessment guidelines.
All rights reserved.
