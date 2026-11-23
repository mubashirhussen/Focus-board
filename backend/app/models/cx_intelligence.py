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

class CXFeedbackCategory(Base):
    __tablename__ = "cx_feedback_categories"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("cx_feedback_categories.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    subcategories = relationship("CXFeedbackCategory", backref="parent", remote_side=[id])


class CXSurvey(Base):
    __tablename__ = "cx_surveys"

    id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    survey_type = Column(String(50), default="CSAT", nullable=False, index=True)  # CSAT, NPS, CES, CUSTOM
    status = Column(String(30), default="ACTIVE", nullable=False, index=True)    # DRAFT, ACTIVE, PAUSED, CLOSED
    target_audience = Column(String(50), default="ALL", nullable=False)
    trigger_event = Column(String(100), nullable=True)
    settings_json = Column(Text, default="{}", nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    creator = relationship("User", foreign_keys=[created_by_id])
    questions = relationship("CXSurveyQuestion", back_populates="survey", cascade="all, delete-orphan", order_by="CXSurveyQuestion.order_index")
    responses = relationship("CXSurveyResponse", back_populates="survey", cascade="all, delete-orphan")

    @property
    def settings(self):
        try:
            return json.loads(self.settings_json or "{}")
        except Exception:
            return {}

    @settings.setter
    def settings(self, val):
        self.settings_json = json.dumps(val)


class CXSurveyQuestion(Base):
    __tablename__ = "cx_survey_questions"

    id = Column(String(64), primary_key=True, index=True)
    survey_id = Column(String(64), ForeignKey("cx_surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(32), default="RATING_5", nullable=False)  # RATING_5, NPS_10, CES_7, TEXT, MULTIPLE_CHOICE
    options_json = Column(Text, default="[]", nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    survey = relationship("CXSurvey", back_populates="questions")

    @property
    def options(self):
        try:
            return json.loads(self.options_json or "[]")
        except Exception:
            return []

    @options.setter
    def options(self, val):
        self.options_json = json.dumps(val)


class CXSurveyResponse(Base):
    __tablename__ = "cx_survey_responses"

    id = Column(String(64), primary_key=True, index=True)
    survey_id = Column(String(64), ForeignKey("cx_surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    respondent_reference = Column(String(100), nullable=True)
    score = Column(Float, nullable=True)
    feedback_text = Column(Text, nullable=True)
    answers_json = Column(Text, default="{}", nullable=False)
    sentiment = Column(String(32), default="NEUTRAL", nullable=False)
    sentiment_score = Column(Float, default=0.0, nullable=False)
    submitted_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    survey = relationship("CXSurvey", back_populates="responses")
    user = relationship("User", foreign_keys=[user_id])

    @property
    def answers(self):
        try:
            return json.loads(self.answers_json or "{}")
        except Exception:
            return {}

    @answers.setter
    def answers(self, val):
        self.answers_json = json.dumps(val)


class CXInsight(Base):
    __tablename__ = "cx_insights"

    id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    insight_type = Column(String(50), default="TREND", nullable=False, index=True)  # TREND, CHURN_RISK, RECURRING_ISSUE, FEATURE_DEMAND, SENTIMENT_ALERT
    severity = Column(String(20), default="MEDIUM", nullable=False, index=True)      # LOW, MEDIUM, HIGH, CRITICAL
    priority = Column(String(20), default="MEDIUM", nullable=False, index=True)
    confidence = Column(Float, default=0.85, nullable=False)
    supporting_metrics_json = Column(Text, default="{}", nullable=False)
    supporting_feedback_ids_json = Column(Text, default="[]", nullable=False)
    recommended_action = Column(Text, nullable=True)
    status = Column(String(30), default="ACTIVE", nullable=False, index=True)        # ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    recommendations = relationship("CXRecommendation", back_populates="insight", cascade="all, delete-orphan")

    @property
    def supporting_metrics(self):
        try:
            return json.loads(self.supporting_metrics_json or "{}")
        except Exception:
            return {}

    @supporting_metrics.setter
    def supporting_metrics(self, val):
        self.supporting_metrics_json = json.dumps(val)

    @property
    def supporting_feedback_ids(self):
        try:
            return json.loads(self.supporting_feedback_ids_json or "[]")
        except Exception:
            return []

    @supporting_feedback_ids.setter
    def supporting_feedback_ids(self, val):
        self.supporting_feedback_ids_json = json.dumps(val)


class CXRecommendation(Base):
    __tablename__ = "cx_recommendations"

    id = Column(String(64), primary_key=True, index=True)
    insight_id = Column(String(64), ForeignKey("cx_insights.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    action_type = Column(String(50), default="TASK", nullable=False)  # TASK, NOTIFICATION, SETTING, WORKFLOW
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, CONVERTED, APPLIED, DISMISSED
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    converted_at = Column(DateTime, nullable=True)

    insight = relationship("CXInsight", back_populates="recommendations")
    task = relationship("Task", foreign_keys=[task_id])


class CXJourneyEvent(Base):
    __tablename__ = "cx_journey_events"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    stage = Column(String(50), nullable=False, index=True)  # ONBOARDING, ADOPTION, RETENTION, EXPANSION, CHURN_RISK, ADVOCACY
    event_name = Column(String(100), nullable=False, index=True)
    sentiment = Column(String(32), default="NEUTRAL", nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id])

    @property
    def metadata_dict(self):
        try:
            return json.loads(self.metadata_json or "{}")
        except Exception:
            return {}

    @metadata_dict.setter
    def metadata_dict(self, val):
        self.metadata_json = json.dumps(val)
