from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class IntegrationResponse(BaseModel):
    id: int
    provider: str
    status: str
    external_account_email: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AvailableIntegrationItem(BaseModel):
    provider: str
    name: str
    category: str
    description: str
    icon: str
    is_connected: bool = False

class ConnectResponse(BaseModel):
    authorization_url: str
    state: str
