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

def get_auth_token(client, email="searcher@example.com", name="Searcher"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "securepassword123"},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

def test_search_unauthenticated(client):
    res = client.get("/api/v1/search?q=test")
    assert res.status_code == 401

def test_search_tasks_and_facets(client):
    token = get_auth_token(client, "alice@example.com", "Alice")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Create tasks
    client.post(
        "/api/v1/tasks",
        json={"title": "Design System Documentation", "description": "Write design guidelines", "category": "Design", "priority": "High"},
        headers=headers
    )
    client.post(
        "/api/v1/tasks",
        json={"title": "Backend Optimization", "description": "Profile API routes", "category": "Development", "priority": "Medium"},
        headers=headers
    )

    # Search with keyword "Design"
    res = client.get("/api/v1/search?q=Design", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["results"][0]["title"] == "Design System Documentation"
    assert data["results"][0]["type"] == "TASK"
    assert "facets" in data
    assert data["facets"]["by_type"]["TASK"] >= 1

def test_search_multi_tenant_isolation(client):
    token1 = get_auth_token(client, "user1@example.com", "User 1")
    token2 = get_auth_token(client, "user2@example.com", "User 2")
    headers1 = {"Authorization": f"Bearer {token1}", "X-Test-Bypass-Rate-Limit": "true"}
    headers2 = {"Authorization": f"Bearer {token2}", "X-Test-Bypass-Rate-Limit": "true"}

    # User 1 creates confidential task
    client.post(
        "/api/v1/tasks",
        json={"title": "Secret Financial Audit", "description": "Confidential numbers", "category": "Finance"},
        headers=headers1
    )

    # User 2 searches for "Financial"
    res2 = client.get("/api/v1/search?q=Financial", headers=headers2)
    assert res2.status_code == 200
    assert res2.json()["total"] == 0

    # User 1 searches for "Financial"
    res1 = client.get("/api/v1/search?q=Financial", headers=headers1)
    assert res1.status_code == 200
    assert res1.json()["total"] == 1
    assert res1.json()["results"][0]["title"] == "Secret Financial Audit"

def test_search_workspaces_and_projects(client):
    token = get_auth_token(client, "collab@example.com", "Collab User")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Create workspace
    ws_res = client.post("/api/v1/workspaces", json={"name": "Alpha Team Workspace", "description": "Core product team"}, headers=headers)
    ws_id = ws_res.json()["id"]

    # Create project in workspace
    client.post(f"/api/v1/workspaces/{ws_id}/projects", json={"name": "Mobile Redesign", "description": "V2 Mobile app"}, headers=headers)

    # Search for "Alpha"
    res_ws = client.get("/api/v1/search?q=Alpha&type=WORKSPACE", headers=headers)
    assert res_ws.status_code == 200
    assert res_ws.json()["total"] == 1
    assert res_ws.json()["results"][0]["title"] == "Alpha Team Workspace"

    # Search for "Redesign"
    res_prj = client.get("/api/v1/search?q=Redesign&type=PROJECT", headers=headers)
    assert res_prj.status_code == 200
    assert res_prj.json()["total"] == 1
    assert res_prj.json()["results"][0]["title"] == "Mobile Redesign"
