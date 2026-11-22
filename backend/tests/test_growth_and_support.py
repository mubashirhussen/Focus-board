import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def get_auth_token(client, email="user@growth.com", role="Member", name="Growth User"):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "securepassword123", "role": role},
        headers={"X-Test-Bypass-Rate-Limit": "true"}
    )
    return res.json()["access_token"]

# ==========================================
# PHASE 28: PRODUCT-LED GROWTH & ONBOARDING
# ==========================================

def test_onboarding_lifecycle(client):
    token = get_auth_token(client, "onboarding@user.com", "Member", "New Onboarding User")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Fetch initial onboarding progress
    res = client.get("/api/v1/growth/onboarding", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["current_step"] == 1
    assert data["is_completed"] is False
    assert data["completed_steps"] == []

    # 2. Update step 1 (set primary goal)
    res = client.post(
        "/api/v1/growth/onboarding",
        json={"step_id": "workspace", "primary_goal": "team_productivity"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "workspace" in data["completed_steps"]
    assert data["primary_goal"] == "team_productivity"

    # 3. Complete remaining steps (project, first_task, analytics)
    for s in ["project", "first_task", "analytics"]:
        res = client.post(
            "/api/v1/growth/onboarding",
            json={"step_id": s},
            headers=headers,
        )
        assert res.status_code == 200

    final_res = client.get("/api/v1/growth/onboarding", headers=headers)
    final_data = final_res.json()
    assert final_data["is_completed"] is True
    assert set(final_data["completed_steps"]) == {"workspace", "project", "first_task", "analytics"}

def test_product_event_tracking(client):
    token = get_auth_token(client, "tracker@user.com", "Member")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Track a valid registered event
    res = client.post(
        "/api/v1/growth/events",
        json={
            "event_name": "onboarding_step_completed",
            "properties": {"step": 1, "goal": "personal_organization"}
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["event_name"] == "onboarding_step_completed"

    # Track an invalid/unregistered event (should be rejected for data governance)
    bad_res = client.post(
        "/api/v1/growth/events",
        json={
            "event_name": "random_unauthorized_custom_event",
            "properties": {}
        },
        headers=headers,
    )
    assert bad_res.status_code == 400
    assert "Invalid" in bad_res.json()["detail"] or "not in the allowed" in bad_res.json()["detail"]

def test_activation_funnel_and_conversion(client):
    token = get_auth_token(client, "admin@growth.com", "Owner")
    headers = {"Authorization": f"Bearer {token}", "X-Test-Bypass-Rate-Limit": "true"}

    res = client.get("/api/v1/growth/activation", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "created_workspace" in data
    assert "created_first_task" in data
    assert "completed_first_task" in data
    assert "activation_rate" in data

def test_feedback_submission_and_management(client):
    member_token = get_auth_token(client, "member@feedback.com", "Member")
    admin_token = get_auth_token(client, "admin@feedback.com", "Owner")

    member_headers = {"Authorization": f"Bearer {member_token}", "X-Test-Bypass-Rate-Limit": "true"}
    admin_headers = {"Authorization": f"Bearer {admin_token}", "X-Test-Bypass-Rate-Limit": "true"}

    # Submit feedback
    sub_res = client.post(
        "/api/v1/growth/feedback",
        json={
            "category": "feature_request",
            "rating": 5,
            "description": "Great workspace views, please add Gantt chart view!",
        },
        headers=member_headers,
    )
    assert sub_res.status_code == 201
    feedback_id = sub_res.json()["id"]

    # Member can view their own feedback
    list_res = client.get("/api/v1/growth/feedback", headers=member_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Admin updates feedback status to planned
    update_res = client.patch(
        f"/api/v1/growth/feedback/{feedback_id}",
        json={"status": "planned", "admin_notes": "Gantt view is scheduled for Q3 roadmap."},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "planned"

# ==========================================
# PHASE 29: CUSTOMER SUPPORT & OPERATIONS
# ==========================================

def test_support_ticket_lifecycle_and_sla(client):
    cust_token = get_auth_token(client, "customer@support.com", "Member", "Customer User")
    agent_token = get_auth_token(client, "support.agent@company.com", "Admin", "Agent Jane")

    cust_headers = {"Authorization": f"Bearer {cust_token}", "X-Test-Bypass-Rate-Limit": "true"}
    agent_headers = {"Authorization": f"Bearer {agent_token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Create an URGENT support ticket (creates initial description message)
    t_res = client.post(
        "/api/v1/support/tickets",
        json={
            "title": "Cannot export project data",
            "description": "Export button returns 500 error on Large project.",
            "category": "technical_issue",
            "priority": "URGENT",
        },
        headers=cust_headers,
    )
    assert t_res.status_code == 201
    ticket = t_res.json()
    ticket_id = ticket["id"]
    assert ticket["priority"] == "URGENT"
    assert ticket["status"] == "OPEN"
    assert ticket["sla_deadline"] is not None

    # 2. Agent posts an internal note (customer must not see it)
    note_res = client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        json={"message": "Checking worker logs for export timeout", "is_internal_note": True},
        headers=agent_headers,
    )
    assert note_res.status_code == 201
    assert note_res.json()["is_internal_note"] is True

    # 3. Customer checks messages -> only initial customer message is visible (internal note filtered out)
    cust_msg_res = client.get(f"/api/v1/support/tickets/{ticket_id}/messages", headers=cust_headers)
    assert cust_msg_res.status_code == 200
    cust_messages = cust_msg_res.json()
    assert len(cust_messages) == 1
    assert cust_messages[0]["is_internal_note"] is False

    # 4. Agent checks messages -> both initial message and internal note ARE visible
    agent_msg_res = client.get(f"/api/v1/support/tickets/{ticket_id}/messages", headers=agent_headers)
    assert agent_msg_res.status_code == 200
    agent_messages = agent_msg_res.json()
    assert len(agent_messages) == 2
    assert any(m["is_internal_note"] is True for m in agent_messages)

    # 5. Customer cannot post internal notes
    forbidden_note = client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        json={"message": "I am trying to post internal note", "is_internal_note": True},
        headers=cust_headers,
    )
    assert forbidden_note.status_code == 403

    # 6. Agent sends customer-facing reply
    reply_res = client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        json={"message": "We have resolved the memory limit issue on export.", "is_internal_note": False},
        headers=agent_headers,
    )
    assert reply_res.status_code == 201

    # 7. Customer sees agent's reply (now 2 public messages: initial + reply)
    cust_msg_res_2 = client.get(f"/api/v1/support/tickets/{ticket_id}/messages", headers=cust_headers)
    assert len(cust_msg_res_2.json()) == 2
    assert all(not m["is_internal_note"] for m in cust_msg_res_2.json())

    # 8. Agent resolves ticket
    res_ticket = client.patch(
        f"/api/v1/support/tickets/{ticket_id}",
        json={"status": "RESOLVED"},
        headers=agent_headers,
    )
    assert res_ticket.status_code == 200
    assert res_ticket.json()["status"] == "RESOLVED"

def test_knowledge_base_and_roadmap(client):
    user_token = get_auth_token(client, "reader@kb.com", "Member")
    headers = {"Authorization": f"Bearer {user_token}", "X-Test-Bypass-Rate-Limit": "true"}

    # 1. Fetch categories
    cat_res = client.get("/api/v1/support/knowledge-base/categories", headers=headers)
    assert cat_res.status_code == 200
    categories = cat_res.json()
    assert len(categories) >= 3  # Getting Started, Integrations, Security

    # 2. Fetch articles
    articles_res = client.get("/api/v1/support/knowledge-base/articles", headers=headers)
    assert articles_res.status_code == 200
    articles = articles_res.json()
    assert len(articles) >= 3
    first_art = articles[0]

    # 3. Vote helpful on article
    vote_res = client.post(
        f"/api/v1/support/knowledge-base/articles/{first_art['id']}/vote",
        json={"helpful": True},
        headers=headers,
    )
    assert vote_res.status_code == 200
    assert vote_res.json()["helpful_count"] == first_art["helpful_count"] + 1

    # 4. Roadmap listing & voting
    road_res = client.get("/api/v1/support/roadmap", headers=headers)
    assert road_res.status_code == 200
    items = road_res.json()
    assert len(items) >= 3
    first_road = items[0]

    vote_road = client.post(f"/api/v1/support/roadmap/{first_road['id']}/vote", headers=headers)
    assert vote_road.status_code == 200
    assert vote_road.json()["vote_count"] == first_road["vote_count"] + 1

def test_customer_health_score(client):
    user_token = get_auth_token(client, "health@user.com", "Member")
    headers = {"Authorization": f"Bearer {user_token}", "X-Test-Bypass-Rate-Limit": "true"}

    res = client.get("/api/v1/support/customer-health", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "health_score" in data
    assert "health_status" in data
    assert data["health_status"] in ["HEALTHY", "NEEDS_ATTENTION", "AT_RISK"]
    assert "metrics" in data
    assert "completion_rate" in data["metrics"]
