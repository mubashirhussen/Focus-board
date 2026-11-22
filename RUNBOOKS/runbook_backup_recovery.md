# Runbook: Database Backup & Point-In-Time Disaster Recovery

## 1. Trigger & Severity
- **Trigger**: Catastrophic database corruption, accidental mass table deletion, or storage hardware failure.
- **Severity**: **SEV-1**.

## 2. Immediate Diagnostic Steps
1. Stop incoming write traffic by putting the API in maintenance mode or scaling backend replicas to 0.
2. Identify the target Point-in-Time timestamp (UTC) immediately preceding the incident.

## 3. Recovery Procedure
- **Method 1: Point-In-Time Recovery (PITR) on Cloud Provider (Neon / AWS RDS)**:
  1. Open cloud database console.
  2. Select "Restore to Point in Time".
  3. Enter the target timestamp.
  4. Launch restored database instance.
  5. Update `DATABASE_URL` in container environment settings.
- **Method 2: Standalone S3 Snapshot Restore**:
  1. Download the latest daily encrypted dump from backup S3 bucket:
     ```bash
     aws s3 cp s3://focusboard-backups/focusboard_dump_latest.sql.gz .
     ```
  2. Decompress and restore into target PostgreSQL instance:
     ```bash
     gzip -d focusboard_dump_latest.sql.gz
     psql "$DATABASE_URL" < focusboard_dump_latest.sql
     ```
  3. Run Alembic verification:
     ```bash
     python -m scripts.run_migrations
     ```

## 4. Post-Recovery Verification
Run smoke tests and verify task counts and user records match expected state.
