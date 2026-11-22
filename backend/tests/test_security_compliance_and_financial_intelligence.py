import os
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def auth_headers(db_session: Session):
    unique_email = f"ciso_fin_{uuid.uuid4().hex[:8]}@focusboard.enterprise"
    user = User(
        email=unique_email,
        name="Chief Security & Finance Officer",
        hashed_password="hashed_pw_fixture",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}, user

def test_security_compliance_overview(auth_headers):
    headers, user = auth_headers
    resp = client.get("/api/v1/security/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_controls"] >= 10
    assert data["implemented_controls"] > 0
    assert data["overall_readiness_percentage"] > 0.0
    assert len(data["frameworks"]) >= 3
    framework_names = [f["framework"] for f in data["frameworks"]]
    assert "SOC2" in framework_names
    assert "ISO27001" in framework_names
    assert "GDPR" in framework_names
    assert data["approved_policies_count"] >= 3

def test_compliance_controls_and_evidence(auth_headers):
    headers, user = auth_headers
    # 1. List controls filtered by SOC2
    resp = client.get("/api/v1/security/controls?framework=SOC2", headers=headers)
    assert resp.status_code == 200
    controls = resp.json()
    assert len(controls) > 0
    soc2_ctrl = controls[0]

    # 2. Update control
    ctrl_id = soc2_ctrl["id"]
    update_payload = {
        "status": "IMPLEMENTED",
        "remediation_notes": "Automated regression verification and continuous token monitoring.",
    }
    update_resp = client.put(f"/api/v1/security/controls/{ctrl_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "IMPLEMENTED"

    # 3. Attach evidence
    evidence_payload = {
        "control_id": ctrl_id,
        "name": "AWS IAM Least-Privilege Audit Log Extract",
        "description": "Quarterly export validating zero root-account usage.",
        "evidence_type": "AUDIT_LOG",
        "file_url": "s3://focusboard-audit/aws_iam_2026_q1.json",
        "status": "VALIDATED",
    }
    evidence_resp = client.post(f"/api/v1/security/controls/{ctrl_id}/evidence", json=evidence_payload, headers=headers)
    assert evidence_resp.status_code == 201
    ev_data = evidence_resp.json()
    assert ev_data["control_id"] == ctrl_id
    assert ev_data["status"] == "VALIDATED"

    # 4. List evidence
    list_ev_resp = client.get(f"/api/v1/security/controls/{ctrl_id}/evidence", headers=headers)
    assert list_ev_resp.status_code == 200
    assert len(list_ev_resp.json()) >= 1

def test_security_policies_and_acknowledgment(auth_headers):
    headers, user = auth_headers
    # 1. List policies
    resp = client.get("/api/v1/security/policies", headers=headers)
    assert resp.status_code == 200
    policies = resp.json()
    assert len(policies) >= 3

    # 2. Create custom policy
    new_pol = {
        "policy_key": f"pol_ai_{uuid.uuid4().hex[:4]}",
        "title": "AI & Machine Learning Usage Policy",
        "category": "GOVERNANCE",
        "version": "1.0",
        "status": "APPROVED",
        "content": "# AI Governance\n\nNo sensitive customer PII shall be transmitted to non-enterprise AI endpoints.",
    }
    create_resp = client.post("/api/v1/security/policies", json=new_pol, headers=headers)
    assert create_resp.status_code == 201
    pol_id = create_resp.json()["id"]

    # 3. Acknowledge policy
    ack_resp = client.post(
        f"/api/v1/security/policies/{pol_id}/acknowledge",
        json={"version": "1.0"},
        headers=headers,
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["policy_id"] == pol_id
    assert ack_resp.json()["user_id"] == user.id

def test_security_risk_register(auth_headers):
    headers, user = auth_headers
    risk_payload = {
        "risk_code": f"RSK-TEST-{uuid.uuid4().hex[:4]}",
        "title": "Third-Party Webhook Downtime Risk",
        "description": "Upstream webhook latency may delay customer notification receipts.",
        "category": "APP_SEC",
        "severity": "HIGH",
        "likelihood": "CRITICAL",
        "impact": "HIGH",
        "mitigation_plan": "Implement exponential backoff retry queues and dead-letter channels.",
        "status": "IDENTIFIED",
    }
    create_resp = client.post("/api/v1/security/risks", json=risk_payload, headers=headers)
    assert create_resp.status_code == 201
    risk = create_resp.json()
    assert risk["risk_score"] == 12  # HIGH (3) * CRITICAL (4) = 12

    # Update risk
    risk_id = risk["id"]
    upd_resp = client.put(
        f"/api/v1/security/risks/{risk_id}",
        json={"severity": "LOW", "status": "IN_PROGRESS"},
        headers=headers,
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["risk_score"] == 4  # LOW (1) * CRITICAL (4) = 4
    assert upd_resp.json()["status"] == "IN_PROGRESS"

def test_security_incidents_lifecycle(auth_headers):
    headers, user = auth_headers
    inc_payload = {
        "incident_code": f"INC-TEST-{uuid.uuid4().hex[:4]}",
        "title": "Spike in Failed Authentication Requests",
        "summary": "Anomalous rate of 401s detected from single IP address range.",
        "severity": "HIGH",
        "category": "UNAUTHORIZED_ACCESS",
        "status": "DETECTED",
    }
    create_resp = client.post("/api/v1/security/incidents", json=inc_payload, headers=headers)
    assert create_resp.status_code == 201
    inc_id = create_resp.json()["id"]

    # Progress to RESOLVED
    res_resp = client.put(
        f"/api/v1/security/incidents/{inc_id}",
        json={
            "status": "RESOLVED",
            "root_cause": "Misconfigured staging client script looping expired tokens.",
            "corrective_actions": "IP temporarily rate-limited; updated client test credentials.",
        },
        headers=headers,
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"
    assert res_resp.json()["resolved_at"] is not None

def test_vendors_and_privacy_requests(auth_headers):
    headers, user = auth_headers
    # 1. Register vendor
    vendor_payload = {
        "name": "Datadog Observability",
        "service_type": "ANALYTICS",
        "data_classification": "INTERNAL",
        "risk_rating": "LOW",
        "security_contact": "security@datadoghq.com",
        "status": "ACTIVE",
    }
    v_resp = client.post("/api/v1/security/vendors", json=vendor_payload, headers=headers)
    assert v_resp.status_code == 201
    assert v_resp.json()["name"] == "Datadog Observability"

    # 2. Create Privacy Request
    pr_payload = {
        "request_type": "EXPORT",
        "requester_email": user.email,
        "details": "Customer GDPR Art. 20 Data Portability Request for workspace activity.",
    }
    pr_resp = client.post("/api/v1/security/privacy-requests", json=pr_payload, headers=headers)
    assert pr_resp.status_code == 201
    req_id = pr_resp.json()["id"]
    assert pr_resp.json()["request_type"] == "EXPORT"

    # 3. Update Privacy Request
    pr_upd = client.put(
        f"/api/v1/security/privacy-requests/{req_id}",
        json={"status": "COMPLETED", "details": "Export generated and delivered via secure portal link."},
        headers=headers,
    )
    assert pr_upd.status_code == 200
    assert pr_upd.json()["status"] == "COMPLETED"
    assert pr_upd.json()["completed_at"] is not None

def test_trust_center_public_posture():
    # Public endpoint without auth headers
    resp = client.get("/api/v1/security/trust/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    assert "TLS 1.3" in data["encryption_in_transit"]
    assert "AES-256" in data["encryption_at_rest"]
    assert data["soc2_readiness_percentage"] > 0.0
    assert len(data["public_documents"]) >= 2
    assert len(data["approved_subprocessors"]) >= 3

def test_financial_intelligence_overview_and_mrr(auth_headers):
    headers, user = auth_headers
    resp = client.get("/api/v1/finance/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_mrr"] > 0.0
    assert round(data["total_arr"], 1) == round(data["total_mrr"] * 12.0, 1)
    assert data["gross_revenue"] > 0.0
    assert data["finops"]["gross_margin_percentage"] > 50.0
    assert data["retention"]["gross_revenue_retention"] > 80.0
    assert data["retention"]["net_revenue_retention"] >= 90.0
    assert data["unit_economics"]["arpu"] > 0.0
    assert data["unit_economics"]["ltv_to_cac_ratio"] > 0.0
    assert len(data["active_budgets"]) > 0

def test_financial_transactions_and_costs(auth_headers):
    headers, user = auth_headers
    # 1. Record charge transaction
    tx_payload = {
        "tenant_id": "default",
        "transaction_type": "SUBSCRIPTION_PAYMENT",
        "amount_cents": 49900,  # $499.00
        "currency": "USD",
        "status": "SUCCEEDED",
        "description": "Enterprise Tier Annual Prepay",
    }
    tx_resp = client.post("/api/v1/finance/transactions", json=tx_payload, headers=headers)
    assert tx_resp.status_code == 201
    assert tx_resp.json()["amount"] == 499.00

    # 2. Record cost
    now = datetime.now(timezone.utc)
    cost_payload = {
        "tenant_id": "default",
        "category": "AI_TOKENS",
        "description": "Claude Sonnet Copilot Execution",
        "amount_cents": 8550,  # $85.50
        "currency": "USD",
        "billing_period": now.strftime("%Y-%m"),
    }
    cost_resp = client.post("/api/v1/finance/costs", json=cost_payload, headers=headers)
    assert cost_resp.status_code == 201
    assert cost_resp.json()["amount"] == 85.50

def test_financial_budgets_and_alert_threshold(auth_headers):
    headers, user = auth_headers
    budget_payload = {
        "tenant_id": "default",
        "category": "MARKETING",
        "budget_amount_cents": 50000,  # $500.00
        "currency": "USD",
        "period": "MONTHLY",
        "alert_threshold_percentage": 80.0,
        "status": "ACTIVE",
    }
    b_resp = client.post("/api/v1/finance/budgets", json=budget_payload, headers=headers)
    assert b_resp.status_code == 201
    budget_id = b_resp.json()["id"]

    # Update budget limit
    upd_resp = client.put(
        f"/api/v1/finance/budgets/{budget_id}",
        json={"budget_amount_cents": 60000, "alert_threshold_percentage": 85.0},
        headers=headers,
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["budget_amount"] == 600.0

def test_financial_forecasts_and_csv_export(auth_headers):
    headers, user = auth_headers
    # 1. List forecasts
    fc_resp = client.get("/api/v1/finance/forecasts", headers=headers)
    assert fc_resp.status_code == 200
    forecasts = fc_resp.json()
    assert len(forecasts) >= 3

    # 2. Export CSV report
    export_payload = {
        "report_type": "EXECUTIVE_SUMMARY",
        "format": "CSV",
    }
    exp_resp = client.post("/api/v1/finance/reports/export", json=export_payload, headers=headers)
    assert exp_resp.status_code == 200
    report_data = exp_resp.json()
    assert "focusboard_financial_executive_summary" in report_data["report_name"]
    assert "Total MRR" in report_data["content"]
    assert "Gross Margin %" in report_data["content"]
    assert "Customer Churn Rate" in report_data["content"]
