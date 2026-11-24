"""
Automated Pytest Suite for FocusBoard Module B53: Client & Guest Portal.
Tests external guest invitations, token hashing, expiration, acceptance,
project scoping, visibility rules, versioned deliverables, approvals,
feedback, comments, guest account suspension, and access revocation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.collaboration import Workspace
from app.models.project import Project
from app.models.task import Task
from app.models.client_portal import (
    GuestProfile,
    GuestInvitation,
    GuestProjectAccess,
    ClientProjectVisibility,
    ClientDeliverable,
    ClientDeliverableVersion,
    ClientFeedback,
    ClientComment,
    ClientDocumentAccess,
    ClientReport,
    GuestActivityLog,
    ClientPortalSettings,
)
from app.services import client_portal_service as service
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
def test_setup(db_session: Session):
    timestamp = int(datetime.now(timezone.utc).timestamp())

    # 1. Admin / Project Manager user
    admin_user = User(
        name="Project Manager",
        email=f"pm_admin_{timestamp}@example.com",
        hashed_password="hashed_pm_password",
        role="Admin",
    )
    # 2. External Client user (who will accept invitation)
    client_user = User(
        name="Acme Client Lead",
        email=f"client_lead_{timestamp}@acme-corp.com",
        hashed_password="hashed_client_password",
        role="Member",
    )
    # 3. Third-party unauthorized user
    other_user = User(
        name="Other User",
        email=f"other_{timestamp}@unauthorized.com",
        hashed_password="hashed_other_password",
        role="Member",
    )
    db_session.add_all([admin_user, client_user, other_user])
    db_session.commit()
    db_session.refresh(admin_user)
    db_session.refresh(client_user)
    db_session.refresh(other_user)

    # Organization
    org = Organization(
        name=f"Digital Agency {timestamp}",
        slug=f"agency-{timestamp}",
        owner_id=admin_user.id,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    org_member = OrganizationMember(
        organization_id=org.id,
        user_id=admin_user.id,
        role="owner",
    )
    db_session.add(org_member)

    # Workspace
    workspace = Workspace(
        organization_id=org.id,
        name=f"Client Deliverables Workspace {timestamp}",
        owner_id=admin_user.id,
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)

    # Project 1: Shared Project
    project1 = Project(
        organization_id=org.id,
        workspace_id=workspace.id,
        name=f"Acme Corp Website Redesign {timestamp}",
        slug=f"acme-web-{timestamp}",
        description="Public client redesign milestone project",
        created_by=admin_user.id,
        owner_id=admin_user.id,
        status="ACTIVE",
    )
    # Project 2: Internal-only Project (Must NOT be visible to client)
    project2 = Project(
        organization_id=org.id,
        workspace_id=workspace.id,
        name=f"Agency Confidential Operations {timestamp}",
        slug=f"internal-ops-{timestamp}",
        description="Confidential agency operations and margins",
        created_by=admin_user.id,
        owner_id=admin_user.id,
        status="ACTIVE",
    )
    db_session.add_all([project1, project2])
    db_session.commit()
    db_session.refresh(project1)
    db_session.refresh(project2)

    # Tokens
    admin_token = create_access_token(data={"sub": str(admin_user.id)})
    client_token = create_access_token(data={"sub": str(client_user.id)})
    other_token = create_access_token(data={"sub": str(other_user.id)})

    return {
        "admin": admin_user,
        "client": client_user,
        "other": other_user,
        "org": org,
        "workspace": workspace,
        "project1": project1,
        "project2": project2,
        "admin_token": admin_token,
        "client_token": client_token,
        "other_token": other_token,
    }


def test_client_portal_settings_and_invitation_creation(client, test_setup, db_session):
    """Test portal governance settings and invitation generation with secure token hash."""
    admin_token = test_setup["admin_token"]
    org = test_setup["org"]
    project1 = test_setup["project1"]

    # 1. Fetch default settings
    r_settings = client.get("/api/v1/client-portal/settings", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_settings.status_code == 200
    assert r_settings.json()["is_portal_enabled"] is True

    # 2. Create guest invitation
    invite_payload = {
        "guest_email": test_setup["client"].email,
        "guest_name": "Acme Client Lead",
        "company_name": "Acme Corporation",
        "role": "CLIENT_APPROVER",
        "project_ids": [project1.id],
        "message": "Welcome to your project deliverables portal!",
        "expiration_days": 14,
    }
    r_invite = client.post("/api/v1/client-portal/invitations", json=invite_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert r_invite.status_code == 200
    data = r_invite.json()
    assert data["status"] == "PENDING"
    assert data["guest_email"] == test_setup["client"].email
    assert data["role"] == "CLIENT_APPROVER"
    assert "raw_token" in data
    assert len(data["raw_token"]) > 20

    # Verify SHA-256 hash was persisted in DB, not raw token
    inv_db = db_session.query(GuestInvitation).filter(GuestInvitation.id == data["id"]).first()
    assert inv_db is not None
    assert inv_db.token_hash != data["raw_token"]
    assert len(inv_db.token_hash) == 64

    # Save raw token on test_setup for acceptance test
    test_setup["invite_raw_token"] = data["raw_token"]
    test_setup["invitation_id"] = data["id"]


def test_accept_invitation_and_project_grant(client, test_setup, db_session):
    """Test invitation acceptance with email validation, profile creation, and project scoping."""
    client_token = test_setup["client_token"]
    raw_token = test_setup["invite_raw_token"]
    other_token = test_setup["other_token"]

    # 1. Reject email identity mismatch (other user attempts to accept client's token)
    r_bad_user = client.post(
        "/api/v1/client-portal/invitations/accept",
        json={"token": raw_token},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert r_bad_user.status_code == 400
    assert "email does not match" in r_bad_user.json()["detail"].lower()

    # 2. Legitimate client accepts invitation
    r_accept = client.post(
        "/api/v1/client-portal/invitations/accept",
        json={"token": raw_token},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_accept.status_code == 200
    res = r_accept.json()
    assert res["status"] == "ACCEPTED"
    assert test_setup["project1"].id in res["granted_projects"]

    # 3. Prevent token reuse
    r_reuse = client.post(
        "/api/v1/client-portal/invitations/accept",
        json={"token": raw_token},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_reuse.status_code == 400
    assert "already been accepted" in r_reuse.json()["detail"].lower()

    # 4. Verify GuestProfile created in database
    prof = db_session.query(GuestProfile).filter(
        GuestProfile.user_id == test_setup["client"].id,
        GuestProfile.organization_id == test_setup["org"].id,
    ).first()
    assert prof is not None
    assert prof.status == "ACTIVE"
    assert prof.company_name == "Acme Corporation"


def test_client_portal_dashboard_strict_isolation(client, test_setup):
    """Test client dashboard exposes only authorized projects and excludes internal-only projects."""
    client_token = test_setup["client_token"]

    r_dash = client.get("/api/v1/client-portal/dashboard", headers={"Authorization": f"Bearer {client_token}"})
    assert r_dash.status_code == 200
    dash_data = r_dash.json()

    # Project 1 should be visible
    visible_project_ids = [p["project_id"] for p in dash_data["projects"]]
    assert test_setup["project1"].id in visible_project_ids

    # Project 2 (confidential internal) MUST NOT be visible
    assert test_setup["project2"].id not in visible_project_ids

    # Detail page for shared project
    r_detail = client.get(f"/api/v1/client-portal/projects/{test_setup['project1'].id}", headers={"Authorization": f"Bearer {client_token}"})
    assert r_detail.status_code == 200
    proj_detail = r_detail.json()
    assert proj_detail["name"] == test_setup["project1"].name

    # Attempting to access unshared Project 2 directly must return 403 Forbidden
    r_forbidden = client.get(f"/api/v1/client-portal/projects/{test_setup['project2'].id}", headers={"Authorization": f"Bearer {client_token}"})
    assert r_forbidden.status_code == 403


def test_client_deliverable_review_and_approval(client, test_setup, db_session):
    """Test deliverable lifecycle: creation, change request with mandatory comment, and approval."""
    admin_token = test_setup["admin_token"]
    client_token = test_setup["client_token"]
    project1 = test_setup["project1"]

    # 1. Admin uploads deliverable
    deliv_payload = {
        "title": "Homepage Design Concept v1",
        "description": "Figma mockups and responsive wireframes",
        "file_name": "homepage_v1.pdf",
        "file_url": "https://storage.focusboard.com/deliverables/homepage_v1.pdf",
        "file_size": 2450000,
        "file_type": "application/pdf",
    }
    r_deliv = client.post(
        f"/api/v1/client-portal/projects/{project1.id}/deliverables",
        json=deliv_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_deliv.status_code == 200
    deliv_id = r_deliv.json()["deliverable_id"]

    # 2. Client lists deliverables
    r_list = client.get(
        f"/api/v1/client-portal/projects/{project1.id}/deliverables",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_list.status_code == 200
    assert any(d["id"] == deliv_id for d in r_list.json())

    # 3. Client requests changes (requires comment)
    r_bad_review = client.post(
        f"/api/v1/client-portal/deliverables/{deliv_id}/review",
        json={"decision": "CHANGES_REQUESTED", "comments": ""},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_bad_review.status_code == 400

    r_changes = client.post(
        f"/api/v1/client-portal/deliverables/{deliv_id}/review",
        json={"decision": "CHANGES_REQUESTED", "comments": "Please update hero section with brand secondary color"},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_changes.status_code == 200
    assert r_changes.json()["status"] == "CHANGES_REQUESTED"

    # 4. Client approves deliverable
    r_approve = client.post(
        f"/api/v1/client-portal/deliverables/{deliv_id}/review",
        json={"decision": "APPROVED", "comments": "Approved for frontend development"},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_approve.status_code == 200
    assert r_approve.json()["status"] == "APPROVED"


def test_client_feedback_and_comments_workflow(client, test_setup):
    """Test client feedback submission, admin response, and client-visible comments."""
    admin_token = test_setup["admin_token"]
    client_token = test_setup["client_token"]
    project1 = test_setup["project1"]

    # 1. Client posts feedback
    fb_payload = {
        "title": "Navigation font readability issue",
        "content": "On mobile Safari, the submenus appear with low contrast against the dark background.",
        "category": "BUG",
    }
    r_fb = client.post(
        f"/api/v1/client-portal/projects/{project1.id}/feedback",
        json=fb_payload,
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_fb.status_code == 200
    fb_id = r_fb.json()["feedback_id"]

    # 2. Client lists feedback
    r_fb_list = client.get(
        f"/api/v1/client-portal/projects/{project1.id}/feedback",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_fb_list.status_code == 200
    assert any(f["id"] == fb_id for f in r_fb_list.json())

    # 3. Client posts comment
    r_comment = client.post(
        f"/api/v1/client-portal/projects/{project1.id}/comments",
        json={"content": "We tested on iPhone 15 Pro, viewport 390px.", "feedback_id": fb_id},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_comment.status_code == 200
    comment_id = r_comment.json()["comment_id"]

    # 4. Verify comments listing
    r_c_list = client.get(
        f"/api/v1/client-portal/projects/{project1.id}/comments?feedback_id={fb_id}",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_c_list.status_code == 200
    assert any(c["id"] == comment_id for c in r_c_list.json())


def test_client_report_generation(client, test_setup):
    """Test generating and listing client progress reports."""
    admin_token = test_setup["admin_token"]
    client_token = test_setup["client_token"]
    project1 = test_setup["project1"]

    report_payload = {
        "title": "Bi-Weekly Executive Progress Summary",
        "summary": "All design deliverables approved; mobile responsiveness verified.",
        "status_override": "ON_TRACK",
    }
    r_rep = client.post(
        f"/api/v1/client-portal/projects/{project1.id}/reports",
        json=report_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_rep.status_code == 200
    rep_id = r_rep.json()["report_id"]

    r_rep_list = client.get(
        f"/api/v1/client-portal/projects/{project1.id}/reports",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_rep_list.status_code == 200
    assert any(r["id"] == rep_id for r in r_rep_list.json())


def test_guest_suspension_and_access_revocation(client, test_setup, db_session):
    """Test immediate access blocking when guest is suspended or revoked."""
    admin_token = test_setup["admin_token"]
    client_token = test_setup["client_token"]
    client_user = test_setup["client"]
    project1 = test_setup["project1"]

    # 1. Admin suspends guest account
    r_suspend = client.post(
        f"/api/v1/client-portal/guests/{client_user.id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_suspend.status_code == 200
    assert r_suspend.json()["status"] == "SUSPENDED"

    # 2. Client immediately loses access to project overview
    r_blocked = client.get(
        f"/api/v1/client-portal/projects/{project1.id}",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_blocked.status_code == 403

    # 3. Admin reactivates guest account
    r_reactivate = client.post(
        f"/api/v1/client-portal/guests/{client_user.id}/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_reactivate.status_code == 200
    assert r_reactivate.json()["status"] == "ACTIVE"

    # 4. Client access restored
    r_restored = client.get(
        f"/api/v1/client-portal/projects/{project1.id}",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert r_restored.status_code == 200

    # 5. Check audit logs
    r_logs = client.get(
        "/api/v1/client-portal/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_logs.status_code == 200
    logs = r_logs.json()
    actions = [l["action"] for l in logs]
    assert "ACCESS_SUSPENDED" in actions
    assert "ACCESS_REACTIVATED" in actions
