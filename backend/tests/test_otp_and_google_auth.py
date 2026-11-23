"""
Automated Integration Tests for FocusBoard Email OTP & Google OAuth Authentication.
Tests:
- Passwordless email start (new user vs existing user)
- Username availability, validation, and reserved words check
- New user registration with email OTP
- OTP verification, hashing, attempt limits, expiration, and user provisioning
- Existing user login with OTP
- OTP resend throttling
- Google OAuth URL and account selection
- Google identity verification (login and new user creation)
"""

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.models.auth import EmailOTPVerification
from app.models.user import User
from app.services.otp_service import otp_service

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


def test_username_validation_and_availability(client):
    """Test username checking for length, characters, reserved names, and uniqueness."""
    # Too short
    res = client.get(f"{settings.API_V1_STR}/auth/username/check?username=ab")
    assert res.status_code == 200
    assert res.json()["available"] is False
    assert "between 3 and 30" in res.json()["message"]

    # Invalid characters
    res = client.get(f"{settings.API_V1_STR}/auth/username/check?username=bad@user!")
    assert res.status_code == 200
    assert res.json()["available"] is False

    # Reserved username
    res = client.get(f"{settings.API_V1_STR}/auth/username/check?username=admin")
    assert res.status_code == 200
    assert res.json()["available"] is False
    assert "reserved" in res.json()["message"]

    # Valid available username
    res = client.get(f"{settings.API_V1_STR}/auth/username/check?username=creative_coder_99")
    assert res.status_code == 200
    assert res.json()["available"] is True


def test_email_start_new_vs_existing_user(client, db_session):
    """Test email start identifies whether account exists or registration is needed."""
    # 1. Unregistered email -> is_new_user = True
    res_new = client.post(f"{settings.API_V1_STR}/auth/email/start", json={"email": "daisy@focusboard.io"})
    assert res_new.status_code == 200
    data_new = res_new.json()
    assert data_new["success"] is True
    assert data_new["is_new_user"] is True

    # 2. Register a user
    user = User(
        email="daisy@focusboard.io",
        name="daisy",
        display_name="Daisy Duck",
        hashed_password="some_secret_hash",
        role="member",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # 3. Existing email -> is_new_user = False, returns verification_session_id
    res_exist = client.post(f"{settings.API_V1_STR}/auth/email/start", json={"email": "daisy@focusboard.io"})
    assert res_exist.status_code == 200
    data_exist = res_exist.json()
    assert data_exist["success"] is True
    assert data_exist["is_new_user"] is False
    assert data_exist["verification_session_id"] is not None
    assert data_exist["expires_in"] == 300


def test_new_user_registration_and_otp_verification(client, db_session):
    """Test registration details submission, OTP email dispatch, and successful verification provisioning."""
    email = "sarah.connor@focusboard.io"
    reg_payload = {
        "name": "Sarah Connor",
        "username": "sarah_c",
        "email": email,
        "role": "member",
    }
    reg_res = client.post(f"{settings.API_V1_STR}/auth/email/register", json=reg_payload)
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    session_id = reg_data["verification_session_id"]
    assert session_id is not None

    # Retrieve OTP hash record from DB to verify hashing
    otp_record = db_session.query(EmailOTPVerification).filter(EmailOTPVerification.session_id == session_id).first()
    assert otp_record is not None
    assert otp_record.is_verified is False
    assert otp_record.attempts == 0

    # Wrong OTP code
    bad_res = client.post(f"{settings.API_V1_STR}/auth/email/verify-otp", json={
        "email": email,
        "otp": "000000",
        "verification_session_id": session_id,
        "purpose": "registration",
    })
    assert bad_res.status_code == 400
    assert "incorrect" in bad_res.json()["detail"].lower()

    # Refresh record to check attempt count
    db_session.refresh(otp_record)
    assert otp_record.attempts == 1

    # Now verify with simulated valid OTP: generate matching hash
    valid_test_otp = "123456"
    otp_record.otp_hash = otp_service.hash_otp(valid_test_otp)
    db_session.commit()

    good_res = client.post(f"{settings.API_V1_STR}/auth/email/verify-otp", json={
        "email": email,
        "otp": valid_test_otp,
        "verification_session_id": session_id,
        "purpose": "registration",
    })
    assert good_res.status_code == 200
    auth_data = good_res.json()
    assert "access_token" in auth_data
    assert "refresh_token" in auth_data
    assert auth_data["token_type"] == "bearer"
    assert auth_data["user"]["email"] == email
    assert auth_data["user"]["username"] == "sarah_c"
    assert auth_data["user"]["is_verified"] is True

    # Check user created in DB
    created_user = db_session.query(User).filter(User.email == email).first()
    assert created_user is not None
    assert created_user.name == "sarah_c"
    assert created_user.display_name == "Sarah Connor"


def test_existing_user_otp_login_flow(client, db_session):
    """Test existing user login via OTP code."""
    email = "alex.murphy@focusboard.io"
    user = User(
        email=email,
        name="alex_m",
        display_name="Alex Murphy",
        hashed_password="some_hashed_password",
        role="member",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    start_res = client.post(f"{settings.API_V1_STR}/auth/email/start", json={"email": email})
    assert start_res.status_code == 200
    session_id = start_res.json()["verification_session_id"]

    otp_record = db_session.query(EmailOTPVerification).filter(EmailOTPVerification.session_id == session_id).first()
    test_otp = "654321"
    otp_record.otp_hash = otp_service.hash_otp(test_otp)
    db_session.commit()

    login_res = client.post(f"{settings.API_V1_STR}/auth/email/verify-otp", json={
        "email": email,
        "otp": test_otp,
        "verification_session_id": session_id,
        "purpose": "login",
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert token_data["user"]["email"] == email
    assert token_data["user"]["id"] == user.id


def test_resend_otp_rate_limiting(client, db_session):
    """Test that requesting an OTP resend immediately is throttled by cooldown."""
    email = "cooldown.test@focusboard.io"
    user = User(email=email, name="cooldown_user", hashed_password="pw", is_active=True)
    db_session.add(user)
    db_session.commit()

    start_res = client.post(f"{settings.API_V1_STR}/auth/email/start", json={"email": email})
    session_id = start_res.json()["verification_session_id"]

    # Immediate resend attempt should fail with 429
    resend_res = client.post(f"{settings.API_V1_STR}/auth/email/resend-otp", json={
        "email": email,
        "verification_session_id": session_id,
        "purpose": "login",
    })
    assert resend_res.status_code == 429
    assert "please wait" in resend_res.json()["detail"].lower()


def test_google_oauth_endpoints(client, db_session):
    """Test Google OAuth URL generation and identity verification."""
    # 1. URL generation
    url_res = client.get(f"{settings.API_V1_STR}/auth/google/url")
    assert url_res.status_code == 200
    url_data = url_res.json()
    assert "accounts.google.com" in url_data["url"]
    assert "prompt=select_account" in url_data["url"]

    # 2. New Google user verification
    google_res = client.post(f"{settings.API_V1_STR}/auth/google/verify", json={
        "email": "daisy.google@example.com",
        "name": "Daisy Google",
        "avatar_url": "https://example.com/avatar.png",
    })
    assert google_res.status_code == 200
    token_data = google_res.json()
    assert token_data["user"]["email"] == "daisy.google@example.com"
    assert token_data["user"]["is_verified"] is True
    assert "access_token" in token_data

    # 3. Existing Google user verification (logs in without creating duplicate)
    existing_res = client.post(f"{settings.API_V1_STR}/auth/google/verify", json={
        "email": "daisy.google@example.com",
        "name": "Daisy Google",
    })
    assert existing_res.status_code == 200
    assert existing_res.json()["user"]["id"] == token_data["user"]["id"]
