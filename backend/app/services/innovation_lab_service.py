import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.innovation_lab import (
    InnovationIdea,
    InnovationHypothesis,
    InnovationExperiment,
    InnovationExperimentResult,
    InnovationPrototype,
    InnovationValidation,
    InnovationPortfolio,
)
from app.models.support import ProductRoadmapItem
from app.schemas.innovation_lab import (
    InnovationIdeaCreate,
    InnovationIdeaUpdate,
    InnovationHypothesisCreate,
    InnovationHypothesisUpdate,
    InnovationExperimentCreate,
    InnovationExperimentUpdate,
    InnovationExperimentResultCreate,
    InnovationPrototypeCreate,
    InnovationPrototypeUpdate,
    InnovationValidationCreate,
    InnovationPortfolioCreate,
    PromoteIdeaToRoadmapResponse,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def seed_default_innovation_data(db: Session, owner_id: Optional[int] = None):
    """Seed initial innovation lab portfolio, ideas, hypotheses, experiments, prototypes, and validations if empty."""
    if db.query(InnovationPortfolio).first():
        return

    # 1. Portfolios
    core_port = InnovationPortfolio(
        id=f"iport_{uuid.uuid4().hex[:12]}",
        name="Enterprise Workflow Automation & AI",
        focus_area="AI Copilots & Autonomous Agents",
        budget_limit=100000.0,
        allocated_spend=32500.0,
        active_ideas_count=4,
    )
    growth_port = InnovationPortfolio(
        id=f"iport_{uuid.uuid4().hex[:12]}",
        name="Product-Led Growth & Realtime Collaboration",
        focus_area="Interactive Workspaces & Canvas",
        budget_limit=75000.0,
        allocated_spend=18000.0,
        active_ideas_count=3,
    )
    db.add_all([core_port, growth_port])
    db.flush()

    # 2. Innovation Ideas
    idea1 = InnovationIdea(
        id=f"idea_{uuid.uuid4().hex[:12]}",
        title="Autonomous Cross-Project Task Dependency Engine",
        problem_statement="Cross-functional project teams struggle with hidden blocking dependencies across separate workspaces, leading to delayed milestones.",
        proposed_solution="AI-powered dependency graph that detects implicit task blockers from comments, commit messages, and task descriptions automatically.",
        category="AI",
        stage="VALIDATED",
        target_audience="Enterprise Program Managers",
        estimated_effort="MEDIUM",
        strategic_value="TRANSFORMATIVE",
        owner_id=owner_id,
    )
    idea2 = InnovationIdea(
        id=f"idea_{uuid.uuid4().hex[:12]}",
        title="Real-Time Collaborative Brainstorming Canvas",
        problem_statement="Teams switch between Miro/Figma Jam and FocusBoard during ideation phases, losing actionable context when converting sticky notes to tasks.",
        proposed_solution="Integrated zero-latency infinite canvas directly inside FocusBoard that converts sticky notes into trackable tasks with one click.",
        category="PRODUCT",
        stage="PROTOTYPE",
        target_audience="Product Managers & Agile Teams",
        estimated_effort="HIGH",
        strategic_value="TRANSFORMATIVE",
        owner_id=owner_id,
    )
    idea3 = InnovationIdea(
        id=f"idea_{uuid.uuid4().hex[:12]}",
        title="Voice-to-Action Daily Standup Summarizer",
        problem_statement="Remote teams spend 20+ minutes on async status updates that go unread and fail to update task status in real time.",
        proposed_solution="60-second voice note intake that transcribes, parses action items, updates assignee statuses, and posts an executive summary.",
        category="UX",
        stage="EXPERIMENTATION",
        target_audience="Distributed Engineering Teams",
        estimated_effort="LOW",
        strategic_value="SUBSTANTIAL",
        owner_id=owner_id,
    )
    idea4 = InnovationIdea(
        id=f"idea_{uuid.uuid4().hex[:12]}",
        title="Zero-Knowledge Client-Side Vault for Sensitive Project Data",
        problem_statement="Highly regulated defense and healthcare clients cannot store unencrypted project data in cloud multi-tenant stores.",
        proposed_solution="E2E client-side encryption module using WebCrypto API allowing selective field encryption before persisting to PostgreSQL.",
        category="TECHNICAL",
        stage="RESEARCH",
        target_audience="Fintech & Healthcare Enterprises",
        estimated_effort="HIGH",
        strategic_value="SUBSTANTIAL",
        owner_id=owner_id,
    )
    db.add_all([idea1, idea2, idea3, idea4])
    db.flush()

    # 3. Hypotheses
    hypo1 = InnovationHypothesis(
        id=f"hypo_{uuid.uuid4().hex[:12]}",
        idea_id=idea1.id,
        statement="We believe enterprise program managers will resolve cross-project bottlenecks 40% faster if dependencies are automatically inferred.",
        measurable_criterion="40% decrease in task blocked duration in pilot cohort of 15 teams.",
        confidence_score=0.88,
        status="VALIDATED",
    )
    hypo2 = InnovationHypothesis(
        id=f"hypo_{uuid.uuid4().hex[:12]}",
        idea_id=idea2.id,
        statement="We believe in-app canvas will increase weekly user sessions by 25% and reduce external tool licensing costs.",
        measurable_criterion="Weekly active canvas sessions >= 3 per team and 20%+ increase in task creation speed.",
        confidence_score=0.82,
        status="TESTING",
    )
    hypo3 = InnovationHypothesis(
        id=f"hypo_{uuid.uuid4().hex[:12]}",
        idea_id=idea3.id,
        statement="We believe async audio standups will achieve 85% completion rate compared to 45% text check-ins.",
        measurable_criterion=">= 80% daily standup completion rate among pilot cohort.",
        confidence_score=0.75,
        status="TESTING",
    )
    db.add_all([hypo1, hypo2, hypo3])
    db.flush()

    # 4. Experiments
    exp1 = InnovationExperiment(
        id=f"exp_{uuid.uuid4().hex[:12]}",
        idea_id=idea1.id,
        hypothesis_id=hypo1.id,
        name="Dependency Prediction Accuracy Benchmark",
        experiment_type="TECHNICAL_POC",
        methodology="Trained fine-tuned embeddings on historical project issues and measured F1-score against manually verified dependencies.",
        sample_size=120,
        start_date=utc_now() - timedelta(days=21),
        end_date=utc_now() - timedelta(days=5),
        status="COMPLETED",
        budget_spent=4200.0,
    )
    exp2 = InnovationExperiment(
        id=f"exp_{uuid.uuid4().hex[:12]}",
        idea_id=idea2.id,
        hypothesis_id=hypo2.id,
        name="Prototype Usability Session with 20 Agile PMs",
        experiment_type="PROTOTYPE_TEST",
        methodology="Observed 20 product leaders conduct 45-minute sprint planning on interactive canvas mockup vs traditional sprint board.",
        sample_size=20,
        start_date=utc_now() - timedelta(days=10),
        end_date=utc_now() - timedelta(days=2),
        status="COMPLETED",
        budget_spent=3500.0,
    )
    exp3 = InnovationExperiment(
        id=f"exp_{uuid.uuid4().hex[:12]}",
        idea_id=idea3.id,
        hypothesis_id=hypo3.id,
        name="Async Voice Check-In Pilot",
        experiment_type="CUSTOMER_INTERVIEW",
        methodology="Running 14-day trial with 5 internal engineering squads evaluating daily transcription quality and participation.",
        sample_size=35,
        start_date=utc_now() - timedelta(days=7),
        end_date=None,
        status="RUNNING",
        budget_spent=1200.0,
    )
    db.add_all([exp1, exp2, exp3])
    db.flush()

    # 5. Results
    res1 = InnovationExperimentResult(
        id=f"exres_{uuid.uuid4().hex[:12]}",
        experiment_id=exp1.id,
        quantitative_summary="Achieved 91.4% precision and 88.2% recall in cross-project dependency inference across 1,400 test tasks.",
        qualitative_feedback="Lead Architects reported saving approximately 3.5 hours per week during bi-weekly synchronization meetings.",
        success_criteria_met=True,
        evidence_attachment_url="https://metrics.focusboard.internal/experiments/dep-eval-report.pdf",
        lessons_learned="Subtasks with short descriptions require parent context to avoid false-positive semantic links.",
    )
    res2 = InnovationExperimentResult(
        id=f"exres_{uuid.uuid4().hex[:12]}",
        experiment_id=exp2.id,
        quantitative_summary="18 out of 20 PMs rated the experience 9/10 or higher. Time to convert sticky ideas to backlog items dropped by 64%.",
        qualitative_feedback="Participants loved the live cursor sync and seamless right-click 'Convert to FocusBoard Task' interaction.",
        success_criteria_met=True,
        evidence_attachment_url="https://metrics.focusboard.internal/experiments/canvas-pm-interview-synthesis.pdf",
        lessons_learned="Need zoom-to-fit shortcut and mobile view-only mode for exec review.",
    )
    db.add_all([res1, res2])

    # 6. Prototypes
    proto1 = InnovationPrototype(
        id=f"proto_{uuid.uuid4().hex[:12]}",
        idea_id=idea1.id,
        name="Auto-Dependency Directed Acyclic Graph (DAG) Visualizer",
        prototype_type="TECHNICAL_POC",
        demo_url="https://staging.focusboard.internal/prototypes/dep-graph",
        repository_url="https://github.com/focusboard/dep-graph-poc",
        tech_stack="React Flow + FastAPI + NetworkX",
        status="APPROVED",
    )
    proto2 = InnovationPrototype(
        id=f"proto_{uuid.uuid4().hex[:12]}",
        idea_id=idea2.id,
        name="Infinite Canvas Alpha v0.3",
        prototype_type="INTERACTIVE_MOCKUP",
        demo_url="https://staging.focusboard.internal/prototypes/infinite-canvas",
        repository_url="https://github.com/focusboard/canvas-alpha",
        tech_stack="HTML5 Canvas + WebSockets + Yjs CRDT",
        status="BUILDING",
    )
    db.add_all([proto1, proto2])

    # 7. Validations
    val1 = InnovationValidation(
        id=f"ival_{uuid.uuid4().hex[:12]}",
        idea_id=idea1.id,
        dimension="PROBLEM",
        criteria="Severe recurring blocker in customer retention calls (>15 enterprise churn mentions).",
        status="PASSED",
        reviewer_id=owner_id,
        confidence=0.95,
        notes="Validated across 12 enterprise customer success quarterly reviews.",
    )
    val2 = InnovationValidation(
        id=f"ival_{uuid.uuid4().hex[:12]}",
        idea_id=idea1.id,
        dimension="TECHNICAL",
        criteria="Graph traversal latency under 80ms for 500 nodes.",
        status="PASSED",
        reviewer_id=owner_id,
        confidence=0.92,
        notes="Benchmarked in SQLite and PostgreSQL with sub-second recalculation.",
    )
    val3 = InnovationValidation(
        id=f"ival_{uuid.uuid4().hex[:12]}",
        idea_id=idea2.id,
        dimension="CUSTOMER",
        criteria="Validated with minimum 15 customer design partners willing to pilot.",
        status="IN_PROGRESS",
        reviewer_id=owner_id,
        confidence=0.85,
        notes="11 enterprise teams currently in pre-release sign-up queue.",
    )
    db.add_all([val1, val2, val3])
    db.commit()


# --- Innovation Overview Service ---
def get_innovation_overview(db: Session) -> Dict[str, Any]:
    seed_default_innovation_data(db)

    ideas = db.query(InnovationIdea).order_by(desc(InnovationIdea.updated_at)).all()
    experiments = db.query(InnovationExperiment).order_by(desc(InnovationExperiment.created_at)).all()
    prototypes = db.query(InnovationPrototype).order_by(desc(InnovationPrototype.created_at)).all()

    total_ideas = len(ideas)
    active_experiments = [e for e in experiments if e.status == "RUNNING"]
    completed_experiments = [e for e in experiments if e.status == "COMPLETED"]
    validated_ideas = [i for i in ideas if i.stage in ["VALIDATED", "ROADMAP"]]
    prototypes_building = [p for p in prototypes if p.status in ["BUILDING", "PLANNING", "TESTING"]]

    # Calculate success rate from results
    results = db.query(InnovationExperimentResult).all()
    success_rate = 0.0
    if results:
        met = sum(1 for r in results if r.success_criteria_met)
        success_rate = round((met / len(results)) * 100.0, 1)

    # Pipeline stage distribution
    stage_dist: Dict[str, int] = {}
    for i in ideas:
        stage_dist[i.stage] = stage_dist.get(i.stage, 0) + 1

    # Category distribution
    cat_dist: Dict[str, int] = {}
    for i in ideas:
        cat_dist[i.category] = cat_dist.get(i.category, 0) + 1

    # Formatted recent ideas
    recent_ideas_data = []
    for idea in ideas[:6]:
        hypo_count = len(idea.hypotheses)
        exp_count = len(idea.experiments)
        recent_ideas_data.append({
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
            "hypotheses_count": hypo_count,
            "experiments_count": exp_count,
        })

    recent_exps_data = []
    for exp in active_experiments[:5]:
        recent_exps_data.append({
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
        })

    recent_protos_data = []
    for p in prototypes[:5]:
        recent_protos_data.append({
            "id": p.id,
            "idea_id": p.idea_id,
            "name": p.name,
            "prototype_type": p.prototype_type,
            "demo_url": p.demo_url,
            "repository_url": p.repository_url,
            "tech_stack": p.tech_stack,
            "status": p.status,
            "created_at": p.created_at,
        })

    return {
        "total_ideas_count": total_ideas,
        "active_experiments_count": len(active_experiments),
        "completed_experiments_count": len(completed_experiments),
        "validated_ideas_count": len(validated_ideas),
        "prototypes_building_count": len(prototypes_building),
        "experiment_success_rate": success_rate,
        "pipeline_stage_distribution": stage_dist,
        "category_distribution": cat_dist,
        "recent_ideas": recent_ideas_data,
        "active_experiments": recent_exps_data,
        "recent_prototypes": recent_protos_data,
    }


# --- Ideas CRUD ---
def get_ideas(db: Session, stage: Optional[str] = None, category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    query = db.query(InnovationIdea)
    if stage:
        query = query.filter(InnovationIdea.stage == stage)
    if category:
        query = query.filter(InnovationIdea.category == category)
    
    ideas = query.order_by(desc(InnovationIdea.updated_at)).offset(offset).limit(limit).all()
    results = []
    for idea in ideas:
        results.append({
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
        })
    return results

def get_idea_by_id(db: Session, idea_id: str) -> Optional[InnovationIdea]:
    return db.query(InnovationIdea).filter(InnovationIdea.id == idea_id).first()

def create_idea(db: Session, data: InnovationIdeaCreate, owner_id: Optional[int] = None) -> InnovationIdea:
    idea = InnovationIdea(
        id=f"idea_{uuid.uuid4().hex[:12]}",
        title=data.title,
        problem_statement=data.problem_statement,
        proposed_solution=data.proposed_solution,
        category=data.category,
        stage=data.stage,
        target_audience=data.target_audience,
        estimated_effort=data.estimated_effort,
        strategic_value=data.strategic_value,
        owner_id=owner_id,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea

def update_idea(db: Session, idea_id: str, data: InnovationIdeaUpdate) -> Optional[InnovationIdea]:
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return None
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(idea, field, val)
    idea.updated_at = utc_now()
    db.commit()
    db.refresh(idea)
    return idea

def delete_idea(db: Session, idea_id: str) -> bool:
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return False
    db.delete(idea)
    db.commit()
    return True


# --- Hypotheses CRUD ---
def create_hypothesis(db: Session, data: InnovationHypothesisCreate) -> InnovationHypothesis:
    hypo = InnovationHypothesis(
        id=f"hypo_{uuid.uuid4().hex[:12]}",
        idea_id=data.idea_id,
        statement=data.statement,
        measurable_criterion=data.measurable_criterion,
        confidence_score=data.confidence_score,
        status=data.status,
    )
    db.add(hypo)
    db.commit()
    db.refresh(hypo)
    return hypo

def get_hypotheses(db: Session, idea_id: Optional[str] = None) -> List[InnovationHypothesis]:
    query = db.query(InnovationHypothesis)
    if idea_id:
        query = query.filter(InnovationHypothesis.idea_id == idea_id)
    return query.order_by(desc(InnovationHypothesis.created_at)).all()

def update_hypothesis(db: Session, hypo_id: str, data: InnovationHypothesisUpdate) -> Optional[InnovationHypothesis]:
    hypo = db.query(InnovationHypothesis).filter(InnovationHypothesis.id == hypo_id).first()
    if not hypo:
        return None
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(hypo, field, val)
    db.commit()
    db.refresh(hypo)
    return hypo


# --- Experiments CRUD ---
def create_experiment(db: Session, data: InnovationExperimentCreate) -> InnovationExperiment:
    exp = InnovationExperiment(
        id=f"exp_{uuid.uuid4().hex[:12]}",
        idea_id=data.idea_id,
        hypothesis_id=data.hypothesis_id,
        name=data.name,
        experiment_type=data.experiment_type,
        methodology=data.methodology,
        sample_size=data.sample_size,
        start_date=data.start_date or utc_now(),
        end_date=data.end_date,
        status=data.status,
        budget_spent=data.budget_spent,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp

def get_experiments(db: Session, idea_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    query = db.query(InnovationExperiment)
    if idea_id:
        query = query.filter(InnovationExperiment.idea_id == idea_id)
    if status:
        query = query.filter(InnovationExperiment.status == status)
    exps = query.order_by(desc(InnovationExperiment.created_at)).all()
    results = []
    for exp in exps:
        results.append({
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
        })
    return results

def get_experiment_by_id(db: Session, exp_id: str) -> Optional[InnovationExperiment]:
    return db.query(InnovationExperiment).filter(InnovationExperiment.id == exp_id).first()

def update_experiment(db: Session, exp_id: str, data: InnovationExperimentUpdate) -> Optional[InnovationExperiment]:
    exp = get_experiment_by_id(db, exp_id)
    if not exp:
        return None
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(exp, field, val)
    db.commit()
    db.refresh(exp)
    return exp


# --- Results CRUD ---
def attach_experiment_result(db: Session, data: InnovationExperimentResultCreate) -> InnovationExperimentResult:
    result = InnovationExperimentResult(
        id=f"exres_{uuid.uuid4().hex[:12]}",
        experiment_id=data.experiment_id,
        quantitative_summary=data.quantitative_summary,
        qualitative_feedback=data.qualitative_feedback,
        success_criteria_met=data.success_criteria_met,
        evidence_attachment_url=data.evidence_attachment_url,
        lessons_learned=data.lessons_learned,
    )
    db.add(result)
    # Automatically mark experiment COMPLETED if not already
    exp = get_experiment_by_id(db, data.experiment_id)
    if exp and exp.status == "RUNNING":
        exp.status = "COMPLETED"
        exp.end_date = utc_now()
    db.commit()
    db.refresh(result)
    return result

def get_experiment_results(db: Session, experiment_id: str) -> List[InnovationExperimentResult]:
    return db.query(InnovationExperimentResult).filter(InnovationExperimentResult.experiment_id == experiment_id).all()


# --- Prototypes CRUD ---
def create_prototype(db: Session, data: InnovationPrototypeCreate) -> InnovationPrototype:
    proto = InnovationPrototype(
        id=f"proto_{uuid.uuid4().hex[:12]}",
        idea_id=data.idea_id,
        name=data.name,
        prototype_type=data.prototype_type,
        demo_url=data.demo_url,
        repository_url=data.repository_url,
        tech_stack=data.tech_stack,
        status=data.status,
    )
    db.add(proto)
    db.commit()
    db.refresh(proto)
    return proto

def get_prototypes(db: Session, idea_id: Optional[str] = None) -> List[InnovationPrototype]:
    query = db.query(InnovationPrototype)
    if idea_id:
        query = query.filter(InnovationPrototype.idea_id == idea_id)
    return query.order_by(desc(InnovationPrototype.created_at)).all()

def update_prototype(db: Session, proto_id: str, data: InnovationPrototypeUpdate) -> Optional[InnovationPrototype]:
    proto = db.query(InnovationPrototype).filter(InnovationPrototype.id == proto_id).first()
    if not proto:
        return None
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(proto, field, val)
    db.commit()
    db.refresh(proto)
    return proto


# --- Validations CRUD ---
def create_validation(db: Session, data: InnovationValidationCreate, reviewer_id: Optional[int] = None) -> InnovationValidation:
    val = InnovationValidation(
        id=f"ival_{uuid.uuid4().hex[:12]}",
        idea_id=data.idea_id,
        dimension=data.dimension,
        criteria=data.criteria,
        status=data.status,
        reviewer_id=reviewer_id,
        confidence=data.confidence,
        notes=data.notes,
    )
    db.add(val)
    db.commit()
    db.refresh(val)
    return val

def get_validations(db: Session, idea_id: Optional[str] = None) -> List[InnovationValidation]:
    query = db.query(InnovationValidation)
    if idea_id:
        query = query.filter(InnovationValidation.idea_id == idea_id)
    return query.order_by(desc(InnovationValidation.created_at)).all()


# --- Portfolios CRUD ---
def get_portfolios(db: Session) -> List[InnovationPortfolio]:
    seed_default_innovation_data(db)
    return db.query(InnovationPortfolio).order_by(desc(InnovationPortfolio.created_at)).all()

def create_portfolio(db: Session, data: InnovationPortfolioCreate) -> InnovationPortfolio:
    port = InnovationPortfolio(
        id=f"iport_{uuid.uuid4().hex[:12]}",
        name=data.name,
        focus_area=data.focus_area,
        budget_limit=data.budget_limit,
    )
    db.add(port)
    db.commit()
    db.refresh(port)
    return port


# --- Promote Idea to Product Roadmap ---
def promote_idea_to_roadmap(
    db: Session,
    idea_id: str,
    roadmap_category: str = "Innovation",
    target_status: str = "PLANNED",
) -> Optional[PromoteIdeaToRoadmapResponse]:
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return None

    # Create ProductRoadmapItem
    roadmap_item = ProductRoadmapItem(
        title=idea.title,
        description=f"{idea.problem_statement}\n\nProposed Solution: {idea.proposed_solution}",
        category=roadmap_category,
        status=target_status,
        vote_count=1,
    )
    db.add(roadmap_item)
    db.flush()

    # Link back to idea and update stage
    idea.roadmap_item_id = roadmap_item.id
    idea.stage = "ROADMAP"
    idea.updated_at = utc_now()
    db.commit()

    return PromoteIdeaToRoadmapResponse(
        idea_id=idea.id,
        roadmap_item_id=roadmap_item.id,
        title=idea.title,
        promoted_at=utc_now(),
    )
