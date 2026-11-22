from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
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
)
from app.schemas.product_lifecycle import (
    ProductDiscoveryCreate,
    ProductDiscoveryUpdate,
    ProductDiscoveryResponse,
    ProductIdeaCreate,
    ProductIdeaUpdate,
    ProductIdeaResponse,
    ProductFeatureRequestCreate,
    ProductFeatureRequestUpdate,
    ProductFeatureRequestResponse,
    ProductOpportunityCreate,
    ProductOpportunityResponse,
    ProductPrioritizationItemCreate,
    ProductPrioritizationItemResponse,
    ProductInitiativeCreate,
    ProductInitiativeResponse,
    LifecycleRoadmapItemCreate,
    LifecycleRoadmapItemResponse,
    RoadmapDependencyCreate,
    RoadmapDependencyResponse,
    ProductExperimentCreate,
    ProductExperimentResponse,
    ExperimentVariantResponse,
    ProductReleaseCreate,
    ProductReleaseResponse,
    AIProductAssistantRequest,
    AIProductAssistantResponse,
)
from app.services.product_lifecycle_service import ProductLifecycleService

router = APIRouter()

@router.get("/overview", response_model=Dict[str, Any])
def get_lifecycle_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve aggregate product lifecycle pipeline metrics, customer demand, and experiment counts."""
    return ProductLifecycleService.get_lifecycle_overview(db)

# Discoveries
@router.get("/discoveries", response_model=List[ProductDiscoveryResponse])
def list_discoveries(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product discoveries and customer problem investigations."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    query = db.query(ProductDiscovery)
    if status_filter:
        query = query.filter(ProductDiscovery.status == status_filter)
    return query.order_by(desc(ProductDiscovery.created_at)).all()

@router.post("/discoveries", response_model=ProductDiscoveryResponse, status_code=status.HTTP_201_CREATED)
def create_discovery(
    disc_in: ProductDiscoveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a new customer problem discovery and opportunity hypothesis."""
    disc = ProductDiscovery(**disc_in.model_dump(), owner_id=current_user.id)
    db.add(disc)
    db.commit()
    db.refresh(disc)
    return disc

# Ideas
@router.get("/ideas", response_model=List[ProductIdeaResponse])
def list_ideas(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product solution ideas."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    query = db.query(ProductIdea)
    if status_filter:
        query = query.filter(ProductIdea.status == status_filter)
    return query.order_by(desc(ProductIdea.created_at)).all()

@router.post("/ideas", response_model=ProductIdeaResponse, status_code=status.HTTP_201_CREATED)
def create_idea(
    idea_in: ProductIdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a product concept or solution idea."""
    idea = ProductIdea(**idea_in.model_dump(), owner_id=current_user.id)
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea

# Feature Requests
@router.get("/feature-requests", response_model=List[ProductFeatureRequestResponse])
def list_feature_requests(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List customer feature requests with demand count and revenue impact."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    query = db.query(ProductFeatureRequest)
    if status_filter:
        query = query.filter(ProductFeatureRequest.status == status_filter)
    if priority:
        query = query.filter(ProductFeatureRequest.priority == priority)
    return query.order_by(desc(ProductFeatureRequest.request_count)).all()

@router.post("/feature-requests", response_model=ProductFeatureRequestResponse, status_code=status.HTTP_201_CREATED)
def create_feature_request(
    req_in: ProductFeatureRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a customer-demanded feature request."""
    freq = ProductFeatureRequest(**req_in.model_dump(), owner_id=current_user.id)
    db.add(freq)
    db.commit()
    db.refresh(freq)
    return freq

@router.post("/feature-requests/{request_id}/merge", response_model=ProductFeatureRequestResponse)
def merge_feature_requests(
    request_id: str,
    target_id: str = Query(..., description="ID of primary feature request to merge into"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Merge duplicate feature request into a primary record, aggregating demand count."""
    source_req = db.query(ProductFeatureRequest).filter(ProductFeatureRequest.id == request_id).first()
    target_req = db.query(ProductFeatureRequest).filter(ProductFeatureRequest.id == target_id).first()
    if not source_req or not target_req:
        raise HTTPException(status_code=404, detail="Source or target feature request not found")

    target_req.request_count += source_req.request_count
    target_req.revenue_impact += source_req.revenue_impact
    source_req.merged_into_id = target_req.id
    source_req.status = "DECLINED"

    db.commit()
    db.refresh(target_req)
    return target_req

# Opportunities
@router.get("/opportunities", response_model=List[ProductOpportunityResponse])
def list_opportunities(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List evaluated market and product opportunities."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    return db.query(ProductOpportunity).order_by(desc(ProductOpportunity.created_at)).all()

@router.post("/opportunities", response_model=ProductOpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opp_in: ProductOpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a qualified product business opportunity."""
    opp = ProductOpportunity(**opp_in.model_dump(), owner_id=current_user.id)
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

# Prioritization
@router.post("/prioritization/calculate", response_model=Dict[str, float])
def calculate_prioritization(
    reach: float = Query(..., ge=1.0),
    impact: float = Query(..., ge=0.5, le=5.0),
    confidence: float = Query(..., ge=0.1, le=1.0),
    effort: float = Query(..., ge=0.5),
    ease: float = Query(3.0, ge=1.0, le=5.0),
    current_user: User = Depends(get_current_user),
):
    """Calculate RICE, ICE, and weighted priority scores."""
    return ProductLifecycleService.calculate_prioritization(reach, impact, confidence, effort, ease)

@router.get("/prioritization/items", response_model=List[ProductPrioritizationItemResponse])
def list_prioritization_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List ranked prioritization items."""
    return db.query(ProductPrioritizationItem).order_by(desc(ProductPrioritizationItem.rice_score)).all()

@router.post("/prioritization/items", response_model=ProductPrioritizationItemResponse, status_code=status.HTTP_201_CREATED)
def score_prioritization_item(
    item_in: ProductPrioritizationItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Persist a scored prioritization entry with RICE/ICE evaluation."""
    scores = ProductLifecycleService.calculate_prioritization(
        item_in.reach, item_in.impact, item_in.confidence, item_in.effort, item_in.ease
    )
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
        evaluated_at=ProductLifecycleService.seed_initial_product_lifecycle_data(db) or ProductLifecycleService.calculate_prioritization(1,1,1,1) and None or None,
    )
    from datetime import datetime, timezone
    pitem.evaluated_at = datetime.now(timezone.utc)
    db.add(pitem)
    db.commit()
    db.refresh(pitem)
    return pitem

# Initiatives & Roadmaps
@router.get("/initiatives", response_model=List[ProductInitiativeResponse])
def list_initiatives(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List strategic product initiatives."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    return db.query(ProductInitiative).order_by(desc(ProductInitiative.created_at)).all()

@router.post("/initiatives", response_model=ProductInitiativeResponse, status_code=status.HTTP_201_CREATED)
def create_initiative(
    init_in: ProductInitiativeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a high-level strategic product initiative."""
    init = ProductInitiative(**init_in.model_dump(), owner_id=current_user.id)
    db.add(init)
    db.commit()
    db.refresh(init)
    return init

@router.get("/roadmap", response_model=List[LifecycleRoadmapItemResponse])
def list_roadmap_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all scheduled roadmap timeline deliverables."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    return db.query(LifecycleRoadmapItem).order_by(LifecycleRoadmapItem.quarter, LifecycleRoadmapItem.target_date).all()

@router.post("/roadmap", response_model=LifecycleRoadmapItemResponse, status_code=status.HTTP_201_CREATED)
def create_roadmap_item(
    item_in: LifecycleRoadmapItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an item to the product roadmap schedule."""
    item = LifecycleRoadmapItem(**item_in.model_dump(), owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# Experiments & A/B Testing
@router.get("/experiments", response_model=List[ProductExperimentResponse])
def list_experiments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all A/B testing and growth experiments."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    return db.query(ProductExperiment).order_by(desc(ProductExperiment.created_at)).all()

@router.post("/experiments", response_model=ProductExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    exp_in: ProductExperimentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Configure a new A/B test experiment with treatment variants."""
    data = exp_in.model_dump()
    variants_data = data.pop("variants", [])
    exp = ProductExperiment(**data, owner_id=current_user.id)
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

@router.post("/experiments/{exp_id}/assign", response_model=ExperimentVariantResponse)
def assign_user_to_experiment(
    exp_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministically assign user to an experiment variant."""
    try:
        return ProductLifecycleService.assign_experiment_variant(db, exp_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/experiments/{exp_id}/events", status_code=status.HTTP_200_OK)
def track_experiment_telemetry(
    exp_id: str,
    event_name: str = Query(..., description="Telemetry event e.g. conversion, task_completed"),
    metric_value: float = Query(1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Track conversion event for the current user's assigned variant."""
    ProductLifecycleService.track_experiment_event(db, exp_id, current_user.id, event_name, metric_value)
    return {"status": "recorded", "experiment_id": exp_id, "event_name": event_name}

# Releases
@router.get("/releases", response_model=List[ProductReleaseResponse])
def list_releases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List product feature releases and rollout stages."""
    ProductLifecycleService.seed_initial_product_lifecycle_data(db)
    return db.query(ProductRelease).order_by(desc(ProductRelease.created_at)).all()

@router.post("/releases", response_model=ProductReleaseResponse, status_code=status.HTTP_201_CREATED)
def create_release(
    rel_in: ProductReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Schedule and document a product feature release."""
    rel = ProductRelease(**rel_in.model_dump(), owner_id=current_user.id)
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel

# AI Product Assistant
@router.post("/ai/query", response_model=AIProductAssistantResponse)
def ask_ai_product_assistant(
    request: AIProductAssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query Grounded AI Product Assistant for discovery, demand, and roadmap recommendations."""
    return ProductLifecycleService.answer_ai_product_query(db, request.query, request.context_type)
