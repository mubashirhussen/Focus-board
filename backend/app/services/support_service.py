import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.support import (
    SupportTicket,
    SupportMessage,
    KnowledgeBaseCategory,
    KnowledgeBaseArticle,
    ProductRoadmapItem,
)
from app.models.user import User
from app.models.task import Task

def utc_now():
    return datetime.now(timezone.utc)

def seed_default_knowledge_base(db: Session):
    """Seed initial, verified knowledge base articles if empty."""
    if db.query(KnowledgeBaseCategory).count() > 0:
        return

    # 1. Getting Started
    cat_start = KnowledgeBaseCategory(
        name="Getting Started",
        slug="getting-started",
        description="Learn core task management, workspaces, and navigation in FocusBoard.",
        display_order=1,
    )
    # 2. Integrations & Sync
    cat_integrations = KnowledgeBaseCategory(
        name="Integrations & Sync",
        slug="integrations-and-sync",
        description="Connect Google Calendar, configure Webhooks, and sync offline on PWA.",
        display_order=2,
    )
    # 3. Security & Governance
    cat_security = KnowledgeBaseCategory(
        name="Security & Governance",
        slug="security-and-governance",
        description="Configure RFC 6238 TOTP MFA, custom RBAC permissions, and verified domains.",
        display_order=3,
    )
    db.add_all([cat_start, cat_integrations, cat_security])
    db.commit()

    # Articles
    a1 = KnowledgeBaseArticle(
        category_id=cat_start.id,
        title="Mastering FocusBoard Task Lifecycle & Priorities",
        slug="mastering-task-lifecycle",
        content="""## Task Management in FocusBoard
FocusBoard provides three essential status columns:
1. **Todo**: Tasks queued for execution.
2. **In Progress**: Active items currently undergoing focus sessions.
3. **Completed**: Finished tasks automatically tracked for velocity metrics.

### Keyboard Shortcuts
- Press `N` to quickly open the Create Task modal.
- Press `Cmd+K` or `Ctrl+K` to open the Command Palette.
- Press `?` to review all keyboard shortcuts.
""",
        status="PUBLISHED",
        helpful_count=12,
    )

    a2 = KnowledgeBaseArticle(
        category_id=cat_integrations.id,
        title="Connecting Google Calendar for Two-Way Scheduling",
        slug="google-calendar-sync",
        content="""## Google Calendar Sync Guide
1. Navigate to **Integrations** in the main navigation.
2. Under **Google Calendar**, click **Connect Account**.
3. Authorize calendar access via OAuth.
4. Tasks with scheduled due dates will automatically synchronize into your calendar.
""",
        status="PUBLISHED",
        helpful_count=8,
    )

    a3 = KnowledgeBaseArticle(
        category_id=cat_security.id,
        title="Enforcing Enterprise TOTP Multi-Factor Authentication",
        slug="enterprise-totp-mfa",
        content="""## Two-Factor Authentication Setup
FocusBoard utilizes pure RFC 6238 TOTP authentication:
1. Navigate to **Enterprise Admin > Two-Factor Authentication**.
2. Click **Begin MFA Configuration**.
3. Add the secret key or scan the `otpauth://` URI in Google Authenticator or 1Password.
4. Store your 8 emergency backup recovery codes in a secure vault.
5. Enter the 6-digit verification code to activate.
""",
        status="PUBLISHED",
        helpful_count=15,
    )

    db.add_all([a1, a2, a3])

    # Default Roadmap Items
    r1 = ProductRoadmapItem(
        title="Biometric FIDO2 / WebAuthn Passkeys",
        description="Hardware security key authentication alongside existing RFC 6238 TOTP.",
        status="PLANNED",
        category="Security",
        vote_count=24,
    )
    r2 = ProductRoadmapItem(
        title="Multi-Region Active Read Replicas",
        description="Automated geographical routing for global sub-50ms analytics query latency.",
        status="IN_PROGRESS",
        category="Infrastructure",
        vote_count=18,
    )
    r3 = ProductRoadmapItem(
        title="Visual Drag-and-Drop Workflow Canvas",
        description="Interactive visual node editor for automated webhooks and task pipelines.",
        status="PLANNED",
        category="Automations",
        vote_count=32,
    )
    db.add_all([r1, r2, r3])
    db.commit()

def calculate_sla_deadline(priority: str) -> datetime:
    now = utc_now()
    pri = (priority or "NORMAL").upper()
    if pri == "URGENT":
        return now + timedelta(hours=1)
    elif pri == "HIGH":
        return now + timedelta(hours=4)
    elif pri == "LOW":
        return now + timedelta(hours=72)
    return now + timedelta(hours=24) # NORMAL default

def create_support_ticket(
    db: Session,
    user_id: int,
    title: str,
    description: str,
    category: str = "technical_issue",
    priority: str = "NORMAL",
    workspace_id: Optional[int] = None,
) -> SupportTicket:
    ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
    sla = calculate_sla_deadline(priority)

    # Auto-assign to an available admin if present
    admin_user = db.query(User).filter(User.role.in_(["Admin", "Owner"]), User.id != user_id).first()
    agent_id = admin_user.id if admin_user else None

    ticket = SupportTicket(
        id=ticket_id,
        user_id=user_id,
        workspace_id=workspace_id,
        title=title,
        description=description,
        category=category,
        priority=priority.upper(),
        status="OPEN",
        assigned_agent_id=agent_id,
        sla_deadline=sla,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Initial customer message
    msg = SupportMessage(
        ticket_id=ticket.id,
        sender_id=user_id,
        is_internal_note=False,
        message=description,
    )
    db.add(msg)
    db.commit()
    return ticket

def add_ticket_message(
    db: Session,
    ticket_id: str,
    sender_id: int,
    message: str,
    is_internal_note: bool = False,
    is_agent: bool = False,
) -> Optional[SupportMessage]:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        return None

    msg = SupportMessage(
        ticket_id=ticket_id,
        sender_id=sender_id,
        is_internal_note=is_internal_note,
        message=message,
    )
    db.add(msg)

    # If first agent reply, record first_response_at
    if is_agent and not is_internal_note and not ticket.first_response_at:
        ticket.first_response_at = utc_now()
        if ticket.status == "OPEN":
            ticket.status = "IN_PROGRESS"

    ticket.updated_at = utc_now()
    db.commit()
    db.refresh(msg)
    return msg

def list_tickets(
    db: Session,
    user_id: int,
    is_agent_or_admin: bool = False,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
) -> List[SupportTicket]:
    query = db.query(SupportTicket)
    if not is_agent_or_admin:
        query = query.filter(SupportTicket.user_id == user_id)

    if status_filter:
        query = query.filter(SupportTicket.status == status_filter.upper())
    if category_filter:
        query = query.filter(SupportTicket.category == category_filter)

    return query.order_by(SupportTicket.created_at.desc()).all()

def calculate_customer_health_score(db: Session, user_id: int) -> Dict[str, Any]:
    """Computes an explainable, deterministic customer health score based on real activity."""
    total_tasks = db.query(func.count(Task.id)).filter(Task.user_id == user_id).scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.user_id == user_id, Task.status == "Completed").scalar() or 0
    overdue_tasks = db.query(func.count(Task.id)).filter(
        Task.user_id == user_id,
        Task.status != "Completed",
        Task.due_date != None,
        Task.due_date < utc_now().isoformat()
    ).scalar() or 0

    open_urgent_tickets = db.query(func.count(SupportTicket.id)).filter(
        SupportTicket.user_id == user_id,
        SupportTicket.priority.in_(["HIGH", "URGENT"]),
        SupportTicket.status.in_(["OPEN", "IN_PROGRESS", "ESCALATED"])
    ).scalar() or 0

    # Base score: 80
    score = 80
    reasons = []

    if total_tasks > 5:
        score += 10
        reasons.append("High task creation volume (+10)")
    elif total_tasks == 0:
        score -= 20
        reasons.append("No active tasks created (-20)")

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    if completion_rate >= 50:
        score += 10
        reasons.append(f"Strong completion rate of {int(completion_rate)}% (+10)")

    if overdue_tasks > 3:
        score -= 15
        reasons.append(f"{overdue_tasks} overdue tasks accumulated (-15)")

    if open_urgent_tickets > 0:
        score -= 25
        reasons.append(f"{open_urgent_tickets} open high/urgent support ticket(s) (-25)")

    score = max(0, min(100, score))

    if score >= 75:
        status = "HEALTHY"
    elif score >= 50:
        status = "NEEDS_ATTENTION"
    else:
        status = "AT_RISK"

    return {
        "health_status": status,
        "health_score": score,
        "metrics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": int(completion_rate),
            "urgent_tickets": open_urgent_tickets,
        },
        "recommendations": reasons,
    }
