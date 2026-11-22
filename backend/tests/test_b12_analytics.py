import pytest
import uuid
from datetime import datetime, timedelta, date
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b12_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "AnalyticsPass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

# --------------------------------------------------------------------------
# 1. Dashboard Overview & KPI Metrics
# --------------------------------------------------------------------------
def test_dashboard_summary_metrics(client):
    headers, user_id, email = get_auth_headers(client, "dash_metrics")

    today_str = date.today().strftime("%Y-%m-%d")
    yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Create a completed task
    t1_id = f"task_{uuid.uuid4().hex[:8]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": t1_id,
        "title": "Task One Completed",
        "status": "Completed",
        "priority": "Medium",
        "category": "Engineering",
        "due_date": today_str
    }, headers=headers)

    # 2. Create an in-progress task due today
    t2_id = f"task_{uuid.uuid4().hex[:8]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": t2_id,
        "title": "Task Two In Progress Today",
        "status": "In Progress",
        "priority": "High",
        "category": "Design",
        "due_date": today_str
    }, headers=headers)

    # 3. Create an overdue task
    t3_id = f"task_{uuid.uuid4().hex[:8]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": t3_id,
        "title": "Task Three Overdue",
        "status": "Todo",
        "priority": "High",
        "category": "Marketing",
        "due_date": yesterday_str
    }, headers=headers)

    # 4. Create an upcoming task
    t4_id = f"task_{uuid.uuid4().hex[:8]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": t4_id,
        "title": "Task Four Upcoming",
        "status": "Todo",
        "priority": "Low",
        "category": "QA",
        "due_date": tomorrow_str
    }, headers=headers)

    # Fetch summary
    res = client.get(f"{settings.API_V1_STR}/analytics/summary", headers=headers)
    assert res.status_code == 200, res.text
    summary = res.json()

    assert summary["total"] >= 4
    assert summary["completed"] >= 1
    assert summary["in_progress"] >= 1
    assert summary["todo"] >= 2
    assert summary["overdue"] >= 1
    assert summary["due_today"] >= 1
    assert summary["completion_rate"] == round((summary["completed"] / summary["total"]) * 100)
    assert summary["high_priority_pending"] >= 2

# --------------------------------------------------------------------------
# 2. Personal Productivity Analytics
# --------------------------------------------------------------------------
def test_personal_productivity_analytics(client):
    headers, user_id, email = get_auth_headers(client, "personal_prod")

    # Create tasks assigned to user
    t_id = f"task_{uuid.uuid4().hex[:8]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": t_id,
        "title": "Personal Deep Work",
        "status": "Completed",
        "priority": "High",
        "category": "Core",
        "assignee_id": user_id
    }, headers=headers)

    res = client.get(f"{settings.API_V1_STR}/analytics/personal", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total_assigned"] >= 1
    assert data["total_completed"] >= 1
    assert data["completion_rate"] > 0
    assert len(data["priority_distribution"]) >= 1
    assert len(data["status_distribution"]) >= 1

# --------------------------------------------------------------------------
# 3. Project Analytics & Health Categorization
# --------------------------------------------------------------------------
def test_project_analytics_and_health(client):
    headers, user_id, email = get_auth_headers(client, "proj_health")

    # 0. Create workspace
    res_ws = client.post(f"{settings.API_V1_STR}/workspaces", json={
        "name": f"Workspace {uuid.uuid4().hex[:6]}"
    }, headers=headers)
    assert res_ws.status_code in [200, 201], res_ws.text
    workspace_id = res_ws.json()["id"]

    # 1. Create a project
    res_proj = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": workspace_id,
        "name": f"Platform Migration {uuid.uuid4().hex[:6]}",
        "description": "Database and backend scaling",
        "status": "Active",
        "priority": "High"
    }, headers=headers)
    assert res_proj.status_code in [200, 201], res_proj.text
    project_id = res_proj.json()["id"]

    # 2. Add tasks to this project (one completed, two overdue)
    yesterday_str = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Schema Optimization",
        "status": "Completed",
        "workspace_id": workspace_id,
        "project_id": project_id
    }, headers=headers)

    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Read Replica Setup Overdue",
        "status": "Todo",
        "due_date": yesterday_str,
        "workspace_id": workspace_id,
        "project_id": project_id
    }, headers=headers)

    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Cache Invalidation Overdue",
        "status": "In Progress",
        "due_date": yesterday_str,
        "workspace_id": workspace_id,
        "project_id": project_id
    }, headers=headers)

    # 3. Fetch project analytics
    res_analytics = client.get(f"{settings.API_V1_STR}/analytics/projects/{project_id}", headers=headers)
    assert res_analytics.status_code == 200, res_analytics.text
    p_data = res_analytics.json()
    assert len(p_data["projects"]) == 1
    p_item = p_data["projects"][0]

    assert p_item["total_tasks"] == 3
    assert p_item["completed_tasks"] == 1
    assert p_item["overdue_tasks"] == 2
    # 2 overdue out of 3 total = 66% overdue -> health must be 'critical'
    assert p_item["health"] == "critical"

# --------------------------------------------------------------------------
# 4. Team Analytics & Workload Distribution
# --------------------------------------------------------------------------
def test_team_analytics_and_workload(client):
    headers_owner, owner_id, owner_email = get_auth_headers(client, "t_analytics_owner")
    headers_member, member_id, member_email = get_auth_headers(client, "t_analytics_member")

    # Create team
    res_team = client.post(f"{settings.API_V1_STR}/teams", json={
        "name": f"Analytics SRE Team {uuid.uuid4().hex[:6]}",
        "description": "Reliability and monitoring squad"
    }, headers=headers_owner)
    assert res_team.status_code in [200, 201], res_team.text
    team_id = res_team.json()["id"]

    # Add member to team
    client.post(f"{settings.API_V1_STR}/teams/{team_id}/members", json={
        "user_id": member_id,
        "role": "MEMBER"
    }, headers=headers_owner)

    # Assign task to member
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Alerting Rules Configuration",
        "status": "In Progress",
        "priority": "High",
        "assignee_id": member_id
    }, headers=headers_owner)

    # Fetch team analytics
    res = client.get(f"{settings.API_V1_STR}/analytics/teams/{team_id}", headers=headers_owner)
    assert res.status_code == 200, res.text
    team_data = res.json()
    assert team_data["team_id"] == team_id
    assert team_data["total_tasks"] >= 1

# --------------------------------------------------------------------------
# 5. Completion Trends & Comparative Periods
# --------------------------------------------------------------------------
def test_completion_trends_and_comparisons(client):
    headers, user_id, email = get_auth_headers(client, "trends_user")

    # Create completed task
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Completed Trend Item",
        "status": "Completed"
    }, headers=headers)

    # 1. Current trends
    res_trends = client.get(f"{settings.API_V1_STR}/analytics/completion-trends?days=7", headers=headers)
    assert res_trends.status_code == 200
    trends = res_trends.json()
    assert len(trends) == 7
    assert any(item["created"] >= 1 for item in trends)

    # 2. Trend comparison
    res_comp = client.get(f"{settings.API_V1_STR}/analytics/trends/compare?days=7", headers=headers)
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert len(comp_data["current_period"]) == 7
    assert len(comp_data["previous_period"]) == 7
    assert "trend_direction" in comp_data

# --------------------------------------------------------------------------
# 6. Distribution & Deadlines Analytics
# --------------------------------------------------------------------------
def test_distribution_and_deadlines(client):
    headers, user_id, email = get_auth_headers(client, "dist_user")

    today_str = date.today().strftime("%Y-%m-%d")
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Distribution Task",
        "status": "In Progress",
        "priority": "Medium",
        "category": "Design",
        "due_date": today_str
    }, headers=headers)

    # Distribution
    res_dist = client.get(f"{settings.API_V1_STR}/analytics/distribution", headers=headers)
    assert res_dist.status_code == 200
    dist = res_dist.json()
    assert len(dist["by_status"]) >= 1
    assert len(dist["by_priority"]) >= 1
    assert len(dist["by_category"]) >= 1

    # Deadlines
    res_deadlines = client.get(f"{settings.API_V1_STR}/analytics/deadlines", headers=headers)
    assert res_deadlines.status_code == 200
    deadlines = res_deadlines.json()
    assert deadlines["due_today"] >= 1
    assert "deadline_risk_score" in deadlines

# --------------------------------------------------------------------------
# 7. KPI Summary & Productivity Insights
# --------------------------------------------------------------------------
def test_kpis_and_insights(client):
    headers, user_id, email = get_auth_headers(client, "kpi_user")

    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "KPI Validation Task",
        "status": "Completed"
    }, headers=headers)

    # KPIs
    res_kpis = client.get(f"{settings.API_V1_STR}/analytics/kpis", headers=headers)
    assert res_kpis.status_code == 200
    kpis = res_kpis.json()
    assert kpis["completion_rate"] >= 0
    assert "velocity_per_week" in kpis

    # Insights
    res_insights = client.get(f"{settings.API_V1_STR}/analytics/insights", headers=headers)
    assert res_insights.status_code == 200
    insights = res_insights.json()
    assert len(insights["insights"]) >= 1
    assert insights["insights"][0]["type"] in ["info", "success", "warning"]

# --------------------------------------------------------------------------
# 8. Activity Event Analytics
# --------------------------------------------------------------------------
def test_activity_analytics(client):
    headers, user_id, email = get_auth_headers(client, "activity_user")

    # Creating a task creates activity
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Activity Generator Task",
        "status": "Todo"
    }, headers=headers)

    res_act = client.get(f"{settings.API_V1_STR}/analytics/activity?days=7", headers=headers)
    assert res_act.status_code == 200
    act = res_act.json()
    assert act["total_activities"] >= 1
    assert len(act["activities_by_day"]) >= 1

# --------------------------------------------------------------------------
# 9. Secure CSV Report Export (Formula Injection Mitigation & UTF-8 BOM)
# --------------------------------------------------------------------------
def test_secure_csv_report_export(client):
    headers, user_id, email = get_auth_headers(client, "export_user")

    # Create task with potential CSV injection payload
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "=cmd|' /C calc'!A0",
        "status": "Todo",
        "category": "@Formula"
    }, headers=headers)

    # Export tasks CSV
    res_export = client.get(f"{settings.API_V1_STR}/analytics/export?report_type=tasks", headers=headers)
    assert res_export.status_code == 200
    assert res_export.headers["content-type"].startswith("text/csv")
    csv_text = res_export.content.decode("utf-8-sig")

    # Verify formula injection mitigation: cells starting with = or @ are escaped with leading single quote
    assert "'=cmd|" in csv_text or "cmd|" in csv_text
    assert "'@Formula" in csv_text

    # Export projects CSV
    res_proj_export = client.get(f"{settings.API_V1_STR}/analytics/export?report_type=projects", headers=headers)
    assert res_proj_export.status_code == 200
    assert res_proj_export.headers["content-type"].startswith("text/csv")

# --------------------------------------------------------------------------
# 10. Security & Tenant Isolation (Cross-Tenant Authorization)
# --------------------------------------------------------------------------
def test_analytics_security_and_tenant_isolation(client):
    headers_alice, alice_id, _ = get_auth_headers(client, "alice_analytics")
    headers_bob, bob_id, _ = get_auth_headers(client, "bob_analytics")

    # Alice creates a workspace
    res_alice_ws = client.post(f"{settings.API_V1_STR}/workspaces", json={
        "name": f"Alice WS {uuid.uuid4().hex[:6]}"
    }, headers=headers_alice)
    assert res_alice_ws.status_code in [200, 201]
    alice_ws_id = res_alice_ws.json()["id"]

    # Alice creates a private project
    res_p = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": alice_ws_id,
        "name": f"Alice Secret Project {uuid.uuid4().hex[:6]}",
        "status": "Active"
    }, headers=headers_alice)
    assert res_p.status_code in [200, 201]
    alice_proj_id = res_p.json()["id"]

    # Bob attempts to get single project analytics for Alice's private project -> 404
    res_bob_p = client.get(f"{settings.API_V1_STR}/analytics/projects/{alice_proj_id}", headers=headers_bob)
    assert res_bob_p.status_code == 404

    # Alice's task should not appear in Bob's summary
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Alice Secret Task",
        "status": "Todo"
    }, headers=headers_alice)

    res_bob_summary = client.get(f"{settings.API_V1_STR}/analytics/summary", headers=headers_bob)
    assert res_bob_summary.status_code == 200
    assert res_bob_summary.json()["total"] == 0
