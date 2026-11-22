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

def get_token(client, email, name):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "securepassword123"}
    )
    return res.json()["access_token"]

def test_tenant_task_isolation(client):
    """Verify that User A cannot access, edit, or delete User B's tasks."""
    token_a = get_token(client, "alice_sec@example.com", "Alice Sec")
    token_b = get_token(client, "bob_sec@example.com", "Bob Sec")
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # Alice creates a confidential task
    t_res = client.post(
        "/api/v1/tasks",
        json={"title": "Alice Confidential Strategy", "priority": "High", "status": "Todo"},
        headers=h_a
    )
    assert t_res.status_code == 201
    task_id = t_res.json()["id"]

    # Bob tries to access Alice's task directly by ID -> must fail with 404 (not found / isolated)
    get_res = client.get(f"/api/v1/tasks/{task_id}", headers=h_b)
    assert get_res.status_code == 404

    # Bob tries to modify Alice's task -> must fail with 404
    put_res = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Hacked Title", "status": "Completed"},
        headers=h_b
    )
    assert put_res.status_code == 404

    # Bob tries to delete Alice's task -> must fail with 404
    del_res = client.delete(f"/api/v1/tasks/{task_id}", headers=h_b)
    assert del_res.status_code == 404

    # Confirm Alice's task is still intact
    verify_res = client.get(f"/api/v1/tasks/{task_id}", headers=h_a)
    assert verify_res.status_code == 200
    assert verify_res.json()["title"] == "Alice Confidential Strategy"

def test_tenant_workspace_and_project_isolation(client):
    """Verify that User B cannot access User A's workspace or its projects."""
    token_a = get_token(client, "tenant_a@example.com", "Tenant A")
    token_b = get_token(client, "tenant_b@example.com", "Tenant B")
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A creates an enterprise workspace
    ws_res = client.post(
        "/api/v1/workspaces",
        json={"name": "Org A Workspace", "description": "Private Org A"},
        headers=h_a
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # Tenant B lists workspaces -> Org A workspace must NOT appear
    ws_list_b = client.get("/api/v1/workspaces", headers=h_b)
    assert ws_list_b.status_code == 200
    assert not any(ws["id"] == ws_id for ws in ws_list_b.json())

    # Tenant B tries to create a project in Org A workspace -> must fail with 403 or 404
    proj_res = client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        json={"name": "Unauthorized Project", "description": "Breach Attempt"},
        headers=h_b
    )
    assert proj_res.status_code in [403, 404]

def test_tenant_search_and_analytics_isolation(client):
    """Verify that search and analytics queries are strictly scoped to the requesting tenant."""
    token_a = get_token(client, "search_a@example.com", "Search A")
    token_b = get_token(client, "search_b@example.com", "Search B")
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a task with a distinct codeword
    client.post(
        "/api/v1/tasks",
        json={"title": "Project Nightingale Secret Code", "priority": "High", "status": "Todo"},
        headers=h_a
    )

    # User A searches for the codeword -> finds 1 result
    search_a = client.get("/api/v1/search?q=Nightingale", headers=h_a)
    assert search_a.status_code == 200
    assert len(search_a.json()["results"]) == 1

    # User B searches for the exact same codeword -> returns 0 results
    search_b = client.get("/api/v1/search?q=Nightingale", headers=h_b)
    assert search_b.status_code == 200
    assert len(search_b.json()["results"]) == 0

    # User B checks analytics -> total tasks must be 0
    analytics_b = client.get("/api/v1/analytics/summary", headers=h_b)
    assert analytics_b.status_code == 200
    assert analytics_b.json()["total"] == 0

def test_unauthenticated_request_rejection(client):
    """Verify that protected API endpoints reject missing or malformed tokens with 401."""
    endpoints = [
        ("GET", "/api/v1/tasks"),
        ("POST", "/api/v1/tasks"),
        ("GET", "/api/v1/workspaces"),
        ("GET", "/api/v1/analytics/summary"),
        ("GET", "/api/v1/intelligence/metrics"),
        ("GET", "/api/v1/enterprise/policies"),
        ("GET", "/api/v1/billing/subscription"),
    ]

    for method, path in endpoints:
        # Request with no header
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        assert res.status_code in [401, 403], f"Endpoint {path} did not reject unauthenticated request"

        # Request with bogus token
        bogus_header = {"Authorization": "Bearer invalid_tampered_jwt_token"}
        if method == "GET":
            res_bogus = client.get(path, headers=bogus_header)
        else:
            res_bogus = client.post(path, json={}, headers=bogus_header)
        assert res_bogus.status_code in [401, 403], f"Endpoint {path} accepted invalid JWT token"
