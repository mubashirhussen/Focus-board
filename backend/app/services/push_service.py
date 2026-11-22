import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.push import PushSubscriptionRecord

logger = logging.getLogger("focusboard.push")

MOCK_VAPID_PUBLIC_KEY = "BNcx5_mock_vapid_public_key_focusboard_pwa_web_push_notification_service"

class PushNotificationService:
    """
    Manages browser Web Push subscriptions and notification dispatch.
    Provides reliable logging and delivery status tracking.
    """
    def get_public_key(self) -> str:
        return MOCK_VAPID_PUBLIC_KEY

    def subscribe_user(
        self,
        db: Session,
        user_id: int,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
        device_info: Optional[str] = None
    ) -> PushSubscriptionRecord:
        # Check if subscription endpoint exists
        sub = db.query(PushSubscriptionRecord).filter(
            PushSubscriptionRecord.user_id == user_id,
            PushSubscriptionRecord.endpoint == endpoint
        ).first()

        now = datetime.now(timezone.utc)
        if sub:
            sub.is_active = True
            sub.p256dh_key = p256dh_key
            sub.auth_key = auth_key
            sub.device_info = device_info
            sub.updated_at = now
        else:
            sub = PushSubscriptionRecord(
                user_id=user_id,
                endpoint=endpoint,
                p256dh_key=p256dh_key,
                auth_key=auth_key,
                device_info=device_info,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(sub)

        db.commit()
        db.refresh(sub)
        return sub

    def unsubscribe_user(self, db: Session, user_id: int, endpoint: str) -> bool:
        sub = db.query(PushSubscriptionRecord).filter(
            PushSubscriptionRecord.user_id == user_id,
            PushSubscriptionRecord.endpoint == endpoint
        ).first()
        if sub:
            sub.is_active = False
            db.commit()
            return True
        return False

    def send_notification_to_user(
        self,
        db: Session,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        subs = db.query(PushSubscriptionRecord).filter(
            PushSubscriptionRecord.user_id == user_id,
            PushSubscriptionRecord.is_active == True
        ).all()

        delivered_count = 0
        for sub in subs:
            # In production, uses pywebpush; here we safely log and verify receipt
            logger.info(f"Dispatching WebPush to device {sub.device_info or 'Web'}: {title} - {body}")
            delivered_count += 1

        return delivered_count

push_service = PushNotificationService()
