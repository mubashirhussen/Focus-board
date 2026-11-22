# FocusBoard Cloud Cost Optimization & Financial Model

## 1. Cloud Cost Architecture
FocusBoard is designed to minimize fixed cloud expenses and scale costs strictly with active paying tenants.

---

## 2. Estimated Monthly Cloud Expenditure

### Base Deployment (Up to 1,000 Active Users)
| Resource | Provider | Sizing / Plan | Estimated Monthly Cost |
|---|---|---|---|
| **Frontend CDN** | Vercel / Cloudflare Pages | Pro / Standard | $20 / month (or Free tier) |
| **Backend API** | Render / Railway | 2 Instances (1 vCPU, 1GB) | $14 – $20 / month |
| **Database** | Neon / Supabase | Managed PostgreSQL 16 | $19 – $25 / month |
| **Redis Cache** | Upstash | Pay-per-request serverless | $0 – $5 / month |
| **AI Assistant** | Gemini API | Flash / Pro models with caching| ~$10 – $30 / month |
| **Total Base Cost** | | | **~$63 – $100 / month** |

---

## 3. Cost Optimization Levers
1. **Model Selection**: Default to `gemini-1.5-flash` for daily planning and task breakdown; reserve heavier models for complex analysis.
2. **Aggressive Browser Caching**: Static JS/CSS assets cached with `max-age=31536000, immutable` to minimize CDN bandwidth charges.
3. **Connection Pooling**: Use pgBouncer to avoid over-provisioning database RAM for idle connections.
4. **Log Retention Pruning**: Enforce 14-day log retention for staging and 30-day for production to eliminate cloud storage bloat.
