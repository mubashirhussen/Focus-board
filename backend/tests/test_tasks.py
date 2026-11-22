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
        json={"name": name, "email": email, "password": "securepassword123"}
    )
    return res.json()["access_token"]

def test_task_crud_and_user_isolation(client):
    # Create two users
    token1 = get_auth_token(client, "user1@example.com", "User 1")
    token2 = get_auth_token(client, "user2@example.com", "User 2")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates a task
    create_res = client.post(
        "/api/v1/tasks",
        headers=headers1,
        json={"title": "Design System Review", "category": "Design", "status": "Todo", "priority": "High"}
    )
    assert create_res.status_code == 201
    task1 = create_res.json()
    task1_id = task1["id"]
    assert task1["title"] == "Design System Review"
    assert task1["completed_at"] is None

    # User 1 lists tasks -> sees task1
    list1 = client.get("/api/v1/tasks", headers=headers1)
    assert len(list1.json()) == 1

    # User 2 lists tasks -> sees 0 tasks (isolation!)
    list2 = client.get("/api/v1/tasks", headers=headers2)
    assert len(list2.json()) == 0

    # User 2 tries to access User 1's task directly -> 404 Not Found
    unauthorized_get = client.get(f"/api/v1/tasks/{task1_id}", headers=headers2)
    assert unauthorized_get.status_code == 404

    # User 2 tries to update User 1's task -> 404 Not Found
    unauthorized_update = client.put(f"/api/v1/tasks/{task1_id}", headers=headers2, json={"title": "Hacked Title"})
    assert unauthorized_update.status_code == 404

    # User 2 tries to delete User 1's task -> 404 Not Found
    unauthorized_delete = client.delete(f"/api/v1/tasks/{task1_id}", headers=headers2)
    assert unauthorized_delete.status_code == 404

    # User 1 updates status to Completed -> completed_at timestamp is populated
    update_res = client.put(f"/api/v1/tasks/{task1_id}", headers=headers1, json={"status": "Completed"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Completed"
    assert update_res.json()["completed_at"] is not None

    # User 1 moves back to In Progress -> completed_at is cleared
    reopen_res = client.put(f"/api/v1/tasks/{task1_id}", headers=headers1, json={"status": "In Progress"})
    assert reopen_res.status_code == 200
    assert reopen_res.json()["completed_at"] is None

    # User 1 deletes task
    del_res = client.delete(f"/api/v1/tasks/{task1_id}", headers=headers1)
    assert del_res.status_code == 204
    assert len(client.get("/api/v1/tasks", headers=headers1).json()) == 0
