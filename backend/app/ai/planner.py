from datetime import datetime, timezone, timedelta
from typing import List
from app.models.task import Task
from app.ai.schemas import DailyPlanRequest, DailyPlanResponse, PlannedTaskItem
from app.ai.prioritizer import prioritize_tasks

def generate_daily_plan(tasks: List[Task], request: DailyPlanRequest) -> DailyPlanResponse:
    """
    Generate an intelligent, bounded daily schedule:
    - Filters incomplete tasks.
    - Orders by priority score and urgency.
    - Allocates realistic time blocks (default 60-90m per task) up to available_hours.
    - Includes planned intervals and rest breaks.
    """
    planning_date = request.planning_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    available_minutes = int(request.available_hours * 60)

    # 1. Prioritize incomplete tasks
    ranked_recommendations = prioritize_tasks(tasks)

    # Filter by category if requested
    if request.preferred_category and request.preferred_category.lower() != "all":
        target_cat = request.preferred_category.lower()
        task_lookup = {t.id: t for t in tasks}
        ranked_recommendations = [
            r for r in ranked_recommendations
            if task_lookup.get(r.task_id) and (task_lookup[r.task_id].category or "").lower() == target_cat
        ]

    task_lookup = {t.id: t for t in tasks}
    recommended_items: List[PlannedTaskItem] = []
    allocated_minutes = 0

    # Start work day at 09:00 AM
    current_time = datetime.strptime(f"{planning_date} 09:00", "%Y-%m-%d %H:%M")

    for rank in ranked_recommendations:
        t = task_lookup.get(rank.task_id)
        if not t:
            continue

        # Estimate task duration: High = 90 min, Medium = 60 min, Low = 45 min
        p_lower = (t.priority or "medium").lower()
        duration = 90 if p_lower == "high" else (60 if p_lower == "medium" else 45)

        if allocated_minutes + duration > available_minutes:
            break

        start_str = current_time.strftime("%H:%M")
        end_time = current_time + timedelta(minutes=duration)
        end_str = end_time.strftime("%H:%M")

        recommended_items.append(PlannedTaskItem(
            task_id=t.id,
            title=t.title,
            category=t.category or "General",
            priority=t.priority or "Medium",
            estimated_minutes=duration,
            time_block=f"{start_str} - {end_str}",
            selection_reason=f"{rank.urgency} urgency ({rank.priority_score} pts): {rank.reason}"
        ))

        allocated_minutes += duration
        # Add 15 min rest transition
        current_time = end_time + timedelta(minutes=15)

    deferred_count = max(0, len(ranked_recommendations) - len(recommended_items))

    assumptions = (
        f"Schedule built for {request.available_hours} hours. "
        f"Tasks estimated conservatively (45-90 min) with 15-minute inter-task breaks. "
        f"All deferred tasks ({deferred_count}) preserved for upcoming work periods."
    )

    breaks = [
        "Take a 15-minute screen-free break between focus blocks.",
        "Include a 45-60 minute mid-day meal interval.",
        "Stay hydrated and review completed tasks at the end of the day."
    ]

    return DailyPlanResponse(
        planning_date=planning_date,
        available_hours=request.available_hours,
        allocated_hours=round(allocated_minutes / 60, 1),
        recommended_tasks=recommended_items,
        deferred_tasks_count=deferred_count,
        planning_assumptions=assumptions,
        break_suggestions=breaks
    )
