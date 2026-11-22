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


def test_board_crud_lifecycle_and_default_columns(client):
    """Test board creation, auto-generation of 4 Kanban columns, settings, archive, and deletion."""
    token = get_auth_token(client, "alice_board@example.com", "aliceboard")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Validation: empty name fails with 422
    inv_res = client.post(f"{settings.API_V1_STR}/boards", headers=headers, json={"name": "   "})
    assert inv_res.status_code == 422

    # 2. Create valid board
    create_res = client.post(
        f"{settings.API_V1_STR}/boards",
        headers=headers,
        json={
            "name": "Core Engineering Kanban",
            "description": "Main task board for sprint cycles",
            "board_type": "kanban",
            "visibility": "workspace",
            "settings": {"show_wip": True, "card_size": "compact"}
        }
    )
    assert create_res.status_code == 201
    board_data = create_res.json()
    board_id = board_data["id"]
    assert board_data["name"] == "Core Engineering Kanban"
    assert board_data["settings"] == {"show_wip": True, "card_size": "compact"}
    assert len(board_data["columns"]) == 4  # Auto-generated default columns

    # Verify default columns
    col_names = [c["name"] for c in board_data["columns"]]
    assert col_names == ["To Do", "In Progress", "In Review", "Done"]

    # 3. Retrieve board detail
    get_res = client.get(f"{settings.API_V1_STR}/boards/{board_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == board_id

    # 4. Update board settings and metadata
    patch_res = client.patch(
        f"{settings.API_V1_STR}/boards/{board_id}",
        headers=headers,
        json={"name": "Core Engineering Kanban v2", "settings": {"show_wip": False}}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Core Engineering Kanban v2"
    assert patch_res.json()["settings"]["show_wip"] is False

    # 5. Archive and restore
    arc_res = client.post(f"{settings.API_V1_STR}/boards/{board_id}/archive", headers=headers)
    assert arc_res.status_code == 200
    assert arc_res.json()["is_archived"] is True

    # Active boards list excludes archived
    active_boards = client.get(f"{settings.API_V1_STR}/boards", headers=headers).json()
    assert not any(b["id"] == board_id for b in active_boards)

    # Restore board
    res_res = client.post(f"{settings.API_V1_STR}/boards/{board_id}/restore", headers=headers)
    assert res_res.status_code == 200
    assert res_res.json()["is_archived"] is False

    # 6. Delete board
    del_res = client.delete(f"{settings.API_V1_STR}/boards/{board_id}", headers=headers)
    assert del_res.status_code == 204
    assert client.get(f"{settings.API_V1_STR}/boards/{board_id}", headers=headers).status_code == 404


def test_board_column_management_and_task_reassignment(client):
    """Test column CRUD, reordering, WIP limits, and task reassignment on column deletion."""
    token = get_auth_token(client, "bob_col@example.com", "bobcol")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create board
    board_res = client.post(
        f"{settings.API_V1_STR}/boards",
        headers=headers,
        json={"name": "QA Pipeline Board"}
    )
    board_id = board_res.json()["id"]
    cols = board_res.json()["columns"]
    todo_col = next(c for c in cols if c["status_value"] == "Todo")
    in_prog_col = next(c for c in cols if c["status_value"] == "In Progress")

    # 2. Add custom column
    new_col_res = client.post(
        f"{settings.API_V1_STR}/boards/{board_id}/columns",
        headers=headers,
        json={
            "name": "Staging Verification",
            "status_value": "Staging",
            "color": "#ec4899",
            "wip_limit": 3
        }
    )
    assert new_col_res.status_code == 201
    new_col = new_col_res.json()
    assert new_col["name"] == "Staging Verification"
    assert new_col["wip_limit"] == 3

    # 3. Reorder columns
    reorder_res = client.post(
        f"{settings.API_V1_STR}/boards/{board_id}/columns/reorder",
        headers=headers,
        json={"items": [{"id": new_col["id"], "position": 0}, {"id": todo_col["id"], "position": 1}]}
    )
    assert reorder_res.status_code == 200
    updated_cols = reorder_res.json()
    assert updated_cols[0]["id"] == new_col["id"]

    # 4. Create a task in 'Staging' status
    task_res = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=headers,
        json={"title": "Verify OAuth on Staging", "status": "Staging"}
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 5. Delete column with active tasks without target_column_id fails with 400
    del_fail = client.delete(f"{settings.API_V1_STR}/boards/{board_id}/columns/{new_col['id']}", headers=headers)
    assert del_fail.status_code == 400
    assert "reassign" in del_fail.json()["detail"].lower()

    # 6. Delete column with target_column_id remaps tasks to target column
    del_ok = client.delete(
        f"{settings.API_V1_STR}/boards/{board_id}/columns/{new_col['id']}?target_column_id={in_prog_col['id']}",
        headers=headers
    )
    assert del_ok.status_code == 204

    # Verify task was remapped to target column's status
    remapped_task = client.get(f"{settings.API_V1_STR}/tasks/{task_id}", headers=headers).json()
    assert remapped_task["status"] == "In Progress"


def test_kanban_drag_and_drop_movement_and_bulk_move(client):
    """Test task movement between columns, status updating, position updating, and board data payload."""
    token = get_auth_token(client, "carol_kanban@example.com", "carolkanban")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create board
    board = client.post(f"{settings.API_V1_STR}/boards", headers=headers, json={"name": "Sprint 42 Board"}).json()
    board_id = board["id"]
    cols = board["columns"]
    todo_col = next(c for c in cols if c["status_value"] == "Todo")
    in_prog_col = next(c for c in cols if c["status_value"] == "In Progress")
    done_col = next(c for c in cols if c["status_value"] == "Completed")

    # 2. Create tasks
    t1 = client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Build Auth", "status": "Todo"}).json()["id"]
    t2 = client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Build UI", "status": "Todo"}).json()["id"]

    # 3. Move Task 1 to "In Progress" column (Drag-and-Drop)
    move_res = client.patch(
        f"{settings.API_V1_STR}/boards/{board_id}/tasks/{t1}/position",
        headers=headers,
        json={"destination_column_id": in_prog_col["id"], "destination_position": 0}
    )
    assert move_res.status_code == 200
    assert move_res.json()["status"] == "In Progress"
    assert move_res.json()["sort_order"] == 0

    # 4. Move Task 1 to "Done" -> completed_at populated
    done_move = client.patch(
        f"{settings.API_V1_STR}/boards/{board_id}/tasks/{t1}/position",
        headers=headers,
        json={"destination_column_id": done_col["id"], "destination_position": 0}
    )
    assert done_move.status_code == 200
    assert done_move.json()["status"] == "Completed"
    assert done_move.json()["completed_at"] is not None

    # 5. Move Task 1 back to "To Do" -> completed_at cleared
    reopen_move = client.patch(
        f"{settings.API_V1_STR}/boards/{board_id}/tasks/{t1}/position",
        headers=headers,
        json={"destination_column_id": todo_col["id"], "destination_position": 1}
    )
    assert reopen_move.status_code == 200
    assert reopen_move.json()["completed_at"] is None

    # 6. Bulk move tasks to "In Progress"
    bulk_res = client.post(
        f"{settings.API_V1_STR}/boards/{board_id}/tasks/bulk-move",
        headers=headers,
        json={"task_ids": [t1, t2], "destination_column_id": in_prog_col["id"]}
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["moved_count"] == 2

    # 7. Query board data: verify grouped tasks and summary
    data_res = client.get(f"{settings.API_V1_STR}/boards/{board_id}/data", headers=headers)
    assert data_res.status_code == 200
    board_data = data_res.json()
    assert board_data["summary"]["total_tasks"] == 2
    # Column "In Progress" should have 2 tasks
    in_prog_data = next(c for c in board_data["columns"] if c["column"]["status_value"] == "In Progress")
    assert in_prog_data["task_count"] == 2


def test_saved_views_creation_duplication_and_defaults(client):
    """Test saved views CRUD, view types, setting defaults, and view duplication."""
    token = get_auth_token(client, "dave_views@example.com", "daveviews")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create custom views
    v1_res = client.post(
        f"{settings.API_V1_STR}/views",
        headers=headers,
        json={
            "name": "High Priority Bugs",
            "view_type": "list",
            "visibility": "workspace",
            "filters": {"conditions": [{"field": "priority", "operator": "equals", "value": "High"}]},
            "sort_config": [{"field": "due_date", "order": "asc"}]
        }
    )
    assert v1_res.status_code == 201
    v1 = v1_res.json()
    assert v1["view_type"] == "list"
    assert v1["is_default"] is False

    v2_res = client.post(
        f"{settings.API_V1_STR}/views",
        headers=headers,
        json={"name": "Sprint Calendar", "view_type": "calendar", "visibility": "workspace"}
    )
    assert v2_res.status_code == 201
    v2_id = v2_res.json()["id"]

    # 2. Set v1 as default view
    set_def = client.patch(f"{settings.API_V1_STR}/views/{v1['id']}/default", headers=headers)
    assert set_def.status_code == 200
    assert set_def.json()["is_default"] is True

    # 3. Duplicate view
    dup_res = client.post(
        f"{settings.API_V1_STR}/views/{v1['id']}/duplicate",
        headers=headers,
        json={"new_name": "High Priority Bugs (Copy)"}
    )
    assert dup_res.status_code == 201
    dup_view = dup_res.json()
    assert dup_view["id"] != v1["id"]
    assert dup_view["name"] == "High Priority Bugs (Copy)"
    assert dup_view["filters"] == v1["filters"]

    # 4. List views filtered by view_type
    list_cal = client.get(f"{settings.API_V1_STR}/views?view_type=calendar", headers=headers).json()
    assert len(list_cal) == 1
    assert list_cal[0]["id"] == v2_id

    # 5. Delete view
    del_res = client.delete(f"{settings.API_V1_STR}/views/{v2_id}", headers=headers)
    assert del_res.status_code == 204
    assert client.get(f"{settings.API_V1_STR}/views/{v2_id}", headers=headers).status_code == 404


def test_advanced_filters_and_view_data_execution(client):
    """Test filter conditions (AND, OR, contains, equals), saved filters, and view data grouping."""
    token = get_auth_token(client, "eve_filter@example.com", "evefilter")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create diverse tasks
    client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Design Landing Page", "category": "Design", "priority": "High", "status": "Todo"})
    client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Design Mobile Mockups", "category": "Design", "priority": "Low", "status": "In Progress"})
    client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Implement Payment API", "category": "Engineering", "priority": "High", "status": "Todo"})
    client.post(f"{settings.API_V1_STR}/tasks", headers=headers, json={"title": "Deploy Microservice", "category": "Engineering", "priority": "Medium", "status": "Completed"})

    # 2. Test filter evaluation: category=Design AND priority=High
    filter_apply_res = client.post(
        f"{settings.API_V1_STR}/filters/apply",
        headers=headers,
        json={
            "query_config": {
                "match_type": "ALL",
                "conditions": [
                    {"field": "category", "operator": "equals", "value": "Design"},
                    {"field": "priority", "operator": "equals", "value": "High"}
                ]
            }
        }
    )
    assert filter_apply_res.status_code == 200
    matched = filter_apply_res.json()
    assert len(matched) == 1
    assert matched[0]["title"] == "Design Landing Page"

    # 3. Test text match: title contains 'Mockups'
    contains_res = client.post(
        f"{settings.API_V1_STR}/filters/apply",
        headers=headers,
        json={
            "query_config": {
                "conditions": [{"field": "title", "operator": "contains", "value": "Mockups"}]
            }
        }
    )
    assert contains_res.status_code == 200
    assert len(contains_res.json()) == 1

    # 4. Save filter
    save_filter_res = client.post(
        f"{settings.API_V1_STR}/filters",
        headers=headers,
        json={
            "name": "High Priority Design Work",
            "query_config": {
                "match_type": "ALL",
                "conditions": [
                    {"field": "category", "operator": "equals", "value": "Design"},
                    {"field": "priority", "operator": "equals", "value": "High"}
                ]
            }
        }
    )
    assert save_filter_res.status_code == 201
    filter_id = save_filter_res.json()["id"]

    # Apply by filter_id
    apply_by_id = client.post(
        f"{settings.API_V1_STR}/filters/apply",
        headers=headers,
        json={"filter_id": filter_id}
    )
    assert apply_by_id.status_code == 200
    assert len(apply_by_id.json()) == 1

    # 5. Create View with Grouping by priority
    grouped_view = client.post(
        f"{settings.API_V1_STR}/views",
        headers=headers,
        json={
            "name": "Tasks by Priority",
            "view_type": "list",
            "group_config": {"field": "priority"}
        }
    ).json()

    # Query view data
    v_data_res = client.get(f"{settings.API_V1_STR}/views/{grouped_view['id']}/data", headers=headers)
    assert v_data_res.status_code == 200
    v_data = v_data_res.json()
    assert v_data["total"] == 4
    assert "High" in v_data["groups"]
    assert len(v_data["groups"]["High"]) == 2
    assert v_data["group_counts"]["High"] == 2


def test_multi_tenant_isolation_and_workspace_sharing(client):
    """Test tenant boundary enforcement, 404 IDOR shielding, and workspace shared boards."""
    token1 = get_auth_token(client, "org_u1@example.com", "orgu1")
    token2 = get_auth_token(client, "org_u2@example.com", "orgu2")
    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # 1. User 1 creates private board and private view
    board1 = client.post(f"{settings.API_V1_STR}/boards", headers=h1, json={"name": "Executive Private Board", "visibility": "private"}).json()["id"]
    view1 = client.post(f"{settings.API_V1_STR}/views", headers=h1, json={"name": "Secret View", "visibility": "private"}).json()["id"]

    # 2. User 2 cannot access private board or view -> 404 Not Found
    assert client.get(f"{settings.API_V1_STR}/boards/{board1}", headers=h2).status_code == 404
    assert client.patch(f"{settings.API_V1_STR}/boards/{board1}", headers=h2, json={"name": "Hacked"}).status_code == 404
    assert client.delete(f"{settings.API_V1_STR}/boards/{board1}", headers=h2).status_code == 404
    assert client.get(f"{settings.API_V1_STR}/views/{view1}", headers=h2).status_code == 404
    assert client.delete(f"{settings.API_V1_STR}/views/{view1}", headers=h2).status_code == 404

    # 3. User 1 creates a workspace, invites User 2
    ws = client.post(f"{settings.API_V1_STR}/workspaces", headers=h1, json={"name": "Product Collaboration"}).json()
    ws_id = ws["id"]

    inv = client.post(
        f"{settings.API_V1_STR}/workspaces/{ws_id}/invitations",
        headers=h1,
        json={"email": "org_u2@example.com", "role": "MEMBER"}
    ).json()
    client.post(f"{settings.API_V1_STR}/workspaces/invitations/{inv['token']}/accept", headers=h2)

    # 4. User 1 creates a shared board in the workspace
    shared_board = client.post(
        f"{settings.API_V1_STR}/boards",
        headers=h1,
        json={"name": "Sprint Board", "workspace_id": ws_id, "visibility": "workspace"}
    ).json()
    shared_board_id = shared_board["id"]
    col_in_prog = next(c for c in shared_board["columns"] if c["status_value"] == "In Progress")

    # 5. User 1 creates task in workspace
    shared_task = client.post(
        f"{settings.API_V1_STR}/tasks",
        headers=h1,
        json={"title": "Shared UI Task", "workspace_id": ws_id}
    ).json()["id"]

    # 6. User 2 can view shared board and move shared task
    u2_board = client.get(f"{settings.API_V1_STR}/boards/{shared_board_id}", headers=h2)
    assert u2_board.status_code == 200
    assert u2_board.json()["name"] == "Sprint Board"

    u2_move = client.patch(
        f"{settings.API_V1_STR}/boards/{shared_board_id}/tasks/{shared_task}/position",
        headers=h2,
        json={"destination_column_id": col_in_prog["id"], "destination_position": 0}
    )
    assert u2_move.status_code == 200
    assert u2_move.json()["status"] == "In Progress"
