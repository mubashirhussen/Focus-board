"""
Automated Integration & Security Tests for Phase B4: Complete Projects Backend.
Tests project creation, CRUD, lifecycle transitions, ownership, memberships,
visibility, settings, dynamic progress calculation, templates, duplication,
dependency graphs with cycle detection, search, activity feeds, and tenant isolation.
"""

from datetime import datetime, timedelta, timezone
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


def _create_user_and_token(client, email: str, username: str) -> tuple:
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": email,
        "username": username,
        "password": "Password123!",
    })
    res = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": email,
        "password": "Password123!",
    }).json()
    return res["user"]["id"], res["access_token"]


def _setup_org_and_workspace(client, token: str, org_name="Test Org", ws_name="Test Workspace") -> tuple:
    headers = {"Authorization": f"Bearer {token}"}
    org = client.post(f"{settings.API_V1_STR}/organizations", json={"name": org_name}, headers=headers).json()
    ws = client.post(
        f"{settings.API_V1_STR}/organizations/{org['id']}/workspaces",
        json={"name": ws_name},
        headers=headers,
    ).json()
    return org["id"], ws["id"]


def test_b4_project_creation_and_validation(client):
    """Test project creation, validation rules (dates, status), and automatic ownership."""
    u1_id, t1 = _create_user_and_token(client, "pm_creator@test.io", "pm_creator")
    headers = {"Authorization": f"Bearer {t1}"}
    org_id, ws_id = _setup_org_and_workspace(client, t1)

    # Valid creation
    now = datetime.utcnow()
    res = client.post(
        f"{settings.API_V1_STR}/projects",
        json={
            "workspace_id": ws_id,
            "name": "FocusBoard V2 Mobile",
            "description": "Next gen native app",
            "priority": "HIGH",
            "health": "ON_TRACK",
            "visibility": "WORKSPACE",
            "start_date": now.isoformat(),
            "due_date": (now + timedelta(days=30)).isoformat(),
            "category": "Engineering",
            "tags": ["mobile", "react-native"],
        },
        headers=headers,
    )
    assert res.status_code == 201
    proj = res.json()
    assert proj["name"] == "FocusBoard V2 Mobile"
    assert proj["workspace_id"] == ws_id
    assert proj["created_by"] == u1_id
    assert proj["owner_id"] == u1_id
    assert proj["priority"] == "HIGH"
    assert "mobile" in proj["tags"]

    # Invalid dates (start_date > due_date)
    bad_dates = client.post(
        f"{settings.API_V1_STR}/projects",
        json={
            "workspace_id": ws_id,
            "name": "Impossible Project",
            "start_date": (now + timedelta(days=10)).isoformat(),
            "due_date": now.isoformat(),
        },
        headers=headers,
    )
    assert bad_dates.status_code == 400
    assert "start_date cannot be later than due_date" in bad_dates.json()["detail"]

    # Invalid status
    bad_status = client.post(
        f"{settings.API_V1_STR}/projects",
        json={
            "workspace_id": ws_id,
            "name": "Invalid Status Project",
            "status": "NONEXISTENT",
        },
        headers=headers,
    )
    assert bad_status.status_code == 400


def test_b4_project_listing_search_and_filtering(client):
    """Test project listing, filtering by status/health/priority, search keyword, and pagination."""
    u1_id, t1 = _create_user_and_token(client, "lister@test.io", "lister")
    headers = {"Authorization": f"Bearer {t1}"}
    org_id, ws_id = _setup_org_and_workspace(client, t1, ws_name="Listing WS")

    # Seed 3 projects
    client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws_id, "name": "Alpha Portal", "priority": "CRITICAL", "health": "AT_RISK", "category": "Dev"
    }, headers=headers)
    client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws_id, "name": "Beta Backend", "priority": "LOW", "health": "ON_TRACK", "category": "Infra"
    }, headers=headers)
    client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws_id, "name": "Gamma AI", "priority": "HIGH", "health": "ON_TRACK", "category": "AI"
    }, headers=headers)

    # List all
    all_res = client.get(f"{settings.API_V1_STR}/projects?workspace_id={ws_id}", headers=headers)
    assert all_res.status_code == 200
    assert len(all_res.json()) == 3

    # Filter priority
    crit_res = client.get(f"{settings.API_V1_STR}/projects?workspace_id={ws_id}&priority=CRITICAL", headers=headers)
    assert len(crit_res.json()) == 1
    assert crit_res.json()[0]["name"] == "Alpha Portal"

    # Filter health
    risk_res = client.get(f"{settings.API_V1_STR}/projects?workspace_id={ws_id}&health=AT_RISK", headers=headers)
    assert len(risk_res.json()) == 1
    assert risk_res.json()[0]["name"] == "Alpha Portal"

    # Search keyword
    search_res = client.get(f"{settings.API_V1_STR}/projects/search?q=Gamma", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert search_res.json()[0]["name"] == "Gamma AI"

    # Pagination
    page_res = client.get(f"{settings.API_V1_STR}/projects?workspace_id={ws_id}&skip=0&limit=2", headers=headers)
    assert len(page_res.json()) == 2


def test_b4_project_lifecycle_and_archival(client):
    """Test project lifecycle transitions (PLANNING, ACTIVE, COMPLETED, ARCHIVED) and restoration."""
    u1_id, t1 = _create_user_and_token(client, "lifecycle_mgr@test.io", "lifecycle_mgr")
    headers = {"Authorization": f"Bearer {t1}"}
    _, ws_id = _setup_org_and_workspace(client, t1)

    proj = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws_id, "name": "Lifecycle Test Project", "status": "PLANNING"
    }, headers=headers).json()
    proj_id = proj["id"]
    assert proj["status"] == "PLANNING"

    # Status transition to ACTIVE
    res1 = client.patch(f"{settings.API_V1_STR}/projects/{proj_id}/status", json={"status": "ACTIVE"}, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "ACTIVE"

    # Status transition to COMPLETED
    res2 = client.patch(f"{settings.API_V1_STR}/projects/{proj_id}/status", json={"status": "COMPLETED"}, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "COMPLETED"

    # Archive project
    arch_res = client.post(f"{settings.API_V1_STR}/projects/{proj_id}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["is_archived"] is True
    assert arch_res.json()["status"] == "ARCHIVED"

    # Should not appear in active projects list
    active_list = client.get(f"{settings.API_V1_STR}/projects?workspace_id={ws_id}", headers=headers).json()
    assert not any(p["id"] == proj_id for p in active_list)

    # Restore project
    rest_res = client.post(f"{settings.API_V1_STR}/projects/{proj_id}/restore", headers=headers)
    assert rest_res.status_code == 200
    assert rest_res.json()["is_archived"] is False
    assert rest_res.json()["status"] == "ACTIVE"


def test_b4_dynamic_progress_calculation(client):
    """Test that project progress is computed dynamically from actual tasks."""
    u1_id, t1 = _create_user_and_token(client, "progress_mgr@test.io", "progress_mgr")
    headers = {"Authorization": f"Bearer {t1}"}
    _, ws_id = _setup_org_and_workspace(client, t1)

    proj = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws_id, "name": "Task Progress Project"
    }, headers=headers).json()
    proj_id = proj["id"]

    # Initial progress: 0%
    prog0 = client.get(f"{settings.API_V1_STR}/projects/{proj_id}/progress", headers=headers).json()
    assert prog0["total_tasks"] == 0
    assert prog0["progress_percent"] == 0.0

    # Add 4 tasks (2 Completed, 1 In Progress, 1 Todo) using workspace tasks API
    client.post(f"{settings.API_V1_STR}/workspaces/{ws_id}/tasks?project_id={proj_id}", json={
        "title": "Task 1", "status": "Completed"
    }, headers=headers)
    client.post(f"{settings.API_V1_STR}/workspaces/{ws_id}/tasks?project_id={proj_id}", json={
        "title": "Task 2", "status": "Completed"
    }, headers=headers)
    client.post(f"{settings.API_V1_STR}/workspaces/{ws_id}/tasks?project_id={proj_id}", json={
        "title": "Task 3", "status": "In Progress"
    }, headers=headers)
    client.post(f"{settings.API_V1_STR}/workspaces/{ws_id}/tasks?project_id={proj_id}", json={
        "title": "Task 4", "status": "Todo"
    }, headers=headers)

    # Progress should be 50.0% (2 / 4)
    prog1 = client.get(f"{settings.API_V1_STR}/projects/{proj_id}/progress", headers=headers).json()
    assert prog1["total_tasks"] == 4
    assert prog1["completed_tasks"] == 2
    assert prog1["in_progress_tasks"] == 1
    assert prog1["todo_tasks"] == 1
    assert prog1["progress_percent"] == 50.0

    # Project summary dashboard metrics
    summary = client.get(f"{settings.API_V1_STR}/projects/{proj_id}/summary", headers=headers).json()
    assert summary["total_tasks"] == 4
    assert summary["completed_tasks"] == 2
    assert summary["progress_percent"] == 50.0


def test_b4_project_memberships_and_rbac(client):
    """Test adding, updating, and removing project members with role enforcement."""
    u1_id, t1 = _create_user_and_token(client, "pm_lead@test.io", "pm_lead")
    u2_id, t2 = _create_user_and_token(client, "pm_dev@test.io", "pm_dev")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}
    org_id, ws_id = _setup_org_and_workspace(client, t1)

    # Add u2 to workspace first
    inv = client.post(f"{settings.API_V1_STR}/workspaces/{ws_id}/invitations", json={"email": "pm_dev@test.io", "role": "MEMBER"}, headers=h1).json()
    client.post(f"{settings.API_V1_STR}/workspaces/invitations/{inv['token']}/accept", headers=h2)

    proj = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws_id, "name": "Team Collab Project"
    }, headers=h1).json()
    proj_id = proj["id"]

    # Add u2 as PROJECT_MEMBER
    add_mem = client.post(f"{settings.API_V1_STR}/projects/{proj_id}/members", json={
        "user_id": u2_id, "role": "PROJECT_MEMBER"
    }, headers=h1)
    assert add_mem.status_code == 201
    assert add_mem.json()["role"] == "PROJECT_MEMBER"

    # List members
    members = client.get(f"{settings.API_V1_STR}/projects/{proj_id}/members", headers=h1).json()
    assert len(members) == 2
    assert any(m["user_id"] == u2_id for m in members)

    # Update role to PROJECT_ADMIN
    patch_mem = client.patch(f"{settings.API_V1_STR}/projects/{proj_id}/members/{u2_id}", json={
        "role": "PROJECT_ADMIN"
    }, headers=h1)
    assert patch_mem.status_code == 200
    assert patch_mem.json()["role"] == "PROJECT_ADMIN"

    # Remove member
    del_mem = client.delete(f"{settings.API_V1_STR}/projects/{proj_id}/members/{u2_id}", headers=h1)
    assert del_mem.status_code == 200
    assert len(client.get(f"{settings.API_V1_STR}/projects/{proj_id}/members", headers=h1).json()) == 1


def test_b4_project_duplication(client):
    """Test project duplication copying tasks and settings."""
    u1_id, t1 = _create_user_and_token(client, "duplicator@test.io", "duplicator")
    headers = {"Authorization": f"Bearer {t1}"}
    _, ws_id = _setup_org_and_workspace(client, t1)

    proj = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws_id,
        "name": "Original Blueprint",
        "category": "Design",
        "settings": {"sprint_length": 14},
    }, headers=headers).json()
    proj_id = proj["id"]

    # Add a task to original
    client.post(f"{settings.API_V1_STR}/workspaces/{ws_id}/tasks?project_id={proj_id}", json={
        "title": "Wireframing Screen 1"
    }, headers=headers)

    # Duplicate
    dup_res = client.post(f"{settings.API_V1_STR}/projects/{proj_id}/duplicate", json={
        "name": "Duplicated Blueprint",
        "duplicate_tasks": True,
        "duplicate_settings": True,
    }, headers=headers)
    assert dup_res.status_code == 201
    dup_proj = dup_res.json()
    assert dup_proj["name"] == "Duplicated Blueprint"
    assert dup_proj["id"] != proj_id
    assert dup_proj["settings"]["sprint_length"] == 14
    assert dup_proj["tasks_count"] == 1


def test_b4_project_dependencies_and_cycle_prevention(client):
    """Test creating project dependencies and preventing self or circular dependencies."""
    u1_id, t1 = _create_user_and_token(client, "dep_mgr@test.io", "dep_mgr")
    headers = {"Authorization": f"Bearer {t1}"}
    _, ws_id = _setup_org_and_workspace(client, t1)

    pA = client.post(f"{settings.API_V1_STR}/projects", json={"workspace_id": ws_id, "name": "Project A"}, headers=headers).json()
    pB = client.post(f"{settings.API_V1_STR}/projects", json={"workspace_id": ws_id, "name": "Project B"}, headers=headers).json()
    pC = client.post(f"{settings.API_V1_STR}/projects", json={"workspace_id": ws_id, "name": "Project C"}, headers=headers).json()

    # Self dependency must fail
    self_res = client.post(f"{settings.API_V1_STR}/projects/{pA['id']}/dependencies", json={
        "depends_on_project_id": pA["id"]
    }, headers=headers)
    assert self_res.status_code == 400
    assert "cannot depend on itself" in self_res.json()["detail"].lower()

    # A depends on B
    dep1 = client.post(f"{settings.API_V1_STR}/projects/{pA['id']}/dependencies", json={
        "depends_on_project_id": pB["id"], "dependency_type": "FINISH_TO_START"
    }, headers=headers)
    assert dep1.status_code == 201

    # B depends on C
    dep2 = client.post(f"{settings.API_V1_STR}/projects/{pB['id']}/dependencies", json={
        "depends_on_project_id": pC["id"], "dependency_type": "FINISH_TO_START"
    }, headers=headers)
    assert dep2.status_code == 201

    # C depends on A (Circular: C -> A -> B -> C) MUST fail
    cycle_res = client.post(f"{settings.API_V1_STR}/projects/{pC['id']}/dependencies", json={
        "depends_on_project_id": pA["id"]
    }, headers=headers)
    assert cycle_res.status_code == 400
    assert "circular dependency" in cycle_res.json()["detail"].lower()


def test_b4_project_templates(client):
    """Test project template creation, retrieval, and instantiation into a live project."""
    u1_id, t1 = _create_user_and_token(client, "template_mgr@test.io", "template_mgr")
    headers = {"Authorization": f"Bearer {t1}"}
    _, ws_id = _setup_org_and_workspace(client, t1)

    # Create Template
    tmpl = client.post(f"{settings.API_V1_STR}/project-templates", json={
        "name": "Standard Agile Sprint",
        "description": "2-week sprint with backlog, grooming, and review",
        "category": "Software",
        "default_settings": {"review_frequency": "weekly"},
        "default_tasks": [
            {"title": "Sprint Planning", "priority": "High"},
            {"title": "Sprint Retrospective", "priority": "Medium"},
        ],
    }, headers=headers).json()
    tmpl_id = tmpl["id"]
    assert tmpl["name"] == "Standard Agile Sprint"

    # Instantiate project from template
    from_tmpl = client.post(f"{settings.API_V1_STR}/projects/from-template/{tmpl_id}", json={
        "workspace_id": ws_id,
        "name": "Sprint 42 Live",
    }, headers=headers)
    assert from_tmpl.status_code == 201
    proj_inst = from_tmpl.json()
    assert proj_inst["name"] == "Sprint 42 Live"
    assert proj_inst["settings"]["review_frequency"] == "weekly"
    assert proj_inst["tasks_count"] == 2


def test_b4_multi_tenant_isolation(client):
    """Test cross-tenant and cross-workspace project security isolation."""
    u1_id, t1 = _create_user_and_token(client, "tenant1_pm@test.io", "tenant1_pm")
    u2_id, t2 = _create_user_and_token(client, "tenant2_pm@test.io", "tenant2_pm")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    _, ws1_id = _setup_org_and_workspace(client, t1, org_name="Tenant 1 Org", ws_name="Tenant 1 WS")
    _, ws2_id = _setup_org_and_workspace(client, t2, org_name="Tenant 2 Org", ws_name="Tenant 2 WS")

    proj1 = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws1_id, "name": "Confidential Tenant 1 Project", "visibility": "PRIVATE"
    }, headers=h1).json()
    proj1_id = proj1["id"]

    # User 2 attempts to view Tenant 1's project -> 403 Forbidden
    view_res = client.get(f"{settings.API_V1_STR}/projects/{proj1_id}", headers=h2)
    assert view_res.status_code == 403

    # User 2 attempts to edit Tenant 1's project -> 403 Forbidden
    edit_res = client.patch(f"{settings.API_V1_STR}/projects/{proj1_id}", json={"name": "Hacked Name"}, headers=h2)
    assert edit_res.status_code == 403

    # User 2 attempts to delete Tenant 1's project -> 403 Forbidden
    del_res = client.delete(f"{settings.API_V1_STR}/projects/{proj1_id}", headers=h2)
    assert del_res.status_code == 403

    # User 2 attempts to create project in Tenant 1's workspace -> 403 Forbidden
    cross_create = client.post(f"{settings.API_V1_STR}/projects", json={
        "workspace_id": ws1_id, "name": "Illegal Project"
    }, headers=h2)
    assert cross_create.status_code == 403
