import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.notification import Notification, NotificationPreference
from app.schemas.notification import (
    NotificationResponse,
    NotificationCreateRequest,
    NotificationSummaryResponse,
    UnreadCountResponse,
    BulkNotificationActionRequest,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.api.dependencies import get_current_user
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications & Reminders"])

# -------------------------------------------------------------
# Static collection endpoints (Must come before /{notification_id})
# -------------------------------------------------------------

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    category: Optional[str] = Query(None, description="Filter by category (TASK, PROJECT, TEAM, etc.)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, NORMAL, HIGH, URGENT)"),
    is_archived: bool = Query(False, description="Filter by archived state"),
    search: Optional[str] = Query(None, description="Search keyword in title or message"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve notifications belonging strictly to the authenticated user with filtering."""
    return notification_service.list_notifications(
        db=db,
        user_id=current_user.id,
        category=category,
        priority=priority,
        unread_only=unread_only,
        is_archived=is_archived,
        search=search,
        skip=skip,
        limit=limit,
    )

@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return the unread notification count for badge rendering."""
    summary = notification_service.get_summary(db, current_user.id)
    return {"unread_count": summary["unread_count"]}

@router.get("/summary", response_model=NotificationSummaryResponse)
def get_notification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return comprehensive notification summary counts and category/priority breakdown."""
    return notification_service.get_summary(db, current_user.id)

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
    if pref_update.enable_push is not None:
        pref.enable_push = pref_update.enable_push
    if pref_update.enable_due_soon is not None:
        pref.enable_due_soon = pref_update.enable_due_soon
    if pref_update.enable_overdue is not None:
        pref.enable_overdue = pref_update.enable_overdue
    if pref_update.enable_daily_plan is not None:
        pref.enable_daily_plan = pref_update.enable_daily_plan
    if pref_update.enable_task_assigned is not None:
        pref.enable_task_assigned = pref_update.enable_task_assigned
    if pref_update.enable_comments is not None:
        pref.enable_comments = pref_update.enable_comments
    if pref_update.enable_mentions is not None:
        pref.enable_mentions = pref_update.enable_mentions
    if pref_update.enable_project_updates is not None:
        pref.enable_project_updates = pref_update.enable_project_updates
    if pref_update.enable_team_updates is not None:
        pref.enable_team_updates = pref_update.enable_team_updates
    if pref_update.enable_invitations is not None:
        pref.enable_invitations = pref_update.enable_invitations
    if pref_update.daily_reminder_time is not None:
        pref.daily_reminder_time = pref_update.daily_reminder_time
    if pref_update.timezone is not None:
        pref.timezone = pref_update.timezone
    if pref_update.category_overrides is not None:
        pref.category_overrides = pref_update.category_overrides

    db.commit()
    db.refresh(pref)
    return pref

@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notif_in: NotificationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a notification for current user."""
    notif = notification_service.create_notification(
        db=db,
        user_id=current_user.id,
        type=notif_in.type,
        title=notif_in.title,
        message=notif_in.message,
        category=notif_in.category or "TASK",
        priority=notif_in.priority or "NORMAL",
        actor_id=current_user.id,
        entity_type=notif_in.entity_type,
        entity_id=notif_in.entity_id,
        task_id=notif_in.task_id,
        project_id=notif_in.project_id,
        team_id=notif_in.team_id,
        workspace_id=notif_in.workspace_id,
        delivery_channel=notif_in.delivery_channel,
        metadata=notif_in.metadata,
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notification could not be created or was suppressed by user preferences.")
    return notif

@router.patch("/read-all", status_code=status.HTTP_200_OK)
def mark_all_as_read(
    category: Optional[str] = Query(None, description="Optional category filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all unread notifications as read for current user."""
    affected = notification_service.mark_all_as_read(db, current_user.id, category=category)
    return {"message": "All notifications marked as read.", "affected": affected}

@router.post("/bulk/read", status_code=status.HTTP_200_OK)
def bulk_mark_as_read(
    bulk_in: BulkNotificationActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk mark notifications as read."""
    affected = notification_service.bulk_mark_as_read(db, current_user.id, bulk_in.notification_ids)
    return {"message": "Notifications marked as read.", "affected": affected}

@router.post("/bulk/delete", status_code=status.HTTP_200_OK)
def bulk_delete_notifications(
    bulk_in: BulkNotificationActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk delete notifications."""
    affected = notification_service.bulk_delete(db, current_user.id, bulk_in.notification_ids)
    return {"message": "Notifications deleted.", "affected": affected}

@router.post("/trigger-check", response_model=List[NotificationResponse])
def trigger_deadline_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually or periodically trigger task reminder checks for the authenticated user."""
    return notification_service.check_and_generate_task_reminders(db, current_user.id)

# -------------------------------------------------------------
# Parameterized endpoints (/{notification_id})
# -------------------------------------------------------------

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification_detail(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a single notification."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notif

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an individual notification as read."""
    try:
        return notification_service.mark_as_read(db, notification_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

@router.patch("/{notification_id}/unread", response_model=NotificationResponse)
def mark_notification_as_unread(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an individual notification as unread."""
    try:
        return notification_service.mark_as_unread(db, notification_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

@router.post("/{notification_id}/archive", response_model=NotificationResponse)
def archive_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive an individual notification."""
    try:
        return notification_service.archive_notification(db, notification_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification owned by the authenticated user."""
    try:
        notification_service.delete_notification(db, notification_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return None
