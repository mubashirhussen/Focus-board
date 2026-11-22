from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.observability import (
    ServiceRegistryItemResponse,
    PlatformAlertRuleResponse,
    PlatformAlertResponse,
    PlatformAlertCreate,
    PlatformIncidentResponse,
    PlatformIncidentCreate,
    PlatformIncidentUpdate,
    IncidentActionItemResponse,
    IncidentActionItemCreate,
    IncidentPostMortemResponse,
    IncidentPostMortemCreate,
    SLODefinitionResponse,
    PlatformMaintenanceWindowResponse,
    PlatformMaintenanceWindowCreate,
    SupportDiagnosticRequest,
    SupportDiagnosticResponse,
    PlatformOperationsOverviewResponse,
)
from app.services import observability_service

router = APIRouter(prefix="/observability", tags=["FocusBoard Platform Observability & Operations"])

# --- Overview & Health ---
@router.get("/overview", response_model=PlatformOperationsOverviewResponse)
def get_operations_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full operations overview: system health, active alerts, incidents, and SLO metrics."""
    return observability_service.get_operations_overview(db)

@router.get("/services", response_model=List[ServiceRegistryItemResponse])
def list_services(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Live diagnostic scan and status listing of registered services."""
    return observability_service.run_live_health_checks(db)

# --- Alerts ---
@router.get("/alerts", response_model=List[PlatformAlertResponse])
def list_alerts(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List operational alerts."""
    return observability_service.list_alerts(db, status=status)

@router.post("/alerts", response_model=PlatformAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: PlatformAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or record an operational alert."""
    return observability_service.create_alert(db, payload)

@router.post("/alerts/{alert_id}/acknowledge", response_model=PlatformAlertResponse)
def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Acknowledge an active alert."""
    alert = observability_service.acknowledge_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert

@router.post("/alerts/{alert_id}/resolve", response_model=PlatformAlertResponse)
def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resolve an active or acknowledged alert."""
    alert = observability_service.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert

# --- Incidents ---
@router.get("/incidents", response_model=List[PlatformIncidentResponse])
def list_incidents(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List platform operational incidents."""
    return observability_service.list_incidents(db, status=status)

@router.get("/incidents/{incident_id}", response_model=PlatformIncidentResponse)
def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get incident details with timeline entries and action items."""
    inc = observability_service.get_incident(db, incident_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return inc

@router.post("/incidents", response_model=PlatformIncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: PlatformIncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report and open a new platform incident."""
    return observability_service.create_incident(db, payload, creator_id=current_user.id)

@router.patch("/incidents/{incident_id}", response_model=PlatformIncidentResponse)
def update_incident(
    incident_id: str,
    payload: PlatformIncidentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update incident status, severity, root cause, or resolution."""
    inc = observability_service.update_incident(db, incident_id, payload, user_id=current_user.id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return inc

@router.post("/incidents/{incident_id}/action-items", response_model=IncidentActionItemResponse, status_code=status.HTTP_201_CREATED)
def add_action_item(
    incident_id: str,
    payload: IncidentActionItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Attach preventative action item to an incident."""
    return observability_service.add_incident_action_item(db, incident_id, payload)

@router.post("/incidents/{incident_id}/post-mortem", response_model=IncidentPostMortemResponse, status_code=status.HTTP_201_CREATED)
def create_post_mortem(
    incident_id: str,
    payload: IncidentPostMortemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish blameless post-mortem for resolved incident."""
    return observability_service.create_incident_post_mortem(db, incident_id, payload)

# --- Support Diagnostics & Maintenance ---
@router.post("/diagnostics/support", response_model=SupportDiagnosticResponse)
def run_support_diagnostics(
    payload: SupportDiagnosticRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute safe non-intrusive workspace diagnosis."""
    try:
        return observability_service.run_support_diagnostics(db, payload.workspace_id, payload.check_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/maintenance", response_model=List[PlatformMaintenanceWindowResponse])
def list_maintenance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List scheduled or completed maintenance windows."""
    windows = observability_service.list_maintenance_windows(db)
    out = []
    for w in windows:
        aff = []
        try:
            import json
            aff = json.loads(w.affected_services_json)
        except Exception:
            aff = []
        out.append({
            "id": w.id,
            "title": w.title,
            "description": w.description,
            "status": w.status,
            "scheduled_start": w.scheduled_start,
            "scheduled_end": w.scheduled_end,
            "affected_services_json": w.affected_services_json,
            "affected_services_list": aff,
            "created_by_id": w.created_by_id,
            "created_at": w.created_at,
        })
    return out

@router.post("/maintenance", response_model=PlatformMaintenanceWindowResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance(
    payload: PlatformMaintenanceWindowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schedule a platform maintenance window."""
    w = observability_service.create_maintenance_window(db, payload, user_id=current_user.id)
    aff = []
    try:
        import json
        aff = json.loads(w.affected_services_json)
    except Exception:
        aff = []
    return {
        "id": w.id,
        "title": w.title,
        "description": w.description,
        "status": w.status,
        "scheduled_start": w.scheduled_start,
        "scheduled_end": w.scheduled_end,
        "affected_services_json": w.affected_services_json,
        "affected_services_list": aff,
        "created_by_id": w.created_by_id,
        "created_at": w.created_at,
    }
