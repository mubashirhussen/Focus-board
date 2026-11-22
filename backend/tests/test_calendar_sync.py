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

def get_auth_token(client, email="cal_tester@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Calendar Tester", "email": email, "password": "password123"},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

def test_task_scheduling_and_calendar_events(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Create task
    task_res = client.post("/api/v1/tasks", json={"title": "Client Architecture Review"}, headers=headers)
    task_id = task_res.json()["id"]

    # 2. Schedule task
    now = datetime.now(timezone.utc).replace(microsecond=0)
    sched_start = (now + timedelta(days=1)).replace(hour=14, minute=0, second=0)

    sched_res = client.post(
        "/api/v1/calendar/schedule-task",
        json={
            "task_id": task_id,
            "scheduled_start": sched_start.isoformat(),
            "estimated_duration_minutes": 45
        },
        headers=headers
    )
    assert sched_res.status_code == 200
    assert sched_res.json()["title"] == "Client Architecture Review"

    # 3. Retrieve calendar events
    events_res = client.get("/api/v1/calendar/events", headers=headers)
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 1
    assert any(e["task_id"] == str(task_id) for e in events)

def test_calendar_conflict_detection_and_sync(client):
    token = get_auth_token(client, "conflict_user@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Create two tasks and schedule them at the exact same overlapping time
    t1 = client.post("/api/v1/tasks", json={"title": "Sprint Planning"}, headers=headers).json()["id"]
    t2 = client.post("/api/v1/tasks", json={"title": "Team 1-on-1"}, headers=headers).json()["id"]

    now = datetime.now(timezone.utc).replace(microsecond=0)
    conflict_time = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0)

    client.post(
        "/api/v1/calendar/schedule-task",
        json={"task_id": t1, "scheduled_start": conflict_time.isoformat(), "estimated_duration_minutes": 60},
        headers=headers
    )
    client.post(
        "/api/v1/calendar/schedule-task",
        json={"task_id": t2, "scheduled_start": (conflict_time + timedelta(minutes=15)).isoformat(), "estimated_duration_minutes": 30},
        headers=headers
    )

    # Check conflict detection
    conflicts_res = client.get("/api/v1/calendar/conflicts", headers=headers)
    assert conflicts_res.status_code == 200
    conflicts = conflicts_res.json()
    assert len(conflicts) >= 1
    assert any(c["conflict_type"] == "OVERLAP" for c in conflicts)

    # Trigger calendar sync
    sync_res = client.post("/api/v1/calendar/sync", headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "SUCCESS"
    assert sync_res.json()["tasks_synced"] >= 2
