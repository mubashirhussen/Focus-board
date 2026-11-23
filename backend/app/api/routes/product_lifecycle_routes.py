from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember
from app.models.product_lifecycle import (
    ProductDiscovery,
    ProductIdea,
    ProductFeatureRequest,
    ProductOpportunity,
    ProductPrioritizationItem,
    ProductInitiative,
    LifecycleRoadmapItem,
    RoadmapDependency,
    ProductExperiment,
    ExperimentVariant,
    ProductRelease,
    ProductDecision,
    ProductRiskRecord,
)
from app.schemas.product_lifecycle import (
    ProductDiscoveryCreate,
    ProductDiscoveryUpdate,
    ProductDiscoveryResponse,
    ProductIdeaCreate,
    ProductIdeaUpdate,
    ProductIdeaResponse,
    IdeaConvertRequest,
    IdeaConvertResponse,
    ProductFeatureRequestCreate,
    ProductFeatureRequestUpdate,
    ProductFeatureRequestResponse,
    ProductOpportunityCreate,
    ProductOpportunityUpdate,
    ProductOpportunityResponse,
    ProductPrioritizationItemCreate,
    ProductPrioritizationItemResponse,
    ProductInitiativeCreate,
    ProductInitiativeUpdate,
    ProductInitiativeResponse,
    LifecycleRoadmapItemCreate,
    LifecycleRoadmapItemUpdate,
    LifecycleRoadmapItemResponse,
    RoadmapDependencyCreate,
    RoadmapDependencyResponse,
    RoadmapReorderRequest,
    ProductExperimentCreate,
    ProductExperimentUpdate,
    ProductExperimentResponse,
    ExperimentVariantResponse,
    ExperimentStatisticalAnalysisResponse,
    ProductReleaseCreate,
    ProductReleaseUpdate,
    ProductReleaseResponse,
    ReleaseReadinessResponse,
    ProductDecisionCreate,
    ProductDecisionResponse,
    ProductRiskCreate,
    ProductRiskResponse,
    AIProductAssistantRequest,
    AIProductAssistantResponse,
)
from app.services.product_lifecycle_service import ProductLifecycleService

router = APIRouter()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def resolve_tenant_org_id(db: Session, current_user: User, explicit_org_id: Optional[int] = None) -> int:
    """
    Resolve and enforce organization / workspace tenant boundary for current_user.
    If explicit_org_id is provided, validates that user belongs to that workspace/organization.
    Raises 403 Forbidden if unauthorized.
    """
    if explicit_org_id is not None:
        if getattr(current_user, "role", None) == "admin":
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
            detail="Access denied: You do not have authorization for this organization context."
        )

    # Resolve user's primary workspace
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).first()
    if member:
        return member.workspace_id
    ws = db.query(Workspace).filter(Workspace.owner_id == current_user.id).first()
    if ws:
        return ws.id
    # Default to user's personal ID as fallback tenant boundary
    return current_user.id

# ----------------- OVERVIEW -----------------
@router.get("/overview", response_model=Dict[str, Any])
def get_lifecycle_overview(
    organization_id: Optional[int] = Query(None),
    workspace_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve aggregate product lifecycle pipeline metrics scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    return ProductLifecycleService.get_lifecycle_overview(db, organization_id=org_id, workspace_id=workspace_id)

# ----------------- DISCOVERIES -----------------
@router.get("/discoveries", response_model=List[ProductDiscoveryResponse])
def list_discoveries(
    status_filter: Optional[str] = None,
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product discoveries scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductDiscovery).filter(ProductDiscovery.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductDiscovery.workspace_id == workspace_id)
    if status_filter:
        query = query.filter(ProductDiscovery.status == status_filter)
    return query.order_by(desc(ProductDiscovery.created_at)).all()

@router.post("/discoveries", response_model=ProductDiscoveryResponse, status_code=status.HTTP_201_CREATED)
def create_discovery(
    disc_in: ProductDiscoveryCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a new customer problem discovery and opportunity hypothesis."""
    org_id = resolve_tenant_org_id(db, current_user, disc_in.organization_id or organization_id or x_organization_id)
    data = disc_in.model_dump()
    data.pop("organization_id", None)
    disc = ProductDiscovery(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(disc)
    db.commit()
    db.refresh(disc)
    return disc

@router.get("/discoveries/{discovery_id}", response_model=ProductDiscoveryResponse)
def get_discovery(
    discovery_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve discovery by ID with tenant scoping."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    disc = db.query(ProductDiscovery).filter(
        ProductDiscovery.id == discovery_id,
        ProductDiscovery.organization_id == org_id
    ).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Discovery not found or unauthorized.")
    return disc

@router.patch("/discoveries/{discovery_id}", response_model=ProductDiscoveryResponse)
def update_discovery(
    discovery_id: str,
    disc_update: ProductDiscoveryUpdate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update discovery status or hypothesis with transition check."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    disc = db.query(ProductDiscovery).filter(
        ProductDiscovery.id == discovery_id,
        ProductDiscovery.organization_id == org_id
    ).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Discovery not found or unauthorized.")

    update_dict = disc_update.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"]:
        if not ProductLifecycleService.validate_stage_transition("discovery", disc.status, update_dict["status"]):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid discovery stage transition from {disc.status} to {update_dict['status']}"
            )

    for k, v in update_dict.items():
        setattr(disc, k, v)
    disc.updated_at = utc_now()
    db.commit()
    db.refresh(disc)
    return disc

@router.delete("/discoveries/{discovery_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discovery(
    discovery_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a discovery record with tenant check."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    disc = db.query(ProductDiscovery).filter(
        ProductDiscovery.id == discovery_id,
        ProductDiscovery.organization_id == org_id
    ).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Discovery not found or unauthorized.")
    db.delete(disc)
    db.commit()
    return None

# ----------------- IDEAS -----------------
@router.get("/ideas", response_model=List[ProductIdeaResponse])
def list_ideas(
    status_filter: Optional[str] = None,
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product solution ideas scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductIdea).filter(ProductIdea.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductIdea.workspace_id == workspace_id)
    if status_filter:
        query = query.filter(ProductIdea.status == status_filter)
    return query.order_by(desc(ProductIdea.created_at)).all()

@router.post("/ideas", response_model=ProductIdeaResponse, status_code=status.HTTP_201_CREATED)
def create_idea(
    idea_in: ProductIdeaCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a product concept or solution idea."""
    org_id = resolve_tenant_org_id(db, current_user, idea_in.organization_id or organization_id or x_organization_id)
    if idea_in.discovery_id:
        disc = db.query(ProductDiscovery).filter(
            ProductDiscovery.id == idea_in.discovery_id,
            ProductDiscovery.organization_id == org_id
        ).first()
        if not disc:
            raise HTTPException(status_code=404, detail="Linked discovery not found in current organization.")

    data = idea_in.model_dump()
    data.pop("organization_id", None)
    idea = ProductIdea(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea

@router.get("/ideas/{idea_id}", response_model=ProductIdeaResponse)
def get_idea(
    idea_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve idea by ID with tenant scoping."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    idea = db.query(ProductIdea).filter(
        ProductIdea.id == idea_id,
        ProductIdea.organization_id == org_id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found or unauthorized.")
    return idea

@router.patch("/ideas/{idea_id}", response_model=ProductIdeaResponse)
def update_idea(
    idea_id: str,
    idea_update: ProductIdeaUpdate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update idea properties with transition validation."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    idea = db.query(ProductIdea).filter(
        ProductIdea.id == idea_id,
        ProductIdea.organization_id == org_id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found or unauthorized.")

    update_dict = idea_update.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"]:
        if not ProductLifecycleService.validate_stage_transition("idea", idea.status, update_dict["status"]):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid idea stage transition from {idea.status} to {update_dict['status']}"
            )

    for k, v in update_dict.items():
        setattr(idea, k, v)
    idea.updated_at = utc_now()
    db.commit()
    db.refresh(idea)
    return idea

@router.delete("/ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idea(
    idea_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an idea record with tenant check."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    idea = db.query(ProductIdea).filter(
        ProductIdea.id == idea_id,
        ProductIdea.organization_id == org_id
    ).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found or unauthorized.")
    db.delete(idea)
    db.commit()
    return None

@router.post("/ideas/{idea_id}/convert", response_model=IdeaConvertResponse)
def convert_idea(
    idea_id: str,
    convert_in: IdeaConvertRequest,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert a validated product idea into a Task, Feature Request, or Roadmap Item."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    try:
        return ProductLifecycleService.convert_idea(
            db=db,
            idea_id=idea_id,
            target_type=convert_in.target_type,
            user_id=current_user.id,
            organization_id=org_id,
            workspace_id=convert_in.workspace_id,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

# ----------------- FEATURE REQUESTS -----------------
@router.get("/feature-requests", response_model=List[ProductFeatureRequestResponse])
def list_feature_requests(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List customer feature requests scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductFeatureRequest).filter(ProductFeatureRequest.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductFeatureRequest.workspace_id == workspace_id)
    if status_filter:
        query = query.filter(ProductFeatureRequest.status == status_filter)
    if priority:
        query = query.filter(ProductFeatureRequest.priority == priority)
    return query.order_by(desc(ProductFeatureRequest.request_count)).all()

@router.post("/feature-requests", response_model=ProductFeatureRequestResponse, status_code=status.HTTP_201_CREATED)
def create_feature_request(
    req_in: ProductFeatureRequestCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a customer-demanded feature request."""
    org_id = resolve_tenant_org_id(db, current_user, req_in.organization_id or organization_id or x_organization_id)
    data = req_in.model_dump()
    data.pop("organization_id", None)
    freq = ProductFeatureRequest(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(freq)
    db.commit()
    db.refresh(freq)
    return freq

@router.get("/feature-requests/{request_id}", response_model=ProductFeatureRequestResponse)
def get_feature_request(
    request_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve feature request by ID with tenant scoping."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    freq = db.query(ProductFeatureRequest).filter(
        ProductFeatureRequest.id == request_id,
        ProductFeatureRequest.organization_id == org_id
    ).first()
    if not freq:
        raise HTTPException(status_code=404, detail="Feature request not found or unauthorized.")
    return freq

@router.patch("/feature-requests/{request_id}", response_model=ProductFeatureRequestResponse)
def update_feature_request(
    request_id: str,
    req_update: ProductFeatureRequestUpdate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update feature request status or priority with transition checks."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    freq = db.query(ProductFeatureRequest).filter(
        ProductFeatureRequest.id == request_id,
        ProductFeatureRequest.organization_id == org_id
    ).first()
    if not freq:
        raise HTTPException(status_code=404, detail="Feature request not found or unauthorized.")

    update_dict = req_update.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"]:
        if not ProductLifecycleService.validate_stage_transition("feature_request", freq.status, update_dict["status"]):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feature request transition from {freq.status} to {update_dict['status']}"
            )

    for k, v in update_dict.items():
        setattr(freq, k, v)
    freq.updated_at = utc_now()
    db.commit()
    db.refresh(freq)
    return freq

@router.post("/feature-requests/{request_id}/merge", response_model=ProductFeatureRequestResponse)
def merge_feature_requests(
    request_id: str,
    target_id: str = Query(..., description="ID of primary feature request to merge into"),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hardened merge endpoint with self-merge, cross-tenant, and circularity prevention."""
    if request_id == target_id:
        raise HTTPException(status_code=400, detail="Cannot merge a feature request into itself.")

    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    source_req = db.query(ProductFeatureRequest).filter(
        ProductFeatureRequest.id == request_id,
        ProductFeatureRequest.organization_id == org_id
    ).first()
    target_req = db.query(ProductFeatureRequest).filter(
        ProductFeatureRequest.id == target_id,
        ProductFeatureRequest.organization_id == org_id
    ).first()

    if not source_req or not target_req:
        raise HTTPException(status_code=404, detail="Source or target feature request not found in organization.")

    if source_req.merged_into_id is not None:
        raise HTTPException(status_code=400, detail="Source feature request has already been merged into another record.")

    if target_req.merged_into_id is not None:
        raise HTTPException(status_code=400, detail="Cannot merge into a target that is itself already merged.")

    if target_req.id == source_req.merged_into_id:
        raise HTTPException(status_code=400, detail="Circular merge detected.")

    # Atomic demand and revenue aggregation
    target_req.request_count += source_req.request_count
    target_req.revenue_impact += source_req.revenue_impact
    source_req.merged_into_id = target_req.id
    source_req.status = "DECLINED"
    source_req.updated_at = utc_now()
    target_req.updated_at = utc_now()

    db.commit()
    db.refresh(target_req)
    return target_req

# ----------------- OPPORTUNITIES -----------------
@router.get("/opportunities", response_model=List[ProductOpportunityResponse])
def list_opportunities(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List evaluated market and product opportunities scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductOpportunity).filter(ProductOpportunity.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductOpportunity.workspace_id == workspace_id)
    return query.order_by(desc(ProductOpportunity.created_at)).all()

@router.post("/opportunities", response_model=ProductOpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opp_in: ProductOpportunityCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a qualified product business opportunity."""
    org_id = resolve_tenant_org_id(db, current_user, opp_in.organization_id or organization_id or x_organization_id)
    data = opp_in.model_dump()
    data.pop("organization_id", None)
    opp = ProductOpportunity(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

# ----------------- PRIORITIZATION -----------------
@router.post("/prioritization/calculate", response_model=Dict[str, Any])
def calculate_prioritization(
    reach: float = Query(..., ge=1.0),
    impact: float = Query(..., ge=0.1, le=10.0),
    confidence: float = Query(..., ge=0.01, le=1.0),
    effort: float = Query(..., gt=0.0),
    ease: float = Query(3.0, ge=0.1, le=10.0),
    current_user: User = Depends(get_current_user),
):
    """Calculate RICE, ICE, and weighted priority scores with strict mathematical validation."""
    try:
        return ProductLifecycleService.calculate_prioritization(reach, impact, confidence, effort, ease)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.get("/prioritization/items", response_model=List[ProductPrioritizationItemResponse])
def list_prioritization_items(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List ranked prioritization items scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductPrioritizationItem).filter(ProductPrioritizationItem.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductPrioritizationItem.workspace_id == workspace_id)
    return query.order_by(desc(ProductPrioritizationItem.rice_score)).all()

@router.post("/prioritization/items", response_model=ProductPrioritizationItemResponse, status_code=status.HTTP_201_CREATED)
def score_prioritization_item(
    item_in: ProductPrioritizationItemCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Persist a scored prioritization entry with RICE/ICE evaluation."""
    org_id = resolve_tenant_org_id(db, current_user, item_in.organization_id or organization_id or x_organization_id)
    try:
        scores = ProductLifecycleService.calculate_prioritization(
            item_in.reach, item_in.impact, item_in.confidence, item_in.effort, item_in.ease
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    pitem = ProductPrioritizationItem(
        item_type=item_in.item_type,
        item_id=item_in.item_id,
        title=item_in.title,
        reach=item_in.reach,
        impact=item_in.impact,
        confidence=item_in.confidence,
        effort=item_in.effort,
        rice_score=scores["rice_score"],
        ease=item_in.ease,
        ice_score=scores["ice_score"],
        moscow_category=item_in.moscow_category,
        weighted_score=scores["weighted_score"],
        priority_rank=item_in.priority_rank,
        notes=item_in.notes,
        evaluated_by_id=current_user.id,
        organization_id=org_id,
        workspace_id=item_in.workspace_id,
        evaluated_at=utc_now(),
    )
    db.add(pitem)
    db.commit()
    db.refresh(pitem)
    return pitem

# ----------------- INITIATIVES & ROADMAP -----------------
@router.get("/initiatives", response_model=List[ProductInitiativeResponse])
def list_initiatives(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List strategic product initiatives scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductInitiative).filter(ProductInitiative.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductInitiative.workspace_id == workspace_id)
    return query.order_by(desc(ProductInitiative.created_at)).all()

@router.post("/initiatives", response_model=ProductInitiativeResponse, status_code=status.HTTP_201_CREATED)
def create_initiative(
    init_in: ProductInitiativeCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a high-level strategic product initiative."""
    org_id = resolve_tenant_org_id(db, current_user, init_in.organization_id or organization_id or x_organization_id)
    data = init_in.model_dump()
    data.pop("organization_id", None)
    goal = data.pop("strategic_goal", None)
    if goal and not data.get("strategic_objective"):
        data["strategic_objective"] = goal
    data.pop("target_quarter", None)
    init = ProductInitiative(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(init)
    db.commit()
    db.refresh(init)
    return init

@router.patch("/initiatives/{init_id}", response_model=ProductInitiativeResponse)
def update_initiative(
    init_id: str,
    init_update: ProductInitiativeUpdate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update product initiative."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    init = db.query(ProductInitiative).filter(
        ProductInitiative.id == init_id,
        ProductInitiative.organization_id == org_id
    ).first()
    if not init:
        raise HTTPException(status_code=404, detail="Initiative not found or unauthorized.")
    for k, v in init_update.model_dump(exclude_unset=True).items():
        setattr(init, k, v)
    init.updated_at = utc_now()
    db.commit()
    db.refresh(init)
    return init

@router.delete("/initiatives/{init_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_initiative(
    init_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete product initiative."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    init = db.query(ProductInitiative).filter(
        ProductInitiative.id == init_id,
        ProductInitiative.organization_id == org_id
    ).first()
    if not init:
        raise HTTPException(status_code=404, detail="Initiative not found or unauthorized.")
    db.delete(init)
    db.commit()
    return None

@router.get("/roadmap", response_model=List[LifecycleRoadmapItemResponse])
def list_roadmap_items(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List scheduled roadmap deliverables scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(LifecycleRoadmapItem).filter(LifecycleRoadmapItem.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(LifecycleRoadmapItem.workspace_id == workspace_id)
    return query.order_by(LifecycleRoadmapItem.quarter, LifecycleRoadmapItem.sort_order, LifecycleRoadmapItem.target_date).all()

@router.post("/roadmap", response_model=LifecycleRoadmapItemResponse, status_code=status.HTTP_201_CREATED)
def create_roadmap_item(
    item_in: LifecycleRoadmapItemCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an item to the product roadmap schedule."""
    org_id = resolve_tenant_org_id(db, current_user, item_in.organization_id or organization_id or x_organization_id)
    if item_in.initiative_id:
        init = db.query(ProductInitiative).filter(
            ProductInitiative.id == item_in.initiative_id,
            ProductInitiative.organization_id == org_id
        ).first()
        if not init:
            raise HTTPException(status_code=404, detail="Linked initiative not found in organization.")

    data = item_in.model_dump()
    data.pop("organization_id", None)
    item = LifecycleRoadmapItem(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.patch("/roadmap/{item_id}", response_model=LifecycleRoadmapItemResponse)
def update_roadmap_item(
    item_id: str,
    item_update: LifecycleRoadmapItemUpdate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update roadmap item details."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    item = db.query(LifecycleRoadmapItem).filter(
        LifecycleRoadmapItem.id == item_id,
        LifecycleRoadmapItem.organization_id == org_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found or unauthorized.")
    for k, v in item_update.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    item.updated_at = utc_now()
    db.commit()
    db.refresh(item)
    return item

@router.delete("/roadmap/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roadmap_item(
    item_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete roadmap item."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    item = db.query(LifecycleRoadmapItem).filter(
        LifecycleRoadmapItem.id == item_id,
        LifecycleRoadmapItem.organization_id == org_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found or unauthorized.")
    db.delete(item)
    db.commit()
    return None

@router.post("/roadmap/reorder", response_model=Dict[str, Any])
def reorder_roadmap_items(
    reorder_in: RoadmapReorderRequest,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reorder roadmap items across quarters with drag-and-drop sort order persistence."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    items_list = [itm.model_dump() if hasattr(itm, "model_dump") else itm for itm in reorder_in.items]
    updated = ProductLifecycleService.reorder_roadmap_items(db, items_list, org_id)
    return {"status": "reordered", "count": len(updated)}

# ----------------- ROADMAP DEPENDENCIES -----------------
@router.get("/roadmap/dependencies", response_model=List[RoadmapDependencyResponse])
def list_roadmap_dependencies(
    roadmap_item_id: Optional[str] = Query(None),
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List dependencies between roadmap items scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(RoadmapDependency).join(
        LifecycleRoadmapItem, RoadmapDependency.roadmap_item_id == LifecycleRoadmapItem.id
    ).filter(LifecycleRoadmapItem.organization_id == org_id)
    if roadmap_item_id:
        query = query.filter(
            (RoadmapDependency.roadmap_item_id == roadmap_item_id) |
            (RoadmapDependency.depends_on_item_id == roadmap_item_id)
        )
    if workspace_id is not None:
        query = query.filter(LifecycleRoadmapItem.workspace_id == workspace_id)
    return query.all()

@router.post("/roadmap/dependencies", response_model=RoadmapDependencyResponse, status_code=status.HTTP_201_CREATED)
def create_roadmap_dependency(
    dep_in: RoadmapDependencyCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a dependency relationship between roadmap items with cycle detection."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    try:
        dep = ProductLifecycleService.create_roadmap_dependency(
            db=db,
            roadmap_item_id=dep_in.roadmap_item_id,
            depends_on_item_id=dep_in.depends_on_item_id,
            dependency_type=dep_in.dependency_type,
            risk_level=dep_in.risk_level,
            notes=dep_in.notes,
            organization_id=org_id,
        )
        return dep
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.delete("/roadmap/dependencies/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roadmap_dependency(
    dep_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a roadmap dependency."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    dep = db.query(RoadmapDependency).join(
        LifecycleRoadmapItem, RoadmapDependency.roadmap_item_id == LifecycleRoadmapItem.id
    ).filter(
        RoadmapDependency.id == dep_id,
        LifecycleRoadmapItem.organization_id == org_id
    ).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found or unauthorized.")
    db.delete(dep)
    db.commit()
    return None

# ----------------- EXPERIMENTS -----------------
@router.get("/experiments", response_model=List[ProductExperimentResponse])
def list_experiments(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List A/B experiments scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductExperiment).filter(ProductExperiment.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductExperiment.workspace_id == workspace_id)
    return query.order_by(desc(ProductExperiment.created_at)).all()

@router.post("/experiments", response_model=ProductExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    exp_in: ProductExperimentCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Configure a new experiment with validated variant allocations summing to 100%."""
    org_id = resolve_tenant_org_id(db, current_user, exp_in.organization_id or organization_id or x_organization_id)
    data = exp_in.model_dump()
    data.pop("organization_id", None)
    variants_data = data.pop("variants", [])

    if variants_data:
        total_alloc = sum(v.get("allocation_pct", 0.0) for v in variants_data)
        if abs(total_alloc - 100.0) > 0.5:
            raise HTTPException(
                status_code=400,
                detail=f"Variant allocation percentages must sum to 100%. Current total: {total_alloc}%."
            )

    exp = ProductExperiment(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(exp)
    db.flush()

    for v in variants_data:
        variant = ExperimentVariant(
            experiment_id=exp.id,
            variant_name=v["variant_name"],
            variant_key=v["variant_key"],
            allocation_pct=v.get("allocation_pct", 50.0),
            config_json=v.get("config_json", "{}"),
        )
        db.add(variant)

    db.commit()
    db.refresh(exp)
    return exp

@router.get("/experiments/{exp_id}", response_model=ProductExperimentResponse)
def get_experiment(
    exp_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve experiment by ID with tenant scoping."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    exp = db.query(ProductExperiment).filter(
        ProductExperiment.id == exp_id,
        ProductExperiment.organization_id == org_id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found or unauthorized.")
    return exp

@router.patch("/experiments/{exp_id}", response_model=ProductExperimentResponse)
def update_experiment(
    exp_id: str,
    exp_update: ProductExperimentUpdate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update experiment lifecycle status with transition validation and variant readiness checks."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    exp = db.query(ProductExperiment).filter(
        ProductExperiment.id == exp_id,
        ProductExperiment.organization_id == org_id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found in organization.")

    update_dict = exp_update.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"]:
        if not ProductLifecycleService.validate_stage_transition("experiment", exp.status, update_dict["status"]):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid experiment stage transition from {exp.status} to {update_dict['status']}"
            )
        if update_dict["status"] == "RUNNING":
            variants = db.query(ExperimentVariant).filter(ExperimentVariant.experiment_id == exp.id).all()
            if len(variants) < 1:
                raise HTTPException(status_code=400, detail="Cannot activate experiment without configured treatment variants.")
            total_alloc = sum(v.allocation_pct for v in variants)
            if abs(total_alloc - 100.0) > 0.5:
                raise HTTPException(status_code=400, detail=f"Cannot activate experiment: Variant allocations sum to {total_alloc}%, expected 100%.")

    for k, v in update_dict.items():
        setattr(exp, k, v)
    exp.updated_at = utc_now()
    db.commit()
    db.refresh(exp)
    return exp

@router.post("/experiments/{exp_id}/assign", response_model=ExperimentVariantResponse)
def assign_user_to_experiment(
    exp_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministically assign user to an active experiment variant within tenant context."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    exp = db.query(ProductExperiment).filter(
        ProductExperiment.id == exp_id,
        ProductExperiment.organization_id == org_id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found in authorized organization context.")

    try:
        return ProductLifecycleService.assign_experiment_variant(db, exp_id, current_user.id, organization_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/experiments/{exp_id}/events", status_code=status.HTTP_200_OK)
def track_experiment_telemetry(
    exp_id: str,
    event_name: str = Query(..., description="Telemetry event e.g. conversion, task_completed"),
    metric_value: float = Query(1.0),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Track conversion event for the current user's assigned variant with tenant security."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    exp = db.query(ProductExperiment).filter(
        ProductExperiment.id == exp_id,
        ProductExperiment.organization_id == org_id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found in authorized organization context.")

    try:
        ProductLifecycleService.track_experiment_event(
            db, exp_id, current_user.id, event_name, metric_value, organization_id=org_id
        )
        return {"status": "recorded", "experiment_id": exp_id, "event_name": event_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/experiments/{exp_id}/analysis", response_model=ExperimentStatisticalAnalysisResponse)
def get_experiment_statistical_analysis(
    exp_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate statistical significance, uplift, pooled z-test, and 95% confidence intervals."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    try:
        return ProductLifecycleService.analyze_experiment_statistics(db, exp_id, org_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

# ----------------- RELEASES -----------------
@router.get("/releases", response_model=List[ProductReleaseResponse])
def list_releases(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product feature releases scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductRelease).filter(ProductRelease.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductRelease.workspace_id == workspace_id)
    return query.order_by(desc(ProductRelease.created_at)).all()

@router.post("/releases", response_model=ProductReleaseResponse, status_code=status.HTTP_201_CREATED)
def create_release(
    rel_in: ProductReleaseCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Schedule and document a product feature release."""
    org_id = resolve_tenant_org_id(db, current_user, rel_in.organization_id or organization_id or x_organization_id)
    data = rel_in.model_dump()
    data.pop("organization_id", None)
    target_dt = data.pop("target_date", None)
    if target_dt and not data.get("release_date"):
        data["release_date"] = target_dt
    rel = ProductRelease(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel

@router.patch("/releases/{release_id}", response_model=ProductReleaseResponse)
def update_release(
    release_id: str,
    rel_update: ProductReleaseUpdate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update release details and status with stage transition validation."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    rel = db.query(ProductRelease).filter(
        ProductRelease.id == release_id,
        ProductRelease.organization_id == org_id
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Release not found or unauthorized.")

    update_dict = rel_update.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"]:
        if not ProductLifecycleService.validate_stage_transition("release", rel.status, update_dict["status"]):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid release stage transition from {rel.status} to {update_dict['status']}"
            )

    for k, v in update_dict.items():
        setattr(rel, k, v)
    rel.updated_at = utc_now()
    db.commit()
    db.refresh(rel)
    return rel

@router.delete("/releases/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_release(
    release_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a product release record."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    rel = db.query(ProductRelease).filter(
        ProductRelease.id == release_id,
        ProductRelease.organization_id == org_id
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Release not found or unauthorized.")
    db.delete(rel)
    db.commit()
    return None

@router.get("/releases/{release_id}/readiness", response_model=ReleaseReadinessResponse)
def get_release_readiness(
    release_id: str,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate quantifiable release readiness score (0-100%) and blocker evaluation."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    try:
        return ProductLifecycleService.calculate_release_readiness(db, release_id, org_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

# ----------------- DECISIONS & RISKS -----------------
@router.get("/decisions", response_model=List[ProductDecisionResponse])
def list_decisions(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product decisions scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductDecision).filter(ProductDecision.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductDecision.workspace_id == workspace_id)
    return query.order_by(desc(ProductDecision.decision_date)).all()

@router.post("/decisions", response_model=ProductDecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    dec_in: ProductDecisionCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a strategic product decision."""
    org_id = resolve_tenant_org_id(db, current_user, dec_in.organization_id or organization_id or x_organization_id)
    data = dec_in.model_dump()
    data.pop("organization_id", None)
    decision = ProductDecision(**data, decision_maker_id=current_user.id, organization_id=org_id)
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision

@router.get("/risks", response_model=List[ProductRiskResponse])
def list_risks(
    workspace_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product risks scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    query = db.query(ProductRiskRecord).filter(ProductRiskRecord.organization_id == org_id)
    if workspace_id is not None:
        query = query.filter(ProductRiskRecord.workspace_id == workspace_id)
    return query.order_by(desc(ProductRiskRecord.created_at)).all()

@router.post("/risks", response_model=ProductRiskResponse, status_code=status.HTTP_201_CREATED)
def create_risk(
    risk_in: ProductRiskCreate,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a product technical or delivery risk."""
    org_id = resolve_tenant_org_id(db, current_user, risk_in.organization_id or organization_id or x_organization_id)
    data = risk_in.model_dump()
    data.pop("organization_id", None)
    risk = ProductRiskRecord(**data, owner_id=current_user.id, organization_id=org_id)
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk

# ----------------- AI PRODUCT ASSISTANT -----------------
@router.post("/ai/query", response_model=AIProductAssistantResponse)
def ask_ai_product_assistant(
    request: AIProductAssistantRequest,
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query Grounded AI Product Assistant scoped to tenant organization."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    return ProductLifecycleService.answer_ai_product_query(
        db, request.query, request.context_type, organization_id=org_id
    )

# ----------------- EXPLICIT DEMO SEEDING -----------------
@router.post("/seed-demo", status_code=status.HTTP_200_OK)
def seed_demo_data(
    organization_id: Optional[int] = Query(None),
    x_organization_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicit endpoint to populate initial demo data for a workspace. Never runs automatically in production."""
    org_id = resolve_tenant_org_id(db, current_user, organization_id or x_organization_id)
    ProductLifecycleService.seed_initial_product_lifecycle_data(db, organization_id=org_id)
    return {"status": "seeded", "organization_id": org_id, "message": "Demo product lifecycle records successfully populated."}
