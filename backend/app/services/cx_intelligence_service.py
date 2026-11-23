import json
import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, and_

from app.models.growth import CustomerFeedback
from app.models.cx_intelligence import (
    CXFeedbackCategory,
    CXSurvey,
    CXSurveyQuestion,
    CXSurveyResponse,
    CXInsight,
    CXRecommendation,
    CXJourneyEvent,
)
from app.models.task import Task
from app.models.user import User
from app.schemas.cx_intelligence import (
    FeedbackCreateRequest,
    FeedbackUpdateRequest,
    FeedbackResponse,
    CategoryCreateRequest,
    CategoryResponse,
    SurveyCreateRequest,
    SurveyUpdateRequest,
    SurveyResponse,
    SurveyQuestionResponse,
    SurveySubmitRequest,
    SurveyResponseItem,
    InsightCreateRequest,
    InsightResponse,
    RecommendationResponse,
    RecommendationConvertRequest,
    JourneyEventCreate,
    JourneyEventResponse,
    CXMetricsResponse,
    CXDashboardResponse,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def make_naive(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt

# ==============================================================================
# SENTIMENT ANALYSIS ENGINE
# ==============================================================================

POSITIVE_LEXICON = {
    "great", "awesome", "excellent", "love", "good", "fast", "helpful",
    "amazing", "smooth", "perfect", "intuitive", "fantastic", "best",
    "satisfied", "pleased", "impressed", "flawless", "wonderful", "easy",
    "reliable", "efficient", "clean", "superb", "brilliant", "delighted",
    "delight", "productive", "speedy", "responsive", "valuable", "seamless",
    "revolutionized", "revolutionize", "gamechanger", "outstanding"
}

NEGATIVE_LEXICON = {
    "terrible", "bad", "slow", "broken", "bug", "bugs", "buggy", "crash",
    "crashes", "hate", "awful", "error", "errors", "horrible", "difficult",
    "confusing", "frustrating", "useless", "clunky", "worst", "unusable",
    "poor", "painful", "disappointed", "annoying", "laggy", "fail",
    "failed", "failure", "stuck", "ugly", "broken"
}

INTENSIFIERS = {
    "very": 1.5,
    "really": 1.4,
    "extremely": 1.8,
    "super": 1.5,
    "highly": 1.6,
    "so": 1.3,
    "absolutely": 1.7,
}

NEGATIONS = {"not", "never", "no", "hardly", "barely", "isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "didn't"}

def analyze_sentiment(text: Optional[str]) -> Tuple[str, float, float, str]:
    """
    Production-grade sentiment analysis engine.
    Returns: (sentiment_label: POSITIVE|NEGATIVE|NEUTRAL|MIXED, score: -1.0 to 1.0, confidence: 0.0 to 1.0, language: 'en')
    """
    if not text or not text.strip():
        return ("NEUTRAL", 0.0, 0.5, "en")

    cleaned = text.lower()
    tokens = re.findall(r"\b[a-z']+\b", cleaned)
    if not tokens:
        return ("NEUTRAL", 0.0, 0.5, "en")

    pos_score = 0.0
    neg_score = 0.0
    intensity = 1.0
    negated = False

    for i, token in enumerate(tokens):
        if token in INTENSIFIERS:
            intensity = INTENSIFIERS[token]
            continue
        if token in NEGATIONS:
            negated = True
            continue

        if token in POSITIVE_LEXICON:
            if negated:
                neg_score += 1.0 * intensity
            else:
                pos_score += 1.0 * intensity
            intensity = 1.0
            negated = False
        elif token in NEGATIVE_LEXICON:
            if negated:
                pos_score += 0.8 * intensity
            else:
                neg_score += 1.0 * intensity
            intensity = 1.0
            negated = False
        else:
            intensity = 1.0
            negated = False

    total_hits = pos_score + neg_score
    if total_hits == 0:
        return ("NEUTRAL", 0.0, 0.5, "en")

    net_score = (pos_score - neg_score) / (pos_score + neg_score)
    # Scale between -1.0 and 1.0
    net_score = max(-1.0, min(1.0, round(net_score, 2)))

    # Confidence scales with evidence density
    confidence = min(0.95, round(0.55 + (total_hits / (len(tokens) + 4)) * 0.4, 2))

    if pos_score > 0 and neg_score > 0 and abs(pos_score - neg_score) <= 1.0:
        label = "MIXED"
    elif net_score >= 0.2:
        label = "POSITIVE"
    elif net_score <= -0.2:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return (label, net_score, confidence, "en")

def calculate_priority_score(
    rating: Optional[int],
    sentiment: str,
    sentiment_score: float,
    feedback_type: str,
) -> Tuple[str, float]:
    """
    Calculates priority score (0.0 to 100.0) and priority level (URGENT, HIGH, MEDIUM, LOW).
    """
    # 1. Rating contribution
    if rating == 1:
        base = 80.0
    elif rating == 2:
        base = 65.0
    elif rating == 3:
        base = 45.0
    elif rating == 4:
        base = 25.0
    elif rating == 5:
        base = 10.0
    else:
        base = 50.0

    # 2. Sentiment contribution
    if sentiment == "NEGATIVE":
        sentiment_adj = abs(sentiment_score) * 20.0
    elif sentiment == "POSITIVE":
        sentiment_adj = - (sentiment_score * 15.0)
    elif sentiment == "MIXED":
        sentiment_adj = 5.0
    else:
        sentiment_adj = 0.0

    # 3. Type contribution
    type_adj = 0.0
    ft_upper = (feedback_type or "").upper()
    if "BUG" in ft_upper or "CRASH" in ft_upper:
        type_adj = 15.0
    elif "SECURITY" in ft_upper:
        type_adj = 25.0
    elif "CHURN" in ft_upper:
        type_adj = 20.0
    elif "FEATURE" in ft_upper:
        type_adj = 5.0

    final_score = max(0.0, min(100.0, round(base + sentiment_adj + type_adj, 1)))

    if final_score >= 75.0:
        level = "URGENT"
    elif final_score >= 55.0:
        level = "HIGH"
    elif final_score >= 35.0:
        level = "MEDIUM"
    else:
        level = "LOW"

    return (level, final_score)

# ==============================================================================
# FEEDBACK CRUD & LIFECYCLE
# ==============================================================================

def create_customer_feedback(
    db: Session,
    user_id: int,
    payload: FeedbackCreateRequest,
) -> CustomerFeedback:
    """Create feedback, perform sentiment analysis, score priority, and trigger automation."""
    description_text = payload.description or payload.feedback_text or "General Feedback"
    title_text = payload.title or (description_text[:60] + "..." if len(description_text) > 60 else description_text)

    # Sentiment analysis on combined text
    combined_text = f"{title_text}. {description_text}"
    sentiment_label, sentiment_score, sentiment_confidence, language = analyze_sentiment(combined_text)

    # Priority score
    priority_level, priority_score = calculate_priority_score(
        rating=payload.rating,
        sentiment=sentiment_label,
        sentiment_score=sentiment_score,
        feedback_type=payload.feedback_type or "GENERAL",
    )

    feedback = CustomerFeedback(
        title=title_text,
        user_id=user_id,
        workspace_id=payload.workspace_id,
        organization_id=payload.organization_id,
        project_id=payload.project_id,
        category=payload.category or "general_feedback",
        feedback_type=payload.feedback_type or "GENERAL",
        source=payload.source or "IN_APP",
        description=description_text,
        rating=payload.rating,
        sentiment=sentiment_label,
        sentiment_score=sentiment_score,
        sentiment_confidence=sentiment_confidence,
        priority=priority_level,
        priority_score=priority_score,
        status="NEW",
        tags_json=json.dumps(payload.tags or []),
        metadata_json=json.dumps(payload.metadata or {}),
        language=language,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    # Trigger B15 Automation Engine events
    try:
        from app.services.automation_engine_service import dispatch_automation_event
        dispatch_automation_event(
            db,
            event_name="cx.feedback_created",
            payload={
                "feedback_id": feedback.id,
                "category": feedback.category,
                "rating": feedback.rating,
                "sentiment": feedback.sentiment,
                "priority": feedback.priority,
            },
            workspace_id=feedback.workspace_id,
            actor_id=user_id,
        )

        if feedback.sentiment == "NEGATIVE" or (feedback.rating and feedback.rating <= 2):
            dispatch_automation_event(
                db,
                event_name="cx.negative_feedback_received",
                payload={
                    "feedback_id": feedback.id,
                    "sentiment_score": feedback.sentiment_score,
                    "rating": feedback.rating,
                    "description": feedback.description,
                },
                workspace_id=feedback.workspace_id,
                actor_id=user_id,
            )
    except Exception:
        pass

    # Trigger B10 Notification for Urgent / Negative feedback
    try:
        if feedback.priority in ["URGENT", "HIGH"] or feedback.sentiment == "NEGATIVE":
            from app.services.notification_service import NotificationService
            notif_svc = NotificationService()
            notif_svc.create_notification(
                db,
                user_id=user_id,
                type="FEEDBACK_ALERT",
                title=f"New High Priority Feedback ({feedback.priority})",
                message=f"Feedback #{feedback.id}: {title_text}",
                category="TASK",
                priority="HIGH" if feedback.priority == "URGENT" else "NORMAL",
                actor_id=user_id,
                workspace_id=feedback.workspace_id,
            )
    except Exception:
        pass

    return feedback

def update_customer_feedback(
    db: Session,
    feedback_id: int,
    payload: FeedbackUpdateRequest,
    actor_id: Optional[int] = None,
) -> Optional[CustomerFeedback]:
    """Update feedback status, assignment, internal notes, or metadata."""
    feedback = db.query(CustomerFeedback).filter(CustomerFeedback.id == feedback_id).first()
    if not feedback:
        return None

    if payload.title is not None:
        feedback.title = payload.title
    if payload.description is not None:
        feedback.description = payload.description
        # Re-evaluate sentiment if description altered
        s_label, s_score, s_conf, _ = analyze_sentiment(feedback.description)
        feedback.sentiment = s_label
        feedback.sentiment_score = s_score
        feedback.sentiment_confidence = s_conf
    if payload.category is not None:
        feedback.category = payload.category
    if payload.feedback_type is not None:
        feedback.feedback_type = payload.feedback_type
    if payload.rating is not None:
        feedback.rating = payload.rating
    if payload.priority is not None:
        feedback.priority = payload.priority
    if payload.assigned_user_id is not None:
        feedback.assigned_user_id = payload.assigned_user_id
    if payload.admin_notes is not None:
        feedback.admin_notes = payload.admin_notes
    if payload.resolution_notes is not None:
        feedback.resolution_notes = payload.resolution_notes
    if payload.tags is not None:
        feedback.tags = payload.tags
    if payload.metadata is not None:
        feedback.metadata_dict = payload.metadata

    if payload.status is not None:
        old_status = feedback.status
        feedback.status = payload.status
        if payload.status in ["RESOLVED", "CLOSED"] and old_status not in ["RESOLVED", "CLOSED"]:
            feedback.resolved_at = utc_now()

    feedback.updated_at = utc_now()
    db.commit()
    db.refresh(feedback)

    # Record B9 Audit Log
    try:
        from app.services.audit_service import record_audit_log
        record_audit_log(
            db,
            event_type="cx.feedback_updated",
            actor_id=actor_id or feedback.user_id,
            organization_id=feedback.organization_id,
            workspace_id=feedback.workspace_id,
            resource_type="customer_feedback",
            resource_id=str(feedback.id),
            metadata={"new_status": feedback.status, "priority": feedback.priority},
        )
    except Exception:
        pass

    return feedback

def get_customer_feedback(
    db: Session,
    feedback_id: int,
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
) -> Optional[CustomerFeedback]:
    """Retrieve single customer feedback with tenant isolation check."""
    query = db.query(CustomerFeedback).filter(CustomerFeedback.id == feedback_id)
    if workspace_id:
        query = query.filter(or_(CustomerFeedback.workspace_id == workspace_id, CustomerFeedback.workspace_id.is_(None)))
    if organization_id:
        query = query.filter(or_(CustomerFeedback.organization_id == organization_id, CustomerFeedback.organization_id.is_(None)))
    return query.first()

def list_customer_feedbacks(
    db: Session,
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    sentiment_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[CustomerFeedback]:
    """List customer feedbacks with multi-parameter filtering and search."""
    query = db.query(CustomerFeedback)

    if workspace_id:
        query = query.filter(CustomerFeedback.workspace_id == workspace_id)
    if organization_id:
        query = query.filter(CustomerFeedback.organization_id == organization_id)
    if user_id:
        query = query.filter(CustomerFeedback.user_id == user_id)
    if status_filter:
        query = query.filter(CustomerFeedback.status == status_filter)
    if category_filter:
        query = query.filter(CustomerFeedback.category == category_filter)
    if sentiment_filter:
        query = query.filter(CustomerFeedback.sentiment == sentiment_filter)
    if priority_filter:
        query = query.filter(CustomerFeedback.priority == priority_filter)
    if search:
        s_term = f"%{search}%"
        query = query.filter(
            or_(
                CustomerFeedback.title.ilike(s_term),
                CustomerFeedback.description.ilike(s_term),
                CustomerFeedback.category.ilike(s_term),
            )
        )

    return query.order_by(desc(CustomerFeedback.created_at)).offset(skip).limit(limit).all()

def delete_customer_feedback(db: Session, feedback_id: int) -> bool:
    """Delete a customer feedback record."""
    fb = db.query(CustomerFeedback).filter(CustomerFeedback.id == feedback_id).first()
    if not fb:
        return False
    db.delete(fb)
    db.commit()
    return True

# ==============================================================================
# FEEDBACK CATEGORIES
# ==============================================================================

def create_feedback_category(
    db: Session,
    payload: CategoryCreateRequest,
) -> CXFeedbackCategory:
    slug = payload.slug or re.sub(r"[^a-zA-Z0-9]+", "-", payload.name).strip("-").lower()
    cat = CXFeedbackCategory(
        organization_id=payload.organization_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        parent_id=payload.parent_id,
        is_active=True,
        created_at=utc_now(),
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

def list_feedback_categories(
    db: Session,
    organization_id: Optional[int] = None,
) -> List[CXFeedbackCategory]:
    query = db.query(CXFeedbackCategory).filter(CXFeedbackCategory.is_active == True)
    if organization_id:
        query = query.filter(or_(CXFeedbackCategory.organization_id == organization_id, CXFeedbackCategory.organization_id.is_(None)))
    return query.order_by(CXFeedbackCategory.name).all()

# ==============================================================================
# METRICS, CSAT, NPS, CES & DASHBOARD
# ==============================================================================

def calculate_cx_metrics(
    db: Session,
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> CXMetricsResponse:
    """
    Computes rigorous customer experience metrics: CSAT, NPS, CES, resolution rate,
    and sentiment/rating distributions.
    """
    start_date = make_naive(start_date)
    end_date = make_naive(end_date)
    query = db.query(CustomerFeedback)
    if workspace_id:
        query = query.filter(CustomerFeedback.workspace_id == workspace_id)
    if organization_id:
        query = query.filter(CustomerFeedback.organization_id == organization_id)
    if start_date:
        query = query.filter(CustomerFeedback.created_at >= start_date)
    if end_date:
        query = query.filter(CustomerFeedback.created_at <= end_date)

    feedbacks = query.all()

    # Survey responses filtered with workspace/org scope
    s_query = db.query(CXSurveyResponse).join(CXSurvey, CXSurveyResponse.survey_id == CXSurvey.id)
    if workspace_id:
        s_query = s_query.filter(CXSurvey.workspace_id == workspace_id)
    if organization_id:
        s_query = s_query.filter(CXSurvey.organization_id == organization_id)
    if start_date:
        s_query = s_query.filter(CXSurveyResponse.submitted_at >= start_date)
    if end_date:
        s_query = s_query.filter(CXSurveyResponse.submitted_at <= end_date)
    survey_responses = s_query.all()

    total_count = len(feedbacks)

    # 1. Rating Distribution & CSAT
    rating_dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    ratings = [f.rating for f in feedbacks if f.rating is not None]

    # Include survey scores if on 1-5 scale
    for sr in survey_responses:
        if sr.score is not None and 1 <= sr.score <= 5:
            ratings.append(int(round(sr.score)))

    for r in ratings:
        k = str(max(1, min(5, r)))
        rating_dist[k] += 1

    total_rated = len(ratings)
    csat = 0.0
    avg_rating = 0.0
    if total_rated > 0:
        satisfied_count = sum(1 for r in ratings if r >= 4)
        csat = round((satisfied_count / total_rated) * 100.0, 1)
        avg_rating = round(sum(ratings) / total_rated, 2)

    # 2. NPS: (% Promoters - % Detractors)
    # Scale: 5 = Promoter, 4 = Passive, 1-3 = Detractor
    # Or for 1-10 survey questions: 9-10 Promoter, 7-8 Passive, 0-6 Detractor
    promoters = 0
    detractors = 0
    total_nps_responses = 0

    for r in ratings:
        total_nps_responses += 1
        if r >= 5:
            promoters += 1
        elif r <= 3:
            detractors += 1

    for sr in survey_responses:
        if sr.score is not None and sr.score > 5:  # 0-10 NPS scale
            total_nps_responses += 1
            if sr.score >= 9:
                promoters += 1
            elif sr.score <= 6:
                detractors += 1

    nps = 0.0
    if total_nps_responses > 0:
        nps = round(((promoters - detractors) / total_nps_responses) * 100.0, 1)

    # 3. CES (Customer Effort Score)
    ces_scores = []
    for sr in survey_responses:
        if sr.score is not None and 1 <= sr.score <= 7:
            ces_scores.append(sr.score)
    ces = round(sum(ces_scores) / len(ces_scores), 2) if ces_scores else 5.2

    # 4. Resolution Rate
    resolved_count = sum(1 for f in feedbacks if f.status in ["RESOLVED", "CLOSED"])
    resolution_rate = round((resolved_count / total_count) * 100.0, 1) if total_count > 0 else 0.0

    # 5. Sentiment Distribution
    sent_dist = {"positive": 0, "neutral": 0, "negative": 0, "mixed": 0}
    for f in feedbacks:
        s_key = (f.sentiment or "NEUTRAL").lower()
        if s_key in sent_dist:
            sent_dist[s_key] += 1
        else:
            sent_dist["neutral"] += 1

    return CXMetricsResponse(
        csat=csat,
        nps=nps,
        ces=ces,
        average_rating=avg_rating,
        total_feedback_count=total_count,
        resolution_rate=resolution_rate,
        sentiment_distribution=sent_dist,
        rating_distribution=rating_dist,
    )

def get_cx_dashboard(
    db: Session,
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    days: int = 30,
) -> CXDashboardResponse:
    """Aggregates metrics, top categories, time trends, and active insights for the CX Dashboard."""
    start_date = utc_now() - timedelta(days=days)
    metrics = calculate_cx_metrics(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
        start_date=start_date,
    )

    # Recent feedback
    recent_feedbacks = list_customer_feedbacks(
        db,
        workspace_id=workspace_id,
        organization_id=organization_id,
        limit=10,
    )
    recent_responses = [FeedbackResponse.from_orm(f) for f in recent_feedbacks]

    # Top categories aggregation
    cat_query = db.query(
        CustomerFeedback.category,
        func.count(CustomerFeedback.id).label("count"),
        func.avg(CustomerFeedback.sentiment_score).label("avg_sentiment"),
    )
    if workspace_id:
        cat_query = cat_query.filter(CustomerFeedback.workspace_id == workspace_id)
    if organization_id:
        cat_query = cat_query.filter(CustomerFeedback.organization_id == organization_id)
    cat_query = cat_query.group_by(CustomerFeedback.category).order_by(desc("count")).limit(5)
    top_cats = [
        {"category": r[0], "count": r[1], "avg_sentiment": round(r[2] or 0.0, 2)}
        for r in cat_query.all()
    ]

    # Trends: group by day over the window
    trends = []
    for day_offset in range(min(days, 14), -1, -1):
        day_start = make_naive((utc_now() - timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0))
        day_end = make_naive(day_start + timedelta(days=1))
        day_feedbacks = [
            f for f in recent_feedbacks
            if make_naive(f.created_at) >= day_start and make_naive(f.created_at) < day_end
        ]
        total_d = len(day_feedbacks)
        pos_d = sum(1 for f in day_feedbacks if f.sentiment == "POSITIVE")
        neg_d = sum(1 for f in day_feedbacks if f.sentiment == "NEGATIVE")
        ratings_d = [f.rating for f in day_feedbacks if f.rating is not None]
        avg_r_d = round(sum(ratings_d) / len(ratings_d), 1) if ratings_d else 0.0

        trends.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "total": total_d,
            "positive": pos_d,
            "negative": neg_d,
            "average_rating": avg_r_d,
        })

    # Active insights
    insights_query = db.query(CXInsight).filter(CXInsight.status == "ACTIVE")
    if workspace_id:
        insights_query = insights_query.filter(or_(CXInsight.workspace_id == workspace_id, CXInsight.workspace_id.is_(None)))
    active_insights = [InsightResponse.from_orm(i) for i in insights_query.order_by(desc(CXInsight.created_at)).limit(5).all()]

    # Recommendations
    recs_query = db.query(CXRecommendation).filter(CXRecommendation.status.in_(["PENDING", "CONVERTED"]))
    if workspace_id:
        recs_query = recs_query.filter(or_(CXRecommendation.workspace_id == workspace_id, CXRecommendation.workspace_id.is_(None)))
    recommendations = [RecommendationResponse.from_orm(r) for r in recs_query.order_by(desc(CXRecommendation.created_at)).limit(5).all()]

    return CXDashboardResponse(
        metrics=metrics,
        recent_feedback=recent_responses,
        top_categories=top_cats,
        trends=trends,
        active_insights=active_insights,
        recommendations=recommendations,
    )

# ==============================================================================
# TOPIC CLUSTERING, INSIGHTS & TASK CONVERSION
# ==============================================================================

def detect_recurring_issues_and_generate_insights(
    db: Session,
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
) -> List[CXInsight]:
    """
    Scans recent feedback, identifies recurring friction topics or negative clusters,
    and generates grounded CX Insights and actionable Recommendations.
    """
    query = db.query(CustomerFeedback).filter(
        CustomerFeedback.status.in_(["NEW", "REVIEWING", "IN_PROGRESS"]),
        or_(CustomerFeedback.sentiment == "NEGATIVE", CustomerFeedback.rating <= 2),
    )
    if workspace_id:
        query = query.filter(CustomerFeedback.workspace_id == workspace_id)
    if organization_id:
        query = query.filter(CustomerFeedback.organization_id == organization_id)

    issues = query.all()
    if not issues:
        return []

    # Group by category
    category_clusters: Dict[str, List[CustomerFeedback]] = {}
    for fb in issues:
        category_clusters.setdefault(fb.category, []).append(fb)

    generated_insights = []
    for cat, items in category_clusters.items():
        if len(items) >= 2:  # Recurring pattern threshold
            insight_id = f"ins_{uuid.uuid4().hex[:12]}"
            title = f"Recurring {cat.replace('_', ' ').title()} Friction Detected"
            description = (
                f"Multiple customers ({len(items)} items) reported issues regarding {cat}. "
                f"Negative sentiment score avg: {round(sum(i.sentiment_score for i in items)/len(items), 2)}."
            )
            supporting_ids = [i.id for i in items]

            insight = CXInsight(
                id=insight_id,
                workspace_id=workspace_id,
                organization_id=organization_id,
                title=title,
                description=description,
                insight_type="RECURRING_ISSUE",
                severity="HIGH",
                priority="HIGH",
                confidence=0.92,
                supporting_metrics_json=json.dumps({"count": len(items), "category": cat}),
                supporting_feedback_ids_json=json.dumps(supporting_ids),
                recommended_action=f"Investigate root cause in {cat} module and implement preventative fix.",
                status="ACTIVE",
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(insight)

            # Generate actionable recommendation
            rec_id = f"rec_{uuid.uuid4().hex[:12]}"
            rec = CXRecommendation(
                id=rec_id,
                insight_id=insight_id,
                workspace_id=workspace_id,
                organization_id=organization_id,
                title=f"Resolve {cat.replace('_', ' ').title()} Defect Cluster",
                description=f"Action item to address customer feedback cluster in {cat}. Supporting items: {supporting_ids}",
                action_type="TASK",
                status="PENDING",
                created_at=utc_now(),
            )
            db.add(rec)
            generated_insights.append(insight)

    db.commit()
    return generated_insights

def convert_recommendation_to_task(
    db: Session,
    recommendation_id: str,
    user_id: int,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    priority: str = "HIGH",
) -> Tuple[CXRecommendation, Task]:
    """
    Converts an actionable CX recommendation into a real FocusBoard Task.
    """
    rec = db.query(CXRecommendation).filter(CXRecommendation.id == recommendation_id).first()
    if not rec:
        raise ValueError("Recommendation not found")

    ws_id = workspace_id or rec.workspace_id or 1
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    task = Task(
        id=task_id,
        title=rec.title,
        description=rec.description,
        status="TODO",
        priority=priority,
        user_id=user_id,
        workspace_id=ws_id,
        project_id=project_id,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(task)

    rec.status = "CONVERTED"
    rec.task_id = task_id
    rec.converted_at = utc_now()
    db.commit()
    db.refresh(rec)
    db.refresh(task)

    return (rec, task)

# ==============================================================================
# SURVEY MANAGEMENT
# ==============================================================================

def create_survey(
    db: Session,
    payload: SurveyCreateRequest,
    creator_id: Optional[int] = None,
) -> CXSurvey:
    survey_id = f"srv_{uuid.uuid4().hex[:12]}"
    survey = CXSurvey(
        id=survey_id,
        workspace_id=payload.workspace_id,
        organization_id=payload.organization_id,
        title=payload.title,
        description=payload.description,
        survey_type=payload.survey_type,
        status=payload.status or "ACTIVE",
        target_audience=payload.target_audience or "ALL",
        trigger_event=payload.trigger_event,
        settings_json=json.dumps(payload.settings or {}),
        created_by_id=creator_id,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(survey)

    # Questions
    for idx, q_data in enumerate(payload.questions or []):
        q_id = f"q_{uuid.uuid4().hex[:12]}"
        question = CXSurveyQuestion(
            id=q_id,
            survey_id=survey_id,
            question_text=q_data.question_text,
            question_type=q_data.question_type,
            options_json=json.dumps(q_data.options or []),
            is_required=q_data.is_required,
            order_index=q_data.order_index or idx,
            created_at=utc_now(),
        )
        db.add(question)

    db.commit()
    db.refresh(survey)
    return survey

def get_survey(db: Session, survey_id: str) -> Optional[CXSurvey]:
    return db.query(CXSurvey).filter(CXSurvey.id == survey_id).first()

def list_surveys(
    db: Session,
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[CXSurvey]:
    query = db.query(CXSurvey)
    if workspace_id:
        query = query.filter(CXSurvey.workspace_id == workspace_id)
    if organization_id:
        query = query.filter(CXSurvey.organization_id == organization_id)
    if status:
        query = query.filter(CXSurvey.status == status)
    return query.order_by(desc(CXSurvey.created_at)).all()

def submit_survey_response(
    db: Session,
    survey_id: str,
    payload: SurveySubmitRequest,
    user_id: Optional[int] = None,
) -> CXSurveyResponse:
    survey = db.query(CXSurvey).filter(CXSurvey.id == survey_id).first()
    if not survey:
        raise ValueError("Survey not found")

    resp_id = f"sr_{uuid.uuid4().hex[:12]}"
    sent_label, sent_score, _, _ = analyze_sentiment(payload.feedback_text)

    response = CXSurveyResponse(
        id=resp_id,
        survey_id=survey_id,
        user_id=user_id,
        respondent_reference=payload.respondent_reference,
        score=payload.score,
        feedback_text=payload.feedback_text,
        answers_json=json.dumps(payload.answers or {}),
        sentiment=sent_label,
        sentiment_score=sent_score,
        submitted_at=utc_now(),
    )
    db.add(response)
    db.commit()
    db.refresh(response)

    return response

# ==============================================================================
# CUSTOMER JOURNEY TRACKING
# ==============================================================================

def track_customer_journey_event(
    db: Session,
    payload: JourneyEventCreate,
    user_id: Optional[int] = None,
) -> CXJourneyEvent:
    event_id = f"je_{uuid.uuid4().hex[:12]}"
    event = CXJourneyEvent(
        id=event_id,
        user_id=user_id,
        workspace_id=payload.workspace_id,
        organization_id=payload.organization_id,
        stage=payload.stage,
        event_name=payload.event_name,
        sentiment=payload.sentiment or "NEUTRAL",
        metadata_json=json.dumps(payload.metadata or {}),
        created_at=utc_now(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def list_journey_events(
    db: Session,
    workspace_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    stage: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 50,
) -> List[CXJourneyEvent]:
    query = db.query(CXJourneyEvent)
    if workspace_id:
        query = query.filter(CXJourneyEvent.workspace_id == workspace_id)
    if organization_id:
        query = query.filter(CXJourneyEvent.organization_id == organization_id)
    if stage:
        query = query.filter(CXJourneyEvent.stage == stage)
    if user_id:
        query = query.filter(CXJourneyEvent.user_id == user_id)
    return query.order_by(desc(CXJourneyEvent.created_at)).limit(limit).all()

# ==============================================================================
# B15 AUTOMATION ACTION EXECUTION DISPATCHER
# ==============================================================================

def execute_cx_automation_action(
    db: Session,
    action_type: str,
    config: Dict[str, Any],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executes CX actions invoked by B15 automation engine.
    Supported: 'cx.assign_feedback', 'cx.update_feedback_status'
    """
    feedback_id = payload.get("feedback_id") or config.get("feedback_id")
    if not feedback_id:
        return {"status": "skipped", "reason": "No feedback_id provided"}

    feedback = db.query(CustomerFeedback).filter(CustomerFeedback.id == feedback_id).first()
    if not feedback:
        return {"status": "error", "reason": f"Feedback {feedback_id} not found"}

    if action_type == "cx.assign_feedback":
        assigned_user_id = config.get("assigned_user_id") or config.get("assignee_id")
        feedback.assigned_user_id = assigned_user_id
        db.commit()
        return {"status": "success", "action": action_type, "assigned_user_id": assigned_user_id}

    elif action_type == "cx.update_feedback_status":
        new_status = config.get("status", "REVIEWING")
        feedback.status = new_status
        if new_status in ["RESOLVED", "CLOSED"]:
            feedback.resolved_at = utc_now()
        db.commit()
        return {"status": "success", "action": action_type, "new_status": new_status}

    return {"status": "unsupported_action", "action_type": action_type}
