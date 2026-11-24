from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.time_tracking_service import time_tracking_service
from app.schemas.time_tracking import (
    TimerStartRequest,
    ActiveTimerDetail,
    TimeEntryCreate,
    TimeEntryUpdate,
    TimeEntryResponse,
    TimesheetCreate,
    TimesheetReviewRequest,
    TimesheetResponse,
    TimesheetDetailResponse,
    TimeTrackingSummaryResponse,
    ProjectTimeReportItem,
    UserTimeReportItem,
    BillableReportResponse,
    TimeTrackingSettingsUpdate,
    TimeTrackingSettingsResponse,
)

router = APIRouter(prefix="/time-tracking", tags=["Time Tracking & Timesheets"])


# =========================================================================
# 1. Active Timer Endpoints
# =========================================================================

@router.get("/timer/active", response_model=Optional[ActiveTimerDetail])
def get_active_timer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the current active or paused timer for the authenticated user."""
    return time_tracking_service.get_active_timer(db, current_user)


@router.post("/timer/start", response_model=ActiveTimerDetail)
def start_timer(
    payload: TimerStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new running timer or switch tasks."""
    try:
        timer_data = time_tracking_service.start_timer(
            db=db,
            user=current_user,
            project_id=payload.project_id,
            task_id=payload.task_id,
            description=payload.description,
            billable=payload.billable,
        )
        return timer_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timer/pause", response_model=ActiveTimerDetail)
def pause_timer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause the currently running timer."""
    try:
        timer_data = time_tracking_service.pause_timer(db, current_user)
        return timer_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timer/resume", response_model=ActiveTimerDetail)
def resume_timer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused timer."""
    try:
        timer_data = time_tracking_service.resume_timer(db, current_user)
        return timer_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timer/stop", response_model=TimeEntryResponse)
def stop_timer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop active timer and record entry."""
    try:
        entry = time_tracking_service.stop_timer(db, current_user)
        return time_tracking_service.serialize_time_entry(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timer/cancel")
def cancel_timer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel and discard the active timer without saving a time entry."""
    success = time_tracking_service.cancel_timer(db, current_user)
    return {"success": success, "message": "Active timer cancelled and discarded."}


# =========================================================================
# 2. Time Entries Endpoints
# =========================================================================

@router.get("/entries", response_model=List[TimeEntryResponse])
def list_entries(
    project_id: Optional[int] = Query(None),
    task_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List time entries for current user."""
    return time_tracking_service.get_entries(
        db=db,
        user=current_user,
        project_id=project_id,
        task_id=task_id,
        limit=limit,
        offset=offset,
    )


@router.post("/entries", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
def create_manual_entry(
    payload: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a manual time tracking entry."""
    try:
        entry = time_tracking_service.create_manual_entry(
            db=db,
            user=current_user,
            data=payload.model_dump(),
        )
        return time_tracking_service.serialize_time_entry(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/entries/{entry_id}", response_model=TimeEntryResponse)
def update_entry(
    entry_id: int,
    payload: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update time entry (forbidden if attached to approved timesheet)."""
    try:
        entry = time_tracking_service.update_entry(
            db=db,
            user=current_user,
            entry_id=entry_id,
            data=payload.model_dump(exclude_unset=True),
        )
        return time_tracking_service.serialize_time_entry(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete time entry (forbidden if attached to approved timesheet)."""
    try:
        time_tracking_service.delete_entry(
            db=db,
            user=current_user,
            entry_id=entry_id,
        )
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 3. Timesheet Endpoints
# =========================================================================

@router.get("/timesheets", response_model=List[TimesheetResponse])
def list_timesheets(
    status_filter: Optional[str] = Query(None, alias="status"),
    all_team: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List timesheets."""
    return time_tracking_service.get_timesheets(
        db=db,
        user=current_user,
        status=status_filter,
    )


@router.post("/timesheets", response_model=TimesheetResponse)
def get_or_create_timesheet(
    payload: TimesheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get or auto-generate a timesheet for a given period."""
    try:
        timesheet = time_tracking_service.get_or_create_timesheet(
            db=db,
            user=current_user,
            period_start=payload.period_start,
            period_end=payload.period_end,
        )
        return time_tracking_service.serialize_timesheet(timesheet)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/timesheets/{timesheet_id}", response_model=TimesheetDetailResponse)
def get_timesheet_detail(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full timesheet detail including all time entries and approval history."""
    detail = time_tracking_service.get_timesheet_detail(
        db=db,
        timesheet_id=timesheet_id,
        user=current_user,
    )
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found.")
    return detail


@router.post("/timesheets/{timesheet_id}/submit", response_model=TimesheetResponse)
def submit_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a draft timesheet for manager review."""
    try:
        timesheet = time_tracking_service.submit_timesheet(
            db=db,
            user=current_user,
            timesheet_id=timesheet_id,
        )
        return time_tracking_service.serialize_timesheet(timesheet)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timesheets/{timesheet_id}/withdraw", response_model=TimesheetResponse)
def withdraw_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Withdraw a submitted timesheet back to draft status."""
    try:
        timesheet = time_tracking_service.withdraw_timesheet(
            db=db,
            user=current_user,
            timesheet_id=timesheet_id,
        )
        return time_tracking_service.serialize_timesheet(timesheet)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timesheets/{timesheet_id}/approve", response_model=TimesheetResponse)
def approve_timesheet(
    timesheet_id: int,
    payload: TimesheetReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a submitted timesheet (Manager or Admin role required)."""
    if current_user.role not in ["ADMIN", "OWNER", "MANAGER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager or Admin permissions required.")
    try:
        timesheet = time_tracking_service.review_timesheet(
            db=db,
            reviewer=current_user,
            timesheet_id=timesheet_id,
            decision="APPROVED",
            comments=payload.review_comments,
        )
        return time_tracking_service.serialize_timesheet(timesheet)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timesheets/{timesheet_id}/reject", response_model=TimesheetResponse)
def reject_timesheet(
    timesheet_id: int,
    payload: TimesheetReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a submitted timesheet with feedback comments."""
    if current_user.role not in ["ADMIN", "OWNER", "MANAGER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager or Admin permissions required.")
    try:
        timesheet = time_tracking_service.review_timesheet(
            db=db,
            reviewer=current_user,
            timesheet_id=timesheet_id,
            decision="REJECTED",
            comments=payload.review_comments,
        )
        return time_tracking_service.serialize_timesheet(timesheet)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/timesheets/{timesheet_id}/reopen", response_model=TimesheetResponse)
def reopen_timesheet(
    timesheet_id: int,
    payload: TimesheetReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reopen an approved or rejected timesheet back to draft."""
    if current_user.role not in ["ADMIN", "OWNER", "MANAGER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager or Admin permissions required.")
    try:
        timesheet = time_tracking_service.review_timesheet(
            db=db,
            reviewer=current_user,
            timesheet_id=timesheet_id,
            decision="REOPENED",
            comments=payload.review_comments,
        )
        return time_tracking_service.serialize_timesheet(timesheet)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 4. Analytics & Reports Endpoints
# =========================================================================

@router.get("/summary", response_model=TimeTrackingSummaryResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get high-level time tracking dashboard KPIs for current user."""
    return time_tracking_service.get_summary(db, current_user)


@router.get("/reports/project", response_model=List[ProjectTimeReportItem])
def get_project_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get breakdown of time logged by project."""
    return time_tracking_service.get_project_reports(db, current_user)


@router.get("/reports/user", response_model=List[UserTimeReportItem])
def get_user_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get team member time breakdown (Managers/Admins only)."""
    if current_user.role not in ["ADMIN", "OWNER", "MANAGER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager permissions required.")
    return time_tracking_service.get_user_reports(db, current_user)


@router.get("/reports/billable", response_model=BillableReportResponse)
def get_billable_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get billable vs non-billable revenue and hours report."""
    return time_tracking_service.get_billable_report(db, current_user)


# =========================================================================
# 5. Settings Endpoints
# =========================================================================

@router.get("/settings", response_model=TimeTrackingSettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve time tracking preferences and rules."""
    s = time_tracking_service.get_or_create_settings(db, current_user)
    return time_tracking_service.serialize_settings(s)


@router.put("/settings", response_model=TimeTrackingSettingsResponse)
def update_settings(
    payload: TimeTrackingSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update time tracking preferences."""
    if current_user.role not in ["ADMIN", "OWNER", "MANAGER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    s = time_tracking_service.update_settings(
        db=db,
        user=current_user,
        data=payload.model_dump(exclude_unset=True),
    )
    return time_tracking_service.serialize_settings(s)
