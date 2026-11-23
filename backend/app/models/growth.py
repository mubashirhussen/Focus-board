from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
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
    title = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), default="general_feedback", nullable=False, index=True)
    feedback_type = Column(String(50), default="GENERAL", nullable=False, index=True)
    source = Column(String(50), default="IN_APP", nullable=False)
    description = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    sentiment = Column(String(32), default="NEUTRAL", nullable=False, index=True)
    sentiment_score = Column(Float, default=0.0, nullable=False)
    sentiment_confidence = Column(Float, default=0.5, nullable=False)
    priority = Column(String(20), default="MEDIUM", nullable=False, index=True)
    priority_score = Column(Float, default=50.0, nullable=False)
    status = Column(String(30), default="NEW", nullable=False, index=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    tags_json = Column(Text, default="[]", nullable=False)
    admin_notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    metadata_json = Column(Text, default="{}", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])

    @property
    def tags(self):
        try:
            return json.loads(self.tags_json or "[]")
        except Exception:
            return []

    @tags.setter
    def tags(self, val):
        self.tags_json = json.dumps(val)

    @property
    def metadata_dict(self):
        try:
            return json.loads(self.metadata_json or "{}")
        except Exception:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, val):
        self.metadata_json = json.dumps(val)
