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
    CalendarDataResponse,
    CalendarSummaryResponse,
    RescheduleTaskRequest,
    CalendarTaskItem,
)
from app.schemas.reminder import (
    RecurrenceRuleCreate,
    RecurrenceRuleResponse,
)
from app.api.dependencies import get_current_user
from app.services.google_calendar_service import calendar_service as google_calendar_service
from app.services.calendar_service import calendar_service
from app.services.recurrence_service import recurrence_service

router = APIRouter(prefix="/calendar", tags=["Calendar & Task Scheduling"])

# -------------------------------------------------------------
# Comprehensive Calendar View Endpoints
# -------------------------------------------------------------

@router.get("", response_model=CalendarDataResponse)
def get_calendar_overview(
    view: str = Query("month", description="Calendar view: month, week, day, agenda"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO)"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tz: str = Query("UTC", alias="timezone", description="User local timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full calendar data with tenant scoping and timezone conversion."""
    return calendar_service.get_calendar_data(
        db=db,
        current_user=current_user,
        view=view,
        start_date=start_date,
        end_date=end_date,
        workspace_id=workspace_id,
        project_id=project_id,
        organization_id=organization_id,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        category=category,
        tz_name=tz,
    )

@router.get("/month", response_model=CalendarDataResponse)
def get_month_calendar(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    tz: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Specialized monthly calendar view."""
    return calendar_service.get_calendar_data(
        db=db,
        current_user=current_user,
        view="month",
        start_date=start_date,
        end_date=end_date,
        workspace_id=workspace_id,
        project_id=project_id,
        tz_name=tz,
    )

@router.get("/week", response_model=CalendarDataResponse)
def get_week_calendar(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    tz: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Specialized weekly calendar view."""
    return calendar_service.get_calendar_data(
        db=db,
        current_user=current_user,
        view="week",
        start_date=start_date,
        end_date=end_date,
        workspace_id=workspace_id,
        project_id=project_id,
        tz_name=tz,
    )

@router.get("/day", response_model=CalendarDataResponse)
def get_day_calendar(
    start_date: Optional[datetime] = None,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    tz: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Specialized daily calendar view."""
    return calendar_service.get_calendar_data(
        db=db,
        current_user=current_user,
        view="day",
        start_date=start_date,
        end_date=None,
        workspace_id=workspace_id,
        project_id=project_id,
        tz_name=tz,
    )

@router.get("/agenda", response_model=CalendarDataResponse)
def get_agenda_calendar(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    workspace_id: Optional[int] = None,
    project_id: Optional[int] = None,
    tz: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Specialized agenda chronological calendar view."""
    return calendar_service.get_calendar_data(
        db=db,
        current_user=current_user,
        view="agenda",
        start_date=start_date,
        end_date=end_date,
        workspace_id=workspace_id,
        project_id=project_id,
        tz_name=tz,
    )

@router.get("/summary", response_model=CalendarSummaryResponse)
def get_calendar_summary(
    workspace_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    tz: str = Query("UTC", alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated calendar and deadline metrics."""
    return calendar_service.get_calendar_summary(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
        tz_name=tz,
    )

# -------------------------------------------------------------
# Scheduling & Drag-and-Drop Movement
# -------------------------------------------------------------

@router.post("/reschedule", response_model=CalendarTaskItem)
def reschedule_task(
    req: RescheduleTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Drag-and-drop or programmatic task rescheduling and date adjustment."""
    try:
        return calendar_service.reschedule_task(db, current_user, req)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        elif "unauthorized" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

# -------------------------------------------------------------
# Recurrence Management
# -------------------------------------------------------------

@router.post("/recurrence/{task_id}", response_model=RecurrenceRuleResponse)
def set_task_recurrence(
    task_id: str,
    rule_in: RecurrenceRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Configure recurring pattern (daily, weekly, monthly, yearly) for a task."""
    try:
        rule = recurrence_service.set_task_recurrence(db, current_user, task_id, rule_in)
        return RecurrenceRuleResponse(
            id=rule.id,
            task_id=rule.task_id,
            user_id=rule.user_id,
            organization_id=rule.organization_id,
            frequency=rule.frequency,
            interval=rule.interval,
            weekdays=[],
            month_day=rule.month_day,
            end_date=rule.end_date,
            max_occurrences=rule.max_occurrences,
            occurrences_created=rule.occurrences_created,
            next_run_at=rule.next_run_at,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        elif "unauthorized" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

@router.get("/recurrence/{task_id}", response_model=RecurrenceRuleResponse)
def get_task_recurrence(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve recurring configuration for a task."""
    try:
        rule = recurrence_service.get_task_recurrence(db, current_user, task_id)
        return RecurrenceRuleResponse(
            id=rule.id,
            task_id=rule.task_id,
            user_id=rule.user_id,
            organization_id=rule.organization_id,
            frequency=rule.frequency,
            interval=rule.interval,
            weekdays=[],
            month_day=rule.month_day,
            end_date=rule.end_date,
            max_occurrences=rule.max_occurrences,
            occurrences_created=rule.occurrences_created,
            next_run_at=rule.next_run_at,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/recurrence/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_recurrence(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete recurring configuration for a task."""
    try:
        recurrence_service.delete_task_recurrence(db, current_user, task_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/recurrence/{task_id}/generate-next")
def generate_next_recurrence_instance(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually or worker-triggered generation of the next recurring task occurrence."""
    try:
        new_task = recurrence_service.generate_next_occurrence(db, current_user, task_id)
        return {"status": "success", "new_task_id": new_task.id, "title": new_task.title}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# -------------------------------------------------------------
# Backward-Compatible Endpoints for existing frontend & services
# -------------------------------------------------------------

@router.get("/events", response_model=List[CalendarEventItem])
def get_calendar_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve scheduled tasks and external calendar events for the calendar view."""
    now = datetime.now(timezone.utc)
    s_date = start or (now - timedelta(days=7))
    e_date = end or (now + timedelta(days=30))
    return google_calendar_service.fetch_calendar_events(db, current_user.id, s_date, e_date)

@router.post("/schedule-task", response_model=CalendarEventItem)
def schedule_task(
    req: ScheduleTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Schedule a specific task into a calendar time slot."""
    task = db.query(Task).filter(Task.id == req.task_id).first()
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
        is_completed=(task.status.lower() in ["completed", "done"]),
        priority=task.priority,
        description=task.description,
    )

@router.get("/conflicts", response_model=List[CalendarConflictItem])
def get_calendar_conflicts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze schedule and return any overlapping tasks."""
    return calendar_service.detect_conflicts(db, current_user.id)

@router.post("/sync", response_model=SyncResultResponse)
def trigger_calendar_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger on-demand bidirectional synchronization with Google Calendar."""
    return google_calendar_service.sync_tasks_to_calendar(db, current_user.id)
