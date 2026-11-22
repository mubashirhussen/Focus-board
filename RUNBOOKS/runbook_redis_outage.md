# Runbook: Redis Cache & Queue Outage

## 1. Trigger & Severity
- **Trigger**: Background worker stalls; cache lookups fail or timeout.
- **Severity**: **SEV-2** or **SEV-3** (Core task management continues functioning; caching degrades gracefully).

## 2. Immediate Diagnostic Steps
1. Verify Redis cluster connectivity:
   ```bash
   # Check Redis ping
   redis-cli -u "$REDIS_URL" ping
   ```
2. Inspect backend logs for connection timeout warnings from cache clients.

## 3. Resolution Procedures
- **Graceful Fallback**:
  FocusBoard is architected so cache failures do not crash API requests. Database queries serve as direct fallbacks.
- **Restart Redis**:
  Restart the local Redis container or check managed Upstash / ElastiCache instance status.
- **Evict Stale Memory**:
  If Redis ran out of memory, verify `maxmemory-policy` is set to `allkeys-lru` and trigger an eviction.

## 4. Post-Recovery Verification
Verify background tasks and notification dispatch operate normally.
