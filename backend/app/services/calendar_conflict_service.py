from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.calendar import CalendarConflictItem, CalendarEventItem
from app.services.google_calendar_service import calendar_service

def detect_calendar_conflicts(
    db: Session,
    user_id: int,
    work_start_hour: int = 9,
    work_end_hour: int = 18
) -> List[CalendarConflictItem]:
    """
    Detect overlapping scheduled tasks and tasks scheduled outside working hours.
    """
    conflicts: List[CalendarConflictItem] = []
    now = datetime.now(timezone.utc)
    events = calendar_service.fetch_calendar_events(
        db=db,
        user_id=user_id,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=7)
    )

    # Sort events by start time
    scheduled_events = [e for e in events if not e.is_completed]
    scheduled_events.sort(key=lambda x: x.start)

    # 1. Check working hours constraint
    for evt in scheduled_events:
        if evt.task_id:
            hour = evt.start.hour
            if hour < work_start_hour or hour >= work_end_hour:
                conflicts.append(CalendarConflictItem(
                    task_id=evt.task_id,
                    task_title=evt.title,
                    conflict_type="OUTSIDE_WORKING_HOURS",
                    conflicting_event_title=None,
                    message=f"Task '{evt.title}' is scheduled at {hour}:00, outside configured working hours ({work_start_hour}:00 - {work_end_hour}:00)."
                ))

    # 2. Check overlap between events
    for i in range(len(scheduled_events)):
        current = scheduled_events[i]
        for j in range(i + 1, len(scheduled_events)):
            next_evt = scheduled_events[j]
            # If current ends after next starts, we have a collision
            if current.end > next_evt.start:
                if current.task_id:
                    conflicts.append(CalendarConflictItem(
                        task_id=current.task_id,
                        task_title=current.title,
                        conflict_type="OVERLAP",
                        conflicting_event_title=next_evt.title,
                        message=f"Collision detected: '{current.title}' overlaps with '{next_evt.title}'."
                    ))
            else:
                break

    return conflicts
