from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class IntegrationResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    workspace_id: Optional[int] = None
    provider: str
    status: str
    health_status: str = "HEALTHY"
    external_account_email: Optional[str] = None
    connection_metadata: Optional[str] = None
    config_json: Optional[str] = "{}"
    last_synced_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AvailableIntegrationItem(BaseModel):
    provider: str
    name: str
    category: str
    description: str
    icon: str
    auth_type: str = "OAUTH2"
    is_connected: bool = False
    supported_features: List[str] = []
    required_scopes: List[str] = []
    documentation_url: Optional[str] = None

class ConnectResponse(BaseModel):
    authorization_url: str
    state: str

class ConnectApiKeyRequest(BaseModel):
    provider: str = Field(..., description="Provider identifier (e.g. jira, slack, linear, webhook)")
    api_key: str = Field(..., description="API key or access token")
    account_identifier: Optional[str] = None
    base_url: Optional[str] = None
    workspace_id: Optional[int] = None
    config: Dict[str, Any] = {}

class IntegrationConfigUpdate(BaseModel):
    config: Optional[Dict[str, Any]] = None
    external_account_email: Optional[str] = None
    status: Optional[str] = None

class ConnectionTestResponse(BaseModel):
    provider: str
    is_healthy: bool
    status: str
    latency_ms: int
    message: str
    tested_at: datetime

class IntegrationHealthResponse(BaseModel):
    integration_id: int
    provider: str
    status: str
    health_status: str
    last_synced_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    token_valid: bool = True
    token_expiry: Optional[datetime] = None

class IntegrationSyncRequest(BaseModel):
    sync_type: str = Field(default="INCREMENTAL", description="FULL, INCREMENTAL")
    direction: str = Field(default="BIDIRECTIONAL", description="INBOUND, OUTBOUND, BIDIRECTIONAL")
    conflict_resolution: str = Field(default="LATEST_UPDATE_WINS", description="INTERNAL_WINS, EXTERNAL_WINS, LATEST_UPDATE_WINS")

class IntegrationSyncJobResponse(BaseModel):
    id: str
    integration_id: Optional[int] = None
    workspace_id: Optional[int] = None
    provider: str
    sync_type: str
    direction: str
    status: str
    records_synced: int = 0
    records_failed: int = 0
    conflict_resolution: str = "LATEST_UPDATE_WINS"
    duration_ms: int = 0
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SyncLogResponse(BaseModel):
    id: int
    integration_id: int
    operation: str
    status: str
    error_details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IntegrationEntityMappingResponse(BaseModel):
    id: str
    integration_id: Optional[int] = None
    workspace_id: Optional[int] = None
    provider: str
    entity_type: str
    internal_id: str
    external_id: str
    external_url: Optional[str] = None
    sync_status: str
    last_synced_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InboundWebhookResponse(BaseModel):
    received: bool = True
    event_id: str
    event_type: str
    processed: bool = True
    workflow_triggered: bool = False
