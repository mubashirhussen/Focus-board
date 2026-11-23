import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.session import SessionLocal
from app.models.task import Task
from app.models.product_lifecycle import (
    ProductDiscovery,
    ProductIdea,
    ProductFeatureRequest,
    LifecycleRoadmapItem,
    RoadmapDependency,
    ProductExperiment,
    ExperimentVariant,
    ExperimentEvent,
    ProductRelease,
)
from app.services.product_lifecycle_service import (
    ProductLifecycleService,
    execute_product_lifecycle_automation_action,
)

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b18_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "LifecyclePass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"Lifecycle User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

def create_test_workspace(client, headers, name="Product Workspace"):
    res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Workspace for B18 testing"},
        headers=headers,
    )
    assert res.status_code in [200, 201], res.text
    return res.json()["id"]

# ==============================================================================
# 1. PRODUCT DISCOVERY CRUD & LIFECYCLE TRANSITIONS
# ==============================================================================
def test_product_discovery_crud_and_lifecycle(client):
    headers, user_id, _ = get_auth_headers(client, "disc_user")
    ws_id = create_test_workspace(client, headers, "Discovery WS")

    # 1. Create discovery
    payload = {
        "title": "Enterprise SSO Friction",
        "problem_statement": "Enterprise customers struggle to configure SAML/OIDC quickly.",
        "hypothesis": "Providing pre-built IdP templates will reduce onboarding time by 60%.",
        "target_users": "Enterprise IT Admins",
        "customer_segment": "ENTERPRISE",
        "business_impact": "Prevents churn in 6-figure enterprise deals.",
        "customer_impact": "Cuts setup time from 4 days to 30 minutes.",
        "status": "DISCOVERED",
        "workspace_id": ws_id,
    }
    create_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries",
        json=payload,
        headers=headers,
    )
    assert create_res.status_code == 201, create_res.text
    disc = create_res.json()
    disc_id = disc["id"]
    assert disc["title"] == payload["title"]
    assert disc["status"] == "DISCOVERED"

    # 2. Get discovery
    get_res = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries/{disc_id}",
        headers=headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["hypothesis"] == payload["hypothesis"]

    # 3. Valid stage transition: DISCOVERED -> INVESTIGATING
    update_res = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries/{disc_id}",
        json={"status": "INVESTIGATING"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "INVESTIGATING"

    # 4. Valid stage transition: INVESTIGATING -> VALIDATING -> VALIDATED
    client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries/{disc_id}",
        json={"status": "VALIDATING"},
        headers=headers,
    )
    val_res = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries/{disc_id}",
        json={"status": "VALIDATED"},
        headers=headers,
    )
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "VALIDATED"

    # 5. Invalid stage transition: VALIDATED -> INVALID_STATUS (or invalid direct jump)
    invalid_res = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries/{disc_id}",
        json={"status": "DISCOVERED"},
        headers=headers,
    )
    assert invalid_res.status_code == 400
    assert "Invalid discovery stage transition" in invalid_res.json()["detail"]

    # 6. List discoveries
    list_res = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert any(d["id"] == disc_id for d in list_res.json())

    # 7. Delete discovery
    del_res = client.delete(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries/{disc_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

# ==============================================================================
# 2. PRODUCT IDEA CRUD & CONVERSION ENGINE
# ==============================================================================
def test_idea_crud_and_conversion(client):
    headers, user_id, _ = get_auth_headers(client, "idea_user")
    ws_id = create_test_workspace(client, headers, "Idea WS")

    # 1. Create Idea
    idea_payload = {
        "title": "One-Click Okta Integration",
        "description": "Pre-configured tile in Okta Integration Network",
        "problem_statement": "Manual SAML metadata entry causes configuration errors.",
        "proposed_solution": "Publish verified app to Okta and Azure AD galleries.",
        "product_area": "SECURITY",
        "category": "INTEGRATION",
        "priority": "HIGH",
        "status": "NEW",
        "workspace_id": ws_id,
        "tags_json": '["sso", "security", "enterprise"]',
    }
    create_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/ideas",
        json=idea_payload,
        headers=headers,
    )
    assert create_res.status_code == 201, create_res.text
    idea = create_res.json()
    idea_id = idea["id"]
    assert idea["title"] == idea_payload["title"]

    # 2. Update status NEW -> UNDER_REVIEW -> VALIDATED
    client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/ideas/{idea_id}",
        json={"status": "UNDER_REVIEW"},
        headers=headers,
    )
    val_res = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/ideas/{idea_id}",
        json={"status": "VALIDATED"},
        headers=headers,
    )
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "VALIDATED"

    # 3. Convert idea to Task
    convert_task_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/ideas/{idea_id}/convert",
        json={"target_type": "TASK", "workspace_id": ws_id},
        headers=headers,
    )
    assert convert_task_res.status_code == 200, convert_task_res.text
    conv_data = convert_task_res.json()
    assert conv_data["target_type"] == "TASK"
    assert conv_data["target_id"] is not None
    task_id = conv_data["target_id"]

    # Verify task in database
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == str(task_id)).first()
        assert task is not None
        assert "One-Click Okta Integration" in task.title

        # Check idea updated with linked_task_id
        db_idea = db.query(ProductIdea).filter(ProductIdea.id == idea_id).first()
        assert db_idea.linked_task_id == str(task_id)
        assert db_idea.status == "IN_PROGRESS"
    finally:
        db.close()

    # 4. Create second idea to convert to Feature Request
    idea2_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/ideas",
        json={
            "title": "Automated SCIM User Deprovisioning",
            "description": "Deprovision users automatically when removed from IdP",
            "problem_statement": "Manual seat revocation leads to lingering access.",
            "proposed_solution": "Implement SCIM 2.0 endpoints.",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert idea2_res.status_code == 201
    idea2_id = idea2_res.json()["id"]

    convert_freq_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/ideas/{idea2_id}/convert",
        json={"target_type": "FEATURE_REQUEST", "workspace_id": ws_id},
        headers=headers,
    )
    assert convert_freq_res.status_code == 200
    freq_data = convert_freq_res.json()
    assert freq_data["target_type"] == "FEATURE_REQUEST"

    # 5. Convert to Roadmap item
    idea3_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/ideas",
        json={
            "title": "Role-Based Custom Permissions",
            "description": "Granular action-level permissions",
            "problem_statement": "Customers need fine-grained role control.",
            "proposed_solution": "RBAC policy engine.",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    idea3_id = idea3_res.json()["id"]

    convert_road_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/ideas/{idea3_id}/convert",
        json={"target_type": "ROADMAP_ITEM", "workspace_id": ws_id},
        headers=headers,
    )
    assert convert_road_res.status_code == 200
    assert convert_road_res.json()["target_type"] == "ROADMAP_ITEM"

# ==============================================================================
# 3. FEATURE REQUESTS & HARDENED MERGE
# ==============================================================================
def test_feature_requests_and_merge(client):
    headers, user_id, _ = get_auth_headers(client, "freq_user")
    ws_id = create_test_workspace(client, headers, "Feature WS")

    # 1. Create Feature Request A (Primary target)
    req_a_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/feature-requests",
        json={
            "title": "Dark Mode Support",
            "description": "System-wide dark mode theme",
            "customer_name": "Acme Corp",
            "request_count": 5,
            "revenue_impact": 15000.0,
            "priority": "HIGH",
            "status": "OPEN",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert req_a_res.status_code == 201
    freq_a = req_a_res.json()

    # 2. Create Feature Request B (Duplicate source)
    req_b_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/feature-requests",
        json={
            "title": "Night / Dark Theme UI",
            "description": "Please add a dark theme option for late work sessions",
            "customer_name": "Globex Inc",
            "request_count": 3,
            "revenue_impact": 10000.0,
            "priority": "MEDIUM",
            "status": "OPEN",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert req_b_res.status_code == 201
    freq_b = req_b_res.json()

    # 3. Prevent self-merge
    self_merge_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/feature-requests/{freq_a['id']}/merge?target_id={freq_a['id']}",
        headers=headers,
    )
    assert self_merge_res.status_code == 400
    assert "Cannot merge a feature request into itself" in self_merge_res.json()["detail"]

    # 4. Perform valid merge B into A
    merge_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/feature-requests/{freq_b['id']}/merge?target_id={freq_a['id']}",
        headers=headers,
    )
    assert merge_res.status_code == 200
    merged_a = merge_res.json()
    assert merged_a["request_count"] == 8  # 5 + 3
    assert merged_a["revenue_impact"] == 25000.0  # 15000 + 10000

    # 5. Verify source B status is DECLINED and merged_into_id is set
    get_b_res = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/feature-requests/{freq_b['id']}",
        headers=headers,
    )
    assert get_b_res.status_code == 200
    b_data = get_b_res.json()
    assert b_data["status"] == "DECLINED"
    assert b_data["merged_into_id"] == freq_a["id"]

    # 6. Attempt to merge B again (should fail)
    remerge_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/feature-requests/{freq_b['id']}/merge?target_id={freq_a['id']}",
        headers=headers,
    )
    assert remerge_res.status_code == 400
    assert "already been merged" in remerge_res.json()["detail"]

# ==============================================================================
# 4. PRIORITIZATION ENGINE & QUADRANTS
# ==============================================================================
def test_prioritization_engine_and_quadrants(client):
    headers, user_id, _ = get_auth_headers(client, "prio_user")
    ws_id = create_test_workspace(client, headers, "Prio WS")

    # 1. Test calculation endpoint
    # reach=1000, impact=3.0, confidence=0.8, effort=2.0, ease=4.0
    # Expected RICE = (1000 * 3.0 * 0.8) / 2.0 = 2400 / 2 = 1200.0
    # Expected ICE = 3.0 * 0.8 * 4.0 = 9.6
    # Weighted = (0.6 * 1200) + (0.4 * 9.6) = 720 + 3.84 = 723.84
    calc_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/prioritization/calculate?reach=1000&impact=3.0&confidence=0.8&effort=2.0&ease=4.0",
        headers=headers,
    )
    assert calc_res.status_code == 200, calc_res.text
    scores = calc_res.json()
    assert scores["rice_score"] == 1200.0
    assert scores["ice_score"] == 9.6
    assert abs(scores["weighted_score"] - 723.84) < 0.01

    # 2. Test effort <= 0 rejection
    invalid_effort_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/prioritization/calculate?reach=1000&impact=3.0&confidence=0.8&effort=0&ease=4.0",
        headers=headers,
    )
    assert invalid_effort_res.status_code in [400, 422]

    # 3. Save a prioritization item
    pitem_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/prioritization/items",
        json={
            "item_type": "FEATURE",
            "item_id": "feat_1234",
            "title": "Automated SSO Provisioning",
            "reach": 500.0,
            "impact": 4.0,
            "confidence": 0.9,
            "effort": 3.0,
            "ease": 3.5,
            "moscow_category": "MUST_HAVE",
            "priority_rank": 1,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert pitem_res.status_code == 201, pitem_res.text
    pitem = pitem_res.json()
    # RICE = (500 * 4.0 * 0.9) / 3.0 = 1800 / 3 = 600.0
    assert pitem["rice_score"] == 600.0
    assert pitem["moscow_category"] == "MUST_HAVE"

    # 4. List prioritization items
    list_pitem_res = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/prioritization/items",
        headers=headers,
    )
    assert list_pitem_res.status_code == 200
    assert any(i["id"] == pitem["id"] for i in list_pitem_res.json())

# ==============================================================================
# 5. ROADMAP ITEMS & DRAG-AND-DROP REORDERING
# ==============================================================================
def test_roadmap_items_and_reordering(client):
    headers, user_id, _ = get_auth_headers(client, "road_user")
    ws_id = create_test_workspace(client, headers, "Roadmap WS")

    # 1. Create strategic initiative
    init_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/initiatives",
        json={
            "title": "H1 Security & Compliance",
            "strategic_goal": "Achieve SOC 2 Type II readiness",
            "target_quarter": "Q2 2026",
            "progress_pct": 25.0,
            "status": "IN_PROGRESS",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert init_res.status_code == 201
    init_id = init_res.json()["id"]

    # 2. Create 3 roadmap items
    item1_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap",
        json={
            "initiative_id": init_id,
            "title": "Audit Logging v2",
            "quarter": "Q1 2026",
            "status": "PLANNED",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    item2_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap",
        json={
            "initiative_id": init_id,
            "title": "Encrypted Exports",
            "quarter": "Q1 2026",
            "status": "PLANNED",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    item1_id = item1_res.json()["id"]
    item2_id = item2_res.json()["id"]

    # 3. Reorder roadmap items across quarters
    reorder_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap/reorder",
        json={
            "items": [
                {"id": item2_id, "sort_order": 0, "quarter": "Q2 2026"},
                {"id": item1_id, "sort_order": 1, "quarter": "Q2 2026"},
            ]
        },
        headers=headers,
    )
    assert reorder_res.status_code == 200, reorder_res.text
    assert reorder_res.json()["status"] == "reordered"

    # 4. Verify new quarters and sort orders
    list_res = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap",
        headers=headers,
    )
    assert list_res.status_code == 200
    items = {item["id"]: item for item in list_res.json()}
    assert items[item2_id]["quarter"] == "Q2 2026"
    assert items[item2_id]["sort_order"] == 0
    assert items[item1_id]["quarter"] == "Q2 2026"
    assert items[item1_id]["sort_order"] == 1

# ==============================================================================
# 6. ROADMAP DEPENDENCIES & CYCLE DETECTION
# ==============================================================================
def test_roadmap_dependencies_and_cycle_prevention(client):
    headers, user_id, _ = get_auth_headers(client, "dep_user")
    ws_id = create_test_workspace(client, headers, "Dep WS")

    # Create 3 items: A, B, C
    res_a = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap",
        json={"title": "Item A - Schema Migration", "quarter": "Q1 2026", "workspace_id": ws_id},
        headers=headers,
    )
    res_b = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap",
        json={"title": "Item B - API Endpoints", "quarter": "Q1 2026", "workspace_id": ws_id},
        headers=headers,
    )
    res_c = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap",
        json={"title": "Item C - UI Dashboard", "quarter": "Q1 2026", "workspace_id": ws_id},
        headers=headers,
    )
    id_a = res_a.json()["id"]
    id_b = res_b.json()["id"]
    id_c = res_c.json()["id"]

    # 1. B depends on A (A -> B)
    dep_ab = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap/dependencies",
        json={"roadmap_item_id": id_b, "depends_on_item_id": id_a, "workspace_id": ws_id},
        headers=headers,
    )
    assert dep_ab.status_code == 201, dep_ab.text
    dep_ab_id = dep_ab.json()["id"]

    # 2. C depends on B (B -> C)
    dep_bc = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap/dependencies",
        json={"roadmap_item_id": id_c, "depends_on_item_id": id_b, "workspace_id": ws_id},
        headers=headers,
    )
    assert dep_bc.status_code == 201, dep_bc.text

    # 3. Try to add A depends on C (C -> A). This creates cycle: A -> B -> C -> A
    cycle_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap/dependencies",
        json={"roadmap_item_id": id_a, "depends_on_item_id": id_c, "workspace_id": ws_id},
        headers=headers,
    )
    assert cycle_res.status_code == 400
    assert "Circular dependency detected" in cycle_res.json()["detail"]

    # 4. List dependencies
    list_deps = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap/dependencies?roadmap_item_id={id_b}",
        headers=headers,
    )
    assert list_deps.status_code == 200
    deps = list_deps.json()
    assert len(deps) >= 1

    # 5. Delete dependency
    del_dep = client.delete(
        f"{settings.API_V1_STR}/product-lifecycle/roadmap/dependencies/{dep_ab_id}",
        headers=headers,
    )
    assert del_dep.status_code == 204

# ==============================================================================
# 7. EXPERIMENTATION STATISTICAL ANALYSIS & A/B TESTING
# ==============================================================================
def test_experimentation_statistical_analysis(client):
    headers, user_id, _ = get_auth_headers(client, "exp_user")
    ws_id = create_test_workspace(client, headers, "Exp WS")

    # 1. Invalid variant allocation sum (!= 100%)
    invalid_exp_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/experiments",
        json={
            "name": "Onboarding Flow Test",
            "metric_key": "signup_completed",
            "hypothesis": "Short form increases conversion by 15%",
            "variants": [
                {"variant_name": "Control", "variant_key": "control", "allocation_pct": 50.0},
                {"variant_name": "Treatment", "variant_key": "treatment", "allocation_pct": 30.0},
            ],
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert invalid_exp_res.status_code == 400
    assert "sum to 100%" in invalid_exp_res.json()["detail"]

    # 2. Valid experiment creation
    create_exp_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/experiments",
        json={
            "name": "Onboarding Flow Test v2",
            "metric_key": "signup_completed",
            "hypothesis": "Short form increases conversion by 15%",
            "status": "DRAFT",
            "variants": [
                {"variant_name": "Control", "variant_key": "control", "allocation_pct": 50.0},
                {"variant_name": "Treatment", "variant_key": "treatment", "allocation_pct": 50.0},
            ],
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert create_exp_res.status_code == 201, create_exp_res.text
    exp_id = create_exp_res.json()["id"]

    # 3. Transition DRAFT -> RUNNING
    run_res = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/experiments/{exp_id}",
        json={"status": "RUNNING"},
        headers=headers,
    )
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "RUNNING"

    # 4. Assign user
    assign_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/experiments/{exp_id}/assign",
        headers=headers,
    )
    assert assign_res.status_code == 200
    variant = assign_res.json()
    assert variant["variant_key"] in ["control", "treatment"]

    # 5. Populate telemetry conversion counts for statistical analysis
    db = SessionLocal()
    try:
        variants = db.query(ExperimentVariant).filter(ExperimentVariant.experiment_id == exp_id).all()
        v_control = next(v for v in variants if v.variant_key == "control")
        v_treat = next(v for v in variants if v.variant_key == "treatment")

        # Control: 100 impressions, 10 conversions (10%)
        # Treatment: 100 impressions, 25 conversions (25%)
        v_control.impression_count = 100
        v_control.conversion_count = 10
        v_treat.impression_count = 100
        v_treat.conversion_count = 25

        exp = db.query(ProductExperiment).filter(ProductExperiment.id == exp_id).first()
        exp.total_sample_size = 200
        db.commit()
    finally:
        db.close()

    # 6. Calculate statistical analysis
    analysis_res = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/experiments/{exp_id}/analysis",
        headers=headers,
    )
    assert analysis_res.status_code == 200, analysis_res.text
    analysis = analysis_res.json()
    assert analysis["experiment_id"] == exp_id
    assert analysis["total_sample_size"] == 200
    assert analysis["relative_uplift_pct"] == 150.0  # (0.25 - 0.10) / 0.10 = 1.50 -> 150%
    assert analysis["p_value"] < 0.05
    assert analysis["is_statistically_significant"] is True
    assert "Statistically significant positive uplift" in analysis["conclusion"]

# ==============================================================================
# 8. RELEASE MANAGEMENT & READINESS SCORING
# ==============================================================================
def test_release_management_and_readiness_scoring(client):
    headers, user_id, _ = get_auth_headers(client, "rel_user")
    ws_id = create_test_workspace(client, headers, "Release WS")

    # 1. Create a release
    unique_ver = f"v2.5.0-{uuid.uuid4().hex[:6]}"
    rel_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/releases",
        json={
            "release_version": unique_ver,
            "target_date": "2026-06-01T00:00:00Z",
            "release_notes": "SSO, dark mode and compliance enhancements",
            "status": "PLANNING",
            "rollout_percentage": 0.0,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert rel_res.status_code == 201, rel_res.text
    rel = rel_res.json()
    rel_id = rel["id"]

    # 2. Check initial readiness
    readiness_res = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/releases/{rel_id}/readiness",
        headers=headers,
    )
    assert readiness_res.status_code == 200
    readiness = readiness_res.json()
    assert readiness["readiness_score"] >= 0.0
    assert readiness["readiness_status"] in ["READY_FOR_RELEASE", "ON_TRACK", "AT_RISK", "BLOCKED"]

    # 3. Valid stage transition: PLANNING -> DEVELOPMENT -> CODE_FREEZE
    patch_dev = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/releases/{rel_id}",
        json={"status": "DEVELOPMENT"},
        headers=headers,
    )
    assert patch_dev.status_code == 200
    assert patch_dev.json()["status"] == "DEVELOPMENT"

    patch_freeze = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/releases/{rel_id}",
        json={"status": "CODE_FREEZE"},
        headers=headers,
    )
    assert patch_freeze.status_code == 200
    assert patch_freeze.json()["status"] == "CODE_FREEZE"

    # 4. Invalid stage transition: CODE_FREEZE -> PLANNING (backwards jump rejected)
    invalid_rel = client.patch(
        f"{settings.API_V1_STR}/product-lifecycle/releases/{rel_id}",
        json={"status": "PLANNING"},
        headers=headers,
    )
    assert invalid_rel.status_code == 400
    assert "Invalid release stage transition" in invalid_rel.json()["detail"]

# ==============================================================================
# 9. GROUNDED AI PRODUCT ASSISTANT
# ==============================================================================
def test_ai_product_assistant_grounding(client):
    headers, user_id, _ = get_auth_headers(client, "ai_user")
    ws_id = create_test_workspace(client, headers, "AI WS")

    # Add a feature request to provide real context for the assistant
    client.post(
        f"{settings.API_V1_STR}/product-lifecycle/feature-requests",
        json={
            "title": "Real-time Notification Webhooks",
            "description": "Send JSON webhooks on project updates",
            "request_count": 12,
            "revenue_impact": 50000.0,
            "priority": "HIGH",
            "status": "OPEN",
            "workspace_id": ws_id,
        },
        headers=headers,
    )

    # Query assistant about customer demand
    ai_res = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/ai/query",
        json={
            "query": "What are the top customer demanded features and their revenue impact?",
            "context_type": "CUSTOMER_DEMAND",
        },
        headers=headers,
    )
    assert ai_res.status_code == 200, ai_res.text
    ai_data = ai_res.json()
    assert ai_data["answer"] != ""
    assert len(ai_data["recommended_roadmap_actions"]) > 0
    assert "grounded_evidence" in ai_data

# ==============================================================================
# 10. MULTI-TENANT ISOLATION
# ==============================================================================
def test_product_lifecycle_multi_tenant_isolation(client):
    # Tenant 1
    headers1, user1_id, _ = get_auth_headers(client, "tenant1_user")
    ws1_id = create_test_workspace(client, headers1, "Tenant1 WS")

    # Tenant 2
    headers2, user2_id, _ = get_auth_headers(client, "tenant2_user")
    ws2_id = create_test_workspace(client, headers2, "Tenant2 WS")

    # Tenant 1 creates a private discovery
    t1_disc = client.post(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries",
        json={
            "title": "Tenant 1 Secret Innovation",
            "problem_statement": "Secret problem",
            "hypothesis": "Secret hypothesis",
            "target_users": "Secret users",
            "business_impact": "High",
            "customer_impact": "High",
            "workspace_id": ws1_id,
        },
        headers=headers1,
    ).json()

    # Tenant 2 tries to read Tenant 1's discovery by ID
    t2_read = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries/{t1_disc['id']}",
        headers=headers2,
    )
    assert t2_read.status_code == 404

    # Tenant 2 lists discoveries - Tenant 1's discovery must not appear
    t2_list = client.get(
        f"{settings.API_V1_STR}/product-lifecycle/discoveries",
        headers=headers2,
    ).json()
    assert all(d["id"] != t1_disc["id"] for d in t2_list)

# ==============================================================================
# 11. B15 AUTOMATION ENGINE INTEGRATION
# ==============================================================================
def test_product_lifecycle_b15_automation(client):
    headers, user_id, _ = get_auth_headers(client, "auto_user")
    ws_id = create_test_workspace(client, headers, "Auto WS")

    db = SessionLocal()
    try:
        # 1. Action: create_product_idea
        res_idea = execute_product_lifecycle_automation_action(
            db=db,
            action_type="create_product_idea",
            payload={
                "title": "Auto Created Innovation",
                "description": "Spawned by B15 automation trigger",
                "workspace_id": ws_id,
            },
            user_id=user_id,
            organization_id=ws_id,
        )
        assert res_idea["status"] == "success"
        idea_id = res_idea["idea_id"]

        # Verify in database
        idea = db.query(ProductIdea).filter(ProductIdea.id == idea_id).first()
        assert idea is not None
        assert idea.title == "Auto Created Innovation"

        # 2. Action: update_feature_request_status
        freq = ProductFeatureRequest(
            title="Auto Feature",
            description="Testing automated status bump",
            customer_name="Automated Enterprise",
            organization_id=ws_id,
            status="OPEN",
        )
        db.add(freq)
        db.commit()
        db.refresh(freq)

        res_update = execute_product_lifecycle_automation_action(
            db=db,
            action_type="update_feature_request_status",
            payload={"feature_request_id": freq.id, "status": "IN_REVIEW"},
            user_id=user_id,
            organization_id=ws_id,
        )
        assert res_update["status"] == "success"
        db.refresh(freq)
        assert freq.status == "IN_REVIEW"

        # 3. Action: advance_release_stage
        rel_ver = f"v3.0.0-{uuid.uuid4().hex[:6]}"
        rel = ProductRelease(
            release_version=rel_ver,
            title=f"Release {rel_ver}",
            description="Automated release",
            release_notes="Initial release notes",
            organization_id=ws_id,
            status="PLANNING",
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)

        res_rel = execute_product_lifecycle_automation_action(
            db=db,
            action_type="advance_release_stage",
            payload={"release_id": rel.id, "status": "DEVELOPMENT"},
            user_id=user_id,
            organization_id=ws_id,
        )
        assert res_rel["status"] == "success"
        db.refresh(rel)
        assert rel.status == "DEVELOPMENT"
    finally:
        db.close()
