# FocusBoard Service Level Objectives (SLOs) & Error Budget Framework

## 1. Service Level Indicators (SLIs)
FocusBoard monitors 4 core indicators:
1. **API Availability**: Percentage of valid HTTP requests returning non-5xx responses.
2. **API Latency**: Response time measured at the ingress gateway.
3. **Database Connectivity**: Success rate of ping queries across worker connection pools.
4. **Offline Synchronization Integrity**: Percentage of queued offline actions successfully replayed without data corruption.

---

## 2. Service Level Objectives (SLOs)

| Service Area | SLI Metric | Monthly SLO Target |
|---|---|---|
| **API Availability** | Successful (non-5xx) HTTP responses | **99.9%** (~43 minutes downtime/month) |
| **Critical API Latency** | P95 latency for task CRUD & auth | **< 200 ms** |
| **Edge API Latency** | P99 latency across all routes | **< 500 ms** |
| **Database Pool Health** | Connection acquisition time | **< 50 ms** |
| **Background Notifications** | Dispatch delay from scheduled time | **< 60 seconds** (99% of jobs) |

---

## 3. Error Budget Management
- **Monthly Error Budget (99.9% SLO)**: 0.1% of all production requests.
- **Burn-Rate Alerts**:
  - *Fast Burn Alert*: 2% of monthly budget consumed in 1 hour -> Page On-Call Engineer.
  - *Slow Burn Alert*: 10% of monthly budget consumed in 24 hours -> File SEV-3 Ticket.
- **Budget Exhaustion Policy**:
  If monthly error budget is depleted (> 0.1% failures), non-critical feature releases are frozen. Engineering efforts shift entirely to reliability hardening and technical debt elimination.
