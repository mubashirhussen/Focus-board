from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.integration import ExternalIntegration
from app.schemas.integration import (
    IntegrationResponse,
    AvailableIntegrationItem,
    ConnectResponse,
    ConnectApiKeyRequest,
    ConnectionTestResponse,
    IntegrationHealthResponse,
    IntegrationSyncRequest,
    IntegrationSyncJobResponse,
    SyncLogResponse,
    IntegrationEntityMappingResponse,
    InboundWebhookResponse,
)
from app.api.dependencies import get_current_user
from app.services import integration_service

router = APIRouter(prefix="/integrations", tags=["External Integrations"])

@router.get("", response_model=List[IntegrationResponse])
def get_user_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all external integrations connected by the authenticated user."""
    return integration_service.get_user_integrations(db, current_user.id)

@router.get("/available", response_model=List[AvailableIntegrationItem])
def get_available_integrations(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available integration hub catalog items with connection status."""
    return integration_service.get_available_integrations(
        db, user_id=current_user.id, category=category, search=search
    )

@router.get("/providers/{provider_id}", response_model=AvailableIntegrationItem)
def get_provider_details(
    provider_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get metadata and feature capabilities for a specific integration provider."""
    return integration_service.get_provider_details(
        db, provider_id=provider_id, user_id=current_user.id
    )

# Backward-compatible Google Calendar connect and callback routes
@router.get("/google/connect", response_model=ConnectResponse)
def connect_google_calendar_legacy(
    redirect_uri: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initiate Google OAuth flow for Calendar synchronization."""
    return integration_service.initiate_oauth(
        db=db,
        provider="google_calendar",
        user_id=current_user.id,
        redirect_uri=redirect_uri or "http://localhost:5173/integrations/callback"
    )

@router.get("/google/callback", response_model=IntegrationResponse)
def google_calendar_callback_legacy(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth CSRF state"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Authorize Google Calendar and persist credentials."""
    return integration_service.handle_oauth_callback(
        db=db,
        provider="google_calendar",
        code=code,
        state=state,
        user_id=current_user.id
    )

# API-key based connect
@router.post("/api-key/connect", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
def connect_api_key_provider(
    payload: ConnectApiKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Connect an integration using an API token or webhook URL with encrypted storage."""
    return integration_service.connect_api_key(
        db=db,
        user_id=current_user.id,
        payload=payload
    )

# Inbound Webhooks
@router.post("/webhooks/{provider}", response_model=InboundWebhookResponse)
async def inbound_webhook_receiver(
    provider: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Process inbound webhook payloads from external providers with signature verification."""
    raw_body = await request.body()
    headers = dict(request.headers)
    query_params = dict(request.query_params)

    return integration_service.process_inbound_webhook(
        db=db,
        provider=provider,
        raw_body=raw_body,
        headers=headers,
        query_params=query_params
    )

# Generic OAuth connect & callback
@router.get("/{provider}/connect", response_model=ConnectResponse)
def connect_oauth_provider(
    provider: str,
    redirect_uri: Optional[str] = Query(None),
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate OAuth authorization handshake with signed, timestamped CSRF protection."""
    prov = "google_calendar" if provider.lower() in ("google", "google_calendar") else provider
    return integration_service.initiate_oauth(
        db=db,
        provider=prov,
        user_id=current_user.id,
        redirect_uri=redirect_uri,
        workspace_id=workspace_id
    )

@router.get("/{provider}/callback", response_model=IntegrationResponse)
def oauth_provider_callback(
    provider: str,
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth CSRF state"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle OAuth callback exchange, encrypt credentials at rest, and persist integration."""
    prov = "google_calendar" if provider.lower() in ("google", "google_calendar") else provider
    return integration_service.handle_oauth_callback(
        db=db,
        provider=prov,
        code=code,
        state=state,
        user_id=current_user.id
    )

# Connection testing & health
@router.post("/{integration_id:int}/test", response_model=ConnectionTestResponse)
def test_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test live connectivity and authentication health for an active integration."""
    return integration_service.test_integration_connection(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id
    )

@router.get("/{integration_id:int}/health", response_model=IntegrationHealthResponse)
def get_integration_health(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed health diagnostic for an active integration."""
    return integration_service.get_integration_health(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id
    )

@router.post("/{integration_id:int}/reconnect", response_model=IntegrationResponse)
def reconnect_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Re-establish and heal an integration connection."""
    return integration_service.reconnect_integration(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id
    )

# Synchronization
@router.post("/{integration_id:int}/sync", response_model=IntegrationSyncJobResponse)
def run_sync(
    integration_id: int,
    sync_req: IntegrationSyncRequest = IntegrationSyncRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger data synchronization job (bidirectional, inbound, or outbound)."""
    return integration_service.run_synchronization(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id,
        sync_req=sync_req
    )

@router.get("/{integration_id:int}/sync-history", response_model=List[IntegrationSyncJobResponse])
def get_sync_history(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve history of synchronization executions."""
    return integration_service.get_sync_history(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id
    )

@router.get("/{integration_id:int}/sync-logs", response_model=List[SyncLogResponse])
def get_sync_logs(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve audit sync logs."""
    return integration_service.get_sync_logs(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id
    )

@router.get("/{integration_id:int}/mappings", response_model=List[IntegrationEntityMappingResponse])
def get_mappings(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve internal-to-external mapped entities."""
    return integration_service.get_entity_mappings(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id
    )

# Disconnect
@router.delete("/{integration_id:int}", status_code=status.HTTP_200_OK)
def disconnect_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disconnect and revoke integration credentials with multi-tenant protection."""
    integration_service.disconnect_integration(
        db=db,
        integration_id=integration_id,
        user_id=current_user.id
    )
    return {"message": "Integration successfully disconnected"}
