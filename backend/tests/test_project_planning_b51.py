"""Automated Pytest Suite for Module B51: Advanced Project Planning & Scheduling."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, Base, SessionLocal
from app.models.user import User


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
from app.models.organization import Organization
from app.models.collaboration import Workspace
from app.models.project import Project
from app.models.task import Task, TaskDependency
from app.models.project_planning import (
    ProjectSchedule,
    ProjectBaseline,
    ProjectBudget,
    ProjectScheduleScenario,
)
from app.services.project_planning_service import ProjectPlanningService
from app.core.security import create_access_token


@pytest.fixture(scope="module")
def test_setup(db_session: Session):
    # Ensure fresh DB state
    timestamp = int(datetime.now(timezone.utc).timestamp())
    user = User(
        name="Project Planner",
        email=f"planner_{timestamp}@example.com",
        hashed_password="hashed_test_password",
        role="ADMIN",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    ws = Workspace(
        name=f"Engineering Workspace {timestamp}",
        owner_id=user.id,
    )
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)

    project = Project(
        name="Enterprise Infrastructure Migration",
        description="Core platform replatforming and database clustering",
        workspace_id=ws.id,
        created_by=user.id,
        status="ACTIVE",
        start_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
        due_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # Add 3 test tasks
    t1 = Task(
        id=f"plan_t1_{user.id}",
        title="Architecture Design Signoff",
        project_id=project.id,
        user_id=user.id,
        status="Completed",
        estimated_duration_minutes=8 * 60,  # 1 day
    )
    t2 = Task(
        id=f"plan_t2_{user.id}",
        title="Cluster Provisioning & Networking",
        project_id=project.id,
        user_id=user.id,
        status="In Progress",
        estimated_duration_minutes=16 * 60,  # 2 days
    )
    t3 = Task(
        id=f"plan_t3_{user.id}",
        title="Live Traffic Cutover",
        project_id=project.id,
        user_id=user.id,
        status="Todo",
        estimated_duration_minutes=8 * 60,  # 1 day
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "user": user,
        "project": project,
        "tasks": [t1, t2, t3],
        "headers": headers,
    }


def test_project_schedule_and_settings(client: TestClient, test_setup, db_session: Session):
    project = test_setup["project"]
    headers = test_setup["headers"]

    # 1. Fetch Planning Overview
    resp = client.get(f"/api/v1/projects/{project.id}/planning", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"]["name"] == "Enterprise Infrastructure Migration"
    assert "schedule" in data
    assert data["tasks_summary"]["total"] == 3

    # 2. Update Settings
    update_resp = client.put(
        f"/api/v1/projects/{project.id}/planning",
        headers=headers,
        json={
            "planning_mode": "CPM_DRIVEN",
            "working_hours_per_day": 8.0,
            "working_days": ["MON", "TUE", "WED", "THU", "FRI"],
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["planning_mode"] == "CPM_DRIVEN"


def test_dependency_engine_and_cycle_prevention(client: TestClient, test_setup, db_session: Session):
    project = test_setup["project"]
    t1, t2, t3 = test_setup["tasks"]
    headers = test_setup["headers"]

    # Create dependency: t1 -> t2 (t2 depends on t1)
    d1 = client.post(
        f"/api/v1/projects/{project.id}/planning/dependencies",
        headers=headers,
        json={
            "task_id": t2.id,
            "depends_on_task_id": t1.id,
            "dependency_type": "FINISH_TO_START",
            "lag_duration": 1.0,
        },
    )
    assert d1.status_code == 201
    assert d1.json()["dependency_type"] == "FINISH_TO_START"
    assert d1.json()["lag_duration"] == 1.0

    # Create dependency: t2 -> t3 (t3 depends on t2)
    d2 = client.post(
        f"/api/v1/projects/{project.id}/planning/dependencies",
        headers=headers,
        json={
            "task_id": t3.id,
            "depends_on_task_id": t2.id,
            "dependency_type": "FINISH_TO_START",
        },
    )
    assert d2.status_code == 201

    # Attempt circular dependency: t1 depends on t3 (creates cycle t1 -> t2 -> t3 -> t1)
    cycle_res = client.post(
        f"/api/v1/projects/{project.id}/planning/dependencies",
        headers=headers,
        json={
            "task_id": t1.id,
            "depends_on_task_id": t3.id,
        },
    )
    assert cycle_res.status_code == 400
    assert "Circular dependency detected" in cycle_res.json()["detail"]

    # Attempt self-dependency: t1 depends on t1
    self_res = client.post(
        f"/api/v1/projects/{project.id}/planning/dependencies",
        headers=headers,
        json={
            "task_id": t1.id,
            "depends_on_task_id": t1.id,
        },
    )
    assert self_res.status_code == 400
    assert "Self-dependencies are not allowed" in self_res.json()["detail"]


def test_critical_path_method_cpm(client: TestClient, test_setup, db_session: Session):
    project = test_setup["project"]
    t1, t2, t3 = test_setup["tasks"]
    headers = test_setup["headers"]

    # Ensure chain t1 (1d) -> t2 (2d) -> t3 (1d) exists
    for (succ, pred) in [(t2.id, t1.id), (t3.id, t2.id)]:
        existing = (
            db_session.query(TaskDependency)
            .filter(TaskDependency.task_id == succ, TaskDependency.depends_on_task_id == pred)
            .first()
        )
        if not existing:
            ProjectPlanningService.create_task_dependency(
                db_session, project.id, task_id=succ, depends_on_task_id=pred, lag_duration=0.0
            )

    cpm_res = client.get(f"/api/v1/projects/{project.id}/critical-path", headers=headers)
    assert cpm_res.status_code == 200
    data = cpm_res.json()
    assert data["critical_tasks_count"] == 3
    # 1 day (t1) + 1 day lag + 2 days (t2) + 1 day (t3) = 5.0 days
    assert data["critical_path_duration_days"] == 5.0
    critical_ids = [item["task_id"] for item in data["critical_path"]]
    assert t1.id in critical_ids
    assert t2.id in critical_ids
    assert t3.id in critical_ids


def test_baseline_management_and_comparison(client: TestClient, test_setup, db_session: Session):
    project = test_setup["project"]
    headers = test_setup["headers"]

    # 1. Create Baseline
    create_res = client.post(
        f"/api/v1/projects/{project.id}/baselines",
        headers=headers,
        json={
            "name": "Q4 Initial Approved Plan",
            "description": "Baseline before sprint kickoff",
        },
    )
    assert create_res.status_code == 201
    baseline_id = create_res.json()["id"]
    assert create_res.json()["version"] == 1

    # 2. Compare baseline with current
    cmp_res = client.get(f"/api/v1/baselines/{baseline_id}/comparison", headers=headers)
    assert cmp_res.status_code == 200
    data = cmp_res.json()
    assert data["baseline_name"] == "Q4 Initial Approved Plan"
    assert len(data["task_variances"]) == 3


def test_project_budget_and_cost_records(client: TestClient, test_setup, db_session: Session):
    project = test_setup["project"]
    headers = test_setup["headers"]

    # 1. Update Budget
    b_res = client.put(
        f"/api/v1/projects/{project.id}/budget",
        headers=headers,
        json={
            "total_budget": 50000.0,
            "currency": "USD",
            "notes": "Approved Q4 budget",
            "is_approved": True,
        },
    )
    assert b_res.status_code == 200
    assert b_res.json()["total_budget"] == 50000.0

    # 2. Record Actual Cost
    cost_res = client.post(
        f"/api/v1/projects/{project.id}/budget/costs",
        headers=headers,
        json={
            "description": "Cloud DB cluster provisioning",
            "amount": 12500.0,
            "record_type": "ACTUAL",
        },
    )
    assert cost_res.status_code == 201

    # 3. Verify Budget Summary
    summary_res = client.get(f"/api/v1/projects/{project.id}/budget", headers=headers)
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert data["total_budget"] == 50000.0
    assert data["actual_cost"] == 12500.0
    assert data["remaining_budget"] == 37500.0
    assert data["is_over_budget"] is False


def test_schedule_forecasting(client: TestClient, test_setup, db_session: Session):
    project = test_setup["project"]
    headers = test_setup["headers"]

    forecast_res = client.get(f"/api/v1/projects/{project.id}/forecast", headers=headers)
    assert forecast_res.status_code == 200
    data = forecast_res.json()
    assert data["health_status"] in ("ON_TRACK", "AT_RISK", "DELAYED", "CRITICAL", "INSUFFICIENT_DATA")
    assert "forecast_completion_date" in data
    assert data["confidence_score"] > 0


def test_what_if_scenario_simulation_and_apply(client: TestClient, test_setup, db_session: Session):
    project = test_setup["project"]
    t1, t2, t3 = test_setup["tasks"]
    headers = test_setup["headers"]

    # 1. Create Scenario
    scen_res = client.post(
        f"/api/v1/projects/{project.id}/scenarios",
        headers=headers,
        json={
            "name": "Compressed SRE Sprint",
            "description": "Simulating doubling capacity to halve cluster provisioning time",
        },
    )
    assert scen_res.status_code == 201
    scenario_id = scen_res.json()["id"]

    # 2. Add Task Change to Scenario (simulate t2 duration dropping from 2d to 0.5d)
    chg_res = client.post(
        f"/api/v1/scenarios/{scenario_id}/changes",
        headers=headers,
        json={
            "task_id": t2.id,
            "proposed_duration_days": 0.5,
            "proposed_priority": "Critical",
        },
    )
    assert chg_res.status_code == 200

    # 3. Run Simulation without mutating real DB
    sim_res = client.post(f"/api/v1/scenarios/{scenario_id}/simulate", headers=headers)
    assert sim_res.status_code == 200
    assert sim_res.json()["status"] == "SIMULATED"
    assert "outcomes" in sim_res.json()

    # Verify real task was NOT modified yet
    db_session.refresh(t2)
    assert t2.priority != "Critical"

    # 4. Explicitly Apply Scenario
    apply_res = client.post(f"/api/v1/scenarios/{scenario_id}/apply", headers=headers)
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "APPLIED"

    # Verify real task IS now updated
    db_session.refresh(t2)
    assert t2.priority == "Critical"
