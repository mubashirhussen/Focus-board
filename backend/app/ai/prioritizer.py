from datetime import datetime, timezone
from typing import List
from app.models.task import Task
from app.ai.schemas import TaskPriorityRecommendation

def calculate_priority_score(task: Task, today_str: str) -> dict:
    """
    Deterministic transparent scoring formula:
    - Base Priority: High = 50, Medium = 30, Low = 10
    - Deadline Urgency:
        - Overdue (due < today): +40 points
        - Due Today (due == today): +30 points
        - Due within 3 days: +15 points
        - Otherwise: 0 points
    - Status Momentum:
        - In Progress: +10 points
        - Todo: 0 points
        - Completed: excluded (score 0)
    Returns: { score, urgency, suggested_priority, reason, action }
    """
    if (task.status or "").lower() == "completed":
        return {
            "score": 0,
            "urgency": "Completed",
            "suggested_priority": task.priority or "Medium",
            "reason": "Task is already completed.",
            "action": "Archive or review completed work."
        }

    # 1. Base score
    p_lower = (task.priority or "medium").lower()
    base_score = 50 if p_lower == "high" else (30 if p_lower == "medium" else 10)

    # 2. Due date urgency score
    urgency_score = 0
    urgency_label = "Normal"
    due_reason = ""

    if task.due_date:
        if task.due_date < today_str:
            urgency_score = 40
            urgency_label = "Critical"
            due_reason = f"Deadline was {task.due_date} (Overdue)."
        elif task.due_date == today_str:
            urgency_score = 30
            urgency_label = "High"
            due_reason = "Due today."
        else:
            try:
                task_date = datetime.strptime(task.due_date, "%Y-%m-%d").date()
                curr_date = datetime.strptime(today_str, "%Y-%m-%d").date()
                days_diff = (task_date - curr_date).days
                if 1 <= days_diff <= 3:
                    urgency_score = 15
                    urgency_label = "Moderate"
                    due_reason = f"Due in {days_diff} day{'s' if days_diff > 1 else ''}."
            except ValueError:
                pass

    # 3. Status momentum
    status_score = 10 if (task.status or "").lower() == "in progress" else 0

    total_score = min(100, base_score + urgency_score + status_score)

    # Determine suggested priority
    current_p = task.priority or "Medium"
    suggested_p = current_p
    action = "Work during standard planned schedule."

    if total_score >= 70:
        suggested_p = "High"
        action = "Prioritize immediately in your next focus block."
    elif total_score <= 25 and p_lower != "low":
        suggested_p = "Low"
        action = "Can be safely scheduled after higher priority items."

    reasons = []
    if due_reason:
        reasons.append(due_reason)
    if status_score > 0:
        reasons.append("Currently in progress.")
    reasons.append(f"Base priority is {current_p}.")

    return {
        "score": total_score,
        "urgency": urgency_label,
        "suggested_priority": suggested_p,
        "reason": " ".join(reasons),
        "action": action
    }

def prioritize_tasks(tasks: List[Task]) -> List[TaskPriorityRecommendation]:
    """Score and prioritize a list of user tasks using deterministic rules."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results = []

    for task in tasks:
        if (task.status or "").lower() == "completed":
            continue

        calc = calculate_priority_score(task, today_str)
        results.append(TaskPriorityRecommendation(
            task_id=task.id,
            title=task.title,
            current_priority=task.priority or "Medium",
            suggested_priority=calc["suggested_priority"],
            priority_score=calc["score"],
            urgency=calc["urgency"],
            due_date=task.due_date,
            reason=calc["reason"],
            suggested_action=calc["action"]
        ))

    # Sort descending by priority score
    results.sort(key=lambda r: r.priority_score, reverse=True)
    return results
