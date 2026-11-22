# Runbook: Background Worker & Scheduler Failure

## 1. Trigger & Severity
- **Trigger**: Scheduled reminders, email notifications, or recurring sync jobs are delayed > 15 minutes.
- **Severity**: **SEV-3**.

## 2. Immediate Diagnostic Steps
1. Inspect worker process status in container logs:
   ```bash
   docker logs --tail 100 focusboard-backend | grep "Scheduler"
   ```
2. Check unread notification queue growth in database:
   `SELECT count(*) FROM notifications WHERE status = 'PENDING';`

## 3. Resolution Procedures
- **If Worker Thread Terminated**:
  Restart the application worker process:
  ```bash
  docker restart focusboard-backend
  ```
- **If Deadlocked Jobs**:
  Purge stuck or non-idempotent failed jobs from the dead-letter queue.
- **Worker Concurrency**:
  Increase worker thread pool size in `backend/entrypoint.sh` or environment settings (`WORKERS=4`).

## 4. Post-Recovery Verification
Verify pending notifications are processed and sent.
