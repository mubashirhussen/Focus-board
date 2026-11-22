from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.notification import Notification, NotificationPreference
from app.schemas.notification import (
    NotificationResponse,
    UnreadCountResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.api.dependencies import get_current_user
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications & Reminders"])

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve notifications belonging strictly to the authenticated user."""
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status != "CANCELLED"
    )

    if unread_only:
        query = query.filter(Notification.read_at == None)

    return query.order_by(Notification.created_at.desc()).limit(limit).all()

@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return the unread notification count for badge rendering."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at == None,
        Notification.status != "CANCELLED"
    ).count()
    return {"unread_count": count}

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an individual notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    if not notif.read_at:
        notif.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notif)
    return notif

@router.patch("/read-all", status_code=status.HTTP_200_OK)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all unread notifications as read for current user."""
    now = datetime.now(timezone.utc)
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at == None
    ).update({"read_at": now}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read."}

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification owned by the authenticated user."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    db.delete(notif)
    db.commit()
    return None

@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve notification configuration preferences."""
    return notification_service.get_or_create_preferences(db, current_user.id)

@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    pref_update: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update notification channel and frequency preferences."""
    pref = notification_service.get_or_create_preferences(db, current_user.id)

    if pref_update.enable_in_app is not None:
        pref.enable_in_app = pref_update.enable_in_app
    if pref_update.enable_email is not None:
        pref.enable_email = pref_update.enable_email
    if pref_update.enable_due_soon is not None:
        pref.enable_due_soon = pref_update.enable_due_soon
    if pref_update.enable_overdue is not None:
        pref.enable_overdue = pref_update.enable_overdue
    if pref_update.enable_daily_plan is not None:
        pref.enable_daily_plan = pref_update.enable_daily_plan
    if pref_update.daily_reminder_time is not None:
        pref.daily_reminder_time = pref_update.daily_reminder_time
    if pref_update.timezone is not None:
        pref.timezone = pref_update.timezone

    db.commit()
    db.refresh(pref)
    return pref

@router.post("/trigger-check", response_model=List[NotificationResponse])
def trigger_deadline_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually or periodically trigger task reminder checks for the authenticated user."""
    created = notification_service.check_and_generate_task_reminders(db, current_user.id)
    return created
