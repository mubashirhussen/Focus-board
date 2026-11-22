from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    current_step = Column(Integer, default=1, nullable=False)
    completed_steps_json = Column(Text, default="[]", nullable=False)
    dismissed = Column(Boolean, default=False, nullable=False)
    primary_goal = Column(String(100), default="personal_productivity", nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", backref="onboarding_record")

    @property
    def completed_steps(self):
        try:
            return json.loads(self.completed_steps_json or "[]")
        except Exception:
            return []

    @completed_steps.setter
    def completed_steps(self, steps_list):
        self.completed_steps_json = json.dumps(steps_list)


class ProductAnalyticsEvent(Base):
    __tablename__ = "product_analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    properties_json = Column(Text, default="{}", nullable=False)
    source = Column(String(50), default="web", nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    @property
    def properties(self):
        try:
            return json.loads(self.properties_json or "{}")
        except Exception:
            return {}


class CustomerFeedback(Base):
    __tablename__ = "customer_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), default="general_feedback", nullable=False, index=True)
    description = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    status = Column(String(30), default="NEW", nullable=False, index=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
