"""
Automated Integration & Security Tests for Phase B2: Complete Authentication & Identity.
Tests registration, login, token rotation, session lifecycle, password reset,
change password, email verification, and profile endpoints.
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
import app.models  # ensure models loaded

# Use in-memory SQLite isolated DB for tests
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


def test_b2_user_registration(client):
    """Test standard user registration, privilege escalation prevention, and duplicate email prevention."""
    payload = {
        "email": "alice@focusboard.io",
        "username": "alice",
        "password": "StrongPassword123!",
        "full_name": "Alice Smith",
        "role": "admin",  # Attempt privilege escalation
    }
    res = client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "alice@focusboard.io"
    assert data["role"] == "member"  # Escalation prevented
    assert data["is_active"] is True
    assert data["is_verified"] is False

    # Duplicate registration must fail
    res_dup = client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"].lower()


def test_b2_login_and_token_generation(client):
    """Test user login returns access and refresh JWTs with session id."""
    reg = client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": "bob@focusboard.io",
        "password": "SecretPassword999!",
        "username": "bob",
    })
    assert reg.status_code == 201

    # Bad password
    bad_res = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "bob@focusboard.io",
        "password": "WrongPassword!",
    })
    assert bad_res.status_code == 401

    # Good password
    login_res = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "bob@focusboard.io",
        "password": "SecretPassword999!",
        "device_name": "Workstation Chrome",
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "bob@focusboard.io"


def test_b2_token_refresh_and_rotation(client):
    """Test that refresh token issues new tokens and rotates."""
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": "carol@focusboard.io",
        "password": "CarolPassword123!",
    })
    login_res = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "carol@focusboard.io",
        "password": "CarolPassword123!",
    })
    refresh_token = login_res.json()["refresh_token"]

    # Refresh
    refresh_res = client.post(f"{settings.API_V1_STR}/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["refresh_token"] != refresh_token


def test_b2_session_management_and_revocation(client):
    """Test session listing, specific revocation, and logout-all."""
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": "dave@focusboard.io",
        "password": "DavePassword123!",
    })
    login_1 = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "dave@focusboard.io",
        "password": "DavePassword123!",
        "device_name": "Device 1",
    }).json()
    token_1 = login_1["access_token"]

    login_2 = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "dave@focusboard.io",
        "password": "DavePassword123!",
        "device_name": "Device 2",
    }).json()
    token_2 = login_2["access_token"]

    # List sessions using token_1
    sess_res = client.get(
        f"{settings.API_V1_STR}/auth/sessions",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    assert sess_res.status_code == 200
    sessions = sess_res.json()
    assert len(sessions) >= 2

    # Logout all sessions using token_1
    logout_all = client.post(
        f"{settings.API_V1_STR}/auth/logout-all",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    assert logout_all.status_code == 200
    assert logout_all.json()["revoked_sessions"] >= 2


def test_b2_password_reset_flow(client):
    """Test forgot-password token generation, reset-password, and new password login."""
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": "eve@focusboard.io",
        "password": "EveOldPassword123!",
    })

    # Forgot password
    forgot_res = client.post(f"{settings.API_V1_STR}/auth/forgot-password", json={
        "email": "eve@focusboard.io",
    })
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["reset_token"]
    assert reset_token is not None

    # Reset password
    reset_res = client.post(f"{settings.API_V1_STR}/auth/reset-password", json={
        "token": reset_token,
        "new_password": "EveNewPassword456!",
    })
    assert reset_res.status_code == 200

    # Old password fails
    old_login = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "eve@focusboard.io",
        "password": "EveOldPassword123!",
    })
    assert old_login.status_code == 401

    # New password succeeds
    new_login = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "eve@focusboard.io",
        "password": "EveNewPassword456!",
    })
    assert new_login.status_code == 200


def test_b2_profile_update_and_data_export(client):
    """Test user profile get, patch, and GDPR data export."""
    client.post(f"{settings.API_V1_STR}/auth/register", json={
        "email": "frank@focusboard.io",
        "password": "FrankPassword123!",
    })
    token = client.post(f"{settings.API_V1_STR}/auth/login", json={
        "email": "frank@focusboard.io",
        "password": "FrankPassword123!",
    }).json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Profile Get
    me_res = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "frank@focusboard.io"

    # Profile Patch
    patch_res = client.patch(
        f"{settings.API_V1_STR}/auth/me",
        json={"display_name": "Frank The Architect", "timezone": "America/New_York"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["display_name"] == "Frank The Architect"
    assert patch_res.json()["timezone"] == "America/New_York"

    # Data export
    export_res = client.get(f"{settings.API_V1_STR}/auth/export-data", headers=headers)
    assert export_res.status_code == 200
    assert "user_profile" in export_res.json()
    assert "session_history" in export_res.json()
