from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.api.dependencies import get_current_user
from app.services.audit_service import record_audit_log

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    action: Optional[str] = Query(None, description="Alias for event_type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    actor_id: Optional[int] = Query(None, description="Filter by actor ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    from_date: Optional[datetime] = Query(None, description="Earliest timestamp"),
    to_date: Optional[datetime] = Query(None, description="Latest timestamp"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve immutable audit log records.
    Normal users retrieve their own actions; Admins retrieve all system security logs.
    """
    # Record read access audit FIRST so it is captured in the retrieved audit logs
    record_audit_log(
        db=db,
        event_type="AUDIT_LOG_VIEW",
        actor_id=current_user.id,
        resource_type="AUDIT_LOG",
        request=request,
        metadata={"page": page}
    )

    query = db.query(AuditLog)

    is_admin = (current_user.role or "").upper() in ["ADMIN", "OWNER"]
    if not is_admin:
        query = query.filter(AuditLog.actor_id == current_user.id)
    elif actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)

    eff_event_type = event_type or action
    if eff_event_type:
        query = query.filter(AuditLog.event_type == eff_event_type)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == str(resource_id))
    if organization_id:
        query = query.filter(AuditLog.organization_id == organization_id)
    if workspace_id:
        query = query.filter(AuditLog.workspace_id == workspace_id)
    if from_date:
        from_naive = from_date.replace(tzinfo=None) if from_date.tzinfo else from_date
        query = query.filter(AuditLog.created_at >= from_naive)
    if to_date:
        to_naive = to_date.replace(tzinfo=None) if to_date.tzinfo else to_date
        query = query.filter(AuditLog.created_at <= to_naive)

    query = query.order_by(desc(AuditLog.created_at))
    start_idx = (page - 1) * page_size
    logs = query.offset(start_idx).limit(page_size).all()

    return logs
