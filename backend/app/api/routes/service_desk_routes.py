"""
Service Desk & SLA Management REST API Routes (Module B52).
Mounted under prefix `/api/v1/service-desk`.
"""

from typing import List, Optional, Dict, Any
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.service_desk import (
    ServiceDeskTicket,
    ServiceDeskCategory,
    ServiceDeskSLAPolicy,
    ServiceDeskEscalationRule,
)
from app.schemas.service_desk import (
    ServiceDeskTicketCreate,
    ServiceDeskTicketResponse,
    ServiceDeskCommentCreate,
    ServiceDeskCommentResponse,
    ServiceDeskAssignRequest,
    ServiceDeskStatusTransitionRequest,
    ServiceDeskEscalateRequest,
    ServiceDeskCategoryCreate,
    ServiceDeskCategoryResponse,
    ServiceDeskSLAPolicyCreate,
    ServiceDeskSLAPolicyUpdate,
    ServiceDeskSLAPolicyResponse,
    ServiceDeskEscalationRuleCreate,
    ServiceDeskEscalationRuleResponse,
    ServiceDeskDashboardResponse,
)
from app.services import service_desk_service

router = APIRouter(prefix="/service-desk", tags=["Service Desk & SLA Management"])


def _get_user_org_id(current_user: User, db: Session) -> int:
    """Helper to ensure user belongs to an organization."""
    if hasattr(current_user, "organization_id") and current_user.organization_id:
        return current_user.organization_id
    org = db.query(Organization).first()
    if org:
        return org.id
    # Default fallback
    new_org = Organization(name="Default Organization", slug="default-org")
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org.id


def _map_ticket_to_response(t: ServiceDeskTicket) -> ServiceDeskTicketResponse:
    tags = []
    try:
        tags = json.loads(t.tags_json or "[]")
    except Exception:
        tags = []

    return ServiceDeskTicketResponse(
        id=t.id,
        ticket_number=t.ticket_number,
        organization_id=t.organization_id,
        workspace_id=t.workspace_id,
        subject=t.subject,
        description=t.description,
        requester_id=t.requester_id,
        requester_name=t.requester.name if t.requester else None,
        requester_email=t.requester.email if t.requester else None,
        assigned_agent_id=t.assigned_agent_id,
        assigned_agent_name=t.assigned_agent.name if t.assigned_agent else None,
        assigned_team_id=t.assigned_team_id,
        assigned_team_name=t.assigned_team.name if t.assigned_team else None,
        category_id=t.category_id,
        category_name=t.category_name,
        priority=t.priority,
        status=t.status,
        source=t.source,
        sla_policy_id=t.sla_policy_id,
        first_response_due_at=t.first_response_due_at,
        resolution_due_at=t.resolution_due_at,
        first_response_at=t.first_response_at,
        resolved_at=t.resolved_at,
        closed_at=t.closed_at,
        reopened_at=t.reopened_at,
        sla_response_status=t.sla_response_status,
        sla_resolution_status=t.sla_resolution_status,
        total_sla_pause_minutes=t.total_sla_pause_minutes,
        resolution_notes=t.resolution_notes,
        related_project_id=t.related_project_id,
        related_task_id=t.related_task_id,
        tags=tags,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


# =========================================================================
# 1. TICKETS ENDPOINTS
# =========================================================================

@router.post("/tickets", response_model=ServiceDeskTicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: ServiceDeskTicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new service desk ticket with automatic SLA calculation."""
    org_id = _get_user_org_id(current_user, db)
    ticket = service_desk_service.create_ticket(
        db=db,
        requester_id=current_user.id,
        organization_id=org_id,
        subject=payload.subject,
        description=payload.description,
        category_name=payload.category_name,
        category_id=payload.category_id,
        priority=payload.priority,
        workspace_id=payload.workspace_id,
        assigned_agent_id=payload.assigned_agent_id,
        assigned_team_id=payload.assigned_team_id,
        related_project_id=payload.related_project_id,
        related_task_id=payload.related_task_id,
        tags=payload.tags,
        source=payload.source,
    )
    return _map_ticket_to_response(ticket)


@router.get("/tickets", response_model=List[ServiceDeskTicketResponse])
def list_tickets(
    view: str = Query("all", description="my, assigned, queue, unassigned, all, overdue, at_risk, breached, resolved"),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    agent_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List service desk tickets with role-based scoping and filters."""
    org_id = _get_user_org_id(current_user, db)
    is_agent = current_user.role in ["Admin", "Owner", "Support", "Manager"]
    tickets = service_desk_service.list_tickets(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        is_agent=is_agent,
        view=view,
        status=status,
        priority=priority,
        category_id=category_id,
        team_id=team_id,
        agent_id=agent_id,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [_map_ticket_to_response(t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=ServiceDeskTicketResponse)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ticket detail with permissions enforcement."""
    ticket = service_desk_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_agent = current_user.role in ["Admin", "Owner", "Support", "Manager"]
    if not is_agent and ticket.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")

    return _map_ticket_to_response(ticket)


@router.post("/tickets/{ticket_id}/assign", response_model=ServiceDeskTicketResponse)
def assign_ticket(
    ticket_id: int,
    payload: ServiceDeskAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign or transfer a ticket to an agent or team."""
    is_agent = current_user.role in ["Admin", "Owner", "Support", "Manager"]
    if not is_agent:
        raise HTTPException(status_code=403, detail="Only support agents and admins can reassign tickets")

    try:
        updated = service_desk_service.assign_ticket(
            db=db,
            ticket_id=ticket_id,
            assigned_by_id=current_user.id,
            agent_id=payload.agent_id,
            team_id=payload.team_id,
            notes=payload.notes,
        )
        return _map_ticket_to_response(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tickets/{ticket_id}/status", response_model=ServiceDeskTicketResponse)
def update_ticket_status(
    ticket_id: int,
    payload: ServiceDeskStatusTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute controlled ticket lifecycle transition."""
    try:
        updated = service_desk_service.transition_ticket_status(
            db=db,
            ticket_id=ticket_id,
            user_id=current_user.id,
            new_status=payload.status,
            resolution_notes=payload.resolution_notes,
        )
        return _map_ticket_to_response(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tickets/{ticket_id}/escalate", status_code=status.HTTP_200_OK)
def escalate_ticket(
    ticket_id: int,
    payload: ServiceDeskEscalateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger manual escalation for a ticket."""
    try:
        record = service_desk_service.trigger_escalation(
            db=db,
            ticket_id=ticket_id,
            user_id=current_user.id,
            reason=payload.reason,
            bump_priority=payload.bump_priority,
            reassign_team_id=payload.reassign_team_id,
        )
        return {"status": "success", "escalation_id": record.id, "action_taken": record.action_taken}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 2. CONVERSATIONS & INTERNAL NOTES
# =========================================================================

@router.get("/tickets/{ticket_id}/comments", response_model=List[ServiceDeskCommentResponse])
def get_ticket_comments(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve ticket comments. Internal notes are strictly concealed from non-agent requesters."""
    ticket = service_desk_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_agent = current_user.role in ["Admin", "Owner", "Support", "Manager"]
    if not is_agent and ticket.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    comments = service_desk_service.get_ticket_comments(
        db=db,
        ticket_id=ticket_id,
        current_user_id=current_user.id,
        is_agent=is_agent,
    )
    return [
        ServiceDeskCommentResponse(
            id=c.id,
            ticket_id=c.ticket_id,
            user_id=c.user_id,
            user_name=c.author.name if c.author else None,
            user_email=c.author.email if c.author else None,
            is_internal_note=c.is_internal_note,
            content=c.content,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in comments
    ]


@router.post("/tickets/{ticket_id}/comments", response_model=ServiceDeskCommentResponse, status_code=status.HTTP_201_CREATED)
def add_ticket_comment(
    ticket_id: int,
    payload: ServiceDeskCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Post public response or confidential internal note."""
    ticket = service_desk_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_agent = current_user.role in ["Admin", "Owner", "Support", "Manager"]
    if not is_agent and ticket.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if payload.is_internal_note and not is_agent:
        raise HTTPException(status_code=403, detail="Requesters cannot create internal notes")

    comment = service_desk_service.add_ticket_comment(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        content=payload.content,
        is_internal_note=payload.is_internal_note,
        is_agent=is_agent,
    )
    return ServiceDeskCommentResponse(
        id=comment.id,
        ticket_id=comment.ticket_id,
        user_id=comment.user_id,
        user_name=current_user.name,
        user_email=current_user.email,
        is_internal_note=comment.is_internal_note,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


# =========================================================================
# 3. CATEGORIES & SLA POLICIES
# =========================================================================

@router.get("/categories", response_model=List[ServiceDeskCategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List service desk categories."""
    org_id = _get_user_org_id(current_user, db)
    cats = db.query(ServiceDeskCategory).filter(
        ServiceDeskCategory.organization_id == org_id,
        ServiceDeskCategory.is_active == True,
    ).order_by(ServiceDeskCategory.display_order.asc()).all()

    # Seed default categories if none exist
    if not cats:
        defaults = [
            ("Technical Support", "Software, bug reports, and errors", "HIGH"),
            ("Account & Access", "Login, SSO, MFA, and permission requests", "URGENT"),
            ("Hardware & Equipment", "Laptops, peripherals, and desk equipment", "MEDIUM"),
            ("Infrastructure & DevOps", "Cloud, CI/CD, databases, and deployment", "CRITICAL"),
            ("General Inquiry", "Questions, onboarding, and requests", "LOW"),
        ]
        for idx, (cname, cdesc, cpri) in enumerate(defaults):
            c = ServiceDeskCategory(
                organization_id=org_id,
                name=cname,
                description=cdesc,
                default_priority=cpri,
                display_order=idx,
            )
            db.add(c)
        db.commit()
        cats = db.query(ServiceDeskCategory).filter(
            ServiceDeskCategory.organization_id == org_id,
            ServiceDeskCategory.is_active == True,
        ).order_by(ServiceDeskCategory.display_order.asc()).all()

    return cats


@router.post("/categories", response_model=ServiceDeskCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: ServiceDeskCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create service desk category."""
    if current_user.role not in ["Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Only admins can manage categories")

    org_id = _get_user_org_id(current_user, db)
    cat = ServiceDeskCategory(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        default_priority=payload.default_priority,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/sla-policies", response_model=List[ServiceDeskSLAPolicyResponse])
def list_sla_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List SLA policies for organization."""
    org_id = _get_user_org_id(current_user, db)
    policies = db.query(ServiceDeskSLAPolicy).filter(
        ServiceDeskSLAPolicy.organization_id == org_id
    ).all()

    # Seed default SLA policy if empty
    if not policies:
        default_p = ServiceDeskSLAPolicy(
            organization_id=org_id,
            name="Standard Business SLA",
            description="Default SLA policy with 1h response and 8h resolution during standard business hours.",
            is_default=True,
            first_response_target_minutes=60,
            resolution_target_minutes=480,
            business_hours_start="09:00",
            business_hours_end="17:00",
            work_days="MON,TUE,WED,THU,FRI",
            timezone="UTC",
        )
        db.add(default_p)
        db.commit()
        db.refresh(default_p)
        policies = [default_p]

    return policies


@router.post("/sla-policies", response_model=ServiceDeskSLAPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_sla_policy(
    payload: ServiceDeskSLAPolicyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an SLA policy."""
    if current_user.role not in ["Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Only admins can manage SLA policies")

    org_id = _get_user_org_id(current_user, db)
    policy = ServiceDeskSLAPolicy(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        is_default=payload.is_default,
        first_response_target_minutes=payload.first_response_target_minutes,
        resolution_target_minutes=payload.resolution_target_minutes,
        business_hours_start=payload.business_hours_start,
        business_hours_end=payload.business_hours_end,
        work_days=payload.work_days,
        timezone=payload.timezone,
        applies_to_categories_json=payload.applies_to_categories_json or "[]",
        applies_to_priorities_json=payload.applies_to_priorities_json or "[]",
        allow_pause_on_waiting=payload.allow_pause_on_waiting,
        at_risk_threshold_percentage=payload.at_risk_threshold_percentage,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


# =========================================================================
# 4. ESCALATION RULES & BATCH EVALUATION
# =========================================================================

@router.get("/escalation-rules", response_model=List[ServiceDeskEscalationRuleResponse])
def list_escalation_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List escalation rules."""
    org_id = _get_user_org_id(current_user, db)
    return db.query(ServiceDeskEscalationRule).filter(
        ServiceDeskEscalationRule.organization_id == org_id
    ).all()


@router.post("/escalation-rules", response_model=ServiceDeskEscalationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_escalation_rule(
    payload: ServiceDeskEscalationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an automated escalation rule."""
    if current_user.role not in ["Admin", "Owner"]:
        raise HTTPException(status_code=403, detail="Only admins can manage escalation rules")

    org_id = _get_user_org_id(current_user, db)
    rule = ServiceDeskEscalationRule(
        organization_id=org_id,
        name=payload.name,
        trigger_type=payload.trigger_type,
        threshold_minutes=payload.threshold_minutes,
        target_action=payload.target_action,
        target_agent_id=payload.target_agent_id,
        target_team_id=payload.target_team_id,
        target_priority=payload.target_priority,
        is_enabled=payload.is_enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/sla/recalculate")
def recalculate_slas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Force recalculation of countdowns and breach detection across open tickets."""
    org_id = _get_user_org_id(current_user, db)
    count = service_desk_service.evaluate_sla_statuses(db, org_id)
    return {"status": "success", "evaluated_tickets": count}


# =========================================================================
# 5. DASHBOARD & PERFORMANCE REPORTS
# =========================================================================

@router.get("/dashboard", response_model=ServiceDeskDashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get centralized service desk operational metrics."""
    org_id = _get_user_org_id(current_user, db)
    # Automatically evaluate SLA countdowns on dashboard load
    service_desk_service.evaluate_sla_statuses(db, org_id)
    metrics = service_desk_service.get_service_desk_dashboard_metrics(db, org_id)
    return ServiceDeskDashboardResponse(**metrics)


@router.get("/reports/performance")
def get_performance_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get service team and agent performance analytics."""
    org_id = _get_user_org_id(current_user, db)
    return service_desk_service.get_agent_and_team_performance(db, org_id)
