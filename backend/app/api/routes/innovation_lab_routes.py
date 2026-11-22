from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.innovation_lab import (
    InnovationIdeaCreate,
    InnovationIdeaUpdate,
    InnovationIdeaResponse,
    InnovationHypothesisCreate,
    InnovationHypothesisUpdate,
    InnovationHypothesisResponse,
    InnovationExperimentCreate,
    InnovationExperimentUpdate,
    InnovationExperimentResponse,
    InnovationExperimentResultBase,
    InnovationExperimentResultCreate,
    InnovationExperimentResultResponse,
    InnovationPrototypeCreate,
    InnovationPrototypeUpdate,
    InnovationPrototypeResponse,
    InnovationValidationCreate,
    InnovationValidationResponse,
    InnovationPortfolioCreate,
    InnovationPortfolioResponse,
    PromoteIdeaToRoadmapRequest,
    PromoteIdeaToRoadmapResponse,
    InnovationDashboardOverviewResponse,
)
from app.services import innovation_lab_service

router = APIRouter(prefix="/innovation", tags=["FocusBoard Innovation Lab & R&D"])

@router.get("/overview", response_model=InnovationDashboardOverviewResponse)
def get_innovation_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Innovation Lab dashboard overview: ideas in pipeline, active experiments, prototypes, and success metrics."""
    return innovation_lab_service.get_innovation_overview(db)

# --- Ideas ---
@router.get("/ideas", response_model=List[InnovationIdeaResponse])
def list_ideas(
    stage: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.get_ideas(db, stage=stage, category=category, limit=limit, offset=offset)

@router.get("/ideas/{idea_id}", response_model=InnovationIdeaResponse)
def get_idea(
    idea_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    idea = innovation_lab_service.get_idea_by_id(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Innovation idea not found")
    return {
        "id": idea.id,
        "title": idea.title,
        "problem_statement": idea.problem_statement,
        "proposed_solution": idea.proposed_solution,
        "category": idea.category,
        "stage": idea.stage,
        "target_audience": idea.target_audience,
        "estimated_effort": idea.estimated_effort,
        "strategic_value": idea.strategic_value,
        "owner_id": idea.owner_id,
        "roadmap_item_id": idea.roadmap_item_id,
        "created_at": idea.created_at,
        "updated_at": idea.updated_at,
        "hypotheses_count": len(idea.hypotheses),
        "experiments_count": len(idea.experiments),
    }

@router.post("/ideas", response_model=InnovationIdeaResponse, status_code=status.HTTP_201_CREATED)
def create_idea(
    data: InnovationIdeaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    idea = innovation_lab_service.create_idea(db, data, owner_id=current_user.id)
    return {
        "id": idea.id,
        "title": idea.title,
        "problem_statement": idea.problem_statement,
        "proposed_solution": idea.proposed_solution,
        "category": idea.category,
        "stage": idea.stage,
        "target_audience": idea.target_audience,
        "estimated_effort": idea.estimated_effort,
        "strategic_value": idea.strategic_value,
        "owner_id": idea.owner_id,
        "roadmap_item_id": idea.roadmap_item_id,
        "created_at": idea.created_at,
        "updated_at": idea.updated_at,
        "hypotheses_count": 0,
        "experiments_count": 0,
    }

@router.patch("/ideas/{idea_id}", response_model=InnovationIdeaResponse)
def update_idea(
    idea_id: str,
    data: InnovationIdeaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    idea = innovation_lab_service.update_idea(db, idea_id, data)
    if not idea:
        raise HTTPException(status_code=404, detail="Innovation idea not found")
    return {
        "id": idea.id,
        "title": idea.title,
        "problem_statement": idea.problem_statement,
        "proposed_solution": idea.proposed_solution,
        "category": idea.category,
        "stage": idea.stage,
        "target_audience": idea.target_audience,
        "estimated_effort": idea.estimated_effort,
        "strategic_value": idea.strategic_value,
        "owner_id": idea.owner_id,
        "roadmap_item_id": idea.roadmap_item_id,
        "created_at": idea.created_at,
        "updated_at": idea.updated_at,
        "hypotheses_count": len(idea.hypotheses),
        "experiments_count": len(idea.experiments),
    }

@router.delete("/ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idea(
    idea_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = innovation_lab_service.delete_idea(db, idea_id)
    if not success:
        raise HTTPException(status_code=404, detail="Innovation idea not found")
    return None

# --- Promote Idea to Product Roadmap ---
@router.post("/ideas/{idea_id}/promote-to-roadmap", response_model=PromoteIdeaToRoadmapResponse)
def promote_idea_to_roadmap(
    idea_id: str,
    payload: PromoteIdeaToRoadmapRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Promote a validated idea directly into a production ProductRoadmapItem."""
    res = innovation_lab_service.promote_idea_to_roadmap(
        db,
        idea_id=idea_id,
        roadmap_category=payload.roadmap_category,
        target_status=payload.target_status,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Innovation idea not found")
    return res

# --- Hypotheses ---
@router.get("/hypotheses", response_model=List[InnovationHypothesisResponse])
def list_hypotheses(
    idea_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.get_hypotheses(db, idea_id=idea_id)

@router.post("/hypotheses", response_model=InnovationHypothesisResponse, status_code=status.HTTP_201_CREATED)
def create_hypothesis(
    data: InnovationHypothesisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.create_hypothesis(db, data)

@router.patch("/hypotheses/{hypo_id}", response_model=InnovationHypothesisResponse)
def update_hypothesis(
    hypo_id: str,
    data: InnovationHypothesisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hypo = innovation_lab_service.update_hypothesis(db, hypo_id, data)
    if not hypo:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypo

# --- Experiments ---
@router.get("/experiments", response_model=List[InnovationExperimentResponse])
def list_experiments(
    idea_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.get_experiments(db, idea_id=idea_id, status=status)

@router.post("/experiments", response_model=InnovationExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    data: InnovationExperimentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = innovation_lab_service.create_experiment(db, data)
    return {
        "id": exp.id,
        "idea_id": exp.idea_id,
        "hypothesis_id": exp.hypothesis_id,
        "name": exp.name,
        "experiment_type": exp.experiment_type,
        "methodology": exp.methodology,
        "sample_size": exp.sample_size,
        "start_date": exp.start_date,
        "end_date": exp.end_date,
        "status": exp.status,
        "budget_spent": exp.budget_spent,
        "created_at": exp.created_at,
        "has_results": False,
    }

@router.patch("/experiments/{exp_id}", response_model=InnovationExperimentResponse)
def update_experiment(
    exp_id: str,
    data: InnovationExperimentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exp = innovation_lab_service.update_experiment(db, exp_id, data)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "id": exp.id,
        "idea_id": exp.idea_id,
        "hypothesis_id": exp.hypothesis_id,
        "name": exp.name,
        "experiment_type": exp.experiment_type,
        "methodology": exp.methodology,
        "sample_size": exp.sample_size,
        "start_date": exp.start_date,
        "end_date": exp.end_date,
        "status": exp.status,
        "budget_spent": exp.budget_spent,
        "created_at": exp.created_at,
        "has_results": len(exp.results) > 0,
    }

# --- Results ---
@router.get("/experiments/{exp_id}/results", response_model=List[InnovationExperimentResultResponse])
def get_experiment_results(
    exp_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.get_experiment_results(db, experiment_id=exp_id)

@router.post("/experiments/{exp_id}/results", response_model=InnovationExperimentResultResponse, status_code=status.HTTP_201_CREATED)
def attach_experiment_result(
    exp_id: str,
    data: InnovationExperimentResultBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    create_dto = InnovationExperimentResultCreate(
        experiment_id=exp_id,
        quantitative_summary=data.quantitative_summary,
        qualitative_feedback=data.qualitative_feedback,
        success_criteria_met=data.success_criteria_met,
        evidence_attachment_url=data.evidence_attachment_url,
        lessons_learned=data.lessons_learned,
    )
    return innovation_lab_service.attach_experiment_result(db, create_dto)

# --- Prototypes ---
@router.get("/prototypes", response_model=List[InnovationPrototypeResponse])
def list_prototypes(
    idea_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.get_prototypes(db, idea_id=idea_id)

@router.post("/prototypes", response_model=InnovationPrototypeResponse, status_code=status.HTTP_201_CREATED)
def create_prototype(
    data: InnovationPrototypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.create_prototype(db, data)

@router.patch("/prototypes/{proto_id}", response_model=InnovationPrototypeResponse)
def update_prototype(
    proto_id: str,
    data: InnovationPrototypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proto = innovation_lab_service.update_prototype(db, proto_id, data)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    return proto

# --- Validations ---
@router.get("/validations", response_model=List[InnovationValidationResponse])
def list_validations(
    idea_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.get_validations(db, idea_id=idea_id)

@router.post("/validations", response_model=InnovationValidationResponse, status_code=status.HTTP_201_CREATED)
def create_validation(
    data: InnovationValidationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.create_validation(db, data, reviewer_id=current_user.id)

# --- Portfolios ---
@router.get("/portfolios", response_model=List[InnovationPortfolioResponse])
def list_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.get_portfolios(db)

@router.post("/portfolios", response_model=InnovationPortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    data: InnovationPortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return innovation_lab_service.create_portfolio(db, data)
