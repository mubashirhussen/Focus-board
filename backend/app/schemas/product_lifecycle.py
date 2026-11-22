from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# 1. Product Discovery Schemas
class ProductDiscoveryCreate(BaseModel):
    title: str
    problem_statement: str
    hypothesis: str
    target_users: str
    customer_segment: str = "ENTERPRISE"
    business_impact: str
    customer_impact: str
    status: str = "DISCOVERED"
    organization_id: Optional[int] = None

class ProductDiscoveryUpdate(BaseModel):
    title: Optional[str] = None
    problem_statement: Optional[str] = None
    hypothesis: Optional[str] = None
    status: Optional[str] = None
    business_impact: Optional[str] = None
    customer_impact: Optional[str] = None

class ProductDiscoveryResponse(BaseModel):
    id: str
    title: str
    problem_statement: str
    hypothesis: str
    target_users: str
    customer_segment: str
    business_impact: str
    customer_impact: str
    status: str
    owner_id: Optional[int] = None
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 2. Product Idea Schemas
class ProductIdeaCreate(BaseModel):
    discovery_id: Optional[str] = None
    title: str
    description: str
    problem_statement: str
    proposed_solution: str
    product_area: str = "CORE_PLATFORM"
    category: str = "PRODUCTIVITY"
    priority: str = "MEDIUM"
    status: str = "NEW"
    tags_json: Optional[str] = "[]"

class ProductIdeaUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    proposed_solution: Optional[str] = None

class ProductIdeaResponse(BaseModel):
    id: str
    discovery_id: Optional[str] = None
    title: str
    description: str
    problem_statement: str
    proposed_solution: str
    product_area: str
    category: str
    priority: str
    status: str
    owner_id: Optional[int] = None
    tags_json: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 3. Product Feature Request Schemas
class ProductFeatureRequestCreate(BaseModel):
    title: str
    description: str
    customer_name: str
    customer_segment: str = "ENTERPRISE"
    source: str = "CUSTOMER_FEEDBACK"
    request_count: int = 1
    priority: str = "MEDIUM"
    status: str = "NEW"
    business_impact: Optional[str] = None
    revenue_impact: float = 0.0
    linked_idea_id: Optional[str] = None

class ProductFeatureRequestUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    request_count: Optional[int] = None
    merged_into_id: Optional[str] = None

class ProductFeatureRequestResponse(BaseModel):
    id: str
    title: str
    description: str
    customer_name: str
    customer_segment: str
    source: str
    request_count: int
    priority: str
    status: str
    business_impact: Optional[str] = None
    revenue_impact: float
    merged_into_id: Optional[str] = None
    linked_idea_id: Optional[str] = None
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 4. Product Opportunity Schemas
class ProductOpportunityCreate(BaseModel):
    title: str
    description: str
    problem_statement: str
    customer_segment: str = "ALL"
    market_segment: str = "B2B_SAAS"
    product_area: str = "CORE_PLATFORM"
    business_impact: str
    customer_impact: str
    revenue_potential: float = 0.0
    effort_estimate: str = "MEDIUM"
    risk_level: str = "LOW"
    validation_status: str = "IDENTIFIED"
    priority: str = "MEDIUM"

class ProductOpportunityResponse(BaseModel):
    id: str
    title: str
    description: str
    problem_statement: str
    customer_segment: str
    market_segment: str
    product_area: str
    business_impact: str
    customer_impact: str
    revenue_potential: float
    effort_estimate: str
    risk_level: str
    validation_status: str
    priority: str
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 5. Prioritization Item Schemas
class ProductPrioritizationItemCreate(BaseModel):
    item_type: str = "FEATURE_REQUEST"
    item_id: str
    title: str
    reach: float = 100.0
    impact: float = 3.0
    confidence: float = 0.8
    effort: float = 2.0
    ease: float = 3.0
    moscow_category: str = "SHOULD_HAVE"
    weighted_score: float = 75.0
    priority_rank: int = 1
    notes: Optional[str] = None

class ProductPrioritizationItemResponse(BaseModel):
    id: str
    item_type: str
    item_id: str
    title: str
    reach: float
    impact: float
    confidence: float
    effort: float
    rice_score: float
    ease: float
    ice_score: float
    moscow_category: str
    weighted_score: float
    priority_rank: int
    notes: Optional[str] = None
    evaluated_by_id: Optional[int] = None
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 6. Strategic Product Initiative Schemas
class ProductInitiativeCreate(BaseModel):
    title: str
    description: str
    strategic_objective: str
    priority: str = "HIGH"
    status: str = "IN_PROGRESS"
    progress_pct: float = 0.0
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None

class ProductInitiativeResponse(BaseModel):
    id: str
    title: str
    description: str
    strategic_objective: str
    priority: str
    status: str
    progress_pct: float
    owner_id: Optional[int] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 7. Roadmap & Dependencies Schemas
class LifecycleRoadmapItemCreate(BaseModel):
    initiative_id: Optional[str] = None
    title: str
    description: str
    product_area: str = "CORE_PLATFORM"
    status: str = "PLANNED"
    priority: str = "MEDIUM"
    quarter: str = "Q1-2027"
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    progress_pct: float = 0.0

class LifecycleRoadmapItemResponse(BaseModel):
    id: str
    initiative_id: Optional[str] = None
    title: str
    description: str
    product_area: str
    status: str
    priority: str
    quarter: str
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    progress_pct: float
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoadmapDependencyCreate(BaseModel):
    roadmap_item_id: str
    depends_on_item_id: str
    dependency_type: str = "BLOCKS"
    risk_level: str = "MEDIUM"
    notes: Optional[str] = None

class RoadmapDependencyResponse(BaseModel):
    id: str
    roadmap_item_id: str
    depends_on_item_id: str
    dependency_type: str
    status: str
    risk_level: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 8. Experimentation & A/B Testing Schemas
class ExperimentVariantCreate(BaseModel):
    variant_name: str
    variant_key: str
    allocation_pct: float = 50.0
    config_json: Optional[str] = "{}"

class ExperimentVariantResponse(BaseModel):
    id: str
    experiment_id: str
    variant_name: str
    variant_key: str
    allocation_pct: float
    config_json: str
    impression_count: int
    conversion_count: int
    conversion_rate: float

    model_config = ConfigDict(from_attributes=True)

class ProductExperimentCreate(BaseModel):
    name: str
    description: str
    hypothesis: str
    experiment_type: str = "AB_TEST"
    primary_metric: str = "conversion_rate"
    status: str = "RUNNING"
    audience_segment: str = "ALL_USERS"
    variants: List[ExperimentVariantCreate] = []

class ProductExperimentResponse(BaseModel):
    id: str
    name: str
    description: str
    hypothesis: str
    experiment_type: str
    primary_metric: str
    status: str
    audience_segment: str
    start_date: datetime
    end_date: Optional[datetime] = None
    total_sample_size: int
    conclusion: Optional[str] = None
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    variants: List[ExperimentVariantResponse] = []

    model_config = ConfigDict(from_attributes=True)

# 9. Product Releases & Retrospectives Schemas
class ProductReleaseCreate(BaseModel):
    release_version: str
    title: str
    description: str
    status: str = "PLANNED"
    release_date: Optional[datetime] = None
    rollout_percentage: float = 100.0
    release_notes: str

class ProductReleaseResponse(BaseModel):
    id: str
    release_version: str
    title: str
    description: str
    status: str
    release_date: Optional[datetime] = None
    rollout_percentage: float
    release_notes: str
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 10. AI Product Assistant Query
class AIProductAssistantRequest(BaseModel):
    query: str
    context_type: Optional[str] = "PRODUCT_OVERVIEW"

class AIProductAssistantResponse(BaseModel):
    query: str
    answer: str
    total_discoveries: int
    total_ideas: int
    total_feature_requests: int
    active_experiments: int
    recommended_roadmap_actions: List[str] = []
    grounded_evidence: Dict[str, Any] = {}
