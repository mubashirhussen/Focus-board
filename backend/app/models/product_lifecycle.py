import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# 1. Product Discovery
class ProductDiscovery(Base):
    __tablename__ = "product_discoveries"

    id = Column(String(64), primary_key=True, default=lambda: f"disc_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    problem_statement = Column(Text, nullable=False)
    hypothesis = Column(Text, nullable=False)
    target_users = Column(String(255), nullable=False)
    customer_segment = Column(String(64), default="ENTERPRISE", nullable=False)
    business_impact = Column(Text, nullable=False)
    customer_impact = Column(Text, nullable=False)
    status = Column(String(32), default="DISCOVERED", nullable=False, index=True)
    # DISCOVERED, INVESTIGATING, VALIDATING, VALIDATED, PRIORITIZED, PLANNED, REJECTED, ARCHIVED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    ideas = relationship("ProductIdea", back_populates="discovery", cascade="all, delete-orphan")
    validations = relationship("ProductValidation", back_populates="discovery", cascade="all, delete-orphan")

# 2. Product Ideas
class ProductIdea(Base):
    __tablename__ = "product_ideas"

    id = Column(String(64), primary_key=True, default=lambda: f"idea_{uuid.uuid4().hex[:12]}")
    discovery_id = Column(String(64), ForeignKey("product_discoveries.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    problem_statement = Column(Text, nullable=False)
    proposed_solution = Column(Text, nullable=False)
    product_area = Column(String(64), default="CORE_PLATFORM", nullable=False)
    category = Column(String(64), default="PRODUCTIVITY", nullable=False)
    priority = Column(String(32), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, URGENT
    status = Column(String(32), default="NEW", nullable=False, index=True)
    # NEW, UNDER_REVIEW, VALIDATED, PLANNED, IN_PROGRESS, SHIPPED, ARCHIVED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    tags_json = Column(Text, server_default="[]", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    discovery = relationship("ProductDiscovery", back_populates="ideas")
    owner = relationship("User", foreign_keys=[owner_id])

# 3. Product Feature Requests (Customer Demand Hub)
class ProductFeatureRequest(Base):
    __tablename__ = "product_feature_requests"

    id = Column(String(64), primary_key=True, default=lambda: f"freq_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    customer_name = Column(String(128), nullable=False)
    customer_segment = Column(String(64), default="ENTERPRISE", nullable=False)
    source = Column(String(64), default="CUSTOMER_FEEDBACK", nullable=False)
    # CUSTOMER_FEEDBACK, SUPPORT_TICKET, SURVEY, SALES, INTERNAL, TELEMETRY
    request_count = Column(Integer, default=1, nullable=False)
    priority = Column(String(32), default="MEDIUM", nullable=False)
    status = Column(String(32), default="NEW", nullable=False, index=True)
    # NEW, UNDER_REVIEW, VALIDATED, PRIORITIZED, PLANNED, IN_PROGRESS, RELEASED, DECLINED
    business_impact = Column(Text, nullable=True)
    revenue_impact = Column(Float, default=0.0, nullable=False)
    merged_into_id = Column(String(64), ForeignKey("product_feature_requests.id", ondelete="SET NULL"), nullable=True)
    linked_idea_id = Column(String(64), ForeignKey("product_ideas.id", ondelete="SET NULL"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])

# 4. Product Opportunities
class ProductOpportunity(Base):
    __tablename__ = "product_opportunities"

    id = Column(String(64), primary_key=True, default=lambda: f"opp_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    problem_statement = Column(Text, nullable=False)
    customer_segment = Column(String(64), default="ALL", nullable=False)
    market_segment = Column(String(64), default="B2B_SAAS", nullable=False)
    product_area = Column(String(64), default="CORE_PLATFORM", nullable=False)
    business_impact = Column(Text, nullable=False)
    customer_impact = Column(Text, nullable=False)
    revenue_potential = Column(Float, default=0.0, nullable=False)
    effort_estimate = Column(String(32), default="MEDIUM", nullable=False)
    risk_level = Column(String(32), default="LOW", nullable=False)
    validation_status = Column(String(32), default="IDENTIFIED", nullable=False, index=True)
    # IDENTIFIED, INVESTIGATING, VALIDATING, VALIDATED, PRIORITIZED, PLANNED, IMPLEMENTING, COMPLETED
    priority = Column(String(32), default="MEDIUM", nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])

# 5. Prioritization Frameworks (RICE, ICE, MoSCoW, Weighted)
class ProductPrioritizationItem(Base):
    __tablename__ = "product_prioritization_items"

    id = Column(String(64), primary_key=True, default=lambda: f"prio_{uuid.uuid4().hex[:12]}")
    item_type = Column(String(64), default="FEATURE_REQUEST", nullable=False) # FEATURE_REQUEST, PRODUCT_IDEA, OPPORTUNITY
    item_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    reach = Column(Float, default=100.0, nullable=False)
    impact = Column(Float, default=3.0, nullable=False)
    confidence = Column(Float, default=0.8, nullable=False)
    effort = Column(Float, default=2.0, nullable=False)
    rice_score = Column(Float, default=120.0, nullable=False)
    ease = Column(Float, default=3.0, nullable=False)
    ice_score = Column(Float, default=7.2, nullable=False)
    moscow_category = Column(String(32), default="SHOULD_HAVE", nullable=False) # MUST_HAVE, SHOULD_HAVE, COULD_HAVE, WONT_HAVE
    weighted_score = Column(Float, default=75.0, nullable=False)
    priority_rank = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)
    evaluated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    evaluated_at = Column(DateTime, default=utc_now, nullable=False)

    evaluated_by = relationship("User", foreign_keys=[evaluated_by_id])

# 6. Strategic Product Initiatives
class ProductInitiative(Base):
    __tablename__ = "product_initiatives"

    id = Column(String(64), primary_key=True, default=lambda: f"init_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    strategic_objective = Column(String(255), nullable=False)
    priority = Column(String(32), default="HIGH", nullable=False)
    status = Column(String(32), default="IN_PROGRESS", nullable=False, index=True) # PLANNED, IN_PROGRESS, ON_HOLD, COMPLETED, CANCELLED
    progress_pct = Column(Float, default=0.0, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    start_date = Column(DateTime, nullable=True)
    target_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    roadmap_items = relationship("LifecycleRoadmapItem", back_populates="initiative", cascade="all, delete-orphan")

# 7. Lifecycle Roadmaps (Gantt & Kanban timeline items)
class LifecycleRoadmapItem(Base):
    __tablename__ = "lifecycle_roadmap_items"

    id = Column(String(64), primary_key=True, default=lambda: f"lrmi_{uuid.uuid4().hex[:12]}")
    initiative_id = Column(String(64), ForeignKey("product_initiatives.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    product_area = Column(String(64), default="CORE_PLATFORM", nullable=False)
    status = Column(String(32), default="PLANNED", nullable=False, index=True) # IDEA, PLANNED, IN_PROGRESS, BLOCKED, COMPLETED, CANCELLED
    priority = Column(String(32), default="MEDIUM", nullable=False)
    quarter = Column(String(16), default="Q1-2027", nullable=False)
    start_date = Column(DateTime, nullable=True)
    target_date = Column(DateTime, nullable=True)
    progress_pct = Column(Float, default=0.0, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    initiative = relationship("ProductInitiative", back_populates="roadmap_items")
    owner = relationship("User", foreign_keys=[owner_id])

# 8. Roadmap Dependencies
class RoadmapDependency(Base):
    __tablename__ = "roadmap_dependencies"

    id = Column(String(64), primary_key=True, default=lambda: f"rdep_{uuid.uuid4().hex[:12]}")
    roadmap_item_id = Column(String(64), ForeignKey("lifecycle_roadmap_items.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_item_id = Column(String(64), ForeignKey("lifecycle_roadmap_items.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String(32), default="BLOCKS", nullable=False) # BLOCKS, REQUIRES, RELATES_TO
    status = Column(String(32), default="ACTIVE", nullable=False) # ACTIVE, RESOLVED
    risk_level = Column(String(32), default="MEDIUM", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

# 9. Product Validation Records
class ProductValidation(Base):
    __tablename__ = "product_validations"

    id = Column(String(64), primary_key=True, default=lambda: f"pval_{uuid.uuid4().hex[:12]}")
    discovery_id = Column(String(64), ForeignKey("product_discoveries.id", ondelete="CASCADE"), nullable=False, index=True)
    hypothesis = Column(Text, nullable=False)
    method = Column(String(64), default="INTERVIEW", nullable=False) # INTERVIEW, SURVEY, PROTOTYPE, USABILITY, USAGE_METRIC, EXPERIMENT
    sample_size = Column(Integer, default=10, nullable=False)
    results_summary = Column(Text, nullable=False)
    outcome = Column(String(32), default="VALIDATED", nullable=False) # NOT_VALIDATED, VALIDATING, VALIDATED, INVALIDATED, INCONCLUSIVE
    confidence_pct = Column(Float, default=85.0, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    validated_at = Column(DateTime, default=utc_now, nullable=False)

    discovery = relationship("ProductDiscovery", back_populates="validations")
    owner = relationship("User", foreign_keys=[owner_id])

# 10. Product Experimentation & A/B Testing
class ProductExperiment(Base):
    __tablename__ = "product_experiments"

    id = Column(String(64), primary_key=True, default=lambda: f"pexp_{uuid.uuid4().hex[:12]}")
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    hypothesis = Column(Text, nullable=False)
    experiment_type = Column(String(32), default="AB_TEST", nullable=False) # AB_TEST, MULTIVARIATE, FEATURE_FLAG, ONBOARDING, PRICING
    primary_metric = Column(String(128), default="conversion_rate", nullable=False)
    status = Column(String(32), default="DRAFT", nullable=False, index=True) # DRAFT, REVIEW, APPROVED, SCHEDULED, RUNNING, PAUSED, COMPLETED, ANALYZED, ARCHIVED
    audience_segment = Column(String(64), default="ALL_USERS", nullable=False)
    start_date = Column(DateTime, default=utc_now, nullable=False)
    end_date = Column(DateTime, nullable=True)
    total_sample_size = Column(Integer, default=0, nullable=False)
    conclusion = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    variants = relationship("ExperimentVariant", back_populates="experiment", cascade="all, delete-orphan")

# 11. Experiment Variants
class ExperimentVariant(Base):
    __tablename__ = "experiment_variants"

    id = Column(String(64), primary_key=True, default=lambda: f"evar_{uuid.uuid4().hex[:12]}")
    experiment_id = Column(String(64), ForeignKey("product_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_name = Column(String(128), nullable=False)
    variant_key = Column(String(32), nullable=False) # control_a, treatment_b
    allocation_pct = Column(Float, default=50.0, nullable=False)
    config_json = Column(Text, server_default="{}", nullable=False)
    impression_count = Column(Integer, default=0, nullable=False)
    conversion_count = Column(Integer, default=0, nullable=False)
    conversion_rate = Column(Float, default=0.0, nullable=False)

    experiment = relationship("ProductExperiment", back_populates="variants")

# 12. Experiment Assignments
class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"

    id = Column(String(64), primary_key=True, default=lambda: f"easn_{uuid.uuid4().hex[:12]}")
    experiment_id = Column(String(64), ForeignKey("product_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(64), ForeignKey("experiment_variants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=utc_now, nullable=False)
    context_json = Column(Text, server_default="{}", nullable=False)

# 13. Experiment Events (Telemetry)
class ExperimentEvent(Base):
    __tablename__ = "experiment_events"

    id = Column(String(64), primary_key=True, default=lambda: f"eevt_{uuid.uuid4().hex[:12]}")
    experiment_id = Column(String(64), ForeignKey("product_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(64), ForeignKey("experiment_variants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_name = Column(String(128), nullable=False)
    metric_value = Column(Float, default=1.0, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

# 14. Product Feature Releases
class ProductRelease(Base):
    __tablename__ = "product_releases"

    id = Column(String(64), primary_key=True, default=lambda: f"prel_{uuid.uuid4().hex[:12]}")
    release_version = Column(String(32), nullable=False, unique=True, index=True) # e.g. v2.4.0
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(32), default="PLANNED", nullable=False, index=True) # DRAFT, PLANNED, READY, RELEASING, RELEASED, ROLLED_BACK
    release_date = Column(DateTime, nullable=True)
    rollout_percentage = Column(Float, default=100.0, nullable=False)
    release_notes = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    retrospectives = relationship("ProductRetrospective", back_populates="release", cascade="all, delete-orphan")

# 15. Product Retrospectives
class ProductRetrospective(Base):
    __tablename__ = "product_retrospectives"

    id = Column(String(64), primary_key=True, default=lambda: f"pret_{uuid.uuid4().hex[:12]}")
    release_id = Column(String(64), ForeignKey("product_releases.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    expected_vs_actual = Column(Text, nullable=False)
    customer_impact_summary = Column(Text, nullable=False)
    lessons_learned = Column(Text, nullable=False)
    action_items_json = Column(Text, server_default="[]", nullable=False)
    conductor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    held_at = Column(DateTime, default=utc_now, nullable=False)

    release = relationship("ProductRelease", back_populates="retrospectives")
    conductor = relationship("User", foreign_keys=[conductor_id])

# 16. Product Event Records (Instrumentation)
class ProductEventRecord(Base):
    __tablename__ = "product_event_records"

    id = Column(String(64), primary_key=True, default=lambda: f"prec_{uuid.uuid4().hex[:12]}")
    event_name = Column(String(128), nullable=False, index=True)
    event_category = Column(String(64), default="USAGE", nullable=False, index=True) # USAGE, ACTIVATION, FUNNEL, RETENTION, EXPERIMENT
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    product_area = Column(String(64), default="CORE_PLATFORM", nullable=False)
    metadata_json = Column(Text, server_default="{}", nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

# 17. Product Decisions
class ProductDecision(Base):
    __tablename__ = "product_decisions"

    id = Column(String(64), primary_key=True, default=lambda: f"pdec_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    problem = Column(Text, nullable=False)
    decision_summary = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    alternatives_considered = Column(Text, nullable=True)
    status = Column(String(32), default="APPROVED", nullable=False) # PROPOSED, APPROVED, REJECTED, SUPERSEDED
    decision_maker_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    decision_date = Column(DateTime, default=utc_now, nullable=False)

    decision_maker = relationship("User", foreign_keys=[decision_maker_id])

# 18. Product Risk Records
class ProductRiskRecord(Base):
    __tablename__ = "product_risk_records"

    id = Column(String(64), primary_key=True, default=lambda: f"prsk_{uuid.uuid4().hex[:12]}")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), default="TECHNICAL", nullable=False) # TECHNICAL, ADOPTION, DELIVERY, DEPENDENCY, MARKET
    severity = Column(String(32), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    likelihood = Column(String(32), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH
    mitigation_plan = Column(Text, nullable=False)
    status = Column(String(32), default="IDENTIFIED", nullable=False, index=True) # IDENTIFIED, ASSESSED, MITIGATING, ACCEPTED, RESOLVED
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
