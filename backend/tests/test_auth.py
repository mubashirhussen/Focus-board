import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_register_and_login_flow(client):
    # 1. Register
    reg_response = client.post(
        "/api/v1/auth/register",
        json={"name": "Alex Morgan", "email": "alex@example.com", "password": "password123"}
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "alex@example.com"
    assert "hashed_password" not in reg_data["user"]

    # 2. Duplicate registration rejected
    dup_response = client.post(
        "/api/v1/auth/register",
        json={"name": "Alex Morgan", "email": "alex@example.com", "password": "password123"}
    )
    assert dup_response.status_code == 400

    # 3. Login success
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    token = login_data["access_token"]
    assert token

    # 4. Login invalid credentials
    invalid_login = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@example.com", "password": "wrongpassword"}
    )
    assert invalid_login.status_code == 401

    # 5. Access /me with token
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["name"] == "Alex Morgan"
