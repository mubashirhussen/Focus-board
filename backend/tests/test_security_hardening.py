import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.core.rate_limiter import RateLimiterMiddleware

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def client():
    RateLimiterMiddleware.reset()
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

def test_security_headers_present(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in res.headers
    assert "Content-Security-Policy" in res.headers

def test_audit_logs_recorded_on_auth_flow(client):
    headers = {"X-Test-Bypass-Rate-Limit": "true"}
    # Register
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Audit User", "email": "audit@example.com", "password": "password123"},
        headers=headers
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}", **headers}

    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_res.status_code == 200

    # Retrieve audit logs
    audit_res = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    event_types = [l["event_type"] for l in logs]
    assert "AUTH_REGISTER" in event_types
    assert "AUTH_LOGOUT" in event_types
    assert "AUDIT_LOG_VIEW" in event_types

def test_user_data_export_and_account_deletion(client):
    headers = {"X-Test-Bypass-Rate-Limit": "true"}
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Privacy User", "email": "privacy@example.com", "password": "password123"},
        headers=headers
    )
    token = reg_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}", **headers}

    # Create a task
    client.post("/api/v1/tasks", json={"title": "Personal Task for GDPR", "category": "Personal"}, headers=auth_headers)

    # Export user data
    export_res = client.get("/api/v1/auth/export-data", headers=auth_headers)
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["user_profile"]["email"] == "privacy@example.com"
    assert len(export_data["tasks"]) == 1
    assert export_data["tasks"][0]["title"] == "Personal Task for GDPR"

    # Delete account
    del_res = client.delete("/api/v1/auth/me", headers=auth_headers)
    assert del_res.status_code == 200

    # Attempting to query with same token should now fail (user no longer exists)
    fail_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert fail_res.status_code == 401

def test_rate_limiting_enforced(client):
    # Enforce rate limit via X-Test-Enforce-Rate-Limit header (limit 5 requests)
    status_codes = []
    for i in range(10):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": f"fake{i}@test.com", "password": "badpassword"},
            headers={"X-Test-Enforce-Rate-Limit": "true"}
        )
        status_codes.append(res.status_code)

    assert 429 in status_codes
