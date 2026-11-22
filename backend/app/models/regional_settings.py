from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRegionalSetting(Base):
    __tablename__ = "user_regional_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    language = Column(String(16), default="en", nullable=False)  # en, hi, te, ta, es, ar
    locale = Column(String(32), default="en-US", nullable=False)  # en-US, en-IN, hi-IN, te-IN, es-ES, ar-AE
    timezone = Column(String(64), default="Asia/Kolkata", nullable=False)  # IANA identifier
    date_format = Column(String(32), default="YYYY-MM-DD", nullable=False)  # YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY
    time_format = Column(String(16), default="12h", nullable=False)  # 12h, 24h
    week_start = Column(Integer, default=1, nullable=False)  # 1 = Monday, 0 = Sunday
    currency = Column(String(8), default="USD", nullable=False)  # ISO 4217: USD, INR, EUR, GBP, AED, JPY
    number_format = Column(String(32), default="standard", nullable=False)  # standard, indian_lakhs
    direction = Column(String(8), default="ltr", nullable=False)  # ltr, rtl
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
