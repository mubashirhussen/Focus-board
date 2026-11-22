import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.session import SessionLocal
from app.models.task import Task
from app.models.comment import Comment
from app.models.notification import Notification
from app.services.automation_engine_service import evaluate_condition, calculate_next_run

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b15_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "AutomationPass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"Automation User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

def create_test_workspace(client, headers, name="Automation Workspace"):
    res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Workspace for B15 testing"},
        headers=headers,
    )
    assert res.status_code in [200, 201], res.text
    return res.json()["id"]

# -------------------------------------------------------------
# 1. Workflow CRUD & Versioning
# -------------------------------------------------------------
def test_automation_workflow_crud_and_versioning(client):
    headers, user_id, _ = get_auth_headers(client, "wf_crud")
    ws_id = create_test_workspace(client, headers, "WF Crud WS")

    # 1. Create workflow
    nodes = [
        {"id": "trigger_1", "type": "trigger", "action_type": "event", "config": {"event": "task.created"}},
        {"id": "action_1", "type": "action", "action_type": "notification.send", "config": {"recipient_id": user_id, "title": "New Task", "message": "A task was created."}}
    ]
    edges = [{"id": "e1", "source": "trigger_1", "target": "action_1"}]

    create_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_id,
            "title": "Onboarding Auto Notification",
            "description": "Sends notification when task is created",
            "trigger_type": "EVENT",
            "trigger_event": "task.created",
            "nodes": nodes,
            "edges": edges,
            "is_active": True
        },
        headers=headers
    )
    assert create_res.status_code == 201, create_res.text
    wf = create_res.json()
    wf_id = wf["id"]
    assert wf["title"] == "Onboarding Auto Notification"
    assert wf["current_version"] == "1.0"

    # 2. Update workflow nodes -> bump version to 1.1
    updated_nodes = nodes + [{"id": "action_2", "type": "action", "action_type": "task.create", "config": {"title": "Follow up task"}}]
    updated_edges = edges + [{"id": "e2", "source": "action_1", "target": "action_2"}]
    patch_res = client.patch(
        f"{settings.API_V1_STR}/automation/workflows/{wf_id}",
        json={
            "title": "Updated Auto Notification",
            "nodes": updated_nodes,
            "edges": updated_edges
        },
        headers=headers
    )
    assert patch_res.status_code == 200, patch_res.text
    updated_wf = patch_res.json()
    assert updated_wf["title"] == "Updated Auto Notification"
    assert updated_wf["current_version"] == "1.1"

    # 3. Check versions history
    ver_res = client.get(
        f"{settings.API_V1_STR}/automation/workflows/{wf_id}/versions",
        headers=headers
    )
    assert ver_res.status_code == 200
    versions = ver_res.json()
    assert len(versions) >= 2

    # 4. Delete workflow
    del_res = client.delete(f"{settings.API_V1_STR}/automation/workflows/{wf_id}", headers=headers)
    assert del_res.status_code == 204

# -------------------------------------------------------------
# 2. Workflow Toggle Status
# -------------------------------------------------------------
def test_automation_workflow_toggle_status(client):
    headers, user_id, _ = get_auth_headers(client, "wf_toggle")
    ws_id = create_test_workspace(client, headers, "WF Toggle WS")

    create_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_id,
            "title": "Toggle Workflow",
            "trigger_type": "MANUAL",
            "nodes": [{"id": "t1", "type": "trigger"}],
            "edges": [],
            "is_active": True,
            "status": "ACTIVE"
        },
        headers=headers
    )
    assert create_res.status_code == 201
    wf_id = create_res.json()["id"]

    # Toggle from ACTIVE to PAUSED
    t1 = client.patch(f"{settings.API_V1_STR}/automation/workflows/{wf_id}/toggle", headers=headers)
    assert t1.status_code == 200
    res1 = t1.json()
    assert res1["status"] == "PAUSED"
    assert res1["is_active"] is False

    # Toggle back to ACTIVE
    t2 = client.patch(f"{settings.API_V1_STR}/automation/workflows/{wf_id}/toggle", headers=headers)
    assert t2.status_code == 200
    res2 = t2.json()
    assert res2["status"] == "ACTIVE"
    assert res2["is_active"] is True

# -------------------------------------------------------------
# 3. Condition Engine Advanced Operators
# -------------------------------------------------------------
def test_condition_engine_advanced_operators():
    context = {
        "task": {
            "title": "Fix Critical Production Bug",
            "priority": "HIGH",
            "score": 85,
            "tags": ["urgent", "backend", "security"],
            "created_at": "2026-11-20T10:00:00Z"
        }
    }

    # GREATER_THAN
    cond_gt = {"field": "task.score", "operator": "GREATER_THAN", "value": 80}
    assert evaluate_condition(cond_gt, context) is True
    cond_gt_fail = {"field": "task.score", "operator": "GREATER_THAN", "value": 90}
    assert evaluate_condition(cond_gt_fail, context) is False

    # IN_LIST
    cond_in = {"field": "task.priority", "operator": "IN_LIST", "value": ["HIGH", "URGENT"]}
    assert evaluate_condition(cond_in, context) is True
    cond_not_in = {"field": "task.priority", "operator": "NOT_IN_LIST", "value": ["LOW", "MEDIUM"]}
    assert evaluate_condition(cond_not_in, context) is True

    # CONTAINS
    cond_contains = {"field": "task.title", "operator": "CONTAINS", "value": "Production"}
    assert evaluate_condition(cond_contains, context) is True

    # STARTS_WITH & ENDS_WITH
    assert evaluate_condition({"field": "task.title", "operator": "STARTS_WITH", "value": "Fix"}, context) is True
    assert evaluate_condition({"field": "task.title", "operator": "ENDS_WITH", "value": "Bug"}, context) is True

    # DATE_BEFORE & DATE_AFTER
    assert evaluate_condition({"field": "task.created_at", "operator": "DATE_BEFORE", "value": "2026-11-25T00:00:00Z"}, context) is True
    assert evaluate_condition({"field": "task.created_at", "operator": "DATE_AFTER", "value": "2026-11-15T00:00:00Z"}, context) is True

    # IS_NOT_EMPTY
    assert evaluate_condition({"field": "task.tags", "operator": "IS_NOT_EMPTY"}, context) is True

# -------------------------------------------------------------
# 4. Condition Groups (AND/OR Logic)
# -------------------------------------------------------------
def test_condition_groups_and_or_logic():
    context = {
        "status": "IN_PROGRESS",
        "priority": "URGENT",
        "estimate_hours": 12
    }

    # AND group: both must match
    and_group = {
        "operator": "AND",
        "conditions": [
            {"field": "status", "operator": "EQUALS", "value": "IN_PROGRESS"},
            {"field": "priority", "operator": "EQUALS", "value": "URGENT"}
        ]
    }
    assert evaluate_condition(and_group, context) is True

    # AND group with failing condition
    and_group_fail = {
        "operator": "AND",
        "conditions": [
            {"field": "status", "operator": "EQUALS", "value": "IN_PROGRESS"},
            {"field": "priority", "operator": "EQUALS", "value": "LOW"}
        ]
    }
    assert evaluate_condition(and_group_fail, context) is False

    # OR group: one matches
    or_group = {
        "operator": "OR",
        "conditions": [
            {"field": "priority", "operator": "EQUALS", "value": "LOW"},
            {"field": "estimate_hours", "operator": "GREATER_THAN", "value": 10}
        ]
    }
    assert evaluate_condition(or_group, context) is True

# -------------------------------------------------------------
# 5. Real Action Execution: Task Create
# -------------------------------------------------------------
def test_action_execution_task_crud(client):
    headers, user_id, _ = get_auth_headers(client, "act_crud")
    ws_id = create_test_workspace(client, headers, "Action Task Create WS")

    unique_title = f"Automated Task {uuid.uuid4().hex[:6]}"
    nodes = [
        {"id": "t1", "type": "trigger", "action_type": "manual", "config": {}},
        {
            "id": "a1",
            "type": "action",
            "action_type": "task.create",
            "config": {
                "title": unique_title,
                "description": "Created automatically by FocusBoard automation engine",
                "priority": "HIGH",
                "status": "TODO",
                "workspace_id": ws_id
            }
        }
    ]
    edges = [{"id": "e1", "source": "t1", "target": "a1"}]

    wf_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_id,
            "title": "Task Creator Flow",
            "trigger_type": "MANUAL",
            "nodes": nodes,
            "edges": edges,
            "is_active": True
        },
        headers=headers
    )
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["id"]

    # Trigger execution
    trig_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows/{wf_id}/trigger",
        json={"trigger_event": "MANUAL", "payload": {}, "dry_run": False},
        headers=headers
    )
    assert trig_res.status_code == 200, trig_res.text
    exec_data = trig_res.json()
    assert exec_data["status"] == "COMPLETED"

    # Verify real task created in database
    db = SessionLocal()
    try:
        created_task = db.query(Task).filter(Task.title == unique_title, Task.workspace_id == ws_id).first()
        assert created_task is not None
        assert created_task.priority == "HIGH"
        assert created_task.status == "TODO"
    finally:
        db.close()

# -------------------------------------------------------------
# 6. Real Action Execution: Task Update & Add Comment
# -------------------------------------------------------------
def test_action_execution_task_update_and_comment(client):
    headers, user_id, _ = get_auth_headers(client, "act_update")
    ws_id = create_test_workspace(client, headers, "Action Task Update WS")

    # Create task first
    task_res = client.post(
        f"{settings.API_V1_STR}/tasks",
        json={
            "title": "Base Task to Update",
            "workspace_id": ws_id,
            "priority": "LOW",
            "status": "TODO"
        },
        headers=headers
    )
    assert task_res.status_code in [200, 201]
    task_id = task_res.json()["id"]

    comment_msg = f"Automated audit comment {uuid.uuid4().hex[:6]}"
    nodes = [
        {"id": "t1", "type": "trigger", "action_type": "manual", "config": {}},
        {
            "id": "a1",
            "type": "action",
            "action_type": "task.update",
            "config": {
                "task_id": task_id,
                "priority": "URGENT",
                "status": "IN_PROGRESS"
            }
        },
        {
            "id": "a2",
            "type": "action",
            "action_type": "task.add_comment",
            "config": {
                "task_id": task_id,
                "content": comment_msg
            }
        }
    ]
    edges = [
        {"id": "e1", "source": "t1", "target": "a1"},
        {"id": "e2", "source": "a1", "target": "a2"}
    ]

    wf_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_id,
            "title": "Task Modifier Flow",
            "trigger_type": "MANUAL",
            "nodes": nodes,
            "edges": edges,
            "is_active": True
        },
        headers=headers
    )
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["id"]

    # Trigger execution
    trig_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows/{wf_id}/trigger",
        json={"trigger_event": "MANUAL", "payload": {}, "dry_run": False},
        headers=headers
    )
    assert trig_res.status_code == 200
    assert trig_res.json()["status"] == "COMPLETED"

    # Verify DB state
    db = SessionLocal()
    try:
        updated_task = db.query(Task).filter(Task.id == task_id).first()
        assert updated_task.priority == "URGENT"
        assert updated_task.status == "IN_PROGRESS"

        c = db.query(Comment).filter(Comment.task_id == task_id, Comment.content == comment_msg).first()
        assert c is not None
    finally:
        db.close()

# -------------------------------------------------------------
# 7. Action Execution: Notification Dispatch
# -------------------------------------------------------------
def test_action_execution_notification_dispatch(client):
    headers, user_id, _ = get_auth_headers(client, "act_notif")
    ws_id = create_test_workspace(client, headers, "Action Notif WS")

    notif_title = f"Alert {uuid.uuid4().hex[:6]}"
    nodes = [
        {"id": "t1", "type": "trigger", "action_type": "manual", "config": {}},
        {
            "id": "a1",
            "type": "action",
            "action_type": "notification.send",
            "config": {
                "recipient_id": user_id,
                "title": notif_title,
                "message": "Automation triggered this notification."
            }
        }
    ]
    edges = [{"id": "e1", "source": "t1", "target": "a1"}]

    wf_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_id,
            "title": "Notifier Flow",
            "trigger_type": "MANUAL",
            "nodes": nodes,
            "edges": edges,
            "is_active": True
        },
        headers=headers
    )
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["id"]

    trig_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows/{wf_id}/trigger",
        json={"trigger_event": "MANUAL", "payload": {}, "dry_run": False},
        headers=headers
    )
    assert trig_res.status_code == 200
    assert trig_res.json()["status"] == "COMPLETED"

    db = SessionLocal()
    try:
        notif = db.query(Notification).filter(Notification.user_id == user_id, Notification.title == notif_title).first()
        assert notif is not None
    finally:
        db.close()

# -------------------------------------------------------------
# 8. Human in the Loop Approval Flow
# -------------------------------------------------------------
def test_human_in_the_loop_approval_flow(client):
    headers, user_id, _ = get_auth_headers(client, "wf_appr")
    ws_id = create_test_workspace(client, headers, "Approval Flow WS")

    nodes = [
        {"id": "t1", "type": "trigger", "action_type": "manual", "config": {}},
        {
            "id": "appr1",
            "type": "action",
            "action_type": "approval",
            "config": {
                "approver_id": user_id,
                "title": "Deploy to Production Approval"
            }
        },
        {
            "id": "a2",
            "type": "action",
            "action_type": "notification.send",
            "config": {
                "recipient_id": user_id,
                "title": "Deployment Approved",
                "message": "Deployment completed successfully."
            }
        }
    ]
    edges = [
        {"id": "e1", "source": "t1", "target": "appr1"},
        {"id": "e2", "source": "appr1", "target": "a2"}
    ]

    wf_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_id,
            "title": "Approval Gate Flow",
            "trigger_type": "MANUAL",
            "nodes": nodes,
            "edges": edges,
            "is_active": True
        },
        headers=headers
    )
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["id"]

    # Trigger execution - should halt at REQUIRES_APPROVAL
    trig_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows/{wf_id}/trigger",
        json={"trigger_event": "MANUAL", "payload": {}, "dry_run": False},
        headers=headers
    )
    assert trig_res.status_code == 200
    exec_data = trig_res.json()
    assert exec_data["status"] == "REQUIRES_APPROVAL"
    exec_id = exec_data["id"]

    # Fetch pending approvals
    appr_list_res = client.get(
        f"{settings.API_V1_STR}/automation/approvals?execution_id={exec_id}",
        headers=headers
    )
    assert appr_list_res.status_code == 200
    approvals = appr_list_res.json()
    assert len(approvals) >= 1
    approval_id = approvals[0]["id"]
    assert approvals[0]["status"] == "PENDING"

    # Submit Approval Decision: APPROVED
    dec_res = client.post(
        f"{settings.API_V1_STR}/automation/approvals/{approval_id}/decision",
        json={"decision": "APPROVED", "comments": "Looks good to deploy!"},
        headers=headers
    )
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["status"] == "APPROVED"

    # Verify execution resumed and completed
    exec_check = client.get(
        f"{settings.API_V1_STR}/automation/executions/{exec_id}",
        headers=headers
    )
    assert exec_check.status_code == 200
    assert exec_check.json()["status"] == "COMPLETED"

# -------------------------------------------------------------
# 9. Scheduled Automation Execution
# -------------------------------------------------------------
def test_scheduled_automation_execution(client):
    headers, user_id, _ = get_auth_headers(client, "sched_user")
    ws_id = create_test_workspace(client, headers, "Schedule WS")

    wf_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_id,
            "title": "Daily Cleanup Automation",
            "trigger_type": "SCHEDULED",
            "nodes": [
                {"id": "t1", "type": "trigger", "action_type": "scheduled", "config": {"expression": "0 0 * * *"}},
                {"id": "a1", "type": "action", "action_type": "notification.send", "config": {"recipient_id": user_id, "title": "Daily Cleanup", "message": "Cleaned up tasks"}}
            ],
            "edges": [{"id": "e1", "source": "t1", "target": "a1"}],
            "is_active": True
        },
        headers=headers
    )
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["id"]

    # Create schedule
    sched_res = client.post(
        f"{settings.API_V1_STR}/automation/schedules",
        json={
            "workflow_id": wf_id,
            "expression": "*/5 * * * *",
            "timezone": "UTC",
            "is_active": True
        },
        headers=headers
    )
    assert sched_res.status_code == 201, sched_res.text
    sched_data = sched_res.json()
    sched_id = sched_data["id"]
    assert sched_data["workflow_id"] == wf_id
    assert sched_data["next_run_at"] is not None

    # List schedules
    list_res = client.get(
        f"{settings.API_V1_STR}/automation/schedules?workflow_id={wf_id}",
        headers=headers
    )
    assert list_res.status_code == 200
    schedules = list_res.json()
    assert len(schedules) >= 1

    # Manually backdate next_run_at in DB so run_due_schedules picks it up
    db = SessionLocal()
    try:
        from app.models.automation import AutomationSchedule
        s = db.query(AutomationSchedule).filter(AutomationSchedule.id == sched_id).first()
        s.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        db.commit()
    finally:
        db.close()

    # Trigger run-due
    run_due_res = client.post(
        f"{settings.API_V1_STR}/automation/schedules/run-due",
        headers=headers
    )
    assert run_due_res.status_code == 200
    rd_data = run_due_res.json()
    assert (len(rd_data) >= 1 if isinstance(rd_data, list) else rd_data.get("executed", 0) >= 1)

    # Delete schedule
    del_sched = client.delete(f"{settings.API_V1_STR}/automation/schedules/{sched_id}", headers=headers)
    assert del_sched.status_code == 204

# -------------------------------------------------------------
# 10. Event-Driven Dispatch & Multi-Tenant Isolation
# -------------------------------------------------------------
def test_event_driven_dispatch_and_multi_tenant_isolation(client):
    headers_a, user_a, _ = get_auth_headers(client, "tenant_a")
    headers_b, user_b, _ = get_auth_headers(client, "tenant_b")

    ws_a = create_test_workspace(client, headers_a, "Workspace Alpha")
    ws_b = create_test_workspace(client, headers_b, "Workspace Beta")

    # Workflow in Workspace A
    wf_a_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_a,
            "title": "Tenant A Handler",
            "trigger_type": "EVENT",
            "trigger_event": "task.created",
            "nodes": [
                {"id": "t1", "type": "trigger", "action_type": "event", "config": {"event": "task.created"}},
                {"id": "a1", "type": "action", "action_type": "notification.send", "config": {"recipient_id": user_a, "title": "Tenant A Event", "message": "Fired in A"}}
            ],
            "edges": [{"id": "e1", "source": "t1", "target": "a1"}],
            "is_active": True
        },
        headers=headers_a
    )
    assert wf_a_res.status_code == 201
    wf_a_id = wf_a_res.json()["id"]

    # Workflow in Workspace B
    wf_b_res = client.post(
        f"{settings.API_V1_STR}/automation/workflows",
        json={
            "workspace_id": ws_b,
            "title": "Tenant B Handler",
            "trigger_type": "EVENT",
            "trigger_event": "task.created",
            "nodes": [
                {"id": "t1", "type": "trigger", "action_type": "event", "config": {"event": "task.created"}},
                {"id": "a1", "type": "action", "action_type": "notification.send", "config": {"recipient_id": user_b, "title": "Tenant B Event", "message": "Fired in B"}}
            ],
            "edges": [{"id": "e1", "source": "t1", "target": "a1"}],
            "is_active": True
        },
        headers=headers_b
    )
    assert wf_b_res.status_code == 201
    wf_b_id = wf_b_res.json()["id"]

    # Emit event targeting Workspace A only
    emit_res = client.post(
        f"{settings.API_V1_STR}/automation/events/emit",
        json={
            "event_type": "task.created",
            "workspace_id": ws_a,
            "payload": {"title": "Tenant Isolation Test Task", "priority": "MEDIUM"}
        },
        headers=headers_a
    )
    assert emit_res.status_code == 200
    emit_data = emit_res.json()
    if isinstance(emit_data, list):
        triggered_wfs = [e["workflow_id"] for e in emit_data]
        assert len(emit_data) == 1
        assert wf_a_id in triggered_wfs
        assert wf_b_id not in triggered_wfs
    else:
        assert emit_data["triggered_count"] == 1
        assert wf_a_id in emit_data["workflow_ids"]
        assert wf_b_id not in emit_data["workflow_ids"]

    # Verify executions: Workflow A has at least 1 execution, Workflow B has 0
    exec_a_res = client.get(
        f"{settings.API_V1_STR}/automation/executions?workflow_id={wf_a_id}",
        headers=headers_a
    )
    assert exec_a_res.status_code == 200
    assert len(exec_a_res.json()) >= 1

    exec_b_res = client.get(
        f"{settings.API_V1_STR}/automation/executions?workflow_id={wf_b_id}",
        headers=headers_b
    )
    assert exec_b_res.status_code == 200
    assert len(exec_b_res.json()) == 0
