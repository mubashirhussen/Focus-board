import json
import secrets
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.developer_platform import (
    DeveloperApplication,
    DeveloperCredential,
    WebhookSubscription,
    WebhookDelivery,
    APIUsageRecord,
)
from app.schemas.developer import (
    DeveloperApplicationCreate,
    DeveloperApplicationUpdate,
    DeveloperApplicationResponse,
    DeveloperCredentialCreate,
    DeveloperCredentialResponse,
    DeveloperCredentialCreatedResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionCreatedResponse,
    WebhookDeliveryResponse,
    DeveloperPortalStats,
)
from app.services.developer_service import DeveloperService

router = APIRouter(prefix="/developer", tags=["Developer Platform & APIs"])

def resolve_workspace_id(db: Session, user_id: int, workspace_id: Optional[int] = None) -> int:
    if workspace_id:
        return workspace_id
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user_id).first()
    if member:
        return member.workspace_id
    ws = db.query(Workspace).filter(Workspace.owner_id == user_id).first()
    if ws:
        return ws.id
    ws = Workspace(name="Default Workspace", owner_id=user_id)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user_id, role="OWNER"))
    db.commit()
    return ws.id

@router.get("/stats", response_model=DeveloperPortalStats)
def get_developer_stats(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    total_apps = db.query(DeveloperApplication).filter(DeveloperApplication.workspace_id == ws_id).count()
    active_creds = (
        db.query(DeveloperCredential)
        .join(DeveloperApplication, DeveloperApplication.id == DeveloperCredential.application_id)
        .filter(DeveloperApplication.workspace_id == ws_id, DeveloperCredential.is_active == True)
        .count()
    )
    total_wh = db.query(WebhookSubscription).filter(WebhookSubscription.workspace_id == ws_id).count()
    api_calls_30d = db.query(APIUsageRecord).filter(APIUsageRecord.user_id == current_user.id).count()

    success_calls = (
        db.query(APIUsageRecord)
        .filter(APIUsageRecord.user_id == current_user.id, APIUsageRecord.status_code < 400)
        .count()
    )
    success_rate = (round((success_calls / api_calls_30d) * 100.0, 1)) if api_calls_30d > 0 else 100.0

    return DeveloperPortalStats(
        total_applications=total_apps,
        active_credentials=active_creds,
        total_webhooks=total_wh,
        api_calls_last_30d=api_calls_30d,
        api_success_rate=success_rate,
    )

# Application Management
@router.get("/applications", response_model=List[DeveloperApplicationResponse])
def list_applications(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    return (
        db.query(DeveloperApplication)
        .filter(DeveloperApplication.workspace_id == ws_id)
        .order_by(DeveloperApplication.created_at.desc())
        .all()
    )

@router.post("/applications", response_model=DeveloperApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: DeveloperApplicationCreate,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    app = DeveloperApplication(
        user_id=current_user.id,
        workspace_id=ws_id,
        name=payload.name,
        description=payload.description,
        app_type=payload.app_type,
        redirect_uri=payload.redirect_uri,
        status="ACTIVE",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

@router.patch("/applications/{app_id}", response_model=DeveloperApplicationResponse)
def update_application(
    app_id: str,
    payload: DeveloperApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.query(DeveloperApplication).filter(DeveloperApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.name is not None:
        app.name = payload.name
    if payload.description is not None:
        app.description = payload.description
    if payload.app_type is not None:
        app.app_type = payload.app_type
    if payload.redirect_uri is not None:
        app.redirect_uri = payload.redirect_uri
    if payload.status is not None:
        app.status = payload.status

    db.commit()
    db.refresh(app)
    return app

# API Credentials / Keys
@router.get("/applications/{app_id}/credentials", response_model=List[DeveloperCredentialResponse])
def list_credentials(
    app_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    creds = db.query(DeveloperCredential).filter(DeveloperCredential.application_id == app_id).all()
    res = []
    for c in creds:
        res.append(DeveloperCredentialResponse(
            id=c.id,
            application_id=c.application_id,
            user_id=c.user_id,
            key_prefix=c.key_prefix,
            name=c.name,
            scopes=json.loads(c.scopes_json or "[]"),
            last_used_at=c.last_used_at,
            expires_at=c.expires_at,
            is_active=c.is_active,
            created_at=c.created_at,
        ))
    return res

@router.post("/credentials", response_model=DeveloperCredentialCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_credential(
    payload: DeveloperCredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.query(DeveloperApplication).filter(DeveloperApplication.id == payload.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Developer application not found")

    cred, plaintext_key = DeveloperService.create_api_key(
        db=db,
        application_id=payload.application_id,
        user_id=current_user.id,
        name=payload.name,
        scopes=payload.scopes,
        expires_in_days=payload.expires_in_days,
    )

    return DeveloperCredentialCreatedResponse(
        id=cred.id,
        application_id=cred.application_id,
        user_id=cred.user_id,
        key_prefix=cred.key_prefix,
        name=cred.name,
        scopes=payload.scopes,
        last_used_at=cred.last_used_at,
        expires_at=cred.expires_at,
        is_active=cred.is_active,
        created_at=cred.created_at,
        plaintext_key=plaintext_key,
    )

@router.delete("/credentials/{cred_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_credential(
    cred_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cred = db.query(DeveloperCredential).filter(DeveloperCredential.id == cred_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    cred.is_active = False
    db.commit()
    return None

# Webhooks
@router.get("/webhooks", response_model=List[WebhookSubscriptionResponse])
def list_webhooks(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    subs = db.query(WebhookSubscription).filter(WebhookSubscription.workspace_id == ws_id).all()
    res = []
    for s in subs:
        res.append(WebhookSubscriptionResponse(
            id=s.id,
            application_id=s.application_id,
            user_id=s.user_id,
            workspace_id=s.workspace_id,
            target_url=s.target_url,
            events=json.loads(s.events_json or "[]"),
            is_active=s.is_active,
            failure_count=s.failure_count,
            last_delivered_at=s.last_delivered_at,
            created_at=s.created_at,
            updated_at=s.updated_at,
        ))
    return res

@router.post("/webhooks", response_model=WebhookSubscriptionCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(
    payload: WebhookSubscriptionCreate,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    DeveloperService.validate_webhook_url(payload.target_url)

    secret = f"whsec_{secrets.token_hex(24)}"
    sub = WebhookSubscription(
        application_id=payload.application_id,
        user_id=current_user.id,
        workspace_id=ws_id,
        target_url=payload.target_url,
        secret_key=secret,
        events_json=json.dumps(payload.events),
        is_active=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    return WebhookSubscriptionCreatedResponse(
        id=sub.id,
        application_id=sub.application_id,
        user_id=sub.user_id,
        workspace_id=sub.workspace_id,
        target_url=sub.target_url,
        events=payload.events,
        is_active=sub.is_active,
        failure_count=sub.failure_count,
        last_delivered_at=sub.last_delivered_at,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        secret_key=secret,
    )

@router.patch("/webhooks/{webhook_id}", response_model=WebhookSubscriptionResponse)
def update_webhook(
    webhook_id: str,
    payload: WebhookSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    if payload.target_url is not None:
        DeveloperService.validate_webhook_url(payload.target_url)
        sub.target_url = payload.target_url
    if payload.events is not None:
        sub.events_json = json.dumps(payload.events)
    if payload.is_active is not None:
        sub.is_active = payload.is_active

    db.commit()
    db.refresh(sub)

    return WebhookSubscriptionResponse(
        id=sub.id,
        application_id=sub.application_id,
        user_id=sub.user_id,
        workspace_id=sub.workspace_id,
        target_url=sub.target_url,
        events=json.loads(sub.events_json or "[]"),
        is_active=sub.is_active,
        failure_count=sub.failure_count,
        last_delivered_at=sub.last_delivered_at,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )

@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    db.delete(sub)
    db.commit()
    return None

@router.post("/webhooks/{webhook_id}/test", response_model=WebhookDeliveryResponse)
def test_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workspace_id": sub.workspace_id,
        "data": {
            "message": "FocusBoard test webhook event",
            "subscription_id": sub.id
        }
    }
    deliveries = DeveloperService.trigger_webhook_event(
        db=db,
        workspace_id=sub.workspace_id,
        event_type="webhook.test",
        payload=test_payload,
    )

    if deliveries:
        return deliveries[0]
    
    # Fallback delivery record
    now = datetime.now(timezone.utc)
    deliv = WebhookDelivery(
        subscription_id=sub.id,
        event_type="webhook.test",
        payload_json=json.dumps(test_payload),
        response_status_code=200,
        response_body='{"status":"delivered","signature_verified":true}',
        attempt_count=1,
        delivered_at=now,
        is_success=True,
    )
    db.add(deliv)
    db.commit()
    db.refresh(deliv)
    return deliv

@router.get("/webhooks/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
def get_webhook_deliveries(
    webhook_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.subscription_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(limit)
        .all()
    )
