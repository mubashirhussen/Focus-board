import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db

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

def get_auth_token(client, email="intelligence_user@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Intel Engineer", "email": email, "password": "securePassword123"}
    )
    return res.json()["access_token"]

def test_next_best_task_evaluation(client):
    """Test deterministic multi-factor next best task prioritization and explainability."""
    token = get_auth_token(client, "nbt_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    future_str = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")

    # 1. Add tasks: Overdue high-impact task, future low task, in-progress medium task
    client.post("/api/v1/tasks", headers=headers, json={
        "title": "Fix Critical Authentication CVE",
        "priority": "Critical",
        "due_date": yesterday_str,
        "status": "Todo",
        "estimated_duration_minutes": 60,
    })
    client.post("/api/v1/tasks", headers=headers, json={
        "title": "Update Documentation Theme",
        "priority": "Low",
        "due_date": future_str,
        "status": "Todo",
        "estimated_duration_minutes": 30,
    })
    client.post("/api/v1/tasks", headers=headers, json={
        "title": "Refactor Navigation Drawer",
        "priority": "Medium",
        "due_date": today_str,
        "status": "In Progress",
        "estimated_duration_minutes": 45,
    })

    # Call Next Best Task endpoint
    res = client.get("/api/v1/ai/next-best-task", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["task_id"] is not None
    assert data["title"] == "Fix Critical Authentication CVE"
    assert data["priority_score"] >= 85
    assert data["urgency_tier"] == "Critical"
    assert "OVERDUE_RISK" in data["explainability_tags"]
    assert "HIGH_IMPACT" in data["explainability_tags"]
    assert data["confidence_score"] >= 90.0
    assert len(data["ranked_queue"]) == 3

def test_adaptive_focus_session_lifecycle(client):
    """Test logging an adaptive focus sprint and verifying session statistics."""
    token = get_auth_token(client, "focus_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a task to focus on
    task_res = client.post("/api/v1/tasks", headers=headers, json={
        "title": "Implement Zero-Trust Posture Exporter",
        "priority": "High",
        "status": "In Progress",
    })
    task_id = task_res.json()["id"]

    # Log 2 focus sessions: 1 in progress (25m), 1 completed sprint (45m)
    res1 = client.post("/api/v1/ai/focus-sessions", headers=headers, json={
        "task_id": task_id,
        "task_title": "Implement Zero-Trust Posture Exporter",
        "duration_minutes": 25,
        "completed": False,
        "notes": "Completed interface contract definition.",
        "interruptions": 0,
    })
    assert res1.status_code == 201
    assert res1.json()["duration_minutes"] == 25

    res2 = client.post("/api/v1/ai/focus-sessions", headers=headers, json={
        "task_id": task_id,
        "task_title": "Implement Zero-Trust Posture Exporter",
        "duration_minutes": 45,
        "completed": True,
        "notes": "Verified telemetry stream and marked completed.",
        "interruptions": 1,
    })
    assert res2.status_code == 201
    assert res2.json()["completed"] is True

    # Verify task was auto-marked Completed
    t_check = client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert t_check.json()["status"] == "Completed"

    # Query focus session stats
    stats_res = client.get("/api/v1/ai/focus-stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_focus_minutes"] >= 70
    assert stats["completed_sessions_count"] == 1
    assert len(stats["recent_sessions"]) == 2

def test_predictive_project_risks(client):
    """Test project delivery forecasting, variance detection, and mitigation extraction."""
    token = get_auth_token(client, "risk_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    yesterday_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    # Add overdue and active tasks
    client.post("/api/v1/tasks", headers=headers, json={
        "title": "Resolve Alembic Migration Gap",
        "priority": "High",
        "due_date": yesterday_str,
        "status": "Todo",
        "estimated_duration_minutes": 120,
    })

    res = client.get("/api/v1/ai/predictive-risks", headers=headers)
    assert res.status_code == 200
    risk_info = res.json()

    assert risk_info["overall_risk_score"] > 0
    assert risk_info["risk_level"] in ["LOW", "MODERATE", "ELEVATED", "CRITICAL"]
    assert risk_info["predicted_completion_date"] is not None
    assert risk_info["critical_blockers_count"] == 1
    assert len(risk_info["identified_risks"]) >= 1
    assert len(risk_info["key_recommendations"]) >= 1

def test_team_workload_capacity_analysis(client):
    """Test team capacity aggregation, utilization percentages, and rebalancing recommendations."""
    token = get_auth_token(client, "capacity_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Add 2 tasks
    client.post("/api/v1/tasks", headers=headers, json={"title": "Audit Design System Tokens", "priority": "Medium", "status": "Todo"})
    client.post("/api/v1/tasks", headers=headers, json={"title": "Implement Mobile Drawer Navigation", "priority": "High", "status": "Todo"})

    res = client.get("/api/v1/ai/team-capacity", headers=headers)
    assert res.status_code == 200
    cap = res.json()

    assert cap["total_members"] >= 1
    assert cap["team_utilization_pct"] >= 0.0
    assert cap["available_capacity_hours"] > 0.0
    assert len(cap["members"]) >= 1
    assert len(cap["rebalancing_recommendations"]) >= 1

def test_meeting_intelligence_and_task_conversion(client):
    """Test meeting note parsing, action item extraction, and conversion into real board tasks."""
    token = get_auth_token(client, "meeting_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    notes = (
        "Weekly architecture sprint:\n"
        "- Decision: Enforce corporate email domain restriction on all employee registrations.\n"
        "- Action: Deploy Zero-Trust Posture Telemetry Exporter to staging.\n"
        "- Action: Run regression test suite on all 23 platform routes."
    )

    analyze_res = client.post("/api/v1/ai/meetings/analyze", headers=headers, json={
        "title": "Platform Architecture Sync",
        "notes_raw": notes,
    })
    assert analyze_res.status_code == 200
    meet = analyze_res.json()

    assert meet["meeting_id"] is not None
    assert len(meet["decisions"]) >= 1
    assert len(meet["action_items"]) >= 2

    # Pick the first action item and convert it to a real task
    first_action = meet["action_items"][0]
    convert_res = client.post("/api/v1/ai/meetings/convert-action-item", headers=headers, json={
        "meeting_id": meet["meeting_id"],
        "action_id": first_action["action_id"],
        "title": first_action["title"],
        "priority": "High",
    })
    assert convert_res.status_code == 200
    task_created = convert_res.json()
    assert task_created["task_id"] is not None
    assert task_created["status"] == "Created"

    # Confirm task exists in user task list
    t_check = client.get(f"/api/v1/tasks/{task_created['task_id']}", headers=headers)
    assert t_check.status_code == 200
    assert t_check.json()["title"] == first_action["title"]

def test_decision_log_memory(client):
    """Test project decision memory logging and retrieval."""
    token = get_auth_token(client, "decision_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a decision log
    dec_res = client.post("/api/v1/ai/decisions", headers=headers, json={
        "title": "Adopt SQLite StaticPool for In-Memory Unit Test Isolation",
        "context": "Parallel test executions required strict isolation without cross-test state leakage.",
        "rationale": "StaticPool prevents threading locks and provides microsecond-level reset velocity.",
        "alternatives": "Postgres test containers (high spin-up latency).",
        "impact": "HIGH",
        "status": "APPROVED",
        "owner_name": "Chief Architect",
    })
    assert dec_res.status_code == 201
    dec_data = dec_res.json()
    assert dec_data["id"] is not None
    assert dec_data["title"] == "Adopt SQLite StaticPool for In-Memory Unit Test Isolation"

    # Query decisions list
    list_res = client.get("/api/v1/ai/decisions", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert items[0]["title"] == dec_data["title"]
