# Runbook: Failed Deployment & Fast Rollback

## 1. Trigger & Severity
- **Trigger**: Post-deployment smoke test fails (`python scripts/smoke_test.py` exits with code 1); error rate spikes immediately after new release.
- **Severity**: **SEV-1** or **SEV-2**.

## 2. Immediate Diagnostic Steps
1. Run smoke tests to pinpoint the failing component:
   ```bash
   python scripts/smoke_test.py --backend-url https://api.focusboard.app --frontend-url https://app.focusboard.app
   ```
2. Review deployment logs in GitHub Actions (`.github/workflows/deploy.yml`) or cloud container host.

## 3. Fast Rollback Procedure
- **Frontend Rollback (Instant)**:
  In Vercel / Cloudflare Pages dashboard, promote the previous verified deployment snapshot with one click.
- **Backend Container Rollback**:
  Revert container image tag to previous stable version (e.g. `focusboard-backend:v1.0.0` -> `focusboard-backend:v0.9.9`).
- **Database Safety Check**:
  Verify whether the failed deployment executed a forward schema migration. If schema is backward-compatible (all FocusBoard migrations are additive), keep schema intact and roll back application container.

## 4. Post-Rollback Verification
Run smoke tests to confirm previous stable release is active and error rates return to zero.
