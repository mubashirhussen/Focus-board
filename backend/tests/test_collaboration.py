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

def get_auth_token(client, email="user@example.com", name="User"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "password123"}
    )
    return res.json()["access_token"]

def test_collaboration_workspace_and_permissions(client):
    # Two users: Alice (Owner) and Bob (Invitee)
    token_alice = get_auth_token(client, "alice@example.com", "Alice")
    token_bob = get_auth_token(client, "bob@example.com", "Bob")

    h_alice = {"Authorization": f"Bearer {token_alice}"}
    h_bob = {"Authorization": f"Bearer {token_bob}"}

    # 1. Alice creates workspace
    ws_res = client.post(
        "/api/v1/workspaces",
        headers=h_alice,
        json={"name": "Core Product Team", "description": "FocusBoard core engineering"}
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # 2. Bob tries to access workspace -> 403 Forbidden
    unauth_get = client.get(f"/api/v1/workspaces/{ws_id}", headers=h_bob)
    assert unauth_get.status_code == 403

    # 3. Alice invites Bob
    inv_res = client.post(
        f"/api/v1/workspaces/{ws_id}/invitations",
        headers=h_alice,
        json={"email": "bob@example.com", "role": "MEMBER"}
    )
    assert inv_res.status_code == 201
    token = inv_res.json()["token"]

    # 4. Bob accepts invitation
    accept_res = client.post(f"/api/v1/workspaces/invitations/{token}/accept", headers=h_bob)
    assert accept_res.status_code == 200

    # Bob can now view the workspace
    bob_get = client.get(f"/api/v1/workspaces/{ws_id}", headers=h_bob)
    assert bob_get.status_code == 200
    assert bob_get.json()["name"] == "Core Product Team"

    # 5. Alice creates a project
    proj_res = client.post(
        f"/api/v1/workspaces/{ws_id}/projects",
        headers=h_alice,
        json={"name": "Mobile Redesign", "description": "Phase 16 UX sprint"}
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 6. Alice creates shared task in workspace
    task_res = client.post(
        f"/api/v1/workspaces/{ws_id}/tasks?project_id={proj_id}",
        headers=h_alice,
        json={"title": "Figma Auto-Layout Audit", "priority": "High", "status": "Todo"}
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 7. Alice assigns task to Bob
    # Fetch Bob's user id
    bob_me = client.get("/api/v1/auth/me", headers=h_bob).json()
    bob_id = bob_me["id"]

    assign_res = client.patch(
        f"/api/v1/workspaces/{ws_id}/tasks/{task_id}/assign",
        headers=h_alice,
        json={"assignee_id": bob_id}
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assignee_id"] == bob_id

    # 8. Bob comments on the task
    comm_res = client.post(
        f"/api/v1/workspaces/{ws_id}/tasks/{task_id}/comments",
        headers=h_bob,
        json={"content": "Started reviewing mobile frames 15:2 and 15:30."}
    )
    assert comm_res.status_code == 201
    assert "mobile frames" in comm_res.json()["content"]

    # 9. Check Activity Feed
    act_res = client.get(f"/api/v1/workspaces/{ws_id}/activities", headers=h_alice)
    assert act_res.status_code == 200
    activities = act_res.json()
    assert len(activities) >= 4  # Workspace, Member, Project, Task, Comment

    # 10. Check Team Analytics
    analytics_res = client.get(f"/api/v1/workspaces/{ws_id}/analytics", headers=h_alice)
    assert analytics_res.status_code == 200
    stats = analytics_res.json()
    assert stats["total_shared_tasks"] == 1
    assert stats["members_count"] == 2
    assert stats["active_projects_count"] == 1
