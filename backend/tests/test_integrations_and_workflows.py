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

def get_auth_token(client, email="wf_user@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "WF Tester", "email": email, "password": "password123"},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

def test_available_integrations_catalog(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    res = client.get("/api/v1/integrations/available", headers=headers)
    assert res.status_code == 200
    items = res.json()
    providers = [i["provider"] for i in items]
    assert "google_calendar" in providers
    assert "slack" in providers
    assert "github" in providers

def test_google_calendar_oauth_connect_flow(client):
    token = get_auth_token(client, "gcal_user@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Connect URL
    conn_res = client.get("/api/v1/integrations/google/connect", headers=headers)
    assert conn_res.status_code == 200
    assert "authorization_url" in conn_res.json()
    assert "accounts.google.com" in conn_res.json()["authorization_url"]

    # Callback
    cb_res = client.get("/api/v1/integrations/google/callback?code=mock_code_123&state=test_state", headers=headers)
    assert cb_res.status_code == 200
    assert cb_res.json()["provider"] == "google_calendar"
    assert cb_res.json()["status"] == "connected"

def test_workflow_creation_and_test_execution(client):
    token = get_auth_token(client, "workflow_owner@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Create workflow
    create_res = client.post(
        "/api/v1/workflows",
        json={
            "name": "High Priority Task Alert",
            "trigger_type": "task_created",
            "conditions": [{"field": "priority", "op": "==", "value": "High"}],
            "actions": [{"type": "create_notification", "title": "Urgent Task Detected"}],
            "is_active": True
        },
        headers=headers
    )
    assert create_res.status_code == 201
    wf_id = create_res.json()["id"]

    # Test workflow execution
    test_res = client.post(f"/api/v1/workflows/{wf_id}/test", headers=headers)
    assert test_res.status_code == 200
    assert test_res.json()["status"] == "success"

    # Toggle workflow
    toggle_res = client.patch(f"/api/v1/workflows/{wf_id}/toggle", headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False
