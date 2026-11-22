# FocusBoard CI/CD Pipeline Guide

## 1. Architecture Overview
FocusBoard's Continuous Integration and Continuous Deployment (CI/CD) pipelines are automated using **GitHub Actions**. Every code push and pull request is systematically evaluated through quality gates, security scanners, and container validations before code is accepted into `master`.

---

## 2. GitHub Actions Workflows

### 2.1 Continuous Integration (`.github/workflows/ci.yml`)
Runs on every push to `master`/`main` and all pull requests.
- **Job 1: `frontend-quality`**
  - Node 20 environment with npm caching.
  - Executes complete frontend test suite (`npm test`).
  - Compiles production Vite assets (`npm run build`).
  - Uploads compiled `dist/` bundle as build artifact.
- **Job 2: `backend-quality`**
  - Python 3.10 environment with pip caching.
  - Executes 44 automated pytest test suites with coverage.
  - Validates full Alembic database migration chain (`python -m scripts.run_migrations`).
- **Job 3: `security-scan`**
  - Runs Bandit static security analysis on `backend/app`.
  - Runs `npm audit --audit-level=high` on frontend dependencies.
- **Job 4: `docker-validation`**
  - Verifies multi-stage Docker builds for both Frontend (Nginx) and Backend (FastAPI).

### 2.2 Staging & Production Deployment (`.github/workflows/deploy.yml`)
- **Staging Deployment**: Automatically triggered on merge to `master`. Deploys to staging cluster and executes smoke tests.
- **Production Gate**: Requires manual workflow dispatch or approval in GitHub Environment `production`. Runs production smoke tests against live endpoints.

### 2.3 Semantic Versioned Release (`.github/workflows/release.yml`)
- Triggered on tag push matching `v*.*.*`.
- Automatically builds production assets, packages a tarball, and creates a tagged GitHub Release with changelog notes.

---

## 3. Required GitHub Secrets
To configure CI/CD deployments in your GitHub repository settings (*Settings > Secrets and variables > Actions*):

| Secret Name | Description | Environment |
|---|---|---|
| `DATABASE_URL` | Production PostgreSQL connection string (with `?sslmode=require`) | Production |
| `SECRET_KEY` | 64-character cryptographic secret for JWT authentication | Staging & Prod |
| `RENDER_API_KEY` / `VERCEL_TOKEN` | Cloud hosting deployment tokens | Staging & Prod |
| `STRIPE_SECRET_KEY` | Stripe payment gateway secret key | Staging & Prod |
| `GEMINI_API_KEY` | AI productivity assistant API key | Staging & Prod |
