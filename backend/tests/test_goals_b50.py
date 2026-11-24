"""
Integration and Unit Tests for Module B50: Goals, OKRs & Milestones Management.
Verifies goal creation, hierarchy cycle detection, key result measurement formulas,
milestone dependencies, task linking, check-in workflows, and explainable health evaluations.
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.models.collaboration import Workspace
from app.models.project import Project
from app.models.task import Task
from app.models.goals import (
    Goal,
    KeyResult,
    KeyResultProgressHistory,
    GoalMilestone,
    MilestoneDependency,
    GoalCheckIn,
)
from app.services import goal_service
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
def setup_b50_data(db_session: Session):
    timestamp = int(datetime.now(timezone.utc).timestamp())
    user = User(
        name="OKR Manager",
        email=f"okr_mgr_{timestamp}@example.com",
        hashed_password="hashed_pw_okr",
        role="ADMIN",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    ws = Workspace(
        name=f"OKR Workspace {timestamp}",
        owner_id=user.id,
    )
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)

    project = Project(
        name=f"Strategic Project {timestamp}",
        workspace_id=ws.id,
        created_by=user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    task1 = Task(
        id=f"b50_task_1_{timestamp}",
        title="Deliver MVP Authentication",
        user_id=user.id,
        project_id=project.id,
        workspace_id=ws.id,
        status="Completed",
        progress_percent=100.0,
    )
    task2 = Task(
        id=f"b50_task_2_{timestamp}",
        title="Implement Push Notifications",
        user_id=user.id,
        project_id=project.id,
        workspace_id=ws.id,
        status="In Progress",
        progress_percent=50.0,
    )
    db_session.add_all([task1, task2])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "user": user,
        "workspace": ws,
        "project": project,
        "task1": task1,
        "task2": task2,
        "headers": headers,
    }


def test_goal_creation_and_hierarchy(client, setup_b50_data, db_session):
    headers = setup_b50_data["headers"]
    
    # 1. Create Parent Goal
    res = client.post(
        "/api/v1/goals",
        json={
            "title": "Scale Platform Reliability",
            "description": "Achieve 99.99% uptime and enhance service resilience",
            "goal_level": "ORGANIZATIONAL",
            "priority": "HIGH",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "target_date": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        },
        headers=headers,
    )
    assert res.status_code == 201
    parent_goal = res.json()
    assert parent_goal["title"] == "Scale Platform Reliability"
    assert parent_goal["goal_level"] == "ORGANIZATIONAL"

    # 2. Create Child Goal
    res_child = client.post(
        "/api/v1/goals",
        json={
            "title": "Zero Downtime Deployments",
            "goal_level": "TEAM",
            "parent_goal_id": parent_goal["id"],
        },
        headers=headers,
    )
    assert res_child.status_code == 201
    child_goal = res_child.json()
    assert child_goal["parent_goal_id"] == parent_goal["id"]

    # 3. Test Cycle Prevention
    with pytest.raises(ValueError, match="Circular goal hierarchy detected"):
        goal_service.validate_goal_hierarchy(db_session, goal_id=parent_goal["id"], parent_goal_id=child_goal["id"])


def test_key_result_mathematical_formulas():
    # 1. Increase: from 20 to 100 with current 60 -> ((60-20)/(100-20)) = 50%
    p1 = goal_service.compute_key_result_progress("NUMERIC_INCREASE", 20.0, 100.0, 60.0)
    assert p1 == 50.0

    # 2. Decrease: from 12 days to 4 days with current 8 days -> ((12-8)/(12-4)) = 50%
    p2 = goal_service.compute_key_result_progress("NUMERIC_DECREASE", 12.0, 4.0, 8.0)
    assert p2 == 50.0

    # 3. Percentage: from 0% to 100% with current 75%
    p3 = goal_service.compute_key_result_progress("PERCENTAGE", 0.0, 100.0, 75.0)
    assert p3 == 75.0

    # 4. Binary: 0.0 -> 0%, 1.0 -> 100%
    assert goal_service.compute_key_result_progress("BINARY", 0.0, 1.0, 0.0) == 0.0
    assert goal_service.compute_key_result_progress("BINARY", 0.0, 1.0, 1.0) == 100.0

    # 5. Zero denominator safety
    assert goal_service.compute_key_result_progress("NUMERIC_INCREASE", 50.0, 50.0, 50.0) == 100.0
    assert goal_service.compute_key_result_progress("NUMERIC_INCREASE", 50.0, 50.0, 40.0) == 0.0


def test_key_result_lifecycle_and_history(client, setup_b50_data):
    headers = setup_b50_data["headers"]

    # Create Goal
    g_res = client.post(
        "/api/v1/goals",
        json={"title": "Improve Response Time", "goal_level": "TEAM"},
        headers=headers,
    )
    goal_id = g_res.json()["id"]

    # Add Key Result: Decrease API latency from 250ms to 50ms
    kr_res = client.post(
        f"/api/v1/goals/{goal_id}/key-results",
        json={
            "title": "Reduce p95 API Latency",
            "measurement_type": "NUMERIC_DECREASE",
            "starting_value": 250.0,
            "target_value": 50.0,
            "current_value": 250.0,
            "unit": "ms",
        },
        headers=headers,
    )
    assert kr_res.status_code == 201
    kr = kr_res.json()
    assert kr["progress_percent"] == 0.0

    # Update progress: current latency dropped to 150ms -> ((250-150)/(250-50)) = 50%
    up_res = client.post(
        f"/api/v1/goals/key-results/{kr['id']}/progress",
        json={"current_value": 150.0, "comment": "Redis caching implemented."},
        headers=headers,
    )
    assert up_res.status_code == 200
    assert up_res.json()["progress_percent"] == 50.0

    # Verify history snapshots
    hist_res = client.get(f"/api/v1/goals/key-results/{kr['id']}/history", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 2
    assert history[0]["new_value"] == 150.0
    assert history[0]["comment"] == "Redis caching implemented."


def test_milestone_management_and_dependencies(client, setup_b50_data, db_session):
    headers = setup_b50_data["headers"]

    g_res = client.post(
        "/api/v1/goals",
        json={"title": "Product Launch Q1", "goal_level": "ORGANIZATIONAL"},
        headers=headers,
    )
    goal_id = g_res.json()["id"]

    # Milestone 1: Design Phase
    m1_res = client.post(
        f"/api/v1/goals/{goal_id}/milestones",
        json={"title": "Design Specs Approved", "status": "NOT_STARTED"},
        headers=headers,
    )
    m1_id = m1_res.json()["id"]

    # Milestone 2: Build Phase
    m2_res = client.post(
        f"/api/v1/goals/{goal_id}/milestones",
        json={"title": "Backend Engineering Complete", "status": "NOT_STARTED"},
        headers=headers,
    )
    m2_id = m2_res.json()["id"]

    # Add dependency: M2 depends on M1
    dep_res = client.post(
        f"/api/v1/goals/milestones/{m2_id}/dependencies",
        json={"depends_on_milestone_id": m1_id},
        headers=headers,
    )
    assert dep_res.status_code == 200

    # Circular dependency check: M1 depends on M2 should fail
    circ_res = client.post(
        f"/api/v1/goals/milestones/{m1_id}/dependencies",
        json={"depends_on_milestone_id": m2_id},
        headers=headers,
    )
    assert circ_res.status_code == 400

    # Attempt completing M2 before M1 should fail
    fail_comp = client.post(f"/api/v1/goals/milestones/{m2_id}/complete", headers=headers)
    assert fail_comp.status_code == 400

    # Complete M1, then M2 should succeed
    succ_m1 = client.post(f"/api/v1/goals/milestones/{m1_id}/complete", headers=headers)
    assert succ_m1.status_code == 200

    succ_m2 = client.post(f"/api/v1/goals/milestones/{m2_id}/complete", headers=headers)
    assert succ_m2.status_code == 200
    assert succ_m2.json()["status"] == "COMPLETED"


def test_task_linking_and_automated_progress(client, setup_b50_data):
    headers = setup_b50_data["headers"]
    task1 = setup_b50_data["task1"]  # 100% completed
    task2 = setup_b50_data["task2"]  # 50% in progress

    # Create Goal with TASK_COMPLETION Key Result
    g_res = client.post(
        "/api/v1/goals",
        json={"title": "Engineering Deliverables", "goal_level": "TEAM"},
        headers=headers,
    )
    goal_id = g_res.json()["id"]

    kr_res = client.post(
        f"/api/v1/goals/{goal_id}/key-results",
        json={
            "title": "Complete Core Tasks",
            "measurement_type": "TASK_COMPLETION",
            "starting_value": 0.0,
            "target_value": 2.0,
            "unit": "tasks",
        },
        headers=headers,
    )
    kr_id = kr_res.json()["id"]

    # Link Task 1 and Task 2
    l1 = client.post(f"/api/v1/goals/key-results/{kr_id}/tasks", json={"task_id": task1.id, "weight": 1.0}, headers=headers)
    assert l1.status_code == 200

    l2 = client.post(f"/api/v1/goals/key-results/{kr_id}/tasks", json={"task_id": task2.id, "weight": 1.0}, headers=headers)
    assert l2.status_code == 200

    # Detail check: progress should be (1.0 + 0.5) / 2.0 = 75.0%
    goal_detail = client.get(f"/api/v1/goals/{goal_id}", headers=headers).json()
    assert goal_detail["progress_percent"] == 75.0


def test_check_in_and_review_workflow(client, setup_b50_data):
    headers = setup_b50_data["headers"]

    g_res = client.post(
        "/api/v1/goals",
        json={"title": "Quarterly OKR Check-in Target", "goal_level": "ORGANIZATIONAL"},
        headers=headers,
    )
    goal_id = g_res.json()["id"]

    # Submit check-in
    chk_res = client.post(
        f"/api/v1/goals/{goal_id}/check-ins",
        json={
            "progress_percent": 65.0,
            "confidence_score": 5,
            "summary": "Sprint 3 completed ahead of schedule. Core APIs deployed.",
            "blockers": "None",
            "next_steps": "Security penetration testing.",
        },
        headers=headers,
    )
    assert chk_res.status_code == 201
    chk = chk_res.json()
    assert chk["status"] == "SUBMITTED"
    assert chk["confidence_score"] == 5

    # Review check-in
    rev_res = client.post(
        f"/api/v1/goals/check-ins/{chk['id']}/review",
        json={"feedback": "Outstanding progress. Proceeding with QA testing."},
        headers=headers,
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "REVIEWED"
    assert rev_res.json()["reviewer_feedback"] == "Outstanding progress. Proceeding with QA testing."


def test_goals_overview_analytics(client, setup_b50_data):
    headers = setup_b50_data["headers"]

    res = client.get("/api/v1/goals/analytics/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_goals" in data
    assert "active_goals" in data
    assert "level_breakdown" in data
    assert "health_breakdown" in data
    assert data["total_goals"] >= 1
