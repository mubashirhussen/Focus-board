import os
import uuid
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.collaboration import Workspace
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
def auth_context(db_session: Session):
    unique_email = f"sec_prod_{uuid.uuid4().hex[:8]}@focusboard.enterprise"
    user = User(
        email=unique_email,
        name="Lead Security & Product Architect",
        hashed_password="hashed_pw_fixture",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    workspace = Workspace(
        name="SecProd Testing Workspace",
        description="Workspace for Phase 43-45 automated testing",
        owner_id=user.id,
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(workspace)

    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}, user, workspace

# ----------------- PHASE 43 TESTS -----------------
def test_security_posture_endpoint(auth_context):
    headers, user, _ = auth_context
    response = client.get("/api/v1/security-intelligence/posture", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "overall_posture_score" in data
    assert "category_scores" in data
    assert "mfa_adoption_pct" in data
    assert data["overall_posture_score"] >= 0 and data["overall_posture_score"] <= 100

def test_security_events_and_rule_detection(auth_context):
    headers, user, _ = auth_context
    payload = {
        "event_type": "LOGIN_SUCCESS",
        "severity": "INFO",
        "actor_email": user.email,
        "target_entity": "web_console",
        "source": "AUTH",
    }
    create_resp = client.post("/api/v1/security-intelligence/events", json=payload, headers=headers)
    assert create_resp.status_code == 201
    evt = create_resp.json()
    assert evt["event_type"] == "LOGIN_SUCCESS"
    assert evt["actor_email"] == user.email

    list_resp = client.get("/api/v1/security-intelligence/events?event_type=LOGIN_SUCCESS", headers=headers)
    assert list_resp.status_code == 200
    events = list_resp.json()
    assert len(events) >= 1

def test_detection_rules_and_alerts(auth_context, db_session: Session):
    headers, user, _ = auth_context
    rules_resp = client.get("/api/v1/security-intelligence/detection-rules", headers=headers)
    assert rules_resp.status_code == 200
    rules = rules_resp.json()
    assert len(rules) >= 1

    from app.models.security_intelligence import SecurityAlert
    alert = SecurityAlert(
        alert_code=f"TEST-ALT-{uuid.uuid4().hex[:6]}",
        title="Simulated Lateral Movement Attempt",
        description="Unauthorized access to internal artifact storage detected.",
        severity="HIGH",
        status="OPEN",
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    alert_id = alert.id

    patch_resp = client.patch(
        f"/api/v1/security-intelligence/alerts/{alert_id}",
        json={"status": "RESOLVED"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "RESOLVED"
    assert patch_resp.json()["resolved_at"] is not None

def test_access_reviews_campaign_and_decision(auth_context, db_session: Session):
    headers, user, _ = auth_context
    camp_payload = {
        "title": "Privileged Admin Role Audit",
        "scope_type": "PRIVILEGED_ROLES",
        "notes": "Verify all platform administrator permissions.",
    }
    camp_resp = client.post("/api/v1/security-intelligence/access-reviews", json=camp_payload, headers=headers)
    assert camp_resp.status_code == 201
    camp = camp_resp.json()
    camp_id = camp["id"]

    from app.models.security_intelligence import AccessReviewRecord
    rec = AccessReviewRecord(
        campaign_id=camp_id,
        user_id=user.id,
        role_or_permission="ROLE_PLATFORM_ADMIN",
        resource_name="Production Core API",
        decision="PENDING",
    )
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)
    rec_id = rec.id

    dec_resp = client.patch(
        f"/api/v1/security-intelligence/access-reviews/{camp_id}/records/{rec_id}",
        json={"decision": "APPROVED", "justification": "Verified role compliance."},
        headers=headers,
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["decision"] == "APPROVED"

def test_vulnerabilities_registry(auth_context):
    headers, user, _ = auth_context
    vuln_payload = {
        "cve_id": f"CVE-2026-{uuid.uuid4().hex[:4]}",
        "title": "Test Dependency Advisory",
        "description": "Prototype pollution in dev library.",
        "component": "tests/test_mock.js",
        "severity": "LOW",
        "source": "DEPENDENCY_SCAN",
        "remediation_status": "OPEN",
    }
    create_resp = client.post("/api/v1/security-intelligence/vulnerabilities", json=vuln_payload, headers=headers)
    assert create_resp.status_code == 201
    vuln_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/security-intelligence/vulnerabilities/{vuln_id}",
        json={"remediation_status": "RESOLVED"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["remediation_status"] == "RESOLVED"

def test_ai_security_assistant(auth_context):
    headers, user, _ = auth_context
    resp = client.post(
        "/api/v1/security-intelligence/ai/query",
        json={"query": "What is our current Zero-Trust posture score and top active alerts?"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "posture_score" in data
    assert "answer" in data
    assert "recommended_actions" in data
    assert "grounded_evidence" in data

# ----------------- PHASE 45 TESTS -----------------
def test_product_lifecycle_overview(auth_context):
    headers, user, _ = auth_context
    resp = client.get("/api/v1/product-lifecycle/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_discoveries" in data
    assert "total_ideas" in data
    assert "total_feature_requests" in data
    assert "active_experiments_count" in data

def test_product_discoveries_and_ideas(auth_context):
    headers, user, _ = auth_context
    disc_payload = {
        "title": "Offline-First Mobile Voice Dictation",
        "problem_statement": "Users on the go want to record tasks hands-free.",
        "hypothesis": "Voice capture will increase daily task creation by 25%.",
        "target_users": "Field Engineers and Mobile Professionals",
        "customer_segment": "ENTERPRISE",
        "business_impact": "High mobile conversion.",
        "customer_impact": "Fast hands-free entry.",
    }
    disc_resp = client.post("/api/v1/product-lifecycle/discoveries", json=disc_payload, headers=headers)
    assert disc_resp.status_code == 201
    disc_id = disc_resp.json()["id"]

    idea_payload = {
        "discovery_id": disc_id,
        "title": "On-Device Whisper STT Voice Processor",
        "description": "Local speech-to-text without cloud roundtrip latency.",
        "problem_statement": "Privacy concerns with transmitting audio transcripts.",
        "proposed_solution": "WebAssembly local speech transcription.",
        "product_area": "MOBILE_AI",
        "category": "PRODUCTIVITY",
        "priority": "HIGH",
    }
    idea_resp = client.post("/api/v1/product-lifecycle/ideas", json=idea_payload, headers=headers)
    assert idea_resp.status_code == 201
    assert idea_resp.json()["discovery_id"] == disc_id

def test_feature_requests_and_merge(auth_context):
    headers, user, _ = auth_context
    r1 = client.post(
        "/api/v1/product-lifecycle/feature-requests",
        json={
            "title": "Native Dark Mode Scheduling",
            "description": "Sync with sunrise/sunset.",
            "customer_name": "Alpha Corp",
            "request_count": 5,
            "revenue_impact": 20000.0,
        },
        headers=headers,
    ).json()

    r2 = client.post(
        "/api/v1/product-lifecycle/feature-requests",
        json={
            "title": "Auto Dark Mode at Night",
            "description": "Switch themes automatically based on clock.",
            "customer_name": "Beta LLC",
            "request_count": 3,
            "revenue_impact": 15000.0,
        },
        headers=headers,
    ).json()

    merge_resp = client.post(
        f"/api/v1/product-lifecycle/feature-requests/{r2['id']}/merge?target_id={r1['id']}",
        headers=headers,
    )
    assert merge_resp.status_code == 200
    merged = merge_resp.json()
    assert merged["request_count"] == 8
    assert merged["revenue_impact"] == 35000.0

def test_prioritization_calculation(auth_context):
    headers, user, _ = auth_context
    resp = client.post(
        "/api/v1/product-lifecycle/prioritization/calculate?reach=200&impact=4&confidence=0.8&effort=2&ease=3",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["rice_score"] == 320.0
    assert data["ice_score"] == 9.6
    assert "weighted_score" in data

def test_product_initiatives_and_roadmap(auth_context):
    headers, user, _ = auth_context
    init_payload = {
        "title": "Enterprise Collaboration Q2",
        "description": "Real-time canvas and multi-editor sync.",
        "strategic_objective": "Increase workspace retention.",
        "priority": "HIGH",
        "status": "IN_PROGRESS",
    }
    init_resp = client.post("/api/v1/product-lifecycle/initiatives", json=init_payload, headers=headers)
    assert init_resp.status_code == 201
    init_id = init_resp.json()["id"]

    item_payload = {
        "initiative_id": init_id,
        "title": "Live Collaborative Whiteboard Canvas",
        "description": "SVG interactive task board.",
        "product_area": "COLLABORATION",
        "quarter": "Q2-2027",
    }
    item_resp = client.post("/api/v1/product-lifecycle/roadmap", json=item_payload, headers=headers)
    assert item_resp.status_code == 201
    assert item_resp.json()["initiative_id"] == init_id

def test_experimentation_variant_assignment_and_events(auth_context):
    headers, user, _ = auth_context
    exp_payload = {
        "name": "Checkout CTA Color Test",
        "description": "Test blue vs green upgrade button conversion.",
        "hypothesis": "Green button yields 15% higher checkout completion.",
        "primary_metric": "checkout_completed",
        "variants": [
            {"variant_name": "Blue Button", "variant_key": "control_blue", "allocation_pct": 50.0},
            {"variant_name": "Green Button", "variant_key": "treatment_green", "allocation_pct": 50.0},
        ],
    }
    exp_resp = client.post("/api/v1/product-lifecycle/experiments", json=exp_payload, headers=headers)
    assert exp_resp.status_code == 201
    exp_id = exp_resp.json()["id"]

    assign_resp = client.post(f"/api/v1/product-lifecycle/experiments/{exp_id}/assign", headers=headers)
    assert assign_resp.status_code == 200
    variant = assign_resp.json()
    assert variant["variant_key"] in ["control_blue", "treatment_green"]

    evt_resp = client.post(
        f"/api/v1/product-lifecycle/experiments/{exp_id}/events?event_name=checkout_completed&metric_value=1.0",
        headers=headers,
    )
    assert evt_resp.status_code == 200
    assert evt_resp.json()["status"] == "recorded"

def test_ai_product_assistant(auth_context):
    headers, user, _ = auth_context
    resp = client.post(
        "/api/v1/product-lifecycle/ai/query",
        json={"query": "What are our top customer feature requests and active experiments?"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "total_discoveries" in data
    assert "total_feature_requests" in data
    assert "recommended_roadmap_actions" in data
    assert "grounded_evidence" in data
