from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Standardized timestamp mixin for FocusBoard entity models."""
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

# Export declarative base for models
__all__ = ["Base", "TimestampMixin", "utc_now"]
