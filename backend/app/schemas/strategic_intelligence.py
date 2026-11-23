from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Strategic Plan ---
class StrategicPlanBase(BaseModel):
    title: str
    vision: str
    mission: str
    strategic_themes_json: str = "[]"
    time_horizon: str = Field(default="ANNUAL", description="ANNUAL, 3_YEAR, QUARTERLY")
    status: str = Field(default="ACTIVE", description="DRAFT, ACTIVE, UNDER_REVIEW, ARCHIVED")
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class StrategicPlanCreate(StrategicPlanBase):
    pass

class StrategicPlanUpdate(BaseModel):
    title: Optional[str] = None
    vision: Optional[str] = None
    mission: Optional[str] = None
    strategic_themes_json: Optional[str] = None
    time_horizon: Optional[str] = None
    status: Optional[str] = None
    workspace_id: Optional[int] = None

class StrategicPlanResponse(StrategicPlanBase):
    id: str
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    goals_count: int = 0

    model_config = ConfigDict(from_attributes=True)

# --- Strategic Goal ---
class StrategicGoalBase(BaseModel):
    title: str
    description: str
    category: str = Field(..., description="REVENUE, MARKET_SHARE, PRODUCT, RETENTION, EFFICIENCY")
    target_metric: str
    baseline_value: float = 0.0
    target_value: float
    current_value: float = 0.0
    unit: str = "$"
    status: str = Field(default="ACTIVE", description="PLANNED, ACTIVE, AT_RISK, COMPLETED, CANCELLED")
    deadline: Optional[datetime] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class StrategicGoalCreate(StrategicGoalBase):
    plan_id: str

class StrategicGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    status: Optional[str] = None
    deadline: Optional[datetime] = None
    workspace_id: Optional[int] = None

class StrategicGoalResponse(StrategicGoalBase):
    id: str
    plan_id: str
    owner_id: Optional[int] = None
    progress_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Strategic Initiative ---
class StrategicInitiativeBase(BaseModel):
    title: str
    description: str
    priority: str = Field(default="P2_HIGH", description="P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW")
    budget_amount: float = 0.0
    status: str = Field(default="IN_PROGRESS", description="PROPOSED, APPROVED, IN_PROGRESS, BLOCKED, COMPLETED")
    progress_percentage: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class StrategicInitiativeCreate(StrategicInitiativeBase):
    goal_id: str

class StrategicInitiativeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    progress_percentage: Optional[float] = None
    budget_amount: Optional[float] = None
    workspace_id: Optional[int] = None

class StrategicInitiativeResponse(StrategicInitiativeBase):
    id: str
    goal_id: str
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Market Intelligence & Signals ---
class MarketIntelligenceBase(BaseModel):
    title: str
    intelligence_type: str = Field(..., description="TREND, TECH_DISRUPTION, REGULATORY, MACROECONOMIC")
    summary: str
    source_name: str
    source_url: Optional[str] = None
    confidence_score: float = 0.9
    impact_rating: str = Field(default="HIGH", description="LOW, MEDIUM, HIGH, TRANSFORMATIVE")
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class MarketIntelligenceCreate(MarketIntelligenceBase):
    pass

class MarketIntelligenceResponse(MarketIntelligenceBase):
    id: str
    owner_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MarketSignalBase(BaseModel):
    signal_type: str = Field(..., description="GROWTH, PRICING_SHIFT, CUSTOMER_DEMAND, COMPETITOR_MOVE")
    title: str
    observations: str
    trend_direction: str = Field(default="ACCELERATING", description="ACCELERATING, STABLE, DECELERATING")
    urgency: str = Field(default="NEAR_TERM", description="IMMEDIATE, NEAR_TERM, MONITOR")
    is_converted_to_opportunity: bool = False
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class MarketSignalCreate(MarketSignalBase):
    pass

class MarketSignalResponse(MarketSignalBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Competitor ---
class CompetitorBase(BaseModel):
    name: str
    website: Optional[str] = None
    market_position: str = Field(default="CHALLENGER", description="LEADER, CHALLENGER, NICHE, NEW_ENTRANT")
    pricing_model: str = Field(default="PER_SEAT", description="FREEMIUM, PER_SEAT, USAGE_BASED, ENTERPRISE")
    strengths_json: str = "[]"
    weaknesses_json: str = "[]"
    features_diff_json: str = "{}"
    threat_level: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    notes: Optional[str] = None
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorUpdate(BaseModel):
    website: Optional[str] = None
    market_position: Optional[str] = None
    pricing_model: Optional[str] = None
    strengths_json: Optional[str] = None
    weaknesses_json: Optional[str] = None
    features_diff_json: Optional[str] = None
    threat_level: Optional[str] = None
    notes: Optional[str] = None
    workspace_id: Optional[int] = None

class CompetitorResponse(CompetitorBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- SWOT ---
class SWOTEntryBase(BaseModel):
    swot_type: str = Field(..., description="STRENGTH, WEAKNESS, OPPORTUNITY, THREAT")
    title: str
    description: str
    impact: str = Field(default="HIGH", description="LOW, MEDIUM, HIGH")
    evidence_text: Optional[str] = None
    is_ai_generated: bool = False
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class SWOTEntryCreate(SWOTEntryBase):
    pass

class SWOTEntryResponse(SWOTEntryBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Market Sizing ---
class MarketSizingBase(BaseModel):
    market_name: str
    methodology: str = Field(default="BOTTOM_UP", description="TOP_DOWN, BOTTOM_UP, VALUE_BASED")
    tam_cents: int
    sam_cents: int
    som_cents: int
    currency: str = "USD"
    assumptions_json: str = "{}"
    confidence_score: float = 0.85
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class MarketSizingCreate(MarketSizingBase):
    pass

class MarketSizingResponse(MarketSizingBase):
    id: str
    tam_dollars: float = 0.0
    sam_dollars: float = 0.0
    som_dollars: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Opportunities & RICE Prioritization ---
class StrategicOpportunityBase(BaseModel):
    title: str
    description: str
    customer_segment: str = "Enterprise B2B"
    estimated_value_cents: int = 0
    feasibility_score: float = 8.0
    rice_reach: float = 1000.0
    rice_impact: float = 3.0
    rice_confidence: float = 0.8
    rice_effort: float = 2.0
    status: str = Field(default="EVALUATING", description="IDENTIFIED, EVALUATING, APPROVED, IN_PROGRESS, REALIZED, REJECTED")
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class StrategicOpportunityCreate(StrategicOpportunityBase):
    pass

class StrategicOpportunityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    feasibility_score: Optional[float] = None
    rice_reach: Optional[float] = None
    rice_impact: Optional[float] = None
    rice_confidence: Optional[float] = None
    rice_effort: Optional[float] = None
    workspace_id: Optional[int] = None

class StrategicOpportunityResponse(StrategicOpportunityBase):
    id: str
    rice_score: float
    estimated_value: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Scenarios & Decisions ---
class StrategicScenarioBase(BaseModel):
    name: str
    scenario_type: str = Field(default="BASE_CASE", description="BEST_CASE, BASE_CASE, WORST_CASE, MARKET_DISRUPTION")
    description: str
    revenue_multiplier: float = 1.0
    churn_rate_impact: float = 0.0
    assumptions_json: str = "{}"
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class StrategicScenarioCreate(StrategicScenarioBase):
    pass

class StrategicScenarioResponse(StrategicScenarioBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StrategicScenarioCompareResponse(BaseModel):
    scenarios: List[StrategicScenarioResponse]
    baseline_id: Optional[str] = None
    metrics_comparison: Dict[str, Any]

class StrategicDecisionBase(BaseModel):
    title: str
    context: str
    decision_outcome: str
    rationale: str
    decision_date: Optional[datetime] = None
    status: str = Field(default="APPROVED", description="APPROVED, IN_EFFECT, SUPERSEDED, REVERSED")
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class StrategicDecisionCreate(StrategicDecisionBase):
    pass

class StrategicDecisionResponse(StrategicDecisionBase):
    id: str
    decision_maker_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Business KPIs ---
class BusinessKPIBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = Field(default="GROWTH", description="REVENUE, GROWTH, CUSTOMER, PRODUCT, OPERATIONAL")
    measurement_unit: str = "units"
    target_value: float = 0.0
    current_value: float = 0.0
    baseline_value: float = 0.0
    trend_direction: str = Field(default="UP", description="UP, DOWN, STABLE")
    status: str = Field(default="ON_TRACK", description="ON_TRACK, AT_RISK, BEHIND, EXCEEDED")
    organization_id: Optional[int] = None
    workspace_id: Optional[int] = None

class BusinessKPICreate(BusinessKPIBase):
    pass

class BusinessKPIUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    measurement_unit: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    baseline_value: Optional[float] = None
    trend_direction: Optional[str] = None
    status: Optional[str] = None
    workspace_id: Optional[int] = None

class BusinessKPIValueBase(BaseModel):
    value: float
    period_date: str
    notes: Optional[str] = None

class BusinessKPIValueCreate(BusinessKPIValueBase):
    pass

class BusinessKPIValueResponse(BusinessKPIValueBase):
    id: str
    kpi_id: str
    recorded_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BusinessKPIResponse(BusinessKPIBase):
    id: str
    owner_id: Optional[int] = None
    achievement_percentage: float = 0.0
    history: List[BusinessKPIValueResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Dashboard & AI Analyst ---
class AIStrategyRecommendation(BaseModel):
    theme: str
    recommendation: str
    confidence: float
    rationale: str
    grounded_evidence: str

class StrategicDashboardOverviewResponse(BaseModel):
    active_plans_count: int
    total_goals_count: int
    completed_goals_count: int
    goal_completion_rate: float
    active_initiatives_count: int
    active_signals_count: int
    tracked_competitors_count: int
    open_opportunities_count: int
    total_pipeline_value_dollars: float
    swot_summary: Dict[str, int]
    recent_signals: List[MarketSignalResponse] = []
    top_opportunities: List[StrategicOpportunityResponse] = []
    recent_decisions: List[StrategicDecisionResponse] = []
    ai_recommendations: List[AIStrategyRecommendation] = []

class StrategicAIAnalyzeRequest(BaseModel):
    context: Optional[str] = "executive_strategy"
    focus_theme: Optional[str] = None
    include_competitors: bool = True
    include_swot: bool = True
    workspace_id: Optional[int] = None

class StrategicAIAnalyzeResponse(BaseModel):
    summary: str
    recommendations: List[AIStrategyRecommendation]
    strategic_score: float
    identified_risks: List[str]
    identified_opportunities: List[str]
    generated_at: datetime
