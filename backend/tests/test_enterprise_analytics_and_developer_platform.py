import pytest
import os
import sys
import uuid
import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add SDK to sys.path for testing
sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sdk", "python"))
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.task import Task
from app.models.collaboration import Workspace, WorkspaceMember, Project
from app.models.enterprise_analytics import ProjectMilestone, ProjectRisk, ResourceCapacity, AnalyticsReport
from app.models.developer_platform import DeveloperApplication, DeveloperCredential, WebhookSubscription
from app.services.developer_service import DeveloperService
from app.services.enterprise_analytics_service import EnterpriseAnalyticsService

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_setup(db_session: Session):
    unique_id = uuid.uuid4().hex[:8]
    email = f"exec_dev_{unique_id}@focusboard.test"
    
    # Create user
    user = User(
        email=email,
        name="Enterprise Executive",
        hashed_password="hashed_pw_test",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create workspace
    workspace = Workspace(
        name=f"Enterprise Workspace {unique_id}",
        owner_id=user.id
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)

    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="OWNER")
    db_session.add(member)

    # Create Project
    project = Project(
        workspace_id=workspace.id,
        name="Alpha Core Infrastructure",
        description="Core platform modernization",
        status="active",
        created_by=user.id,
        deadline=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # Add tasks to project
    t1 = Task(
        id=f"t1_{unique_id}",
        user_id=user.id,
        workspace_id=workspace.id,
        project_id=project.id,
        title="Database Sharding",
        status="completed",
        priority="high",
        assignee_id=user.id
    )
    t2 = Task(
        id=f"t2_{unique_id}",
        user_id=user.id,
        workspace_id=workspace.id,
        project_id=project.id,
        title="API Gateway Modernization",
        status="in_progress",
        priority="medium",
        assignee_id=user.id
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    return {"user": user, "workspace": workspace, "project": project, "tasks": [t1, t2]}


def test_project_health_and_signals(db_session: Session, test_setup):
    project = test_setup["project"]
    health = EnterpriseAnalyticsService.calculate_project_health(db_session, project.id)

    assert health is not None
    assert health["project_id"] == project.id
    assert health["health_score"] >= 80
    assert health["health_status"] == "HEALTHY"
    assert health["total_tasks"] == 2
    assert health["completed_tasks"] == 1
    assert health["completion_rate"] == 50.0
    assert len(health["signals"]) > 0


def test_project_risk_and_milestones(db_session: Session, test_setup):
    project = test_setup["project"]
    user = test_setup["user"]

    # 1. Add Milestone
    ms = ProjectMilestone(
        project_id=project.id,
        title="Phase 1 Alpha Launch",
        status="IN_PROGRESS"
    )
    db_session.add(ms)

    # 2. Add Risk
    risk = ProjectRisk(
        project_id=project.id,
        category="SCHEDULE",
        severity="HIGH",
        title="Third-party vendor delay",
        description="Vendor API migration pending",
        status="ACTIVE"
    )
    db_session.add(risk)
    db_session.commit()

    # Recalculate health with risk
    health = EnterpriseAnalyticsService.calculate_project_health(db_session, project.id)
    assert health["health_score"] < 100  # Penalty deducted for high risk
    assert any("Third-party vendor delay" in s for s in health["signals"])


def test_team_workload_and_capacity(db_session: Session, test_setup):
    workspace = test_setup["workspace"]
    user = test_setup["user"]

    # Set custom capacity
    cap = ResourceCapacity(
        user_id=user.id,
        workspace_id=workspace.id,
        weekly_hours_capacity=30.0
    )
    db_session.add(cap)
    db_session.commit()

    workload = EnterpriseAnalyticsService.get_team_workload(db_session, workspace.id)
    assert workload["workspace_id"] == workspace.id
    assert workload["total_members"] >= 1
    member_data = next(m for m in workload["members"] if m["user_id"] == user.id)
    assert member_data["weekly_capacity_hours"] == 30.0
    assert member_data["assigned_tasks_count"] == 1  # 1 active task


def test_executive_report_generation(db_session: Session, test_setup):
    workspace = test_setup["workspace"]
    user = test_setup["user"]

    report = EnterpriseAnalyticsService.generate_report(
        db=db_session,
        user_id=user.id,
        workspace_id=workspace.id,
        title="Q4 Executive Performance Summary",
        report_type="EXECUTIVE_KPI",
        fmt="CSV"
    )
    assert report.id is not None
    assert report.title == "Q4 Executive Performance Summary"

    csv_data = EnterpriseAnalyticsService.export_report_csv(report)
    assert "Metric,Value" in csv_data
    assert "Total Projects" in csv_data


def test_developer_application_and_credentials(db_session: Session, test_setup):
    workspace = test_setup["workspace"]
    user = test_setup["user"]

    # 1. Create Developer Application
    app = DeveloperApplication(
        user_id=user.id,
        workspace_id=workspace.id,
        name="FocusBoard Slack Bot",
        app_type="INTERNAL"
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # 2. Generate API Key
    cred, plaintext_key = DeveloperService.create_api_key(
        db=db_session,
        application_id=app.id,
        user_id=user.id,
        name="Production Key",
        scopes=["tasks:read", "tasks:write", "projects:read"]
    )
    assert plaintext_key.startswith("fb_live_")
    assert cred.key_prefix.startswith("fb_live_")
    assert cred.hashed_key != plaintext_key  # Must be hashed!

    # 3. Authenticate with Key
    auth_user, auth_cred, scopes = DeveloperService.verify_api_key(
        db=db_session,
        api_key_header=plaintext_key,
        endpoint="/public/v1/tasks"
    )
    assert auth_user.id == user.id
    assert auth_cred.id == cred.id
    assert "tasks:read" in scopes


def test_public_api_endpoints_with_api_key(db_session: Session, test_setup):
    workspace = test_setup["workspace"]
    user = test_setup["user"]

    app = DeveloperApplication(
        user_id=user.id,
        workspace_id=workspace.id,
        name="Mobile Sync Client",
        app_type="PUBLIC"
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # Key with tasks:read only
    _, read_only_key = DeveloperService.create_api_key(
        db=db_session,
        application_id=app.id,
        user_id=user.id,
        name="Read Only Key",
        scopes=["tasks:read"]
    )

    # Key with full tasks:write
    _, full_key = DeveloperService.create_api_key(
        db=db_session,
        application_id=app.id,
        user_id=user.id,
        name="Full Access Key",
        scopes=["tasks:read", "tasks:write", "projects:read"]
    )

    # 1. Read tasks using valid key
    resp = client.get("/api/v1/public/v1/tasks", headers={"X-API-Key": read_only_key})
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 2

    # 2. Attempt to create task with read-only key (should get 403 Forbidden)
    resp = client.post(
        "/api/v1/public/v1/tasks",
        headers={"X-API-Key": read_only_key},
        json={"title": "Unauthorized write task"}
    )
    assert resp.status_code == 403

    # 3. Create task with full access key and idempotency key
    idem_key = f"idem_{int(datetime.now(timezone.utc).timestamp())}"
    resp = client.post(
        "/api/v1/public/v1/tasks",
        headers={"X-API-Key": full_key, "Idempotency-Key": idem_key},
        json={"title": "Public API Created Task", "priority": "high", "category": "Testing"}
    )
    assert resp.status_code == 201
    created_task = resp.json()
    assert created_task["title"] == "Public API Created Task"

    # 4. Duplicate request with same Idempotency-Key returns cached task
    resp_dup = client.post(
        "/api/v1/public/v1/tasks",
        headers={"X-API-Key": full_key, "Idempotency-Key": idem_key},
        json={"title": "Public API Created Task", "priority": "high", "category": "Testing"}
    )
    assert resp_dup.status_code == 201
    assert resp_dup.json()["id"] == created_task["id"]


def test_webhook_event_dispatch_and_hmac(db_session: Session, test_setup):
    workspace = test_setup["workspace"]
    user = test_setup["user"]

    secret = "whsec_test_secret_12345678"
    sub = WebhookSubscription(
        user_id=user.id,
        workspace_id=workspace.id,
        target_url="https://api.external-partner.com/webhook",
        secret_key=secret,
        events_json=json.dumps(["task.created", "task.updated"]),
        is_active=True
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    # Trigger event
    payload = {"event": "task.created", "task_id": "test-t-1", "title": "Check signature"}
    deliveries = DeveloperService.trigger_webhook_event(
        db=db_session,
        workspace_id=workspace.id,
        event_type="task.created",
        payload=payload
    )

    assert len(deliveries) == 1
    delivery = deliveries[0]
    assert delivery.is_success is True

    # Test HMAC verification logic
    ts = int(datetime.now(timezone.utc).timestamp())
    payload_str = json.dumps(payload)
    sig = DeveloperService.generate_webhook_signature(secret, payload_str, ts)
    header = f"t={ts},v1={sig}"

    from focusboard_sdk.client import FocusBoardClient
    is_valid = FocusBoardClient.verify_webhook_signature(payload_str, header, secret)
    assert is_valid is True

    # Verification should fail with incorrect secret
    assert FocusBoardClient.verify_webhook_signature(payload_str, header, "wrong_secret") is False
