from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Innovation Idea ---
class InnovationIdeaBase(BaseModel):
    title: str
    problem_statement: str
    proposed_solution: str
    category: str = Field(default="PRODUCT", description="PRODUCT, AI, TECHNICAL, BUSINESS, PROCESS, UX")
    stage: str = Field(default="CAPTURE", description="CAPTURE, SCREENING, RESEARCH, HYPOTHESIS, EXPERIMENTATION, PROTOTYPE, VALIDATED, ROADMAP, REJECTED")
    target_audience: str = "Enterprise Teams"
    estimated_effort: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    strategic_value: str = Field(default="SUBSTANTIAL", description="INCREMENTAL, SUBSTANTIAL, TRANSFORMATIVE")

class InnovationIdeaCreate(InnovationIdeaBase):
    pass

class InnovationIdeaUpdate(BaseModel):
    title: Optional[str] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None
    category: Optional[str] = None
    stage: Optional[str] = None
    target_audience: Optional[str] = None
    estimated_effort: Optional[str] = None
    strategic_value: Optional[str] = None

class InnovationIdeaResponse(InnovationIdeaBase):
    id: str
    owner_id: Optional[int] = None
    roadmap_item_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    hypotheses_count: int = 0
    experiments_count: int = 0

    model_config = ConfigDict(from_attributes=True)

# --- Innovation Hypothesis ---
class InnovationHypothesisBase(BaseModel):
    statement: str = Field(..., description="We believe [target] will [behavior] because [reason]...")
    measurable_criterion: str
    confidence_score: float = 0.8
    status: str = Field(default="UNTESTED", description="UNTESTED, TESTING, VALIDATED, INVALIDATED")

class InnovationHypothesisCreate(InnovationHypothesisBase):
    idea_id: str

class InnovationHypothesisUpdate(BaseModel):
    statement: Optional[str] = None
    measurable_criterion: Optional[str] = None
    confidence_score: Optional[float] = None
    status: Optional[str] = None

class InnovationHypothesisResponse(InnovationHypothesisBase):
    id: str
    idea_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Innovation Experiment ---
class InnovationExperimentBase(BaseModel):
    name: str
    experiment_type: str = Field(default="CUSTOMER_INTERVIEW", description="CUSTOMER_INTERVIEW, SURVEY, PROTOTYPE_TEST, A_B_TEST, TECHNICAL_POC, LANDING_PAGE")
    methodology: str
    sample_size: int = 25
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = Field(default="RUNNING", description="DRAFT, RUNNING, COMPLETED, CANCELLED")
    budget_spent: float = 0.0

class InnovationExperimentCreate(InnovationExperimentBase):
    idea_id: str
    hypothesis_id: Optional[str] = None

class InnovationExperimentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    budget_spent: Optional[float] = None
    methodology: Optional[str] = None

class InnovationExperimentResponse(InnovationExperimentBase):
    id: str
    idea_id: str
    hypothesis_id: Optional[str] = None
    created_at: datetime
    has_results: bool = False

    model_config = ConfigDict(from_attributes=True)

# --- Experiment Results ---
class InnovationExperimentResultBase(BaseModel):
    quantitative_summary: str
    qualitative_feedback: str
    success_criteria_met: bool = True
    evidence_attachment_url: Optional[str] = None
    lessons_learned: str

class InnovationExperimentResultCreate(InnovationExperimentResultBase):
    experiment_id: str

class InnovationExperimentResultResponse(InnovationExperimentResultBase):
    id: str
    experiment_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Prototype ---
class InnovationPrototypeBase(BaseModel):
    name: str
    prototype_type: str = Field(default="INTERACTIVE_MOCKUP", description="UX_FIGMA, INTERACTIVE_MOCKUP, TECHNICAL_POC, AI_AGENT_PROTOTYPE")
    demo_url: Optional[str] = None
    repository_url: Optional[str] = None
    tech_stack: str = "React + FastAPI"
    status: str = Field(default="BUILDING", description="PLANNING, BUILDING, TESTING, APPROVED, ARCHIVED")

class InnovationPrototypeCreate(InnovationPrototypeBase):
    idea_id: str

class InnovationPrototypeUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    demo_url: Optional[str] = None
    repository_url: Optional[str] = None
    tech_stack: Optional[str] = None

class InnovationPrototypeResponse(InnovationPrototypeBase):
    id: str
    idea_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Validation ---
class InnovationValidationBase(BaseModel):
    dimension: str = Field(..., description="PROBLEM, CUSTOMER, MARKET, TECHNICAL, BUSINESS, SECURITY")
    criteria: str
    status: str = Field(default="PASSED", description="NOT_STARTED, IN_PROGRESS, PASSED, FAILED, NEEDS_EVIDENCE")
    confidence: float = 0.9
    notes: Optional[str] = None

class InnovationValidationCreate(InnovationValidationBase):
    idea_id: str

class InnovationValidationResponse(InnovationValidationBase):
    id: str
    idea_id: str
    reviewer_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Portfolio ---
class InnovationPortfolioBase(BaseModel):
    name: str
    focus_area: str
    budget_limit: float = 50000.0

class InnovationPortfolioCreate(InnovationPortfolioBase):
    pass

class InnovationPortfolioResponse(InnovationPortfolioBase):
    id: str
    allocated_spend: float = 0.0
    active_ideas_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Roadmap Promotion ---
class PromoteIdeaToRoadmapRequest(BaseModel):
    roadmap_category: str = "Innovation"
    target_status: str = "PLANNED"

class PromoteIdeaToRoadmapResponse(BaseModel):
    idea_id: str
    roadmap_item_id: int
    title: str
    promoted_at: datetime

# --- Innovation Dashboard Overview ---
class InnovationDashboardOverviewResponse(BaseModel):
    total_ideas_count: int
    active_experiments_count: int
    completed_experiments_count: int
    validated_ideas_count: int
    prototypes_building_count: int
    experiment_success_rate: float
    pipeline_stage_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    recent_ideas: List[InnovationIdeaResponse] = []
    active_experiments: List[InnovationExperimentResponse] = []
    recent_prototypes: List[InnovationPrototypeResponse] = []
