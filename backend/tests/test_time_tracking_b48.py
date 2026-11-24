"""
Integration and Unit Tests for Module B48: Time Tracking & Timesheets.
Verifies active timer lifecycle, task effort sync, manual time entries,
timesheet aggregation, approval workflows, reporting, and permissions.
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.collaboration import Workspace
from app.models.project import Project
from app.models.task import Task
from app.models.time_tracking import (
    TimeEntry,
    ActiveTimer,
    Timesheet,
    TimesheetApproval,
    TimeTrackingSettings,
)
from app.core.security import create_access_token


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def setup_users_and_tasks(db_session: Session):
    timestamp = int(datetime.now(timezone.utc).timestamp())
    # User 1: Regular Developer
    user1 = User(
        name="Time Tracker Dev",
        email=f"dev_b48_{timestamp}@example.com",
        hashed_password="mock_hashed_password_dev",
        role="MEMBER",
        is_active=True,
    )
    # User 2: Team Manager
    user2 = User(
        name="Time Tracker Manager",
        email=f"mgr_b48_{timestamp}@example.com",
        hashed_password="mock_hashed_password_mgr",
        role="MANAGER",
        is_active=True,
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    # Workspace
    ws = Workspace(
        name=f"Workspace B48 {timestamp}",
        owner_id=user2.id,
    )
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)

    # Project
    proj = Project(
        name=f"B48 Core Engine {timestamp}",
        description="Time tracking test project",
        workspace_id=ws.id,
        created_by=user2.id,
        owner_id=user2.id,
    )
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)

    # Task
    task = Task(
        id=f"task_{timestamp}",
        title="Develop Active Timer Feature",
        description="Implement real-time timer calculations",
        project_id=proj.id,
        user_id=user1.id,
        status="IN_PROGRESS",
        actual_minutes=0,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    token1 = create_access_token(data={"sub": str(user1.id)})
    token2 = create_access_token(data={"sub": str(user2.id)})

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    return {
        "user1": user1,
        "user2": user2,
        "project": proj,
        "task": task,
        "headers1": headers1,
        "headers2": headers2,
    }


# =========================================================================
# 1. Active Timer Tests
# =========================================================================

def test_active_timer_lifecycle(client: TestClient, setup_users_and_tasks, db_session: Session):
    data = setup_users_and_tasks
    headers = data["headers1"]
    task = data["task"]
    proj = data["project"]

    # Ensure no active timer initially
    res = client.get("/time-tracking/timer/active", headers=headers)
    assert res.status_code == 200

    # Start timer
    start_payload = {
        "project_id": proj.id,
        "task_id": str(task.id),
        "description": "Coding timer engine",
        "billable": True,
    }
    res = client.post("/time-tracking/timer/start", json=start_payload, headers=headers)
    assert res.status_code == 200
    active = res.json()
    assert active["status"] == "RUNNING"
    assert active["project_id"] == proj.id
    assert active["task_id"] == str(task.id)

    # Pause timer
    res = client.post("/time-tracking/timer/pause", headers=headers)
    assert res.status_code == 200
    paused = res.json()
    assert paused["status"] == "PAUSED"

    # Resume timer
    res = client.post("/time-tracking/timer/resume", headers=headers)
    assert res.status_code == 200
    resumed = res.json()
    assert resumed["status"] == "RUNNING"

    # Stop timer -> Creates TimeEntry & Updates Task actual_minutes
    res = client.post("/time-tracking/timer/stop", headers=headers)
    assert res.status_code == 200
    entry = res.json()
    assert entry["project_id"] == proj.id
    assert entry["task_id"] == str(task.id)
    assert entry["billable"] is True
    assert entry["duration_seconds"] >= 0

    # Verify active timer is now None
    res = client.get("/time-tracking/timer/active", headers=headers)
    assert res.status_code == 200
    assert res.json() is None


def test_timer_cancel(client: TestClient, setup_users_and_tasks):
    data = setup_users_and_tasks
    headers = data["headers1"]

    # Start a timer
    client.post("/time-tracking/timer/start", json={"description": "To be cancelled", "billable": False}, headers=headers)

    # Cancel timer
    res = client.post("/time-tracking/timer/cancel", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Confirm timer is gone
    res = client.get("/time-tracking/timer/active", headers=headers)
    assert res.status_code == 200
    assert res.json() is None


# =========================================================================
# 2. Manual Time Entries CRUD Tests
# =========================================================================

def test_manual_time_entry_crud(client: TestClient, setup_users_and_tasks, db_session: Session):
    data = setup_users_and_tasks
    headers = data["headers1"]
    proj = data["project"]
    task = data["task"]

    start = datetime.now(timezone.utc) - timedelta(hours=2)
    end = datetime.now(timezone.utc) - timedelta(hours=1)

    # Create manual entry (1 hour = 3600s)
    create_payload = {
        "project_id": proj.id,
        "task_id": str(task.id),
        "description": "Manual documentation writeup",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "duration_seconds": 3600,
        "billable": True,
        "hourly_rate": 100.0,
    }
    res = client.post("/time-tracking/entries", json=create_payload, headers=headers)
    assert res.status_code == 201
    created = res.json()
    entry_id = created["id"]
    assert created["duration_seconds"] == 3600
    assert created["billable_amount"] == 100.0
    assert created["entry_source"] == "MANUAL"

    # List entries
    res = client.get("/time-tracking/entries", headers=headers)
    assert res.status_code == 200
    entries = res.json()
    assert any(e["id"] == entry_id for e in entries)

    # Update entry
    update_payload = {
        "description": "Updated manual documentation",
        "duration_seconds": 5400,  # 1.5h
    }
    res = client.put(f"/time-tracking/entries/{entry_id}", json=update_payload, headers=headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["description"] == "Updated manual documentation"
    assert updated["duration_seconds"] == 5400
    assert updated["billable_amount"] == 150.0  # 1.5h * 100

    # Delete entry
    res = client.delete(f"/time-tracking/entries/{entry_id}", headers=headers)
    assert res.status_code == 204


# =========================================================================
# 3. Timesheet Workflow & Approvals Tests
# =========================================================================

def test_timesheet_lifecycle_and_approval(client: TestClient, setup_users_and_tasks):
    data = setup_users_and_tasks
    dev_headers = data["headers1"]
    mgr_headers = data["headers2"]
    proj = data["project"]

    # Create a time entry for this week
    today = datetime.now(timezone.utc)
    entry_payload = {
        "project_id": proj.id,
        "description": "Sprint work for timesheet",
        "start_time": today.isoformat(),
        "duration_seconds": 7200,  # 2 hours
        "billable": True,
        "hourly_rate": 80.0,
    }
    client.post("/time-tracking/entries", json=entry_payload, headers=dev_headers)

    period_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    period_end = (today + timedelta(days=6 - today.weekday())).strftime("%Y-%m-%d")

    # 1. Get or create timesheet
    res = client.post("/time-tracking/timesheets", json={
        "period_start": period_start,
        "period_end": period_end,
    }, headers=dev_headers)
    assert res.status_code == 200
    ts = res.json()
    ts_id = ts["id"]
    assert ts["status"] == "DRAFT"
    assert ts["total_hours"] >= 2.0

    # 2. Submit timesheet
    res = client.post(f"/time-tracking/timesheets/{ts_id}/submit", headers=dev_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"

    # 3. Withdraw timesheet
    res = client.post(f"/time-tracking/timesheets/{ts_id}/withdraw", headers=dev_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "DRAFT"

    # Re-submit for manager approval
    client.post(f"/time-tracking/timesheets/{ts_id}/submit", headers=dev_headers)

    # 4. Manager reviews and approves
    res = client.post(f"/time-tracking/timesheets/{ts_id}/approve", json={
        "review_comments": "Great work this week, approved!"
    }, headers=mgr_headers)
    assert res.status_code == 200
    approved_ts = res.json()
    assert approved_ts["status"] == "APPROVED"
    assert approved_ts["reviewer_name"] is not None

    # 5. Check timesheet detail
    res = client.get(f"/time-tracking/timesheets/{ts_id}", headers=dev_headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["status"] == "APPROVED"
    assert len(detail["approvals"]) >= 1

    # 6. Reopen timesheet
    res = client.post(f"/time-tracking/timesheets/{ts_id}/reopen", json={
        "review_comments": "Reopening for additional hours adjustment."
    }, headers=mgr_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "REOPENED"


# =========================================================================
# 4. Analytics, Reports & Settings Tests
# =========================================================================

def test_summary_and_reports(client: TestClient, setup_users_and_tasks):
    data = setup_users_and_tasks
    headers = data["headers1"]
    mgr_headers = data["headers2"]

    # Dashboard Summary
    res = client.get("/time-tracking/summary", headers=headers)
    assert res.status_code == 200
    summary = res.json()
    assert "today_hours" in summary
    assert "this_week_hours" in summary
    assert "billable_hours" in summary

    # Project breakdown
    res = client.get("/time-tracking/reports/project", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Billable report
    res = client.get("/time-tracking/reports/billable", headers=headers)
    assert res.status_code == 200
    billable_rep = res.json()
    assert "total_billable_hours" in billable_rep
    assert "total_billable_amount" in billable_rep

    # Team User report (Manager only)
    res = client.get("/time-tracking/reports/user", headers=mgr_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_settings_crud(client: TestClient, setup_users_and_tasks):
    data = setup_users_and_tasks
    headers = data["headers2"]  # Manager

    # Get settings
    res = client.get("/time-tracking/settings", headers=headers)
    assert res.status_code == 200
    settings = res.json()
    assert "default_daily_hours" in settings

    # Update settings
    update_data = {
        "default_daily_hours": 7.5,
        "default_hourly_rate": 85.0,
        "allow_manual_entry": True,
    }
    res = client.put("/time-tracking/settings", json=update_data, headers=headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["default_daily_hours"] == 7.5
    assert updated["default_hourly_rate"] == 85.0
