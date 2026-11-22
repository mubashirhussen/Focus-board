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

def get_auth_token(client, email="notif_user@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Notif Tester", "email": email, "password": "password123"}
    )
    return res.json()["access_token"]

def test_notification_flow_and_deduplication(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1. Create a task due today
    task_res = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Client Deliverable", "status": "Todo", "due_date": today_str}
    )
    task_id = task_res.json()["id"]

    # 2. Trigger deadline check
    trigger_res = client.post("/api/v1/notifications/trigger-check", headers=headers)
    assert trigger_res.status_code == 200
    created = trigger_res.json()
    assert len(created) == 1
    assert created[0]["type"] == "TASK_DUE_TODAY"
    notif_id = created[0]["id"]

    # 3. Deduplication: running again today does NOT create duplicate
    dup_res = client.post("/api/v1/notifications/trigger-check", headers=headers)
    assert dup_res.status_code == 200
    assert len(dup_res.json()) == 0

    # 4. Check unread count
    count_res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res.json()["unread_count"] == 1

    # 5. Mark individual notification as read
    read_res = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["read_at"] is not None

    # Unread count is now 0
    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["unread_count"] == 0

    # 6. Notification preferences
    pref_res = client.get("/api/v1/notifications/preferences", headers=headers)
    assert pref_res.status_code == 200
    assert pref_res.json()["enable_in_app"] is True

    update_pref = client.put(
        "/api/v1/notifications/preferences",
        headers=headers,
        json={"daily_reminder_time": "08:30", "timezone": "America/New_York"}
    )
    assert update_pref.status_code == 200
    assert update_pref.json()["daily_reminder_time"] == "08:30"
    assert update_pref.json()["timezone"] == "America/New_York"

    # 7. Delete notification
    del_res = client.delete(f"/api/v1/notifications/{notif_id}", headers=headers)
    assert del_res.status_code == 204
    assert len(client.get("/api/v1/notifications", headers=headers).json()) == 0
