from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.support import (
    SupportTicket,
    KnowledgeBaseCategory,
    KnowledgeBaseArticle,
    ProductRoadmapItem,
)
from app.schemas.support import (
    SupportTicketCreate,
    SupportTicketUpdate,
    SupportTicketResponse,
    SupportMessageCreate,
    SupportMessageResponse,
    KnowledgeBaseCategoryResponse,
    KnowledgeBaseArticleResponse,
    ArticleVoteRequest,
    RoadmapItemCreate,
    RoadmapItemResponse,
    CustomerHealthResponse,
)
from app.services import support_service

router = APIRouter(prefix="/support", tags=["Customer Support, Knowledge Base & Success"])

@router.post("/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a support ticket with automatic SLA calculation and agent assignment."""
    ticket = support_service.create_support_ticket(
        db,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category or "technical_issue",
        priority=payload.priority or "NORMAL",
        workspace_id=payload.workspace_id,
    )
    return SupportTicketResponse(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        requester_id=ticket.user_id,
        requester_email=current_user.email,
        assigned_agent_id=ticket.assigned_agent_id,
        sla_deadline=ticket.sla_deadline,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        messages_count=1,
    )

@router.get("/tickets", response_model=List[SupportTicketResponse])
def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List tickets (customers see their own, support agents/admins see all)."""
    is_agent_or_admin = current_user.role in ["Admin", "Owner"]
    tickets = support_service.list_tickets(
        db,
        user_id=current_user.id,
        is_agent_or_admin=is_agent_or_admin,
        status_filter=status_filter,
        category_filter=category_filter,
    )
    return [
        SupportTicketResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            category=t.category,
            priority=t.priority,
            status=t.status,
            requester_id=t.user_id,
            requester_email=t.requester.email if t.requester else None,
            assigned_agent_id=t.assigned_agent_id,
            assigned_agent_name=t.assigned_agent.name if t.assigned_agent else None,
            sla_deadline=t.sla_deadline,
            created_at=t.created_at,
            updated_at=t.updated_at,
            messages_count=len(t.messages),
        )
        for t in tickets
    ]

@router.get("/tickets/{ticket_id}/messages", response_model=List[SupportMessageResponse])
def get_ticket_messages(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ticket message thread. Internal notes are filtered out for regular customers."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    is_agent_or_admin = current_user.role in ["Admin", "Owner"]
    if not is_agent_or_admin and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    messages = ticket.messages
    if not is_agent_or_admin:
        # Filter out internal notes
        messages = [m for m in messages if not m.is_internal_note]

    return [
        SupportMessageResponse(
            id=m.id,
            ticket_id=m.ticket_id,
            sender_id=m.sender_id,
            sender_name=m.sender.name if m.sender else None,
            is_internal_note=m.is_internal_note,
            message=m.message,
            created_at=m.created_at,
        )
        for m in messages
    ]

@router.post("/tickets/{ticket_id}/messages", response_model=SupportMessageResponse, status_code=status.HTTP_201_CREATED)
def reply_to_ticket(
    ticket_id: str,
    payload: SupportMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Post customer reply or agent internal note."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    is_agent_or_admin = current_user.role in ["Admin", "Owner"]
    if not is_agent_or_admin and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if payload.is_internal_note and not is_agent_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support agents or administrators can post internal notes."
        )

    internal = payload.is_internal_note and is_agent_or_admin

    msg = support_service.add_ticket_message(
        db,
        ticket_id=ticket_id,
        sender_id=current_user.id,
        message=payload.message,
        is_internal_note=internal,
        is_agent=is_agent_or_admin,
    )

    return SupportMessageResponse(
        id=msg.id,
        ticket_id=msg.ticket_id,
        sender_id=msg.sender_id,
        sender_name=current_user.name,
        is_internal_note=msg.is_internal_note,
        message=msg.message,
        created_at=msg.created_at,
    )

@router.put("/tickets/{ticket_id}", response_model=SupportTicketResponse)
@router.patch("/tickets/{ticket_id}", response_model=SupportTicketResponse)
def update_ticket_status(
    ticket_id: str,
    payload: SupportTicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update ticket status, priority, or agent assignment."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    is_agent_or_admin = current_user.role in ["Admin", "Owner"]
    if not is_agent_or_admin and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if payload.status:
        ticket.status = payload.status.upper()
        if ticket.status == "RESOLVED" and not ticket.resolved_at:
            ticket.resolved_at = support_service.utc_now()
    if payload.priority and is_agent_or_admin:
        ticket.priority = payload.priority.upper()
    if payload.assigned_agent_id and is_agent_or_admin:
        ticket.assigned_agent_id = payload.assigned_agent_id

    db.commit()
    db.refresh(ticket)

    return SupportTicketResponse(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        requester_id=ticket.user_id,
        assigned_agent_id=ticket.assigned_agent_id,
        sla_deadline=ticket.sla_deadline,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        messages_count=len(ticket.messages),
    )

# Knowledge Base Endpoints
@router.get("/kb/categories", response_model=List[KnowledgeBaseCategoryResponse])
@router.get("/knowledge-base/categories", response_model=List[KnowledgeBaseCategoryResponse])
def get_kb_categories(db: Session = Depends(get_db)):
    """List knowledge base categories with published article counts."""
    support_service.seed_default_knowledge_base(db)
    categories = db.query(KnowledgeBaseCategory).order_by(KnowledgeBaseCategory.display_order).all()
    return [
        KnowledgeBaseCategoryResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            display_order=c.display_order,
            article_count=len([a for a in c.articles if a.status == "PUBLISHED"]),
        )
        for c in categories
    ]

@router.get("/kb/articles", response_model=List[KnowledgeBaseArticleResponse])
@router.get("/knowledge-base/articles", response_model=List[KnowledgeBaseArticleResponse])
def list_kb_articles(
    category_id: Optional[int] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Search and browse published knowledge base articles."""
    support_service.seed_default_knowledge_base(db)
    query = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.status == "PUBLISHED")
    if category_id:
        query = query.filter(KnowledgeBaseArticle.category_id == category_id)
    if q:
        query = query.filter(KnowledgeBaseArticle.title.ilike(f"%{q}%") | KnowledgeBaseArticle.content.ilike(f"%{q}%"))

    articles = query.all()
    return [
        KnowledgeBaseArticleResponse(
            id=a.id,
            category_id=a.category_id,
            title=a.title,
            slug=a.slug,
            content=a.content,
            status=a.status,
            helpful_count=a.helpful_count,
            not_helpful_count=a.not_helpful_count,
            created_at=a.created_at,
        )
        for a in articles
    ]

@router.post("/kb/articles/{article_id}/vote")
@router.post("/knowledge-base/articles/{article_id}/vote")
def vote_kb_article(
    article_id: int,
    payload: ArticleVoteRequest,
    db: Session = Depends(get_db),
):
    """Vote helpful or not helpful on a knowledge base article."""
    article = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")

    if payload.helpful:
        article.helpful_count += 1
    else:
        article.not_helpful_count += 1

    db.commit()
    return {"status": "success", "helpful_count": article.helpful_count, "not_helpful_count": article.not_helpful_count}

# Product Roadmap Endpoints
@router.get("/roadmap", response_model=List[RoadmapItemResponse])
def get_roadmap_items(db: Session = Depends(get_db)):
    """List public product roadmap initiatives."""
    support_service.seed_default_knowledge_base(db)
    items = db.query(ProductRoadmapItem).order_by(ProductRoadmapItem.vote_count.desc()).all()
    return [
        RoadmapItemResponse(
            id=r.id,
            title=r.title,
            description=r.description,
            status=r.status,
            category=r.category,
            vote_count=r.vote_count,
            created_at=r.created_at,
        )
        for r in items
    ]

@router.post("/roadmap/{item_id}/vote")
def upvote_roadmap_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Upvote a roadmap feature request."""
    item = db.query(ProductRoadmapItem).filter(ProductRoadmapItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found.")
    item.vote_count += 1
    db.commit()
    return {"status": "success", "vote_count": item.vote_count}

# Customer Health Score
@router.get("/health-score", response_model=CustomerHealthResponse)
@router.get("/customer-health", response_model=CustomerHealthResponse)
def get_customer_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Explainable customer health score derived from real user workload and tickets."""
    health_data = support_service.calculate_customer_health_score(db, current_user.id)
    return CustomerHealthResponse(**health_data)
