from datetime import datetime, timezone, timedelta, date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
import app.models

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()

def get_auth_token(client, email="user@example.com", username="testuser"):
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": email,
        "username": username,
        "password": "Password123!",
    })
    res = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": email,
        "password": "Password123!",
    }).json()
    return res["access_token"]

def test_task_crud_lifecycle_and_due_dates(client):
    """Test standard task creation, validation, date sanity, lifecycle, archive, and soft deletion."""
    token = get_auth_token(client, "alice@example.com", "alice")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Validation: empty title fails with 422
    invalid_res = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={"title": "   ", "category": "Design"}
    )
    assert invalid_res.status_code == 422

    # 2. Validation: scheduled_end earlier than scheduled_start fails with 422
    now = datetime.now(timezone.utc)
    invalid_dates = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={
            "title": "Invalid Schedule Task",
            "scheduled_start": (now + timedelta(days=2)).isoformat(),
            "scheduled_end": (now + timedelta(days=1)).isoformat()
        }
    )
    assert invalid_dates.status_code == 422

    # 3. Create valid task
    create_res = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={
            "title": "Architect FocusBoard Engine",
            "description": "Core architecture for high-performance SaaS engine",
            "category": "Architecture",
            "status": "Todo",
            "priority": "High",
            "due_date": "2026-12-01",
            "labels": ["backend", "core", "v2"],
            "estimated_duration_minutes": 120
        }
    )
    assert create_res.status_code == 201
    task_data = create_res.json()
    task_id = task_data["id"]
    assert task_data["title"] == "Architect FocusBoard Engine"
    assert task_data["priority"] == "High"
    assert task_data["labels"] == ["backend", "core", "v2"]
    assert task_data["is_archived"] is False
    assert task_data["completed_at"] is None

    # 4. Read single task
    get_res = client.get(f"{settings.API_V1_STR}/tasks/{task_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # 5. Update task metadata and priority
    update_res = client.patch(
        f"{settings.API_V1_STR}/tasks/{task_id}",
        headers=headers,
        json={"title": "Architect FocusBoard Engine v2", "actual_minutes": 45}
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Architect FocusBoard Engine v2"
    assert update_res.json()["actual_minutes"] == 45

    # 6. Status lifecycle transition via PATCH /tasks/{id}/status
    status_res = client.patch(
        f"{settings.API_V1_STR}/tasks/{task_id}/status",
        headers=headers,
        json={"status": "Completed"}
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "Completed"
    assert status_res.json()["completed_at"] is not None
    assert status_res.json()["progress_percent"] == 100.0

    # 7. Move status back to In Progress -> completed_at clears
    reopen_res = client.patch(
        f"{settings.API_V1_STR}/tasks/{task_id}/status",
        headers=headers,
        json={"status": "In Progress"}
    )
    assert reopen_res.status_code == 200
    assert reopen_res.json()["completed_at"] is None

    # 8. Archive and restore
    arc_res = client.post(f"{settings.API_V1_STR}/tasks/{task_id}/archive", headers=headers)
    assert arc_res.status_code == 200
    assert arc_res.json()["is_archived"] is True

    # When archived, it should not appear in default task list
    list_active = client.get(f"{settings.API_V1_STR}/tasks", headers=headers)
    assert len(list_active.json()) == 0

    # Query with is_archived=true -> appears
    list_archived = client.get(f"{settings.API_V1_STR}/tasks?is_archived=true", headers=headers)
    assert len(list_archived.json()) == 1

    # Restore task
    res_res = client.post(f"{settings.API_V1_STR}/tasks/{task_id}/restore", headers=headers)
    assert res_res.status_code == 200
    assert res_res.json()["is_archived"] is False

    # 9. Soft delete task
    del_res = client.delete(f"{settings.API_V1_STR}/tasks/{task_id}", headers=headers)
    assert del_res.status_code == 204

    # Direct retrieval returns 404
    after_del = client.get(f"{settings.API_V1_STR}/tasks/{task_id}", headers=headers)
    assert after_del.status_code == 404

    # List query returns 0 tasks
    final_list = client.get(f"{settings.API_V1_STR}/tasks", headers=headers)
    assert len(final_list.json()) == 0

def test_subtasks_hierarchy_and_progress_rollup(client):
    """Test parent-child subtasks hierarchy and automated progress percentage roll-up."""
    token = get_auth_token(client, "bob@example.com", "bob")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create parent task
    parent_res = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={"title": "Launch Mobile App MVP", "category": "Product", "status": "Todo"}
    )
    assert parent_res.status_code == 201
    parent_id = parent_res.json()["id"]

    # 2. Add 3 subtasks
    s1 = client.post(
        f"{settings.API_V1_STR}/tasks/{parent_id}/subtasks",
        headers=headers,
        json={"title": "Setup React Native scaffold", "category": "Development"}
    ).json()
    s2 = client.post(
        f"{settings.API_V1_STR}/tasks/{parent_id}/subtasks",
        headers=headers,
        json={"title": "Implement Offline Sync", "category": "Development"}
    ).json()
    s3 = client.post(
        f"{settings.API_V1_STR}/tasks/{parent_id}/subtasks",
        headers=headers,
        json={"title": "App Store Assets & Release Build", "category": "Deployment"}
    ).json()

    # 3. Retrieve subtasks
    subs_res = client.get(f"{settings.API_V1_STR}/tasks/{parent_id}/subtasks", headers=headers)
    assert subs_res.status_code == 200
    sub_list = subs_res.json()
    assert len(sub_list) == 3

    # Check parent task subtask count and initial progress
    p_check = client.get(f"{settings.API_V1_STR}/tasks/{parent_id}", headers=headers).json()
    assert p_check["subtask_count"] == 3
    assert p_check["completed_subtask_count"] == 0
    assert p_check["progress_percent"] == 0.0

    # 4. Complete subtask 1 -> progress = 33.3%
    client.patch(
        f"{settings.API_V1_STR}/tasks/{s1['id']}/status",
        headers=headers,
        json={"status": "Completed"}
    )
    p_check = client.get(f"{settings.API_V1_STR}/tasks/{parent_id}", headers=headers).json()
    assert p_check["completed_subtask_count"] == 1
    assert p_check["progress_percent"] == 33.3

    # 5. Complete subtask 2 -> progress = 66.7%
    client.patch(
        f"{settings.API_V1_STR}/tasks/{s2['id']}/status",
        headers=headers,
        json={"status": "Completed"}
    )
    p_check = client.get(f"{settings.API_V1_STR}/tasks/{parent_id}", headers=headers).json()
    assert p_check["completed_subtask_count"] == 2
    assert p_check["progress_percent"] == 66.7

    # 6. Complete subtask 3 -> progress = 100.0% & parent status auto-completes!
    client.patch(
        f"{settings.API_V1_STR}/tasks/{s3['id']}/status",
        headers=headers,
        json={"status": "Completed"}
    )
    p_check = client.get(f"{settings.API_V1_STR}/tasks/{parent_id}", headers=headers).json()
    assert p_check["completed_subtask_count"] == 3
    assert p_check["progress_percent"] == 100.0
    assert p_check["status"] == "Completed"
    assert p_check["completed_at"] is not None

    # 7. Re-open subtask 1 -> parent status moves to In Progress and completed_at cleared
    client.patch(
        f"{settings.API_V1_STR}/tasks/{s1['id']}/status",
        headers=headers,
        json={"status": "In Progress"}
    )
    p_check = client.get(f"{settings.API_V1_STR}/tasks/{parent_id}", headers=headers).json()
    assert p_check["completed_subtask_count"] == 2
    assert p_check["progress_percent"] == 66.7
    assert p_check["status"] == "In Progress"
    assert p_check["completed_at"] is None

def test_task_dependencies_and_cycle_prevention(client):
    """Test dependency linking, cycle detection algorithm, and self-dependency prevention."""
    token = get_auth_token(client, "carol@example.com", "carol")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Tasks A, B, C
    task_a = client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Task A: Database Setup"}).json()["id"]
    task_b = client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Task B: API Development"}).json()["id"]
    task_c = client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Task C: Frontend Integration"}).json()["id"]

    # 2. Self-dependency fails with 400
    self_dep = client.post(
        f"{settings.API_V1_STR}/tasks/{task_a}/dependencies",
        headers=headers,
        json={"depends_on_task_id": task_a}
    )
    assert self_dep.status_code == 400

    # 3. Add legal dependency: B depends on A
    dep_b_a = client.post(
        f"{settings.API_V1_STR}/tasks/{task_b}/dependencies",
        headers=headers,
        json={"depends_on_task_id": task_a, "dependency_type": "FINISH_TO_START"}
    )
    assert dep_b_a.status_code == 201

    # 4. Add legal dependency: C depends on B
    dep_c_b = client.post(
        f"{settings.API_V1_STR}/tasks/{task_c}/dependencies",
        headers=headers,
        json={"depends_on_task_id": task_b, "dependency_type": "FINISH_TO_START"}
    )
    assert dep_c_b.status_code == 201
    dep_c_b_id = dep_c_b.json()["id"]

    # 5. Cycle prevention: A depends on C (Cycle: A -> C -> B -> A) must fail with 400!
    cycle_res = client.post(
        f"{settings.API_V1_STR}/tasks/{task_a}/dependencies",
        headers=headers,
        json={"depends_on_task_id": task_c}
    )
    assert cycle_res.status_code == 400
    assert "circular dependency" in cycle_res.json()["detail"].lower()

    # 6. Retrieve dependencies of C
    deps_res = client.get(f"{settings.API_V1_STR}/tasks/{task_c}/dependencies", headers=headers)
    assert deps_res.status_code == 200
    assert len(deps_res.json()) == 1
    assert deps_res.json()[0]["depends_on_task_id"] == task_b

    # 7. Delete dependency
    del_dep = client.delete(f"{settings.API_V1_STR}/tasks/{task_c}/dependencies/{dep_c_b_id}", headers=headers)
    assert del_dep.status_code == 204
    assert len(client.get(f"{settings.API_V1_STR}/tasks/{task_c}/dependencies", headers=headers).json()) == 0

def test_bulk_operations_and_reordering(client):
    """Test bulk batch updates (status, priority, delete) and task reordering."""
    token = get_auth_token(client, "dave@example.com", "dave")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create 4 tasks
    t_ids = []
    for i in range(4):
        t = client.post(
            f"{settings.API_V1_STR}/tasks",
            headers=headers,
            json={"title": f"Batch Task {i+1}", "status": "Todo", "priority": "Low", "sort_order": i}
        ).json()["id"]
        t_ids.append(t)

    # 2. Bulk status update to 'Completed'
    bulk_status = client.post(
        f"{settings.API_V1_STR}/tasks/bulk",
        headers=headers,
        json={"task_ids": t_ids, "action": "update_status", "status": "Completed"}
    )
    assert bulk_status.status_code == 200
    assert bulk_status.json()["affected_count"] == 4

    # Verify all are completed
    tasks_after_status = client.get(f"{settings.API_V1_STR}/tasks", headers=headers).json()
    assert all(t["status"] == "Completed" for t in tasks_after_status)

    # 3. Bulk priority update to 'Critical'
    bulk_prio = client.post(
        f"{settings.API_V1_STR}/tasks/bulk",
        headers=headers,
        json={"task_ids": [t_ids[0], t_ids[1]], "action": "update_priority", "priority": "Critical"}
    )
    assert bulk_prio.status_code == 200
    assert bulk_prio.json()["affected_count"] == 2

    # 4. Reorder tasks
    reorder_res = client.post(
        f"{settings.API_V1_STR}/tasks/reorder",
        headers=headers,
        json={"items": [{"id": t_ids[3], "sort_order": 0}, {"id": t_ids[0], "sort_order": 1}]}
    )
    assert reorder_res.status_code == 200

    # 5. Bulk delete 2 tasks
    bulk_del = client.post(
        f"{settings.API_V1_STR}/tasks/bulk",
        headers=headers,
        json={"task_ids": [t_ids[0], t_ids[1]], "action": "delete"}
    )
    assert bulk_del.status_code == 200
    assert bulk_del.json()["affected_count"] == 2

    # Active tasks remaining should be 2
    remaining = client.get(f"{settings.API_V1_STR}/tasks", headers=headers).json()
    assert len(remaining) == 2

def test_search_filters_and_summary_metrics(client):
    """Test text search, multi-criteria filters, overdue detection, and summary dashboard aggregation."""
    token = get_auth_token(client, "eve@example.com", "eve")
    headers = {"Authorization": f"Bearer {token}"}

    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=2)).isoformat()
    future_str = (date.today() + timedelta(days=5)).isoformat()

    # Create distinct tasks
    client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={"title": "Design UI Component Library", "category": "Design", "status": "Completed", "priority": "High", "due_date": yesterday_str}
    )
    client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={"title": "Fix Critical Production Outage", "category": "Infrastructure", "status": "In Progress", "priority": "Critical", "due_date": today_str}
    )
    client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={"title": "Write Automated Unit Tests", "category": "QA", "status": "Todo", "priority": "Medium", "due_date": yesterday_str}
    ) # Overdue!
    client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={"title": "Deploy to Staging Environment", "category": "Deployment", "status": "Todo", "priority": "Low", "due_date": future_str}
    )

    # 1. Search endpoint
    search_res = client.get(f"{settings.API_V1_STR}/tasks/search?q=Production", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert "Production Outage" in search_res.json()[0]["title"]

    # 2. Filter by status
    todo_tasks = client.get(f"{settings.API_V1_STR}/tasks?status=Todo", headers=headers).json()
    assert len(todo_tasks) == 2

    # 3. Filter by priority
    crit_tasks = client.get(f"{settings.API_V1_STR}/tasks?priority=Critical", headers=headers).json()
    assert len(crit_tasks) == 1

    # 4. Filter by overdue
    overdue_tasks = client.get(f"{settings.API_V1_STR}/tasks?is_overdue=true", headers=headers).json()
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0]["title"] == "Write Automated Unit Tests"

    # 5. Summary metrics
    summary_res = client.get(f"{settings.API_V1_STR}/tasks/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total"] == 4
    assert summary["completed"] == 1
    assert summary["in_progress"] == 1
    assert summary["todo"] == 2
    assert summary["overdue"] == 1
    assert summary["due_today"] == 1
    assert summary["completion_rate"] == 25.0
    assert summary["by_priority"]["High"] == 1
    assert summary["by_priority"]["Critical"] == 1

def test_multi_tenant_isolation_and_workspace_sharing(client):
    """Test tenant boundary enforcement, 404 IDOR shielding, and workspace shared task collaboration."""
    token1 = get_auth_token(client, "org_user1@example.com", "orguser1")
    token2 = get_auth_token(client, "org_user2@example.com", "orguser2")
    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # 1. User 1 creates private personal task
    t1 = client.post(f"{settings.API_V1_STR}/tasks", headers=h1, json={"title": "Secret Strategy 2027"}).json()["id"]

    # 2. User 2 cannot access, update, delete or depend on t1 (returns 404)
    assert client.get(f"{settings.API_V1_STR}/tasks/{t1}", headers=h2).status_code == 404
    assert client.patch(f"{settings.API_V1_STR}/tasks/{t1}", headers=h2, json={"title": "Hacked"}).status_code == 404
    assert client.delete(f"{settings.API_V1_STR}/tasks/{t1}", headers=h2).status_code == 404
    assert client.post(f"{settings.API_V1_STR}/tasks/{t1}/subtasks", headers=h2, json={"title": "Rogue"}).status_code == 404

    # 3. User 1 creates a workspace and invites User 2
    ws_res = client.post(f"{settings.API_V1_STR}/workspaces", headers=h1, json={"name": "Engineering Team"})
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    inv_res = client.post(
        f"{settings.API_V1_STR}/workspaces/{ws_id}/invitations",
        headers=h1,
        json={"email": "org_user2@example.com", "role": "MEMBER"}
    )
    assert inv_res.status_code == 201
    token_str = inv_res.json()["token"]

    # User 2 accepts invitation
    acc_res = client.post(f"{settings.API_V1_STR}/workspaces/invitations/{token_str}/accept", headers=h2)
    assert acc_res.status_code == 200

    # 4. User 1 creates a task inside the shared workspace
    shared_task = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=h1,
        json={"title": "Shared Sprint Milestone", "workspace_id": ws_id}
    ).json()["id"]

    # 5. User 2 can now view, update, and collaborate on this shared task!
    user2_get = client.get(f"{settings.API_V1_STR}/tasks/{shared_task}", headers=h2)
    assert user2_get.status_code == 200
    assert user2_get.json()["title"] == "Shared Sprint Milestone"

    user2_update = client.patch(
        f"{settings.API_V1_STR}/tasks/{shared_task}/status",
        headers=h2,
        json={"status": "Completed"}
    )
    assert user2_update.status_code == 200
    assert user2_update.json()["status"] == "Completed"
