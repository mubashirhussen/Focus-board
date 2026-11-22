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

def get_auth_token(client, email="push_tester@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Push Tester", "email": email, "password": "password123"},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

def test_vapid_public_key_retrieval(client):
    res = client.get("/api/v1/push/public-key")
    assert res.status_code == 200
    assert "public_key" in res.json()
    assert len(res.json()["public_key"]) > 10

def test_push_subscription_lifecycle_and_test_dispatch(client):
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Register subscription
    sub_res = client.post(
        "/api/v1/push/subscribe",
        json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/test_endpoint_mock_123",
            "p256dh": "mock_p256dh_key_data",
            "auth": "mock_auth_secret",
            "device_info": "Pixel 7 Chrome Mobile"
        },
        headers=headers
    )
    assert sub_res.status_code == 201
    assert sub_res.json()["is_active"] is True

    # 2. Test notification dispatch
    test_res = client.post(
        "/api/v1/push/test",
        json={"title": "FocusBoard PWA", "message": "Offline sync confirmed!"},
        headers=headers
    )
    assert test_res.status_code == 200
    assert test_res.json()["devices_notified"] >= 1

    # 3. Unsubscribe
    unsub_res = client.delete(
        "/api/v1/push/unsubscribe?endpoint=https://fcm.googleapis.com/fcm/send/test_endpoint_mock_123",
        headers=headers
    )
    assert unsub_res.status_code == 200
    assert unsub_res.json()["success"] is True
