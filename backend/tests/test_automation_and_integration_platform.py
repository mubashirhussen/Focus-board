import os
import uuid
import json
import pytest
from datetime import datetime, timezone
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
    unique_email = f"automation_lead_{uuid.uuid4().hex[:8]}@focusboard.enterprise"
    user = User(
        email=unique_email,
        name="Automation & Ecosystem Architect",
        hashed_password="hashed_pw_fixture",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    workspace = Workspace(
        name="Automation Testing Workspace",
        description="Workspace for Phase 39-40 automated testing",
        owner_id=user.id,
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(workspace)

    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}, user, workspace


# ==============================================================================
# PHASE 39: AUTOMATION PLATFORM TESTS
# ==============================================================================

def test_automation_overview(auth_context):
    headers, _, workspace = auth_context
    resp = client.get(f"/api/v1/automation/overview?workspace_id={workspace.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_workflows_count"] >= 3  # Pre-seeded templates
    assert len(data["templates"]) >= 3
    assert "execution_success_rate" in data
    assert "estimated_hours_saved" in data


def test_workflow_crud_and_versioning(auth_context):
    headers, _, workspace = auth_context

    # 1. Create workflow
    payload = {
        "workspace_id": workspace.id,
        "name": "Sprint Overdue Guard",
        "description": "Automatically alerts on overdue sprint tasks and logs audit entry",
        "workflow_type": "EVENT_DRIVEN",
        "status": "ACTIVE",
        "trigger_type": "EVENT",
        "trigger_config_json": json.dumps({"event": "task.overdue"}),
        "nodes_json": json.dumps([
            {"id": "node_1", "type": "trigger", "name": "Task Overdue Trigger", "config": {"event": "task.overdue"}},
            {"id": "node_2", "type": "condition", "name": "Priority Filter", "config": {"field": "priority", "operator": "EQUALS", "value": "HIGH"}},
            {"id": "node_3", "type": "action", "name": "Send SLA Warning", "config": {"action_type": "notification.send", "title": "Overdue Warning", "message": "High priority task overdue"}},
            {"id": "node_4", "type": "end", "name": "End Workflow", "config": {}}
        ]),
        "edges_json": json.dumps([
            {"source": "node_1", "target": "node_2"},
            {"source": "node_2", "target": "node_3", "condition_branch": "true"},
            {"source": "node_3", "target": "node_4"},
            {"source": "node_2", "target": "node_4", "condition_branch": "false"}
        ]),
        "variables_json": json.dumps({"escalation_tier": "P1"}),
        "execution_settings_json": json.dumps({"max_retries": 2, "timeout_seconds": 30, "error_policy": "STOP"}),
        "version": "1.0",
        "is_template": False,
    }

    resp = client.post("/api/v1/automation/workflows", headers=headers, json=payload)
    assert resp.status_code == 201
    created_wf = resp.json()
    wf_id = created_wf["id"]
    assert created_wf["name"] == "Sprint Overdue Guard"
    assert created_wf["version"] == "1.0"

    # 2. Get workflow by ID
    resp = client.get(f"/api/v1/automation/workflows/{wf_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == wf_id

    # 3. Update workflow (version increment)
    update_payload = {
        "description": "Updated sprint overdue workflow description",
        "nodes_json": json.dumps([
            {"id": "node_1", "type": "trigger", "name": "Task Overdue Trigger", "config": {"event": "task.overdue"}},
            {"id": "node_2", "type": "condition", "name": "Priority Filter", "config": {"field": "priority", "operator": "EQUALS", "value": "HIGH"}},
            {"id": "node_3", "type": "action", "name": "Send Urgent Notification", "config": {"action_type": "notification.send", "title": "Urgent Alert", "message": "Critical task overdue"}},
            {"id": "node_4", "type": "end", "name": "End Workflow", "config": {}}
        ]),
        "change_summary": "Renamed action node and altered message",
    }
    resp = client.patch(f"/api/v1/automation/workflows/{wf_id}", headers=headers, json=update_payload)
    assert resp.status_code == 200
    updated_wf = resp.json()
    assert updated_wf["version"] == "1.1"

    # 4. Check versions history
    resp = client.get(f"/api/v1/automation/workflows/{wf_id}/versions", headers=headers)
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2
    assert versions[0]["version"] == "1.1"


def test_workflow_execution_and_condition_evaluation(auth_context):
    headers, _, workspace = auth_context

    # Create a test workflow
    payload = {
        "workspace_id": workspace.id,
        "name": "Condition Test Workflow",
        "description": "Tests deterministic condition branching",
        "workflow_type": "EVENT_DRIVEN",
        "status": "ACTIVE",
        "trigger_type": "EVENT",
        "trigger_config_json": json.dumps({"event": "task.created"}),
        "nodes_json": json.dumps([
            {"id": "n1", "type": "trigger", "name": "Trigger", "config": {"event": "task.created"}},
            {"id": "n2", "type": "condition", "name": "Check Priority High", "config": {"field": "priority", "operator": "EQUALS", "value": "HIGH"}},
            {"id": "n3", "type": "action", "name": "Notify High Priority", "config": {"action_type": "notification.send", "title": "High Priority Task", "message": "Task {{title}} created"}},
            {"id": "n4", "type": "end", "name": "Finish", "config": {}}
        ]),
        "edges_json": json.dumps([
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3", "condition_branch": "true"},
            {"source": "n3", "target": "n4"},
            {"source": "n2", "target": "n4", "condition_branch": "false"}
        ]),
        "version": "1.0",
    }
    resp = client.post("/api/v1/automation/workflows", headers=headers, json=payload)
    assert resp.status_code == 201
    wf_id = resp.json()["id"]

    # 1. Trigger with matching condition (priority = HIGH)
    exec_resp = client.post(
        f"/api/v1/automation/workflows/{wf_id}/trigger",
        headers=headers,
        json={
            "trigger_event": "task.created",
            "payload": {"title": "Fix Critical Outage", "priority": "HIGH"},
            "dry_run": False,
        }
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["status"] == "COMPLETED"

    # Verify logs
    log_resp = client.get(f"/api/v1/automation/executions/{execution['id']}/logs", headers=headers)
    assert log_resp.status_code == 200
    logs = log_resp.json()
    node_ids = [l["node_id"] for l in logs]
    assert "n1" in node_ids
    assert "n2" in node_ids
    assert "n3" in node_ids  # True branch taken
    assert "n4" in node_ids

    # 2. Trigger with non-matching condition (priority = LOW)
    exec_resp_false = client.post(
        f"/api/v1/automation/workflows/{wf_id}/trigger",
        headers=headers,
        json={
            "trigger_event": "task.created",
            "payload": {"title": "Update Footer Text", "priority": "LOW"},
            "dry_run": False,
        }
    )
    assert exec_resp_false.status_code == 200
    execution_false = exec_resp_false.json()
    assert execution_false["status"] == "COMPLETED"

    # Verify logs for false branch
    log_resp_false = client.get(f"/api/v1/automation/executions/{execution_false['id']}/logs", headers=headers)
    assert log_resp_false.status_code == 200
    logs_false = log_resp_false.json()
    node_ids_false = [l["node_id"] for l in logs_false]
    assert "n2" in node_ids_false
    assert "n3" not in node_ids_false  # False branch skipped action!
    assert "n4" in node_ids_false


def test_human_in_the_loop_approval_flow(auth_context):
    headers, _, workspace = auth_context

    # Create workflow with approval node
    payload = {
        "workspace_id": workspace.id,
        "name": "High Value Disbursement Approval",
        "description": "Workflow pausing for human review",
        "workflow_type": "APPROVAL_CHAIN",
        "status": "ACTIVE",
        "trigger_type": "EVENT",
        "trigger_config_json": json.dumps({"event": "budget.exceeded"}),
        "nodes_json": json.dumps([
            {"id": "a1", "type": "trigger", "name": "Budget Alert", "config": {"event": "budget.exceeded"}},
            {"id": "a2", "type": "approval", "name": "Manager Approval Required", "config": {"approval_type": "FINANCIAL_DISBURSEMENT", "title": "Approve Out-of-budget Expense", "description": "Expense exceeds $5,000 threshold"}},
            {"id": "a3", "type": "action", "name": "Create Approved Record", "config": {"action_type": "task.create", "title": "Process Approved Budget Line"}},
            {"id": "a4", "type": "end", "name": "Done", "config": {}}
        ]),
        "edges_json": json.dumps([
            {"source": "a1", "target": "a2"},
            {"source": "a2", "target": "a3"},
            {"source": "a3", "target": "a4"}
        ]),
        "version": "1.0",
    }
    resp = client.post("/api/v1/automation/workflows", headers=headers, json=payload)
    assert resp.status_code == 201
    wf_id = resp.json()["id"]

    # Trigger execution - should pause on approval node
    exec_resp = client.post(
        f"/api/v1/automation/workflows/{wf_id}/trigger",
        headers=headers,
        json={"trigger_event": "budget.exceeded", "payload": {"amount": 7500, "project": "Cloud Infrastructure"}},
    )
    assert exec_resp.status_code == 200
    execution = exec_resp.json()
    assert execution["status"] == "REQUIRES_APPROVAL"

    # List pending approvals
    appr_resp = client.get(f"/api/v1/automation/approvals?execution_id={execution['id']}", headers=headers)
    assert appr_resp.status_code == 200
    approvals = appr_resp.json()
    assert len(approvals) == 1
    approval = approvals[0]
    assert approval["status"] == "PENDING"
    assert approval["approval_type"] == "FINANCIAL_DISBURSEMENT"

    # Process decision: APPROVE
    dec_resp = client.post(
        f"/api/v1/automation/approvals/{approval['id']}/decision",
        headers=headers,
        json={"decision": "APPROVED", "comments": "Approved after reviewing vendor agreement"}
    )
    assert dec_resp.status_code == 200
    dec_data = dec_resp.json()
    assert dec_data["status"] == "APPROVED"

    # Verify execution resumed and completed
    exec_final = client.get(f"/api/v1/automation/executions/{execution['id']}", headers=headers).json()
    assert exec_final["status"] == "COMPLETED"


def test_ai_workflow_assistant_generate(auth_context):
    headers, _, _ = auth_context
    resp = client.post(
        "/api/v1/automation/assistant/generate",
        headers=headers,
        json={
            "prompt": "When a task becomes overdue, notify the project manager and create a high priority review task.",
            "category": "TASK",
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["workflow_name"] != ""
    assert data["trigger_type"] == "EVENT"
    assert len(data["nodes"]) >= 3
    assert len(data["edges"]) >= 2
    assert "explanation" in data


# ==============================================================================
# PHASE 40: INTEGRATION ECOSYSTEM & DEVELOPER PLATFORM TESTS
# ==============================================================================

def test_integration_providers_catalog(auth_context):
    headers, _, _ = auth_context
    resp = client.get("/api/v1/integration-platform/providers", headers=headers)
    assert resp.status_code == 200
    providers = resp.json()

    provider_ids = [p["id"] for p in providers]
    assert "google_calendar" in provider_ids
    assert "slack" in provider_ids
    assert "github" in provider_ids
    assert "linear" in provider_ids
    assert "webhook" in provider_ids


def test_marketplace_listings_and_installation(auth_context):
    headers, _, workspace = auth_context

    # 1. List listings
    resp = client.get("/api/v1/integration-platform/marketplace/listings", headers=headers)
    assert resp.status_code == 200
    listings = resp.json()
    assert len(listings) >= 3
    target_listing = listings[0]

    # 2. Install listing with granted permissions consent
    install_payload = {
        "listing_id": target_listing["id"],
        "workspace_id": workspace.id,
        "consent_confirmed": True,
        "granted_scopes": ["tasks:read", "tasks:write", "webhooks:read"],
    }
    resp = client.post("/api/v1/integration-platform/marketplace/install", headers=headers, json=install_payload)
    assert resp.status_code == 201
    installation = resp.json()
    assert installation["workspace_id"] == workspace.id
    assert installation["status"] == "ACTIVE"
    assert "tasks:read" in installation["granted_scopes_json"]

    # 3. List workspace installations
    resp = client.get(f"/api/v1/integration-platform/marketplace/installations?workspace_id={workspace.id}", headers=headers)
    assert resp.status_code == 200
    inst_list = resp.json()
    assert len(inst_list) >= 1
    assert inst_list[0]["id"] == installation["id"]


def test_oauth_connectors_lifecycle(auth_context):
    headers, _, workspace = auth_context

    # 1. Connect OAuth Provider
    resp = client.post(
        f"/api/v1/integration-platform/connectors/connect?provider_id=slack&workspace_id={workspace.id}&account_identifier=focusboard-ops-team",
        headers=headers,
    )
    assert resp.status_code == 200
    connector = resp.json()
    assert connector["connection_status"] == "CONNECTED"
    assert connector["account_identifier"] == "focusboard-ops-team"

    # 2. List connectors
    resp = client.get(f"/api/v1/integration-platform/connectors?workspace_id={workspace.id}", headers=headers)
    assert resp.status_code == 200
    connectors = resp.json()
    assert any(c["id"] == connector["id"] and c["connection_status"] == "CONNECTED" for c in connectors)

    # 3. Disconnect connector
    resp = client.post(f"/api/v1/integration-platform/connectors/{connector['id']}/disconnect", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Connector disconnected successfully"

    # Verify status changed to DISCONNECTED
    resp = client.get(f"/api/v1/integration-platform/connectors?workspace_id={workspace.id}", headers=headers)
    updated = [c for c in resp.json() if c["id"] == connector["id"]][0]
    assert updated["connection_status"] == "DISCONNECTED"


def test_webhook_delivery_hmac_signature(auth_context):
    headers, _, _ = auth_context
    payload = {
        "target_url": "https://api.partner.example.com/webhooks/focusboard",
        "secret_key": "sec_prod_signature_key_987654321",
        "event_type": "task.created",
    }
    resp = client.post("/api/v1/integration-platform/webhooks/test", headers=headers, json=payload)
    assert resp.status_code == 200
    res = resp.json()

    assert res["is_delivered"] is True
    assert res["status_code"] == 200
    assert res["signature_header"].startswith("t=")
    assert ",v1=" in res["signature_header"]
    assert res["duration_ms"] >= 0


def test_api_platform_analytics(auth_context):
    headers, _, _ = auth_context
    resp = client.get("/api/v1/integration-platform/analytics", headers=headers)
    assert resp.status_code == 200
    analytics = resp.json()

    assert "total_requests" in analytics
    assert "avg_response_time_ms" in analytics
    assert "active_api_keys_count" in analytics
    assert "active_webhooks_count" in analytics
    assert "webhook_delivery_success_rate" in analytics
    assert len(analytics["top_endpoints"]) > 0
