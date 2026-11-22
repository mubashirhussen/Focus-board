from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="Member", nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False) # ACTIVE, PENDING_VERIFICATION, SUSPENDED, DISABLED, LOCKED
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    timezone = Column(String(64), default="UTC", nullable=False)
    locale = Column(String(10), default="en", nullable=False)
    avatar_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def username(self) -> str:
        return self.name or (self.email.split("@")[0] if self.email else "")

    @property
    def full_name(self) -> str:
        return self.display_name or self.name or ""

    # Isolated user tasks relationship
    tasks = relationship("Task", foreign_keys="[Task.user_id]", back_populates="user", cascade="all, delete-orphan")
