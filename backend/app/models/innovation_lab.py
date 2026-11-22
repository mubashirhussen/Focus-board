import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class InnovationIdea(Base):
    __tablename__ = "innovation_ideas"

    id = Column(String(64), primary_key=True, default=lambda: f"idea_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    problem_statement = Column(Text, nullable=False)
    proposed_solution = Column(Text, nullable=False)
    category = Column(String(64), default="PRODUCT", nullable=False, index=True)  # PRODUCT, AI, TECHNICAL, BUSINESS, PROCESS, UX
    stage = Column(String(32), default="CAPTURE", nullable=False, index=True)
    # CAPTURE, SCREENING, RESEARCH, HYPOTHESIS, EXPERIMENTATION, PROTOTYPE, VALIDATED, ROADMAP, REJECTED
    target_audience = Column(String(128), default="Enterprise Teams", nullable=False)
    estimated_effort = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH
    strategic_value = Column(String(32), default="SUBSTANTIAL", nullable=False)  # INCREMENTAL, SUBSTANTIAL, TRANSFORMATIVE
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    roadmap_item_id = Column(Integer, ForeignKey("product_roadmap_items.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    roadmap_item = relationship("ProductRoadmapItem", foreign_keys=[roadmap_item_id])
    hypotheses = relationship("InnovationHypothesis", back_populates="idea", cascade="all, delete-orphan")
    experiments = relationship("InnovationExperiment", back_populates="idea", cascade="all, delete-orphan")
    prototypes = relationship("InnovationPrototype", back_populates="idea", cascade="all, delete-orphan")
    validations = relationship("InnovationValidation", back_populates="idea", cascade="all, delete-orphan")

class InnovationHypothesis(Base):
    __tablename__ = "innovation_hypotheses"

    id = Column(String(64), primary_key=True, default=lambda: f"hypo_{uuid.uuid4().hex[:12]}")
    idea_id = Column(String(64), ForeignKey("innovation_ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    statement = Column(Text, nullable=False)
    measurable_criterion = Column(String(255), nullable=False)
    confidence_score = Column(Float, default=0.8, nullable=False)
    status = Column(String(32), default="UNTESTED", nullable=False, index=True)  # UNTESTED, TESTING, VALIDATED, INVALIDATED
    created_at = Column(DateTime, default=utc_now, nullable=False)

    idea = relationship("InnovationIdea", back_populates="hypotheses")
    experiments = relationship("InnovationExperiment", back_populates="hypothesis")

class InnovationExperiment(Base):
    __tablename__ = "innovation_experiments"

    id = Column(String(64), primary_key=True, default=lambda: f"exp_{uuid.uuid4().hex[:12]}")
    idea_id = Column(String(64), ForeignKey("innovation_ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    hypothesis_id = Column(String(64), ForeignKey("innovation_hypotheses.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    experiment_type = Column(String(64), default="CUSTOMER_INTERVIEW", nullable=False)
    # CUSTOMER_INTERVIEW, SURVEY, PROTOTYPE_TEST, A_B_TEST, TECHNICAL_POC, LANDING_PAGE
    methodology = Column(Text, nullable=False)
    sample_size = Column(Integer, default=25, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(32), default="RUNNING", nullable=False, index=True)  # DRAFT, RUNNING, COMPLETED, CANCELLED
    budget_spent = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    idea = relationship("InnovationIdea", back_populates="experiments")
    hypothesis = relationship("InnovationHypothesis", back_populates="experiments")
    results = relationship("InnovationExperimentResult", back_populates="experiment", cascade="all, delete-orphan")

class InnovationExperimentResult(Base):
    __tablename__ = "innovation_experiment_results"

    id = Column(String(64), primary_key=True, default=lambda: f"exres_{uuid.uuid4().hex[:12]}")
    experiment_id = Column(String(64), ForeignKey("innovation_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    quantitative_summary = Column(Text, nullable=False)
    qualitative_feedback = Column(Text, nullable=False)
    success_criteria_met = Column(Boolean, default=True, nullable=False)
    evidence_attachment_url = Column(String(512), nullable=True)
    lessons_learned = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    experiment = relationship("InnovationExperiment", back_populates="results")

class InnovationPrototype(Base):
    __tablename__ = "innovation_prototypes"

    id = Column(String(64), primary_key=True, default=lambda: f"proto_{uuid.uuid4().hex[:12]}")
    idea_id = Column(String(64), ForeignKey("innovation_ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    prototype_type = Column(String(64), default="INTERACTIVE_MOCKUP", nullable=False)
    # UX_FIGMA, INTERACTIVE_MOCKUP, TECHNICAL_POC, AI_AGENT_PROTOTYPE
    demo_url = Column(String(512), nullable=True)
    repository_url = Column(String(512), nullable=True)
    tech_stack = Column(String(255), default="React + FastAPI", nullable=False)
    status = Column(String(32), default="BUILDING", nullable=False, index=True)  # PLANNING, BUILDING, TESTING, APPROVED, ARCHIVED
    created_at = Column(DateTime, default=utc_now, nullable=False)

    idea = relationship("InnovationIdea", back_populates="prototypes")

class InnovationValidation(Base):
    __tablename__ = "innovation_validations"

    id = Column(String(64), primary_key=True, default=lambda: f"ival_{uuid.uuid4().hex[:12]}")
    idea_id = Column(String(64), ForeignKey("innovation_ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    dimension = Column(String(64), nullable=False)  # PROBLEM, CUSTOMER, MARKET, TECHNICAL, BUSINESS, SECURITY
    criteria = Column(Text, nullable=False)
    status = Column(String(32), default="PASSED", nullable=False, index=True)  # NOT_STARTED, IN_PROGRESS, PASSED, FAILED, NEEDS_EVIDENCE
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Float, default=0.9, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    idea = relationship("InnovationIdea", back_populates="validations")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

class InnovationPortfolio(Base):
    __tablename__ = "innovation_portfolios"

    id = Column(String(64), primary_key=True, default=lambda: f"iport_{uuid.uuid4().hex[:12]}")
    name = Column(String(255), nullable=False)
    focus_area = Column(String(128), nullable=False)  # Core Platform, AI Copilots, Workflow Automation, Mobile
    budget_limit = Column(Float, default=50000.0, nullable=False)
    allocated_spend = Column(Float, default=0.0, nullable=False)
    active_ideas_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
