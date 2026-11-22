# Runbook: Application Outage & Unresponsiveness

## 1. Trigger & Severity
- **Trigger**: Uptime probe returns HTTP 5xx or fails to respond for 2 consecutive intervals; P95 latency > 1000ms.
- **Severity**: **SEV-1** (if all traffic impacted) or **SEV-2** (partial traffic).

## 2. Immediate Diagnostic Steps
1. Verify API server status:
   ```bash
   curl -I https://api.focusboard.app/health
   curl -I https://api.focusboard.app/ready
   ```
2. Inspect application container logs for fatal exceptions or OOM (Out Of Memory) signals:
   ```bash
   docker logs --tail 100 focusboard-backend
   ```
3. Inspect system CPU and memory utilization on host or cloud container console (Render / Railway / ECS).

## 3. Resolution Procedures
- **If Container Crashed / OOM**:
  Restart the backend service container:
  ```bash
  docker restart focusboard-backend
  ```
- **If Host Saturated**:
  Scale container instances vertically (increase RAM/CPU) or horizontally (+1 replica).
- **If Ingress / Edge Failure**:
  Check CDN / Cloudflare proxy status and DNS resolution.

## 4. Post-Recovery Verification
Run deployment smoke test to confirm all routes are healthy:
```bash
python scripts/smoke_test.py --backend-url https://api.focusboard.app --frontend-url https://app.focusboard.app
```
