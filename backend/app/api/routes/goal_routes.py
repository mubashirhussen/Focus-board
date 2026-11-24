"""
FocusBoard Goals, OKRs & Milestones API Routes (Module B50).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.models.goals import (
    Goal,
    KeyResult,
    KeyResultProgressHistory,
    GoalMilestone,
    MilestoneDependency,
    GoalProjectLink,
    KeyResultTaskLink,
    GoalCheckIn,
    GoalComment,
    GoalSettings,
)
from app.services import goal_service
from app.schemas.goals import (
    GoalCreate,
    GoalUpdate,
    GoalStatusTransition,
    KeyResultCreate,
    KeyResultUpdate,
    KeyResultProgressUpdate,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneDependencyCreate,
    GoalCheckInCreate,
    GoalCheckInReview,
    GoalProjectLinkCreate,
    KeyResultTaskLinkCreate,
    GoalCommentCreate,
    GoalSettingsUpdate,
)

router = APIRouter(prefix="/goals", tags=["Goals, OKRs & Milestones"])


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except Exception:
            return None


# =========================================================================
# 1. Analytics & Overview Endpoints
# =========================================================================

@router.get("/analytics/overview")
def get_goals_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve high-level organizational OKR and milestone KPIs."""
    org_id = current_user.organization_id if hasattr(current_user, "organization_id") else None
    return goal_service.get_goals_overview_metrics(db, org_id)


# =========================================================================
# 2. Goal Endpoints
# =========================================================================

@router.get("")
def list_goals(
    goal_level: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    health_status: Optional[str] = None,
    team_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List goals with multi-faceted filtering."""
    org_id = getattr(current_user, "organization_id", None)
    query = db.query(Goal)

    if org_id:
        query = query.filter(or_(Goal.organization_id == org_id, Goal.organization_id.is_(None)))

    if goal_level:
        query = query.filter(Goal.goal_level == goal_level.upper())
    if status_filter:
        query = query.filter(Goal.status == status_filter.upper())
    if health_status:
        query = query.filter(Goal.health_status == health_status.upper())
    if team_id:
        query = query.filter(Goal.team_id == team_id)
    if owner_id:
        query = query.filter(Goal.owner_id == owner_id)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(Goal.title.ilike(s), Goal.description.ilike(s)))

    total = query.count()
    items = query.order_by(desc(Goal.created_at)).offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [goal_service.serialize_goal(g) for g in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new strategic, team, or individual goal."""
    org_id = getattr(current_user, "organization_id", None)
    data = payload.model_dump()
    data["start_date"] = parse_date(data.get("start_date"))
    data["target_date"] = parse_date(data.get("target_date"))

    try:
        goal = goal_service.create_goal(db, data, user_id=current_user.id, org_id=org_id)
        return goal_service.serialize_goal(goal)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{goal_id}")
def get_goal_detail(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve complete goal hierarchy, key results, milestones, and check-ins."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    # Re-evaluate live progress and health on view
    goal_service.recalculate_goal_progress(db, goal)
    db.commit()
    db.refresh(goal)

    base = goal_service.serialize_goal(goal)

    # Subgoals
    subgoals = db.query(Goal).filter(Goal.parent_goal_id == goal_id).all()
    base["subgoals"] = [goal_service.serialize_goal(sg) for sg in subgoals]

    # Key Results
    krs = db.query(KeyResult).filter(KeyResult.goal_id == goal_id).all()
    base["key_results"] = [
        {
            "id": kr.id,
            "goal_id": kr.goal_id,
            "title": kr.title,
            "description": kr.description,
            "measurement_type": kr.measurement_type,
            "starting_value": kr.starting_value,
            "current_value": kr.current_value,
            "target_value": kr.target_value,
            "unit": kr.unit,
            "progress_percent": kr.progress_percent,
            "weight": kr.weight,
            "status": kr.status,
            "tracking_method": kr.tracking_method,
            "due_date": kr.due_date.isoformat() if kr.due_date else None,
            "last_updated_at": kr.last_updated_at.isoformat() if kr.last_updated_at else None,
            "owner_id": kr.owner_id,
        }
        for kr in krs
    ]

    # Milestones
    milestones = db.query(GoalMilestone).filter(GoalMilestone.goal_id == goal_id).all()
    base["milestones"] = [
        {
            "id": m.id,
            "goal_id": m.goal_id,
            "key_result_id": m.key_result_id,
            "project_id": m.project_id,
            "title": m.title,
            "description": m.description,
            "status": m.status,
            "priority": m.priority,
            "progress_percent": m.progress_percent,
            "start_date": m.start_date.isoformat() if m.start_date else None,
            "due_date": m.due_date.isoformat() if m.due_date else None,
            "completed_date": m.completed_date.isoformat() if m.completed_date else None,
            "blocked_reason": m.blocked_reason,
            "notes": m.notes,
        }
        for m in milestones
    ]

    # Project Links
    plinks = db.query(GoalProjectLink).filter(GoalProjectLink.goal_id == goal_id).all()
    base["project_links"] = [
        {
            "id": pl.id,
            "project_id": pl.project_id,
            "project_name": pl.project.name if pl.project else None,
            "created_at": pl.created_at.isoformat() if pl.created_at else None,
        }
        for pl in plinks
    ]

    # Check-ins
    check_ins = db.query(GoalCheckIn).filter(GoalCheckIn.goal_id == goal_id).order_by(desc(GoalCheckIn.created_at)).all()
    base["check_ins"] = [
        {
            "id": c.id,
            "user_id": c.user_id,
            "user_name": c.user.name if c.user else None,
            "progress_percent": c.progress_percent,
            "confidence_score": c.confidence_score,
            "summary": c.summary,
            "blockers": c.blockers,
            "next_steps": c.next_steps,
            "support_needed": c.support_needed,
            "status": c.status,
            "reviewer_feedback": c.reviewer_feedback,
            "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in check_ins
    ]

    # Comments
    comments = db.query(GoalComment).filter(GoalComment.goal_id == goal_id).order_by(desc(GoalComment.created_at)).all()
    base["comments"] = [
        {
            "id": cm.id,
            "user_id": cm.user_id,
            "user_name": cm.user.name if cm.user else None,
            "content": cm.content,
            "created_at": cm.created_at.isoformat() if cm.created_at else None,
        }
        for cm in comments
    ]

    return base


@router.put("/{goal_id}")
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update goal configuration."""
    org_id = getattr(current_user, "organization_id", None)
    data = payload.model_dump(exclude_unset=True)
    if "start_date" in data:
        data["start_date"] = parse_date(data["start_date"])
    if "target_date" in data:
        data["target_date"] = parse_date(data["target_date"])

    try:
        updated = goal_service.update_goal(db, goal_id, data, user_id=current_user.id, org_id=org_id)
        return goal_service.serialize_goal(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a goal and its associated child records."""
    org_id = getattr(current_user, "organization_id", None)
    success = goal_service.delete_goal(db, goal_id, org_id=org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return {"status": "success", "message": f"Goal '{goal_id}' deleted."}


@router.post("/{goal_id}/status")
def transition_goal_status(
    goal_id: str,
    payload: GoalStatusTransition,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition goal status through lifecycle."""
    try:
        goal = goal_service.transition_goal_status(
            db, goal_id, payload.status, user_id=current_user.id, reason=payload.reason
        )
        return goal_service.serialize_goal(goal)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Explicit lifecycle transition routes
@router.post("/{goal_id}/activate")
def activate_goal(goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return goal_service.transition_goal_status(db, goal_id, "ACTIVE", user_id=current_user.id)


@router.post("/{goal_id}/complete")
def complete_goal(goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return goal_service.transition_goal_status(db, goal_id, "COMPLETED", user_id=current_user.id)


@router.post("/{goal_id}/cancel")
def cancel_goal(goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return goal_service.transition_goal_status(db, goal_id, "CANCELLED", user_id=current_user.id)


@router.post("/{goal_id}/archive")
def archive_goal(goal_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return goal_service.transition_goal_status(db, goal_id, "ARCHIVED", user_id=current_user.id)


# =========================================================================
# 3. Key Results Endpoints
# =========================================================================

@router.post("/{goal_id}/key-results", status_code=status.HTTP_201_CREATED)
def create_key_result(
    goal_id: str,
    payload: KeyResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a measurable key result to a goal."""
    org_id = getattr(current_user, "organization_id", None)
    data = payload.model_dump()
    data["due_date"] = parse_date(data.get("due_date"))

    try:
        kr = goal_service.create_key_result(db, goal_id, data, user_id=current_user.id, org_id=org_id)
        return {
            "id": kr.id,
            "goal_id": kr.goal_id,
            "title": kr.title,
            "measurement_type": kr.measurement_type,
            "starting_value": kr.starting_value,
            "current_value": kr.current_value,
            "target_value": kr.target_value,
            "unit": kr.unit,
            "progress_percent": kr.progress_percent,
            "status": kr.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/key-results/{key_result_id}/progress")
def update_key_result_progress(
    key_result_id: str,
    payload: KeyResultProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current value of a key result and log an audit history record."""
    try:
        kr = goal_service.update_key_result_progress(
            db, key_result_id, payload.current_value, user_id=current_user.id, comment=payload.comment
        )
        return {
            "id": kr.id,
            "current_value": kr.current_value,
            "progress_percent": kr.progress_percent,
            "status": kr.status,
            "last_updated_at": kr.last_updated_at.isoformat() if kr.last_updated_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/key-results/{key_result_id}/history")
def get_key_result_history(
    key_result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit trail of progress snapshots for a key result."""
    history = db.query(KeyResultProgressHistory).filter(
        KeyResultProgressHistory.key_result_id == key_result_id
    ).order_by(desc(KeyResultProgressHistory.created_at)).all()

    return [
        {
            "id": h.id,
            "previous_value": h.previous_value,
            "new_value": h.new_value,
            "previous_progress": h.previous_progress,
            "new_progress": h.new_progress,
            "update_source": h.update_source,
            "comment": h.comment,
            "user_name": h.user.name if h.user else None,
            "created_at": h.created_at.isoformat(),
        }
        for h in history
    ]


@router.delete("/key-results/{key_result_id}")
def delete_key_result(
    key_result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a key result and recalculate parent goal."""
    kr = db.query(KeyResult).filter(KeyResult.id == key_result_id).first()
    if not kr:
        raise HTTPException(status_code=404, detail="Key result not found.")

    goal_id = kr.goal_id
    db.delete(kr)
    db.commit()

    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if goal:
        goal_service.recalculate_goal_progress(db, goal)
        db.commit()

    return {"status": "success", "message": f"Key result '{key_result_id}' deleted."}


# =========================================================================
# 4. Milestone Endpoints
# =========================================================================

@router.get("/milestones/list")
def list_milestones(
    goal_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List milestones across goals or for a specific goal."""
    org_id = getattr(current_user, "organization_id", None)
    query = db.query(GoalMilestone)

    if org_id:
        query = query.filter(or_(GoalMilestone.organization_id == org_id, GoalMilestone.organization_id.is_(None)))
    if goal_id:
        query = query.filter(GoalMilestone.goal_id == goal_id)
    if status_filter:
        query = query.filter(GoalMilestone.status == status_filter.upper())

    milestones = query.order_by(GoalMilestone.due_date).all()
    return [
        {
            "id": m.id,
            "goal_id": m.goal_id,
            "goal_title": m.goal.title if m.goal else None,
            "title": m.title,
            "status": m.status,
            "priority": m.priority,
            "progress_percent": m.progress_percent,
            "due_date": m.due_date.isoformat() if m.due_date else None,
            "blocked_reason": m.blocked_reason,
        }
        for m in milestones
    ]


@router.post("/{goal_id}/milestones", status_code=status.HTTP_201_CREATED)
def create_milestone(
    goal_id: str,
    payload: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a milestone to a goal."""
    org_id = getattr(current_user, "organization_id", None)
    data = payload.model_dump()
    data["start_date"] = parse_date(data.get("start_date"))
    data["due_date"] = parse_date(data.get("due_date"))

    try:
        m = goal_service.create_milestone(db, goal_id, data, user_id=current_user.id, org_id=org_id)
        return {
            "id": m.id,
            "goal_id": m.goal_id,
            "title": m.title,
            "status": m.status,
            "progress_percent": m.progress_percent,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/milestones/{milestone_id}/complete")
def complete_milestone(
    milestone_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark milestone as completed with dependency validation."""
    try:
        m = goal_service.complete_milestone(db, milestone_id, user_id=current_user.id)
        return {"id": m.id, "status": m.status, "completed_date": m.completed_date.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/milestones/{milestone_id}/reopen")
def reopen_milestone(
    milestone_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reopen a completed milestone."""
    try:
        m = goal_service.reopen_milestone(db, milestone_id, user_id=current_user.id)
        return {"id": m.id, "status": m.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/milestones/{milestone_id}/dependencies")
def add_milestone_dependency(
    milestone_id: str,
    payload: MilestoneDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a prerequisite dependency to a milestone with cycle detection."""
    try:
        goal_service.validate_milestone_dependency(db, milestone_id, payload.depends_on_milestone_id)
        dep = MilestoneDependency(
            milestone_id=milestone_id,
            depends_on_milestone_id=payload.depends_on_milestone_id,
        )
        db.add(dep)
        db.commit()
        return {"status": "success", "message": "Dependency registered."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/milestones/{milestone_id}")
def delete_milestone(
    milestone_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a milestone and recompute parent goal."""
    m = db.query(GoalMilestone).filter(GoalMilestone.id == milestone_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found.")

    goal_id = m.goal_id
    db.delete(m)
    db.commit()

    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if goal:
        goal_service.recalculate_goal_progress(db, goal)
        db.commit()

    return {"status": "success", "message": f"Milestone '{milestone_id}' deleted."}


# =========================================================================
# 5. Check-In Endpoints
# =========================================================================

@router.post("/{goal_id}/check-ins", status_code=status.HTTP_201_CREATED)
def submit_check_in(
    goal_id: str,
    payload: GoalCheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a periodic goal progress report."""
    try:
        chk = goal_service.submit_goal_check_in(db, goal_id, payload.model_dump(), user_id=current_user.id)
        return {
            "id": chk.id,
            "goal_id": chk.goal_id,
            "progress_percent": chk.progress_percent,
            "confidence_score": chk.confidence_score,
            "summary": chk.summary,
            "status": chk.status,
            "created_at": chk.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-ins/{check_in_id}/review")
def review_check_in(
    check_in_id: str,
    payload: GoalCheckInReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review and provide management feedback on a check-in."""
    try:
        chk = goal_service.review_goal_check_in(db, check_in_id, reviewer_id=current_user.id, feedback=payload.feedback)
        return {
            "id": chk.id,
            "status": chk.status,
            "reviewer_feedback": chk.reviewer_feedback,
            "reviewed_at": chk.reviewed_at.isoformat() if chk.reviewed_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# 6. Linking Endpoints (Projects & Tasks)
# =========================================================================

@router.post("/{goal_id}/projects")
def link_project_to_goal(
    goal_id: str,
    payload: GoalProjectLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Link a project to a goal."""
    try:
        link = goal_service.link_project_to_goal(db, goal_id, payload.project_id)
        return {"status": "success", "id": link.id, "project_id": link.project_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{goal_id}/projects/{project_id}")
def unlink_project_from_goal(
    goal_id: str,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unlink a project from a goal."""
    link = db.query(GoalProjectLink).filter(
        GoalProjectLink.goal_id == goal_id,
        GoalProjectLink.project_id == project_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found.")
    db.delete(link)
    db.commit()
    return {"status": "success", "message": f"Project #{project_id} unlinked from goal."}


@router.post("/key-results/{key_result_id}/tasks")
def link_task_to_key_result(
    key_result_id: str,
    payload: KeyResultTaskLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Connect a task to an automated key result."""
    try:
        link = goal_service.link_task_to_key_result(db, key_result_id, payload.task_id, payload.weight)
        return {"status": "success", "id": link.id, "task_id": link.task_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/key-results/{key_result_id}/tasks/{task_id}")
def unlink_task_from_key_result(
    key_result_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disconnect a task from a key result."""
    link = db.query(KeyResultTaskLink).filter(
        KeyResultTaskLink.key_result_id == key_result_id,
        KeyResultTaskLink.task_id == task_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found.")
    db.delete(link)
    db.commit()

    kr = db.query(KeyResult).filter(KeyResult.id == key_result_id).first()
    if kr:
        goal_service.recalculate_key_result(db, kr)
        goal = db.query(Goal).filter(Goal.id == kr.goal_id).first()
        if goal:
            goal_service.recalculate_goal_progress(db, goal)
        db.commit()

    return {"status": "success", "message": f"Task '{task_id}' unlinked from key result."}


# =========================================================================
# 7. Goal Comments
# =========================================================================

@router.post("/{goal_id}/comments", status_code=status.HTTP_201_CREATED)
def add_goal_comment(
    goal_id: str,
    payload: GoalCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a collaborative discussion comment to a goal."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    comment = GoalComment(
        goal_id=goal_id,
        organization_id=goal.organization_id,
        user_id=current_user.id,
        content=payload.content.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "id": comment.id,
        "goal_id": comment.goal_id,
        "content": comment.content,
        "user_name": current_user.name or current_user.username,
        "created_at": comment.created_at.isoformat(),
    }
