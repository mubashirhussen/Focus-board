import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.database import SessionLocal
from app.models.notification import Notification, NotificationPreference, NotificationDelivery
from app.services.notification_service import notification_service

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b10_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "NotifSecurePass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

# --------------------------------------------------------------------------
# 1. Notification Creation, Querying, Filtering & Search
# --------------------------------------------------------------------------
def test_notification_creation_and_filtering(client):
    headers, user_id, email = get_auth_headers(client, "notif_filter")

    # 1. Create a notification
    payload = {
        "category": "TASK",
        "type": "TASK_ASSIGNED",
        "title": "Backend Feature Assigned",
        "message": "You have been assigned to implement notification webhooks.",
        "priority": "HIGH",
        "entity_type": "TASK",
        "entity_id": "task_notif_100",
        "delivery_channel": "IN_APP"
    }
    res = client.post(f"{settings.API_V1_STR}/notifications", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    notif = res.json()
    notif_id = notif["id"]
    assert notif["title"] == payload["title"]
    assert notif["category"] == "TASK"
    assert notif["priority"] == "HIGH"

    # 2. Query all notifications
    res_list = client.get(f"{settings.API_V1_STR}/notifications", headers=headers)
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) >= 1
    assert any(n["id"] == notif_id for n in items)

    # 3. Filter by category
    res_cat = client.get(f"{settings.API_V1_STR}/notifications?category=TASK", headers=headers)
    assert res_cat.status_code == 200
    assert all(n["category"] == "TASK" for n in res_cat.json())

    # 4. Filter by priority
    res_prio = client.get(f"{settings.API_V1_STR}/notifications?priority=HIGH", headers=headers)
    assert res_prio.status_code == 200
    assert all(n["priority"] == "HIGH" for n in res_prio.json())

    # 5. Search keyword
    res_search = client.get(f"{settings.API_V1_STR}/notifications?search=webhooks", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1

# --------------------------------------------------------------------------
# 2. Read / Unread Lifecycle & Summary
# --------------------------------------------------------------------------
def test_notification_read_unread_and_summary(client):
    headers, user_id, email = get_auth_headers(client, "notif_read")

    # Create 2 notifications
    client.post(f"{settings.API_V1_STR}/notifications", json={
        "category": "TASK",
        "type": "TASK_DUE_SOON",
        "title": "Task Due Soon",
        "message": "Sprint planning meeting task is due tomorrow.",
        "priority": "NORMAL",
        "entity_type": "TASK",
        "entity_id": "task_201"
    }, headers=headers)

    res2 = client.post(f"{settings.API_V1_STR}/notifications", json={
        "category": "PROJECT",
        "type": "PROJECT_UPDATED",
        "title": "Project Milestone Reached",
        "message": "Milestone Alpha has been completed.",
        "priority": "HIGH",
        "entity_type": "PROJECT",
        "entity_id": "proj_202"
    }, headers=headers)
    notif2_id = res2.json()["id"]

    # Check unread count
    res_count = client.get(f"{settings.API_V1_STR}/notifications/unread-count", headers=headers)
    assert res_count.status_code == 200
    assert res_count.json()["unread_count"] >= 2

    # Check summary
    res_summary = client.get(f"{settings.API_V1_STR}/notifications/summary", headers=headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_count"] >= 2
    assert summary["unread_count"] >= 2
    assert "TASK" in summary["by_category"]
    assert "PROJECT" in summary["by_category"]

    # Mark notif2 as read
    res_read = client.patch(f"{settings.API_V1_STR}/notifications/{notif2_id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["read_at"] is not None

    # Mark notif2 back as unread
    res_unread = client.patch(f"{settings.API_V1_STR}/notifications/{notif2_id}/unread", headers=headers)
    assert res_unread.status_code == 200
    assert res_unread.json()["read_at"] is None

    # Mark all as read
    res_mark_all = client.patch(f"{settings.API_V1_STR}/notifications/read-all", headers=headers)
    assert res_mark_all.status_code == 200
    assert res_mark_all.json()["affected"] >= 2

    # Unread count should now be 0
    res_count_after = client.get(f"{settings.API_V1_STR}/notifications/unread-count", headers=headers)
    assert res_count_after.json()["unread_count"] == 0

# --------------------------------------------------------------------------
# 3. Bulk Read and Bulk Delete Operations
# --------------------------------------------------------------------------
def test_bulk_notification_actions(client):
    headers, user_id, email = get_auth_headers(client, "notif_bulk")

    ids = []
    for i in range(3):
        res = client.post(f"{settings.API_V1_STR}/notifications", json={
            "category": "TEAM",
            "type": "TEAM_UPDATE",
            "title": f"Team Notice {i}",
            "message": f"Notice details {i}",
            "priority": "LOW",
            "entity_type": "TEAM",
            "entity_id": f"team_{i}"
        }, headers=headers)
        ids.append(res.json()["id"])

    # Bulk mark as read
    res_bulk_read = client.post(
        f"{settings.API_V1_STR}/notifications/bulk/read",
        json={"notification_ids": ids[:2]},
        headers=headers
    )
    assert res_bulk_read.status_code == 200
    assert res_bulk_read.json()["affected"] == 2

    # Bulk delete
    res_bulk_del = client.post(
        f"{settings.API_V1_STR}/notifications/bulk/delete",
        json={"notification_ids": ids},
        headers=headers
    )
    assert res_bulk_del.status_code == 200
    assert res_bulk_del.json()["affected"] == 3

    # All should be gone
    res_list = client.get(f"{settings.API_V1_STR}/notifications", headers=headers)
    assert len(res_list.json()) == 0

# --------------------------------------------------------------------------
# 4. Archiving & Retention
# --------------------------------------------------------------------------
def test_notification_archiving(client):
    headers, user_id, email = get_auth_headers(client, "notif_archive")

    res = client.post(f"{settings.API_V1_STR}/notifications", json={
        "category": "CALENDAR",
        "type": "DEADLINE_ALERT",
        "title": "Quarterly Tax Filing",
        "message": "Filing deadline is approaching.",
        "priority": "HIGH",
        "entity_type": "CALENDAR",
        "entity_id": "cal_1"
    }, headers=headers)
    notif_id = res.json()["id"]

    # Archive
    res_archive = client.post(f"{settings.API_V1_STR}/notifications/{notif_id}/archive", headers=headers)
    assert res_archive.status_code == 200
    assert res_archive.json()["is_archived"] is True
    assert res_archive.json()["archived_at"] is not None

    # Query unarchived (default) -> should not contain it
    res_unarch = client.get(f"{settings.API_V1_STR}/notifications?is_archived=false", headers=headers)
    assert not any(n["id"] == notif_id for n in res_unarch.json())

    # Query archived -> should contain it
    res_arch = client.get(f"{settings.API_V1_STR}/notifications?is_archived=true", headers=headers)
    assert any(n["id"] == notif_id for n in res_arch.json())

# --------------------------------------------------------------------------
# 5. User Notification Preferences & Channel Controls
# --------------------------------------------------------------------------
def test_notification_preferences_and_suppression(client):
    headers, user_id, email = get_auth_headers(client, "notif_pref")

    # Get default preferences
    res_pref = client.get(f"{settings.API_V1_STR}/notifications/preferences", headers=headers)
    assert res_pref.status_code == 200
    pref = res_pref.json()
    assert pref["enable_in_app"] is True
    assert pref["enable_task_assigned"] is True

    # Update preferences: disable in-app and task assigned
    update_data = {
        "enable_in_app": False,
        "enable_task_assigned": False,
        "daily_reminder_time": "08:30",
        "timezone": "America/New_York"
    }
    res_update = client.put(f"{settings.API_V1_STR}/notifications/preferences", json=update_data, headers=headers)
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["enable_in_app"] is False
    assert updated["enable_task_assigned"] is False
    assert updated["daily_reminder_time"] == "08:30"
    assert updated["timezone"] == "America/New_York"

    # Attempting to create a normal priority TASK notification should be suppressed
    db = SessionLocal()
    try:
        suppressed = notification_service.create_notification(
            db=db,
            user_id=user_id,
            category="TASK",
            type="TASK_ASSIGNED",
            title="Suppressed Task",
            message="This should be suppressed.",
            priority="NORMAL"
        )
        assert suppressed is None
    finally:
        db.close()

# --------------------------------------------------------------------------
# 6. Idempotency & Deduplication
# --------------------------------------------------------------------------
def test_notification_deduplication_and_idempotency(client):
    headers, user_id, email = get_auth_headers(client, "notif_idemp")
    db = SessionLocal()
    try:
        # Test idempotency key
        key = f"key_{uuid.uuid4().hex}"
        n1 = notification_service.create_notification(
            db=db,
            user_id=user_id,
            type="ALERT",
            title="Alert 1",
            message="Msg 1",
            idempotency_key=key
        )
        assert n1 is not None

        # Repeat call with same idempotency key
        n2 = notification_service.create_notification(
            db=db,
            user_id=user_id,
            type="ALERT",
            title="Alert 1 Duplicate",
            message="Msg 1 Duplicate",
            idempotency_key=key
        )
        assert n2 is not None
        assert n1.id == n2.id

        # Test 5-minute entity deduplication
        n3 = notification_service.create_notification(
            db=db,
            user_id=user_id,
            type="TASK_STATUS",
            title="Status Change",
            message="Moved to doing",
            entity_type="TASK",
            entity_id="task_dedup_1"
        )
        n4 = notification_service.create_notification(
            db=db,
            user_id=user_id,
            type="TASK_STATUS",
            title="Status Change Again",
            message="Moved to doing again",
            entity_type="TASK",
            entity_id="task_dedup_1"
        )
        assert n3.id == n4.id
    finally:
        db.close()

# --------------------------------------------------------------------------
# 7. Event Triggers: Task Assignment & Task Completion
# --------------------------------------------------------------------------
def test_event_triggers_task_lifecycle(client):
    headers_creator, creator_id, creator_email = get_auth_headers(client, "creator")
    headers_assignee, assignee_id, assignee_email = get_auth_headers(client, "assignee")

    # 1. Creator creates task assigned to assignee
    task_id = f"task_{uuid.uuid4().hex[:10]}"
    task_payload = {
        "id": task_id,
        "title": "Implement GraphQL Layer",
        "status": "Todo",
        "priority": "High",
        "category": "Engineering",
        "assignee_id": assignee_id
    }
    res_task = client.post(f"{settings.API_V1_STR}/tasks", json=task_payload, headers=headers_creator)
    assert res_task.status_code in [200, 201], res_task.text

    # Assignee should receive TASK_ASSIGNED notification
    res_notif = client.get(f"{settings.API_V1_STR}/notifications", headers=headers_assignee)
    assert res_notif.status_code == 200
    items = res_notif.json()
    assert any(n["type"] == "TASK_ASSIGNED" and n["task_id"] == task_id for n in items)

    # 2. Assignee completes the task
    res_status = client.patch(
        f"{settings.API_V1_STR}/tasks/{task_id}/status",
        json={"status": "Completed"},
        headers=headers_assignee
    )
    assert res_status.status_code == 200

    # Creator should receive TASK_COMPLETED notification
    res_creator_notif = client.get(f"{settings.API_V1_STR}/notifications", headers=headers_creator)
    assert res_creator_notif.status_code == 200
    creator_items = res_creator_notif.json()
    assert any(n["type"] == "TASK_COMPLETED" and n["task_id"] == task_id for n in creator_items)

# --------------------------------------------------------------------------
# 8. Event Triggers: Comment Mention
# --------------------------------------------------------------------------
def test_event_triggers_comment_mention(client):
    headers_author, author_id, author_email = get_auth_headers(client, "c_author")
    headers_mentioned, mentioned_id, mentioned_email = get_auth_headers(client, "c_mentioned")

    # Create task
    task_id = f"task_{uuid.uuid4().hex[:10]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": task_id,
        "title": "Mention Target Task",
        "status": "Todo",
        "priority": "Medium",
        "category": "Design"
    }, headers=headers_author)

    # Author comments mentioning user
    mention_tag = f"@{mentioned_email}"
    res_comm = client.post(f"{settings.API_V1_STR}/comments", json={
        "entity_type": "TASK",
        "entity_id": task_id,
        "content": f"Hey {mention_tag}, please review these UX wireframes.",
        "content_format": "markdown"
    }, headers=headers_author)
    assert res_comm.status_code == 201, res_comm.text

    # Mentioned user should have received COMMENT_MENTION notification
    res_notif = client.get(f"{settings.API_V1_STR}/notifications", headers=headers_mentioned)
    assert res_notif.status_code == 200
    items = res_notif.json()
    assert any(n["type"] == "COMMENT_MENTION" and n["category"] == "COLLABORATION" for n in items)

# --------------------------------------------------------------------------
# 9. Event Triggers: Team Invitation
# --------------------------------------------------------------------------
def test_event_triggers_team_invitation(client):
    headers_owner, owner_id, owner_email = get_auth_headers(client, "t_owner")
    headers_invitee, invitee_id, invitee_email = get_auth_headers(client, "t_invitee")

    # Create team
    res_team = client.post(f"{settings.API_V1_STR}/teams", json={
        "name": f"Core Engineering Team {uuid.uuid4().hex[:6]}",
        "description": "Platform architecture and core backend"
    }, headers=headers_owner)
    assert res_team.status_code == 201, res_team.text
    team_id = res_team.json()["id"]

    # Send invitation
    res_inv = client.post(f"{settings.API_V1_STR}/teams/{team_id}/invitations", json={
        "email": invitee_email,
        "role": "MEMBER"
    }, headers=headers_owner)
    assert res_inv.status_code == 201, res_inv.text

    # Invitee receives TEAM_INVITATION notification
    res_notif = client.get(f"{settings.API_V1_STR}/notifications", headers=headers_invitee)
    assert res_notif.status_code == 200
    items = res_notif.json()
    assert any(n["type"] == "TEAM_INVITATION" and n["category"] == "INVITATION" for n in items)

# --------------------------------------------------------------------------
# 10. Security & Tenant Isolation (IDOR Protection)
# --------------------------------------------------------------------------
def test_notification_security_and_tenant_isolation(client):
    headers_user_a, user_a_id, _ = get_auth_headers(client, "user_a")
    headers_user_b, user_b_id, _ = get_auth_headers(client, "user_b")

    # User A creates a notification
    res_a = client.post(f"{settings.API_V1_STR}/notifications", json={
        "category": "TASK",
        "type": "SECRET_NOTICE",
        "title": "Private User A Notice",
        "message": "Top secret content for User A.",
        "priority": "HIGH",
        "entity_type": "TASK",
        "entity_id": "secret_task_1"
    }, headers=headers_user_a)
    notif_a_id = res_a.json()["id"]

    # User B attempts to access User A's notification -> 404
    res_get = client.get(f"{settings.API_V1_STR}/notifications/{notif_a_id}", headers=headers_user_b)
    assert res_get.status_code == 404

    # User B attempts to mark User A's notification as read -> 404
    res_patch = client.patch(f"{settings.API_V1_STR}/notifications/{notif_a_id}/read", headers=headers_user_b)
    assert res_patch.status_code == 404

    # User B attempts to delete User A's notification -> 404
    res_del = client.delete(f"{settings.API_V1_STR}/notifications/{notif_a_id}", headers=headers_user_b)
    assert res_del.status_code == 404
