"""
Automated Integration, RBAC & Isolation Tests for Phase B3: Multi-Tenant Organizations.
Tests organization creation, memberships, role hierarchies, invitations,
scoped workspaces, tenant isolation, and ownership transfer.
"""

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


def test_b3_organization_lifecycle_and_ownership(client):
    """Test creating an org, automatic OWNER assignment, editing, and listing."""
    user1_id, token1 = _create_user_and_token(client, "org_owner@test.io", "org_owner")
    headers = {"Authorization": f"Bearer {token1}"}

    # Create Org
    org_res = client.post(
        f"{settings.API_V1_STR}/organizations",
        json={"name": "Acme Corp", "description": "Global Enterprise", "plan": "enterprise_pro"},
        headers=headers,
    )
    assert org_res.status_code == 201
    org_data = org_res.json()
    org_id = org_data["id"]
    assert org_data["name"] == "Acme Corp"
    assert org_data["owner_id"] == user1_id
    assert org_data["slug"] == "acme-corp"

    # List Orgs
    list_res = client.get(f"{settings.API_V1_STR}/organizations", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert any(o["id"] == org_id for o in list_res.json())

    # Update Org (owner permission)
    patch_res = client.patch(
        f"{settings.API_V1_STR}/organizations/{org_id}",
        json={"name": "Acme Global Corporation"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Acme Global Corporation"


def test_b3_invitation_and_membership_acceptance(client):
    """Test inviting a user to an organization, token generation, and acceptance."""
    user1_id, token1 = _create_user_and_token(client, "inviter@test.io", "inviter")
    user2_id, token2 = _create_user_and_token(client, "invitee@test.io", "invitee")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Create Org
    org = client.post(
        f"{settings.API_V1_STR}/organizations",
        json={"name": "Pied Piper"},
        headers=headers1,
    ).json()
    org_id = org["id"]

    # Send Invite
    inv_res = client.post(
        f"{settings.API_V1_STR}/organizations/{org_id}/invitations",
        json={"email": "invitee@test.io", "role": "admin"},
        headers=headers1,
    )
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    invite_token = inv_data["invite_token"]
    assert invite_token is not None

    # Accept Invite using User 2's session
    accept_res = client.post(
        f"{settings.API_V1_STR}/invitations/accept",
        json={"token": invite_token},
        headers=headers2,
    )
    assert accept_res.status_code == 200

    # User 2 now sees the org
    user2_orgs = client.get(f"{settings.API_V1_STR}/organizations", headers=headers2).json()
    assert any(o["id"] == org_id for o in user2_orgs)

    # Members list includes both
    members = client.get(f"{settings.API_V1_STR}/organizations/{org_id}/members", headers=headers1).json()
    assert len(members) == 2
    u2_member = next(m for m in members if m["user_id"] == user2_id)
    assert u2_member["role"] == "admin"


def test_b3_scoped_workspaces_and_tenant_isolation(client):
    """Test that workspaces scoped to an organization are protected from cross-tenant access."""
    u1_id, t1 = _create_user_and_token(client, "tenant_a_user@test.io", "tenant_a")
    u2_id, t2 = _create_user_and_token(client, "tenant_b_user@test.io", "tenant_b")

    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    # Org A created by User A
    org_a = client.post(f"{settings.API_V1_STR}/organizations", json={"name": "Tenant A Corp"}, headers=h1).json()
    org_a_id = org_a["id"]

    # Org B created by User B
    org_b = client.post(f"{settings.API_V1_STR}/organizations", json={"name": "Tenant B Corp"}, headers=h2).json()
    org_b_id = org_b["id"]

    # User A creates Workspace in Org A
    ws_res = client.post(
        f"{settings.API_V1_STR}/organizations/{org_a_id}/workspaces",
        json={"name": "Engineering Workspace", "description": "Core dev"},
        headers=h1,
    )
    assert ws_res.status_code == 201
    ws_data = ws_res.json()
    assert ws_data["organization_id"] == org_a_id

    # User B attempts to access Org A workspaces -> Forbidden (403)
    cross_access = client.get(f"{settings.API_V1_STR}/organizations/{org_a_id}/workspaces", headers=h2)
    assert cross_access.status_code == 403

    # User B attempts to modify Org A -> Forbidden (403)
    cross_patch = client.patch(
        f"{settings.API_V1_STR}/organizations/{org_a_id}",
        json={"name": "Hacked Org Name"},
        headers=h2,
    )
    assert cross_patch.status_code == 403


def test_b3_ownership_transfer(client):
    """Test transferring organization ownership from original creator to another member."""
    u1_id, t1 = _create_user_and_token(client, "founder@test.io", "founder")
    u2_id, t2 = _create_user_and_token(client, "successor@test.io", "successor")

    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    org = client.post(f"{settings.API_V1_STR}/organizations", json={"name": "Dynasty Inc"}, headers=h1).json()
    org_id = org["id"]

    # Invite and accept successor
    inv = client.post(
        f"{settings.API_V1_STR}/organizations/{org_id}/invitations",
        json={"email": "successor@test.io", "role": "admin"},
        headers=h1,
    ).json()
    client.post(f"{settings.API_V1_STR}/invitations/accept", json={"token": inv["invite_token"]}, headers=h2)

    # Transfer ownership
    transfer_res = client.post(
        f"{settings.API_V1_STR}/organizations/{org_id}/transfer-ownership",
        json={"new_owner_user_id": u2_id},
        headers=h1,
    )
    assert transfer_res.status_code == 200

    # Verify new owner
    org_refreshed = client.get(f"{settings.API_V1_STR}/organizations/{org_id}", headers=h2).json()
    assert org_refreshed["owner_id"] == u2_id
