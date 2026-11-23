from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr

class OrganizationPolicyResponse(BaseModel):
    policy_type: str
    policy_value: Dict[str, Any]
    updated_at: datetime

class PolicyUpdateRequest(BaseModel):
    policy_value: Optional[Dict[str, Any]] = None
    policy_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    config_json: Optional[Any] = None

    def get_resolved_value(self) -> Dict[str, Any]:
        """Normalize policy value whether sent as nested dictionary or flat boolean."""
        if self.policy_value is not None:
            val = dict(self.policy_value)
            if self.is_enabled is not None and "enabled" not in val and "is_enabled" not in val:
                val["enabled"] = self.is_enabled
                val["is_enabled"] = self.is_enabled
            return val
        
        enabled = self.is_enabled if self.is_enabled is not None else False
        res: Dict[str, Any] = {"enabled": enabled, "is_enabled": enabled}
        if isinstance(self.config_json, dict):
            res.update(self.config_json)
        return res

class CustomRoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str]

class CustomRoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DomainAddRequest(BaseModel):
    domain: str

class DomainResponse(BaseModel):
    id: int
    domain: str
    verification_token: str
    is_verified: bool
    created_at: datetime
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class EnterpriseInvitationCreate(BaseModel):
    email: str
    role: str = "Member"

class EnterpriseInvitationResponse(BaseModel):
    id: int
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MFASetupResponse(BaseModel):
    secret: str
    qr_uri: str
    recovery_codes: List[str]

class MFAVerifyRequest(BaseModel):
    code: str

class MFADisableRequest(BaseModel):
    code: str

class AuditExportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[str] = None
