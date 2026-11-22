import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.services.mfa_service import generate_totp_code

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

def get_auth_token(client, email="admin@enterprise.com", role="Owner"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Enterprise Owner", "email": email, "password": "securepassword123", "role": role},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

def test_enterprise_policies_and_rbac(client):
    token = get_auth_token(client, "owner@corp.com", "Owner")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Retrieve default policies
    pol_res = client.get("/api/v1/enterprise/policies", headers=headers)
    assert pol_res.status_code == 200
    policies = pol_res.json()
    assert "mfa_required" in policies
    assert "domain_restriction" in policies

    # 2. Update a policy
    update_res = client.put(
        "/api/v1/enterprise/policies/mfa_required",
        json={"policy_value": {"enabled": True, "grace_period_days": 7}},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "policy_updated"

def test_custom_roles_creation_and_listing(client):
    token = get_auth_token(client, "lead@corp.com", "Owner")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    create_res = client.post(
        "/api/v1/enterprise/roles",
        json={
            "name": "SecurityAuditor",
            "description": "Read-only access to audit logs and policies",
            "permissions": ["organization.view", "organization.view_audit_logs"]
        },
        headers=headers
    )
    assert create_res.status_code == 201
    assert create_res.json()["name"] == "SecurityAuditor"

    roles_res = client.get("/api/v1/enterprise/roles", headers=headers)
    assert roles_res.status_code == 200
    assert any(r["name"] == "SecurityAuditor" for r in roles_res.json())

def test_domain_verification_flow(client):
    token = get_auth_token(client, "it@corp.com", "Owner")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Add domain
    add_res = client.post("/api/v1/enterprise/domains", json={"domain": "corp.com"}, headers=headers)
    assert add_res.status_code == 201
    d_id = add_res.json()["id"]
    assert add_res.json()["is_verified"] is False

    # Verify domain
    ver_res = client.post(f"/api/v1/enterprise/domains/{d_id}/verify", headers=headers)
    assert ver_res.status_code == 200
    assert ver_res.json()["is_verified"] is True

def test_totp_mfa_setup_and_verification(client):
    token = get_auth_token(client, "mfa_user@corp.com", "Member")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Setup MFA
    setup_res = client.post("/api/v1/enterprise/mfa/setup", headers=headers)
    assert setup_res.status_code == 200
    setup_data = setup_res.json()
    secret = setup_data["secret"]
    recovery_codes = setup_data["recovery_codes"]
    assert len(recovery_codes) == 8

    # 2. Verify with valid TOTP code
    code = generate_totp_code(secret)
    ver_res = client.post("/api/v1/enterprise/mfa/verify", json={"code": code}, headers=headers)
    assert ver_res.status_code == 200
    assert ver_res.json()["status"] == "mfa_enabled"

    # 3. Disable using recovery code
    dis_res = client.post("/api/v1/enterprise/mfa/disable", json={"code": recovery_codes[0]}, headers=headers)
    assert dis_res.status_code == 200
    assert dis_res.json()["status"] == "mfa_disabled"

def test_compliance_audit_export(client):
    token = get_auth_token(client, "auditor@corp.com", "Owner")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    export_res = client.get("/api/v1/enterprise/audit-logs/export", headers=headers)
    assert export_res.status_code == 200
    assert export_res.headers["Content-Type"].startswith("text/csv")
    csv_text = export_res.text
    assert "Event ID" in csv_text
    assert "Actor ID" in csv_text
