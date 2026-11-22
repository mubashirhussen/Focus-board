import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b11_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "SearchSecurePass123!"
    reg_res = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"name": f"User {unique}", "email": email, "password": password},
    )
    assert reg_res.status_code in [200, 201], reg_res.text
    data = reg_res.json()
    token = data["access_token"]
    user_id = data.get("user", {}).get("id") or data.get("id")
    return {"Authorization": f"Bearer {token}"}, user_id, email

# --------------------------------------------------------------------------
# 1. Global Search Across Diverse Entity Types & Facets
# --------------------------------------------------------------------------
def test_global_search_across_entities(client):
    headers, user_id, email = get_auth_headers(client, "g_search")

    unique_key = uuid.uuid4().hex[:6]
    search_keyword = f"Quantum{unique_key}"

    # 1. Create a task with keyword
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": task_id,
        "title": f"Implement {search_keyword} Engine",
        "description": "High performance computing subroutines.",
        "status": "In Progress",
        "priority": "High",
        "category": "Engineering"
    }, headers=headers)

    # 2. Create a team with keyword
    client.post(f"{settings.API_V1_STR}/teams", json={
        "name": f"{search_keyword} Core Team",
        "description": "Dedicated research squad."
    }, headers=headers)

    # 3. Create a board with keyword
    client.post(f"{settings.API_V1_STR}/boards", json={
        "name": f"{search_keyword} Sprint Board",
        "description": "Kanban planning"
    }, headers=headers)

    # 4. Execute global search
    res = client.get(f"{settings.API_V1_STR}/search?q={search_keyword}", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total"] >= 3
    types_found = {item["type"] for item in data["results"]}
    assert "TASK" in types_found
    assert "TEAM" in types_found
    assert "BOARD" in types_found

    # Verify facets
    assert data["facets"]["by_type"]["TASK"] >= 1
    assert data["facets"]["by_type"]["TEAM"] >= 1
    assert data["facets"]["by_type"]["BOARD"] >= 1

# --------------------------------------------------------------------------
# 2. Query Validation, Multilingual Text & Safe Inputs
# --------------------------------------------------------------------------
def test_search_query_validation_and_multilingual(client):
    headers, user_id, email = get_auth_headers(client, "multiling")

    # Multilingual title
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": task_id,
        "title": "Planificación de Lanzamiento Global",
        "description": "Coordination internationale pour le déploiement.",
        "status": "Todo",
        "priority": "Medium",
        "category": "Marketing"
    }, headers=headers)

    # Search with accented characters
    res = client.get(f"{settings.API_V1_STR}/search?q=Planificación", headers=headers)
    assert res.status_code == 200
    results = res.json()["results"]
    assert any("Planificación" in r["title"] for r in results)

    # Empty query should return paginated recent resources without error
    res_empty = client.get(f"{settings.API_V1_STR}/search", headers=headers)
    assert res_empty.status_code == 200
    assert "results" in res_empty.json()

# --------------------------------------------------------------------------
# 3. Entity-Specific Searches (Tasks, Projects, Teams, Boards, Comments)
# --------------------------------------------------------------------------
def test_entity_specific_searches(client):
    headers, user_id, email = get_auth_headers(client, "spec_search")
    unique_tag = uuid.uuid4().hex[:6]

    # Create task
    t_id = f"task_{unique_tag}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": t_id,
        "title": f"Telemetry Pipeline {unique_tag}",
        "status": "Todo",
        "priority": "Low",
        "category": "DevOps"
    }, headers=headers)

    # Search tasks endpoint
    res_tasks = client.get(f"{settings.API_V1_STR}/search/tasks?q={unique_tag}&category=DevOps", headers=headers)
    assert res_tasks.status_code == 200
    t_items = res_tasks.json()
    assert len(t_items) >= 1
    assert t_items[0]["id"] == t_id

    # Create comment
    client.post(f"{settings.API_V1_STR}/comments", json={
        "entity_type": "TASK",
        "entity_id": t_id,
        "content": f"Critical bug identified in {unique_tag} ingestion stream.",
        "content_format": "markdown"
    }, headers=headers)

    # Search comments endpoint
    res_comms = client.get(f"{settings.API_V1_STR}/search/comments?q={unique_tag}", headers=headers)
    assert res_comms.status_code == 200
    c_items = res_comms.json()
    assert len(c_items) >= 1
    assert "Critical bug" in c_items[0]["description"]

# --------------------------------------------------------------------------
# 4. Member Search with Strict Tenant Boundaries
# --------------------------------------------------------------------------
def test_member_search_tenant_isolation(client):
    headers_org_owner, owner_id, owner_email = get_auth_headers(client, "org_owner")
    headers_org_member, member_id, member_email = get_auth_headers(client, "org_member")
    headers_outsider, outsider_id, outsider_email = get_auth_headers(client, "outsider")

    # Owner creates a team and invites member
    res_team = client.post(f"{settings.API_V1_STR}/teams", json={
        "name": f"Shared Team {uuid.uuid4().hex[:6]}",
        "description": "Cross-functional team"
    }, headers=headers_org_owner)
    team_id = res_team.json()["id"]

    # Member joins team
    inv_res = client.post(f"{settings.API_V1_STR}/teams/{team_id}/invitations", json={
        "email": member_email,
        "role": "MEMBER"
    }, headers=headers_org_owner)
    token = inv_res.json().get("token")
    if token:
        client.post(f"{settings.API_V1_STR}/teams/invitations/{token}/accept", headers=headers_org_member)

    # Owner searches for member -> should find member
    member_prefix = member_email.split("@")[0]
    res_search = client.get(f"{settings.API_V1_STR}/search/members?q={member_prefix}", headers=headers_org_owner)
    assert res_search.status_code == 200
    found_members = res_search.json()
    assert any(m["description"] == member_email for m in found_members)

    # Owner searches for outsider -> MUST NOT discover outsider
    outsider_prefix = outsider_email.split("@")[0]
    res_outsider = client.get(f"{settings.API_V1_STR}/search/members?q={outsider_prefix}", headers=headers_org_owner)
    assert res_outsider.status_code == 200
    assert not any(m["description"] == outsider_email for m in res_outsider.json())

# --------------------------------------------------------------------------
# 5. Search Suggestions & Autocomplete
# --------------------------------------------------------------------------
def test_search_suggestions_autocomplete(client):
    headers, user_id, email = get_auth_headers(client, "sugg_user")

    unique_prefix = f"Auto{uuid.uuid4().hex[:6]}"
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": f"{unique_prefix} Complete Feature Integration",
        "status": "Todo",
        "priority": "High",
        "category": "QA"
    }, headers=headers)

    res_sugg = client.get(f"{settings.API_V1_STR}/search/suggestions?q={unique_prefix}", headers=headers)
    assert res_sugg.status_code == 200
    data = res_sugg.json()
    assert data["query"] == unique_prefix
    assert len(data["suggestions"]) >= 1
    assert "TASK" in data["grouped"]
    assert any(unique_prefix in s["title"] for s in data["grouped"]["TASK"])

# --------------------------------------------------------------------------
# 6. Advanced Filter Engine (Complex Operators & Combinations)
# --------------------------------------------------------------------------
def test_advanced_filtering_engine(client):
    headers, user_id, email = get_auth_headers(client, "adv_filter")

    tag = uuid.uuid4().hex[:6]
    # Create 3 tasks with varying priorities and statuses
    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_1_{tag}",
        "title": f"Alpha Feature {tag}",
        "status": "Todo",
        "priority": "High",
        "category": "Backend"
    }, headers=headers)

    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_2_{tag}",
        "title": f"Beta Feature {tag}",
        "status": "In Progress",
        "priority": "Medium",
        "category": "Backend"
    }, headers=headers)

    client.post(f"{settings.API_V1_STR}/tasks", json={
        "id": f"task_3_{tag}",
        "title": f"Gamma Feature {tag}",
        "status": "Completed",
        "priority": "Low",
        "category": "Frontend"
    }, headers=headers)

    # 1. Filter: category == 'Backend' AND priority IN ['High', 'Medium']
    filter_req = {
        "entity_type": "TASK",
        "match_type": "ALL",
        "conditions": [
            {"field": "category", "operator": "eq", "value": "Backend"},
            {"field": "priority", "operator": "in", "value": ["High", "Medium"]}
        ]
    }
    res_filter = client.post(f"{settings.API_V1_STR}/search/filter", json=filter_req, headers=headers)
    assert res_filter.status_code == 200
    items = res_filter.json()["results"]
    assert len(items) >= 2
    assert all(i["category"] == "Backend" for i in items)

    # 2. Filter with ANY (OR) match
    or_filter_req = {
        "entity_type": "TASK",
        "match_type": "ANY",
        "conditions": [
            {"field": "priority", "operator": "eq", "value": "High"},
            {"field": "priority", "operator": "eq", "value": "Low"}
        ]
    }
    res_or = client.post(f"{settings.API_V1_STR}/search/filter", json=or_filter_req, headers=headers)
    assert res_or.status_code == 200
    or_items = res_or.json()["results"]
    assert any(i["priority"] == "High" for i in or_items)

# --------------------------------------------------------------------------
# 7. Sorting & Pagination Controls
# --------------------------------------------------------------------------
def test_search_sorting_and_pagination(client):
    headers, user_id, email = get_auth_headers(client, "sort_page")

    prefix = f"Page{uuid.uuid4().hex[:6]}"
    for i in range(5):
        client.post(f"{settings.API_V1_STR}/tasks", json={
            "id": f"task_p_{i}_{prefix}",
            "title": f"{prefix} Item {i:02d}",
            "status": "Todo",
            "priority": "Medium",
            "category": "Testing"
        }, headers=headers)

    # Page 1, page_size = 2
    res_p1 = client.get(f"{settings.API_V1_STR}/search?q={prefix}&page=1&page_size=2&sort_by=title&sort_order=asc", headers=headers)
    assert res_p1.status_code == 200
    d1 = res_p1.json()
    assert len(d1["results"]) == 2
    assert d1["total"] == 5
    assert d1["page"] == 1
    assert d1["total_pages"] == 3
    assert d1["has_next"] is True
    assert d1["has_prev"] is False
    assert "00" in d1["results"][0]["title"]

    # Page 2
    res_p2 = client.get(f"{settings.API_V1_STR}/search?q={prefix}&page=2&page_size=2&sort_by=title&sort_order=asc", headers=headers)
    assert res_p2.status_code == 200
    d2 = res_p2.json()
    assert len(d2["results"]) == 2
    assert d2["has_next"] is True
    assert d2["has_prev"] is True

# --------------------------------------------------------------------------
# 8. Search History Lifecycle
# --------------------------------------------------------------------------
def test_search_history_lifecycle(client):
    headers, user_id, email = get_auth_headers(client, "hist_user")

    # Perform a search
    query_str = f"DatabaseOptimization_{uuid.uuid4().hex[:6]}"
    client.get(f"{settings.API_V1_STR}/search?q={query_str}", headers=headers)

    # Retrieve history
    res_hist = client.get(f"{settings.API_V1_STR}/search/history", headers=headers)
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) >= 1
    found_item = next((h for h in history if h["query"] == query_str), None)
    assert found_item is not None

    # Delete specific history item
    hist_id = found_item["id"]
    res_del = client.delete(f"{settings.API_V1_STR}/search/history/{hist_id}", headers=headers)
    assert res_del.status_code == 204

    # Clear all history
    res_clear = client.delete(f"{settings.API_V1_STR}/search/history", headers=headers)
    assert res_clear.status_code == 200

    # History should now be empty
    res_hist_after = client.get(f"{settings.API_V1_STR}/search/history", headers=headers)
    assert len(res_hist_after.json()) == 0

# --------------------------------------------------------------------------
# 9. Saved Searches & Filter Presets CRUD
# --------------------------------------------------------------------------
def test_saved_searches_lifecycle(client):
    headers, user_id, email = get_auth_headers(client, "saved_s_user")

    # Create saved search
    saved_payload = {
        "name": "High Priority Engineering Tasks",
        "description": "Quick filter for backend blockers",
        "entity_type": "TASK",
        "query": "blocker",
        "filter_definition": {"status": "In Progress", "priority": "High"},
        "sorting_config": {"sort_by": "due_date", "sort_order": "asc"},
        "is_shared": False
    }
    res_create = client.post(f"{settings.API_V1_STR}/search/saved", json=saved_payload, headers=headers)
    assert res_create.status_code == 201, res_create.text
    saved_data = res_create.json()
    saved_id = saved_data["id"]
    assert saved_data["name"] == saved_payload["name"]
    assert saved_data["filter_definition"]["priority"] == "High"

    # List saved searches
    res_list = client.get(f"{settings.API_V1_STR}/search/saved", headers=headers)
    assert res_list.status_code == 200
    assert any(s["id"] == saved_id for s in res_list.json())

    # Get single saved search
    res_get = client.get(f"{settings.API_V1_STR}/search/saved/{saved_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == saved_id

    # Update saved search
    res_update = client.put(f"{settings.API_V1_STR}/search/saved/{saved_id}", json={
        "name": "Updated High Priority Blocker Filter",
        "is_shared": True
    }, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Updated High Priority Blocker Filter"
    assert res_update.json()["is_shared"] is True

    # Delete saved search
    res_del = client.delete(f"{settings.API_V1_STR}/search/saved/{saved_id}", headers=headers)
    assert res_del.status_code == 204

    # 404 after deletion
    res_get_deleted = client.get(f"{settings.API_V1_STR}/search/saved/{saved_id}", headers=headers)
    assert res_get_deleted.status_code == 404

# --------------------------------------------------------------------------
# 10. Security & IDOR Isolation (Cross-User Data Protection)
# --------------------------------------------------------------------------
def test_search_security_and_idor_protection(client):
    headers_alice, alice_id, _ = get_auth_headers(client, "alice")
    headers_bob, bob_id, _ = get_auth_headers(client, "bob")

    # Alice creates a private saved search
    res_saved = client.post(f"{settings.API_V1_STR}/search/saved", json={
        "name": "Alice Confidential Preset",
        "entity_type": "TASK",
        "is_shared": False
    }, headers=headers_alice)
    alice_saved_id = res_saved.json()["id"]

    # Bob attempts to read Alice's private saved search -> 404
    res_bob_get = client.get(f"{settings.API_V1_STR}/search/saved/{alice_saved_id}", headers=headers_bob)
    assert res_bob_get.status_code == 404

    # Bob attempts to update Alice's saved search -> 404
    res_bob_put = client.put(f"{settings.API_V1_STR}/search/saved/{alice_saved_id}", json={"name": "Hacked"}, headers=headers_bob)
    assert res_bob_put.status_code == 404

    # Bob attempts to delete Alice's saved search -> 404
    res_bob_del = client.delete(f"{settings.API_V1_STR}/search/saved/{alice_saved_id}", headers=headers_bob)
    assert res_bob_del.status_code == 404
