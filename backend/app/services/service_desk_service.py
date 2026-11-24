"""
Service Desk & SLA Management Service (Module B52).
Handles tickets, assignments, SLA business calendars, breach detection, escalations, and performance analytics.
"""

from datetime import datetime, timezone, timedelta
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from app.models.service_desk import (
    ServiceDeskTicket,
    ServiceDeskCategory,
    ServiceDeskSLAPolicy,
    ServiceDeskComment,
    ServiceDeskAttachment,
    ServiceDeskAssignmentHistory,
    ServiceDeskActivityLog,
    ServiceDeskEscalationRule,
    ServiceDeskEscalationRecord,
    ServiceDeskSLABreach,
)
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.organization import Organization


def utc_now() -> datetime:
    return datetime.utcnow()

def to_naive(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


# =========================================================================
# 1. TICKET NUMBER GENERATION
# =========================================================================

def generate_ticket_number(db: Session, organization_id: int) -> str:
    """Generates collision-safe ticket numbers scoped to organization, e.g. SD-1001."""
    count = db.query(func.count(ServiceDeskTicket.id)).filter(
        ServiceDeskTicket.organization_id == organization_id
    ).scalar() or 0
    return f"SD-{1000 + count + 1}"


# =========================================================================
# 2. SLA BUSINESS CALENDAR CALCULATOR
# =========================================================================

DAY_MAP = {
    0: "MON",
    1: "TUE",
    2: "WED",
    3: "THU",
    4: "FRI",
    5: "SAT",
    6: "SUN",
}

def calculate_sla_target(
    start_time: datetime,
    target_minutes: int,
    business_hours_start: str = "09:00",
    business_hours_end: str = "17:00",
    work_days_str: str = "MON,TUE,WED,THU,FRI",
) -> datetime:
    """
    Calculates SLA due date advancing only through designated business hours and working days.
    """
    start_time = to_naive(start_time)

    allowed_days = set(d.strip().upper() for d in work_days_str.split(","))
    b_start_h, b_start_m = map(int, business_hours_start.split(":"))
    b_end_h, b_end_m = map(int, business_hours_end.split(":"))

    current = start_time
    remaining_minutes = target_minutes

    # If target is 0 or negative
    if remaining_minutes <= 0:
        return current

    # Max safeguard 365 days
    max_loops = 365 * 24
    loops = 0

    while remaining_minutes > 0 and loops < max_loops:
        loops += 1
        day_str = DAY_MAP[current.weekday()]

        if day_str not in allowed_days:
            # Advance to start of next day
            next_day = (current + timedelta(days=1)).replace(hour=b_start_h, minute=b_start_m, second=0, microsecond=0)
            current = next_day
            continue

        day_start = current.replace(hour=b_start_h, minute=b_start_m, second=0, microsecond=0)
        day_end = current.replace(hour=b_end_h, minute=b_end_m, second=0, microsecond=0)

        if current < day_start:
            current = day_start

        if current >= day_end:
            # Past business hours for today, move to tomorrow start
            next_day = (current + timedelta(days=1)).replace(hour=b_start_h, minute=b_start_m, second=0, microsecond=0)
            current = next_day
            continue

        available_today = int((day_end - current).total_seconds() / 60)
        if remaining_minutes <= available_today:
            current = current + timedelta(minutes=remaining_minutes)
            remaining_minutes = 0
            break
        else:
            remaining_minutes -= available_today
            current = (current + timedelta(days=1)).replace(hour=b_start_h, minute=b_start_m, second=0, microsecond=0)

    return current


# =========================================================================
# 3. SLA POLICY RESOLUTION
# =========================================================================

def get_applicable_sla_policy(
    db: Session,
    organization_id: int,
    category_id: Optional[int] = None,
    priority: str = "MEDIUM",
) -> Optional[ServiceDeskSLAPolicy]:
    """Finds most specific active SLA policy matching category and priority, or default policy."""
    policies = db.query(ServiceDeskSLAPolicy).filter(
        ServiceDeskSLAPolicy.organization_id == organization_id,
        ServiceDeskSLAPolicy.is_active == True,
    ).all()

    # 1. Exact match on both category and priority
    for p in policies:
        cats = json.loads(p.applies_to_categories_json or "[]")
        pris = json.loads(p.applies_to_priorities_json or "[]")
        cat_match = (not cats) or (category_id in cats)
        pri_match = (not pris) or (priority in pris)
        if cats and pris and cat_match and pri_match:
            return p

    # 2. Match on priority or category
    for p in policies:
        cats = json.loads(p.applies_to_categories_json or "[]")
        pris = json.loads(p.applies_to_priorities_json or "[]")
        if (pris and priority in pris) or (cats and category_id in cats):
            return p

    # 3. Default organization policy
    for p in policies:
        if p.is_default:
            return p

    # 4. Fallback to any policy
    return policies[0] if policies else None


# =========================================================================
# 4. TICKET CREATION & MANAGEMENT
# =========================================================================

def create_ticket(
    db: Session,
    requester_id: int,
    organization_id: int,
    subject: str,
    description: str,
    category_name: str = "Technical Support",
    category_id: Optional[int] = None,
    priority: str = "MEDIUM",
    workspace_id: Optional[int] = None,
    assigned_agent_id: Optional[int] = None,
    assigned_team_id: Optional[int] = None,
    related_project_id: Optional[int] = None,
    related_task_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    source: str = "PORTAL",
) -> ServiceDeskTicket:
    """Creates a new support ticket with calculated SLA response & resolution deadlines."""
    ticket_num = generate_ticket_number(db, organization_id)
    policy = get_applicable_sla_policy(db, organization_id, category_id, priority)

    now = utc_now()
    first_resp_due = None
    res_due = None
    policy_id = None
    policy_ver = 1

    if policy:
        policy_id = policy.id
        policy_ver = policy.version
        first_resp_due = calculate_sla_target(
            now,
            policy.first_response_target_minutes,
            policy.business_hours_start,
            policy.business_hours_end,
            policy.work_days,
        )
        res_due = calculate_sla_target(
            now,
            policy.resolution_target_minutes,
            policy.business_hours_start,
            policy.business_hours_end,
            policy.work_days,
        )

    initial_status = "ASSIGNED" if (assigned_agent_id or assigned_team_id) else "NEW"

    ticket = ServiceDeskTicket(
        ticket_number=ticket_num,
        organization_id=organization_id,
        workspace_id=workspace_id,
        subject=subject,
        description=description,
        requester_id=requester_id,
        assigned_agent_id=assigned_agent_id,
        assigned_team_id=assigned_team_id,
        category_id=category_id,
        category_name=category_name,
        priority=priority,
        status=initial_status,
        source=source,
        sla_policy_id=policy_id,
        sla_policy_version=policy_ver,
        first_response_due_at=first_resp_due,
        resolution_due_at=res_due,
        sla_response_status="ON_TRACK" if first_resp_due else "COMPLETED",
        sla_resolution_status="ON_TRACK" if res_due else "COMPLETED",
        related_project_id=related_project_id,
        related_task_id=related_task_id,
        tags_json=json.dumps(tags or []),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Activity log
    log = ServiceDeskActivityLog(
        ticket_id=ticket.id,
        user_id=requester_id,
        action="CREATED",
        new_value=ticket.ticket_number,
        details=f"Ticket {ticket.ticket_number} created with priority {priority} and SLA policy #{policy_id or 'none'}.",
    )
    db.add(log)

    if assigned_agent_id or assigned_team_id:
        assign_log = ServiceDeskAssignmentHistory(
            ticket_id=ticket.id,
            assigned_by_id=requester_id,
            new_agent_id=assigned_agent_id,
            new_team_id=assigned_team_id,
            notes="Initial assignment at ticket creation.",
        )
        db.add(assign_log)

    db.commit()
    return ticket


def get_ticket_by_id(db: Session, ticket_id: int) -> Optional[ServiceDeskTicket]:
    return db.query(ServiceDeskTicket).filter(ServiceDeskTicket.id == ticket_id).first()


def list_tickets(
    db: Session,
    organization_id: int,
    user_id: int,
    is_agent: bool = False,
    view: str = "all",  # my, assigned, queue, unassigned, all, overdue, at_risk, breached, resolved
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    team_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[ServiceDeskTicket]:
    """Retrieves tickets based on role, queue filters, and search terms."""
    q = db.query(ServiceDeskTicket).filter(ServiceDeskTicket.organization_id == organization_id)

    # Security scoping: if customer/requester, restrict strictly to own tickets
    if not is_agent:
        q = q.filter(ServiceDeskTicket.requester_id == user_id)
    else:
        # Agent views
        now = utc_now()
        if view == "my":
            q = q.filter(ServiceDeskTicket.requester_id == user_id)
        elif view == "assigned":
            q = q.filter(ServiceDeskTicket.assigned_agent_id == user_id)
        elif view == "unassigned":
            q = q.filter(ServiceDeskTicket.assigned_agent_id == None, ServiceDeskTicket.status.notin_(["RESOLVED", "CLOSED", "CANCELLED"]))
        elif view == "queue":
            if team_id:
                q = q.filter(ServiceDeskTicket.assigned_team_id == team_id)
            else:
                q = q.filter(ServiceDeskTicket.assigned_team_id != None)
        elif view == "overdue":
            q = q.filter(
                or_(
                    and_(ServiceDeskTicket.first_response_due_at < now, ServiceDeskTicket.first_response_at == None),
                    and_(ServiceDeskTicket.resolution_due_at < now, ServiceDeskTicket.resolved_at == None),
                ),
                ServiceDeskTicket.status.notin_(["RESOLVED", "CLOSED", "CANCELLED"])
            )
        elif view == "at_risk":
            q = q.filter(
                or_(
                    ServiceDeskTicket.sla_response_status == "AT_RISK",
                    ServiceDeskTicket.sla_resolution_status == "AT_RISK",
                ),
                ServiceDeskTicket.status.notin_(["RESOLVED", "CLOSED", "CANCELLED"])
            )
        elif view == "breached":
            q = q.filter(
                or_(
                    ServiceDeskTicket.sla_response_status == "BREACHED",
                    ServiceDeskTicket.sla_resolution_status == "BREACHED",
                )
            )
        elif view == "resolved":
            q = q.filter(ServiceDeskTicket.status.in_(["RESOLVED", "CLOSED"]))

    # Additional filters
    if status:
        q = q.filter(ServiceDeskTicket.status == status)
    if priority:
        q = q.filter(ServiceDeskTicket.priority == priority)
    if category_id:
        q = q.filter(ServiceDeskTicket.category_id == category_id)
    if agent_id:
        q = q.filter(ServiceDeskTicket.assigned_agent_id == agent_id)
    if team_id and view != "queue":
        q = q.filter(ServiceDeskTicket.assigned_team_id == team_id)

    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            or_(
                ServiceDeskTicket.ticket_number.ilike(term),
                ServiceDeskTicket.subject.ilike(term),
                ServiceDeskTicket.description.ilike(term),
            )
        )

    return q.order_by(desc(ServiceDeskTicket.created_at)).offset(skip).limit(limit).all()


# =========================================================================
# 5. TICKET STATUS & WORKFLOW ENGINE
# =========================================================================

ALLOWED_TRANSITIONS = {
    "NEW": ["OPEN", "ASSIGNED", "IN_PROGRESS", "CANCELLED"],
    "OPEN": ["ASSIGNED", "IN_PROGRESS", "WAITING_FOR_REQUESTER", "WAITING_FOR_THIRD_PARTY", "ESCALATED", "RESOLVED", "CANCELLED"],
    "ASSIGNED": ["IN_PROGRESS", "OPEN", "WAITING_FOR_REQUESTER", "ESCALATED", "RESOLVED", "CANCELLED"],
    "IN_PROGRESS": ["WAITING_FOR_REQUESTER", "WAITING_FOR_THIRD_PARTY", "ESCALATED", "RESOLVED", "CANCELLED"],
    "WAITING_FOR_REQUESTER": ["IN_PROGRESS", "OPEN", "RESOLVED", "CANCELLED"],
    "WAITING_FOR_THIRD_PARTY": ["IN_PROGRESS", "OPEN", "RESOLVED", "CANCELLED"],
    "ESCALATED": ["IN_PROGRESS", "RESOLVED", "CANCELLED"],
    "RESOLVED": ["CLOSED", "REOPENED"],
    "CLOSED": ["REOPENED"],
    "REOPENED": ["IN_PROGRESS", "ASSIGNED", "OPEN", "RESOLVED"],
    "CANCELLED": ["REOPENED"],
}

def transition_ticket_status(
    db: Session,
    ticket_id: int,
    user_id: int,
    new_status: str,
    resolution_notes: Optional[str] = None,
) -> ServiceDeskTicket:
    """Enforces controlled status lifecycle with SLA pause/resume and resolution checks."""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found")

    old_status = ticket.status
    if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
        raise ValueError(f"Invalid status transition from {old_status} to {new_status}")

    now = utc_now()

    # Handle Pause when entering WAITING_FOR_REQUESTER
    if new_status == "WAITING_FOR_REQUESTER":
        ticket.sla_paused_at = now
        ticket.sla_resolution_status = "PAUSED"

    # Handle Resume when exiting WAITING_FOR_REQUESTER
    elif old_status == "WAITING_FOR_REQUESTER" and ticket.sla_paused_at:
        pause_mins = max(0.0, (to_naive(now) - to_naive(ticket.sla_paused_at)).total_seconds() / 60.0)
        ticket.total_sla_pause_minutes += pause_mins
        ticket.sla_paused_at = None
        if ticket.resolution_due_at:
            ticket.resolution_due_at = to_naive(ticket.resolution_due_at) + timedelta(minutes=pause_mins)
        ticket.sla_resolution_status = "ON_TRACK"

    # Handle Resolution
    if new_status == "RESOLVED":
        ticket.resolved_at = now
        ticket.resolution_notes = resolution_notes or "Resolved"
        if ticket.resolution_due_at and to_naive(now) > to_naive(ticket.resolution_due_at):
            ticket.sla_resolution_status = "BREACHED"
            record_sla_breach(db, ticket, "RESOLUTION", to_naive(ticket.resolution_due_at), to_naive(now))
        else:
            ticket.sla_resolution_status = "COMPLETED"

    # Handle Closure
    elif new_status == "CLOSED":
        ticket.closed_at = now

    # Handle Reopening
    elif new_status == "REOPENED":
        ticket.reopened_at = now
        ticket.resolved_at = None
        ticket.closed_at = None
        ticket.sla_resolution_status = "ON_TRACK"

    ticket.status = new_status
    ticket.updated_at = now

    # Activity log
    log = ServiceDeskActivityLog(
        ticket_id=ticket.id,
        user_id=user_id,
        action="STATUS_CHANGED",
        previous_value=old_status,
        new_value=new_status,
        details=f"Status changed from {old_status} to {new_status}. {resolution_notes or ''}",
    )
    db.add(log)
    db.commit()
    db.refresh(ticket)
    return ticket


# =========================================================================
# 6. ASSIGNMENT & QUEUE MANAGEMENT
# =========================================================================

def assign_ticket(
    db: Session,
    ticket_id: int,
    assigned_by_id: int,
    agent_id: Optional[int] = None,
    team_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> ServiceDeskTicket:
    """Assigns or transfers ticket to an agent or team and records assignment history."""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found")

    old_agent_id = ticket.assigned_agent_id
    old_team_id = ticket.assigned_team_id

    ticket.assigned_agent_id = agent_id
    ticket.assigned_team_id = team_id

    if ticket.status == "NEW" and (agent_id or team_id):
        ticket.status = "ASSIGNED"

    ticket.updated_at = utc_now()

    # History
    history = ServiceDeskAssignmentHistory(
        ticket_id=ticket.id,
        assigned_by_id=assigned_by_id,
        previous_agent_id=old_agent_id,
        new_agent_id=agent_id,
        previous_team_id=old_team_id,
        new_team_id=team_id,
        notes=notes,
    )
    db.add(history)

    # Activity log
    log = ServiceDeskActivityLog(
        ticket_id=ticket.id,
        user_id=assigned_by_id,
        action="ASSIGNED",
        previous_value=f"Agent:{old_agent_id}, Team:{old_team_id}",
        new_value=f"Agent:{agent_id}, Team:{team_id}",
        details=notes or "Ticket assigned.",
    )
    db.add(log)
    db.commit()
    db.refresh(ticket)
    return ticket


# =========================================================================
# 7. CONVERSATIONS & INTERNAL NOTES
# =========================================================================

def add_ticket_comment(
    db: Session,
    ticket_id: int,
    user_id: int,
    content: str,
    is_internal_note: bool = False,
    is_agent: bool = False,
) -> ServiceDeskComment:
    """Adds public response or confidential internal note, calculating first-response SLA."""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found")

    comment = ServiceDeskComment(
        ticket_id=ticket.id,
        user_id=user_id,
        is_internal_note=is_internal_note,
        content=content,
    )
    db.add(comment)

    now = utc_now()

    # First response calculation: Only qualifying public replies from an agent or admin count
    if not is_internal_note and is_agent and user_id != ticket.requester_id and not ticket.first_response_at:
        ticket.first_response_at = now
        if ticket.first_response_due_at:
            if to_naive(now) > to_naive(ticket.first_response_due_at):
                ticket.sla_response_status = "BREACHED"
                record_sla_breach(db, ticket, "FIRST_RESPONSE", to_naive(ticket.first_response_due_at), to_naive(now))
            else:
                ticket.sla_response_status = "COMPLETED"

    # If ticket was waiting for requester, customer reply returns it to IN_PROGRESS
    if not is_agent and user_id == ticket.requester_id and ticket.status == "WAITING_FOR_REQUESTER":
        ticket.status = "IN_PROGRESS"
        if ticket.sla_paused_at:
            pause_mins = max(0.0, (to_naive(now) - to_naive(ticket.sla_paused_at)).total_seconds() / 60.0)
            ticket.total_sla_pause_minutes += pause_mins
            ticket.sla_paused_at = None
            if ticket.resolution_due_at:
                ticket.resolution_due_at = to_naive(ticket.resolution_due_at) + timedelta(minutes=pause_mins)
            ticket.sla_resolution_status = "ON_TRACK"

    ticket.updated_at = now

    log = ServiceDeskActivityLog(
        ticket_id=ticket.id,
        user_id=user_id,
        action="INTERNAL_NOTE" if is_internal_note else "PUBLIC_REPLY",
        details="Added confidential internal note" if is_internal_note else "Added public response to requester.",
    )
    db.add(log)
    db.commit()
    db.refresh(comment)
    return comment


def get_ticket_comments(
    db: Session,
    ticket_id: int,
    current_user_id: int,
    is_agent: bool = False,
) -> List[ServiceDeskComment]:
    """Retrieves ticket comments, strictly concealing internal notes from regular requesters."""
    q = db.query(ServiceDeskComment).filter(ServiceDeskComment.ticket_id == ticket_id)
    if not is_agent:
        q = q.filter(ServiceDeskComment.is_internal_note == False)
    return q.order_by(ServiceDeskComment.created_at.asc()).all()


# =========================================================================
# 8. SLA MONITORING & BREACH DETECTION
# =========================================================================

def record_sla_breach(
    db: Session,
    ticket: ServiceDeskTicket,
    breach_type: str,
    deadline: datetime,
    breached_at: datetime,
) -> Optional[ServiceDeskSLABreach]:
    """Records idempotent SLA breach event."""
    existing = db.query(ServiceDeskSLABreach).filter(
        ServiceDeskSLABreach.ticket_id == ticket.id,
        ServiceDeskSLABreach.breach_type == breach_type,
    ).first()
    if existing:
        return existing

    overdue_mins = max(0.0, (to_naive(breached_at) - to_naive(deadline)).total_seconds() / 60.0)
    breach = ServiceDeskSLABreach(
        ticket_id=ticket.id,
        policy_id=ticket.sla_policy_id,
        breach_type=breach_type,
        target_deadline=deadline,
        breached_at=breached_at,
        minutes_overdue=overdue_mins,
    )
    db.add(breach)
    db.commit()
    return breach


def evaluate_sla_statuses(db: Session, organization_id: int) -> int:
    """Evaluates countdowns, marks AT_RISK and BREACHED tickets across organization."""
    now = utc_now()
    open_tickets = db.query(ServiceDeskTicket).filter(
        ServiceDeskTicket.organization_id == organization_id,
        ServiceDeskTicket.status.notin_(["RESOLVED", "CLOSED", "CANCELLED"]),
    ).all()

    evaluated_count = 0
    for t in open_tickets:
        policy = t.sla_policy
        threshold = policy.at_risk_threshold_percentage if policy else 80.0

        # Response SLA check
        if not t.first_response_at and t.first_response_due_at:
            if to_naive(now) > to_naive(t.first_response_due_at):
                if t.sla_response_status != "BREACHED":
                    t.sla_response_status = "BREACHED"
                    record_sla_breach(db, t, "FIRST_RESPONSE", to_naive(t.first_response_due_at), to_naive(now))
            elif policy:
                total_time = policy.first_response_target_minutes
                remaining = max(0.0, (to_naive(t.first_response_due_at) - to_naive(now)).total_seconds() / 60.0)
                consumed_pct = ((total_time - remaining) / total_time) * 100.0 if total_time > 0 else 0
                if consumed_pct >= threshold:
                    t.sla_response_status = "AT_RISK"

        # Resolution SLA check
        if not t.resolved_at and t.resolution_due_at and t.status != "WAITING_FOR_REQUESTER":
            if to_naive(now) > to_naive(t.resolution_due_at):
                if t.sla_resolution_status != "BREACHED":
                    t.sla_resolution_status = "BREACHED"
                    record_sla_breach(db, t, "RESOLUTION", to_naive(t.resolution_due_at), to_naive(now))
            elif policy:
                total_time = policy.resolution_target_minutes
                remaining = max(0.0, (to_naive(t.resolution_due_at) - to_naive(now)).total_seconds() / 60.0)
                consumed_pct = ((total_time - remaining) / total_time) * 100.0 if total_time > 0 else 0
                if consumed_pct >= threshold:
                    t.sla_resolution_status = "AT_RISK"

        evaluated_count += 1

    db.commit()
    return evaluated_count


# =========================================================================
# 9. ESCALATION ENGINE
# =========================================================================

def trigger_escalation(
    db: Session,
    ticket_id: int,
    user_id: Optional[int] = None,
    rule_id: Optional[int] = None,
    reason: str = "Manual escalation",
    bump_priority: Optional[str] = None,
    reassign_team_id: Optional[int] = None,
) -> ServiceDeskEscalationRecord:
    """Escalates ticket, bump priority or reassigns team, and logs audit record."""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found")

    old_priority = ticket.priority
    ticket.status = "ESCALATED"
    if bump_priority:
        ticket.priority = bump_priority
    if reassign_team_id:
        ticket.assigned_team_id = reassign_team_id

    ticket.updated_at = utc_now()

    record = ServiceDeskEscalationRecord(
        ticket_id=ticket.id,
        rule_id=rule_id,
        triggered_by_id=user_id,
        action_taken=f"Escalated to {ticket.priority} priority",
        details=reason,
    )
    db.add(record)

    log = ServiceDeskActivityLog(
        ticket_id=ticket.id,
        user_id=user_id or ticket.requester_id,
        action="ESCALATED",
        previous_value=old_priority,
        new_value=ticket.priority,
        details=reason,
    )
    db.add(log)
    db.commit()
    db.refresh(record)
    return record


# =========================================================================
# 10. DASHBOARD & REPORTING METRICS
# =========================================================================

def get_service_desk_dashboard_metrics(
    db: Session,
    organization_id: int,
) -> Dict[str, Any]:
    """Computes comprehensive live operational and SLA health metrics."""
    tickets = db.query(ServiceDeskTicket).filter(
        ServiceDeskTicket.organization_id == organization_id
    ).all()

    total_tickets = len(tickets)
    open_tickets = [t for t in tickets if t.status not in ["RESOLVED", "CLOSED", "CANCELLED"]]
    new_tickets = [t for t in tickets if t.status == "NEW"]
    unassigned_tickets = [t for t in open_tickets if not t.assigned_agent_id]
    in_progress_tickets = [t for t in open_tickets if t.status in ["IN_PROGRESS", "ASSIGNED"]]
    resolved_tickets = [t for t in tickets if t.status in ["RESOLVED", "CLOSED"]]

    now = utc_now()
    overdue_tickets = [
        t for t in open_tickets
        if (t.first_response_due_at and to_naive(t.first_response_due_at) < now and not t.first_response_at) or
           (t.resolution_due_at and to_naive(t.resolution_due_at) < now and not t.resolved_at)
    ]
    at_risk_tickets = [
        t for t in open_tickets
        if t.sla_response_status == "AT_RISK" or t.sla_resolution_status == "AT_RISK"
    ]
    breached_tickets = [
        t for t in tickets
        if t.sla_response_status == "BREACHED" or t.sla_resolution_status == "BREACHED"
    ]

    # Calculate average first response time
    response_times = []
    for t in tickets:
        if t.first_response_at and t.created_at:
            diff = (to_naive(t.first_response_at) - to_naive(t.created_at)).total_seconds() / 60.0
            response_times.append(max(0.0, diff))
    avg_first_response_minutes = round(sum(response_times) / len(response_times), 1) if response_times else 0.0

    # Calculate average resolution time
    resolution_times = []
    for t in resolved_tickets:
        if t.resolved_at and t.created_at:
            diff = (to_naive(t.resolved_at) - to_naive(t.created_at)).total_seconds() / 60.0
            resolution_times.append(max(0.0, diff))
    avg_resolution_minutes = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0.0

    # SLA compliance rate
    resolved_count = len(resolved_tickets)
    breached_in_resolved = len([t for t in resolved_tickets if t.sla_resolution_status == "BREACHED"])
    sla_compliance_rate = round(((resolved_count - breached_in_resolved) / resolved_count) * 100.0, 1) if resolved_count > 0 else 100.0

    # Distributions
    by_status = {}
    by_priority = {}
    by_category = {}

    for t in tickets:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
        cat = t.category_name or "General"
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total_tickets": total_tickets,
        "open_tickets": len(open_tickets),
        "new_tickets": len(new_tickets),
        "unassigned_tickets": len(unassigned_tickets),
        "in_progress_tickets": len(in_progress_tickets),
        "resolved_tickets": len(resolved_tickets),
        "overdue_tickets": len(overdue_tickets),
        "at_risk_tickets": len(at_risk_tickets),
        "breached_tickets": len(breached_tickets),
        "avg_first_response_minutes": avg_first_response_minutes,
        "avg_resolution_minutes": avg_resolution_minutes,
        "sla_compliance_rate": sla_compliance_rate,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
    }


def get_agent_and_team_performance(
    db: Session,
    organization_id: int,
) -> Dict[str, Any]:
    """Calculates agent workload, resolved counts, and SLA metrics."""
    tickets = db.query(ServiceDeskTicket).filter(
        ServiceDeskTicket.organization_id == organization_id
    ).all()

    agent_stats: Dict[int, Dict[str, Any]] = {}
    team_stats: Dict[int, Dict[str, Any]] = {}

    for t in tickets:
        if t.assigned_agent_id:
            aid = t.assigned_agent_id
            if aid not in agent_stats:
                agent_stats[aid] = {"agent_id": aid, "assigned": 0, "resolved": 0, "open": 0, "breached": 0}
            agent_stats[aid]["assigned"] += 1
            if t.status in ["RESOLVED", "CLOSED"]:
                agent_stats[aid]["resolved"] += 1
            else:
                agent_stats[aid]["open"] += 1
            if t.sla_resolution_status == "BREACHED":
                agent_stats[aid]["breached"] += 1

        if t.assigned_team_id:
            tid = t.assigned_team_id
            if tid not in team_stats:
                team_stats[tid] = {"team_id": tid, "assigned": 0, "resolved": 0, "open": 0, "breached": 0}
            team_stats[tid]["assigned"] += 1
            if t.status in ["RESOLVED", "CLOSED"]:
                team_stats[tid]["resolved"] += 1
            else:
                team_stats[tid]["open"] += 1
            if t.sla_resolution_status == "BREACHED":
                team_stats[tid]["breached"] += 1

    return {
        "agents": list(agent_stats.values()),
        "teams": list(team_stats.values()),
    }
