from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.task import Task
from app.schemas.calendar import (
    CalendarEventItem,
    ScheduleTaskRequest,
    CalendarConflictItem,
    SyncResultResponse,
)
from app.api.dependencies import get_current_user
from app.services.google_calendar_service import calendar_service
from app.services.calendar_conflict_service import detect_calendar_conflicts

router = APIRouter(prefix="/calendar", tags=["Calendar & Task Scheduling"])

@router.get("/events", response_model=List[CalendarEventItem])
def get_calendar_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve scheduled tasks and external calendar events for the calendar view."""
    now = datetime.now(timezone.utc)
    s_date = start or (now - timedelta(days=7))
    e_date = end or (now + timedelta(days=30))
    return calendar_service.fetch_calendar_events(db, current_user.id, s_date, e_date)

@router.post("/schedule-task", response_model=CalendarEventItem)
def schedule_task(
    req: ScheduleTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule a specific task into a calendar time slot."""
    task = db.query(Task).filter(Task.id == req.task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    duration = req.estimated_duration_minutes or 30
    task.scheduled_start = req.scheduled_start
    task.scheduled_end = req.scheduled_end or (req.scheduled_start + timedelta(minutes=duration))
    task.estimated_duration_minutes = duration

    db.commit()
    db.refresh(task)

    return CalendarEventItem(
        id=f"fb-task-{task.id}",
        title=task.title,
        start=task.scheduled_start,
        end=task.scheduled_end,
        source="focusboard",
        task_id=str(task.id),
        is_completed=(task.status == "Completed"),
        priority=task.priority,
        description=task.description
    )

@router.get("/conflicts", response_model=List[CalendarConflictItem])
def get_calendar_conflicts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze schedule and return any overlapping tasks or outside working hours conflicts."""
    return detect_calendar_conflicts(db, current_user.id)

@router.post("/sync", response_model=SyncResultResponse)
def trigger_calendar_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger on-demand bidirectional synchronization with Google Calendar."""
    return calendar_service.sync_tasks_to_calendar(db, current_user.id)
