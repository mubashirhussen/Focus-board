from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsSummary,
    TrendItem,
    TrendComparisonResponse,
    AnalyticsDistribution,
    AnalyticsInsightsResponse,
    PersonalProductivityResponse,
    ProjectAnalyticsResponse,
    TeamAnalyticsResponse,
    WorkspaceAnalyticsResponse,
    OrganizationAnalyticsResponse,
    DeadlineAnalyticsResponse,
    ActivityAnalyticsResponse,
    KPISummaryResponse,
)
from app.api.dependencies import get_current_user
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Productivity Reports"])

# -------------------------------------------------------------
# 1. Main Dashboard & KPI Summaries
# -------------------------------------------------------------
@router.get("/summary", response_model=AnalyticsSummary)
@router.get("/dashboard", response_model=AnalyticsSummary)
def get_dashboard_summary(
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to project"),
    team_id: Optional[int] = Query(None, description="Scope to team"),
    organization_id: Optional[int] = Query(None, description="Scope to organization"),
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate aggregate task and project KPI metrics for the dashboard."""
    return analytics_service.get_dashboard_summary(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
        team_id=team_id,
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )

@router.get("/kpis", response_model=KPISummaryResponse)
def get_kpis(
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unified summary of core organizational performance KPIs."""
    return analytics_service.get_kpis(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
    )

# -------------------------------------------------------------
# 2. Personal Productivity Analytics
# -------------------------------------------------------------
@router.get("/personal", response_model=PersonalProductivityResponse)
def get_personal_analytics(
    start_date: Optional[str] = Query(None, description="Filter start date"),
    end_date: Optional[str] = Query(None, description="Filter end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Personal productivity, velocity, and workload metrics for the authenticated user."""
    return analytics_service.get_personal_analytics(
        db=db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )

# -------------------------------------------------------------
# 3. Project Analytics & Health
# -------------------------------------------------------------
@router.get("/projects", response_model=ProjectAnalyticsResponse)
def get_projects_analytics(
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to specific project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregate project performance, progress, and health metrics."""
    return analytics_service.get_project_analytics(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
    )

@router.get("/projects/{project_id}", response_model=ProjectAnalyticsResponse)
def get_single_project_analytics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detailed analytics for an individual project."""
    res = analytics_service.get_project_analytics(
        db=db,
        current_user=current_user,
        project_id=project_id,
    )
    if not res.projects:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return res

# -------------------------------------------------------------
# 4. Team Analytics & Workload Distribution
# -------------------------------------------------------------
@router.get("/teams/{team_id}", response_model=TeamAnalyticsResponse)
def get_team_analytics(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Workload distribution and performance metrics for a specific team."""
    try:
        return analytics_service.get_team_analytics(
            db=db,
            current_user=current_user,
            team_id=team_id,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

# -------------------------------------------------------------
# 5. Workspace & Organization Analytics
# -------------------------------------------------------------
@router.get("/workspaces/{workspace_id}", response_model=WorkspaceAnalyticsResponse)
def get_workspace_analytics(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Workspace-scoped analytics metrics."""
    try:
        return analytics_service.get_workspace_analytics(
            db=db,
            current_user=current_user,
            workspace_id=workspace_id,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")

@router.get("/organization", response_model=OrganizationAnalyticsResponse)
def get_organization_analytics(
    organization_id: Optional[int] = Query(None, description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Organization-level aggregate performance metrics."""
    if not organization_id:
        _, _, _, org_ids = analytics_service.get_accessible_scope(db, current_user)
        if not org_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No organization found.")
        organization_id = org_ids[0]

    try:
        return analytics_service.get_organization_analytics(
            db=db,
            current_user=current_user,
            organization_id=organization_id,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization access denied.")

# -------------------------------------------------------------
# 6. Trends, Distributions & Deadlines
# -------------------------------------------------------------
@router.get("/completion-trends", response_model=List[TrendItem])
def get_completion_trends(
    days: int = Query(7, ge=1, le=90, description="Trend window in days (7, 30, 90)"),
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Daily task creations and completions over the selected window."""
    res = analytics_service.get_completion_trends(
        db=db,
        current_user=current_user,
        days=days,
        workspace_id=workspace_id,
        project_id=project_id,
        compare_previous=False,
    )
    return res.current_period

@router.get("/trends/compare", response_model=TrendComparisonResponse)
def get_trends_comparison(
    days: int = Query(7, ge=1, le=90, description="Comparison window in days"),
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Comparative period trend analysis showing percentage changes and direction."""
    return analytics_service.get_completion_trends(
        db=db,
        current_user=current_user,
        days=days,
        workspace_id=workspace_id,
        project_id=project_id,
        compare_previous=True,
    )

@router.get("/distribution", response_model=AnalyticsDistribution)
def get_distribution(
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Distribution of tasks across status, priority, category, and assignee."""
    return analytics_service.get_distribution(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
    )

@router.get("/deadlines", response_model=DeadlineAnalyticsResponse)
def get_deadlines_analytics(
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deadline adherence, overdue metrics, and schedule risk scores."""
    return analytics_service.get_deadline_analytics(
        db=db,
        current_user=current_user,
        workspace_id=workspace_id,
        project_id=project_id,
    )

@router.get("/activity", response_model=ActivityAnalyticsResponse)
def get_activity_analytics(
    days: int = Query(14, ge=1, le=90, description="Activity window in days"),
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activity event velocity and category distribution."""
    return analytics_service.get_activity_analytics(
        db=db,
        current_user=current_user,
        days=days,
        workspace_id=workspace_id,
    )

@router.get("/insights", response_model=AnalyticsInsightsResponse)
def get_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Smart personalized productivity insights and suggestions."""
    return analytics_service.get_insights(db=db, current_user=current_user)

# -------------------------------------------------------------
# 7. Reports & CSV Export
# -------------------------------------------------------------
@router.get("/export")
def export_analytics_csv(
    report_type: str = Query("tasks", description="Report type: tasks, projects"),
    workspace_id: Optional[int] = Query(None, description="Scope to workspace"),
    project_id: Optional[int] = Query(None, description="Scope to project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export analytics reports to secure CSV format with formula injection sanitization and UTF-8 BOM.
    """
    csv_bytes, filename = analytics_service.generate_csv_report(
        db=db,
        current_user=current_user,
        report_type=report_type,
        workspace_id=workspace_id,
        project_id=project_id,
    )
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
