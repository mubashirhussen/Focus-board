import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.services.entitlement_service import seed_default_plans, check_entitlement, record_usage

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
    seed_default_plans(db)
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

def get_auth_token(client, email="billing_tester@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Billing Tester", "email": email, "password": "password123"},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

def test_get_plans_catalog(client):
    res = client.get("/api/v1/billing/plans")
    assert res.status_code == 200
    plans = res.json()
    assert len(plans) >= 5
    slugs = [p["slug"] for p in plans]
    assert "free" in slugs
    assert "starter" in slugs
    assert "pro" in slugs
    assert "team" in slugs
    assert "enterprise" in slugs

def test_tenant_default_subscription_and_checkout(client):
    token = get_auth_token(client, "sub_user@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Default subscription should be Free
    res_sub = client.get("/api/v1/billing/subscription", headers=headers)
    assert res_sub.status_code == 200
    data = res_sub.json()
    assert data["plan"]["slug"] == "free"
    assert data["status"] == "active"

    # Checkout session creation for Pro plan
    plans_res = client.get("/api/v1/billing/plans")
    pro_plan = next(p for p in plans_res.json() if p["slug"] == "pro")

    checkout_res = client.post(
        "/api/v1/billing/checkout",
        json={"plan_id": pro_plan["id"]},
        headers=headers
    )
    assert checkout_res.status_code == 200
    checkout_data = checkout_res.json()
    assert "checkout_url" in checkout_data
    assert "session_id" in checkout_data

def test_plan_switch_and_cancel_lifecycle(client):
    token = get_auth_token(client, "switch_user@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    plans_res = client.get("/api/v1/billing/plans")
    team_plan = next(p for p in plans_res.json() if p["slug"] == "team")

    # Switch to Team plan
    switch_res = client.post(
        "/api/v1/billing/change-plan",
        json={"plan_id": team_plan["id"]},
        headers=headers
    )
    assert switch_res.status_code == 200
    assert switch_res.json()["plan"]["slug"] == "team"

    # Cancel subscription
    cancel_res = client.post("/api/v1/billing/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["cancel_at_period_end"] is True

def test_usage_tracking_and_quota_enforcement(client):
    token = get_auth_token(client, "usage_user@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    usage_res = client.get("/api/v1/billing/usage", headers=headers)
    assert usage_res.status_code == 200
    usage_data = usage_res.json()
    assert "ai_requests" in usage_data["metrics"]
    assert usage_data["metrics"]["ai_requests"]["limit"] == 15
