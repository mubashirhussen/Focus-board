# FocusBoard Data Intelligence, BI & Enterprise Insights Guide

FocusBoard Data Intelligence & Business Intelligence (Phase 42) transforms operational data from all core modules into verifiable analytics, data pipelines, interactive dashboards, custom reports, and grounded AI insights.

---

## 1. Centralized Data Catalog & Data Sources

The Data Catalog registers operational data sources and normalizes them into analytical datasets:
- `tasks_fact`: Operational task entities, completion times, cycle durations, and priority distributions.
- `projects_portfolio`: Project timelines, completion milestones, and deliverable tracking.
- `automation_executions`: Workflow execution records, error logs, and execution durations.
- `api_traffic`: API Gateway telemetry, response latencies, and HTTP status codes.

Each dataset tracks freshness (`FRESH`, `DELAYED`, `STALE`), schema fields, record counts, and last synchronization timestamps.

---

## 2. Automated ETL Data Pipelines

FocusBoard Data Pipelines automate the extraction, transformation, and aggregation of business records:
- **Productivity Aggregator**: Synthesizes task completion records into normalized cycle time and throughput dimensions.
- **Automation Reliability Pipeline**: Processes execution logs and computes SLA compliance metrics.
- Pipelines run on configurable cron schedules or can be executed on-demand via `POST /api/v1/data-intelligence/pipelines/{id}/run`.

---

## 3. Data Quality Engine

The Data Quality Engine audits data integrity across all operational datasets:
- **Completeness**: Validates mandatory fields (e.g. non-empty task titles).
- **Validity**: Enforces domain status constraints (e.g. valid workflow status sets).
- **Freshness**: Verifies telemetry freshness within 24-hour windows.
- Automatically calculates a platform-wide Data Quality Score (%) and logs any detected issues.

---

## 4. Grounded AI Analytics Assistant

Users can ask plain-English analytical questions via `POST /api/v1/data-intelligence/assistant/query`:
- Direct answers computed from real, un-hallucinated database records.
- Verifiable grounded evidence citing the source tables and record counts evaluated.
- Automated chart visualization recommendations (`KPI`, `BAR`, `LINE`, `TABLE`) with formatted chart series.
