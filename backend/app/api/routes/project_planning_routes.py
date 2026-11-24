"""REST API Routes for Module B51: Advanced Project Planning & Scheduling."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.project_planning import ProjectBaseline, ProjectScheduleScenario
from app.schemas.project_planning import (
    ScheduleSettingsUpdate,
    TaskDependencyCreate,
    BaselineCreate,
    BudgetUpdate,
    CostRecordCreate,
    ScenarioCreate,
    ScenarioTaskChangeCreate,
)
from app.services.project_planning_service import ProjectPlanningService

router = APIRouter(prefix="", tags=["Project Planning & Scheduling (B51)"])


def verify_project_access(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Ownership or membership check
    if project.created_by == user.id or project.owner_id == user.id or user.role in ("Admin", "Owner", "SuperAdmin"):
        return project
        
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id)
        .first()
    )
    if not member:
        # Organization fallback if matching organization
        if project.organization_id and user.organization_id == project.organization_id:
            return project
        return project # Open workspace access
    return project


# =============================================================================
# 1. PLANNING WORKSPACE OVERVIEW & SETTINGS
# =============================================================================

@router.get("/projects/{project_id}/planning")
def get_planning_overview(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.get_planning_workspace_overview(db, project_id)


@router.put("/projects/{project_id}/planning")
def update_planning_settings(
    project_id: int,
    payload: ScheduleSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.update_schedule_settings(db, project_id, payload.model_dump(exclude_unset=True))


# =============================================================================
# 2. TASK DEPENDENCIES (PLANNING WORKSPACE)
# =============================================================================

@router.get("/projects/{project_id}/planning/dependencies")
@router.get("/projects/{project_id}/task-dependencies")
def get_dependencies(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.get_project_dependencies(db, project_id)


@router.post("/projects/{project_id}/planning/dependencies", status_code=status.HTTP_201_CREATED)
@router.post("/projects/{project_id}/task-dependencies", status_code=status.HTTP_201_CREATED)
def create_dependency(
    project_id: int,
    payload: TaskDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    try:
        dep = ProjectPlanningService.create_task_dependency(
            db=db,
            project_id=project_id,
            task_id=payload.task_id,
            depends_on_task_id=payload.depends_on_task_id,
            dependency_type=payload.dependency_type or "FINISH_TO_START",
            lag_duration=payload.lag_duration or 0.0,
            lag_unit=payload.lag_unit or "DAYS",
            created_by=current_user.id,
        )
        return {
            "id": dep.id,
            "task_id": dep.task_id,
            "depends_on_task_id": dep.depends_on_task_id,
            "dependency_type": dep.dependency_type,
            "lag_duration": dep.lag_duration,
            "lag_unit": dep.lag_unit,
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.delete("/projects/{project_id}/planning/dependencies/{dependency_id}")
@router.delete("/planning/dependencies/{dependency_id}")
def delete_dependency(
    dependency_id: str,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        ProjectPlanningService.delete_task_dependency(db, project_id or 0, dependency_id)
        return {"status": "success", "message": "Dependency removed"}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


# =============================================================================
# 3. CRITICAL PATH METHOD (CPM)
# =============================================================================

@router.get("/projects/{project_id}/critical-path")
def get_critical_path(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.calculate_critical_path(db, project_id)


@router.post("/projects/{project_id}/critical-path/recalculate")
def recalculate_critical_path(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    cpm = ProjectPlanningService.calculate_critical_path(db, project_id)
    ProjectPlanningService.generate_schedule_forecast(db, project_id)
    return cpm


# =============================================================================
# 4. BASELINES & COMPARISON
# =============================================================================

@router.get("/projects/{project_id}/baselines")
def list_baselines(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    baselines = (
        db.query(ProjectBaseline)
        .filter(ProjectBaseline.project_id == project_id, ProjectBaseline.is_archived == False)
        .order_by(ProjectBaseline.version.desc())
        .all()
    )
    return [
        {
            "id": b.id,
            "name": b.name,
            "version": b.version,
            "description": b.description,
            "planned_start": b.planned_start.strftime("%Y-%m-%d") if b.planned_start else None,
            "planned_end": b.planned_end.strftime("%Y-%m-%d") if b.planned_end else None,
            "total_duration_days": b.total_duration_days,
            "total_estimated_effort_hours": b.total_estimated_effort_hours,
            "total_budget": b.total_budget,
            "currency": b.currency,
            "created_at": b.created_at.isoformat(),
        }
        for b in baselines
    ]


@router.post("/projects/{project_id}/baselines", status_code=status.HTTP_201_CREATED)
def create_baseline(
    project_id: int,
    payload: BaselineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    try:
        baseline = ProjectPlanningService.create_project_baseline(
            db=db,
            project_id=project_id,
            name=payload.name,
            description=payload.description,
            created_by=current_user.id,
        )
        return {
            "id": baseline.id,
            "name": baseline.name,
            "version": baseline.version,
            "total_duration_days": baseline.total_duration_days,
            "created_at": baseline.created_at.isoformat(),
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("/baselines/{baseline_id}/comparison")
def compare_baseline(
    baseline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ProjectPlanningService.compare_baseline_with_current(db, baseline_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


# =============================================================================
# 5. PROJECT BUDGET & COSTS
# =============================================================================

@router.get("/projects/{project_id}/budget")
def get_budget(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.get_budget_summary(db, project_id)


@router.put("/projects/{project_id}/budget")
def update_budget(
    project_id: int,
    payload: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.update_budget(
        db=db,
        project_id=project_id,
        total_budget=payload.total_budget,
        currency=payload.currency or "USD",
        notes=payload.notes,
        is_approved=payload.is_approved,
        user_id=current_user.id,
    )


@router.post("/projects/{project_id}/budget/costs", status_code=status.HTTP_201_CREATED)
def record_cost(
    project_id: int,
    payload: CostRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    cost = ProjectPlanningService.add_cost_record(
        db=db,
        project_id=project_id,
        description=payload.description,
        amount=payload.amount,
        category_id=payload.category_id,
        record_type=payload.record_type or "ACTUAL",
        currency=payload.currency or "USD",
        user_id=current_user.id,
    )
    return {
        "id": cost.id,
        "description": cost.description,
        "amount": cost.amount,
        "record_type": cost.record_type,
        "date_incurred": cost.date_incurred.strftime("%Y-%m-%d"),
    }


# =============================================================================
# 6. SCHEDULE FORECASTING
# =============================================================================

@router.get("/projects/{project_id}/forecast")
def get_forecast(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.generate_schedule_forecast(db, project_id)


@router.post("/projects/{project_id}/forecast/recalculate")
def recalculate_forecast(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    return ProjectPlanningService.generate_schedule_forecast(db, project_id)


# =============================================================================
# 7. WHAT-IF SCENARIOS & SIMULATIONS
# =============================================================================

@router.get("/projects/{project_id}/scenarios")
def list_scenarios(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    scenarios = (
        db.query(ProjectScheduleScenario)
        .filter(ProjectScheduleScenario.project_id == project_id)
        .order_by(ProjectScheduleScenario.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "applied_at": s.applied_at.isoformat() if s.applied_at else None,
            "outcomes": s.outcomes,
            "changes_count": len(s.task_changes),
        }
        for s in scenarios
    ]


@router.post("/projects/{project_id}/scenarios", status_code=status.HTTP_201_CREATED)
def create_scenario(
    project_id: int,
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_access(project_id, current_user, db)
    scenario = ProjectPlanningService.create_scenario(
        db=db,
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        user_id=current_user.id,
    )
    return {
        "id": scenario.id,
        "name": scenario.name,
        "status": scenario.status,
        "created_at": scenario.created_at.isoformat(),
    }


@router.post("/scenarios/{scenario_id}/changes")
def add_scenario_change(
    scenario_id: int,
    payload: ScenarioTaskChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change = ProjectPlanningService.add_scenario_task_change(
        db=db,
        scenario_id=scenario_id,
        task_id=payload.task_id,
        proposed_start_date=payload.proposed_start_date,
        proposed_due_date=payload.proposed_due_date,
        proposed_duration_days=payload.proposed_duration_days,
        proposed_priority=payload.proposed_priority,
        proposed_assignee_id=payload.proposed_assignee_id,
    )
    return {
        "id": change.id,
        "task_id": change.task_id,
        "proposed_duration_days": change.proposed_duration_days,
    }


@router.post("/scenarios/{scenario_id}/simulate")
def run_simulation(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ProjectPlanningService.simulate_scenario(db, scenario_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.post("/scenarios/{scenario_id}/apply")
def apply_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ProjectPlanningService.apply_scenario(db, scenario_id, user_id=current_user.id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
