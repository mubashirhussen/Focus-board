# FocusBoard Disaster Recovery & Backup Guide

## 1. Business Continuity Objectives
- **Recovery Point Objective (RPO)**: **< 1 hour** (Maximum tolerable data loss in disaster).
- **Recovery Time Objective (RTO)**: **< 30 minutes** (Maximum tolerable downtime to restore service).

---

## 2. Backup Strategy

### 2.1 Automated Cloud Database Snapshots
- **Managed PostgreSQL**: Continuous write-ahead log (WAL) archiving with point-in-time recovery (PITR) up to 7 days on Neon/Supabase/AWS RDS.
- **Daily Full Dumps**: Automated `pg_dump` executed daily at 02:00 UTC and uploaded to encrypted, geo-redundant S3 storage with 30-day retention.

### 2.2 Application State & Configuration
- Application source code and Alembic migrations are versioned immutably in Git (`master` branch).
- Environment templates are stored in `.env.production.example`.

---

## 3. Disaster Recovery Procedures

### Scenario A: Accidental Data Corruption or Destructive Mutation
1. Identify the timestamp immediately preceding the corruption event.
2. Initiate point-in-time recovery (PITR) in the managed PostgreSQL console to branch a restored database.
3. Update `DATABASE_URL` in the backend environment variables to point to the restored instance.
4. Verify data integrity and run `python scripts/smoke_test.py`.

### Scenario B: Cloud Provider Regional Outage
1. Provision secondary database from the latest cross-region snapshot backup.
2. Spin up backend container cluster in the alternate cloud region using existing Dockerfile.
3. Update DNS records (or Cloudflare load balancer) to route traffic to the secondary region.
4. Run health and readiness checks.
