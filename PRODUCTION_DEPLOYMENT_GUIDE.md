# FocusBoard Production Deployment Guide

## 1. Target Cloud Architecture
FocusBoard is architected as a high-performance, cost-effective modular platform:

```
[Clients: Web & Mobile PWA]
             │
             ▼
[Cloudflare CDN / Vercel Edge / Nginx] (Static SPA Assets & SSL Termination)
             │  (Reverse Proxy / API Requests)
             ▼
[FastAPI Application Cluster] (Containerized Uvicorn, Non-Root)
             │
             ├──► [Managed PostgreSQL] (Neon / Supabase / AWS RDS, SSL enforced)
             ├──► [Redis Cache & Queue] (Upstash / ElastiCache)
             └──► [External Services] (Gemini AI, Google OAuth, Stripe Billing)
```

---

## 2. Cloud Provider Selection

| Component | Recommended Provider | Alternative | Justification |
|---|---|---|---|
| **Frontend** | **Vercel** / **Cloudflare Pages** | AWS S3 + CloudFront | Instant global CDN, automatic SSL certificates, atomic deploys, client-side route fallback via `vercel.json`. |
| **Backend API** | **Render** / **Railway** / **Fly.io** | AWS ECS / GCP Cloud Run | Native Dockerfile support, automatic SSL termination, zero-downtime rolling deploys, non-root user execution. |
| **Database** | **Neon** / **Supabase** | AWS RDS PostgreSQL | Fully managed PostgreSQL 16, automatic connection pooling, point-in-time recovery, SSL encryption in transit. |
| **Redis** | **Upstash Redis** | AWS ElastiCache | Serverless, pay-per-request Redis with TLS connection strings. |

---

## 3. Step-by-Step Production Deployment

### Step 1: Provision Cloud Database
1. Create a PostgreSQL 16 database on **Neon** or **Supabase**.
2. Note the secure connection string:
   `postgresql+psycopg://user:password@host/focusboard_prod?sslmode=require`

### Step 2: Deploy Backend to Container Host (e.g. Render / Railway)
1. Link your GitHub repository.
2. Select **Docker** as the deployment environment.
3. Configure environment variables (refer to `.env.production.example`):
   - `DATABASE_URL`: Your managed PostgreSQL URL.
   - `SECRET_KEY`: A 64-character cryptographic key (`openssl rand -hex 32`).
   - `CORS_ORIGINS`: `["https://app.focusboard.app"]`
   - `PORT`: `8000`
4. The container starts automatically using `entrypoint.sh`, applying database migrations and launching Uvicorn workers.

### Step 3: Deploy Frontend to Vercel / Cloudflare Pages
1. Link the repository to **Vercel**.
2. Set Build Command: `npm run build`
3. Set Output Directory: `dist`
4. Configure Environment Variable:
   - `VITE_API_URL`: `https://api.focusboard.app/api/v1`
5. The `vercel.json` file automatically configures SPA client-side routing fallback and security headers.

### Step 4: Verify Deployment with Smoke Tests
Run the deployment smoke test suite against your live domains:
```bash
python scripts/smoke_test.py --backend-url https://api.focusboard.app --frontend-url https://app.focusboard.app
```
