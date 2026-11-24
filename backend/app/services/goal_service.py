"""
FocusBoard Goals, OKRs & Milestones Management Service (Module B50).
Provides business logic for goal hierarchies, mathematical OKR key result calculations,
milestone dependencies, task/project linking, check-in workflows, and explainable health evaluations.
"""

from datetime import datetime, timezone, timedelta
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

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
    utc_now,
)
from app.models.task import Task
from app.models.project import Project
from app.models.user import User

logger = logging.getLogger(__name__)


# ============================================================================
# 1. HIERARCHY & CYCLE DETECTION
# ============================================================================

def validate_goal_hierarchy(db: Session, goal_id: Optional[str], parent_goal_id: Optional[str], org_id: Optional[int] = None) -> None:
    """
    Prevents circular goal hierarchies and cross-organization parent-child relationships.
    """
    if not parent_goal_id:
        return
    if goal_id and goal_id == parent_goal_id:
        raise ValueError("A goal cannot be its own parent.")

    parent = db.query(Goal).filter(Goal.id == parent_goal_id).first()
    if not parent:
        raise ValueError("Parent goal does not exist.")

    if org_id is not None and parent.organization_id is not None and parent.organization_id != org_id:
        raise ValueError("Cross-organization goal hierarchy is prohibited.")

    if not goal_id:
        return

    # Traverse upward from parent to check for cycles
    visited = {goal_id}
    curr_id = parent_goal_id
    depth = 0
    max_depth = 20

    while curr_id and depth < max_depth:
        if curr_id in visited:
            raise ValueError("Circular goal hierarchy detected.")
        visited.add(curr_id)
        ancestor = db.query(Goal).filter(Goal.id == curr_id).first()
        if not ancestor or not ancestor.parent_goal_id:
            break
        curr_id = ancestor.parent_goal_id
        depth += 1


def validate_milestone_dependency(db: Session, milestone_id: str, depends_on_id: str) -> None:
    """
    Prevents circular milestone dependency chains and self-dependencies.
    """
    if milestone_id == depends_on_id:
        raise ValueError("A milestone cannot depend on itself.")

    visited = {milestone_id}
    queue = [depends_on_id]

    while queue:
        current = queue.pop(0)
        if current in visited:
            raise ValueError("Circular milestone dependency detected.")
        visited.add(current)
        
        # Find all milestones that `current` depends on
        next_deps = db.query(MilestoneDependency).filter(MilestoneDependency.milestone_id == current).all()
        for d in next_deps:
            queue.append(d.depends_on_milestone_id)


# ============================================================================
# 2. KEY RESULT PROGRESS ENGINE
# ============================================================================

def compute_key_result_progress(
    measurement_type: str,
    starting_value: float,
    target_value: float,
    current_value: float,
    linked_tasks_ratio: Optional[float] = None,
    completed_milestones_ratio: Optional[float] = None,
) -> float:
    """
    Calculates progress percentage across all 7 OKR measurement types.
    Handles division by zero, decreasing targets, and capped/uncapped scenarios safely.
    """
    m_type = measurement_type.upper()

    if m_type == "NUMERIC_INCREASE":
        # Target is higher than start
        denominator = target_value - starting_value
        if denominator == 0:
            return 100.0 if current_value >= target_value else 0.0
        pct = ((current_value - starting_value) / denominator) * 100.0
        return max(0.0, min(100.0, round(pct, 2)))

    elif m_type == "NUMERIC_DECREASE":
        # Lower is better: moving from starting down to target
        denominator = starting_value - target_value
        if denominator == 0:
            return 100.0 if current_value <= target_value else 0.0
        pct = ((starting_value - current_value) / denominator) * 100.0
        return max(0.0, min(100.0, round(pct, 2)))

    elif m_type == "PERCENTAGE":
        denominator = target_value - starting_value
        if denominator == 0:
            return 100.0 if current_value >= target_value else 0.0
        pct = ((current_value - starting_value) / denominator) * 100.0
        return max(0.0, min(100.0, round(pct, 2)))

    elif m_type == "BINARY":
        # Binary completion: target is reached if current >= target or current >= 1.0
        threshold = target_value if target_value > 0 else 1.0
        return 100.0 if current_value >= threshold else 0.0

    elif m_type == "MILESTONE":
        if completed_milestones_ratio is not None:
            return max(0.0, min(100.0, round(completed_milestones_ratio * 100.0, 2)))
        denominator = target_value - starting_value
        if denominator <= 0:
            return 100.0 if current_value >= target_value else 0.0
        return max(0.0, min(100.0, round(((current_value - starting_value) / denominator) * 100.0, 2)))

    elif m_type == "TASK_COMPLETION":
        if linked_tasks_ratio is not None:
            return max(0.0, min(100.0, round(linked_tasks_ratio * 100.0, 2)))
        denominator = target_value - starting_value
        if denominator <= 0:
            return 100.0 if current_value >= target_value else 0.0
        return max(0.0, min(100.0, round(((current_value - starting_value) / denominator) * 100.0, 2)))

    else:  # MANUAL
        denominator = target_value - starting_value
        if denominator == 0:
            return 100.0 if current_value >= target_value else 0.0
        pct = ((current_value - starting_value) / denominator) * 100.0
        return max(0.0, min(100.0, round(pct, 2)))


def recalculate_key_result(db: Session, kr: KeyResult) -> float:
    """
    Evaluates key result progress, taking into account linked tasks and milestones.
    """
    linked_task_ratio = None
    if kr.measurement_type in ("TASK_COMPLETION", "AUTOMATIC"):
        task_links = db.query(KeyResultTaskLink).filter(KeyResultTaskLink.key_result_id == kr.id).all()
        if task_links:
            total_weight = 0.0
            completed_weight = 0.0
            for link in task_links:
                task = db.query(Task).filter(Task.id == link.task_id).first()
                if task:
                    w = link.weight if link.weight > 0 else 1.0
                    total_weight += w
                    is_done = str(task.status).lower() in ("completed", "done") or (task.progress_percent and task.progress_percent >= 100)
                    if is_done:
                        completed_weight += w
                    elif task.progress_percent:
                        completed_weight += w * (task.progress_percent / 100.0)
            if total_weight > 0:
                linked_task_ratio = completed_weight / total_weight
                kr.current_value = round(completed_weight, 2)
                kr.target_value = round(total_weight, 2)

    milestone_ratio = None
    if kr.measurement_type == "MILESTONE":
        milestones = db.query(GoalMilestone).filter(GoalMilestone.key_result_id == kr.id).all()
        if milestones:
            done_count = sum(1 for m in milestones if m.status == "COMPLETED")
            milestone_ratio = done_count / len(milestones)
            kr.current_value = float(done_count)
            kr.target_value = float(len(milestones))

    progress = compute_key_result_progress(
        measurement_type=kr.measurement_type,
        starting_value=kr.starting_value,
        target_value=kr.target_value,
        current_value=kr.current_value,
        linked_tasks_ratio=linked_task_ratio,
        completed_milestones_ratio=milestone_ratio,
    )
    kr.progress_percent = progress
    kr.last_updated_at = utc_now()
    if progress >= 100.0:
        kr.status = "COMPLETED"
    elif progress > 0.0:
        kr.status = "ACTIVE"
    return progress


def recalculate_goal_progress(db: Session, goal: Goal) -> Tuple[float, str, str]:
    """
    Aggregates goal progress from child key results or milestones,
    and updates health classification.
    """
    key_results = db.query(KeyResult).filter(KeyResult.goal_id == goal.id).all()
    
    if key_results:
        total_weight = sum(kr.weight for kr in key_results if kr.weight > 0) or len(key_results)
        weighted_progress = sum(kr.progress_percent * (kr.weight or 1.0) for kr in key_results)
        goal.progress_percent = round(weighted_progress / total_weight, 2)
    else:
        # Fallback to milestones if no key results are defined
        milestones = db.query(GoalMilestone).filter(GoalMilestone.goal_id == goal.id).all()
        if milestones:
            done_count = sum(1 for m in milestones if m.status == "COMPLETED")
            goal.progress_percent = round((done_count / len(milestones)) * 100.0, 2)

    # Health analysis
    health_status, health_reason = evaluate_goal_health(db, goal)
    goal.health_status = health_status
    goal.health_reason = health_reason
    goal.updated_at = utc_now()

    if goal.progress_percent >= 100.0 and goal.status not in ("COMPLETED", "ARCHIVED", "CANCELLED"):
        goal.status = "COMPLETED"
        goal.completed_date = utc_now()

    return goal.progress_percent, health_status, health_reason


# ============================================================================
# 3. EXPLAINABLE HEALTH & RISK DETECTION
# ============================================================================

def evaluate_goal_health(db: Session, goal: Goal) -> Tuple[str, str]:
    """
    Evaluates explainable goal health based on timeline, velocity, milestone blocks, and project health.
    Returns (health_status, health_reason).
    """
    if goal.status == "COMPLETED" or goal.progress_percent >= 100.0:
        return "COMPLETED", "Goal objectives and key results have reached 100% completion."

    if goal.status in ("CANCELLED", "ARCHIVED"):
        return goal.status, f"Goal is currently in {goal.status.lower()} state."

    # Check for blocked milestones
    blocked_ms = db.query(GoalMilestone).filter(
        GoalMilestone.goal_id == goal.id,
        GoalMilestone.status == "BLOCKED"
    ).first()
    if blocked_ms:
        reason = blocked_ms.blocked_reason or "One or more milestones on the critical path are blocked."
        return "AT_RISK", f"Blocked Milestone: '{blocked_ms.title}' — {reason}"

    if not goal.target_date:
        return "INSUFFICIENT_DATA", "Target deadline is not specified for schedule velocity evaluation."

    now = utc_now()
    start = goal.start_date or goal.created_at
    
    # Ensure timezone awareness
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    target = goal.target_date
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)

    total_duration = (target - start).total_seconds()
    if total_duration <= 0:
        if now > target and goal.progress_percent < 100.0:
            days_overdue = max(1, int((now - target).days))
            return "BEHIND", f"Goal is overdue by {days_overdue} day(s) with {goal.progress_percent}% completed."
        return "INSUFFICIENT_DATA", "Target deadline matches or precedes start date."

    elapsed = (now - start).total_seconds()
    if elapsed <= 0:
        return "ON_TRACK", "Goal schedule has not yet begun."

    if now > target:
        days_overdue = max(1, int((now - target).days))
        return "BEHIND", f"Target date passed {days_overdue} day(s) ago; remaining progress is {round(100.0 - goal.progress_percent, 1)}%."

    expected_progress = min(100.0, max(0.0, (elapsed / total_duration) * 100.0))
    progress_gap = expected_progress - goal.progress_percent

    # Significant lag
    if progress_gap >= 30.0:
        return "BEHIND", f"Severe schedule variance: actual progress ({round(goal.progress_percent, 1)}%) trails expected velocity ({round(expected_progress, 1)}%) by {round(progress_gap, 1)}%."
    elif progress_gap >= 15.0:
        return "AT_RISK", f"Moderate schedule variance: progress ({round(goal.progress_percent, 1)}%) is {round(progress_gap, 1)}% behind target curve."

    # Check linked project health if available (B47 integration)
    try:
        from app.models.predictive_intelligence import ProjectHealthSnapshot
        project_links = db.query(GoalProjectLink).filter(GoalProjectLink.goal_id == goal.id).all()
        for link in project_links:
            snap = db.query(ProjectHealthSnapshot).filter(
                ProjectHealthSnapshot.project_id == link.project_id
            ).order_by(desc(ProjectHealthSnapshot.calculated_at)).first()
            if snap and snap.health_status == "CRITICAL":
                return "AT_RISK", f"Linked project #{link.project_id} has critical delivery risk identified by predictive intelligence."
    except Exception as e:
        logger.debug(f"Optional B47 risk check skipped: {e}")

    return "ON_TRACK", f"Progress ({round(goal.progress_percent, 1)}%) is aligned with timeline expectations ({round(expected_progress, 1)}%)."


# ============================================================================
# 4. GOAL CRUD & LIFECYCLE
# ============================================================================

def create_goal(db: Session, data: Dict[str, Any], user_id: int, org_id: Optional[int] = None) -> Goal:
    parent_id = data.get("parent_goal_id")
    validate_goal_hierarchy(db, goal_id=None, parent_goal_id=parent_id, org_id=org_id)

    goal = Goal(
        organization_id=org_id or data.get("organization_id"),
        workspace_id=data.get("workspace_id"),
        team_id=data.get("team_id"),
        parent_goal_id=parent_id,
        owner_id=data.get("owner_id", user_id),
        created_by=user_id,
        title=data["title"].strip(),
        description=data.get("description"),
        goal_level=data.get("goal_level", "ORGANIZATIONAL"),
        status=data.get("status", "ACTIVE"),
        priority=data.get("priority", "HIGH"),
        progress_percent=data.get("progress_percent", 0.0),
        start_date=data.get("start_date") or utc_now(),
        target_date=data.get("target_date"),
        category=data.get("category", "STRATEGY"),
        tags_json=json.dumps(data.get("tags", [])) if isinstance(data.get("tags"), list) else "[]",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    recalculate_goal_progress(db, goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, goal_id: str, data: Dict[str, Any], user_id: int, org_id: Optional[int] = None) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise ValueError(f"Goal '{goal_id}' not found.")
    if org_id and goal.organization_id and goal.organization_id != org_id:
        raise ValueError("Unauthorized cross-organization access.")

    parent_id = data.get("parent_goal_id", goal.parent_goal_id)
    if parent_id != goal.parent_goal_id:
        validate_goal_hierarchy(db, goal_id=goal.id, parent_goal_id=parent_id, org_id=org_id)
        goal.parent_goal_id = parent_id

    for field in ("title", "description", "goal_level", "priority", "status", "category", "team_id", "owner_id", "start_date", "target_date"):
        if field in data and data[field] is not None:
            setattr(goal, field, data[field])

    if "tags" in data and isinstance(data["tags"], list):
        goal.tags_json = json.dumps(data["tags"])

    recalculate_goal_progress(db, goal)
    db.commit()
    db.refresh(goal)
    return goal


def transition_goal_status(db: Session, goal_id: str, new_status: str, user_id: int, reason: Optional[str] = None) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise ValueError(f"Goal '{goal_id}' not found.")

    valid_statuses = ("DRAFT", "ACTIVE", "ON_TRACK", "AT_RISK", "BEHIND", "COMPLETED", "CANCELLED", "ARCHIVED")
    if new_status.upper() not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'. Allowed: {valid_statuses}")

    goal.status = new_status.upper()
    if goal.status == "COMPLETED":
        goal.completed_date = utc_now()
        goal.progress_percent = 100.0
    elif goal.status == "ACTIVE" and goal.completed_date:
        goal.completed_date = None

    if reason:
        goal.health_reason = reason

    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal_id: str, org_id: Optional[int] = None) -> bool:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return False
    if org_id and goal.organization_id and goal.organization_id != org_id:
        raise ValueError("Unauthorized cross-organization deletion.")

    db.delete(goal)
    db.commit()
    return True


# ============================================================================
# 5. KEY RESULTS OPERATIONS
# ============================================================================

def create_key_result(db: Session, goal_id: str, data: Dict[str, Any], user_id: int, org_id: Optional[int] = None) -> KeyResult:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise ValueError(f"Goal '{goal_id}' not found.")

    curr_val = data.get("current_value")
    if curr_val is None:
        curr_val = data.get("starting_value", 0.0)
    starting_val = data.get("starting_value", 0.0)

    kr = KeyResult(
        goal_id=goal_id,
        organization_id=org_id or goal.organization_id,
        owner_id=data.get("owner_id", user_id),
        title=data["title"].strip(),
        description=data.get("description"),
        measurement_type=data.get("measurement_type", "NUMERIC_INCREASE"),
        starting_value=float(starting_val if starting_val is not None else 0.0),
        current_value=float(curr_val if curr_val is not None else 0.0),
        target_value=float(data.get("target_value", 100.0) or 100.0),
        unit=data.get("unit", "%"),
        weight=float(data.get("weight", 1.0) or 1.0),
        tracking_method=data.get("tracking_method", "MANUAL"),
        due_date=data.get("due_date"),
    )
    db.add(kr)
    db.flush()

    progress = recalculate_key_result(db, kr)
    
    # Record initial history entry
    hist = KeyResultProgressHistory(
        key_result_id=kr.id,
        organization_id=kr.organization_id,
        user_id=user_id,
        previous_value=kr.starting_value,
        new_value=kr.current_value,
        previous_progress=0.0,
        new_progress=progress,
        update_source="MANUAL",
        comment="Key result created.",
    )
    db.add(hist)
    
    recalculate_goal_progress(db, goal)
    db.commit()
    db.refresh(kr)
    return kr


def update_key_result_progress(
    db: Session,
    key_result_id: str,
    new_value: float,
    user_id: int,
    comment: Optional[str] = None,
    source: str = "MANUAL",
) -> KeyResult:
    kr = db.query(KeyResult).filter(KeyResult.id == key_result_id).first()
    if not kr:
        raise ValueError(f"Key result '{key_result_id}' not found.")

    prev_val = kr.current_value
    prev_prog = kr.progress_percent

    kr.current_value = float(new_value)
    new_prog = recalculate_key_result(db, kr)

    hist = KeyResultProgressHistory(
        key_result_id=kr.id,
        organization_id=kr.organization_id,
        user_id=user_id,
        previous_value=prev_val,
        new_value=kr.current_value,
        previous_progress=prev_prog,
        new_progress=new_prog,
        update_source=source,
        comment=comment or f"Progress updated from {prev_val} to {new_value} {kr.unit}.",
    )
    db.add(hist)

    goal = db.query(Goal).filter(Goal.id == kr.goal_id).first()
    if goal:
        recalculate_goal_progress(db, goal)

    db.commit()
    db.refresh(kr)
    return kr


# ============================================================================
# 6. MILESTONE OPERATIONS
# ============================================================================

def create_milestone(db: Session, goal_id: str, data: Dict[str, Any], user_id: int, org_id: Optional[int] = None) -> GoalMilestone:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise ValueError(f"Goal '{goal_id}' not found.")

    m = GoalMilestone(
        goal_id=goal_id,
        key_result_id=data.get("key_result_id"),
        project_id=data.get("project_id"),
        organization_id=org_id or goal.organization_id,
        owner_id=data.get("owner_id", user_id),
        title=data["title"].strip(),
        description=data.get("description"),
        status=data.get("status", "NOT_STARTED"),
        priority=data.get("priority", "MEDIUM"),
        progress_percent=data.get("progress_percent", 0.0),
        start_date=data.get("start_date"),
        due_date=data.get("due_date"),
        notes=data.get("notes"),
    )
    db.add(m)
    db.commit()
    db.refresh(m)

    # If linked to KR, trigger recalculation
    if m.key_result_id:
        kr = db.query(KeyResult).filter(KeyResult.id == m.key_result_id).first()
        if kr:
            recalculate_key_result(db, kr)
    recalculate_goal_progress(db, goal)
    db.commit()
    db.refresh(m)
    return m


def complete_milestone(db: Session, milestone_id: str, user_id: int) -> GoalMilestone:
    m = db.query(GoalMilestone).filter(GoalMilestone.id == milestone_id).first()
    if not m:
        raise ValueError(f"Milestone '{milestone_id}' not found.")

    # Check unmet dependencies
    deps = db.query(MilestoneDependency).filter(MilestoneDependency.milestone_id == milestone_id).all()
    for dep in deps:
        prereq = db.query(GoalMilestone).filter(GoalMilestone.id == dep.depends_on_milestone_id).first()
        if prereq and prereq.status != "COMPLETED":
            raise ValueError(f"Cannot complete milestone: prerequisite '{prereq.title}' is not completed.")

    m.status = "COMPLETED"
    m.progress_percent = 100.0
    m.completed_date = utc_now()
    m.blocked_reason = None

    if m.key_result_id:
        kr = db.query(KeyResult).filter(KeyResult.id == m.key_result_id).first()
        if kr:
            recalculate_key_result(db, kr)

    goal = db.query(Goal).filter(Goal.id == m.goal_id).first()
    if goal:
        recalculate_goal_progress(db, goal)

    db.commit()
    db.refresh(m)
    return m


def reopen_milestone(db: Session, milestone_id: str, user_id: int) -> GoalMilestone:
    m = db.query(GoalMilestone).filter(GoalMilestone.id == milestone_id).first()
    if not m:
        raise ValueError(f"Milestone '{milestone_id}' not found.")

    m.status = "IN_PROGRESS"
    m.progress_percent = 0.0
    m.completed_date = None

    if m.key_result_id:
        kr = db.query(KeyResult).filter(KeyResult.id == m.key_result_id).first()
        if kr:
            recalculate_key_result(db, kr)

    goal = db.query(Goal).filter(Goal.id == m.goal_id).first()
    if goal:
        recalculate_goal_progress(db, goal)

    db.commit()
    db.refresh(m)
    return m


# ============================================================================
# 7. CHECK-INS & REVIEWS
# ============================================================================

def submit_goal_check_in(db: Session, goal_id: str, data: Dict[str, Any], user_id: int) -> GoalCheckIn:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise ValueError(f"Goal '{goal_id}' not found.")

    check_in = GoalCheckIn(
        goal_id=goal_id,
        organization_id=goal.organization_id,
        user_id=user_id,
        progress_percent=float(data.get("progress_percent", goal.progress_percent)),
        confidence_score=int(data.get("confidence_score", 4)),
        summary=data["summary"].strip(),
        blockers=data.get("blockers"),
        next_steps=data.get("next_steps"),
        support_needed=data.get("support_needed"),
        status="SUBMITTED",
    )
    db.add(check_in)

    # Optionally update current goal progress if check-in updates it
    if "progress_percent" in data and float(data["progress_percent"]) != goal.progress_percent:
        goal.progress_percent = float(data["progress_percent"])
        recalculate_goal_progress(db, goal)

    db.commit()
    db.refresh(check_in)
    return check_in


def review_goal_check_in(db: Session, check_in_id: str, reviewer_id: int, feedback: str) -> GoalCheckIn:
    chk = db.query(GoalCheckIn).filter(GoalCheckIn.id == check_in_id).first()
    if not chk:
        raise ValueError(f"Check-in '{check_in_id}' not found.")

    chk.status = "REVIEWED"
    chk.reviewer_id = reviewer_id
    chk.reviewed_at = utc_now()
    chk.reviewer_feedback = feedback.strip()

    db.commit()
    db.refresh(chk)
    return chk


# ============================================================================
# 8. TASK & PROJECT LINKING
# ============================================================================

def link_task_to_key_result(db: Session, key_result_id: str, task_id: str, weight: float = 1.0) -> KeyResultTaskLink:
    kr = db.query(KeyResult).filter(KeyResult.id == key_result_id).first()
    if not kr:
        raise ValueError(f"Key result '{key_result_id}' not found.")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"Task '{task_id}' not found.")

    existing = db.query(KeyResultTaskLink).filter(
        KeyResultTaskLink.key_result_id == key_result_id,
        KeyResultTaskLink.task_id == task_id
    ).first()
    if existing:
        return existing

    link = KeyResultTaskLink(
        key_result_id=key_result_id,
        task_id=task_id,
        organization_id=kr.organization_id,
        weight=weight,
    )
    db.add(link)
    db.flush()

    recalculate_key_result(db, kr)
    goal = db.query(Goal).filter(Goal.id == kr.goal_id).first()
    if goal:
        recalculate_goal_progress(db, goal)

    db.commit()
    db.refresh(link)
    return link


def link_project_to_goal(db: Session, goal_id: str, project_id: int) -> GoalProjectLink:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise ValueError(f"Goal '{goal_id}' not found.")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project '{project_id}' not found.")

    existing = db.query(GoalProjectLink).filter(
        GoalProjectLink.goal_id == goal_id,
        GoalProjectLink.project_id == project_id
    ).first()
    if existing:
        return existing

    link = GoalProjectLink(
        goal_id=goal_id,
        project_id=project_id,
        organization_id=goal.organization_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


# ============================================================================
# 9. ANALYTICS & DASHBOARD AGGREGATION
# ============================================================================

def get_goals_overview_metrics(db: Session, org_id: Optional[int] = None) -> Dict[str, Any]:
    q_goals = db.query(Goal)
    if org_id:
        q_goals = q_goals.filter(or_(Goal.organization_id == org_id, Goal.organization_id.is_(None)))
    goals = q_goals.all()

    q_kr = db.query(KeyResult)
    if org_id:
        q_kr = q_kr.filter(or_(KeyResult.organization_id == org_id, KeyResult.organization_id.is_(None)))
    key_results = q_kr.all()

    q_ms = db.query(GoalMilestone)
    if org_id:
        q_ms = q_ms.filter(or_(GoalMilestone.organization_id == org_id, GoalMilestone.organization_id.is_(None)))
    milestones = q_ms.all()

    now = utc_now()

    total_goals = len(goals)
    active_goals = sum(1 for g in goals if g.status in ("ACTIVE", "ON_TRACK", "AT_RISK", "BEHIND"))
    completed_goals = sum(1 for g in goals if g.status == "COMPLETED" or g.progress_percent >= 100)
    at_risk_goals = sum(1 for g in goals if g.health_status == "AT_RISK")
    behind_goals = sum(1 for g in goals if g.health_status == "BEHIND")

    total_krs = len(key_results)
    completed_krs = sum(1 for kr in key_results if kr.status == "COMPLETED" or kr.progress_percent >= 100)

    total_milestones = len(milestones)
    completed_milestones = sum(1 for m in milestones if m.status == "COMPLETED")
    
    # Milestone deadlines
    upcoming_ms = sum(
        1 for m in milestones
        if m.status != "COMPLETED" and m.due_date and (m.due_date.replace(tzinfo=timezone.utc) if m.due_date.tzinfo is None else m.due_date) >= now
    )
    overdue_ms = sum(
        1 for m in milestones
        if m.status != "COMPLETED" and m.due_date and (m.due_date.replace(tzinfo=timezone.utc) if m.due_date.tzinfo is None else m.due_date) < now
    )

    avg_progress = round(sum(g.progress_percent for g in goals) / total_goals, 1) if total_goals else 0.0

    # Level breakdown
    level_breakdown = {
        "ORGANIZATIONAL": sum(1 for g in goals if g.goal_level == "ORGANIZATIONAL"),
        "TEAM": sum(1 for g in goals if g.goal_level == "TEAM"),
        "INDIVIDUAL": sum(1 for g in goals if g.goal_level == "INDIVIDUAL"),
        "PROJECT": sum(1 for g in goals if g.goal_level == "PROJECT"),
    }

    # Health breakdown
    health_breakdown = {
        "ON_TRACK": sum(1 for g in goals if g.health_status == "ON_TRACK"),
        "AT_RISK": at_risk_goals,
        "BEHIND": behind_goals,
        "COMPLETED": completed_goals,
        "INSUFFICIENT_DATA": sum(1 for g in goals if g.health_status == "INSUFFICIENT_DATA"),
    }

    return {
        "total_goals": total_goals,
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "at_risk_goals": at_risk_goals,
        "behind_goals": behind_goals,
        "total_key_results": total_krs,
        "completed_key_results": completed_krs,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "upcoming_milestones": upcoming_ms,
        "overdue_milestones": overdue_ms,
        "average_progress": avg_progress,
        "level_breakdown": level_breakdown,
        "health_breakdown": health_breakdown,
    }


def serialize_goal(goal: Goal) -> Dict[str, Any]:
    return {
        "id": goal.id,
        "organization_id": goal.organization_id,
        "workspace_id": goal.workspace_id,
        "team_id": goal.team_id,
        "parent_goal_id": goal.parent_goal_id,
        "owner_id": goal.owner_id,
        "created_by": goal.created_by,
        "title": goal.title,
        "description": goal.description,
        "goal_level": goal.goal_level,
        "status": goal.status,
        "health_status": goal.health_status,
        "health_reason": goal.health_reason,
        "priority": goal.priority,
        "progress_percent": goal.progress_percent,
        "start_date": goal.start_date.isoformat() if goal.start_date else None,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "completed_date": goal.completed_date.isoformat() if goal.completed_date else None,
        "category": goal.category,
        "tags": json.loads(goal.tags_json) if goal.tags_json else [],
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
        "key_results_count": len(goal.key_results) if goal.key_results else 0,
        "milestones_count": len(goal.milestones) if goal.milestones else 0,
        "owner_name": goal.owner.name if goal.owner else None,
    }
