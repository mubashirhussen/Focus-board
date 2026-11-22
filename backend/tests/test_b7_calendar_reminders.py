import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="cal_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "CalendarSecurePass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": "Calendar Tester", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id

def create_test_task(client, headers, title, due_date=None, scheduled_start=None, status="Todo"):
    task_id = f"task_{uuid.uuid4().hex[:10]}"
    payload = {
        "id": task_id,
        "title": title,
        "status": status,
        "priority": "High",
        "category": "Engineering",
        "due_date": due_date or "",
        "scheduled_start": scheduled_start.isoformat() if scheduled_start else None,
        "estimated_duration_minutes": 45,
    }
    res = client.post(f"{settings.API_V1_STR}/tasks", json=payload, headers=headers)
    assert res.status_code in [200, 201], res.text
    return res.json()

# --------------------------------------------------------------------------
# 1. Calendar Views: Month, Week, Day, Agenda
# --------------------------------------------------------------------------
def test_calendar_views_month_week_day_agenda(client):
    headers, user_id = get_auth_headers(client, "views_tester")
    now = datetime.now(timezone.utc)

    # Create tasks across different dates
    task1 = create_test_task(client, headers, "Sprint Planning", scheduled_start=now)
    task2 = create_test_task(client, headers, "Architecture Review", scheduled_start=now + timedelta(days=2))
    task3 = create_test_task(client, headers, "Release Deployment", scheduled_start=now + timedelta(days=5))

    # Month View
    res_month = client.get(f"{settings.API_V1_STR}/calendar/month", headers=headers)
    assert res_month.status_code == 200
    data_month = res_month.json()
    assert data_month["view"] == "month"
    assert data_month["total_tasks"] >= 3
    assert len(data_month["tasks"]) >= 3
    assert "date_groups" in data_month

    # Week View
    res_week = client.get(f"{settings.API_V1_STR}/calendar/week", headers=headers)
    assert res_week.status_code == 200
    data_week = res_week.json()
    assert data_week["view"] == "week"

    # Day View
    res_day = client.get(f"{settings.API_V1_STR}/calendar/day", headers=headers)
    assert res_day.status_code == 200
    data_day = res_day.json()
    assert data_day["view"] == "day"

    # Agenda View
    res_agenda = client.get(f"{settings.API_V1_STR}/calendar/agenda", headers=headers)
    assert res_agenda.status_code == 200
    data_agenda = res_agenda.json()
    assert data_agenda["view"] == "agenda"
    assert len(data_agenda["tasks"]) >= 3

# --------------------------------------------------------------------------
# 2. Deadlines, Overdue, and Due Today Calculations
# --------------------------------------------------------------------------
def test_calendar_deadlines_overdue_and_due_today(client):
    headers, user_id = get_auth_headers(client, "deadline_tester")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Overdue incomplete task
    task_overdue = create_test_task(client, headers, "Overdue Incomplete Task", due_date=yesterday_str, status="Todo")
    # 2. Completed task with past date (must NOT be overdue)
    task_completed = create_test_task(client, headers, "Completed Past Task", due_date=yesterday_str, status="Completed")
    # 3. Due today task
    task_due_today = create_test_task(client, headers, "Due Today Task", due_date=today_str, status="In Progress")
    # 4. Upcoming task
    task_upcoming = create_test_task(client, headers, "Upcoming Task", due_date=tomorrow_str, status="Todo")

    # Fetch calendar summary
    res_sum = client.get(f"{settings.API_V1_STR}/calendar/summary", headers=headers)
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["overdue"] >= 1
    assert summary["due_today"] >= 1
    assert summary["completed"] >= 1
    assert summary["upcoming_7_days"] >= 1

    # Check task flags in calendar view
    res_cal = client.get(f"{settings.API_V1_STR}/calendar?view=agenda", headers=headers)
    assert res_cal.status_code == 200
    items = {item["task_id"]: item for item in res_cal.json()["tasks"]}

    assert items[task_overdue["id"]]["is_overdue"] is True
    assert items[task_completed["id"]]["is_overdue"] is False
    assert items[task_completed["id"]]["is_completed"] is True

# --------------------------------------------------------------------------
# 3. Task Scheduling, Drag & Drop Reschedule, and Conflict Detection
# --------------------------------------------------------------------------
def test_task_scheduling_reschedule_and_conflicts(client):
    headers, user_id = get_auth_headers(client, "sched_tester")
    now = datetime.now(timezone.utc)

    task = create_test_task(client, headers, "Unscheduled Task")

    # 1. Reschedule task using drag-and-drop endpoint
    new_start = now + timedelta(hours=2)
    new_end = now + timedelta(hours=3)
    res_move = client.post(
        f"{settings.API_V1_STR}/calendar/reschedule",
        json={
            "task_id": task["id"],
            "new_start": new_start.isoformat(),
            "new_end": new_end.isoformat(),
            "duration_minutes": 60,
            "new_due_date": new_start.strftime("%Y-%m-%d"),
            "is_all_day": False,
        },
        headers=headers,
    )
    assert res_move.status_code == 200
    moved_item = res_move.json()
    assert moved_item["duration_minutes"] == 60
    assert moved_item["due_date"] == new_start.strftime("%Y-%m-%d")

    # 2. Reject negative duration
    bad_res = client.post(
        f"{settings.API_V1_STR}/calendar/reschedule",
        json={"task_id": task["id"], "duration_minutes": -10},
        headers=headers,
    )
    assert bad_res.status_code == 400

    # 3. Create overlapping task to test conflict detection
    task2 = create_test_task(
        client,
        headers,
        "Conflicting Overlap Task",
        scheduled_start=new_start + timedelta(minutes=15),
    )
    # Check conflicts
    conflicts_res = client.get(f"{settings.API_V1_STR}/calendar/conflicts", headers=headers)
    assert conflicts_res.status_code == 200
    conflicts = conflicts_res.json()
    assert len(conflicts) >= 1
    assert any(c["conflict_type"] == "OVERLAP" for c in conflicts)

    # 4. Test PATCH /tasks/{task_id}/schedule
    patch_res = client.patch(
        f"{settings.API_V1_STR}/tasks/{task['id']}/schedule",
        json={"estimated_duration_minutes": 90, "is_all_day": True},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["estimated_duration_minutes"] == 90
    assert patch_res.json()["is_all_day"] is True

# --------------------------------------------------------------------------
# 4. Reminders Full CRUD, Snooze, Acknowledge, and Cancellation
# --------------------------------------------------------------------------
def test_reminders_full_crud_and_lifecycle(client):
    headers, user_id = get_auth_headers(client, "reminders_tester")
    now = datetime.now(timezone.utc)
    task = create_test_task(client, headers, "Task for Reminder")

    # 1. Create Reminder
    sched_time = now + timedelta(hours=4)
    create_res = client.post(
        f"{settings.API_V1_STR}/reminders",
        json={
            "task_id": task["id"],
            "title": "Security Posture Review",
            "description": "Double check SOC-2 evidence logs",
            "scheduled_at": sched_time.isoformat(),
            "reminder_type": "DUE_DATE",
            "delivery_channel": "IN_APP",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    reminder = create_res.json()
    rem_id = reminder["id"]
    assert reminder["status"] == "PENDING"
    assert reminder["title"] == "Security Posture Review"

    # 2. List Reminders
    list_res = client.get(f"{settings.API_V1_STR}/reminders?status=PENDING", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Get Reminder by ID
    get_res = client.get(f"{settings.API_V1_STR}/reminders/{rem_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == rem_id

    # 4. Update Reminder
    patch_res = client.patch(
        f"{settings.API_V1_STR}/reminders/{rem_id}",
        json={"title": "Updated Review Title", "delivery_channel": "BOTH"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Review Title"
    assert patch_res.json()["delivery_channel"] == "BOTH"

    # 5. Snooze Reminder
    snooze_res = client.post(
        f"{settings.API_V1_STR}/reminders/{rem_id}/snooze",
        json={"snooze_minutes": 30},
        headers=headers,
    )
    assert snooze_res.status_code == 200
    assert snooze_res.json()["status"] == "SNOOZED"
    assert snooze_res.json()["snoozed_until"] is not None

    # 6. Acknowledge Reminder
    ack_res = client.post(
        f"{settings.API_V1_STR}/reminders/{rem_id}/acknowledge",
        headers=headers,
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "DELIVERED"
    assert ack_res.json()["acknowledged_at"] is not None

    # 7. Cancel Reminder
    cancel_res = client.post(
        f"{settings.API_V1_STR}/reminders/{rem_id}/cancel",
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # 8. Delete Reminder (Task must NOT be deleted)
    del_res = client.delete(f"{settings.API_V1_STR}/reminders/{rem_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirm task still exists
    task_check = client.get(f"{settings.API_V1_STR}/tasks/{task['id']}", headers=headers)
    assert task_check.status_code == 200

# --------------------------------------------------------------------------
# 5. Reminder Delivery Engine & Background Processing
# --------------------------------------------------------------------------
def test_reminder_delivery_engine_and_processing(client):
    headers, user_id = get_auth_headers(client, "engine_tester")
    now = datetime.now(timezone.utc)
    task = create_test_task(client, headers, "Task Due Immediately")

    # Create a reminder scheduled in the past
    past_sched = now - timedelta(minutes=5)
    create_res = client.post(
        f"{settings.API_V1_STR}/reminders",
        json={
            "task_id": task["id"],
            "title": "Immediate Urgent Reminder",
            "description": "This reminder is due now",
            "scheduled_at": past_sched.isoformat(),
            "reminder_type": "DUE_DATE",
            "delivery_channel": "IN_APP",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    rem_id = create_res.json()["id"]

    # Trigger delivery process
    proc_res = client.post(f"{settings.API_V1_STR}/reminders/process", headers=headers)
    assert proc_res.status_code == 200
    result = proc_res.json()
    assert result["processed_count"] >= 1
    assert result["delivered_count"] >= 1

    # Verify reminder status is DELIVERED
    check_rem = client.get(f"{settings.API_V1_STR}/reminders/{rem_id}", headers=headers)
    assert check_rem.status_code == 200
    assert check_rem.json()["status"] == "DELIVERED"
    assert check_rem.json()["delivered_at"] is not None

    # Verify notification created in in-app notifications
    notifs_res = client.get(f"{settings.API_V1_STR}/notifications", headers=headers)
    assert notifs_res.status_code == 200
    notifs = notifs_res.json()
    assert any("Immediate Urgent Reminder" in n["title"] for n in notifs)

# --------------------------------------------------------------------------
# 6. Recurring Tasks and Instance Generation
# --------------------------------------------------------------------------
def test_recurring_tasks_and_instance_generation(client):
    headers, user_id = get_auth_headers(client, "recurrence_tester")
    task = create_test_task(client, headers, "Weekly Team Sync Task")

    # 1. Set Recurrence Rule
    rec_res = client.post(
        f"{settings.API_V1_STR}/calendar/recurrence/{task['id']}",
        json={
            "frequency": "WEEKLY",
            "interval": 1,
            "max_occurrences": 4,
        },
        headers=headers,
    )
    assert rec_res.status_code == 200
    rule = rec_res.json()
    assert rule["frequency"] == "WEEKLY"
    assert rule["interval"] == 1
    assert rule["max_occurrences"] == 4
    assert rule["is_active"] is True

    # 2. Get Recurrence Rule
    get_rule = client.get(f"{settings.API_V1_STR}/calendar/recurrence/{task['id']}", headers=headers)
    assert get_rule.status_code == 200
    assert get_rule.json()["task_id"] == task["id"]

    # 3. Generate Next Occurrence
    next_res = client.post(f"{settings.API_V1_STR}/calendar/recurrence/{task['id']}/generate-next", headers=headers)
    assert next_res.status_code == 200
    assert next_res.json()["status"] == "success"
    new_task_id = next_res.json()["new_task_id"]

    # Verify newly generated task
    new_task = client.get(f"{settings.API_V1_STR}/tasks/{new_task_id}", headers=headers)
    assert new_task.status_code == 200
    assert "Occurrence #1" in new_task.json()["title"]
    assert new_task.json()["status"] == "Todo"

    # 4. Delete Recurrence Rule
    del_res = client.delete(f"{settings.API_V1_STR}/calendar/recurrence/{task['id']}", headers=headers)
    assert del_res.status_code == 204

# --------------------------------------------------------------------------
# 7. Multi-Tenant Security & IDOR Isolation
# --------------------------------------------------------------------------
def test_calendar_and_reminder_security_isolation(client):
    headers_a, user_a_id = get_auth_headers(client, "tenant_a")
    headers_b, user_b_id = get_auth_headers(client, "tenant_b")

    # User A creates a task and reminder
    task_a = create_test_task(client, headers_a, "Tenant A Private Task")
    rem_a_res = client.post(
        f"{settings.API_V1_STR}/reminders",
        json={
            "task_id": task_a["id"],
            "title": "Private Tenant A Reminder",
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
        },
        headers=headers_a,
    )
    assert rem_a_res.status_code == 201
    rem_a_id = rem_a_res.json()["id"]

    # User B attempts to access User A's reminder -> 404 (IDOR protection)
    b_get = client.get(f"{settings.API_V1_STR}/reminders/{rem_a_id}", headers=headers_b)
    assert b_get.status_code == 404

    # User B attempts to reschedule User A's task -> 403 or 404
    b_resched = client.post(
        f"{settings.API_V1_STR}/calendar/reschedule",
        json={"task_id": task_a["id"], "duration_minutes": 60},
        headers=headers_b,
    )
    assert b_resched.status_code in [403, 404]

    # User B attempts to delete User A's reminder -> 404
    b_del = client.delete(f"{settings.API_V1_STR}/reminders/{rem_a_id}", headers=headers_b)
    assert b_del.status_code == 404
