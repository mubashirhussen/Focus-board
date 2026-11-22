import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class StrategicPlan(Base):
    __tablename__ = "strategic_plans"

    id = Column(String(64), primary_key=True, default=lambda: f"splan_{uuid.uuid4().hex[:12]}")
    organization_id = Column(String(64), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    vision = Column(Text, nullable=False)
    mission = Column(Text, nullable=False)
    strategic_themes_json = Column(Text, default="[]", nullable=False)
    time_horizon = Column(String(32), default="ANNUAL", nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)  # DRAFT, ACTIVE, UNDER_REVIEW, ARCHIVED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    goals = relationship("StrategicGoal", back_populates="plan", cascade="all, delete-orphan")

class StrategicGoal(Base):
    __tablename__ = "strategic_goals"

    id = Column(String(64), primary_key=True, default=lambda: f"sgoal_{uuid.uuid4().hex[:12]}")
    plan_id = Column(String(64), ForeignKey("strategic_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)  # REVENUE, MARKET_SHARE, PRODUCT, RETENTION
    target_metric = Column(String(128), nullable=False)
    baseline_value = Column(Float, default=0.0, nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0, nullable=False)
    unit = Column(String(32), default="$", nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)  # PLANNED, ACTIVE, AT_RISK, COMPLETED, CANCELLED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    plan = relationship("StrategicPlan", back_populates="goals")
    initiatives = relationship("StrategicInitiative", back_populates="goal", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])

class StrategicInitiative(Base):
    __tablename__ = "strategic_initiatives"

    id = Column(String(64), primary_key=True, default=lambda: f"sinit_{uuid.uuid4().hex[:12]}")
    goal_id = Column(String(64), ForeignKey("strategic_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(32), default="P2_HIGH", nullable=False)  # P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW
    budget_amount = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="IN_PROGRESS", nullable=False, index=True)  # PROPOSED, APPROVED, IN_PROGRESS, BLOCKED, COMPLETED
    progress_percentage = Column(Float, default=0.0, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    goal = relationship("StrategicGoal", back_populates="initiatives")
    owner = relationship("User", foreign_keys=[owner_id])

class MarketIntelligence(Base):
    __tablename__ = "market_intelligences"

    id = Column(String(64), primary_key=True, default=lambda: f"mkt_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    intelligence_type = Column(String(64), nullable=False, index=True)  # TREND, TECH_DISRUPTION, REGULATORY, MACROECONOMIC
    summary = Column(Text, nullable=False)
    source_name = Column(String(255), nullable=False)
    source_url = Column(String(512), nullable=True)
    confidence_score = Column(Float, default=0.9, nullable=False)
    impact_rating = Column(String(32), default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH, TRANSFORMATIVE
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    owner = relationship("User", foreign_keys=[owner_id])

class MarketSignal(Base):
    __tablename__ = "market_signals"

    id = Column(String(64), primary_key=True, default=lambda: f"sig_{uuid.uuid4().hex[:12]}")
    signal_type = Column(String(64), nullable=False, index=True)  # GROWTH, PRICING_SHIFT, CUSTOMER_DEMAND, COMPETITOR_MOVE
    title = Column(String(255), nullable=False)
    observations = Column(Text, nullable=False)
    trend_direction = Column(String(32), default="ACCELERATING", nullable=False)  # ACCELERATING, STABLE, DECELERATING
    urgency = Column(String(32), default="NEAR_TERM", nullable=False)  # IMMEDIATE, NEAR_TERM, MONITOR
    is_converted_to_opportunity = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(String(64), primary_key=True, default=lambda: f"comp_{uuid.uuid4().hex[:12]}")
    name = Column(String(255), unique=True, nullable=False, index=True)
    website = Column(String(255), nullable=True)
    market_position = Column(String(64), default="CHALLENGER", nullable=False)  # LEADER, CHALLENGER, NICHE, NEW_ENTRANT
    pricing_model = Column(String(64), default="PER_SEAT", nullable=False)  # FREEMIUM, PER_SEAT, USAGE_BASED, ENTERPRISE
    strengths_json = Column(Text, default="[]", nullable=False)
    weaknesses_json = Column(Text, default="[]", nullable=False)
    features_diff_json = Column(Text, default="{}", nullable=False)
    threat_level = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

class SWOTEntry(Base):
    __tablename__ = "swot_entries"

    id = Column(String(64), primary_key=True, default=lambda: f"swot_{uuid.uuid4().hex[:12]}")
    swot_type = Column(String(32), nullable=False, index=True)  # STRENGTH, WEAKNESS, OPPORTUNITY, THREAT
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    impact = Column(String(32), default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH
    evidence_text = Column(Text, nullable=True)
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class MarketSizing(Base):
    __tablename__ = "market_sizings"

    id = Column(String(64), primary_key=True, default=lambda: f"msize_{uuid.uuid4().hex[:12]}")
    market_name = Column(String(255), nullable=False, index=True)
    methodology = Column(String(64), default="BOTTOM_UP", nullable=False)  # TOP_DOWN, BOTTOM_UP, VALUE_BASED
    tam_cents = Column(Integer, nullable=False)  # in cents
    sam_cents = Column(Integer, nullable=False)
    som_cents = Column(Integer, nullable=False)
    currency = Column(String(8), default="USD", nullable=False)
    assumptions_json = Column(Text, default="{}", nullable=False)
    confidence_score = Column(Float, default=0.85, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class StrategicOpportunity(Base):
    __tablename__ = "strategic_opportunities"

    id = Column(String(64), primary_key=True, default=lambda: f"sopp_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    customer_segment = Column(String(128), default="Enterprise B2B", nullable=False)
    estimated_value_cents = Column(Integer, default=0, nullable=False)
    feasibility_score = Column(Float, default=8.0, nullable=False)  # 1 to 10
    rice_reach = Column(Float, default=1000.0, nullable=False)
    rice_impact = Column(Float, default=3.0, nullable=False)
    rice_confidence = Column(Float, default=0.8, nullable=False)
    rice_effort = Column(Float, default=2.0, nullable=False)
    rice_score = Column(Float, default=1200.0, nullable=False)  # (reach * impact * confidence) / effort
    status = Column(String(32), default="EVALUATING", nullable=False, index=True)  # IDENTIFIED, EVALUATING, APPROVED, IN_PROGRESS, REALIZED, REJECTED
    created_at = Column(DateTime, default=utc_now, nullable=False)

class StrategicScenario(Base):
    __tablename__ = "strategic_scenarios"

    id = Column(String(64), primary_key=True, default=lambda: f"scen_{uuid.uuid4().hex[:12]}")
    name = Column(String(255), nullable=False)
    scenario_type = Column(String(32), default="BASE_CASE", nullable=False, index=True)  # BEST_CASE, BASE_CASE, WORST_CASE, MARKET_DISRUPTION
    description = Column(Text, nullable=False)
    revenue_multiplier = Column(Float, default=1.0, nullable=False)
    churn_rate_impact = Column(Float, default=0.0, nullable=False)
    assumptions_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class StrategicDecision(Base):
    __tablename__ = "strategic_decisions"

    id = Column(String(64), primary_key=True, default=lambda: f"sdec_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    context = Column(Text, nullable=False)
    decision_outcome = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    decision_maker_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_date = Column(DateTime, default=utc_now, nullable=False)
    status = Column(String(32), default="APPROVED", nullable=False, index=True)  # APPROVED, IN_EFFECT, SUPERSEDED, REVERSED
    created_at = Column(DateTime, default=utc_now, nullable=False)

    decision_maker = relationship("User", foreign_keys=[decision_maker_id])
