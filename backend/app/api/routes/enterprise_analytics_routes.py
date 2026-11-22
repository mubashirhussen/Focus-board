from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.collaboration import Workspace, WorkspaceMember, Project
from app.models.enterprise_analytics import (
    ProjectMilestone,
    ProjectRisk,
    ResourceCapacity,
    AnalyticsReport,
)
from app.schemas.enterprise_analytics import (
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    ProjectMilestoneResponse,
    ProjectRiskCreate,
    ProjectRiskUpdate,
    ProjectRiskResponse,
    ResourceCapacityCreate,
    ResourceCapacityResponse,
    ProjectHealthResponse,
    PortfolioHealthResponse,
    ExecutiveKPISummary,
    TeamWorkloadResponse,
    AnalyticsReportCreate,
    AnalyticsReportResponse,
)
from app.services.enterprise_analytics_service import EnterpriseAnalyticsService

router = APIRouter(prefix="/enterprise-analytics", tags=["Enterprise Analytics & Executive Dashboards"])

def resolve_workspace_id(db: Session, user_id: int, workspace_id: Optional[int] = None) -> int:
    if workspace_id:
        return workspace_id
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user_id).first()
    if member:
        return member.workspace_id
    ws = db.query(Workspace).filter(Workspace.owner_id == user_id).first()
    if ws:
        return ws.id
    ws = Workspace(name="Default Workspace", owner_id=user_id)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user_id, role="OWNER"))
    db.commit()
    return ws.id

@router.get("/executive-summary", response_model=ExecutiveKPISummary)
def get_executive_summary(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    return EnterpriseAnalyticsService.get_executive_summary(db, ws_id)

@router.get("/portfolio-health", response_model=PortfolioHealthResponse)
def get_portfolio_health(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    return EnterpriseAnalyticsService.get_portfolio_health(db, ws_id)

@router.get("/projects/{project_id}/health", response_model=ProjectHealthResponse)
def get_project_health(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    health = EnterpriseAnalyticsService.calculate_project_health(db, project_id)
    if not health:
        raise HTTPException(status_code=404, detail="Project not found")
    return health

# Milestones
@router.get("/projects/{project_id}/milestones", response_model=List[ProjectMilestoneResponse])
def get_project_milestones(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.project_id == project_id)
        .order_by(ProjectMilestone.due_date.asc().nulls_last())
        .all()
    )

@router.post("/projects/{project_id}/milestones", response_model=ProjectMilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_project_milestone(
    project_id: int,
    payload: ProjectMilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestone = ProjectMilestone(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        status=payload.status,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone

@router.patch("/milestones/{milestone_id}", response_model=ProjectMilestoneResponse)
def update_project_milestone(
    milestone_id: str,
    payload: ProjectMilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    if payload.title is not None:
        milestone.title = payload.title
    if payload.description is not None:
        milestone.description = payload.description
    if payload.due_date is not None:
        milestone.due_date = payload.due_date
    if payload.status is not None:
        milestone.status = payload.status
        if payload.status == "COMPLETED" and not milestone.completed_at:
            milestone.completed_at = datetime.now(timezone.utc)
    if payload.completed_at is not None:
        milestone.completed_at = payload.completed_at

    db.commit()
    db.refresh(milestone)
    return milestone

@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_milestone(
    milestone_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(milestone)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Risks
@router.get("/projects/{project_id}/risks", response_model=List[ProjectRiskResponse])
def get_project_risks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ProjectRisk)
        .filter(ProjectRisk.project_id == project_id)
        .order_by(ProjectRisk.detected_at.desc())
        .all()
    )

@router.post("/projects/{project_id}/risks", response_model=ProjectRiskResponse, status_code=status.HTTP_201_CREATED)
def create_project_risk(
    project_id: int,
    payload: ProjectRiskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    risk = ProjectRisk(
        project_id=project_id,
        category=payload.category,
        severity=payload.severity,
        title=payload.title,
        description=payload.description,
        mitigation_plan=payload.mitigation_plan,
        status="ACTIVE",
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk

@router.patch("/risks/{risk_id}", response_model=ProjectRiskResponse)
def update_project_risk(
    risk_id: str,
    payload: ProjectRiskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    risk = db.query(ProjectRisk).filter(ProjectRisk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    if payload.category is not None:
        risk.category = payload.category
    if payload.severity is not None:
        risk.severity = payload.severity
    if payload.title is not None:
        risk.title = payload.title
    if payload.description is not None:
        risk.description = payload.description
    if payload.status is not None:
        risk.status = payload.status
        if payload.status in ("RESOLVED", "MITIGATED") and not risk.resolved_at:
            risk.resolved_at = datetime.now(timezone.utc)
    if payload.mitigation_plan is not None:
        risk.mitigation_plan = payload.mitigation_plan

    db.commit()
    db.refresh(risk)
    return risk

# Team Workload & Resource Capacity
@router.get("/team-workload", response_model=TeamWorkloadResponse)
def get_team_workload(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    return EnterpriseAnalyticsService.get_team_workload(db, ws_id)

@router.post("/resource-capacity", response_model=ResourceCapacityResponse, status_code=status.HTTP_201_CREATED)
def set_resource_capacity(
    payload: ResourceCapacityCreate,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    
    cap = db.query(ResourceCapacity).filter(
        ResourceCapacity.user_id == payload.user_id,
        ResourceCapacity.workspace_id == ws_id
    ).first()

    if cap:
        cap.weekly_hours_capacity = payload.weekly_hours_capacity
        if payload.effective_date:
            cap.effective_date = payload.effective_date
    else:
        cap = ResourceCapacity(
            user_id=payload.user_id,
            workspace_id=ws_id,
            weekly_hours_capacity=payload.weekly_hours_capacity,
            effective_date=payload.effective_date or datetime.now(timezone.utc)
        )
        db.add(cap)

    db.commit()
    db.refresh(cap)
    return cap

# Reports
@router.post("/reports", response_model=AnalyticsReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: AnalyticsReportCreate,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    return EnterpriseAnalyticsService.generate_report(
        db=db,
        user_id=current_user.id,
        workspace_id=ws_id,
        title=payload.title,
        report_type=payload.report_type,
        parameters=payload.parameters,
        fmt=payload.format,
    )

@router.get("/reports", response_model=List[AnalyticsReportResponse])
def list_reports(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws_id = resolve_workspace_id(db, current_user.id, workspace_id)
    return (
        db.query(AnalyticsReport)
        .filter(AnalyticsReport.workspace_id == ws_id)
        .order_by(AnalyticsReport.created_at.desc())
        .all()
    )

@router.get("/reports/{report_id}/download")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(AnalyticsReport).filter(AnalyticsReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.format == "CSV":
        csv_content = EnterpriseAnalyticsService.export_report_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{report.title}.csv"'}
        )
    else:
        return Response(
            content=report.summary_json,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{report.title}.json"'}
        )
