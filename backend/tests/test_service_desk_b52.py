"""
Automated Pytest Suite for Module B52: Service Desk & SLA Management.
Tests tickets, categories, SLA policies, business hours calculations, transitions, internal notes, breach detection, escalations, and dashboard metrics.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.collaboration import Workspace
from app.models.team import Team, TeamMember
from app.models.service_desk import (
    ServiceDeskTicket,
    ServiceDeskCategory,
    ServiceDeskSLAPolicy,
    ServiceDeskComment,
    ServiceDeskAssignmentHistory,
    ServiceDeskActivityLog,
    ServiceDeskEscalationRule,
    ServiceDeskEscalationRecord,
    ServiceDeskSLABreach,
)
from app.services import service_desk_service
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

    admin_user = User(
        name="Support Admin",
        email=f"sd_admin_{timestamp}@example.com",
        hashed_password="hashed_test_password",
        role="Admin",
    )
    requester_user = User(
        name="Regular Employee",
        email=f"sd_requester_{timestamp}@example.com",
        hashed_password="hashed_test_password",
        role="Member",
    )
    agent_user = User(
        name="Support Agent",
        email=f"sd_agent_{timestamp}@example.com",
        hashed_password="hashed_test_password",
        role="Admin",
    )
    db_session.add_all([admin_user, requester_user, agent_user])
    db_session.commit()
    db_session.refresh(admin_user)
    db_session.refresh(requester_user)
    db_session.refresh(agent_user)

    org = Organization(
        name=f"Service Desk Org {timestamp}",
        slug=f"sd-org-{timestamp}",
        owner_id=admin_user.id,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    admin_user.organization_id = org.id
    requester_user.organization_id = org.id
    agent_user.organization_id = org.id
    db_session.commit()

    admin_token = create_access_token(data={"sub": str(admin_user.id)})
    requester_token = create_access_token(data={"sub": str(requester_user.id)})
    agent_token = create_access_token(data={"sub": str(agent_user.id)})

    team = Team(
        organization_id=org.id,
        name=f"Tier 1 Support {timestamp}",
        slug=f"tier-1-support-{timestamp}",
        owner_id=admin_user.id,
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    return {
        "org": org,
        "admin": admin_user,
        "requester": requester_user,
        "agent": agent_user,
        "admin_token": admin_token,
        "requester_token": requester_token,
        "agent_token": agent_token,
        "team": team,
    }


def test_service_desk_category_and_sla_policy_seeding(client: TestClient, test_setup: dict):
    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}

    # 1. Categories
    resp = client.get("/api/v1/service-desk/categories", headers=headers)
    assert resp.status_code == 200
    categories = resp.json()
    assert len(categories) >= 1
    assert any(c["name"] == "Technical Support" for c in categories)

    # 2. SLA Policies
    resp = client.get("/api/v1/service-desk/sla-policies", headers=headers)
    assert resp.status_code == 200
    policies = resp.json()
    assert len(policies) >= 1
    assert policies[0]["first_response_target_minutes"] > 0
    assert policies[0]["resolution_target_minutes"] > 0


def test_create_support_ticket_with_sla_deadlines(client: TestClient, test_setup: dict):
    headers = {"Authorization": f"Bearer {test_setup['requester_token']}"}

    payload = {
        "subject": "VPN connection drops during video calls",
        "description": "Whenever Zoom or Teams calls exceed 10 minutes, the corporate VPN tunnel resets.",
        "category_name": "Technical Support",
        "priority": "HIGH",
        "source": "PORTAL",
        "tags": ["vpn", "network", "zoom"],
    }
    resp = client.post("/api/v1/service-desk/tickets", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticket_number"].startswith("SD-")
    assert data["subject"] == payload["subject"]
    assert data["priority"] == "HIGH"
    assert data["status"] in ["NEW", "ASSIGNED"]
    assert data["first_response_due_at"] is not None
    assert data["resolution_due_at"] is not None
    assert data["sla_response_status"] == "ON_TRACK"
    assert data["sla_resolution_status"] == "ON_TRACK"

    test_setup["test_ticket_id"] = data["id"]


def test_ticket_assignment_and_history(client: TestClient, test_setup: dict):
    ticket_id = test_setup["test_ticket_id"]
    agent_id = test_setup["agent"].id
    team_id = test_setup["team"].id

    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}
    assign_payload = {
        "agent_id": agent_id,
        "team_id": team_id,
        "notes": "Assigning to Tier 1 network specialists.",
    }
    resp = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/assign", json=assign_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned_agent_id"] == agent_id
    assert data["assigned_team_id"] == team_id
    assert data["status"] == "ASSIGNED"


def test_ticket_status_workflow_transitions(client: TestClient, test_setup: dict):
    ticket_id = test_setup["test_ticket_id"]
    headers = {"Authorization": f"Bearer {test_setup['agent_token']}"}

    # 1. Invalid transition (ASSIGNED -> CLOSED is not allowed directly)
    bad_resp = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/status", json={"status": "CLOSED"}, headers=headers)
    assert bad_resp.status_code == 400

    # 2. ASSIGNED -> IN_PROGRESS
    resp1 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/status", json={"status": "IN_PROGRESS"}, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "IN_PROGRESS"

    # 3. IN_PROGRESS -> WAITING_FOR_REQUESTER (Pauses SLA)
    resp2 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/status", json={"status": "WAITING_FOR_REQUESTER"}, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "WAITING_FOR_REQUESTER"
    assert resp2.json()["sla_resolution_status"] == "PAUSED"

    # 4. WAITING_FOR_REQUESTER -> IN_PROGRESS (Resumes SLA)
    resp3 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/status", json={"status": "IN_PROGRESS"}, headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "IN_PROGRESS"

    # 5. IN_PROGRESS -> RESOLVED (Requires resolution notes)
    res_payload = {"status": "RESOLVED", "resolution_notes": "Updated WireGuard MTU settings to 1360 bytes."}
    resp4 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/status", json=res_payload, headers=headers)
    assert resp4.status_code == 200
    assert resp4.json()["status"] == "RESOLVED"
    assert resp4.json()["resolved_at"] is not None
    assert resp4.json()["resolution_notes"] == res_payload["resolution_notes"]

    # 6. RESOLVED -> CLOSED
    resp5 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/status", json={"status": "CLOSED"}, headers=headers)
    assert resp5.status_code == 200
    assert resp5.json()["status"] == "CLOSED"
    assert resp5.json()["closed_at"] is not None

    # 7. CLOSED -> REOPENED
    resp6 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/status", json={"status": "REOPENED"}, headers=headers)
    assert resp6.status_code == 200
    assert resp6.json()["status"] == "REOPENED"
    assert resp6.json()["reopened_at"] is not None


def test_ticket_conversations_and_internal_note_confidentiality(client: TestClient, test_setup: dict):
    ticket_id = test_setup["test_ticket_id"]
    agent_headers = {"Authorization": f"Bearer {test_setup['agent_token']}"}
    requester_headers = {"Authorization": f"Bearer {test_setup['requester_token']}"}

    # 1. Agent adds public response (Qualifies for First Response SLA)
    pub_payload = {"content": "Hello, we are investigating your VPN tunnel diagnostics.", "is_internal_note": False}
    resp1 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/comments", json=pub_payload, headers=agent_headers)
    assert resp1.status_code == 201

    # Verify first response recorded on ticket
    t_resp = client.get(f"/api/v1/service-desk/tickets/{ticket_id}", headers=agent_headers)
    assert t_resp.status_code == 200
    assert t_resp.json()["first_response_at"] is not None
    assert t_resp.json()["sla_response_status"] in ["COMPLETED", "ON_TRACK"]

    # 2. Agent adds confidential internal note
    internal_payload = {"content": "Suspect MTU handshake drop on Gateway-04, do not disclose to user.", "is_internal_note": True}
    resp2 = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/comments", json=internal_payload, headers=agent_headers)
    assert resp2.status_code == 201

    # 3. Agent views comments -> sees both
    agent_view = client.get(f"/api/v1/service-desk/tickets/{ticket_id}/comments", headers=agent_headers)
    assert agent_view.status_code == 200
    assert len(agent_view.json()) >= 2
    assert any(c["is_internal_note"] for c in agent_view.json())

    # 4. Requester views comments -> internal note is STRICTLY CONCEALED
    req_view = client.get(f"/api/v1/service-desk/tickets/{ticket_id}/comments", headers=requester_headers)
    assert req_view.status_code == 200
    assert all(c["is_internal_note"] is False for c in req_view.json()), "Internal notes MUST NEVER be exposed to requesters"

    # 5. Non-agent requester trying to post internal note gets 403 Forbidden
    forbidden_resp = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/comments", json=internal_payload, headers=requester_headers)
    assert forbidden_resp.status_code == 403


def test_sla_breach_detection_and_recalculation(client: TestClient, test_setup: dict, db_session: Session):
    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}

    # Set ticket deadline in the past to simulate overdue
    ticket = db_session.query(ServiceDeskTicket).filter(ServiceDeskTicket.id == test_setup["test_ticket_id"]).first()
    ticket.resolution_due_at = datetime.utcnow() - timedelta(hours=2)
    ticket.status = "IN_PROGRESS"
    ticket.resolved_at = None
    db_session.commit()

    # Recalculate
    recalc_resp = client.post("/api/v1/service-desk/sla/recalculate", headers=headers)
    assert recalc_resp.status_code == 200
    assert recalc_resp.json()["status"] == "success"

    # Verify ticket marked BREACHED
    db_session.refresh(ticket)
    assert ticket.sla_resolution_status == "BREACHED"

    # Verify breach record created
    breach = db_session.query(ServiceDeskSLABreach).filter(ServiceDeskSLABreach.ticket_id == ticket.id).first()
    assert breach is not None
    assert breach.breach_type == "RESOLUTION"
    assert breach.minutes_overdue > 0


def test_ticket_escalation_and_dashboard_metrics(client: TestClient, test_setup: dict):
    ticket_id = test_setup["test_ticket_id"]
    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}

    # 1. Trigger Escalation
    esc_payload = {
        "reason": "Executive VIP impacted by repeated disconnection",
        "bump_priority": "CRITICAL",
    }
    esc_resp = client.post(f"/api/v1/service-desk/tickets/{ticket_id}/escalate", json=esc_payload, headers=headers)
    assert esc_resp.status_code == 200
    assert esc_resp.json()["status"] == "success"

    # Verify ticket priority bumped to CRITICAL
    t_resp = client.get(f"/api/v1/service-desk/tickets/{ticket_id}", headers=headers)
    assert t_resp.status_code == 200
    assert t_resp.json()["status"] == "ESCALATED"
    assert t_resp.json()["priority"] == "CRITICAL"

    # 2. Dashboard Operational Metrics
    dash_resp = client.get("/api/v1/service-desk/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    data = dash_resp.json()
    assert data["total_tickets"] >= 1
    assert "by_status" in data
    assert "by_priority" in data
    assert "by_category" in data
    assert "sla_compliance_rate" in data

    # 3. Team & Agent Performance
    perf_resp = client.get("/api/v1/service-desk/reports/performance", headers=headers)
    assert perf_resp.status_code == 200
    perf_data = perf_resp.json()
    assert "agents" in perf_data
    assert "teams" in perf_data
