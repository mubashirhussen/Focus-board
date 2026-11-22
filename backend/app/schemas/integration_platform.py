from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Integration Provider (Catalog) ---
class IntegrationProviderBase(BaseModel):
    id: str
    name: str
    description: str
    category: str = "Productivity"
    icon: str = "Layers"
    auth_type: str = "OAUTH2"
    supported_features_json: str = "[]"
    required_scopes_json: str = "[]"
    documentation_url: Optional[str] = None
    is_active: bool = True

class IntegrationProviderResponse(IntegrationProviderBase):
    created_at: datetime
    features_list: List[str] = []
    scopes_list: List[str] = []

    model_config = ConfigDict(from_attributes=True)

# --- Marketplace Listing ---
class MarketplaceListingBase(BaseModel):
    title: str
    slug: str
    description: str
    category: str = "Productivity"
    developer_name: str = "FocusBoard Official"
    version: str = "1.0.0"
    status: str = "PUBLISHED"
    is_official: bool = True
    permissions_json: str = '["tasks:read"]'
    rating: float = 4.9
    icon: str = "Layers"

class MarketplaceListingCreate(MarketplaceListingBase):
    pass

class MarketplaceListingResponse(MarketplaceListingBase):
    id: str
    developer_id: Optional[int] = None
    install_count: int = 0
    created_at: datetime
    updated_at: datetime
    permissions_list: List[str] = []

    model_config = ConfigDict(from_attributes=True)

# --- Marketplace Installation & Permission Consent ---
class MarketplaceInstallationCreate(BaseModel):
    listing_id: str
    workspace_id: int
    consent_confirmed: bool = True
    granted_scopes: List[str] = ["tasks:read"]

class MarketplaceInstallationResponse(BaseModel):
    id: str
    listing_id: str
    workspace_id: int
    installed_by_id: Optional[int] = None
    status: str
    granted_scopes_json: str
    installed_at: datetime
    listing_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- OAuth Connector ---
class OAuthConnectorBase(BaseModel):
    provider_id: str
    connection_status: str = "AVAILABLE"  # AVAILABLE, CONNECTED, DISCONNECTED, NEEDS_REAUTHORIZATION, ERROR, DISABLED
    account_identifier: Optional[str] = None
    granted_scopes_json: str = "[]"

class OAuthConnectorUpdate(BaseModel):
    connection_status: Optional[str] = None
    account_identifier: Optional[str] = None
    encrypted_token_data: Optional[str] = None
    last_error_message: Optional[str] = None

class OAuthConnectorResponse(OAuthConnectorBase):
    id: str
    workspace_id: int
    user_id: int
    last_synced_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    provider_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- Webhook Testing & Delivery ---
class WebhookTestRequest(BaseModel):
    target_url: str
    secret_key: str
    event_type: str = "task.created"
    custom_payload: Optional[Dict[str, Any]] = None

class WebhookTestResponse(BaseModel):
    event_id: str
    target_url: str
    signature_header: str
    timestamp: int
    status_code: int
    response_body: str
    is_delivered: bool
    duration_ms: int

# --- API Platform Analytics ---
class APIPlatformAnalyticsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    active_api_keys_count: int
    active_webhooks_count: int
    webhook_delivery_success_rate: float
    installed_marketplace_apps_count: int
    top_endpoints: List[Dict[str, Any]] = []
