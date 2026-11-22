from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class UserRegionalSettingUpdate(BaseModel):
    language: Optional[str] = Field(None, description="ISO 639-1: en, hi, te, ta, es, ar")
    locale: Optional[str] = Field(None, description="en-US, en-IN, hi-IN, te-IN, es-ES, ar-AE")
    timezone: Optional[str] = Field(None, description="IANA Timezone, e.g. Asia/Kolkata, America/New_York")
    date_format: Optional[str] = Field(None, description="YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY")
    time_format: Optional[str] = Field(None, description="12h or 24h")
    week_start: Optional[int] = Field(None, ge=0, le=6, description="0=Sunday, 1=Monday")
    currency: Optional[str] = Field(None, description="ISO 4217: USD, INR, EUR, GBP, AED, JPY")
    number_format: Optional[str] = Field(None, description="standard or indian_lakhs")
    direction: Optional[str] = Field(None, description="ltr or rtl")

class UserRegionalSettingResponse(BaseModel):
    language: str
    locale: str
    timezone: str
    date_format: str
    time_format: str
    week_start: int
    currency: str
    number_format: str
    direction: str
    updated_at: datetime

class SupportedLocalesResponse(BaseModel):
    languages: List[Dict[str, str]]
    currencies: List[Dict[str, str]]
    timezones: List[str]
    date_formats: List[str]
