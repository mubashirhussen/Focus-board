# FocusBoard Production Environment & Configuration Guide

## 1. Environment Segregation
FocusBoard maintains strict separation between development, staging, and production environments:

- **Local Development**:
  - `DEBUG=true`, SQLite database (`focusboard.db`), permissive CORS (`http://localhost:5173`).
- **Staging**:
  - `DEBUG=false`, Managed PostgreSQL staging instance, staging OAuth & Stripe test keys (`sk_test_*`).
- **Production**:
  - `DEBUG=false`, Managed PostgreSQL production instance with SSL (`?sslmode=require`), live Stripe keys (`sk_live_*`), strict CORS origins (`["https://app.focusboard.app"]`).

---

## 2. Environment Variables Reference

| Variable | Required | Production Value / Description | Sensitivity |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | `postgresql+psycopg://user:pass@host/db?sslmode=require` | **Secret** |
| `SECRET_KEY` | **Yes** | 64-char random hex key for PyJWT signing | **Secret** |
| `CORS_ORIGINS` | **Yes** | `["https://app.focusboard.app"]` | Config |
| `ALLOWED_HOSTS` | **Yes** | `["api.focusboard.app"]` | Config |
| `VAPID_PUBLIC_KEY` | **Yes** | Web Push public encryption key | Public |
| `VAPID_PRIVATE_KEY`| **Yes** | Web Push private signing key | **Secret** |
| `STRIPE_SECRET_KEY`| Optional| Stripe payment processing secret | **Secret** |
| `GEMINI_API_KEY`   | Optional| AI productivity coach API key | **Secret** |
| `VITE_API_URL`     | **Yes** | `https://api.focusboard.app/api/v1` (Frontend build) | Public |

---

## 3. Secret Rotation Procedure
1. **JWT Secret (`SECRET_KEY`)**: Changing this invalidates all active user login tokens. Users will be asked to log in again.
2. **Database Password**: Rotate via managed cloud provider dashboard (e.g. Neon, AWS RDS), then update `DATABASE_URL` in container environment settings with zero downtime.
