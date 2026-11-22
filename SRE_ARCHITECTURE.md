# FocusBoard SRE Architecture & Observability Framework

## 1. Reliability Philosophy
FocusBoard adheres to Site Reliability Engineering (SRE) principles:
- **Measure What Matters**: Ground SLIs in actual user transactions (task CRUD, authentication, search, sync).
- **Embrace Graceful Degradation**: External failures (AI API timeout, Redis downtime) must never take down core task tracking.
- **Automated Observability**: Correlated request IDs (`X-Request-ID`) and distributed trace IDs (`X-Trace-ID`) on every HTTP transaction.

---

## 2. Observability Architecture

```
[Client Application]
      │ (X-Request-ID, X-Trace-ID)
      ▼
[Reverse Proxy / Ingress]
      │
      ▼
[FastAPI Middleware] ──► [Prometheus Metrics Endpoint (/metrics)]
      │                     ├── focusboard_uptime_seconds
      │                     ├── focusboard_database_connected
      │                     └── focusboard_api_status
      ▼
[Structured JSON Logs] ──► Centralized Log Aggregator (Datadog / CloudWatch / Grafana Loki)
```

---

## 3. Metrics & Monitoring Endpoints
- **Liveness Probe**: `GET /health` (Status 200)
- **Readiness Probe**: `GET /ready` (Verifies database query execution)
- **Prometheus Metrics**: `GET /metrics` (Standard text/plain format for Prometheus scraping)
- **Correlation Propagation**: Every response header contains:
  - `X-Request-ID`: Unique UUID for request tracking.
  - `X-Trace-ID`: Distributed trace identifier for end-to-end telemetry.
