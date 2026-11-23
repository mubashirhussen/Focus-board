import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import uuid
import hmac
import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.session import SessionLocal
from app.models.task import Task
from app.models.integration import (
    ExternalIntegration,
    IntegrationEntityMapping,
    IntegrationSyncJob,
    SyncLog,
)
from app.models.developer_platform import WebhookSubscription
from app.services.integration_service import (
    encrypt_credential,
    decrypt_credential,
    generate_oauth_state,
    verify_oauth_state,
    is_safe_external_url,
    deliver_outbound_webhook,
)

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b16_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "IntegrationPass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"Integration User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

def create_test_workspace(client, headers, name="Integration Workspace"):
    res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Workspace for B16 testing"},
        headers=headers,
    )
    assert res.status_code in [200, 201], res.text
    return res.json()["id"]

# ------------------------------------------------------------------------------
# 1. Integration Catalog & Provider Details
# ------------------------------------------------------------------------------
def test_integration_catalog_and_details(client):
    headers, user_id, _ = get_auth_headers(client, "catalog_user")

    # 1. Fetch available catalog
    res = client.get(f"{settings.API_V1_STR}/integrations/available", headers=headers)
    assert res.status_code == 200
    catalog = res.json()
    assert isinstance(catalog, list)
    assert len(catalog) >= 5

    providers = {item["provider"]: item for item in catalog}
    assert "google_calendar" in providers
    assert "slack" in providers
    assert "github" in providers
    assert "jira" in providers

    # Verify features and scopes
    gcal = providers["google_calendar"]
    assert gcal["auth_type"] == "OAUTH2"
    assert gcal["category"] == "Calendar"
    assert "two_way_calendar_sync" in gcal["supported_features"]
    assert gcal["is_connected"] is False

    # 2. Filter by category
    res_cat = client.get(f"{settings.API_V1_STR}/integrations/available?category=Calendar", headers=headers)
    assert res_cat.status_code == 200
    cat_items = res_cat.json()
    assert all(item["category"] == "Calendar" for item in cat_items)
    assert any(item["provider"] == "google_calendar" for item in cat_items)

    # 3. Provider details endpoint
    res_detail = client.get(f"{settings.API_V1_STR}/integrations/providers/slack", headers=headers)
    assert res_detail.status_code == 200
    slack_data = res_detail.json()
    assert slack_data["provider"] == "slack"
    assert slack_data["category"] == "Communication"
    assert "channel_messaging" in slack_data["supported_features"]

    # 4. Unknown provider 404
    res_404 = client.get(f"{settings.API_V1_STR}/integrations/providers/non_existent_provider", headers=headers)
    assert res_404.status_code == 404

# ------------------------------------------------------------------------------
# 2. OAuth Handshake Initiation & CSRF State Signing
# ------------------------------------------------------------------------------
def test_oauth_authorization_initiation_and_csrf_state(client):
    headers, user_id, _ = get_auth_headers(client, "oauth_init")

    # 1. Google Calendar connect initiation
    res = client.get(
        f"{settings.API_V1_STR}/integrations/google_calendar/connect?redirect_uri=http://localhost:5173/integrations/callback",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "authorization_url" in data
    assert "state" in data
    assert "accounts.google.com" in data["authorization_url"]

    # 2. Verify state cryptographic signature and embedded claims
    state = data["state"]
    verified = verify_oauth_state(state)
    assert verified["user_id"] == user_id
    assert verified["provider"] == "google_calendar"
    assert abs(verified["ts"] - int(datetime.now(timezone.utc).timestamp())) < 10

    # 3. Slack and GitHub OAuth initiation
    slack_res = client.get(f"{settings.API_V1_STR}/integrations/slack/connect", headers=headers)
    assert slack_res.status_code == 200
    assert "slack.com/oauth" in slack_res.json()["authorization_url"]

    github_res = client.get(f"{settings.API_V1_STR}/integrations/github/connect", headers=headers)
    assert github_res.status_code == 200
    assert "github.com/login/oauth/authorize" in github_res.json()["authorization_url"]

# ------------------------------------------------------------------------------
# 3. OAuth Callback, Credential Encryption & Response Masking
# ------------------------------------------------------------------------------
def test_oauth_callback_and_credential_encryption(client):
    headers, user_id, _ = get_auth_headers(client, "oauth_cb")

    # 1. Initiate OAuth to get valid signed state
    init_res = client.get(f"{settings.API_V1_STR}/integrations/slack/connect", headers=headers)
    state = init_res.json()["state"]

    # 2. Simulate external OAuth callback
    cb_res = client.get(
        f"{settings.API_V1_STR}/integrations/slack/callback?code=mock_slack_auth_code_123&state={state}",
        headers=headers,
    )
    assert cb_res.status_code == 200
    integ = cb_res.json()
    assert integ["provider"] == "slack"
    assert integ["status"] == "connected"
    assert integ["health_status"] == "HEALTHY"
    integration_id = integ["id"]

    # 3. Verify in database that credentials are encrypted at rest
    db = SessionLocal()
    try:
        db_integ = db.query(ExternalIntegration).filter(ExternalIntegration.id == integration_id).first()
        assert db_integ is not None
        assert db_integ.access_token is not None
        assert db_integ.access_token.startswith("enc:v1:")  # Encrypted at rest
        assert db_integ.refresh_token is not None
        assert db_integ.refresh_token.startswith("enc:v1:")

        # Decrypt credential
        clear_tok = decrypt_credential(db_integ.access_token)
        assert "slack_live_tok_" in clear_tok
    finally:
        db.close()

    # 4. Verify catalog now reflects is_connected = True for Slack
    res_avail = client.get(f"{settings.API_V1_STR}/integrations/available", headers=headers)
    avail_map = {i["provider"]: i for i in res_avail.json()}
    assert avail_map["slack"]["is_connected"] is True

# ------------------------------------------------------------------------------
# 4. OAuth State Tamper Protection & Expiration
# ------------------------------------------------------------------------------
def test_oauth_state_expiration_and_tamper_protection(client):
    headers_a, user_a_id, _ = get_auth_headers(client, "user_a")
    headers_b, user_b_id, _ = get_auth_headers(client, "user_b")

    # 1. Valid state generated for User A
    init_res = client.get(f"{settings.API_V1_STR}/integrations/github/connect", headers=headers_a)
    valid_state = init_res.json()["state"]

    # Tampered state signature
    tampered_state = valid_state[:-4] + "ffff"
    tamper_res = client.get(
        f"{settings.API_V1_STR}/integrations/github/callback?code=code123&state={tampered_state}",
        headers=headers_a,
    )
    assert tamper_res.status_code == 400
    assert "Invalid OAuth state signature" in tamper_res.json()["detail"]

    # Valid state of User A used by User B -> 403 Forbidden
    cross_res = client.get(
        f"{settings.API_V1_STR}/integrations/github/callback?code=code123&state={valid_state}",
        headers=headers_b,
    )
    assert cross_res.status_code == 403

    # Expired state
    import base64
    expired_ts = int(time.time()) - 1000  # 1000s ago (> 600s ttl)
    raw_claims = f"{user_a_id}:0:github:{expired_ts}:{uuid.uuid4().hex[:12]}"
    secret = settings.SECRET_KEY.encode("utf-8")
    sig = hmac.new(secret, raw_claims.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    state_payload = base64.urlsafe_b64encode(raw_claims.encode("utf-8")).decode("utf-8")
    expired_state = f"{state_payload}.{sig}"

    exp_res = client.get(
        f"{settings.API_V1_STR}/integrations/github/callback?code=code123&state={expired_state}",
        headers=headers_a,
    )
    assert exp_res.status_code == 400
    assert "OAuth state has expired" in exp_res.json()["detail"]

# ------------------------------------------------------------------------------
# 5. API-Key Integration Lifecycle (Connect, Test, Health, Disconnect)
# ------------------------------------------------------------------------------
def test_api_key_integration_lifecycle(client):
    headers, user_id, _ = get_auth_headers(client, "apikey_user")
    ws_id = create_test_workspace(client, headers, "APIKey WS")

    # 1. Connect Jira with API Token
    connect_payload = {
        "provider": "jira",
        "api_key": "jira_api_token_secret_live_xyz",
        "account_identifier": "devops@focusboard.io",
        "base_url": "https://focusboard.atlassian.net",
        "workspace_id": ws_id,
        "config": {"default_project_key": "FB", "sync_epics": True},
    }
    con_res = client.post(
        f"{settings.API_V1_STR}/integrations/api-key/connect",
        json=connect_payload,
        headers=headers,
    )
    assert con_res.status_code == 201
    integ = con_res.json()
    assert integ["provider"] == "jira"
    assert integ["status"] == "connected"
    assert integ["health_status"] == "HEALTHY"
    integration_id = integ["id"]

    # Verify encrypted storage
    db = SessionLocal()
    try:
        db_rec = db.query(ExternalIntegration).filter(ExternalIntegration.id == integration_id).first()
        assert db_rec.access_token.startswith("enc:v1:")
        assert decrypt_credential(db_rec.access_token) == "jira_api_token_secret_live_xyz"
    finally:
        db.close()

    # 2. Test Connection
    test_res = client.post(f"{settings.API_V1_STR}/integrations/{integration_id}/test", headers=headers)
    assert test_res.status_code == 200
    test_data = test_res.json()
    assert test_data["is_healthy"] is True
    assert test_data["provider"] == "jira"
    assert test_data["latency_ms"] >= 0

    # 3. Get Health
    health_res = client.get(f"{settings.API_V1_STR}/integrations/{integration_id}/health", headers=headers)
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["health_status"] == "HEALTHY"
    assert health_data["token_valid"] is True

    # 4. Reconnect
    rec_res = client.post(f"{settings.API_V1_STR}/integrations/{integration_id}/reconnect", headers=headers)
    assert rec_res.status_code == 200
    assert rec_res.json()["health_status"] == "HEALTHY"

    # 5. Disconnect
    del_res = client.delete(f"{settings.API_V1_STR}/integrations/{integration_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Integration successfully disconnected"

    # Verify deleted
    get_res = client.get(f"{settings.API_V1_STR}/integrations/{integration_id}/health", headers=headers)
    assert get_res.status_code == 404

# ------------------------------------------------------------------------------
# 6. Synchronization Engine: Google Calendar
# ------------------------------------------------------------------------------
def test_synchronization_engine_google_calendar(client):
    headers, user_id, _ = get_auth_headers(client, "sync_gcal_user")
    ws_id = create_test_workspace(client, headers, "GCal WS")

    # Create local tasks with due dates in DB
    db = SessionLocal()
    try:
        t1_id = f"task_{uuid.uuid4().hex[:12]}"
        t2_id = f"task_{uuid.uuid4().hex[:12]}"
        task1 = Task(
            id=t1_id,
            title="Design Quarterly Roadmap Review",
            description="Prepare slide deck and strategy",
            user_id=user_id,
            workspace_id=ws_id,
            priority="HIGH",
            status="IN_PROGRESS",
            due_date=(datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        )
        task2 = Task(
            id=t2_id,
            title="Security Audit & Remediation",
            description="Review OAuth flows and credentials",
            user_id=user_id,
            workspace_id=ws_id,
            priority="URGENT",
            status="TODO",
            due_date=(datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        )
        db.add_all([task1, task2])
        db.commit()
        db.refresh(task1)
        db.refresh(task2)
        task1_id = task1.id
        task2_id = task2.id
    finally:
        db.close()

    # Connect Google Calendar
    init_res = client.get(f"{settings.API_V1_STR}/integrations/google_calendar/connect", headers=headers)
    cb_res = client.get(
        f"{settings.API_V1_STR}/integrations/google_calendar/callback?code=mock_code&state={init_res.json()['state']}",
        headers=headers,
    )
    integ_id = cb_res.json()["id"]

    # Trigger manual sync
    sync_req = {
        "sync_type": "INCREMENTAL",
        "direction": "BIDIRECTIONAL",
        "conflict_resolution": "LATEST_UPDATE_WINS"
    }
    sync_res = client.post(f"{settings.API_V1_STR}/integrations/{integ_id}/sync", json=sync_req, headers=headers)
    assert sync_res.status_code == 200
    job = sync_res.json()
    assert job["status"] == "COMPLETED"
    assert job["records_synced"] >= 2
    assert job["direction"] == "BIDIRECTIONAL"

    # Verify entity mappings created
    map_res = client.get(f"{settings.API_V1_STR}/integrations/{integ_id}/mappings", headers=headers)
    assert map_res.status_code == 200
    mappings = map_res.json()
    assert len(mappings) >= 2
    mapped_internal_ids = {m["internal_id"] for m in mappings}
    assert str(task1_id) in mapped_internal_ids
    assert str(task2_id) in mapped_internal_ids

    # Verify sync history
    hist_res = client.get(f"{settings.API_V1_STR}/integrations/{integ_id}/sync-history", headers=headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) >= 1
    assert hist[0]["id"] == job["id"]

    # Verify sync audit logs
    logs_res = client.get(f"{settings.API_V1_STR}/integrations/{integ_id}/sync-logs", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) >= 1
    assert any("SUCCESS" in log["status"] for log in logs)

# ------------------------------------------------------------------------------
# 7. Synchronization Engine: GitHub Issues & Jira
# ------------------------------------------------------------------------------
def test_synchronization_engine_github_and_jira(client):
    headers, user_id, _ = get_auth_headers(client, "sync_git_jira")

    # 1. Connect GitHub
    git_init = client.get(f"{settings.API_V1_STR}/integrations/github/connect", headers=headers)
    git_cb = client.get(
        f"{settings.API_V1_STR}/integrations/github/callback?code=mock_git_code&state={git_init.json()['state']}",
        headers=headers,
    )
    git_integ_id = git_cb.json()["id"]

    # Outbound sync to GitHub
    sync_res = client.post(
        f"{settings.API_V1_STR}/integrations/{git_integ_id}/sync",
        json={"sync_type": "FULL", "direction": "OUTBOUND", "conflict_resolution": "INTERNAL_WINS"},
        headers=headers,
    )
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "COMPLETED"

    # Verify GitHub entity mappings
    mappings = client.get(f"{settings.API_V1_STR}/integrations/{git_integ_id}/mappings", headers=headers).json()
    assert any(m["entity_type"] == "issue" for m in mappings)

    # 2. Connect Jira via API Key
    jira_con = client.post(
        f"{settings.API_V1_STR}/integrations/api-key/connect",
        json={"provider": "jira", "api_key": "jira_key_abc", "account_identifier": "lead@focusboard.io"},
        headers=headers,
    )
    jira_id = jira_con.json()["id"]

    # Inbound sync from Jira
    jira_sync = client.post(
        f"{settings.API_V1_STR}/integrations/{jira_id}/sync",
        json={"sync_type": "INCREMENTAL", "direction": "INBOUND", "conflict_resolution": "EXTERNAL_WINS"},
        headers=headers,
    )
    assert jira_sync.status_code == 200
    assert jira_sync.json()["status"] == "COMPLETED"

# ------------------------------------------------------------------------------
# 8. Inbound Webhook Receiver & Signature Verification
# ------------------------------------------------------------------------------
def test_inbound_webhook_processing_and_automation_dispatch(client):
    db = SessionLocal()
    try:
        # 1. Prepare GitHub inbound webhook with HMAC-SHA256 signature
        secret = settings.SECRET_KEY.encode("utf-8")
        body_dict = {
            "action": "opened",
            "issue": {
                "id": 89412,
                "number": 42,
                "title": "Database connection pool timeout under peak load",
                "body": "Connections exhausted during morning sync jobs.",
                "html_url": "https://github.com/focusboard/app/issues/42"
            },
            "repository": {"full_name": "focusboard/app"}
        }
        body_bytes = json.dumps(body_dict).encode("utf-8")
        valid_signature = "sha256=" + hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()

        # 2. Send webhook with valid signature
        res = client.post(
            f"{settings.API_V1_STR}/integrations/webhooks/github",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "x-hub-signature-256": valid_signature,
                "x-github-event": "issues",
                "x-github-delivery": f"deliv_{uuid.uuid4().hex[:10]}",
            }
        )
        assert res.status_code == 200
        webhook_resp = res.json()
        assert webhook_resp["received"] is True
        assert webhook_resp["processed"] is True
        assert webhook_resp["event_type"] == "github.issue_created"

        # 3. Send webhook with invalid signature -> 401 Unauthorized
        bad_sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"
        bad_res = client.post(
            f"{settings.API_V1_STR}/integrations/webhooks/github",
            content=body_bytes,
            headers={
                "Content-Type": "application/json",
                "x-hub-signature-256": bad_sig,
                "x-github-event": "issues",
            }
        )
        assert bad_res.status_code == 401
        assert "Invalid webhook HMAC signature" in bad_res.json()["detail"]
    finally:
        db.close()

# ------------------------------------------------------------------------------
# 9. Outbound Webhook Delivery & SSRF Security Protection
# ------------------------------------------------------------------------------
def test_outbound_webhook_delivery_and_ssrf_protection(client):
    # 1. Test SSRF protection logic
    assert is_safe_external_url("https://api.example.com/v1/webhook") is True
    assert is_safe_external_url("https://hooks.slack.com/services/T00/B00/X00") is True

    # Block local loopback
    assert is_safe_external_url("http://127.0.0.1:8000/webhook") is False
    assert is_safe_external_url("http://localhost:5000/api") is False

    # Block AWS / cloud metadata IP
    assert is_safe_external_url("http://169.254.169.254/latest/meta-data/") is False

    # Block RFC 1918 private subnets
    assert is_safe_external_url("http://10.0.0.1/notify") is False
    assert is_safe_external_url("http://172.16.0.5/api") is False
    assert is_safe_external_url("http://192.168.1.10/webhook") is False

    # 2. Outbound delivery to valid external target
    db = SessionLocal()
    try:
        sub = WebhookSubscription(
            id=f"sub_{uuid.uuid4().hex[:12]}",
            user_id=1,
            workspace_id=1,
            target_url="https://api.externalpartner.com/focusboard-hook",
            events_json=json.dumps(["task.created"]),
            secret_key="secret_test_key_for_hmac",
            is_active=True,
        )
        db.add(sub)
        db.commit()

        deliv = deliver_outbound_webhook(
            db=db,
            subscription=sub,
            event_type="task.created",
            payload={"task_id": 99, "title": "Deploy v2.5"}
        )
        assert deliv.is_success is True
        assert deliv.response_status_code == 200

        # Outbound delivery to SSRF target raises exception
        sub_ssrf = WebhookSubscription(
            id=f"sub_{uuid.uuid4().hex[:12]}",
            user_id=1,
            workspace_id=1,
            target_url="http://169.254.169.254/secret",
            events_json=json.dumps(["task.created"]),
            secret_key="secret_test_key_for_hmac",
            is_active=True,
        )
        with pytest.raises(Exception) as exc_info:
            deliver_outbound_webhook(
                db=db,
                subscription=sub_ssrf,
                event_type="task.created",
                payload={"test": 123}
            )
        assert "SSRF" in str(exc_info.value.detail)
    finally:
        db.close()

# ------------------------------------------------------------------------------
# 10. Multi-Tenant Isolation & IDOR Protection
# ------------------------------------------------------------------------------
def test_multi_tenant_isolation_and_idor_protection(client):
    headers_a, user_a_id, _ = get_auth_headers(client, "tenant_a")
    headers_b, user_b_id, _ = get_auth_headers(client, "tenant_b")

    # User A connects an integration
    a_init = client.get(f"{settings.API_V1_STR}/integrations/slack/connect", headers=headers_a)
    a_cb = client.get(
        f"{settings.API_V1_STR}/integrations/slack/callback?code=code_a&state={a_init.json()['state']}",
        headers=headers_a,
    )
    integ_a_id = a_cb.json()["id"]

    # User B attempts to access User A's integration
    # 1. Health check IDOR attempt
    b_health = client.get(f"{settings.API_V1_STR}/integrations/{integ_a_id}/health", headers=headers_b)
    assert b_health.status_code == 404

    # 2. Test connection IDOR attempt
    b_test = client.post(f"{settings.API_V1_STR}/integrations/{integ_a_id}/test", headers=headers_b)
    assert b_test.status_code == 404

    # 3. Trigger sync IDOR attempt
    b_sync = client.post(f"{settings.API_V1_STR}/integrations/{integ_a_id}/sync", json={}, headers=headers_b)
    assert b_sync.status_code == 404

    # 4. View sync history IDOR attempt
    b_hist = client.get(f"{settings.API_V1_STR}/integrations/{integ_a_id}/sync-history", headers=headers_b)
    assert b_hist.status_code == 404

    # 5. Delete / disconnect IDOR attempt
    b_del = client.delete(f"{settings.API_V1_STR}/integrations/{integ_a_id}", headers=headers_b)
    assert b_del.status_code == 404

# ------------------------------------------------------------------------------
# 11. B15 Automation Engine External Actions Integration
# ------------------------------------------------------------------------------
def test_b15_automation_external_actions_execution(client):
    headers, user_id, _ = get_auth_headers(client, "auto_action_user")
    ws_id = create_test_workspace(client, headers, "Automation Integration WS")

    # Create workflow that executes Slack message and GitHub issue actions
    nodes = [
        {"id": "trig_1", "type": "trigger", "action_type": "event", "config": {"event": "task.completed"}},
        {"id": "act_slack", "type": "action", "action_type": "slack.send_message", "config": {"channel": "#eng-releases", "message": "Sprint task completed successfully!"}},
        {"id": "act_git", "type": "action", "action_type": "github.create_issue", "config": {"repo": "focusboard/app", "title": "Release Follow-up Item"}},
    ]
    edges = [
        {"id": "e1", "source": "trig_1", "target": "act_slack"},
        {"id": "e2", "source": "act_slack", "target": "act_git"},
    ]

    create_wf = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "name": "Integration Automated Dispatch Workflow",
            "workspace_id": ws_id,
            "trigger_type": "EVENT",
            "trigger_event": "task.completed",
            "nodes": nodes,
            "edges": edges,
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert create_wf.status_code == 201
    wf_id = create_wf.json()["id"]

    # Trigger workflow execution
    exec_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows/{wf_id}/trigger",
        json={"payload": {"task_title": "Implement B16 Backend"}},
        headers=headers,
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "COMPLETED"

    results = exec_data.get("results") or json.loads(exec_data.get("results_json", "{}"))
    # Verify Slack action output
    slack_res = results.get("act_slack")
    assert slack_res is not None
    assert slack_res["dispatched"] is True
    assert slack_res["channel"] == "#eng-releases"

    # Verify GitHub action output
    git_res = results.get("act_git")
    assert git_res is not None
    assert git_res["dispatched"] is True
    assert git_res["repo"] == "focusboard/app"
    assert "github.com/focusboard/app/issues" in git_res["issue_url"]
