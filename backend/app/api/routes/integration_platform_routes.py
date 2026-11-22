from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.integration_platform import (
    IntegrationProviderResponse,
    MarketplaceListingResponse,
    MarketplaceInstallationCreate,
    MarketplaceInstallationResponse,
    OAuthConnectorResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    APIPlatformAnalyticsResponse,
)
from app.services import integration_platform_service

router = APIRouter(prefix="/integration-platform", tags=["FocusBoard Integration Ecosystem & Developer Platform"])

# --- Catalog Providers ---
@router.get("/providers", response_model=List[IntegrationProviderResponse])
def list_providers(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve catalog of supported third-party providers with features and required scopes."""
    return integration_platform_service.list_providers(db, category=category)

# --- Marketplace Listings ---
@router.get("/marketplace/listings", response_model=List[MarketplaceListingResponse])
def list_marketplace_listings(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Browse app marketplace listings."""
    return integration_platform_service.list_marketplace_listings(db, category=category)

@router.post("/marketplace/install", response_model=MarketplaceInstallationResponse, status_code=status.HTTP_201_CREATED)
def install_marketplace_app(
    payload: MarketplaceInstallationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Install an app from the marketplace with explicit user consent on permissions."""
    try:
        return integration_platform_service.install_marketplace_app(
            db=db,
            listing_id=payload.listing_id,
            workspace_id=payload.workspace_id,
            user_id=current_user.id,
            granted_scopes=payload.granted_scopes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/marketplace/installations", response_model=List[MarketplaceInstallationResponse])
def list_workspace_installations(
    workspace_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List installed marketplace applications for the given workspace."""
    return integration_platform_service.list_workspace_installations(db, workspace_id=workspace_id)

# --- OAuth Connectors ---
@router.get("/connectors", response_model=List[OAuthConnectorResponse])
def list_connectors(
    workspace_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List OAuth connectors with their connection health status."""
    return integration_platform_service.list_oauth_connectors(db, workspace_id=workspace_id)

@router.post("/connectors/connect", response_model=OAuthConnectorResponse)
def connect_connector(
    provider_id: str = Query(...),
    workspace_id: int = Query(...),
    account_identifier: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initiate or complete connection for an OAuth provider."""
    try:
        return integration_platform_service.connect_oauth_provider(
            db=db,
            provider_id=provider_id,
            workspace_id=workspace_id,
            user_id=current_user.id,
            account_identifier=account_identifier,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/connectors/{connector_id}/disconnect", status_code=status.HTTP_200_OK)
def disconnect_connector(
    connector_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect an OAuth provider connector."""
    success = integration_platform_service.disconnect_oauth_provider(db, connector_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    return {"message": "Connector disconnected successfully", "connector_id": connector_id}

# --- Webhooks Tester & HMAC-SHA256 Delivery Simulator ---
@router.post("/webhooks/test", response_model=WebhookTestResponse)
def test_webhook_delivery(
    payload: WebhookTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Send and verify HMAC-SHA256 signature test payload for webhooks."""
    return integration_platform_service.test_webhook_delivery(payload)

# --- Platform Analytics ---
@router.get("/analytics", response_model=APIPlatformAnalyticsResponse)
def get_platform_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve platform usage metrics, active webhooks, and developer application counts."""
    return integration_platform_service.get_platform_analytics(db)
