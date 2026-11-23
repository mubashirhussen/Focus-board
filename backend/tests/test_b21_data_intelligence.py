import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.data_intelligence import (
    DataSource,
    AnalyticsDataset,
    AnalyticsDataPipeline,
    AnalyticsPipelineExecution,
    AnalyticsDashboard,
    AnalyticsCustomReport,
    DataQualityRule,
    DataLineageNode,
    DataInsight,
)
from app.services.data_intelligence_service import execute_data_automation_action

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client: TestClient, prefix: str = "data_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique}@focusboard.io"
    password = "TestPassword123!"

    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"Data User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    headers = {"Authorization": f"Bearer {token}"}
    return headers, user_id, email

def create_test_workspace(client: TestClient, headers: dict, name: str = "Data WS") -> int:
    ws_res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Data Test Workspace"},
        headers=headers,
    )
    assert ws_res.status_code == 201, ws_res.text
    return ws_res.json()["id"]

# ==============================================================================
# 1. OVERVIEW & BASELINE SEEDING
# ==============================================================================
def test_data_intelligence_overview_and_seeding(client):
    headers, user_id, _ = get_auth_headers(client, "di_ov")
    ws_id = create_test_workspace(client, headers, "Overview WS")

    # API_V1_STR path
    res1 = client.get(f"{settings.API_V1_STR}/data-intelligence/overview?workspace_id={ws_id}", headers=headers)
    assert res1.status_code == 200, res1.text
    data1 = res1.json()

    assert data1["total_datasets_count"] >= 3
    assert data1["active_pipelines_count"] >= 2
    assert data1["data_quality_score_percent"] > 0
    assert "top_metrics_summary" in data1
    assert len(data1["datasets"]) >= 3
    assert len(data1["pipelines"]) >= 2
    assert len(data1["quality_rules"]) >= 2
    assert len(data1["recent_insights"]) >= 1

    # Direct path
    res2 = client.get(f"/data-intelligence/overview?workspace_id={ws_id}", headers=headers)
    assert res2.status_code == 200, res2.text

# ==============================================================================
# 2. DATA SOURCES MANAGEMENT & CONNECTION TESTING
# ==============================================================================
def test_data_sources_management_and_testing(client):
    headers, user_id, _ = get_auth_headers(client, "di_src")
    ws_id = create_test_workspace(client, headers, "Source WS")

    src_payload = {
        "name": "Production BigQuery Telemetry Cluster",
        "source_type": "BIGQUERY",
        "connection_status": "CONNECTED",
        "config_json": '{"project_id": "focusboard-prod", "dataset": "telemetry_v1"}',
        "workspace_id": ws_id,
    }
    res_create = client.post(f"{settings.API_V1_STR}/data-intelligence/sources", json=src_payload, headers=headers)
    assert res_create.status_code == 201, res_create.text
    src_data = res_create.json()
    src_id = src_data["id"]

    # Test connection
    res_test = client.post(f"{settings.API_V1_STR}/data-intelligence/sources/{src_id}/test", headers=headers)
    assert res_test.status_code == 200, res_test.text
    test_data = res_test.json()
    assert test_data["connection_status"] == "CONNECTED"
    assert test_data["latency_ms"] > 0

    # List sources
    res_list = client.get(f"{settings.API_V1_STR}/data-intelligence/sources?workspace_id={ws_id}", headers=headers)
    assert res_list.status_code == 200
    assert any(s["id"] == src_id for s in res_list.json())

# ==============================================================================
# 3. DATASET MANAGEMENT, IMPORTS & PROFILING
# ==============================================================================
def test_dataset_management_imports_and_profiling(client):
    headers, user_id, _ = get_auth_headers(client, "di_ds")
    ws_id = create_test_workspace(client, headers, "Dataset WS")

    # 1. Create Dataset
    ds_payload = {
        "name": "Sprint Cycle Times Fact Dataset",
        "slug": f"sprint_cycles_{uuid.uuid4().hex[:6]}",
        "category": "PRODUCTIVITY",
        "description": "Historical story points and cycle time duration per ticket.",
        "data_source": "JIRA_ETL",
        "source_type": "DATABASE",
        "classification": "INTERNAL",
        "freshness_status": "FRESH",
        "record_count": 120,
        "schema_json": '[{"name": "ticket_id", "type": "STRING"}, {"name": "cycle_hours", "type": "FLOAT"}]',
        "workspace_id": ws_id,
    }
    res_ds = client.post(f"{settings.API_V1_STR}/data-intelligence/datasets", json=ds_payload, headers=headers)
    assert res_ds.status_code == 201, res_ds.text
    slug = res_ds.json()["slug"]

    # 2. Ingest CSV records
    csv_raw = "user_id,session_duration,action_count\nu101,245.5,14\nu102,112.0,8\nu103,430.2,28\n"
    imp_payload = {
        "dataset_name": "Web User Telemetry Upload",
        "dataset_slug": f"web_telemetry_{uuid.uuid4().hex[:6]}",
        "category": "OPERATIONS",
        "format": "CSV",
        "raw_content": csv_raw,
        "workspace_id": ws_id,
    }
    res_imp = client.post(f"{settings.API_V1_STR}/data-intelligence/datasets/import", json=imp_payload, headers=headers)
    assert res_imp.status_code == 201, res_imp.text
    imp_data = res_imp.json()
    assert imp_data["imported_rows"] == 3
    assert len(imp_data["detected_columns"]) == 3

    # 3. Profile Dataset
    res_prof = client.get(f"{settings.API_V1_STR}/data-intelligence/datasets/{slug}/profile", headers=headers)
    assert res_prof.status_code == 200, res_prof.text
    prof_data = res_prof.json()
    assert prof_data["total_records"] == 120
    assert prof_data["column_count"] == 2
    assert "columns_profile" in prof_data

# ==============================================================================
# 4. PIPELINES LIFECYCLE & EXECUTION
# ==============================================================================
def test_pipelines_lifecycle_and_execution(client):
    headers, user_id, _ = get_auth_headers(client, "di_pipe")
    ws_id = create_test_workspace(client, headers, "Pipeline WS")

    pipe_payload = {
        "name": "Sprint Burndown & Velocity Sync ETL",
        "description": "Calculates daily completed story points and backlog throughput.",
        "source_dataset_slug": "tasks_fact",
        "target_model": "VelocitySnapshot",
        "pipeline_config_json": '{"stages": ["EXTRACT", "FILTER_ACTIVE", "CALCULATE_SUM", "LOAD"]}',
        "schedule_cron": "0 2 * * *",
        "status": "ACTIVE",
        "workspace_id": ws_id,
    }
    res_pipe = client.post(f"{settings.API_V1_STR}/data-intelligence/pipelines", json=pipe_payload, headers=headers)
    assert res_pipe.status_code == 201, res_pipe.text
    pipe_id = res_pipe.json()["id"]

    # Execute pipeline
    res_run = client.post(f"{settings.API_V1_STR}/data-intelligence/pipelines/{pipe_id}/run", headers=headers)
    assert res_run.status_code == 200, res_run.text
    run_data = res_run.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["records_processed"] >= 0
    assert run_data["duration_ms"] > 0
    assert "EXTRACTION" in run_data["logs_json"]

# ==============================================================================
# 5. ANALYTICAL DASHBOARDS & WIDGETS
# ==============================================================================
def test_analytical_dashboards_and_widgets(client):
    headers, user_id, _ = get_auth_headers(client, "di_dash")
    ws_id = create_test_workspace(client, headers, "Dashboard WS")

    dash_payload = {
        "title": "Engineering Velocity & SLA Dashboard",
        "description": "Monitors team cycle times and automation success metrics.",
        "visibility": "WORKSPACE",
        "workspace_id": ws_id,
        "layout_json": '{"columns": 2}',
        "widgets": [
            {
                "title": "Tasks Completed KPI",
                "widget_type": "KPI",
                "metric_identifier": "tasks_completed_count",
                "config_json": '{"color": "blue"}',
                "position_order": 0,
            },
            {
                "title": "Automation Reliability Trend",
                "widget_type": "LINE",
                "metric_identifier": "automation_success_rate",
                "config_json": '{"color": "green"}',
                "position_order": 1,
            },
        ],
    }
    res_dash = client.post(f"{settings.API_V1_STR}/data-intelligence/dashboards", json=dash_payload, headers=headers)
    assert res_dash.status_code == 201, res_dash.text
    dash_id = res_dash.json()["id"]
    assert len(res_dash.json()["widgets"]) == 2

    # Get single dashboard
    get_dash = client.get(f"{settings.API_V1_STR}/data-intelligence/dashboards/{dash_id}", headers=headers)
    assert get_dash.status_code == 200
    assert get_dash.json()["title"] == dash_payload["title"]

    # Delete dashboard
    del_res = client.delete(f"{settings.API_V1_STR}/data-intelligence/dashboards/{dash_id}", headers=headers)
    assert del_res.status_code == 204

# ==============================================================================
# 6. CUSTOM REPORTS, EXECUTION & EXPORT
# ==============================================================================
def test_custom_reports_execution_and_export(client):
    headers, user_id, _ = get_auth_headers(client, "di_rep")
    ws_id = create_test_workspace(client, headers, "Report WS")

    rep_payload = {
        "title": "Executive Operational Workload Report",
        "category": "PRODUCTIVITY",
        "query_config_json": '{"dimensions": ["status", "priority"], "aggregations": ["count"]}',
        "format": "CSV",
        "schedule_cron": "0 0 * * 1",
        "workspace_id": ws_id,
    }
    res_rep = client.post(f"{settings.API_V1_STR}/data-intelligence/reports", json=rep_payload, headers=headers)
    assert res_rep.status_code == 201, res_rep.text
    rep_id = res_rep.json()["id"]

    # Execute Report
    run_rep = client.post(f"{settings.API_V1_STR}/data-intelligence/reports/{rep_id}/run", headers=headers)
    assert run_rep.status_code == 200, run_rep.text
    res_data = run_rep.json()
    assert "total_records" in res_data
    assert "data_summary" in res_data

    # Export CSV
    exp_csv = client.get(f"{settings.API_V1_STR}/data-intelligence/reports/{rep_id}/export?format=CSV", headers=headers)
    assert exp_csv.status_code == 200, exp_csv.text
    assert exp_csv.json()["format"] == "CSV"
    assert "Task ID,Title,Status" in exp_csv.json()["raw_content"]

    # Export JSON
    exp_json = client.get(f"{settings.API_V1_STR}/data-intelligence/reports/{rep_id}/export?format=JSON", headers=headers)
    assert exp_json.status_code == 200, exp_json.text
    assert exp_json.json()["format"] == "JSON"

# ==============================================================================
# 7. DATA QUALITY RULES & AUDIT
# ==============================================================================
def test_data_quality_rules_and_audit(client):
    headers, user_id, _ = get_auth_headers(client, "di_qr")
    ws_id = create_test_workspace(client, headers, "Quality WS")

    res_qr = client.get(f"{settings.API_V1_STR}/data-intelligence/quality/rules?workspace_id={ws_id}", headers=headers)
    assert res_qr.status_code == 200, res_qr.text
    rules = res_qr.json()
    assert len(rules) >= 2
    assert any(r["rule_type"] == "COMPLETENESS" for r in rules)
    assert all("status" in r for r in rules)

# ==============================================================================
# 8. DATA LINEAGE GRAPH
# ==============================================================================
def test_data_lineage_graph(client):
    headers, user_id, _ = get_auth_headers(client, "di_lin")
    ws_id = create_test_workspace(client, headers, "Lineage WS")

    res_lin = client.get(f"{settings.API_V1_STR}/data-intelligence/lineage?workspace_id={ws_id}", headers=headers)
    assert res_lin.status_code == 200, res_lin.text
    lin_data = res_lin.json()
    assert lin_data["total_assets"] >= 2
    assert len(lin_data["edges"]) >= 2
    assert any(e["type"] == "SOURCE_TO_DATASET" for e in lin_data["edges"])

# ==============================================================================
# 9. DATA INSIGHTS & ANOMALIES
# ==============================================================================
def test_data_insights_and_anomalies(client):
    headers, user_id, _ = get_auth_headers(client, "di_ins")
    ws_id = create_test_workspace(client, headers, "Insight WS")

    ins_payload = {
        "title": "Anomaly Detected in Background Task Queue Latency",
        "description": "P99 job duration exceeded threshold by 24% between 14:00-15:00 UTC.",
        "insight_type": "ANOMALY",
        "severity": "WARNING",
        "confidence_score": 0.91,
        "supporting_data_json": '{"p99_latency_ms": 1420, "baseline_ms": 1140}',
        "status": "ACTIVE",
        "workspace_id": ws_id,
    }
    res_ins = client.post(f"{settings.API_V1_STR}/data-intelligence/insights", json=ins_payload, headers=headers)
    assert res_ins.status_code == 201, res_ins.text
    ins_id = res_ins.json()["id"]

    list_ins = client.get(f"{settings.API_V1_STR}/data-intelligence/insights?workspace_id={ws_id}", headers=headers)
    assert list_ins.status_code == 200
    assert any(i["id"] == ins_id for i in list_ins.json())

# ==============================================================================
# 10. AI NATURAL LANGUAGE ANALYTICS
# ==============================================================================
def test_ai_natural_language_analytics(client):
    headers, user_id, _ = get_auth_headers(client, "di_ai")
    ws_id = create_test_workspace(client, headers, "AI WS")

    # Question 1: Overdue tasks
    ai_req1 = {
        "prompt": "How many overdue tasks do we currently have across the workspace?",
        "workspace_id": ws_id,
    }
    res_ai1 = client.post(f"{settings.API_V1_STR}/data-intelligence/assistant/query", json=ai_req1, headers=headers)
    assert res_ai1.status_code == 200, res_ai1.text
    ai_data1 = res_ai1.json()
    assert "direct_answer" in ai_data1
    assert "overdue" in ai_data1["direct_answer"].lower()
    assert ai_data1["suggested_visualization"] == "KPI"
    assert len(ai_data1["grounded_evidence"]) >= 1

    # Question 2: Automation workflows
    ai_req2 = {
        "prompt": "What is our automation workflow reliability and success rate?",
        "workspace_id": ws_id,
    }
    res_ai2 = client.post(f"{settings.API_V1_STR}/data-intelligence/assistant/query", json=ai_req2, headers=headers)
    assert res_ai2.status_code == 200, res_ai2.text
    ai_data2 = res_ai2.json()
    assert "automation" in ai_data2["direct_answer"].lower()
    assert ai_data2["suggested_visualization"] == "BAR"

# ==============================================================================
# 11. MULTI-TENANT WORKSPACE ISOLATION
# ==============================================================================
def test_multi_tenant_workspace_isolation(client):
    headers_a, user_a, _ = get_auth_headers(client, "di_tenant_a")
    headers_b, user_b, _ = get_auth_headers(client, "di_tenant_b")

    ws_a = create_test_workspace(client, headers_a, "Workspace A")
    ws_b = create_test_workspace(client, headers_b, "Workspace B")

    # User A creates a data source in Workspace A
    res_create = client.post(
        f"{settings.API_V1_STR}/data-intelligence/sources",
        json={"name": "Workspace A Secret Source", "source_type": "INTERNAL_DB", "workspace_id": ws_a},
        headers=headers_a,
    )
    assert res_create.status_code == 201

    # User B attempts to access Workspace A overview or sources explicitly -> must get 403 Forbidden
    res_forbidden_ov = client.get(
        f"{settings.API_V1_STR}/data-intelligence/overview?workspace_id={ws_a}",
        headers=headers_b,
    )
    assert res_forbidden_ov.status_code == 403, "Cross-tenant access must be rejected with 403"

    res_forbidden_src = client.get(
        f"{settings.API_V1_STR}/data-intelligence/sources?workspace_id={ws_a}",
        headers=headers_b,
    )
    assert res_forbidden_src.status_code == 403, "Cross-tenant access must be rejected with 403"

# ==============================================================================
# 12. B15 AUTOMATION ACTION EXECUTION
# ==============================================================================
def test_b15_automation_action_execution(client):
    headers, user_id, _ = get_auth_headers(client, "di_auto")
    ws_id = create_test_workspace(client, headers, "Automation WS")

    db = SessionLocal()
    try:
        # 1. Run Pipeline Action
        act1 = execute_data_automation_action(
            db=db,
            action_type="RUN_PIPELINE",
            payload={},
            workspace_id=ws_id,
        )
        assert act1["status"] == "SUCCESS"
        assert "execution_id" in act1

        # 2. Run Data Quality Audit Action
        act2 = execute_data_automation_action(
            db=db,
            action_type="RUN_DATA_QUALITY_AUDIT",
            payload={},
            workspace_id=ws_id,
        )
        assert act2["status"] == "SUCCESS"
        assert act2["total_rules"] >= 2

        # 3. Import Dataset Action
        act3 = execute_data_automation_action(
            db=db,
            action_type="IMPORT_DATASET",
            payload={
                "dataset_name": "Automated Sensor Dataset",
                "raw_content": "device_id,temperature,humidity\nd1,22.4,45\nd2,23.1,44",
                "format": "CSV",
            },
            workspace_id=ws_id,
        )
        assert act3["status"] == "SUCCESS"
        assert act3["imported_rows"] == 2
    finally:
        db.close()
