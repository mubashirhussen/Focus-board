# FocusBoard Incident Management Framework

## 1. Incident Classification & Severity Matrix

| Severity | Definition | Target Response (MTTD) | Target Resolution (MTTR) | Communication |
|---|---|---|---|---|
| **SEV-1** | Critical outage; all users blocked; data loss risk | **< 5 minutes** | **< 30 minutes** | Internal channel + Public Statuspage update every 15 min |
| **SEV-2** | Major degradation; core workflow impaired (e.g. task saving down) | **< 15 minutes** | **< 2 hours** | Statuspage notification + Slack alert |
| **SEV-3** | Minor feature down (e.g. AI suggestions or exports failing) | **< 1 hour** | **< 8 hours** | Internal tracking ticket |
| **SEV-4** | Cosmetic or non-blocking defect | **< 4 hours** | Next sprint release | Bug tracker |

---

## 2. Incident Response Lifecycle
```
[Detection: Alert / Sentry / Probe] ──► [Triage & Severity Assignment]
                                                  │
[Post-Mortem Review] ◄── [Resolution Verification] ◄── [Containment via Runbook]
```

### Phase 1: Triage
- Assign Incident Commander (IC).
- Post initial notification to status channel: *"Investigating reports of elevated latency / error rates"*.

### Phase 2: Containment & Remediation
- Follow the corresponding operational runbook in `RUNBOOKS/`.
- If bad release: execute immediate rollback via `RUNBOOKS/runbook_deployment_failure.md`.
- If database issue: consult `RUNBOOKS/runbook_database_outage.md`.

### Phase 3: Resolution & Blameless Post-Mortem
- Verify all health probes and smoke tests pass.
- Publish post-incident timeline and corrective action items within 48 hours.
