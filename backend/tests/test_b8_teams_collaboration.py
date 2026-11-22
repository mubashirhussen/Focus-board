import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def get_auth_headers(client, email_prefix="b8_user"):
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{unique}@focusboard.io"
    password = "TeamSecurePass123!"
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
# 1. Team CRUD & Lifecycle (Create, Read, Update, Archive, Restore, Delete)
# --------------------------------------------------------------------------
def test_team_crud_and_lifecycle(client):
    headers, user_id, _ = get_auth_headers(client, "team_creator")

    # 1. Create team
    create_payload = {
        "name": "Platform Engineering",
        "description": "Core infra and backend platform team",
        "visibility": "ORGANIZATION",
    }
    res_create = client.post(f"{settings.API_V1_STR}/teams", json=create_payload, headers=headers)
    assert res_create.status_code == 201, res_create.text
    team = res_create.json()
    team_id = team["id"]
    assert team["name"] == "Platform Engineering"
    assert team["owner_id"] == user_id
    assert team["is_archived"] is False
    assert team["status"] == "active"
    assert "slug" in team

    # 2. Get team by ID
    res_get = client.get(f"{settings.API_V1_STR}/teams/{team_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == team_id

    # 3. List teams
    res_list = client.get(f"{settings.API_V1_STR}/teams", headers=headers)
    assert res_list.status_code == 200
    team_ids = [t["id"] for t in res_list.json()]
    assert team_id in team_ids

    # 4. Update team
    update_payload = {
        "name": "Core Platform & Infra",
        "description": "Updated platform description",
        "visibility": "WORKSPACE",
    }
    res_update = client.patch(f"{settings.API_V1_STR}/teams/{team_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200
    updated_team = res_update.json()
    assert updated_team["name"] == "Core Platform & Infra"
    assert updated_team["visibility"] == "WORKSPACE"

    # 5. Archive team
    res_archive = client.post(f"{settings.API_V1_STR}/teams/{team_id}/archive", headers=headers)
    assert res_archive.status_code == 200
    assert res_archive.json()["is_archived"] is True
    assert res_archive.json()["status"] == "archived"

    # 6. Restore team
    res_restore = client.post(f"{settings.API_V1_STR}/teams/{team_id}/restore", headers=headers)
    assert res_restore.status_code == 200
    assert res_restore.json()["is_archived"] is False
    assert res_restore.json()["status"] == "active"

    # 7. Delete team (requires OWNER)
    res_del = client.delete(f"{settings.API_V1_STR}/teams/{team_id}", headers=headers)
    assert res_del.status_code == 204

    # Verify team is gone (404)
    res_get_deleted = client.get(f"{settings.API_V1_STR}/teams/{team_id}", headers=headers)
    assert res_get_deleted.status_code == 404

# --------------------------------------------------------------------------
# 2. Team Membership & Role Hierarchy Management
# --------------------------------------------------------------------------
def test_team_membership_and_roles(client):
    owner_headers, owner_id, _ = get_auth_headers(client, "owner_lead")
    collab_headers, collab_id, _ = get_auth_headers(client, "collab_dev")

    # Create team
    res_team = client.post(
        f"{settings.API_V1_STR}/teams",
        json={"name": "Frontend Guild", "description": "UI & Design System Guild"},
        headers=owner_headers,
    )
    assert res_team.status_code == 201
    team_id = res_team.json()["id"]

    # Verify owner is automatically in team members
    res_members = client.get(f"{settings.API_V1_STR}/teams/{team_id}/members", headers=owner_headers)
    assert res_members.status_code == 200
    members = res_members.json()
    assert len(members) == 1
    assert members[0]["user_id"] == owner_id
    assert members[0]["role"] == "OWNER"

    # Add collaborator directly
    add_payload = {
        "user_id": collab_id,
        "role": "MEMBER",
        "title": "Frontend Engineer",
    }
    res_add = client.post(f"{settings.API_V1_STR}/teams/{team_id}/members", json=add_payload, headers=owner_headers)
    assert res_add.status_code == 201
    assert res_add.json()["user_id"] == collab_id
    assert res_add.json()["role"] == "MEMBER"

    # Promoting member to ADMIN
    res_role_update = client.patch(
        f"{settings.API_V1_STR}/teams/{team_id}/members/{collab_id}/role",
        json={"role": "ADMIN", "title": "Lead Frontend Engineer"},
        headers=owner_headers,
    )
    assert res_role_update.status_code == 200
    assert res_role_update.json()["role"] == "ADMIN"
    assert res_role_update.json()["title"] == "Lead Frontend Engineer"

    # Last-owner demotion protection: Owner tries to demote themselves when no other owner exists
    res_demote_owner = client.patch(
        f"{settings.API_V1_STR}/teams/{team_id}/members/{owner_id}/role",
        json={"role": "MEMBER"},
        headers=owner_headers,
    )
    assert res_demote_owner.status_code == 400
    assert "last owner" in res_demote_owner.text.lower()

    # Last-owner removal protection: Owner tries to remove themselves
    res_remove_owner = client.delete(f"{settings.API_V1_STR}/teams/{team_id}/members/{owner_id}", headers=owner_headers)
    assert res_remove_owner.status_code == 400
    assert "last owner" in res_remove_owner.text.lower()

    # Collaborator leaves team voluntarily
    res_leave = client.delete(f"{settings.API_V1_STR}/teams/{team_id}/members/{collab_id}", headers=collab_headers)
    assert res_leave.status_code == 204

    # Verify collaborator is no longer in member list
    res_members_after = client.get(f"{settings.API_V1_STR}/teams/{team_id}/members", headers=owner_headers)
    assert res_members_after.status_code == 200
    remaining_ids = [m["user_id"] for m in res_members_after.json()]
    assert collab_id not in remaining_ids

# --------------------------------------------------------------------------
# 3. Ownership Transfer
# --------------------------------------------------------------------------
def test_team_ownership_transfer(client):
    owner_headers, owner_id, _ = get_auth_headers(client, "first_owner")
    successor_headers, successor_id, _ = get_auth_headers(client, "successor")

    # Create team
    res_team = client.post(
        f"{settings.API_V1_STR}/teams",
        json={"name": "DevOps Operations", "description": "Cloud infra and CI/CD pipelines"},
        headers=owner_headers,
    )
    team_id = res_team.json()["id"]

    # Add successor as member first
    client.post(
        f"{settings.API_V1_STR}/teams/{team_id}/members",
        json={"user_id": successor_id, "role": "ADMIN"},
        headers=owner_headers,
    )

    # Transfer ownership
    res_transfer = client.post(
        f"{settings.API_V1_STR}/teams/{team_id}/transfer-ownership",
        json={"new_owner_id": successor_id},
        headers=owner_headers,
    )
    assert res_transfer.status_code == 200
    assert res_transfer.json()["owner_id"] == successor_id

    # Verify member roles after transfer: successor is OWNER, old owner is ADMIN
    res_members = client.get(f"{settings.API_V1_STR}/teams/{team_id}/members", headers=successor_headers)
    assert res_members.status_code == 200
    member_role_map = {m["user_id"]: m["role"] for m in res_members.json()}
    assert member_role_map[successor_id] == "OWNER"
    assert member_role_map[owner_id] == "ADMIN"

# --------------------------------------------------------------------------
# 4. Team Invitations Lifecycle (Create, Resend, Accept, Decline, Revoke)
# --------------------------------------------------------------------------
def test_team_invitations_lifecycle(client):
    owner_headers, owner_id, _ = get_auth_headers(client, "inviter_owner")
    invitee_headers, invitee_id, invitee_email = get_auth_headers(client, "invitee_user")

    # Create team
    res_team = client.post(
        f"{settings.API_V1_STR}/teams",
        json={"name": "Data Analytics Core"},
        headers=owner_headers,
    )
    team_id = res_team.json()["id"]

    # 1. Create invitation
    invite_payload = {
        "email": invitee_email,
        "role": "MEMBER",
        "message": "Welcome to Data Analytics Team!",
    }
    res_invite = client.post(
        f"{settings.API_V1_STR}/teams/{team_id}/invitations",
        json=invite_payload,
        headers=owner_headers,
    )
    assert res_invite.status_code == 201, res_invite.text
    invitation = res_invite.json()
    assert invitation["invitee_email"] == invitee_email
    assert invitation["status"] == "PENDING"
    raw_token = invitation.get("token")
    assert raw_token is not None
    invitation_id = invitation["id"]

    # 2. List invitations
    res_list_inv = client.get(f"{settings.API_V1_STR}/teams/{team_id}/invitations", headers=owner_headers)
    assert res_list_inv.status_code == 200
    assert len(res_list_inv.json()) >= 1

    # 3. Resend invitation
    res_resend = client.post(
        f"{settings.API_V1_STR}/teams/{team_id}/invitations/{invitation_id}/resend",
        headers=owner_headers,
    )
    assert res_resend.status_code == 200
    new_raw_token = res_resend.json().get("token")
    assert new_raw_token is not None
    assert new_raw_token != raw_token

    # 4. Accept invitation using new token
    res_accept = client.post(
        f"{settings.API_V1_STR}/teams/invitations/{new_raw_token}/accept",
        headers=invitee_headers,
    )
    assert res_accept.status_code == 200, res_accept.text
    assert res_accept.json()["status"] == "success"
    assert res_accept.json()["team_id"] == team_id

    # Verify invitee is now an active member
    res_members = client.get(f"{settings.API_V1_STR}/teams/{team_id}/members", headers=invitee_headers)
    assert res_members.status_code == 200
    member_user_ids = [m["user_id"] for m in res_members.json()]
    assert invitee_id in member_user_ids

    # 5. Test Revoke and Decline with a separate invitation
    other_email = f"other_invite_{uuid.uuid4().hex[:6]}@focusboard.io"
    res_invite2 = client.post(
        f"{settings.API_V1_STR}/teams/{team_id}/invitations",
        json={"email": other_email, "role": "VIEWER"},
        headers=owner_headers,
    )
    assert res_invite2.status_code == 201
    inv2 = res_invite2.json()
    inv2_id = inv2["id"]
    inv2_token = inv2["token"]

    # Decline invitation
    other_headers, _, _ = get_auth_headers(client, "decline_user")
    res_decline = client.post(f"{settings.API_V1_STR}/teams/invitations/{inv2_token}/decline", headers=other_headers)
    assert res_decline.status_code == 200

    # Create third invitation and revoke it
    res_invite3 = client.post(
        f"{settings.API_V1_STR}/teams/{team_id}/invitations",
        json={"email": f"revoke_{uuid.uuid4().hex[:6]}@focusboard.io", "role": "MEMBER"},
        headers=owner_headers,
    )
    inv3_id = res_invite3.json()["id"]
    res_revoke = client.delete(f"{settings.API_V1_STR}/teams/{team_id}/invitations/{inv3_id}", headers=owner_headers)
    assert res_revoke.status_code == 200

# --------------------------------------------------------------------------
# 5. Team Settings & Team Summary
# --------------------------------------------------------------------------
def test_team_settings_and_summary(client):
    headers, user_id, _ = get_auth_headers(client, "settings_user")

    # Create team
    res_team = client.post(
        f"{settings.API_V1_STR}/teams",
        json={"name": "Product Strategy Hub"},
        headers=headers,
    )
    team_id = res_team.json()["id"]

    # Update settings
    settings_payload = {
        "settings": {
            "default_project_visibility": "TEAM",
            "slack_notifications_enabled": True,
            "weekly_digest": False,
        }
    }
    res_set = client.patch(f"{settings.API_V1_STR}/teams/{team_id}/settings", json=settings_payload, headers=headers)
    assert res_set.status_code == 200
    assert res_set.json()["settings"]["slack_notifications_enabled"] is True

    # Retrieve settings
    res_get_set = client.get(f"{settings.API_V1_STR}/teams/{team_id}/settings", headers=headers)
    assert res_get_set.status_code == 200
    assert res_get_set.json()["default_project_visibility"] == "TEAM"

    # Get team summary
    res_summary = client.get(f"{settings.API_V1_STR}/teams/{team_id}/summary", headers=headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["team_id"] == team_id
    assert summary["total_members"] == 1
    assert summary["active_members"] == 1
    assert summary["is_archived"] is False

# --------------------------------------------------------------------------
# 6. Multi-Tenant IDOR Security Isolation
# --------------------------------------------------------------------------
def test_team_security_and_idor_isolation(client):
    user_a_headers, user_a_id, _ = get_auth_headers(client, "user_org_a")
    user_b_headers, user_b_id, _ = get_auth_headers(client, "user_org_b")

    # User A creates a private team
    res_team = client.post(
        f"{settings.API_V1_STR}/teams",
        json={"name": "Confidential Security RedTeam", "visibility": "PRIVATE"},
        headers=user_a_headers,
    )
    team_id = res_team.json()["id"]

    # User B (different user, not in team) attempts to access team
    res_get_unauthorized = client.get(f"{settings.API_V1_STR}/teams/{team_id}", headers=user_b_headers)
    assert res_get_unauthorized.status_code == 404  # Silent 404 for IDOR security

    # User B attempts to update team
    res_patch_unauthorized = client.patch(
        f"{settings.API_V1_STR}/teams/{team_id}",
        json={"name": "Hacked Name"},
        headers=user_b_headers,
    )
    assert res_patch_unauthorized.status_code == 404

    # User B attempts to delete team
    res_del_unauthorized = client.delete(f"{settings.API_V1_STR}/teams/{team_id}", headers=user_b_headers)
    assert res_del_unauthorized.status_code == 404

    # User B attempts to list members
    res_members_unauthorized = client.get(f"{settings.API_V1_STR}/teams/{team_id}/members", headers=user_b_headers)
    assert res_members_unauthorized.status_code == 404
