# FocusBoard Production Observability & Monitoring

## 1. Observability Pillars
FocusBoard incorporates structured logging, health probes, performance metrics, and error alerting to maintain high availability in production.

---

## 2. Health & Readiness Probes

### 2.1 Liveness Probe (`GET /health`)
- **Purpose**: Verifies that the FastAPI process is responsive.
- **Frequency**: Every 15 seconds.
- **Response**: `{"status": "ok", "timestamp": "...", "version": "1.0.0"}`

### 2.2 Readiness Probe (`GET /ready`)
- **Purpose**: Verifies that the database pool is healthy and accepting queries.
- **Query**: Executes `SELECT 1` through SQLAlchemy.
- **Response**: `{"status": "ready", "database": "connected"}`

---

## 3. Structured Logging & Security
- **Log Format**: JSON formatted logs in production including `timestamp`, `level`, `request_id`, `path`, `status_code`, and `duration_ms`.
- **Sensitive Data Redaction**: Log formatters automatically filter out passwords, authorization headers, credit card numbers, and JWT tokens.

---

## 4. Alerting Thresholds

| Metric | Warning Threshold | Critical Threshold | Action |
|---|---|---|---|
| **API Latency (p95)** | > 250ms | > 500ms | Scale backend worker replicas |
| **Error Rate (5xx)** | > 1.0% | > 5.0% | Page on-call DevOps engineer |
| **Database Pool Exhaustion** | > 80% capacity | > 95% capacity | Increase pool size / connection limits |
| **Memory Usage** | > 75% | > 90% | Restart container / upgrade instance tier |
