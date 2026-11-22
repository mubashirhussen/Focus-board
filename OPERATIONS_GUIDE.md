# FocusBoard Operations & Maintenance Guide

## 1. Operational Cadence & Checklists

### Daily Checks (Automated via Cron / Health Pings)
- Verify `/health` and `/ready` probes respond with HTTP 200.
- Verify zero unresolved SEV-1 or SEV-2 alerts.
- Check database connection pool utilization in cloud console.

### Weekly Checks
- Review error budget burn rate in SRE dashboard.
- Inspect top 5 slowest database queries via query logs.
- Review unread notification backlog and failed background jobs.

### Monthly Maintenance
- Review database storage growth and archive audit records older than 90 days if configured.
- Run dependency vulnerability scan (`npm audit`, `pip-audit`).
- Review cloud hosting expenditures against budget targets.

### Quarterly Disaster Recovery Drill
- Perform live drill restoring a database snapshot to an isolated staging environment.
- Verify RPO (< 1 hour) and RTO (< 30 minutes) compliance.
