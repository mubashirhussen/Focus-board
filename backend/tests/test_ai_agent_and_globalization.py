import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.models.task import Task

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def get_auth_token(client, email="agent.user@focusboard.com", role="Member", name="AI Operator"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "securepassword123", role: role},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

# ==========================================
# PHASE 30: AI-NATIVE AGENTS & ORCHESTRATION
# ==========================================

def test_list_and_get_system_agents(client):
    token = get_auth_token(client, "agents.test@focusboard.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    res = client.get("/api/v1/ai-agent/agents", headers=headers)
    assert res.status_code == 200
    agents = res.json()
    assert len(agents) >= 6

    agent_ids = [a["id"] for a in agents]
    assert "agent-task-planner" in agent_ids
    assert "agent-task-breakdown" in agent_ids
    assert "agent-project-planner" in agent_ids
    assert "agent-productivity-insights" in agent_ids
    assert "agent-workflow-automation" in agent_ids
    assert "agent-customer-support" in agent_ids

    # Detail check
    detail_res = client.get("/api/v1/ai-agent/agents/agent-task-planner", headers=headers)
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["name"] == "Autonomous Task Planner"
    assert "create_daily_plan" in data["tools"]

def test_agent_execution_and_planning(client):
    token = get_auth_token(client, "planner.test@focusboard.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Execute Project Architect Agent to plan a new project
    exec_res = client.post(
        "/api/v1/ai-agent/executions",
        json={
            "agent_id": "agent-project-planner",
            "prompt": "Create a project for launching my portfolio and organize the initial work",
        },
        headers=headers,
    )
    assert exec_res.status_code == 201
    exec_data = exec_res.json()
    assert exec_data["status"] in ["COMPLETED", "RUNNING"]
    assert len(exec_data["steps"]) >= 2
    assert exec_data["steps"][0]["tool_name"] == "create_project"
    assert exec_data["steps"][0]["status"] == "COMPLETED"

def test_human_approval_gate_for_sensitive_action(client):
    token = get_auth_token(client, "sensitive.test@focusboard.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Create a task to delete
    task_res = client.post(
        "/api/v1/tasks",
        json={"title": "Old obsolete task to delete", "priority": "low"},
        headers=headers,
    )
    assert task_res.status_code == 201

    # Request agent execution that involves deleting a task
    exec_res = client.post(
        "/api/v1/ai-agent/executions",
        json={
            "agent_id": "agent-task-planner",
            "prompt": "Clean up and delete obsolete tasks from my backlog",
        },
        headers=headers,
    )
    assert exec_res.status_code == 201
    data = exec_res.json()
    # Must halt at AWAITING_APPROVAL because delete_task is sensitive!
    assert data["status"] == "AWAITING_APPROVAL"
    assert len(data["pending_approvals"]) == 1
    approval = data["pending_approvals"][0]
    assert approval["status"] == "PENDING"
    assert approval["action_type"] == "DESTRUCTIVE_ACTION"

    # User explicitly APPROVES the deletion
    appr_res = client.post(
        f"/api/v1/ai-agent/executions/{data['id']}/approve?approval_id={approval['id']}",
        headers=headers,
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] == "COMPLETED"
    # Step that was awaiting approval is now completed
    completed_steps = [s for s in appr_data["steps"] if s["status"] == "COMPLETED"]
    assert any(s["tool_name"] == "delete_task" for s in completed_steps)

def test_human_approval_rejection_and_cancellation(client):
    token = get_auth_token(client, "reject.test@focusboard.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Request sensitive execution
    exec_res = client.post(
        "/api/v1/ai-agent/executions",
        json={
            "agent_id": "agent-task-planner",
            "prompt": "Please delete old tasks immediately",
        },
        headers=headers,
    )
    data = exec_res.json()
    assert data["status"] == "AWAITING_APPROVAL"
    approval_id = data["pending_approvals"][0]["id"]

    # Reject the action
    rej_res = client.post(
        f"/api/v1/ai-agent/executions/{data['id']}/reject?approval_id={approval_id}",
        headers=headers,
    )
    assert rej_res.status_code == 200
    rej_data = rej_res.json()
    # Step was skipped due to user rejection
    skipped_steps = [s for s in rej_data["steps"] if s["status"] == "SKIPPED"]
    assert len(skipped_steps) >= 1

    # Test cancellation on a new execution
    new_exec = client.post(
        "/api/v1/ai-agent/executions",
        json={"agent_id": "agent-task-planner", "prompt": "Delete old tasks"},
        headers=headers,
    ).json()

    cancel_res = client.post(
        f"/api/v1/ai-agent/executions/{new_exec['id']}/cancel",
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

def test_ai_persistent_preferences_memory(client):
    token = get_auth_token(client, "memory.test@focusboard.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Fetch default preferences
    pref_res = client.get("/api/v1/ai-agent/preferences", headers=headers)
    assert pref_res.status_code == 200
    data = pref_res.json()
    assert data["planning_style"] == "balanced"
    assert data["preferred_work_hours"] == 6

    # Update preferences
    up_res = client.put(
        "/api/v1/ai-agent/preferences",
        json={
            "planning_style": "deep_work",
            "preferred_work_hours": 8,
            "prioritization_approach": "impact_first",
        },
        headers=headers,
    )
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert up_data["planning_style"] == "deep_work"
    assert up_data["preferred_work_hours"] == 8
    assert up_data["prioritization_approach"] == "impact_first"

# ==========================================
# PHASE 31: GLOBAL SAAS & REGIONAL SETTINGS
# ==========================================

def test_regional_settings_and_locales(client):
    token = get_auth_token(client, "global.user@focusboard.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Fetch supported locales catalog
    loc_res = client.get("/api/v1/regional/locales", headers=headers)
    assert loc_res.status_code == 200
    catalog = loc_res.json()
    lang_codes = [l["code"] for l in catalog["languages"]]
    assert "en" in lang_codes
    assert "hi" in lang_codes  # Hindi
    assert "te" in lang_codes  # Telugu
    assert "ar" in lang_codes  # Arabic (RTL)

    currency_codes = [c["code"] for c in catalog["currencies"]]
    assert "USD" in currency_codes
    assert "INR" in currency_codes
    assert "EUR" in currency_codes

    # 2. Fetch default user regional settings
    set_res = client.get("/api/v1/regional/settings", headers=headers)
    assert set_res.status_code == 200
    cur_settings = set_res.json()
    assert cur_settings["language"] == "en"
    assert cur_settings["direction"] == "ltr"

    # 3. Update to Hindi (hi) with INR currency
    up_res = client.put(
        "/api/v1/regional/settings",
        json={
            "language": "hi",
            "locale": "hi-IN",
            "timezone": "Asia/Kolkata",
            "currency": "INR",
            "date_format": "DD/MM/YYYY",
        },
        headers=headers,
    )
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert up_data["language"] == "hi"
    assert up_data["currency"] == "INR"
    assert up_data["date_format"] == "DD/MM/YYYY"

    # 4. Update to Arabic (ar) -> auto-activates RTL direction
    ar_res = client.put(
        "/api/v1/regional/settings",
        json={"language": "ar", "currency": "AED"},
        headers=headers,
    )
    assert ar_res.status_code == 200
    assert ar_res.json()["direction"] == "rtl"

    # 5. Invalid currency rejection
    bad_res = client.put(
        "/api/v1/regional/settings",
        json={"currency": "XYZ_FAKE_CURRENCY"},
        headers=headers,
    )
    assert bad_res.status_code == 400
