import json
from typing import List, Dict, Set, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.enterprise import CustomRole

# Standardized granular permissions
ROLE_PERMISSIONS_MAP: Dict[str, Set[str]] = {
    "OWNER": {
        "organization.view", "organization.update", "organization.manage_members",
        "organization.manage_security", "organization.view_audit_logs", "organization.export",
        "workspace.view", "workspace.create", "workspace.update", "workspace.delete", "workspace.manage_members",
        "project.view", "project.create", "project.update", "project.delete",
        "task.view", "task.create", "task.update", "task.delete", "task.assign",
        "billing.view", "billing.manage", "integration.view", "integration.manage"
    },
    "ADMIN": {
        "organization.view", "organization.manage_members", "organization.manage_security",
        "organization.view_audit_logs",
        "workspace.view", "workspace.create", "workspace.update", "workspace.manage_members",
        "project.view", "project.create", "project.update", "project.delete",
        "task.view", "task.create", "task.update", "task.delete", "task.assign",
        "integration.view", "integration.manage"
    },
    "WORKSPACE_ADMIN": {
        "workspace.view", "workspace.update", "workspace.manage_members",
        "project.view", "project.create", "project.update", "project.delete",
        "task.view", "task.create", "task.update", "task.delete", "task.assign"
    },
    "MEMBER": {
        "workspace.view", "project.view", "project.create",
        "task.view", "task.create", "task.update", "task.assign"
    },
    "GUEST": {
        "workspace.view", "project.view", "task.view"
    }
}

def get_user_permissions(db: Session, user: User, tenant_id: str) -> Set[str]:
    """Resolve all active permissions for a user within a given tenant/workspace."""
    # 1. Global user role
    role_name = (user.role or "Member").upper()
    perms: Set[str] = set(ROLE_PERMISSIONS_MAP.get(role_name, ROLE_PERMISSIONS_MAP["MEMBER"]))

    # 2. Check workspace-specific membership role if tenant is a workspace
    if tenant_id.startswith("ws:"):
        ws_id = int(tenant_id.replace("ws:", ""))
        membership = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == ws_id,
            WorkspaceMember.user_id == user.id
        ).first()
        if membership:
            m_role = (membership.role or "MEMBER").upper()
            perms.update(ROLE_PERMISSIONS_MAP.get(m_role, set()))

    # 3. Check custom roles assigned to tenant
    custom_roles = db.query(CustomRole).filter(CustomRole.tenant_id == tenant_id).all()
    for cr in custom_roles:
        if cr.name.upper() == role_name:
            role_perms = json.loads(cr.permissions_json) if cr.permissions_json else []
            perms.update(role_perms)

    return perms

def require_permission(db: Session, user: User, tenant_id: str, permission: str):
    """Enforce permission check and raise HTTP 403 Forbidden on violation."""
    user_perms = get_user_permissions(db, user, tenant_id)
    if permission not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required privilege: '{permission}'"
        )
