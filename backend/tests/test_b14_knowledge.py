import pytest
import io
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b14_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "KnowledgePassword123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"Knowledge User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

def create_test_workspace(client, headers, name="Knowledge Workspace"):
    res = client.post(
        f"{settings.API_V1_STR}/workspaces",
        json={"name": f"{name} {uuid.uuid4().hex[:6]}", "description": "Workspace for B14 testing"},
        headers=headers,
    )
    assert res.status_code in [200, 201], res.text
    return res.json()["id"]

# -------------------------------------------------------------
# 1. Knowledge Collections Lifecycle
# -------------------------------------------------------------
def test_knowledge_collections_lifecycle(client):
    headers, user_id, _ = get_auth_headers(client, "col_user")
    ws_id = create_test_workspace(client, headers, "Col WS")

    # 1. Create a collection
    create_res = client.post(
        f"{settings.API_V1_STR}/knowledge/collections",
        json={
            "workspace_id": ws_id,
            "name": "Platform RFCs and ADRs",
            "description": "Architectural specifications for cloud platform components.",
            "icon": "Layers",
            "is_cross_workspace": False,
        },
        headers=headers,
    )
    assert create_res.status_code == 201, create_res.text
    col = create_res.json()
    assert col["name"] == "Platform RFCs and ADRs"
    assert col["workspace_id"] == ws_id

    # 2. List collections for workspace
    list_res = client.get(
        f"{settings.API_V1_STR}/knowledge/collections?workspace_id={ws_id}",
        headers=headers,
    )
    assert list_res.status_code == 200
    cols = list_res.json()
    assert any(c["id"] == col["id"] for c in cols)

# -------------------------------------------------------------
# 2. Knowledge Document CRUD & Versioning
# -------------------------------------------------------------
def test_knowledge_document_crud_and_versioning(client):
    headers, user_id, _ = get_auth_headers(client, "doc_user")
    ws_id = create_test_workspace(client, headers, "Doc WS")

    # 1. Create document
    doc_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents",
        json={
            "workspace_id": ws_id,
            "title": "API Rate Limiting Standard",
            "slug": f"api-rate-limiting-{uuid.uuid4().hex[:6]}",
            "content": "# Rate Limiting\nFocusBoard enforces a token bucket algorithm at 120 req/minute per user.",
            "document_type": "SPECIFICATION",
            "category": "Architecture",
            "visibility": "INTERNAL",
            "status": "VERIFIED",
            "version": "1.0",
            "quality_score": 95.0,
        },
        headers=headers,
    )
    assert doc_res.status_code == 201, doc_res.text
    doc = doc_res.json()
    doc_id = doc["id"]
    assert doc["version"] == "1.0"
    assert doc["versions_count"] == 1

    # 2. Get document by id
    get_res = client.get(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "API Rate Limiting Standard"

    # 3. Update document with content change (triggers new version)
    update_res = client.patch(
        f"{settings.API_V1_STR}/knowledge/documents/{doc_id}",
        json={
            "content": "# Rate Limiting v2\nUpdated quota to 300 req/minute for Enterprise accounts.",
            "change_summary": "Raised rate limit for enterprise tier",
        },
        headers=headers,
    )
    assert update_res.status_code == 200, update_res.text
    updated = update_res.json()
    assert updated["version"] == "1.1"
    assert updated["versions_count"] == 2

    # 4. Get versions history
    ver_res = client.get(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/versions", headers=headers)
    assert ver_res.status_code == 200
    versions = ver_res.json()
    assert len(versions) == 2
    assert any(v["version"] == "1.1" for v in versions)

    # 5. Delete document
    del_res = client.delete(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirm 404
    get_del = client.get(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}", headers=headers)
    assert get_del.status_code == 404

# -------------------------------------------------------------
# 3. Knowledge Document Upload & Text Extraction
# -------------------------------------------------------------
def test_knowledge_document_upload_and_extraction(client):
    headers, user_id, _ = get_auth_headers(client, "upload_user")
    ws_id = create_test_workspace(client, headers, "Upload WS")

    content = (
        "# Distributed Cache Architecture\n\n"
        "## Summary\n"
        "FocusBoard utilizes a distributed multi-layer cache combining Redis and in-memory LRU buffers.\n\n"
        "## Invalidation Strategy\n"
        "Write-through cache invalidation happens via tenant event broadcast bus.\n"
    )
    file_bytes = content.encode("utf-8")

    upload_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents/upload",
        files={"file": ("cache_architecture.md", io.BytesIO(file_bytes), "text/markdown")},
        data={
            "workspace_id": ws_id,
            "category": "Engineering",
            "document_type": "SPECIFICATION",
            "visibility": "INTERNAL",
        },
        headers=headers,
    )
    assert upload_res.status_code == 201, upload_res.text
    data = upload_res.json()
    assert data["chunks_count"] >= 1
    assert data["extracted_characters"] == len(content)

    doc = data["document"]
    assert doc["original_filename"] == "cache_architecture.md"
    assert doc["file_size"] == len(file_bytes)
    assert doc["processing_status"] == "COMPLETED"
    assert doc["workspace_id"] == ws_id

# -------------------------------------------------------------
# 4. Document Chunking & Metadata Verification
# -------------------------------------------------------------
def test_document_chunking_and_metadata(client):
    headers, user_id, _ = get_auth_headers(client, "chunk_user")
    ws_id = create_test_workspace(client, headers, "Chunk WS")

    # Create document with multiple markdown sections
    doc_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents",
        json={
            "workspace_id": ws_id,
            "title": "Incident Management Runbook",
            "slug": f"incident-runbook-{uuid.uuid4().hex[:6]}",
            "content": (
                "# Incident Triage\n"
                "Verify impact radius and identify affected customer tier.\n\n"
                "## Mitigation Procedures\n"
                "Follow standard roll-back pipeline or redirect traffic to failover standby.\n\n"
                "## Postmortem Timeline\n"
                "Publish root-cause analysis within 48 hours of resolution."
            ),
            "document_type": "RUNBOOK",
            "category": "Operations",
            "visibility": "INTERNAL",
            "status": "VERIFIED",
        },
        headers=headers,
    )
    assert doc_res.status_code == 201, doc_res.text
    doc_id = doc_res.json()["id"]

    # Retrieve chunks
    chunks_res = client.get(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == 200, chunks_res.text
    chunks = chunks_res.json()
    assert len(chunks) >= 1

    first_chunk = chunks[0]
    assert first_chunk["document_id"] == doc_id
    assert first_chunk["chunk_index"] == 0
    assert first_chunk["token_count"] > 0
    assert first_chunk["heading"] is not None

# -------------------------------------------------------------
# 5. Full-Text & Keyword Search
# -------------------------------------------------------------
def test_document_keyword_fulltext_search(client):
    headers, user_id, _ = get_auth_headers(client, "search_user")

    # Seed data has "WebSocket Heartbeat Timeout Spike"
    search_res = client.post(
        f"{settings.API_V1_STR}/knowledge/search",
        json={"query": "WebSocket Heartbeat", "limit": 5},
        headers=headers,
    )
    assert search_res.status_code == 200, search_res.text
    data = search_res.json()
    assert data["total_hits"] >= 1
    top_hit = data["hits"][0]
    assert "websocket" in top_hit["title"].lower() or "websocket" in top_hit["snippet"].lower()
    assert top_hit["relevance_score"] > 0.0

# -------------------------------------------------------------
# 6. Semantic Vector Search & Ranking
# -------------------------------------------------------------
def test_semantic_vector_search_and_ranking(client):
    headers, user_id, _ = get_auth_headers(client, "semantic_user")

    # Natural language query matching ADR-042 or database failover
    search_res = client.post(
        f"{settings.API_V1_STR}/knowledge/search",
        json={"query": "procedure to handle primary database failure and replica promotion", "limit": 5},
        headers=headers,
    )
    assert search_res.status_code == 200, search_res.text
    data = search_res.json()
    assert data["total_hits"] >= 1
    hit_titles = [h["title"] for h in data["hits"]]
    assert any("Failover" in t or "Runbook" in t or "Search" in t for t in hit_titles)

# -------------------------------------------------------------
# 7. RAG Query Execution with Grounded Citations
# -------------------------------------------------------------
def test_rag_query_with_grounded_citations(client):
    headers, user_id, _ = get_auth_headers(client, "rag_user")

    query_res = client.post(
        f"{settings.API_V1_STR}/knowledge/assistant/query",
        json={"question": "What is the trigger threshold for database failover?"},
        headers=headers,
    )
    assert query_res.status_code == 200, query_res.text
    data = query_res.json()
    assert len(data["answer"]) > 10
    assert data["confidence"] > 0.0
    assert len(data["citations"]) >= 1

    citation = data["citations"][0]
    assert "source_id" in citation
    assert "source_title" in citation
    assert "snippet" in citation
    assert citation["relevance"] > 0.0

# -------------------------------------------------------------
# 8. Document Linking to Tasks and Projects
# -------------------------------------------------------------
def test_document_linking_to_tasks_and_projects(client):
    headers, user_id, _ = get_auth_headers(client, "link_user")
    ws_id = create_test_workspace(client, headers, "Link WS")

    # 1. Create document
    doc_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents",
        json={
            "workspace_id": ws_id,
            "title": "OAuth SSO Specification",
            "slug": f"oauth-sso-{uuid.uuid4().hex[:6]}",
            "content": "Detailed OAuth 2.0 and OIDC identity flow implementation details.",
            "document_type": "SPECIFICATION",
            "category": "Security",
            "visibility": "INTERNAL",
        },
        headers=headers,
    )
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    # 2. Link to a Task
    task_link_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/links",
        json={"entity_type": "TASK", "entity_id": "task_999"},
        headers=headers,
    )
    assert task_link_res.status_code == 201, task_link_res.text
    task_link = task_link_res.json()
    assert task_link["entity_type"] == "TASK"
    assert task_link["entity_id"] == "task_999"

    # 3. Link to a Project
    proj_link_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/links",
        json={"entity_type": "PROJECT", "entity_id": "proj_888"},
        headers=headers,
    )
    assert proj_link_res.status_code == 201
    proj_link = proj_link_res.json()
    assert proj_link["entity_type"] == "PROJECT"

    # 4. List document links
    links_res = client.get(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/links", headers=headers)
    assert links_res.status_code == 200
    links = links_res.json()
    assert len(links) == 2

    # 5. Unlink task
    unlink_res = client.delete(
        f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/links/{task_link['id']}",
        headers=headers,
    )
    assert unlink_res.status_code == 204

    # Verify only 1 link remaining
    links_res2 = client.get(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/links", headers=headers)
    assert len(links_res2.json()) == 1

# -------------------------------------------------------------
# 9. Document Summarization
# -------------------------------------------------------------
def test_document_summarization(client):
    headers, user_id, _ = get_auth_headers(client, "summary_user")
    ws_id = create_test_workspace(client, headers, "Summary WS")

    doc_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents",
        json={
            "workspace_id": ws_id,
            "title": "Data Retention Policy",
            "slug": f"data-retention-policy-{uuid.uuid4().hex[:6]}",
            "content": (
                "The organization requires all inactive audit logs to be archived after 365 days. "
                "The security team decided to encrypt all cold storage volumes using AES-256 GCM. "
                "Primary operational databases retain active customer records for the duration of the subscription."
            ),
            "document_type": "DECISION_RECORD",
            "category": "Compliance",
            "visibility": "INTERNAL",
        },
        headers=headers,
    )
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    sum_res = client.get(f"{settings.API_V1_STR}/knowledge/documents/{doc_id}/summarize", headers=headers)
    assert sum_res.status_code == 200, sum_res.text
    data = sum_res.json()
    assert data["document_id"] == doc_id
    assert len(data["summary"]) > 10
    assert isinstance(data["key_points"], list)

# -------------------------------------------------------------
# 10. Multi-Tenant Isolation & Security
# -------------------------------------------------------------
def test_knowledge_multi_tenant_isolation_and_security(client):
    headers_a, user_a, _ = get_auth_headers(client, "tenant_a")
    headers_b, user_b, _ = get_auth_headers(client, "tenant_b")

    ws_a = create_test_workspace(client, headers_a, "Tenant A WS")
    ws_b = create_test_workspace(client, headers_b, "Tenant B WS")

    # Tenant A creates a CONFIDENTIAL document
    doc_a_res = client.post(
        f"{settings.API_V1_STR}/knowledge/documents",
        json={
            "workspace_id": ws_a,
            "title": "Tenant A Secret Patent Strategy",
            "slug": f"tenant-a-secret-patent-{uuid.uuid4().hex[:6]}",
            "content": "Strictly confidential proprietary quantum algorithmic trading formulas.",
            "document_type": "RESEARCH",
            "category": "Executive",
            "visibility": "CONFIDENTIAL",
            "status": "DRAFT",
        },
        headers=headers_a,
    )
    assert doc_a_res.status_code == 201
    doc_a_id = doc_a_res.json()["id"]

    # Tenant B searches within Tenant B workspace for "quantum algorithmic trading formulas"
    search_b = client.post(
        f"{settings.API_V1_STR}/knowledge/search",
        json={"query": "quantum algorithmic trading formulas", "workspace_id": ws_b},
        headers=headers_b,
    )
    assert search_b.status_code == 200
    hits_b = search_b.json()["hits"]
    # Tenant A's confidential document MUST NOT appear in Tenant B's results
    assert not any(h["document_id"] == doc_a_id for h in hits_b)

    # Unauthenticated request to /knowledge/overview must be rejected with 401
    unauth_overview = client.get(f"{settings.API_V1_STR}/knowledge/overview")
    assert unauth_overview.status_code == 401
