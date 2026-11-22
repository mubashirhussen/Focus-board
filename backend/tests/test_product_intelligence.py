import pytest
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

def get_auth_token(client, email="intel_user@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Intelligence Tester", "email": email, "password": "password123"},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

def test_metrics_and_patterns_calculation(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Create several tasks with varying priorities
    client.post("/api/v1/tasks", json={"title": "High Priority Task 1", "priority": "High"}, headers=headers)
    client.post("/api/v1/tasks", json={"title": "High Priority Task 2", "priority": "High"}, headers=headers)
    client.post("/api/v1/tasks", json={"title": "High Priority Task 3", "priority": "High"}, headers=headers)
    t4 = client.post("/api/v1/tasks", json={"title": "Done Task", "priority": "Medium"}, headers=headers).json()["id"]
    client.put(f"/api/v1/tasks/{t4}", json={"title": "Done Task", "status": "Completed"}, headers=headers)

    # 1. Test metrics endpoint
    metrics_res = client.get("/api/v1/intelligence/metrics", headers=headers)
    assert metrics_res.status_code == 200
    m_data = metrics_res.json()
    assert m_data["tasks_total"] == 4
    assert m_data["tasks_completed"] == 1
    assert m_data["tasks_pending"] == 3
    assert m_data["completion_rate"] == 25.0

    # 2. Test patterns endpoint
    patterns_res = client.get("/api/v1/intelligence/patterns", headers=headers)
    assert patterns_res.status_code == 200
    patterns = patterns_res.json()
    assert len(patterns) >= 1
    assert any(p["pattern_type"] == "HIGH_PRIORITY_ACCUMULATION" for p in patterns)

def test_insights_ranking_and_dismissal(client):
    token = get_auth_token(client, "insight_tester@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Create task with urgent due date
    client.post(
        "/api/v1/tasks",
        json={"title": "Imminent Launch Deliverable", "priority": "High", "due_date": "2026-11-23T12:00:00Z"},
        headers=headers
    )

    # Retrieve insights
    res_ins = client.get("/api/v1/intelligence/insights", headers=headers)
    assert res_ins.status_code == 200
    insights = res_ins.json()

    if insights:
        first_id = insights[0]["id"]
        # Dismiss insight
        dis_res = client.post(f"/api/v1/intelligence/insights/{first_id}/dismiss", headers=headers)
        assert dis_res.status_code == 200

        # Retrieve again, should not contain dismissed insight
        res_ins_after = client.get("/api/v1/intelligence/insights", headers=headers)
        ids_after = [i["id"] for i in res_ins_after.json()]
        assert first_id not in ids_after

def test_ai_coach_conversational_query(client):
    token = get_auth_token(client, "coach_user@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    coach_res = client.post(
        "/api/v1/intelligence/coach",
        json={"message": "What should I focus on today?"},
        headers=headers
    )
    assert coach_res.status_code == 200
    coach_data = coach_res.json()
    assert "reply" in coach_data
    assert "data_context_summary" in coach_data
    assert len(coach_data["suggested_actions"]) >= 1
