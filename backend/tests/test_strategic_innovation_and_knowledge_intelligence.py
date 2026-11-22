import os
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.support import ProductRoadmapItem
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def auth_headers(db_session: Session):
    unique_email = f"exec_strat_{uuid.uuid4().hex[:8]}@focusboard.enterprise"
    user = User(
        email=unique_email,
        name="Chief Strategy & Knowledge Officer",
        hashed_password="hashed_pw_fixture",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}, user

# ==============================================================================
# PHASE 36: STRATEGIC INTELLIGENCE TESTS
# ==============================================================================

def test_strategic_overview(auth_headers):
    headers, _ = auth_headers
    resp = client.get("/api/v1/strategy/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_goals_count"] >= 1
    assert data["active_plans_count"] >= 1
    assert data["tracked_competitors_count"] >= 1
    assert data["open_opportunities_count"] >= 1
    assert "swot_summary" in data
    assert len(data["top_opportunities"]) > 0
    assert len(data["ai_recommendations"]) > 0
    first_rec = data["ai_recommendations"][0]
    assert first_rec["theme"] != ""
    assert first_rec["grounded_evidence"] != ""

def test_strategic_opportunity_rice_prioritization(auth_headers):
    headers, _ = auth_headers
    # Test RICE formula: (Reach * Impact * Confidence) / Effort
    # Reach = 5000, Impact = 3 (SUBSTANTIAL), Confidence = 0.8, Effort = 4
    # Score = (5000 * 3.0 * 0.8) / 4.0 = 12000 / 4.0 = 3000.0
    payload = {
        "title": "Automated ERP Integration Suite",
        "description": "Bi-directional sync with SAP and Oracle NetSuite.",
        "customer_segment": "Enterprise B2B",
        "rice_reach": 5000.0,
        "rice_impact": 3.0,
        "rice_confidence": 0.8,
        "rice_effort": 4.0,
        "status": "PROPOSED",
    }
    resp = client.post("/api/v1/strategy/opportunities", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["title"] == "Automated ERP Integration Suite"
    assert data["rice_score"] == pytest.approx(3000.0, rel=1e-2)

def test_strategic_plans_and_goals(auth_headers):
    headers, _ = auth_headers
    plan_payload = {
        "title": "FY2027 Global Enterprise Dominance",
        "vision": "The leading multi-tenant AI-augmented productivity suite for Global 2000.",
        "mission": "Empower modern agile engineering organizations with continuous flow.",
        "time_horizon": "3_YEAR",
        "status": "ACTIVE",
    }
    resp = client.post("/api/v1/strategy/plans", json=plan_payload, headers=headers)
    assert resp.status_code == 201
    plan_data = resp.json()
    plan_id = plan_data["id"]

    goal_payload = {
        "plan_id": plan_id,
        "title": "Achieve $25M ARR with 130% NRR",
        "description": "Expand multi-seat enterprise contracts and expansion upsell.",
        "category": "REVENUE",
        "target_metric": "ARR",
        "target_value": 25000000.0,
        "baseline_value": 8500000.0,
        "current_value": 14200000.0,
        "unit": "USD",
        "status": "ACTIVE",
    }
    resp_goal = client.post("/api/v1/strategy/goals", json=goal_payload, headers=headers)
    assert resp_goal.status_code == 201
    goal_data = resp_goal.json()

    assert goal_data["progress_percentage"] > 30.0

def test_swot_and_market_sizing(auth_headers):
    headers, _ = auth_headers
    swot_payload = {
        "swot_type": "OPPORTUNITY",
        "title": "Legacy Project Management Software Bloat",
        "description": "Enterprise buyers reporting 45% tool fatigue with incumbent suites.",
        "impact": "HIGH",
        "evidence_text": "Gartner Q3 report on tool consolidation.",
    }
    resp_swot = client.post("/api/v1/strategy/swot", json=swot_payload, headers=headers)
    assert resp_swot.status_code == 201

    sizing_payload = {
        "market_name": "Mid-Market & Enterprise Agile Teams",
        "methodology": "BOTTOM_UP",
        "tam_cents": 4500000000000,
        "sam_cents": 850000000000,
        "som_cents": 45000000000,
        "currency": "USD",
        "assumptions_json": '{"accounts": 15000, "acv": 30000}',
        "confidence_score": 0.88,
    }
    resp_size = client.post("/api/v1/strategy/market-sizing", json=sizing_payload, headers=headers)
    assert resp_size.status_code == 201
    assert resp_size.json()["som_cents"] == 45000000000

# ==============================================================================
# PHASE 37: INNOVATION LAB & R&D TESTS
# ==============================================================================

def test_innovation_overview(auth_headers):
    headers, _ = auth_headers
    resp = client.get("/api/v1/innovation/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_ideas_count"] >= 3
    assert data["active_experiments_count"] >= 1
    assert data["experiment_success_rate"] >= 0.0
    assert "pipeline_stage_distribution" in data
    assert len(data["recent_ideas"]) > 0

def test_innovation_idea_lifecycle_and_promotion(auth_headers, db_session: Session):
    headers, user = auth_headers

    # 1. Capture Idea
    idea_payload = {
        "title": "Quantum-Resilient Offline Vault Sync",
        "problem_statement": "Future cryptographic attacks may compromise synchronized offline caches.",
        "proposed_solution": "NIST-standardized Kyber post-quantum envelope encryption on SQLite blobs.",
        "category": "TECHNICAL",
        "stage": "HYPOTHESIS",
        "target_audience": "Government & Defense Contractors",
        "estimated_effort": "HIGH",
        "strategic_value": "TRANSFORMATIVE",
    }
    resp_idea = client.post("/api/v1/innovation/ideas", json=idea_payload, headers=headers)
    assert resp_idea.status_code == 201
    idea = resp_idea.json()
    idea_id = idea["id"]

    # 2. Add Hypothesis
    hypo_payload = {
        "idea_id": idea_id,
        "statement": "We believe Kyber encryption will add less than 15ms overhead to local database reads.",
        "measurable_criterion": "<= 15ms latency overhead in benchmark suites.",
        "confidence_score": 0.85,
        "status": "UNTESTED",
    }
    resp_hypo = client.post("/api/v1/innovation/hypotheses", json=hypo_payload, headers=headers)
    assert resp_hypo.status_code == 201
    hypo_id = resp_hypo.json()["id"]

    # 3. Create Experiment
    exp_payload = {
        "idea_id": idea_id,
        "hypothesis_id": hypo_id,
        "name": "Post-Quantum Cryptographic Benchmark on WASM",
        "experiment_type": "TECHNICAL_POC",
        "methodology": "Simulated 10,000 encrypted SQLite read/write transactions inside WebWorker.",
        "sample_size": 10000,
        "budget_spent": 1500.0,
        "status": "RUNNING",
    }
    resp_exp = client.post("/api/v1/innovation/experiments", json=exp_payload, headers=headers)
    assert resp_exp.status_code == 201
    exp_id = resp_exp.json()["id"]

    # 4. Attach Experiment Result
    res_payload = {
        "quantitative_summary": "Measured 8.4ms average latency overhead, comfortably below 15ms threshold.",
        "qualitative_feedback": "Engineering team validated Rust-compiled WASM module without thread locks.",
        "success_criteria_met": True,
        "lessons_learned": "Pre-computing keypairs eliminates handshake penalty entirely.",
    }
    resp_res = client.post(f"/api/v1/innovation/experiments/{exp_id}/results", json=res_payload, headers=headers)
    assert resp_res.status_code == 201
    assert resp_res.json()["success_criteria_met"] is True

    # 5. Add Prototype
    proto_payload = {
        "idea_id": idea_id,
        "name": "Kyber WASM Sandbox Prototype",
        "prototype_type": "TECHNICAL_POC",
        "demo_url": "https://sandbox.focusboard.internal/kyber",
        "tech_stack": "Rust + WebAssembly + SQLite",
        "status": "APPROVED",
    }
    resp_proto = client.post("/api/v1/innovation/prototypes", json=proto_payload, headers=headers)
    assert resp_proto.status_code == 201

    # 6. Add Validation
    val_payload = {
        "idea_id": idea_id,
        "dimension": "TECHNICAL",
        "criteria": "Passed cryptographic validation and zero regression on query throughput.",
        "status": "PASSED",
        "confidence": 0.98,
        "notes": "Verified by Cryptographic Systems Architect.",
    }
    resp_val = client.post("/api/v1/innovation/validations", json=val_payload, headers=headers)
    assert resp_val.status_code == 201

    # 7. Promote Idea to Product Roadmap
    promote_payload = {
        "roadmap_category": "Security & Core Architecture",
        "target_status": "PLANNED",
    }
    resp_promote = client.post(f"/api/v1/innovation/ideas/{idea_id}/promote-to-roadmap", json=promote_payload, headers=headers)
    assert resp_promote.status_code == 200
    promote_data = resp_promote.json()

    assert promote_data["idea_id"] == idea_id
    assert promote_data["roadmap_item_id"] > 0

    # Verify Idea stage is updated to ROADMAP
    updated_idea_resp = client.get(f"/api/v1/innovation/ideas/{idea_id}", headers=headers)
    assert updated_idea_resp.status_code == 200
    assert updated_idea_resp.json()["stage"] == "ROADMAP"
    assert updated_idea_resp.json()["roadmap_item_id"] == promote_data["roadmap_item_id"]

    # Verify ProductRoadmapItem exists in DB
    roadmap_item = db_session.query(ProductRoadmapItem).filter(ProductRoadmapItem.id == promote_data["roadmap_item_id"]).first()
    assert roadmap_item is not None
    assert roadmap_item.title == "Quantum-Resilient Offline Vault Sync"

# ==============================================================================
# PHASE 38: KNOWLEDGE INTELLIGENCE TESTS
# ==============================================================================

def test_knowledge_overview(auth_headers):
    headers, _ = auth_headers
    resp = client.get("/api/v1/knowledge/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_documents_count"] >= 3
    assert data["verified_documents_count"] >= 2
    assert data["collections_count"] >= 3
    assert data["graph_entities_count"] >= 4
    assert data["graph_relationships_count"] >= 3
    assert data["average_quality_score"] > 80.0
    assert len(data["recent_documents"]) > 0

def test_knowledge_document_versioning(auth_headers):
    headers, _ = auth_headers
    # 1. Create Document
    doc_payload = {
        "title": "ADR-099: Distributed Task Execution Queue",
        "slug": f"adr-099-distributed-queue-{uuid.uuid4().hex[:6]}",
        "content": "Initial proposal to replace background Celery workers with asyncio event loop workers.",
        "document_type": "DECISION_RECORD",
        "category": "Architecture",
        "visibility": "INTERNAL",
        "status": "VERIFIED",
        "version": "1.0",
        "quality_score": 95.0,
    }
    resp = client.post("/api/v1/knowledge/documents", json=doc_payload, headers=headers)
    assert resp.status_code == 201
    doc_id = resp.json()["id"]

    # 2. Update Document Content (should increment version to 1.1 and add a version record)
    update_payload = {
        "content": "Revised decision: Adopt hybrid Redis pub/sub queue with asyncio workers for 10x throughput.",
        "change_summary": "Upgraded worker benchmark specifications.",
    }
    resp_upd = client.patch(f"/api/v1/knowledge/documents/{doc_id}", json=update_payload, headers=headers)
    assert resp_upd.status_code == 200
    assert resp_upd.json()["version"] == "1.1"

    # 3. Verify Document Versions List
    resp_ver = client.get(f"/api/v1/knowledge/documents/{doc_id}/versions", headers=headers)
    assert resp_ver.status_code == 200
    versions = resp_ver.json()
    assert len(versions) >= 2
    version_numbers = [v["version"] for v in versions]
    assert "1.0" in version_numbers
    assert "1.1" in version_numbers

def test_knowledge_graph_explorer(auth_headers):
    headers, _ = auth_headers
    resp = client.get("/api/v1/knowledge/graph", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 4
    assert len(data["edges"]) >= 3

    node_labels = [n["label"] for n in data["nodes"]]
    assert any("Hybrid Search Engine" in label for label in node_labels)

def test_semantic_search_and_ai_citations(auth_headers):
    headers, _ = auth_headers

    # 1. Semantic Search
    search_payload = {
        "query": "hybrid semantic search architecture",
        "limit": 5,
    }
    resp_search = client.post("/api/v1/knowledge/search", json=search_payload, headers=headers)
    assert resp_search.status_code == 200
    search_data = resp_search.json()

    assert search_data["total_hits"] >= 1
    top_hit = search_data["hits"][0]
    assert "Search" in top_hit["title"] or "ADR" in top_hit["title"]
    assert top_hit["relevance_score"] > 0.0
    assert top_hit["snippet"] != ""

    # 2. AI Knowledge Assistant with verifiable citations
    ai_payload = {
        "question": "What is our decision regarding hybrid search and database replication?",
    }
    resp_ai = client.post("/api/v1/knowledge/assistant/query", json=ai_payload, headers=headers)
    assert resp_ai.status_code == 200
    ai_data = resp_ai.json()

    assert ai_data["confidence"] > 0.5
    assert len(ai_data["citations"]) > 0
    first_citation = ai_data["citations"][0]
    assert first_citation["source_id"] != ""
    assert first_citation["source_title"] != ""
    assert first_citation["snippet"] != ""
