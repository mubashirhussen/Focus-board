import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.session import SessionLocal
from app.models.growth import CustomerFeedback
from app.models.cx_intelligence import (
    CXFeedbackCategory,
    CXSurvey,
    CXSurveyQuestion,
    CXSurveyResponse,
    CXInsight,
    CXRecommendation,
    CXJourneyEvent,
)
from app.models.task import Task
from app.services.cx_intelligence_service import (
    analyze_sentiment,
    calculate_priority_score,
    execute_cx_automation_action,
)

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b17_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "CXPassSecure123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"CX User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

def create_test_workspace(client, headers, name="CX Workspace"):
    res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Workspace for B17 testing"},
        headers=headers,
    )
    assert res.status_code in [200, 201], res.text
    return res.json()["id"]

# ==============================================================================
# 1. FEEDBACK CRUD & LIFECYCLE
# ==============================================================================
def test_feedback_crud_and_lifecycle(client):
    headers, user_id, _ = get_auth_headers(client, "crud_user")
    ws_id = create_test_workspace(client, headers)

    # 1. Create feedback
    payload = {
        "title": "Search is confusing",
        "description": "I found the search filter options confusing and hard to locate.",
        "category": "ux_improvement",
        "feedback_type": "UX_IMPROVEMENT",
        "rating": 2,
        "workspace_id": ws_id,
        "tags": ["search", "navigation"],
    }
    create_res = client.post(f"{settings.API_V1_STR}/cx/feedback", json=payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    fb_data = create_res.json()
    fb_id = fb_data["id"]
    assert fb_data["status"] == "NEW"
    assert fb_data["rating"] == 2
    assert "search" in fb_data["tags"]
    assert fb_data["sentiment"] in ["NEGATIVE", "MIXED", "NEUTRAL"]

    # 2. Retrieve feedback
    get_res = client.get(f"{settings.API_V1_STR}/cx/feedback/{fb_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Search is confusing"

    # 3. Update status to IN_PROGRESS
    update_res = client.patch(
        f"{settings.API_V1_STR}/cx/feedback/{fb_id}",
        json={"status": "IN_PROGRESS", "admin_notes": "Assigned to UI squad"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "IN_PROGRESS"

    # 4. Resolve feedback
    resolve_res = client.patch(
        f"{settings.API_V1_STR}/cx/feedback/{fb_id}",
        json={"status": "RESOLVED", "resolution_notes": "Redesigned search popup bar"},
        headers=headers,
    )
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["status"] == "RESOLVED"
    assert res_data["resolved_at"] is not None

    # 5. List with filter
    list_res = client.get(f"{settings.API_V1_STR}/cx/feedback?status=RESOLVED&workspace_id={ws_id}", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["id"] == fb_id for item in items)

# ==============================================================================
# 2. CATEGORIZATION & ASSIGNMENT
# ==============================================================================
def test_feedback_categorization_and_assignment(client):
    headers, user_id, _ = get_auth_headers(client, "cat_user")
    _, assignee_id, _ = get_auth_headers(client, "assignee_user")
    ws_id = create_test_workspace(client, headers)

    # 1. Create custom category
    cat_res = client.post(
        f"{settings.API_V1_STR}/cx/categories",
        json={"name": "Billing & Invoicing", "description": "Customer issues related to payment flows"},
        headers=headers,
    )
    assert cat_res.status_code == 201
    cat_slug = cat_res.json()["slug"]
    assert "billing" in cat_slug

    # 2. Submit feedback with category & assignment
    fb_res = client.post(
        f"{settings.API_V1_STR}/cx/feedback",
        json={
            "title": "Invoice receipt error",
            "description": "Invoice receipt PDF did not download properly after subscription renewal.",
            "category": cat_slug,
            "feedback_type": "BUG_REPORT",
            "rating": 2,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert fb_res.status_code == 201
    fb_id = fb_res.json()["id"]

    # 3. Assign feedback to team member
    assign_res = client.patch(
        f"{settings.API_V1_STR}/cx/feedback/{fb_id}",
        json={"assigned_user_id": assignee_id, "priority": "HIGH"},
        headers=headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_user_id"] == assignee_id
    assert assign_res.json()["priority"] == "HIGH"

# ==============================================================================
# 3. SENTIMENT ANALYSIS ENGINE
# ==============================================================================
def test_sentiment_analysis_engine():
    # Positive sentiment
    p_label, p_score, p_conf, lang = analyze_sentiment("FocusBoard is awesome, incredibly fast, and smooth!")
    assert p_label == "POSITIVE"
    assert p_score > 0.3
    assert p_conf >= 0.5
    assert lang == "en"

    # Negative sentiment
    n_label, n_score, n_conf, _ = analyze_sentiment("The application is terribly slow, full of bugs, and constantly crashes.")
    assert n_label == "NEGATIVE"
    assert n_score < -0.3
    assert n_conf >= 0.5

    # Negation handling: "not good"
    neg_label, neg_score, _, _ = analyze_sentiment("The new update is not good, it feels sluggish.")
    assert neg_label == "NEGATIVE"
    assert neg_score < 0.0

    # Neutral sentiment
    neu_label, neu_score, _, _ = analyze_sentiment("The release notes were posted for version 3.2.1.")
    assert neu_label == "NEUTRAL"
    assert neu_score == 0.0

# ==============================================================================
# 4. MATHEMATICAL CSAT, NPS & CES METRICS
# ==============================================================================
def test_csat_nps_ces_metrics(client):
    headers, user_id, _ = get_auth_headers(client, "metric_user")
    ws_id = create_test_workspace(client, headers, "Metrics WS")

    # Ingest 4 controlled feedbacks:
    # 1: rating 5 (Promoter, Satisfied)
    # 2: rating 4 (Passive, Satisfied)
    # 3: rating 2 (Detractor, Unsatisfied)
    # 4: rating 1 (Detractor, Unsatisfied)
    client.post(f"{settings.API_V1_STR}/cx/feedback", json={"title": "F1", "description": "Love it awesome", "rating": 5, "workspace_id": ws_id}, headers=headers)
    client.post(f"{settings.API_V1_STR}/cx/feedback", json={"title": "F2", "description": "Good product", "rating": 4, "workspace_id": ws_id}, headers=headers)
    client.post(f"{settings.API_V1_STR}/cx/feedback", json={"title": "F3", "description": "Needs work clunky", "rating": 2, "workspace_id": ws_id}, headers=headers)
    client.post(f"{settings.API_V1_STR}/cx/feedback", json={"title": "F4", "description": "Terrible buggy slow", "rating": 1, "workspace_id": ws_id}, headers=headers)

    res = client.get(f"{settings.API_V1_STR}/cx/metrics?workspace_id={ws_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # CSAT: 2 out of 4 rated >= 4 => 50.0%
    assert data["csat"] == 50.0
    # Average rating: (5+4+2+1) / 4 = 12 / 4 = 3.0
    assert data["average_rating"] == 3.0
    # NPS: 1 promoter (25%), 2 detractors (50%) => 25.0 - 50.0 = -25.0%
    assert data["nps"] == -25.0
    assert data["total_feedback_count"] == 4
    assert data["rating_distribution"]["5"] == 1
    assert data["rating_distribution"]["4"] == 1
    assert data["rating_distribution"]["2"] == 1
    assert data["rating_distribution"]["1"] == 1

# ==============================================================================
# 5. DASHBOARD & TRENDS
# ==============================================================================
def test_cx_dashboard_and_trends(client):
    headers, user_id, _ = get_auth_headers(client, "dash_user")
    ws_id = create_test_workspace(client, headers, "Dash WS")

    # Seed feedback
    client.post(
        f"{settings.API_V1_STR}/cx/feedback",
        json={"title": "Great dashboard UI", "description": "Clean and very intuitive interface", "rating": 5, "category": "ux_improvement", "workspace_id": ws_id},
        headers=headers,
    )

    res = client.get(f"{settings.API_V1_STR}/cx/dashboard?workspace_id={ws_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "metrics" in data
    assert "recent_feedback" in data
    assert "top_categories" in data
    assert "trends" in data
    assert len(data["recent_feedback"]) >= 1
    assert any(c["category"] == "ux_improvement" for c in data["top_categories"])

# ==============================================================================
# 6. FEEDBACK PRIORITIZATION & SCORING
# ==============================================================================
def test_feedback_prioritization_and_scoring():
    # Low rating (1) + negative sentiment + BUG_REPORT => URGENT
    urg_level, urg_score = calculate_priority_score(
        rating=1,
        sentiment="NEGATIVE",
        sentiment_score=-0.8,
        feedback_type="BUG_REPORT",
    )
    assert urg_level == "URGENT"
    assert urg_score >= 80.0

    # High rating (5) + positive sentiment + GENERAL => LOW
    low_level, low_score = calculate_priority_score(
        rating=5,
        sentiment="POSITIVE",
        sentiment_score=0.9,
        feedback_type="GENERAL",
    )
    assert low_level == "LOW"
    assert low_score < 35.0

# ==============================================================================
# 7. TOPIC CLUSTERING & RECURRING ISSUE DETECTION
# ==============================================================================
def test_topic_clustering_and_recurring_issues(client):
    headers, user_id, _ = get_auth_headers(client, "cluster_user")
    ws_id = create_test_workspace(client, headers, "Cluster WS")

    # Insert 2 negative feedbacks in the same category
    f1 = client.post(
        f"{settings.API_V1_STR}/cx/feedback",
        json={"title": "Export fails on CSV", "description": "CSV export is completely broken and crashes", "category": "export_bug", "rating": 1, "workspace_id": ws_id},
        headers=headers,
    ).json()
    f2 = client.post(
        f"{settings.API_V1_STR}/cx/feedback",
        json={"title": "Export timeout error", "description": "Large project CSV export gives a terrible timeout error", "category": "export_bug", "rating": 1, "workspace_id": ws_id},
        headers=headers,
    ).json()

    # Trigger insight detection
    detect_res = client.post(f"{settings.API_V1_STR}/cx/insights/detect?workspace_id={ws_id}", headers=headers)
    assert detect_res.status_code == 200
    insights = detect_res.json()
    assert len(insights) >= 1

    cluster_insight = next((i for i in insights if "export" in i["title"].lower() or "export_bug" in str(i.get("supporting_metrics"))), None)
    assert cluster_insight is not None
    assert f1["id"] in cluster_insight["supporting_feedback_ids"]
    assert f2["id"] in cluster_insight["supporting_feedback_ids"]

# ==============================================================================
# 8. CX RECOMMENDATIONS & TASK CONVERSION
# ==============================================================================
def test_cx_insights_and_recommendation_to_task_conversion(client):
    headers, user_id, _ = get_auth_headers(client, "convert_user")
    ws_id = create_test_workspace(client, headers, "Convert WS")

    # 1. Create 2 negative feedbacks and detect insight to generate recommendation
    client.post(
        f"{settings.API_V1_STR}/cx/feedback",
        json={"title": "Auth timeout", "description": "Login session expires prematurely and fails", "category": "auth_issues", "rating": 1, "workspace_id": ws_id},
        headers=headers,
    )
    client.post(
        f"{settings.API_V1_STR}/cx/feedback",
        json={"title": "MFA code error", "description": "MFA verification fails repeatedly", "category": "auth_issues", "rating": 1, "workspace_id": ws_id},
        headers=headers,
    )
    client.post(f"{settings.API_V1_STR}/cx/insights/detect?workspace_id={ws_id}", headers=headers)

    # 2. List recommendations
    rec_res = client.get(f"{settings.API_V1_STR}/cx/recommendations?workspace_id={ws_id}", headers=headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    assert len(recs) >= 1
    rec = recs[0]

    # 3. Convert recommendation to FocusBoard Task
    convert_res = client.post(
        f"{settings.API_V1_STR}/cx/recommendations/{rec['id']}/convert",
        json={"workspace_id": ws_id, "priority": "URGENT"},
        headers=headers,
    )
    assert convert_res.status_code == 200
    converted_data = convert_res.json()
    assert converted_data["status"] == "CONVERTED"
    assert converted_data["task_id"] is not None

    # 4. Verify Task exists in database
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == converted_data["task_id"]).first()
        assert task is not None
        assert task.priority == "URGENT"
        assert task.workspace_id == ws_id
    finally:
        db.close()

# ==============================================================================
# 9. SURVEY MANAGEMENT & RESPONSE COLLECTION
# ==============================================================================
def test_cx_survey_management_and_responses(client):
    headers, user_id, _ = get_auth_headers(client, "survey_user")
    ws_id = create_test_workspace(client, headers, "Survey WS")

    # 1. Create CSAT / NPS Survey
    survey_payload = {
        "title": "Q4 User Experience Survey",
        "description": "Quarterly satisfaction and ease of use survey",
        "survey_type": "NPS",
        "status": "ACTIVE",
        "workspace_id": ws_id,
        "questions": [
            {
                "question_text": "How likely are you to recommend FocusBoard to a colleague?",
                "question_type": "NPS_10",
                "is_required": True,
                "order_index": 0,
            },
            {
                "question_text": "What do you like most about the platform?",
                "question_type": "TEXT",
                "is_required": False,
                "order_index": 1,
            },
        ],
    }
    create_survey_res = client.post(f"{settings.API_V1_STR}/cx/surveys", json=survey_payload, headers=headers)
    assert create_survey_res.status_code == 201
    survey_data = create_survey_res.json()
    survey_id = survey_data["id"]
    assert len(survey_data["questions"]) == 2

    # 2. Submit survey response
    resp_payload = {
        "score": 10.0,
        "feedback_text": "FocusBoard has revolutionized our team workflow, absolute delight to use!",
        "answers": {"recommendation_score": 10, "comment": "Love the AI features"},
    }
    submit_res = client.post(f"{settings.API_V1_STR}/cx/surveys/{survey_id}/responses", json=resp_payload, headers=headers)
    assert submit_res.status_code == 201
    resp_data = submit_res.json()
    assert resp_data["sentiment"] == "POSITIVE"
    assert resp_data["score"] == 10.0

# ==============================================================================
# 10. CUSTOMER JOURNEY EVENT TRACKING
# ==============================================================================
def test_customer_journey_event_tracking(client):
    headers, user_id, _ = get_auth_headers(client, "journey_user")
    ws_id = create_test_workspace(client, headers, "Journey WS")

    # Track milestone events
    stages = ["ONBOARDING", "ADOPTION", "RETENTION"]
    for stage in stages:
        res = client.post(
            f"{settings.API_V1_STR}/cx/journey/events",
            json={
                "stage": stage,
                "event_name": f"{stage.lower()}_completed",
                "sentiment": "POSITIVE",
                "metadata": {"step_count": 3},
                "workspace_id": ws_id,
            },
            headers=headers,
        )
        assert res.status_code == 201

    # List by stage
    list_res = client.get(f"{settings.API_V1_STR}/cx/journey/events?stage=ADOPTION&workspace_id={ws_id}", headers=headers)
    assert list_res.status_code == 200
    events = list_res.json()
    assert len(events) >= 1
    assert events[0]["stage"] == "ADOPTION"

# ==============================================================================
# 11. MULTI-TENANT ISOLATION, AUTOMATION & GROWTH API INTEGRATION
# ==============================================================================
def test_cx_multi_tenant_isolation_and_b15_automation(client):
    # Tenant isolation test
    headers_a, user_a, _ = get_auth_headers(client, "tenant_a")
    headers_b, user_b, _ = get_auth_headers(client, "tenant_b")

    ws_a = create_test_workspace(client, headers_a, "Tenant A WS")
    ws_b = create_test_workspace(client, headers_b, "Tenant B WS")

    # User A creates feedback in Workspace A
    fb_a = client.post(
        f"{settings.API_V1_STR}/cx/feedback",
        json={"title": "Private Feedback A", "description": "Confidential internal note", "workspace_id": ws_a},
        headers=headers_a,
    ).json()

    # User B list in Workspace B should NOT see User A's feedback
    res_b = client.get(f"{settings.API_V1_STR}/cx/feedback?workspace_id={ws_b}", headers=headers_b)
    assert res_b.status_code == 200
    assert all(item["id"] != fb_a["id"] for item in res_b.json())

    # Direct access across tenant boundary
    direct_res = client.get(f"{settings.API_V1_STR}/cx/feedback/{fb_a['id']}", headers=headers_b)
    assert direct_res.status_code in [403, 404]

    # Test B15 Automation Action Handler
    db = SessionLocal()
    try:
        action_res = execute_cx_automation_action(
            db,
            action_type="cx.update_feedback_status",
            config={"status": "REVIEWING"},
            payload={"feedback_id": fb_a["id"]},
        )
        assert action_res["status"] == "success"
        assert action_res["status"] == "success"

        # Verify status in database
        updated_fb = db.query(CustomerFeedback).filter(CustomerFeedback.id == fb_a["id"]).first()
        assert updated_fb.status == "REVIEWING"
    finally:
        db.close()

    # Backwards compatibility: verify /growth/feedback endpoint works with sentiment & priority
    growth_res = client.post(
        f"{settings.API_V1_STR}/growth/feedback",
        json={"category": "feature_request", "rating": 5, "description": "Love the AI features, keep it up!"},
        headers=headers_a,
    )
    assert growth_res.status_code in [200, 201]
    g_data = growth_res.json()
    assert g_data["rating"] == 5
