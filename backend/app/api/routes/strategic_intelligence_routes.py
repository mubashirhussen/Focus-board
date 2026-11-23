from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.schemas.strategic_intelligence import (
    StrategicPlanCreate,
    StrategicPlanUpdate,
    StrategicPlanResponse,
    StrategicGoalCreate,
    StrategicGoalUpdate,
    StrategicGoalResponse,
    StrategicInitiativeCreate,
    StrategicInitiativeUpdate,
    StrategicInitiativeResponse,
    MarketIntelligenceCreate,
    MarketIntelligenceResponse,
    MarketSignalCreate,
    MarketSignalResponse,
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    SWOTEntryCreate,
    SWOTEntryResponse,
    MarketSizingCreate,
    MarketSizingResponse,
    StrategicOpportunityCreate,
    StrategicOpportunityUpdate,
    StrategicOpportunityResponse,
    StrategicScenarioCreate,
    StrategicScenarioResponse,
    StrategicScenarioCompareResponse,
    StrategicDecisionCreate,
    StrategicDecisionResponse,
    StrategicDashboardOverviewResponse,
    BusinessKPICreate,
    BusinessKPIUpdate,
    BusinessKPIResponse,
    BusinessKPIValueCreate,
    BusinessKPIValueResponse,
    StrategicAIAnalyzeRequest,
    StrategicAIAnalyzeResponse,
)
from app.services.strategic_intelligence_service import StrategicIntelligenceService

router = APIRouter(prefix="/strategy", tags=["SaaS Platform Strategic Intelligence"])

def resolve_tenant_org_id(db: Session, current_user: User, explicit_org_id: Optional[int] = None) -> Optional[int]:
    """
    Resolve and enforce organization / workspace tenant boundary for current_user.
    If explicit_org_id is provided, validates that user belongs to that workspace/organization.
    Raises 403 Forbidden if unauthorized.
    """
    if explicit_org_id is not None:
        if getattr(current_user, "role", None) in ["Admin", "Owner", "admin"]:
            return explicit_org_id
        # Check workspace membership
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == explicit_org_id,
            WorkspaceMember.user_id == current_user.id
        ).first()
        if member:
            return explicit_org_id
        # Check workspace ownership
        ws = db.query(Workspace).filter(
            Workspace.id == explicit_org_id,
            Workspace.owner_id == current_user.id
        ).first()
        if ws:
            return explicit_org_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have authorization for this organization or workspace context."
        )

    # Resolve user's primary workspace if present
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).first()
    if member:
        return member.workspace_id
    ws = db.query(Workspace).filter(Workspace.owner_id == current_user.id).first()
    if ws:
        return ws.id
    return None

# --- Overview ---
@router.get("/overview", response_model=StrategicDashboardOverviewResponse)
def get_strategic_overview(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve executive strategic overview: goals progress, competitive threats, opportunities, market sizing, and grounded AI strategic guidance."""
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.get_dashboard_overview(db, organization_id=org_id, workspace_id=workspace_id)

# --- Plans & Goals ---
@router.get("/plans", response_model=List[StrategicPlanResponse])
def list_strategic_plans(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_plans(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/plans", response_model=StrategicPlanResponse, status_code=status.HTTP_201_CREATED)
def create_strategic_plan(
    data: StrategicPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_plan(db, data, owner_id=current_user.id, organization_id=org_id, workspace_id=data.workspace_id)

@router.patch("/plans/{plan_id}", response_model=StrategicPlanResponse)
def update_strategic_plan(
    plan_id: str,
    data: StrategicPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = StrategicIntelligenceService.update_plan(db, plan_id, data)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategic plan '{plan_id}' not found.")
    return plan

@router.get("/goals", response_model=List[StrategicGoalResponse])
def list_strategic_goals(
    plan_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_goals(db, plan_id=plan_id, status=status, organization_id=org_id, workspace_id=workspace_id)

@router.post("/goals", response_model=StrategicGoalResponse, status_code=status.HTTP_201_CREATED)
def create_strategic_goal(
    data: StrategicGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_goal(db, data, owner_id=current_user.id, organization_id=org_id, workspace_id=data.workspace_id)

@router.patch("/goals/{goal_id}", response_model=StrategicGoalResponse)
def update_strategic_goal(
    goal_id: str,
    data: StrategicGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = StrategicIntelligenceService.update_goal(db, goal_id, data)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategic goal '{goal_id}' not found.")
    return goal

@router.get("/initiatives", response_model=List[StrategicInitiativeResponse])
def list_initiatives(
    goal_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_initiatives(db, goal_id=goal_id, priority=priority, organization_id=org_id, workspace_id=workspace_id)

@router.post("/initiatives", response_model=StrategicInitiativeResponse, status_code=status.HTTP_201_CREATED)
def create_initiative(
    data: StrategicInitiativeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_initiative(db, data, lead_id=current_user.id, organization_id=org_id, workspace_id=data.workspace_id)

@router.patch("/initiatives/{init_id}", response_model=StrategicInitiativeResponse)
def update_initiative(
    init_id: str,
    data: StrategicInitiativeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    init = StrategicIntelligenceService.update_initiative(db, init_id, data)
    if not init:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategic initiative '{init_id}' not found.")
    return init

# --- Market Intel & Signals ---
@router.get("/market-intel", response_model=List[MarketIntelligenceResponse])
def list_market_intelligence(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_market_intelligence(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/market-intel", response_model=MarketIntelligenceResponse, status_code=status.HTTP_201_CREATED)
def create_market_intelligence(
    data: MarketIntelligenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_market_intelligence(db, data, owner_id=current_user.id, organization_id=org_id, workspace_id=data.workspace_id)

@router.get("/signals", response_model=List[MarketSignalResponse])
def list_market_signals(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_market_signals(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/signals", response_model=MarketSignalResponse, status_code=status.HTTP_201_CREATED)
def create_market_signal(
    data: MarketSignalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_market_signal(db, data, organization_id=org_id, workspace_id=data.workspace_id)

# --- Competitors ---
@router.get("/competitors", response_model=List[CompetitorResponse])
def list_competitors(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_competitors(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/competitors", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
def create_competitor(
    data: CompetitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_competitor(db, data, organization_id=org_id, workspace_id=data.workspace_id)

@router.patch("/competitors/{comp_id}", response_model=CompetitorResponse)
def update_competitor(
    comp_id: str,
    data: CompetitorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comp = StrategicIntelligenceService.update_competitor(db, comp_id, data)
    if not comp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Competitor '{comp_id}' not found.")
    return comp

# --- SWOT Analysis ---
@router.get("/swot", response_model=List[SWOTEntryResponse])
def list_swot(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_swot(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/swot", response_model=SWOTEntryResponse, status_code=status.HTTP_201_CREATED)
def create_swot_entry(
    data: SWOTEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_swot(db, data, organization_id=org_id, workspace_id=data.workspace_id)

# --- Market Sizing ---
@router.get("/market-sizing", response_model=List[MarketSizingResponse])
def list_market_sizing(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_market_sizings(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/market-sizing", response_model=MarketSizingResponse, status_code=status.HTTP_201_CREATED)
def create_market_sizing(
    data: MarketSizingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_market_sizing(db, data, organization_id=org_id, workspace_id=data.workspace_id)

# --- Opportunities & RICE Prioritization ---
@router.get("/opportunities", response_model=List[StrategicOpportunityResponse])
def list_opportunities(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_opportunities(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/opportunities", response_model=StrategicOpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    data: StrategicOpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_opportunity(db, data, organization_id=org_id, workspace_id=data.workspace_id)

@router.patch("/opportunities/{opp_id}", response_model=StrategicOpportunityResponse)
def update_opportunity(
    opp_id: str,
    data: StrategicOpportunityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opp = StrategicIntelligenceService.update_opportunity(db, opp_id, data)
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategic opportunity '{opp_id}' not found.")
    return opp

# --- Scenarios & Decisions ---
@router.get("/scenarios", response_model=List[StrategicScenarioResponse])
def list_scenarios(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_scenarios(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/scenarios", response_model=StrategicScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    data: StrategicScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_scenario(db, data, organization_id=org_id, workspace_id=data.workspace_id)

@router.post("/scenarios/compare", response_model=StrategicScenarioCompareResponse)
def compare_scenarios(
    scenario_ids: Optional[List[str]] = None,
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.compare_scenarios(db, scenario_ids=scenario_ids, organization_id=org_id, workspace_id=workspace_id)

@router.get("/decisions", response_model=List[StrategicDecisionResponse])
def list_decisions(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_decisions(db, organization_id=org_id, workspace_id=workspace_id)

@router.post("/decisions", response_model=StrategicDecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    data: StrategicDecisionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_decision(db, data, user_id=current_user.id, organization_id=org_id, workspace_id=data.workspace_id)

# --- Business KPIs ---
@router.get("/kpis", response_model=List[BusinessKPIResponse])
def list_business_kpis(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, workspace_id)
    return StrategicIntelligenceService.list_kpis(db, category=category, status=status, organization_id=org_id, workspace_id=workspace_id)

@router.post("/kpis", response_model=BusinessKPIResponse, status_code=status.HTTP_201_CREATED)
def create_business_kpi(
    data: BusinessKPICreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, data.workspace_id or data.organization_id)
    return StrategicIntelligenceService.create_kpi(db, data, owner_id=current_user.id, organization_id=org_id, workspace_id=data.workspace_id)

@router.patch("/kpis/{kpi_id}", response_model=BusinessKPIResponse)
def update_business_kpi(
    kpi_id: str,
    data: BusinessKPIUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kpi = StrategicIntelligenceService.update_kpi(db, kpi_id, data)
    if not kpi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Business KPI '{kpi_id}' not found.")
    return kpi

@router.post("/kpis/{kpi_id}/values", response_model=BusinessKPIValueResponse, status_code=status.HTTP_201_CREATED)
def record_kpi_value(
    kpi_id: str,
    data: BusinessKPIValueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return StrategicIntelligenceService.record_kpi_value(db, kpi_id, data, user_id=current_user.id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

# --- AI Strategy Analyzer ---
@router.post("/ai/analyze", response_model=StrategicAIAnalyzeResponse)
def analyze_strategy_with_ai(
    req: StrategicAIAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = resolve_tenant_org_id(db, current_user, req.workspace_id)
    return StrategicIntelligenceService.analyze_strategy_with_ai(db, req, organization_id=org_id)
