import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.strategic_intelligence import (
    StrategicPlan,
    StrategicGoal,
    StrategicInitiative,
    MarketIntelligence,
    MarketSignal,
    Competitor,
    SWOTEntry,
    MarketSizing,
    StrategicOpportunity,
    StrategicScenario,
    StrategicDecision,
    BusinessKPI,
    BusinessKPIValue,
)
from app.services.strategic_intelligence_service import execute_strategic_automation_action

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client: TestClient, prefix: str = "strat_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique}@focusboard.io"
    password = "TestPassword123!"

    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"Strategic User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    headers = {"Authorization": f"Bearer {token}"}
    return headers, user_id, email

def create_test_workspace(client: TestClient, headers: dict, name: str = "Strategy WS") -> int:
    ws_res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Strategy Test Workspace"},
        headers=headers,
    )
    assert ws_res.status_code == 201, ws_res.text
    return ws_res.json()["id"]

# ==============================================================================
# 1. OVERVIEW & BASELINE SEEDING
# ==============================================================================
def test_strategic_overview_and_baseline_seeding(client):
    headers, user_id, _ = get_auth_headers(client, "strat_ov")
    ws_id = create_test_workspace(client, headers, "Overview WS")

    # Test via API_V1_STR
    res1 = client.get(f"{settings.API_V1_STR}/strategy/overview?workspace_id={ws_id}", headers=headers)
    assert res1.status_code == 200, res1.text
    data1 = res1.json()

    assert data1["active_plans_count"] >= 1
    assert data1["total_goals_count"] >= 2
    assert "goal_completion_rate" in data1
    assert data1["active_initiatives_count"] >= 2
    assert data1["tracked_competitors_count"] >= 3
    assert data1["open_opportunities_count"] >= 2
    assert data1["total_pipeline_value_dollars"] > 0
    assert "STRENGTH" in data1["swot_summary"]
    assert len(data1["top_opportunities"]) >= 1
    assert len(data1["ai_recommendations"]) >= 2

    # Test direct /strategy/overview
    res2 = client.get(f"/strategy/overview?workspace_id={ws_id}", headers=headers)
    assert res2.status_code == 200, res2.text

# ==============================================================================
# 2. STRATEGIC PLANS & GOALS LIFECYCLE
# ==============================================================================
def test_strategic_plans_and_goals_lifecycle(client):
    headers, user_id, _ = get_auth_headers(client, "strat_plan")
    ws_id = create_test_workspace(client, headers, "Plan WS")

    # 1. Create Strategic Plan
    plan_payload = {
        "title": "Global Enterprise Expansion FY28",
        "vision": "Lead the enterprise collaborative intelligence ecosystem.",
        "mission": "Deliver mission-critical tools with zero data leakage.",
        "strategic_themes_json": '["SOC2 Compliance", "Autonomous AI Agents"]',
        "time_horizon": "ANNUAL",
        "status": "ACTIVE",
        "workspace_id": ws_id,
    }
    res_plan = client.post(f"{settings.API_V1_STR}/strategy/plans", json=plan_payload, headers=headers)
    assert res_plan.status_code == 201, res_plan.text
    plan_data = res_plan.json()
    plan_id = plan_data["id"]
    assert plan_data["title"] == plan_payload["title"]

    # Update Plan
    up_res = client.patch(f"{settings.API_V1_STR}/strategy/plans/{plan_id}", json={"status": "ACTIVE"}, headers=headers)
    assert up_res.status_code == 200

    # 2. Create Strategic Goal
    goal_payload = {
        "plan_id": plan_id,
        "title": "Reach $500k ARR",
        "description": "Expand sales outbound to multi-region clients.",
        "category": "REVENUE",
        "target_metric": "ARR Cents",
        "baseline_value": 100000.0,
        "target_value": 500000.0,
        "current_value": 300000.0,
        "unit": "$",
        "status": "ACTIVE",
        "workspace_id": ws_id,
    }
    res_goal = client.post(f"{settings.API_V1_STR}/strategy/goals", json=goal_payload, headers=headers)
    assert res_goal.status_code == 201, res_goal.text
    goal_data = res_goal.json()
    goal_id = goal_data["id"]
    # (300k - 100k) / (500k - 100k) = 200k / 400k = 50%
    assert goal_data["progress_percentage"] == 50.0

    # Update Goal Current Value
    up_goal = client.patch(
        f"{settings.API_V1_STR}/strategy/goals/{goal_id}",
        json={"current_value": 400000.0},
        headers=headers,
    )
    assert up_goal.status_code == 200
    assert up_goal.json()["progress_percentage"] == 75.0

    # 3. Create Initiative linked to Goal
    init_payload = {
        "goal_id": goal_id,
        "title": "Automate SAML SSO Onboarding",
        "description": "Support Okta, Azure AD, and Google Workspace SSO.",
        "priority": "P1_CRITICAL",
        "budget_amount": 12000.0,
        "status": "IN_PROGRESS",
        "progress_percentage": 50.0,
        "workspace_id": ws_id,
    }
    res_init = client.post(f"{settings.API_V1_STR}/strategy/initiatives", json=init_payload, headers=headers)
    assert res_init.status_code == 201, res_init.text
    init_id = res_init.json()["id"]

    # Update Initiative
    up_init = client.patch(
        f"{settings.API_V1_STR}/strategy/initiatives/{init_id}",
        json={"progress_percentage": 90.0, "status": "IN_PROGRESS"},
        headers=headers,
    )
    assert up_init.status_code == 200
    assert up_init.json()["progress_percentage"] == 90.0

# ==============================================================================
# 3. BUSINESS KPIS & HISTORICAL TRACKING
# ==============================================================================
def test_business_kpis_and_historical_tracking(client):
    headers, user_id, _ = get_auth_headers(client, "strat_kpi")
    ws_id = create_test_workspace(client, headers, "KPI WS")

    # 1. Create KPI
    kpi_payload = {
        "name": "Customer Net Promoter Score (NPS)",
        "description": "Quarterly transactional and relational NPS aggregate",
        "category": "CUSTOMER",
        "measurement_unit": "pts",
        "target_value": 75.0,
        "current_value": 58.0,
        "baseline_value": 40.0,
        "trend_direction": "UP",
        "status": "ON_TRACK",
        "workspace_id": ws_id,
    }
    res_kpi = client.post(f"{settings.API_V1_STR}/strategy/kpis", json=kpi_payload, headers=headers)
    assert res_kpi.status_code == 201, res_kpi.text
    kpi_data = res_kpi.json()
    kpi_id = kpi_data["id"]

    # 2. Record Historical Value
    val_payload = {
        "value": 64.0,
        "period_date": "2026-Q4",
        "notes": "Post-release satisfaction survey results.",
    }
    res_val = client.post(f"{settings.API_V1_STR}/strategy/kpis/{kpi_id}/values", json=val_payload, headers=headers)
    assert res_val.status_code == 201, res_val.text

    # 3. List KPIs and verify update
    res_list = client.get(f"{settings.API_V1_STR}/strategy/kpis?workspace_id={ws_id}", headers=headers)
    assert res_list.status_code == 200
    kpis = res_list.json()
    target_kpi = next(k for k in kpis if k["id"] == kpi_id)
    assert target_kpi["current_value"] == 64.0
    assert target_kpi["trend_direction"] == "UP"
    assert len(target_kpi["history"]) >= 1

# ==============================================================================
# 4. MARKET INTELLIGENCE & SIGNALS
# ==============================================================================
def test_market_intelligence_and_signals(client):
    headers, user_id, _ = get_auth_headers(client, "strat_mkt")
    ws_id = create_test_workspace(client, headers, "Market WS")

    # 1. Create Market Intelligence
    mkt_payload = {
        "title": "Rise of Autonomous Multi-Agent Systems in Enterprise Ops",
        "intelligence_type": "TECH_DISRUPTION",
        "summary": "70% of Fortune 500 planning autonomous agent deployments by 2027.",
        "source_name": "Gartner Technology Radar",
        "source_url": "https://gartner.com/report/autonomous-agents",
        "confidence_score": 0.95,
        "impact_rating": "TRANSFORMATIVE",
        "workspace_id": ws_id,
    }
    res_mkt = client.post(f"{settings.API_V1_STR}/strategy/market-intel", json=mkt_payload, headers=headers)
    assert res_mkt.status_code == 201, res_mkt.text

    list_mkt = client.get(f"{settings.API_V1_STR}/strategy/market-intel?workspace_id={ws_id}", headers=headers)
    assert list_mkt.status_code == 200
    assert any(m["title"] == mkt_payload["title"] for m in list_mkt.json())

    # 2. Create Market Signal
    sig_payload = {
        "signal_type": "CUSTOMER_DEMAND",
        "title": "Spike in self-hosted zero-trust deployment inquiries",
        "observations": "Three healthcare prospects requested on-prem or private-cloud options.",
        "trend_direction": "ACCELERATING",
        "urgency": "IMMEDIATE",
        "is_converted_to_opportunity": False,
        "workspace_id": ws_id,
    }
    res_sig = client.post(f"{settings.API_V1_STR}/strategy/signals", json=sig_payload, headers=headers)
    assert res_sig.status_code == 201, res_sig.text

    list_sig = client.get(f"{settings.API_V1_STR}/strategy/signals?workspace_id={ws_id}", headers=headers)
    assert list_sig.status_code == 200
    assert any(s["title"] == sig_payload["title"] for s in list_sig.json())

# ==============================================================================
# 5. COMPETITORS TRACKING & DIFFERENTIATION
# ==============================================================================
def test_competitors_tracking_and_differentiation(client):
    headers, user_id, _ = get_auth_headers(client, "strat_comp")
    ws_id = create_test_workspace(client, headers, "Comp WS")

    unique_name = f"NotionWork_{uuid.uuid4().hex[:6]}"
    comp_payload = {
        "name": unique_name,
        "website": "https://notion.so",
        "market_position": "CHALLENGER",
        "pricing_model": "PER_SEAT",
        "strengths_json": '["Flexible document canvas", "Strong community templates"]',
        "weaknesses_json": '["Unstructured data model", "Lacks strict project governance"]',
        "threat_level": "MEDIUM",
        "notes": "Broad workspace tool expanding into project management.",
        "workspace_id": ws_id,
    }
    res_comp = client.post(f"{settings.API_V1_STR}/strategy/competitors", json=comp_payload, headers=headers)
    assert res_comp.status_code == 201, res_comp.text
    comp_id = res_comp.json()["id"]

    # Update competitor
    up_res = client.patch(
        f"{settings.API_V1_STR}/strategy/competitors/{comp_id}",
        json={"threat_level": "HIGH"},
        headers=headers,
    )
    assert up_res.status_code == 200
    assert up_res.json()["threat_level"] == "HIGH"

# ==============================================================================
# 6. SWOT MATRIX MANAGEMENT
# ==============================================================================
def test_swot_matrix_management(client):
    headers, user_id, _ = get_auth_headers(client, "strat_swot")
    ws_id = create_test_workspace(client, headers, "SWOT WS")

    swot_payload = {
        "swot_type": "OPPORTUNITY",
        "title": "FedRAMP Moderate Certification for GovCloud",
        "description": "Unlock federal agency and defense contractor procurement contracts.",
        "impact": "HIGH",
        "evidence_text": "Government IT modernization bill allocates $2B for modern software.",
        "is_ai_generated": False,
        "workspace_id": ws_id,
    }
    res_swot = client.post(f"{settings.API_V1_STR}/strategy/swot", json=swot_payload, headers=headers)
    assert res_swot.status_code == 201, res_swot.text

    list_swot = client.get(f"{settings.API_V1_STR}/strategy/swot?workspace_id={ws_id}", headers=headers)
    assert list_swot.status_code == 200
    assert any(s["title"] == swot_payload["title"] for s in list_swot.json())

# ==============================================================================
# 7. MARKET SIZING (TAM / SAM / SOM)
# ==============================================================================
def test_market_sizing_tam_sam_som(client):
    headers, user_id, _ = get_auth_headers(client, "strat_size")
    ws_id = create_test_workspace(client, headers, "Size WS")

    sizing_payload = {
        "market_name": "AI-Powered Autonomous DevOps & PM Workspaces",
        "methodology": "BOTTOM_UP",
        "tam_cents": 2800000000000,  # $28B
        "sam_cents": 550000000000,   # $5.5B
        "som_cents": 8000000000,     # $80M
        "currency": "USD",
        "assumptions_json": '{"developer_seats": 35000000, "arpu": 150}',
        "confidence_score": 0.82,
        "workspace_id": ws_id,
    }
    res_size = client.post(f"{settings.API_V1_STR}/strategy/market-sizing", json=sizing_payload, headers=headers)
    assert res_size.status_code == 201, res_size.text
    data = res_size.json()
    assert data["tam_dollars"] == 28000000000.0
    assert data["sam_dollars"] == 5500000000.0
    assert data["som_dollars"] == 80000000.0

# ==============================================================================
# 8. STRATEGIC OPPORTUNITIES & RICE PRIORITIZATION
# ==============================================================================
def test_strategic_opportunities_and_rice_scoring(client):
    headers, user_id, _ = get_auth_headers(client, "strat_opp")
    ws_id = create_test_workspace(client, headers, "Opp WS")

    # Formula: (reach * impact * confidence) / effort
    # (4000 * 3.0 * 0.8) / 2.0 = 9600 / 2.0 = 4800.0
    opp_payload = {
        "title": "Interactive Workflow Debugger for Autonomous AI Agents",
        "description": "Visual step-by-step trace viewer and time-travel replay engine.",
        "customer_segment": "AI Engineers",
        "estimated_value_cents": 2500000,
        "feasibility_score": 8.5,
        "rice_reach": 4000.0,
        "rice_impact": 3.0,
        "rice_confidence": 0.8,
        "rice_effort": 2.0,
        "status": "EVALUATING",
        "workspace_id": ws_id,
    }
    res_opp = client.post(f"{settings.API_V1_STR}/strategy/opportunities", json=opp_payload, headers=headers)
    assert res_opp.status_code == 201, res_opp.text
    opp_data = res_opp.json()
    opp_id = opp_data["id"]
    assert opp_data["rice_score"] == 4800.0
    assert opp_data["estimated_value"] == 25000.0

    # Update effort to 4.0 -> score becomes 2400.0
    up_opp = client.patch(
        f"{settings.API_V1_STR}/strategy/opportunities/{opp_id}",
        json={"rice_effort": 4.0},
        headers=headers,
    )
    assert up_opp.status_code == 200
    assert up_opp.json()["rice_score"] == 2400.0

# ==============================================================================
# 9. STRATEGIC SCENARIOS & COMPARISON
# ==============================================================================
def test_strategic_scenarios_and_comparison(client):
    headers, user_id, _ = get_auth_headers(client, "strat_scen")
    ws_id = create_test_workspace(client, headers, "Scenario WS")

    scen_payload = {
        "name": "Accelerated PLG Viral Growth Scenario",
        "scenario_type": "BEST_CASE",
        "description": "Viral referral loop drives 65% QoQ expansion.",
        "revenue_multiplier": 1.65,
        "churn_rate_impact": -0.02,
        "assumptions_json": '{"viral_k_factor": 1.35}',
        "workspace_id": ws_id,
    }
    res_scen = client.post(f"{settings.API_V1_STR}/strategy/scenarios", json=scen_payload, headers=headers)
    assert res_scen.status_code == 201, res_scen.text

    # Compare Scenarios
    res_comp = client.post(f"{settings.API_V1_STR}/strategy/scenarios/compare?workspace_id={ws_id}", json=None, headers=headers)
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert len(comp_data["scenarios"]) >= 1
    assert "metrics_comparison" in comp_data

# ==============================================================================
# 10. STRATEGIC DECISIONS LOG
# ==============================================================================
def test_strategic_decisions_log(client):
    headers, user_id, _ = get_auth_headers(client, "strat_dec")
    ws_id = create_test_workspace(client, headers, "Decision WS")

    dec_payload = {
        "title": "Migrate In-Memory Cache to Redis Cluster",
        "context": "High-concurrency tenant queries causing websocket latency spikes.",
        "decision_outcome": "Deploy replicated Redis caching cluster with semantic ttl.",
        "rationale": "Reduces database read load by 60% and maintains sub-25ms P95 latency.",
        "status": "APPROVED",
        "workspace_id": ws_id,
    }
    res_dec = client.post(f"{settings.API_V1_STR}/strategy/decisions", json=dec_payload, headers=headers)
    assert res_dec.status_code == 201, res_dec.text
    dec_data = res_dec.json()
    assert dec_data["title"] == dec_payload["title"]

# ==============================================================================
# 11. GROUNDED AI STRATEGY ANALYZER
# ==============================================================================
def test_grounded_ai_strategic_analysis(client):
    headers, user_id, _ = get_auth_headers(client, "strat_ai")
    ws_id = create_test_workspace(client, headers, "AI Strategy WS")

    ai_payload = {
        "context": "executive_strategy",
        "focus_theme": "Enterprise Expansion",
        "include_competitors": True,
        "include_swot": True,
        "workspace_id": ws_id,
    }
    res_ai = client.post(f"{settings.API_V1_STR}/strategy/ai/analyze", json=ai_payload, headers=headers)
    assert res_ai.status_code == 200, res_ai.text
    ai_data = res_ai.json()

    assert "summary" in ai_data
    assert ai_data["strategic_score"] > 0
    assert len(ai_data["recommendations"]) >= 1
    assert len(ai_data["identified_risks"]) >= 1
    assert len(ai_data["identified_opportunities"]) >= 1

# ==============================================================================
# 12. MULTI-TENANT WORKSPACE ISOLATION
# ==============================================================================
def test_multi_tenant_workspace_isolation(client):
    headers_a, user_a, _ = get_auth_headers(client, "strat_tenant_a")
    headers_b, user_b, _ = get_auth_headers(client, "strat_tenant_b")

    ws_a = create_test_workspace(client, headers_a, "Workspace A")
    ws_b = create_test_workspace(client, headers_b, "Workspace B")

    # User A creates a plan in Workspace A
    res = client.post(
        f"{settings.API_V1_STR}/strategy/plans",
        json={
            "title": "Workspace A Confidential Strategy",
            "vision": "Vision A",
            "mission": "Mission A",
            "workspace_id": ws_a,
        },
        headers=headers_a,
    )
    assert res.status_code == 201

    # User B attempts to access Workspace A overview or plans explicitly -> must get 403 Forbidden
    res_forbidden = client.get(
        f"{settings.API_V1_STR}/strategy/overview?workspace_id={ws_a}",
        headers=headers_b,
    )
    assert res_forbidden.status_code == 403, "Cross-tenant access must be rejected with 403"

    res_forbidden_plans = client.get(
        f"{settings.API_V1_STR}/strategy/plans?workspace_id={ws_a}",
        headers=headers_b,
    )
    assert res_forbidden_plans.status_code == 403, "Cross-tenant access must be rejected with 403"

# ==============================================================================
# 13. B15 AUTOMATION ACTION EXECUTION
# ==============================================================================
def test_b15_automation_action_execution(client):
    headers, user_id, _ = get_auth_headers(client, "strat_auto")
    ws_id = create_test_workspace(client, headers, "Automation WS")

    db = SessionLocal()
    try:
        # 1. Create Goal Action
        act1 = execute_strategic_automation_action(
            db=db,
            action_type="CREATE_STRATEGIC_GOAL",
            payload={"title": "Automated Milestone Goal", "target_value": 100.0},
            workspace_id=ws_id,
        )
        assert act1["status"] == "SUCCESS"
        assert "goal_id" in act1

        # 2. Record KPI Value Action
        act2 = execute_strategic_automation_action(
            db=db,
            action_type="RECORD_BUSINESS_KPI_VALUE",
            payload={"value": 88.5, "period_date": "2026-Q4"},
            workspace_id=ws_id,
        )
        assert act2["status"] == "SUCCESS"

        # 3. Evaluate Risks Action
        act3 = execute_strategic_automation_action(
            db=db,
            action_type="EVALUATE_STRATEGIC_RISKS",
            payload={},
            workspace_id=ws_id,
        )
        assert act3["status"] == "SUCCESS"

        # 4. Create Strategic Opportunity Action
        act4 = execute_strategic_automation_action(
            db=db,
            action_type="CREATE_STRATEGIC_OPPORTUNITY",
            payload={"title": "Automated Market Opportunity", "estimated_value_cents": 500000},
            workspace_id=ws_id,
        )
        assert act4["status"] == "SUCCESS"
        assert "opportunity_id" in act4
    finally:
        db.close()
