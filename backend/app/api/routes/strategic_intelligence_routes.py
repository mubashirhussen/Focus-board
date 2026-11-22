from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.strategic_intelligence import (
    StrategicPlanCreate,
    StrategicPlanResponse,
    StrategicGoalCreate,
    StrategicGoalResponse,
    StrategicInitiativeCreate,
    StrategicInitiativeResponse,
    MarketIntelligenceCreate,
    MarketIntelligenceResponse,
    MarketSignalCreate,
    MarketSignalResponse,
    CompetitorCreate,
    CompetitorResponse,
    SWOTEntryCreate,
    SWOTEntryResponse,
    MarketSizingCreate,
    MarketSizingResponse,
    StrategicOpportunityCreate,
    StrategicOpportunityResponse,
    StrategicScenarioCreate,
    StrategicScenarioResponse,
    StrategicDecisionCreate,
    StrategicDecisionResponse,
    StrategicDashboardOverviewResponse,
)
from app.services.strategic_intelligence_service import StrategicIntelligenceService

router = APIRouter(prefix="/strategy", tags=["SaaS Platform Strategic Intelligence"])

# --- Overview ---
@router.get("/overview", response_model=StrategicDashboardOverviewResponse)
def get_strategic_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve executive strategic overview: goals progress, competitive threats, opportunities, market sizing, and grounded AI strategic guidance."""
    return StrategicIntelligenceService.get_dashboard_overview(db)

# --- Plans & Goals ---
@router.get("/plans", response_model=List[StrategicPlanResponse])
def list_strategic_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_plans(db)

@router.post("/plans", response_model=StrategicPlanResponse, status_code=status.HTTP_201_CREATED)
def create_strategic_plan(
    data: StrategicPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_plan(db, data, owner_id=current_user.id)

@router.get("/goals", response_model=List[StrategicGoalResponse])
def list_strategic_goals(
    plan_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_goals(db, plan_id=plan_id, status=status)

@router.post("/goals", response_model=StrategicGoalResponse, status_code=status.HTTP_201_CREATED)
def create_strategic_goal(
    data: StrategicGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_goal(db, data, owner_id=current_user.id)

@router.get("/initiatives", response_model=List[StrategicInitiativeResponse])
def list_initiatives(
    goal_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_initiatives(db, goal_id=goal_id, priority=priority)

@router.post("/initiatives", response_model=StrategicInitiativeResponse, status_code=status.HTTP_201_CREATED)
def create_initiative(
    data: StrategicInitiativeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_initiative(db, data, lead_id=current_user.id)

# --- Market Intel & Signals ---
@router.get("/market-intel", response_model=List[MarketIntelligenceResponse])
def list_market_intelligence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_market_intelligence(db)

@router.post("/market-intel", response_model=MarketIntelligenceResponse, status_code=status.HTTP_201_CREATED)
def create_market_intelligence(
    data: MarketIntelligenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_market_intelligence(db, data, owner_id=current_user.id)

@router.get("/signals", response_model=List[MarketSignalResponse])
def list_market_signals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_market_signals(db)

@router.post("/signals", response_model=MarketSignalResponse, status_code=status.HTTP_201_CREATED)
def create_market_signal(
    data: MarketSignalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_market_signal(db, data)

# --- Competitors ---
@router.get("/competitors", response_model=List[CompetitorResponse])
def list_competitors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_competitors(db)

@router.post("/competitors", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
def create_competitor(
    data: CompetitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_competitor(db, data)

# --- SWOT Analysis ---
@router.get("/swot", response_model=List[SWOTEntryResponse])
def list_swot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_swot(db)

@router.post("/swot", response_model=SWOTEntryResponse, status_code=status.HTTP_201_CREATED)
def create_swot_entry(
    data: SWOTEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_swot(db, data)

# --- Market Sizing ---
@router.get("/market-sizing", response_model=List[MarketSizingResponse])
def list_market_sizing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_market_sizings(db)

@router.post("/market-sizing", response_model=MarketSizingResponse, status_code=status.HTTP_201_CREATED)
def create_market_sizing(
    data: MarketSizingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_market_sizing(db, data)

# --- Opportunities & RICE Prioritization ---
@router.get("/opportunities", response_model=List[StrategicOpportunityResponse])
def list_opportunities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_opportunities(db)

@router.post("/opportunities", response_model=StrategicOpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    data: StrategicOpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_opportunity(db, data)

# --- Scenarios & Decisions ---
@router.get("/scenarios", response_model=List[StrategicScenarioResponse])
def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return []

@router.post("/scenarios", response_model=StrategicScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    data: StrategicScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return None

@router.get("/decisions", response_model=List[StrategicDecisionResponse])
def list_decisions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.list_decisions(db)

@router.post("/decisions", response_model=StrategicDecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    data: StrategicDecisionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StrategicIntelligenceService.create_decision(db, data, user_id=current_user.id)
