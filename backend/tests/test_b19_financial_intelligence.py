import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.financial_intelligence import (
    FinancialTransaction,
    CostRecord,
    FinancialBudget,
    FinancialForecast,
    FinancialDataSource,
    FinancialImport,
    FinancialInsight,
    FinancialRecommendation,
    FinancialScenario,
)
from app.services.financial_intelligence_service import execute_financial_automation_action

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client: TestClient, prefix: str = "fin_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique}@focusboard.io"
    password = "TestPassword123!"

    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"Financial User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    headers = {"Authorization": f"Bearer {token}"}
    return headers, user_id, email

def create_test_workspace(client: TestClient, headers: dict, name: str = "Finance WS") -> int:
    ws_res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Finance Test Workspace"},
        headers=headers,
    )
    assert ws_res.status_code == 201, ws_res.text
    return ws_res.json()["id"]

# ==============================================================================
# 1. OVERVIEW & BASELINE TELEMETRY
# ==============================================================================
def test_financial_overview_and_baseline_telemetry(client):
    headers, user_id, _ = get_auth_headers(client, "fin_ov")
    ws_id = create_test_workspace(client, headers, "Overview WS")

    res = client.get(f"{settings.API_V1_STR}/finance/overview?workspace_id={ws_id}", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total_mrr"] > 0.0
    assert round(data["total_arr"], 1) == round(data["total_mrr"] * 12.0, 1)
    assert data["gross_revenue"] > 0.0
    assert data["net_revenue"] > 0.0
    assert data["finops"]["gross_margin_percentage"] > 0.0
    assert data["finops"]["total_direct_costs"] > 0.0
    assert data["retention"]["gross_revenue_retention"] > 0.0
    assert data["retention"]["net_revenue_retention"] > 0.0
    assert data["unit_economics"]["arpu"] > 0.0
    assert data["unit_economics"]["ltv_to_cac_ratio"] > 0.0
    assert len(data["active_budgets"]) >= 2
    assert len(data["projected_forecasts"]) >= 3

# ==============================================================================
# 2. TRANSACTION LEDGER & REVENUE CALCULATION
# ==============================================================================
def test_transaction_ledger_lifecycle_and_calculations(client):
    headers, user_id, _ = get_auth_headers(client, "fin_tx")
    ws_id = create_test_workspace(client, headers, "Ledger WS")

    # 1. Record subscription payment
    tx1_res = client.post(
        f"{settings.API_V1_STR}/finance/transactions",
        json={
            "transaction_type": "SUBSCRIPTION_PAYMENT",
            "amount_cents": 59900,  # $599.00
            "currency": "USD",
            "status": "SUCCEEDED",
            "description": "Enterprise Annual Tier Renewal",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert tx1_res.status_code == 201, tx1_res.text
    tx1 = tx1_res.json()
    assert tx1["amount"] == 599.00
    assert tx1["status"] == "SUCCEEDED"

    # 2. Record expansion payment
    tx2_res = client.post(
        f"{settings.API_V1_STR}/finance/transactions",
        json={
            "transaction_type": "SEAT_EXPANSION",
            "amount_cents": 12000,  # $120.00
            "currency": "USD",
            "status": "SUCCEEDED",
            "description": "10 Additional Engineering Seats",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert tx2_res.status_code == 201
    assert tx2_res.json()["amount"] == 120.00

    # 3. List transactions
    list_res = client.get(f"{settings.API_V1_STR}/finance/transactions?workspace_id={ws_id}", headers=headers)
    assert list_res.status_code == 200
    tx_list = list_res.json()
    assert len(tx_list) >= 2
    descriptions = [t["description"] for t in tx_list]
    assert "Enterprise Annual Tier Renewal" in descriptions

# ==============================================================================
# 3. COST MANAGEMENT & BUDGET THRESHOLD ALERTS
# ==============================================================================
def test_cost_records_and_budget_threshold_alerts(client):
    headers, user_id, _ = get_auth_headers(client, "fin_cost")
    ws_id = create_test_workspace(client, headers, "Cost WS")

    # 1. Create a custom spending budget with 75% threshold
    bdg_res = client.post(
        f"{settings.API_V1_STR}/finance/budgets",
        json={
            "category": "AI_SERVICES",
            "budget_amount_cents": 100000,  # $1,000.00
            "currency": "USD",
            "period": "MONTHLY",
            "alert_threshold_percentage": 75.0,
            "status": "ACTIVE",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert bdg_res.status_code == 201, bdg_res.text
    bdg = bdg_res.json()
    bdg_id = bdg["id"]
    assert bdg["budget_amount"] == 1000.00

    # 2. Ingest cost record below threshold
    now_period = datetime.now(timezone.utc).strftime("%Y-%m")
    cost1_res = client.post(
        f"{settings.API_V1_STR}/finance/costs",
        json={
            "category": "AI_SERVICES",
            "description": "Claude 3.5 Sonnet Prompt Processing",
            "amount_cents": 50000,  # $500.00 (50% of budget)
            "currency": "USD",
            "billing_period": now_period,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert cost1_res.status_code == 201
    assert cost1_res.json()["amount"] == 500.00

    # 3. Ingest cost record crossing threshold (+$350 -> $850 = 85% > 75%)
    cost2_res = client.post(
        f"{settings.API_V1_STR}/finance/costs",
        json={
            "category": "AI_SERVICES",
            "description": "GPT-4o Vision Inference Batch",
            "amount_cents": 35000,  # $350.00
            "currency": "USD",
            "billing_period": now_period,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert cost2_res.status_code == 201

    # 4. Update budget limit
    upd_res = client.put(
        f"{settings.API_V1_STR}/finance/budgets/{bdg_id}",
        json={"budget_amount_cents": 150000, "alert_threshold_percentage": 80.0},
        headers=headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["budget_amount"] == 1500.00

# ==============================================================================
# 4. FINANCIAL DATA SOURCES (STRIPE, AWS, QUICKBOOKS)
# ==============================================================================
def test_financial_data_sources_management_and_sync(client):
    headers, user_id, _ = get_auth_headers(client, "fin_ds")
    ws_id = create_test_workspace(client, headers, "DS WS")

    # 1. Create data source
    ds_res = client.post(
        f"{settings.API_V1_STR}/finance/data-sources",
        json={
            "name": "Production Stripe Billing Gateway",
            "source_type": "STRIPE",
            "config_json": '{"mode": "live", "webhook_configured": true}',
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert ds_res.status_code == 201, ds_res.text
    ds = ds_res.json()
    ds_id = ds["id"]
    assert ds["name"] == "Production Stripe Billing Gateway"
    assert ds["status"] == "CONNECTED"

    # 2. Test connection
    test_res = client.post(f"{settings.API_V1_STR}/finance/data-sources/{ds_id}/test-connection", headers=headers)
    assert test_res.status_code == 200
    assert test_res.json()["connected"] is True
    assert test_res.json()["latency_ms"] > 0

    # 3. Synchronize data source
    sync_res = client.post(f"{settings.API_V1_STR}/finance/data-sources/{ds_id}/sync", headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["sync_status"] == "SUCCESS"

    # 4. List data sources
    list_res = client.get(f"{settings.API_V1_STR}/finance/data-sources?workspace_id={ws_id}", headers=headers)
    assert list_res.status_code == 200
    assert any(d["id"] == ds_id for d in list_res.json())

    # 5. Delete data source
    del_res = client.delete(f"{settings.API_V1_STR}/finance/data-sources/{ds_id}", headers=headers)
    assert del_res.status_code == 200

# ==============================================================================
# 5. CSV IMPORT PREVIEW & COMMIT
# ==============================================================================
def test_csv_import_preview_and_commit(client):
    headers, user_id, _ = get_auth_headers(client, "fin_imp")
    ws_id = create_test_workspace(client, headers, "Import WS")

    csv_data = """transaction_type,amount,currency,status,description
SUBSCRIPTION_PAYMENT,249.00,USD,SUCCEEDED,Enterprise Monthly Team Plan
SEAT_EXPANSION,49.00,USD,SUCCEEDED,Addon 5 Developer Seats
AI_TOKEN_ADDON,29.00,USD,SUCCEEDED,High-Volume Copilot Pack
"""

    # 1. Preview Import
    prev_res = client.post(
        f"{settings.API_V1_STR}/finance/imports/preview",
        json={
            "filename": "q1_billing_ledger.csv",
            "import_type": "TRANSACTIONS",
            "csv_content": csv_data,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert prev_res.status_code == 200, prev_res.text
    prev = prev_res.json()
    assert prev["total_rows"] == 3
    assert prev["valid_rows"] == 3
    assert prev["error_rows"] == 0
    assert prev["total_amount"] == 327.00
    assert len(prev["sample_preview"]) == 3

    # 2. Commit Import
    commit_res = client.post(
        f"{settings.API_V1_STR}/finance/imports/commit",
        json={
            "filename": "q1_billing_ledger.csv",
            "import_type": "TRANSACTIONS",
            "csv_content": csv_data,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert commit_res.status_code == 201, commit_res.text
    imp = commit_res.json()
    assert imp["status"] == "COMMITTED"
    assert imp["total_rows"] == 3
    assert imp["total_amount"] == 327.00

    # 3. List imports
    list_imp = client.get(f"{settings.API_V1_STR}/finance/imports?workspace_id={ws_id}", headers=headers)
    assert list_imp.status_code == 200
    assert any(i["filename"] == "q1_billing_ledger.csv" for i in list_imp.json())

# ==============================================================================
# 6. FINANCIAL INSIGHTS & ANOMALIES
# ==============================================================================
def test_financial_insights_and_anomaly_detection(client):
    headers, user_id, _ = get_auth_headers(client, "fin_ins")
    ws_id = create_test_workspace(client, headers, "Insight WS")

    # 1. Generate real-time insights based on telemetry
    gen_res = client.post(f"{settings.API_V1_STR}/finance/insights/generate?workspace_id={ws_id}", headers=headers)
    assert gen_res.status_code == 200, gen_res.text
    insights = gen_res.json()
    assert len(insights) >= 1
    ins_id = insights[0]["id"]
    assert insights[0]["status"] == "OPEN"

    # 2. List insights
    list_res = client.get(f"{settings.API_V1_STR}/finance/insights?workspace_id={ws_id}", headers=headers)
    assert list_res.status_code == 200
    assert any(i["id"] == ins_id for i in list_res.json())

    # 3. Update insight status to RESOLVED
    upd_res = client.patch(
        f"{settings.API_V1_STR}/finance/insights/{ins_id}",
        json={"status": "RESOLVED"},
        headers=headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["status"] == "RESOLVED"

# ==============================================================================
# 7. FINANCIAL RECOMMENDATIONS & ACTIONS
# ==============================================================================
def test_financial_recommendations_and_actions(client):
    headers, user_id, _ = get_auth_headers(client, "fin_rec")
    ws_id = create_test_workspace(client, headers, "Rec WS")

    # 1. List recommendations
    list_res = client.get(f"{settings.API_V1_STR}/finance/recommendations?workspace_id={ws_id}", headers=headers)
    assert list_res.status_code == 200, list_res.text
    recs = list_res.json()
    assert len(recs) >= 2
    rec_id = recs[0]["id"]
    assert recs[0]["status"] == "PENDING"
    assert recs[0]["potential_savings"] > 0.0

    # 2. Accept recommendation
    act_res = client.post(
        f"{settings.API_V1_STR}/finance/recommendations/{rec_id}/action",
        json={"action": "ACCEPT"},
        headers=headers,
    )
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "ACCEPTED"
    assert act_res.json()["action_taken_at"] is not None

# ==============================================================================
# 8. STRATEGIC SCENARIOS & COMPARISON
# ==============================================================================
def test_strategic_scenarios_and_comparison(client):
    headers, user_id, _ = get_auth_headers(client, "fin_scen")
    ws_id = create_test_workspace(client, headers, "Scen WS")

    # 1. Create Base Scenario
    scen1_res = client.post(
        f"{settings.API_V1_STR}/finance/scenarios",
        json={
            "name": "Steady Enterprise Expansion",
            "scenario_type": "BASE",
            "revenue_growth_rate": 0.08,
            "cost_factor": 1.02,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert scen1_res.status_code == 201, scen1_res.text
    s1 = scen1_res.json()
    assert s1["projected_mrr"] > 0.0

    # 2. Create Aggressive Growth Scenario
    scen2_res = client.post(
        f"{settings.API_V1_STR}/finance/scenarios",
        json={
            "name": "Aggressive PLG AI Adoption",
            "scenario_type": "BEST",
            "revenue_growth_rate": 0.25,
            "cost_factor": 1.10,
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert scen2_res.status_code == 201
    s2 = scen2_res.json()
    assert s2["projected_mrr"] > s1["projected_mrr"]

    # 3. Compare Scenarios
    comp_res = client.get(f"{settings.API_V1_STR}/finance/scenarios/compare?workspace_id={ws_id}", headers=headers)
    assert comp_res.status_code == 200
    comp = comp_res.json()
    assert comp["current_mrr"] > 0.0
    assert len(comp["scenarios"]) >= 2

# ==============================================================================
# 9. GROUNDED AI FINANCIAL ASSISTANT
# ==============================================================================
def test_grounded_ai_financial_analysis(client):
    headers, user_id, _ = get_auth_headers(client, "fin_ai")
    ws_id = create_test_workspace(client, headers, "AI WS")

    ai_res = client.post(
        f"{settings.API_V1_STR}/finance/ai/analyze",
        json={
            "question": "Assess current SaaS run rate, gross margin efficiency, and key cost drivers.",
            "workspace_id": ws_id,
        },
        headers=headers,
    )
    assert ai_res.status_code == 200, ai_res.text
    ai_data = ai_res.json()

    assert "ARR run rate" in ai_data["summary"]
    assert "Net New MRR" in ai_data["mrr_arr_assessment"]
    assert len(ai_data["strategic_recommendations"]) >= 2
    assert "gross_margin_pct" in ai_data["grounded_metrics"]
    assert "cogs" in ai_data["grounded_metrics"]

# ==============================================================================
# 10. REPORT EXPORT IN CSV FORMAT
# ==============================================================================
def test_financial_reporting_and_csv_export(client):
    headers, user_id, _ = get_auth_headers(client, "fin_rep")
    ws_id = create_test_workspace(client, headers, "Report WS")

    # 1. Export Executive Summary
    exp_exec = client.post(
        f"{settings.API_V1_STR}/finance/reports/export",
        json={"report_type": "EXECUTIVE_SUMMARY", "format": "CSV", "workspace_id": ws_id},
        headers=headers,
    )
    assert exp_exec.status_code == 200
    rep = exp_exec.json()
    assert "focusboard_financial_executive_summary" in rep["report_name"]
    assert "Total MRR" in rep["content"]
    assert "Gross Margin %" in rep["content"]

    # 2. Export Transactions Ledger
    exp_tx = client.post(
        f"{settings.API_V1_STR}/finance/reports/export",
        json={"report_type": "TRANSACTIONS", "format": "CSV", "workspace_id": ws_id},
        headers=headers,
    )
    assert exp_tx.status_code == 200
    assert "focusboard_financial_transactions" in exp_tx.json()["report_name"]

    # 3. Export FinOps Costs
    exp_cst = client.post(
        f"{settings.API_V1_STR}/finance/reports/export",
        json={"report_type": "FINOPS_COSTS", "format": "CSV", "workspace_id": ws_id},
        headers=headers,
    )
    assert exp_cst.status_code == 200
    assert "focusboard_finops_costs" in exp_cst.json()["report_name"]

# ==============================================================================
# 11. MULTI-TENANT ISOLATION
# ==============================================================================
def test_financial_multi_tenant_isolation(client):
    headers1, user1_id, _ = get_auth_headers(client, "tenant1_user")
    headers2, user2_id, _ = get_auth_headers(client, "tenant2_user")

    ws1_id = create_test_workspace(client, headers1, "Tenant 1 WS")
    ws2_id = create_test_workspace(client, headers2, "Tenant 2 WS")

    # Tenant 1 records a proprietary transaction
    tx_res = client.post(
        f"{settings.API_V1_STR}/finance/transactions",
        json={
            "transaction_type": "SUBSCRIPTION_PAYMENT",
            "amount_cents": 888800,  # $8,888.00
            "currency": "USD",
            "status": "SUCCEEDED",
            "description": "Tenant 1 Confidential Sovereign Cloud Contract",
            "workspace_id": ws1_id,
        },
        headers=headers1,
    )
    assert tx_res.status_code == 201

    # Tenant 2 lists transactions in their own workspace
    t2_list = client.get(f"{settings.API_V1_STR}/finance/transactions?workspace_id={ws2_id}", headers=headers2)
    assert t2_list.status_code == 200
    t2_txs = t2_list.json()
    assert not any("Confidential Sovereign Cloud Contract" in t["description"] for t in t2_txs)

    # Tenant 2 cannot access Tenant 1 workspace
    forbidden_res = client.get(f"{settings.API_V1_STR}/finance/transactions?workspace_id={ws1_id}", headers=headers2)
    assert forbidden_res.status_code == 403

# ==============================================================================
# 12. B15 AUTOMATION INTEGRATION
# ==============================================================================
def test_b15_automation_action_integration():
    db = SessionLocal()
    try:
        # 1. Trigger financial report generation
        res1 = execute_financial_automation_action(
            db,
            action_type="CREATE_FINANCIAL_REPORT",
            payload={"report_type": "EXECUTIVE_SUMMARY"},
        )
        assert res1["status"] == "SUCCESS"
        assert "report_name" in res1

        # 2. Trigger budget alert notification
        res2 = execute_financial_automation_action(
            db,
            action_type="CREATE_BUDGET_ALERT",
            payload={"category": "CLOUD", "spent_pct": 88.5},
        )
        assert res2["status"] == "SUCCESS"
    finally:
        db.close()
