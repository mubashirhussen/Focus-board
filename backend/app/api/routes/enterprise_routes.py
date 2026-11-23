import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.enterprise import CustomRole, OrganizationDomain, EnterpriseInvitation, UserMFA
from app.schemas.enterprise import (
    OrganizationPolicyResponse,
    PolicyUpdateRequest,
    CustomRoleCreate,
    CustomRoleResponse,
    DomainAddRequest,
    DomainResponse,
    EnterpriseInvitationCreate,
    EnterpriseInvitationResponse,
    MFASetupResponse,
    MFAVerifyRequest,
    MFADisableRequest,
)
from app.api.dependencies import get_current_user
from app.services.entitlement_service import get_tenant_id_for_user
from app.services.rbac_service import require_permission, get_user_permissions
from app.services.mfa_service import mfa_service
from app.services.enterprise_service import enterprise_service

router = APIRouter(prefix="/enterprise", tags=["Enterprise Administration & RBAC"])

@router.get("/policies")
def get_organization_policies(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve organization governance and security policies."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    return enterprise_service.get_policies(db, tenant_id)

@router.put("/policies/{policy_type}")
def update_organization_policy(
    policy_type: str,
    req: PolicyUpdateRequest,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization security policy (requires organization.manage_security)."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    require_permission(db, current_user, tenant_id, "organization.manage_security")
    resolved_val = req.get_resolved_value()
    enterprise_service.update_policy(db, tenant_id, policy_type, resolved_val, current_user.id)
    return {
        "status": "policy_updated",
        "policy_type": policy_type,
        "is_enabled": resolved_val.get("is_enabled", False),
        "policy_value": resolved_val,
    }

@router.get("/invitations", response_model=List[EnterpriseInvitationResponse])
def get_invitations(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List pending organization invitations."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    require_permission(db, current_user, tenant_id, "organization.manage_members")
    return enterprise_service.list_invitations(db, tenant_id)

@router.post("/invitations", response_model=EnterpriseInvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    req: EnterpriseInvitationCreate,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create organization invitation with corporate domain enforcement."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    require_permission(db, current_user, tenant_id, "organization.manage_members")
    return enterprise_service.create_invitation(
        db=db,
        tenant_id=tenant_id,
        email=req.email,
        role=req.role,
        inviter_id=current_user.id
    )

@router.get("/roles", response_model=List[CustomRoleResponse])
def get_custom_roles(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List custom organization RBAC roles."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    roles = db.query(CustomRole).filter(CustomRole.tenant_id == tenant_id).all()
    results = []
    for r in roles:
        results.append(CustomRoleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            permissions=json.loads(r.permissions_json) if r.permissions_json else [],
            created_at=r.created_at
        ))
    return results

@router.post("/roles", response_model=CustomRoleResponse, status_code=status.HTTP_201_CREATED)
def create_custom_role(
    role_in: CustomRoleCreate,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create custom enterprise role with specific permission assignment."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    require_permission(db, current_user, tenant_id, "organization.manage_members")

    role = CustomRole(
        tenant_id=tenant_id,
        name=role_in.name,
        description=role_in.description,
        permissions_json=json.dumps(role_in.permissions),
        created_by=current_user.id
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    return CustomRoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=role_in.permissions,
        created_at=role.created_at
    )

@router.get("/domains", response_model=List[DomainResponse])
def get_domains(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List verified and pending organization domain records."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    return db.query(OrganizationDomain).filter(OrganizationDomain.tenant_id == tenant_id).all()

@router.post("/domains", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
def add_domain(
    req: DomainAddRequest,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a domain for enterprise email verification."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    require_permission(db, current_user, tenant_id, "organization.manage_security")
    return enterprise_service.add_domain(db, tenant_id, req.domain)

@router.post("/domains/{domain_id}/verify", response_model=DomainResponse)
def verify_domain(
    domain_id: int,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify ownership of an enterprise domain."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    require_permission(db, current_user, tenant_id, "organization.manage_security")
    success = enterprise_service.verify_domain(db, tenant_id, domain_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    return db.query(OrganizationDomain).filter(OrganizationDomain.id == domain_id).first()

# MFA Endpoints
@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate TOTP secret and recovery codes for MFA enrollment."""
    secret, qr_uri, recovery_codes = mfa_service.setup_mfa(db, current_user)
    return MFASetupResponse(
        secret=secret,
        qr_uri=qr_uri,
        recovery_codes=recovery_codes
    )

@router.post("/mfa/verify")
def verify_mfa(
    req: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify TOTP token to activate MFA."""
    success = mfa_service.verify_and_enable(db, current_user, req.code)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP verification code")
    return {"status": "mfa_enabled"}

@router.post("/mfa/disable")
def disable_mfa(
    req: MFADisableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disable MFA using code or backup recovery code."""
    success = mfa_service.disable_mfa(db, current_user, req.code)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code or recovery code")
    return {"status": "mfa_disabled"}

@router.get("/audit-logs/export")
def export_compliance_audit_logs(
    request: Request,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export compliance audit trail to CSV (requires organization.export)."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    require_permission(db, current_user, tenant_id, "organization.view_audit_logs")
    csv_content = enterprise_service.export_audit_logs_csv(db, current_user, request)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=focusboard_audit_{datetime.now().strftime('%Y%m%d')}.csv"}
    )
