from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderSnoozeRequest,
    ReminderProcessResult,
)
from app.api.dependencies import get_current_user
from app.services.reminder_service import reminder_service

router = APIRouter(prefix="/reminders", tags=["Reminders & Notifications"])

@router.get("", response_model=List[ReminderResponse])
def list_user_reminders(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: PENDING, DELIVERED, SNOOZED, CANCELLED, FAILED"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    from_date: Optional[datetime] = Query(None, description="Earliest scheduled date"),
    to_date: Optional[datetime] = Query(None, description="Latest scheduled date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve scheduled reminders for the authenticated user."""
    return reminder_service.list_reminders(
        db=db,
        current_user=current_user,
        status=status_filter,
        task_id=task_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )

@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task or standalone time-based reminder."""
    try:
        return reminder_service.create_reminder(db, current_user, reminder_in)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        elif "unauthorized" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder_by_id(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single reminder enforcing user ownership."""
    try:
        return reminder_service.get_reminder(db, current_user, reminder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    update_in: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update scheduled time, delivery channel, or details for an existing reminder."""
    try:
        return reminder_service.update_reminder(db, current_user, reminder_id, update_in)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete a reminder record (does not delete associated task)."""
    try:
        reminder_service.delete_reminder(db, current_user, reminder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

@router.post("/{reminder_id}/snooze", response_model=ReminderResponse)
def snooze_reminder(
    reminder_id: int,
    snooze_in: ReminderSnoozeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Snooze a reminder by minutes or until a specified datetime."""
    try:
        return reminder_service.snooze_reminder(db, current_user, reminder_id, snooze_in)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

@router.post("/{reminder_id}/acknowledge", response_model=ReminderResponse)
def acknowledge_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge / dismiss a delivered reminder."""
    try:
        return reminder_service.acknowledge_reminder(db, current_user, reminder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

@router.post("/{reminder_id}/cancel", response_model=ReminderResponse)
def cancel_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending or snoozed reminder."""
    try:
        return reminder_service.cancel_reminder(db, current_user, reminder_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

@router.post("/process", response_model=ReminderProcessResult)
def trigger_process_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Background or on-demand worker execution to evaluate and dispatch due reminders."""
    return reminder_service.process_due_reminders(db)
