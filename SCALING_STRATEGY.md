# FocusBoard Incremental Scaling Strategy

## 1. Scaling Philosophy
FocusBoard avoids premature microservice fragmentation. The platform scales cleanly as an optimized modular monolith through clear, incremental milestones:

---

## 2. Incremental Scaling Milestones

### Milestone 1: 1 to 1,000 Users (Current Architecture)
- Single-region container instance with 2–4 Uvicorn workers.
- Managed PostgreSQL 16 (Neon / Supabase).
- CDN edge caching for static assets via Vercel / Cloudflare Pages.
- Performance: P95 latency < 100ms.

### Milestone 2: 1,000 to 10,000 Users
- Scale backend containers horizontally to 3–5 replicas behind an Application Load Balancer.
- Add managed Redis cluster for session token caching and background job queues.
- Activate PostgreSQL connection pooling (pgBouncer / Supabase Supavisor).

### Milestone 3: 10,000 to 50,000 Users
- Add PostgreSQL read replicas:
  - Primary database handles writes and transactional mutations.
  - Read replicas handle read-heavy analytics, dashboard summaries, and global search.
- Implement CDN cache-tag invalidation for project/workspace read endpoints.

### Milestone 4: 50,000+ Users
- Partition high-volume tables (`audit_logs`, `activities`, `productivity_events`) by date range.
- Separate dedicated worker pools for background email/push notification dispatch.
