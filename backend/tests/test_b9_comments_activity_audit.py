import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b9_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "CommentSecurePass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

def create_test_task(client, headers, title="B9 Test Task"):
    task_id = f"task_{uuid.uuid4().hex[:10]}"
    payload = {
        "id": task_id,
        "title": title,
        "status": "Todo",
        "priority": "High",
        "category": "Engineering",
        "due_date": "",
    }
    res = client.post(f"{settings.API_V1_STR}/tasks", json=payload, headers=headers)
    assert res.status_code in [200, 201], res.text
    return res.json()

# --------------------------------------------------------------------------
# 1. Comment CRUD, Threaded Replies & Soft Deletion
# --------------------------------------------------------------------------
def test_comment_crud_and_threaded_replies(client):
    headers, user_id, user_email = get_auth_headers(client, "commenter")
    task = create_test_task(client, headers, "Review Architecture Proposal")
    task_id = task["id"]

    # 1. Create root comment
    comment_payload = {
        "entity_type": "TASK",
        "entity_id": task_id,
        "content": "Initial architecture proposal looks solid. Let's proceed with benchmark tests.",
        "content_format": "markdown",
    }
    res_create = client.post(f"{settings.API_V1_STR}/comments", json=comment_payload, headers=headers)
    assert res_create.status_code == 201, res_create.text
    comment = res_create.json()
    comment_id = comment["id"]
    assert comment["content"] == comment_payload["content"]
    assert comment["author_id"] == user_id
    assert comment["is_edited"] is False
    assert comment["is_deleted"] is False

    # 2. Retrieve comments for the task
    res_list = client.get(f"{settings.API_V1_STR}/comments?entity_type=TASK&entity_id={task_id}", headers=headers)
    assert res_list.status_code == 200
    comments = res_list.json()
    assert len(comments) >= 1
    assert any(c["id"] == comment_id for c in comments)

    # 3. Create a threaded reply
    reply_payload = {
        "content": "Agreed. I have scheduled the benchmark cluster for tomorrow morning.",
    }
    res_reply = client.post(f"{settings.API_V1_STR}/comments/{comment_id}/replies", json=reply_payload, headers=headers)
    assert res_reply.status_code == 201, res_reply.text
    reply = res_reply.json()
    assert reply["parent_comment_id"] == comment_id
    assert reply["content"] == reply_payload["content"]

    # 4. Retrieve replies for the comment
    res_replies = client.get(f"{settings.API_V1_STR}/comments/{comment_id}/replies", headers=headers)
    assert res_replies.status_code == 200
    replies = res_replies.json()
    assert len(replies) == 1
    assert replies[0]["id"] == reply["id"]

    # 5. Edit root comment
    update_payload = {"content": "Updated: Initial architecture proposal looks solid. Verified benchmark metrics."}
    res_update = client.patch(f"{settings.API_V1_STR}/comments/{comment_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200
    updated_comment = res_update.json()
    assert updated_comment["content"] == update_payload["content"]
    assert updated_comment["is_edited"] is True

    # 6. Soft delete root comment
    res_delete = client.delete(f"{settings.API_V1_STR}/comments/{comment_id}", headers=headers)
    assert res_delete.status_code == 204

    # Verify soft-deleted state
    res_get_deleted = client.get(f"{settings.API_V1_STR}/comments/{comment_id}", headers=headers)
    assert res_get_deleted.status_code == 200
    assert res_get_deleted.json()["is_deleted"] is True
    assert "[comment deleted]" in res_get_deleted.json()["content"].lower()

# --------------------------------------------------------------------------
# 2. User Mentions & Autocomplete
# --------------------------------------------------------------------------
def test_user_mentions_and_autocomplete(client):
    author_headers, author_id, author_email = get_auth_headers(client, "mention_author")
    target_headers, target_id, target_email = get_auth_headers(client, "target_engineer")

    task = create_test_task(client, author_headers, "Database Migration Pipeline")
    task_id = task["id"]

    # Autocomplete search
    target_username = target_email.split("@")[0]
    res_ac = client.get(
        f"{settings.API_V1_STR}/comments/mentions/autocomplete?q={target_username[:6]}",
        headers=author_headers,
    )
    assert res_ac.status_code == 200
    ac_results = res_ac.json()
    assert isinstance(ac_results, list)

    # Post comment mentioning the target user
    comment_payload = {
        "entity_type": "TASK",
        "entity_id": task_id,
        "content": f"Hey @{target_email}, please review the DB schema indexes before applying.",
    }
    res_post = client.post(f"{settings.API_V1_STR}/comments", json=comment_payload, headers=author_headers)
    assert res_post.status_code == 201
    created_comment = res_post.json()

    # Verify mentions field
    assert "mentions" in created_comment

# --------------------------------------------------------------------------
# 3. Comment Reactions (Add, List Summary, Remove)
# --------------------------------------------------------------------------
def test_comment_reactions_lifecycle(client):
    headers, user_id, _ = get_auth_headers(client, "reaction_user")
    task = create_test_task(client, headers, "Frontend Design Review")
    task_id = task["id"]

    # Post comment
    res_comm = client.post(
        f"{settings.API_V1_STR}/comments",
        json={"entity_type": "TASK", "entity_id": task_id, "content": "Design looks clean and responsive!"},
        headers=headers,
    )
    comment_id = res_comm.json()["id"]

    # 1. Add reaction (thumbs_up)
    res_react1 = client.post(
        f"{settings.API_V1_STR}/comments/{comment_id}/reactions",
        json={"reaction_type": "thumbs_up"},
        headers=headers,
    )
    assert res_react1.status_code == 201
    assert res_react1.json()["reaction_type"] == "thumbs_up"

    # 2. Add second reaction (rocket)
    res_react2 = client.post(
        f"{settings.API_V1_STR}/comments/{comment_id}/reactions",
        json={"reaction_type": "rocket"},
        headers=headers,
    )
    assert res_react2.status_code == 201

    # 3. Get reactions summary
    res_get_reacts = client.get(f"{settings.API_V1_STR}/comments/{comment_id}/reactions", headers=headers)
    assert res_get_reacts.status_code == 200
    reactions = res_get_reacts.json()
    reaction_map = {r["reaction_type"]: r for r in reactions}
    assert "thumbs_up" in reaction_map
    assert reaction_map["thumbs_up"]["count"] >= 1
    assert reaction_map["thumbs_up"]["user_reacted"] is True

    # 4. Remove reaction
    res_del_react = client.delete(
        f"{settings.API_V1_STR}/comments/{comment_id}/reactions/thumbs_up",
        headers=headers,
    )
    assert res_del_react.status_code == 204

    # Verify removal
    res_after = client.get(f"{settings.API_V1_STR}/comments/{comment_id}/reactions", headers=headers)
    reaction_map_after = {r["reaction_type"]: r for r in res_after.json()}
    assert "thumbs_up" not in reaction_map_after or reaction_map_after["thumbs_up"]["user_reacted"] is False

# --------------------------------------------------------------------------
# 4. Activity Feeds & Event Engine
# --------------------------------------------------------------------------
def test_activity_feeds_and_timelines(client):
    headers, user_id, _ = get_auth_headers(client, "activity_lead")
    task = create_test_task(client, headers, "Deploy Kubernetes Cluster")
    task_id = task["id"]

    # Post comment to generate activity event
    client.post(
        f"{settings.API_V1_STR}/comments",
        json={"entity_type": "TASK", "entity_id": task_id, "content": "Cluster deployment initiated."},
        headers=headers,
    )

    # 1. Query generic activity feed
    res_feed = client.get(f"{settings.API_V1_STR}/activities", headers=headers)
    assert res_feed.status_code == 200
    activities = res_feed.json()
    assert isinstance(activities, list)
    assert len(activities) >= 1

    # 2. Query task-specific activity feed
    res_task_act = client.get(f"{settings.API_V1_STR}/activities/task/{task_id}", headers=headers)
    assert res_task_act.status_code == 200
    task_activities = res_task_act.json()
    assert len(task_activities) >= 1
    assert all(a["entity_id"] == str(task_id) or a["task_id"] == str(task_id) for a in task_activities)

    # 3. Activity feed date filter
    now = datetime.utcnow()
    from_date = (now - timedelta(hours=1)).isoformat()
    res_filtered = client.get(f"{settings.API_V1_STR}/activities?from_date={from_date}", headers=headers)
    assert res_filtered.status_code == 200

# --------------------------------------------------------------------------
# 5. Audit Trail & Security Logs
# --------------------------------------------------------------------------
def test_audit_logs_immutability_and_filtering(client):
    headers, user_id, _ = get_auth_headers(client, "auditor_user")

    # Access audit logs
    res_audit = client.get(f"{settings.API_V1_STR}/audit-logs", headers=headers)
    assert res_audit.status_code == 200
    logs = res_audit.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1

    # Verify audit log fields
    first_log = logs[0]
    assert "event_type" in first_log
    assert "created_at" in first_log

    # Filter audit logs by event_type
    res_audit_filtered = client.get(f"{settings.API_V1_STR}/audit-logs?event_type=AUDIT_LOG_VIEW", headers=headers)
    assert res_audit_filtered.status_code == 200
    filtered_logs = res_audit_filtered.json()
    assert all(log["event_type"] == "AUDIT_LOG_VIEW" for log in filtered_logs)

# --------------------------------------------------------------------------
# 6. Comment Content Validation & Security (Empty, Length, IDOR)
# --------------------------------------------------------------------------
def test_comment_security_and_validation(client):
    user_a_headers, user_a_id, _ = get_auth_headers(client, "security_user_a")
    user_b_headers, user_b_id, _ = get_auth_headers(client, "security_user_b")

    task = create_test_task(client, user_a_headers, "Security Hardening Task")
    task_id = task["id"]

    # 1. Empty comment rejection
    res_empty = client.post(
        f"{settings.API_V1_STR}/comments",
        json={"entity_type": "TASK", "entity_id": task_id, "content": "   "},
        headers=user_a_headers,
    )
    assert res_empty.status_code == 400

    # 2. Excessive comment length rejection (> 5000 chars)
    res_long = client.post(
        f"{settings.API_V1_STR}/comments",
        json={"entity_type": "TASK", "entity_id": task_id, "content": "A" * 5001},
        headers=user_a_headers,
    )
    assert res_long.status_code == 422 or res_long.status_code == 400

    # 3. Create valid comment by User A
    res_valid = client.post(
        f"{settings.API_V1_STR}/comments",
        json={"entity_type": "TASK", "entity_id": task_id, "content": "Confidential security review comment."},
        headers=user_a_headers,
    )
    comment_id = res_valid.json()["id"]

    # 4. User B attempts unauthorized editing of User A's comment
    res_unauth_edit = client.patch(
        f"{settings.API_V1_STR}/comments/{comment_id}",
        json={"content": "Malicious tampering attempt"},
        headers=user_b_headers,
    )
    assert res_unauth_edit.status_code == 403

    # 5. User B attempts unauthorized deletion of User A's comment
    res_unauth_del = client.delete(
        f"{settings.API_V1_STR}/comments/{comment_id}",
        headers=user_b_headers,
    )
    assert res_unauth_del.status_code == 403
