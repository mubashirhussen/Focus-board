import os
import uuid
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.collaboration import Workspace
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def auth_context(db_session: Session):
    unique_email = f"platform_ops_{uuid.uuid4().hex[:8]}@focusboard.enterprise"
    user = User(
        email=unique_email,
        name="Lead SRE & Data Architect",
        hashed_password="hashed_pw_fixture",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    workspace = Workspace(
        name="Platform Operations Testing Workspace",
        description="Workspace for Phase 41-42 automated testing",
        owner_id=user.id,
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(workspace)

    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}, user, workspace


# ==============================================================================
# PHASE 41: OBSERVABILITY, HEALTH, ALERTS, INCIDENTS & DIAGNOSTICS TESTS
# ==============================================================================

def test_observability_overview(auth_context):
    headers, _, _ = auth_context
    resp = client.get("/api/v1/observability/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_health"] in ("OPERATIONAL", "DEGRADED", "CRITICAL")
    assert data["system_uptime_percentage"] > 99.0
    assert data["total_services_count"] >= 8
    assert len(data["services"]) >= 8
    assert len(data["slo_metrics"]) >= 3


def test_service_registry_live_health(auth_context):
    headers, _, _ = auth_context
    resp = client.get("/api/v1/observability/services", headers=headers)
    assert resp.status_code == 200
    services = resp.json()

    service_ids = [s["id"] for s in services]
    assert "api_core" in service_ids
    assert "db_primary" in service_ids
    assert "workers_queue" in service_ids
    assert "automation_engine" in service_ids
    assert all(s["response_time_ms"] >= 0 for s in services)


def test_alert_lifecycle(auth_context):
    headers, _, _ = auth_context

    # 1. Create alert
    payload = {
        "severity": "WARNING",
        "status": "ACTIVE",
        "summary": "Webhook delivery retry spike detected",
        "details": "Outgoing webhooks experienced 3 retries in 60s.",
        "related_service_id": "webhook_engine",
    }
    resp = client.post("/api/v1/observability/alerts", headers=headers, json=payload)
    assert resp.status_code == 201
    alert = resp.json()
    alert_id = alert["id"]
    assert alert["status"] == "ACTIVE"

    # 2. Acknowledge alert
    ack_resp = client.post(f"/api/v1/observability/alerts/{alert_id}/acknowledge", headers=headers)
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "ACKNOWLEDGED"

    # 3. Resolve alert
    res_resp = client.post(f"/api/v1/observability/alerts/{alert_id}/resolve", headers=headers)
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"


def test_incident_management_timeline_and_post_mortem(auth_context):
    headers, user, _ = auth_context

    # 1. Create incident
    inc_payload = {
        "title": "API Gateway Rate Limiter Degradation",
        "description": "Inbound requests to /api/v1/tasks experienced 200ms latency degradation.",
        "severity": "SEV2",
        "status": "DETECTED",
        "affected_services_json": json.dumps(["api_core", "workers_queue"]),
        "lead_operator_id": user.id,
    }
    resp = client.post("/api/v1/observability/incidents", headers=headers, json=inc_payload)
    assert resp.status_code == 201
    incident = resp.json()
    inc_id = incident["id"]
    assert incident["status"] == "DETECTED"
    assert len(incident["timeline_entries"]) >= 1

    # 2. Update status to MITIGATING and add root cause
    update_payload = {
        "status": "MITIGATING",
        "root_cause": "Temporary contention on cache layer caused queue latency.",
        "mitigation_summary": "Evicted stale keys and scaled worker thread pool.",
    }
    patch_resp = client.patch(f"/api/v1/observability/incidents/{inc_id}", headers=headers, json=update_payload)
    assert patch_resp.status_code == 200
    updated_inc = patch_resp.json()
    assert updated_inc["status"] == "MITIGATING"
    assert len(updated_inc["timeline_entries"]) >= 2

    # 3. Attach action item
    action_payload = {
        "action_description": "Implement circuit breaker on redis queue connection pool",
        "assignee_id": user.id,
    }
    act_resp = client.post(f"/api/v1/observability/incidents/{inc_id}/action-items", headers=headers, json=action_payload)
    assert act_resp.status_code == 201
    assert act_resp.json()["action_description"] == action_payload["action_description"]

    # 4. Resolve incident & publish post-mortem
    client.patch(f"/api/v1/observability/incidents/{inc_id}", headers=headers, json={"status": "RESOLVED"})
    pm_payload = {
        "impact_summary": "2.4% of task creation calls experienced delayed response times for 8 minutes.",
        "root_cause_analysis": "Resource exhaustion on memory allocator during high-concurrency burst.",
        "lessons_learned": "Alert thresholds should be lowered to catch memory pressure at 75%.",
        "preventative_measures": "Configured automated container memory autoscaling.",
    }
    pm_resp = client.post(f"/api/v1/observability/incidents/{inc_id}/post-mortem", headers=headers, json=pm_payload)
    assert pm_resp.status_code == 201
    assert pm_resp.json()["incident_id"] == inc_id

    # 5. Fetch full incident
    get_resp = client.get(f"/api/v1/observability/incidents/{inc_id}", headers=headers)
    assert get_resp.status_code == 200
    final_inc = get_resp.json()
    assert final_inc["status"] == "RESOLVED"
    assert len(final_inc["action_items"]) >= 1


def test_support_diagnostics_and_maintenance(auth_context):
    headers, _, workspace = auth_context

    # 1. Run support diagnostics
    diag_resp = client.post(
        "/api/v1/observability/diagnostics/support",
        headers=headers,
        json={"workspace_id": workspace.id, "check_type": "FULL"}
    )
    assert diag_resp.status_code == 200
    diag = diag_resp.json()
    assert diag["health_status"] == "HEALTHY"
    assert len(diag["checks_performed"]) >= 3
    assert len(diag["recommendations"]) >= 1

    # 2. Schedule maintenance window
    start_dt = datetime.now(timezone.utc) + timedelta(days=2)
    end_dt = start_dt + timedelta(hours=2)
    maint_payload = {
        "title": "Database Engine Version Security Patch",
        "description": "Zero-downtime rolling update of underlying database engine.",
        "status": "SCHEDULED",
        "scheduled_start": start_dt.isoformat(),
        "scheduled_end": end_dt.isoformat(),
        "affected_services_json": json.dumps(["db_primary"]),
    }
    maint_resp = client.post("/api/v1/observability/maintenance", headers=headers, json=maint_payload)
    assert maint_resp.status_code == 201
    assert maint_resp.json()["title"] == maint_payload["title"]


# ==============================================================================
# PHASE 42: DATA INTELLIGENCE, DATASETS, PIPELINES & BI TESTS
# ==============================================================================

def test_data_intelligence_overview_and_datasets(auth_context):
    headers, _, workspace = auth_context
    resp = client.get(f"/api/v1/data-intelligence/overview?workspace_id={workspace.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_datasets_count"] >= 4
    assert data["fresh_datasets_count"] >= 4
    assert data["data_quality_score_percent"] >= 80.0
    assert "top_metrics_summary" in data

    # Test datasets endpoint
    ds_resp = client.get("/api/v1/data-intelligence/datasets", headers=headers)
    assert ds_resp.status_code == 200
    datasets = ds_resp.json()
    slugs = [d["slug"] for d in datasets]
    assert "tasks_fact" in slugs
    assert "automation_executions" in slugs


def test_analytics_pipeline_execution(auth_context):
    headers, _, _ = auth_context

    # 1. List pipelines
    pipe_resp = client.get("/api/v1/data-intelligence/pipelines", headers=headers)
    assert pipe_resp.status_code == 200
    pipelines = pipe_resp.json()
    assert len(pipelines) >= 2
    pipe = pipelines[0]

    # 2. Run pipeline
    run_resp = client.post(f"/api/v1/data-intelligence/pipelines/{pipe['id']}/run", headers=headers)
    assert run_resp.status_code == 200
    exec_data = run_resp.json()
    assert exec_data["status"] == "COMPLETED"
    assert exec_data["duration_ms"] >= 0


def test_analytics_dashboards_crud(auth_context):
    headers, _, workspace = auth_context

    payload = {
        "workspace_id": workspace.id,
        "title": "Executive Operational & BI Dashboard",
        "description": "Cross-cutting productivity, automation and reliability telemetry.",
        "visibility": "WORKSPACE",
        "layout_json": json.dumps([{"i": "w1", "x": 0, "y": 0, "w": 6, "h": 4}]),
        "widgets": [
            {
                "title": "Tasks Completed KPI",
                "widget_type": "KPI",
                "metric_identifier": "tasks_completed_count",
                "config_json": json.dumps({"color": "green"}),
                "position_order": 0,
            },
            {
                "title": "Automation Reliability Rate",
                "widget_type": "LINE",
                "metric_identifier": "automation_success_rate",
                "config_json": json.dumps({"chart_type": "line"}),
                "position_order": 1,
            }
        ],
    }

    # 1. Create dashboard
    resp = client.post("/api/v1/data-intelligence/dashboards", headers=headers, json=payload)
    assert resp.status_code == 201
    dash = resp.json()
    dash_id = dash["id"]
    assert dash["title"] == payload["title"]
    assert len(dash["widgets"]) == 2

    # 2. Get dashboard
    get_resp = client.get(f"/api/v1/data-intelligence/dashboards/{dash_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == dash_id

    # 3. Delete dashboard
    del_resp = client.delete(f"/api/v1/data-intelligence/dashboards/{dash_id}", headers=headers)
    assert del_resp.status_code == 204


def test_analytics_custom_reports(auth_context):
    headers, _, workspace = auth_context

    payload = {
        "workspace_id": workspace.id,
        "title": "Monthly Productivity & Cycle Time Audit",
        "category": "PRODUCTIVITY",
        "query_config_json": json.dumps({"group_by": "status", "time_window": "30d"}),
        "format": "CSV",
        "schedule_cron": "0 8 1 * *",
    }

    # 1. Create report
    resp = client.post("/api/v1/data-intelligence/reports", headers=headers, json=payload)
    assert resp.status_code == 201
    rep = resp.json()
    rep_id = rep["id"]

    # 2. Execute report
    run_resp = client.post(f"/api/v1/data-intelligence/reports/{rep_id}/run", headers=headers)
    assert run_resp.status_code == 200
    res = run_resp.json()
    assert res["report_id"] == rep_id
    assert "total_records" in res
    assert "generated_at" in res


def test_data_quality_audit(auth_context):
    headers, _, _ = auth_context
    resp = client.get("/api/v1/data-intelligence/quality/rules", headers=headers)
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) >= 3
    assert all(r["status"] in ("PASS", "FAIL") for r in rules)


def test_ai_analytics_assistant_query(auth_context):
    headers, _, workspace = auth_context
    resp = client.post(
        "/api/v1/data-intelligence/assistant/query",
        headers=headers,
        json={
            "prompt": "What is our current automation workflow success rate and how many tasks are overdue?",
            "workspace_id": workspace.id,
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["direct_answer"] != ""
    assert "synthesized_metrics" in data
    assert len(data["grounded_evidence"]) >= 1
    assert data["suggested_visualization"] in ("KPI", "BAR", "LINE", "TABLE")
    assert len(data["chart_data"]) >= 1
