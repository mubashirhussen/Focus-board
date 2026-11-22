# Runbook: Database Connectivity & Outage

## 1. Trigger & Severity
- **Trigger**: `/ready` probe returns HTTP 503; API endpoints return "Database connection error" or pool timeout.
- **Severity**: **SEV-1**.

## 2. Immediate Diagnostic Steps
1. Test readiness endpoint:
   ```bash
   curl https://api.focusboard.app/ready
   ```
2. Verify network connectivity to managed PostgreSQL provider (Neon / Supabase / AWS RDS):
   - Check provider incident status page.
   - Test connection string resolution and SSL handshake (`?sslmode=require`).
3. Check active connection pool utilization:
   Look for pool exhaustion in backend logs: `QueuePool limit of size X overflow Y reached`.

## 3. Resolution Procedures
- **If Pool Exhaustion**:
  Increase `pool_size` and `max_overflow` in `backend/app/db/database.py` or restart application containers to drain dangling connections.
- **If Managed Database Down**:
  Engage cloud provider support; if prolonged regional failure, initiate disaster recovery failover to cross-region replica.
- **If Migration Failure**:
  Inspect Alembic version table:
  ```bash
  alembic current
  ```

## 4. Post-Recovery Verification
```bash
curl https://api.focusboard.app/ready
# Expected: {"status": "ready", "database": "connected"}
```
