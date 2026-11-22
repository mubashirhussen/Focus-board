from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.push import PushSubscriptionRecord
from app.schemas.push import PushSubscribeRequest, PushSubscriptionResponse, PushTestRequest
from app.api.dependencies import get_current_user
from app.services.push_service import push_service

router = APIRouter(prefix="/push", tags=["PWA & Web Push Notifications"])

@router.get("/public-key")
def get_vapid_public_key():
    """Retrieve VAPID public key for browser PushManager subscription."""
    return {"public_key": push_service.get_public_key()}

@router.post("/subscribe", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def subscribe(
    req: PushSubscribeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register browser push subscription for the authenticated user."""
    sub = push_service.subscribe_user(
        db=db,
        user_id=current_user.id,
        endpoint=req.endpoint,
        p256dh_key=req.p256dh,
        auth_key=req.auth,
        device_info=req.device_info
    )
    return sub

@router.delete("/unsubscribe", status_code=status.HTTP_200_OK)
def unsubscribe(
    endpoint: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate browser push subscription."""
    success = push_service.unsubscribe_user(db, current_user.id, endpoint)
    return {"success": success}

@router.post("/test")
def send_test_push(
    req: PushTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a test Web Push notification to all active devices of user."""
    sent = push_service.send_notification_to_user(
        db=db,
        user_id=current_user.id,
        title=req.title or "FocusBoard Test",
        body=req.message or "Test alert",
    )
    return {"message": "Test push dispatched", "devices_notified": sent}
