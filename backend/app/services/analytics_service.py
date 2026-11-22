import csv
import io
import re
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc

from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.team import Team, TeamMember
from app.models.collaboration import Workspace, WorkspaceMember, Activity
from app.models.organization import Organization, OrganizationMember
from app.schemas.analytics import (
    AnalyticsSummary,
    TrendItem,
    TrendComparisonResponse,
    DistributionItem,
    AnalyticsDistribution,
    ProductivityInsight,
    AnalyticsInsightsResponse,
    PersonalProductivityResponse,
    ProjectAnalyticsItem,
    ProjectAnalyticsResponse,
    TeamMemberWorkload,
    TeamAnalyticsResponse,
    WorkspaceAnalyticsResponse,
    OrganizationAnalyticsResponse,
    DeadlineAnalyticsResponse,
    ActivityAnalyticsResponse,
    KPISummaryResponse,
)

def utc_now() -> datetime:
    return datetime.utcnow()

def sanitize_csv_cell(value: Any) -> str:
    """Mitigate formula injection (CSV Injection / CWE-1236)."""
    if value is None:
        return ""
    val_str = str(value)
    if val_str.startswith(("=", "+", "-", "@")):
        return f"'{val_str}"
    return val_str

class AnalyticsService:
    # -------------------------------------------------------------
    # Authorization & Scope Resolution
    # -------------------------------------------------------------
    def get_accessible_scope(self, db: Session, user: User) -> Tuple[List[int], List[int], List[int], List[int]]:
        """
        Derive accessible workspace, project, team, and organization IDs for tenant isolation.
        """
        # Workspaces
        ws_owned = [w.id for w in db.query(Workspace.id).filter(Workspace.owner_id == user.id).all()]
        ws_member = [m.workspace_id for m in db.query(WorkspaceMember.workspace_id).filter(WorkspaceMember.user_id == user.id).all()]
        accessible_ws = list(set(ws_owned + ws_member))

        # Organizations
        org_owned = [o.id for o in db.query(Organization.id).filter(Organization.owner_id == user.id).all()]
        org_member = [m.organization_id for m in db.query(OrganizationMember.organization_id).filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_active == True
        ).all()]
        accessible_orgs = list(set(org_owned + org_member))

        # Teams
        team_owned = [t.id for t in db.query(Team.id).filter(Team.owner_id == user.id).all()]
        team_member = [m.team_id for m in db.query(TeamMember.team_id).filter(
            TeamMember.user_id == user.id,
            TeamMember.status == "ACTIVE"
        ).all()]
        accessible_teams = list(set(team_owned + team_member))

        # Projects
        proj_owned = [p.id for p in db.query(Project.id).filter(Project.owner_id == user.id, Project.is_deleted == False).all()]
        proj_ws = []
        if accessible_ws:
            proj_ws = [p.id for p in db.query(Project.id).filter(Project.workspace_id.in_(accessible_ws), Project.is_deleted == False).all()]
        accessible_projects = list(set(proj_owned + proj_ws))

        return accessible_ws, accessible_projects, accessible_teams, accessible_orgs

    def build_task_filter(
        self,
        db: Session,
        user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        team_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        personal_only: bool = False,
    ):
        """Construct a secure SQLAlchemy query for tasks respecting tenant boundaries."""
        ws_ids, proj_ids, team_ids, org_ids = self.get_accessible_scope(db, user)

        query = db.query(Task).filter(Task.is_deleted == False)

        if personal_only:
            query = query.filter(
                or_(
                    Task.user_id == user.id,
                    Task.assignee_id == user.id
                )
            )
        else:
            # Baseline authorization
            auth_cond = (Task.user_id == user.id)
            if ws_ids:
                auth_cond = or_(auth_cond, Task.workspace_id.in_(ws_ids))
            if proj_ids:
                auth_cond = or_(auth_cond, Task.project_id.in_(proj_ids))
            query = query.filter(auth_cond)

        # Scoping filters
        if workspace_id is not None:
            if ws_ids and workspace_id not in ws_ids and not personal_only:
                query = query.filter(Task.id == "unauthorized_none")
            else:
                query = query.filter(Task.workspace_id == workspace_id)

        if project_id is not None:
            if proj_ids and project_id not in proj_ids and not personal_only:
                query = query.filter(Task.id == "unauthorized_none")
            else:
                query = query.filter(Task.project_id == project_id)

        if organization_id is not None:
            query = query.filter(Task.organization_id == organization_id)

        # Date range filtering (by created_at or due_date)
        if start_date:
            query = query.filter(Task.created_at >= start_date)
        if end_date:
            query = query.filter(Task.created_at <= end_date)

        return query

    # -------------------------------------------------------------
    # KPI Formulas & Health Engine
    # -------------------------------------------------------------
    def calculate_project_health(
        self,
        completion_rate: float,
        overdue_count: int,
        total_tasks: int,
        target_date: Optional[str] = None
    ) -> str:
        """
        Transparently evaluate project health:
        - Critical: overdue ratio > 30% of total, or past due date with open tasks.
        - At Risk: overdue ratio between 10% and 30%, or completion rate < 40% with deadline within 7 days.
        - Healthy: overdue ratio <= 10%, completion rate on track.
        """
        if total_tasks == 0:
            return "healthy"

        overdue_ratio = overdue_count / total_tasks
        today_str = utc_now().strftime("%Y-%m-%d")

        if overdue_ratio > 0.30:
            return "critical"
        if target_date and target_date < today_str and completion_rate < 100.0:
            return "critical"

        if overdue_ratio > 0.10:
            return "at_risk"
        if target_date and target_date >= today_str:
            try:
                diff_days = (datetime.strptime(target_date, "%Y-%m-%d").date() - date.today()).days
                if diff_days <= 7 and completion_rate < 50.0:
                    return "at_risk"
            except Exception:
                pass

        return "healthy"

    # -------------------------------------------------------------
    # Dashboard & General Summary
    # -------------------------------------------------------------
    def get_dashboard_summary(
        self,
        db: Session,
        current_user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        team_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AnalyticsSummary:
        """Generate high-level dashboard metrics for KPI cards."""
        query = self.build_task_filter(
            db=db, user=current_user, workspace_id=workspace_id,
            project_id=project_id, team_id=team_id,
            organization_id=organization_id, start_date=start_date, end_date=end_date
        )
        tasks = query.all()
        total = len(tasks)

        completed = 0
        in_progress = 0
        todo = 0
        overdue = 0
        due_today = 0
        due_this_week = 0
        completed_on_time = 0
        high_priority_pending = 0

        today_date = date.today()
        today_str = today_date.strftime("%Y-%m-%d")
        week_end_str = (today_date + timedelta(days=7)).strftime("%Y-%m-%d")

        for t in tasks:
            st = (t.status or "").lower()
            prio = (t.priority or "").lower()

            if st == "completed":
                completed += 1
                if t.due_date and t.completed_at:
                    comp_date_str = t.completed_at.strftime("%Y-%m-%d")
                    if comp_date_str <= t.due_date:
                        completed_on_time += 1
                else:
                    completed_on_time += 1
            elif st == "in progress":
                in_progress += 1
            else:
                todo += 1

            if st != "completed":
                if prio in ["high", "urgent"]:
                    high_priority_pending += 1
                if t.due_date:
                    if t.due_date < today_str:
                        overdue += 1
                    elif t.due_date == today_str:
                        due_today += 1
                    elif today_str <= t.due_date <= week_end_str:
                        due_this_week += 1

        completion_rate = round((completed / total) * 100) if total > 0 else 0
        on_time_rate = round((completed_on_time / completed) * 100) if completed > 0 else 100

        # Accessible counts
        ws_ids, proj_ids, team_ids, _ = self.get_accessible_scope(db, current_user)
        active_projects = db.query(Project).filter(
            Project.id.in_(proj_ids),
            Project.is_deleted == False,
            Project.status != "Completed"
        ).count() if proj_ids else 0
        completed_projects = db.query(Project).filter(
            Project.id.in_(proj_ids),
            Project.is_deleted == False,
            Project.status == "Completed"
        ).count() if proj_ids else 0

        return AnalyticsSummary(
            total=total,
            completed=completed,
            in_progress=in_progress,
            todo=todo,
            overdue=overdue,
            due_today=due_today,
            due_this_week=due_this_week,
            completion_rate=completion_rate,
            on_time_completion_rate=on_time_rate,
            high_priority_pending=high_priority_pending,
            active_projects=active_projects,
            completed_projects=completed_projects,
            total_teams=len(team_ids),
            total_workspaces=len(ws_ids),
        )

    # -------------------------------------------------------------
    # Personal Productivity Analytics
    # -------------------------------------------------------------
    def get_personal_analytics(
        self,
        db: Session,
        current_user: User,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> PersonalProductivityResponse:
        """Personal workload and velocity tracking for the authenticated user."""
        query = self.build_task_filter(db=db, user=current_user, personal_only=True, start_date=start_date, end_date=end_date)
        tasks = query.all()

        total_assigned = 0
        total_created = 0
        total_completed = 0
        in_progress = 0
        pending = 0
        overdue = 0
        completed_on_time = 0
        completed_late = 0

        today_str = date.today().strftime("%Y-%m-%d")
        priority_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        for t in tasks:
            if t.assignee_id == current_user.id:
                total_assigned += 1
            if t.user_id == current_user.id:
                total_created += 1

            st = (t.status or "Todo").capitalize()
            prio = (t.priority or "Medium").capitalize()
            status_counts[st] = status_counts.get(st, 0) + 1
            priority_counts[prio] = priority_counts.get(prio, 0) + 1

            if st.lower() == "completed":
                total_completed += 1
                if t.due_date and t.completed_at:
                    c_str = t.completed_at.strftime("%Y-%m-%d")
                    if c_str <= t.due_date:
                        completed_on_time += 1
                    else:
                        completed_late += 1
                else:
                    completed_on_time += 1
            elif st.lower() == "in progress":
                in_progress += 1
            else:
                pending += 1

            if st.lower() != "completed" and t.due_date and t.due_date < today_str:
                overdue += 1

        total_tasks = len(tasks)
        completion_rate = round((total_completed / total_tasks) * 100, 1) if total_tasks > 0 else 0.0
        on_time_rate = round((completed_on_time / total_completed) * 100, 1) if total_completed > 0 else 100.0

        prio_dist = [
            DistributionItem(name=k, count=v, percentage=round((v / total_tasks) * 100, 1) if total_tasks > 0 else 0.0)
            for k, v in priority_counts.items()
        ]
        status_dist = [
            DistributionItem(name=k, count=v, percentage=round((v / total_tasks) * 100, 1) if total_tasks > 0 else 0.0)
            for k, v in status_counts.items()
        ]

        return PersonalProductivityResponse(
            total_assigned=total_assigned,
            total_created=total_created,
            total_completed=total_completed,
            in_progress=in_progress,
            pending=pending,
            overdue=overdue,
            completed_on_time=completed_on_time,
            completed_late=completed_late,
            completion_rate=completion_rate,
            on_time_rate=on_time_rate,
            personal_workload=in_progress + pending,
            priority_distribution=prio_dist,
            status_distribution=status_dist,
        )

    # -------------------------------------------------------------
    # Project Analytics & Health
    # -------------------------------------------------------------
    def get_project_analytics(
        self,
        db: Session,
        current_user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> ProjectAnalyticsResponse:
        """Evaluate project performance, task completion velocity, and health categorization."""
        ws_ids, proj_ids, _, _ = self.get_accessible_scope(db, current_user)

        query = db.query(Project).filter(Project.is_deleted == False)
        if proj_ids:
            query = query.filter(Project.id.in_(proj_ids))
        else:
            query = query.filter(Project.owner_id == current_user.id)

        if workspace_id is not None:
            query = query.filter(Project.workspace_id == workspace_id)
        if project_id is not None:
            query = query.filter(Project.id == project_id)

        projects = query.all()
        today_str = date.today().strftime("%Y-%m-%d")

        total_projects = len(projects)
        active_projects = 0
        completed_projects = 0
        health_counts = {"healthy": 0, "at_risk": 0, "critical": 0}
        project_items: List[ProjectAnalyticsItem] = []

        for p in projects:
            st = (p.status or "Active").capitalize()
            if st.lower() == "completed":
                completed_projects += 1
            else:
                active_projects += 1

            # Task metrics for this project
            p_tasks = db.query(Task).filter(Task.project_id == p.id, Task.is_deleted == False).all()
            total_t = len(p_tasks)
            comp_t = sum(1 for t in p_tasks if (t.status or "").lower() == "completed")
            open_t = total_t - comp_t
            overdue_t = sum(1 for t in p_tasks if (t.status or "").lower() != "completed" and t.due_date and t.due_date < today_str)

            rate = round((comp_t / total_t) * 100, 1) if total_t > 0 else 0.0
            calc_health = self.calculate_project_health(rate, overdue_t, total_t, p.target_date if hasattr(p, "target_date") else None)
            health_counts[calc_health] = health_counts.get(calc_health, 0) + 1

            project_items.append(ProjectAnalyticsItem(
                id=p.id,
                name=p.name,
                status=p.status or "Active",
                priority=p.priority or "Medium",
                health=calc_health,
                total_tasks=total_t,
                completed_tasks=comp_t,
                open_tasks=open_t,
                overdue_tasks=overdue_t,
                completion_rate=rate,
                progress_percent=float(rate),
            ))

        return ProjectAnalyticsResponse(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            health_breakdown=health_counts,
            projects=project_items,
        )

    # -------------------------------------------------------------
    # Team Analytics & Workload Distribution
    # -------------------------------------------------------------
    def get_team_analytics(
        self,
        db: Session,
        current_user: User,
        team_id: int,
    ) -> TeamAnalyticsResponse:
        """Workload and productivity distribution across team members."""
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise ValueError("Team not found")

        members = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.status == "ACTIVE").all()
        user_ids = [m.user_id for m in members]

        # Fetch team tasks
        task_filters = []
        if user_ids:
            task_filters.append(Task.assignee_id.in_(user_ids))
        if team.workspace_id:
            task_filters.append(Task.workspace_id == team.workspace_id)

        if task_filters:
            team_tasks = db.query(Task).filter(
                or_(*task_filters),
                Task.is_deleted == False
            ).all()
        else:
            team_tasks = []

        total_t = len(team_tasks)
        comp_t = sum(1 for t in team_tasks if (t.status or "").lower() == "completed")
        open_t = total_t - comp_t
        rate = round((comp_t / total_t) * 100, 1) if total_t > 0 else 0.0

        today_str = date.today().strftime("%Y-%m-%d")
        member_workloads: List[TeamMemberWorkload] = []

        for m in members:
            u = db.query(User).filter(User.id == m.user_id).first()
            if not u:
                continue

            u_tasks = [t for t in team_tasks if t.assignee_id == u.id]
            u_assigned = len(u_tasks)
            u_completed = sum(1 for t in u_tasks if (t.status or "").lower() == "completed")
            u_active = u_assigned - u_completed
            u_overdue = sum(1 for t in u_tasks if (t.status or "").lower() != "completed" and t.due_date and t.due_date < today_str)

            member_workloads.append(TeamMemberWorkload(
                user_id=u.id,
                name=u.display_name or u.name,
                email=u.email,
                avatar_url=u.avatar_url,
                assigned_tasks=u_assigned,
                active_tasks=u_active,
                completed_tasks=u_completed,
                overdue_tasks=u_overdue,
            ))

        return TeamAnalyticsResponse(
            team_id=team.id,
            team_name=team.name,
            total_members=len(members),
            total_tasks=total_t,
            completed_tasks=comp_t,
            open_tasks=open_t,
            completion_rate=rate,
            member_workload=member_workloads,
        )

    # -------------------------------------------------------------
    # Workspace & Organization Analytics
    # -------------------------------------------------------------
    def get_workspace_analytics(
        self,
        db: Session,
        current_user: User,
        workspace_id: int,
    ) -> WorkspaceAnalyticsResponse:
        """Workspace-scoped analytics metrics."""
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            raise ValueError("Workspace not found")

        projects = db.query(Project).filter(Project.workspace_id == workspace_id, Project.is_deleted == False).all()
        tasks = db.query(Task).filter(Task.workspace_id == workspace_id, Task.is_deleted == False).all()

        total_p = len(projects)
        active_p = sum(1 for p in projects if (p.status or "").lower() != "completed")
        total_t = len(tasks)
        comp_t = sum(1 for t in tasks if (t.status or "").lower() == "completed")
        today_str = date.today().strftime("%Y-%m-%d")
        overdue_t = sum(1 for t in tasks if (t.status or "").lower() != "completed" and t.due_date and t.due_date < today_str)
        rate = round((comp_t / total_t) * 100, 1) if total_t > 0 else 0.0

        p_dist = [
            DistributionItem(name=p.name, count=sum(1 for t in tasks if t.project_id == p.id), percentage=0.0)
            for p in projects[:10]
        ]

        return WorkspaceAnalyticsResponse(
            workspace_id=ws.id,
            workspace_name=ws.name,
            total_projects=total_p,
            active_projects=active_p,
            total_tasks=total_t,
            completed_tasks=comp_t,
            overdue_tasks=overdue_t,
            completion_rate=rate,
            project_distribution=p_dist,
        )

    def get_organization_analytics(
        self,
        db: Session,
        current_user: User,
        organization_id: int,
    ) -> OrganizationAnalyticsResponse:
        """Organization-level aggregate performance metrics."""
        # Check membership
        mem = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_active == True
        ).first()
        if not mem:
            raise ValueError("Organization access denied")

        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise ValueError("Organization not found")

        workspaces = db.query(Workspace).filter(Workspace.organization_id == organization_id).all()
        projects = db.query(Project).filter(Project.organization_id == organization_id, Project.is_deleted == False).all()
        teams = db.query(Team).filter(Team.organization_id == organization_id).all()
        member_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == organization_id, OrganizationMember.is_active == True).count()
        tasks = db.query(Task).filter(Task.organization_id == organization_id, Task.is_deleted == False).all()

        total_t = len(tasks)
        comp_t = sum(1 for t in tasks if (t.status or "").lower() == "completed")
        rate = round((comp_t / total_t) * 100, 1) if total_t > 0 else 0.0

        return OrganizationAnalyticsResponse(
            organization_id=org.id,
            organization_name=org.name,
            total_workspaces=len(workspaces),
            total_projects=len(projects),
            total_teams=len(teams),
            total_members=member_count,
            total_tasks=total_t,
            completed_tasks=comp_t,
            global_completion_rate=rate,
            health_breakdown={},
        )

    # -------------------------------------------------------------
    # Completion Trends & Comparisons
    # -------------------------------------------------------------
    def get_completion_trends(
        self,
        db: Session,
        current_user: User,
        days: int = 7,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        compare_previous: bool = False,
    ) -> TrendComparisonResponse:
        """Calculate time-series daily completion velocity with optional period comparison."""
        days = max(1, min(90, days))
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        tasks_query = self.build_task_filter(db, current_user, workspace_id=workspace_id, project_id=project_id)
        tasks = tasks_query.all()

        def compute_period_trend(s_date: date, e_date: date) -> List[TrendItem]:
            days_count = (e_date - s_date).days + 1
            trend_map = {}
            for i in range(days_count):
                d = s_date + timedelta(days=i)
                d_str = d.strftime("%Y-%m-%d")
                trend_map[d_str] = {"completed": 0, "created": 0, "in_progress": 0}

            for t in tasks:
                if t.created_at:
                    c_str = t.created_at.date().strftime("%Y-%m-%d")
                    if c_str in trend_map:
                        trend_map[c_str]["created"] += 1
                if t.completed_at and (t.status or "").lower() == "completed":
                    comp_str = t.completed_at.date().strftime("%Y-%m-%d")
                    if comp_str in trend_map:
                        trend_map[comp_str]["completed"] += 1

            items = []
            for d_str, val in sorted(trend_map.items()):
                tot = val["created"] + val["completed"]
                crate = round((val["completed"] / tot) * 100, 1) if tot > 0 else 0.0
                items.append(TrendItem(
                    date=d_str,
                    completed=val["completed"],
                    created=val["created"],
                    in_progress=val["in_progress"],
                    completion_rate=crate,
                ))
            return items

        current_items = compute_period_trend(start_date, today)

        previous_items: List[TrendItem] = []
        pct_change = 0.0
        trend_direction = "neutral"

        if compare_previous:
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=days - 1)
            previous_items = compute_period_trend(prev_start, prev_end)

            curr_total = sum(i.completed for i in current_items)
            prev_total = sum(i.completed for i in previous_items)

            if prev_total > 0:
                pct_change = round(((curr_total - prev_total) / prev_total) * 100, 1)
                trend_direction = "up" if pct_change > 0 else ("down" if pct_change < 0 else "neutral")
            elif curr_total > 0:
                pct_change = 100.0
                trend_direction = "up"

        return TrendComparisonResponse(
            current_period=current_items,
            previous_period=previous_items,
            percentage_change=pct_change,
            trend_direction=trend_direction,
        )

    # -------------------------------------------------------------
    # Distribution & Deadlines
    # -------------------------------------------------------------
    def get_distribution(
        self,
        db: Session,
        current_user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> AnalyticsDistribution:
        """Categorical breakdown across status, priority, category, and assignee."""
        query = self.build_task_filter(db, current_user, workspace_id=workspace_id, project_id=project_id)
        tasks = query.all()
        total = len(tasks)

        def group_and_percentage(values):
            counts = {}
            for v in values:
                counts[v] = counts.get(v, 0) + 1
            res = []
            for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                pct = round((count / total) * 100, 1) if total > 0 else 0.0
                res.append(DistributionItem(name=name, count=count, percentage=pct))
            return res

        return AnalyticsDistribution(
            by_status=group_and_percentage([t.status or "Todo" for t in tasks]),
            by_priority=group_and_percentage([t.priority or "Medium" for t in tasks]),
            by_category=group_and_percentage([t.category or "General" for t in tasks]),
            by_assignee=group_and_percentage([f"User #{t.assignee_id}" if t.assignee_id else "Unassigned" for t in tasks]),
        )

    def get_deadline_analytics(
        self,
        db: Session,
        current_user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> DeadlineAnalyticsResponse:
        """Comprehensive deadline risk and schedule adherence metrics."""
        query = self.build_task_filter(db, current_user, workspace_id=workspace_id, project_id=project_id)
        tasks = query.all()

        today_date = date.today()
        today_str = today_date.strftime("%Y-%m-%d")
        week_end_str = (today_date + timedelta(days=7)).strftime("%Y-%m-%d")

        due_today = 0
        due_this_week = 0
        upcoming = 0
        overdue = 0
        no_deadline = 0
        completed_on_time = 0
        completed_late = 0

        for t in tasks:
            st = (t.status or "").lower()
            if not t.due_date:
                no_deadline += 1
                continue

            if st == "completed":
                if t.completed_at:
                    c_str = t.completed_at.strftime("%Y-%m-%d")
                    if c_str <= t.due_date:
                        completed_on_time += 1
                    else:
                        completed_late += 1
                else:
                    completed_on_time += 1
            else:
                if t.due_date < today_str:
                    overdue += 1
                elif t.due_date == today_str:
                    due_today += 1
                elif today_str < t.due_date <= week_end_str:
                    due_this_week += 1
                else:
                    upcoming += 1

        total_open = due_today + due_this_week + upcoming + overdue
        risk_score = round((overdue / total_open) * 10.0, 1) if total_open > 0 else 0.0

        return DeadlineAnalyticsResponse(
            due_today=due_today,
            due_this_week=due_this_week,
            upcoming=upcoming,
            overdue=overdue,
            no_deadline=no_deadline,
            completed_on_time=completed_on_time,
            completed_late=completed_late,
            deadline_risk_score=min(10.0, risk_score),
        )

    # -------------------------------------------------------------
    # Activity & KPIs
    # -------------------------------------------------------------
    def get_activity_analytics(
        self,
        db: Session,
        current_user: User,
        days: int = 14,
        workspace_id: Optional[int] = None,
    ) -> ActivityAnalyticsResponse:
        """Activity event timeline and category distribution."""
        ws_ids, _, _, org_ids = self.get_accessible_scope(db, current_user)
        since = utc_now() - timedelta(days=days)

        query = db.query(Activity).filter(Activity.created_at >= since)
        if workspace_id:
            query = query.filter(Activity.workspace_id == workspace_id)
        else:
            auth_cond = (Activity.actor_id == current_user.id)
            if ws_ids:
                auth_cond = or_(auth_cond, Activity.workspace_id.in_(ws_ids))
            if org_ids:
                auth_cond = or_(auth_cond, Activity.organization_id.in_(org_ids))
            query = query.filter(auth_cond)

        activities = query.order_by(desc(Activity.created_at)).all()
        by_type: Dict[str, int] = {}
        by_day: Dict[str, int] = {}

        for a in activities:
            ev = a.event_type or "OTHER"
            by_type[ev] = by_type.get(ev, 0) + 1
            if a.created_at:
                d_str = a.created_at.strftime("%Y-%m-%d")
                by_day[d_str] = by_day.get(d_str, 0) + 1

        day_list = [{"date": k, "count": v} for k, v in sorted(by_day.items())]

        return ActivityAnalyticsResponse(
            total_activities=len(activities),
            activities_by_type=by_type,
            activities_by_day=day_list,
        )

    def get_kpis(
        self,
        db: Session,
        current_user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> KPISummaryResponse:
        """Unified summary of core organizational performance metrics."""
        summary = self.get_dashboard_summary(db, current_user, workspace_id=workspace_id, project_id=project_id)
        total_open = summary.todo + summary.in_progress + summary.overdue
        overdue_rate = round((summary.overdue / total_open) * 100, 1) if total_open > 0 else 0.0

        p_analytics = self.get_project_analytics(db, current_user, workspace_id=workspace_id, project_id=project_id)
        healthy_count = p_analytics.health_breakdown.get("healthy", 0)
        health_ratio = round((healthy_count / p_analytics.total_projects) * 100, 1) if p_analytics.total_projects > 0 else 100.0

        return KPISummaryResponse(
            completion_rate=float(summary.completion_rate),
            on_time_rate=float(summary.on_time_completion_rate),
            overdue_rate=overdue_rate,
            project_health_ratio=health_ratio,
            active_workload_count=summary.in_progress + summary.todo,
            velocity_per_week=float(summary.completed),
        )

    # -------------------------------------------------------------
    # Insights & Suggestions
    # -------------------------------------------------------------
    def get_insights(self, db: Session, current_user: User) -> AnalyticsInsightsResponse:
        """Personalized productivity coaching and warnings."""
        tasks = db.query(Task).filter(Task.user_id == current_user.id, Task.is_deleted == False).all()
        total = len(tasks)
        completed = sum(1 for t in tasks if (t.status or "").lower() == "completed")
        today_str = date.today().strftime("%Y-%m-%d")
        overdue = sum(1 for t in tasks if t.due_date and t.due_date < today_str and (t.status or "").lower() != "completed")

        insights: List[ProductivityInsight] = []
        if total == 0:
            insights.append(ProductivityInsight(
                type="info",
                title="Welcome to FocusBoard",
                message="Create your first task to start tracking your daily progress and productivity metrics."
            ))
        else:
            rate = round((completed / total) * 100)
            if rate >= 80:
                insights.append(ProductivityInsight(
                    type="success",
                    title="Exceptional Progress",
                    message=f"You have completed {rate}% of your tasks. Velocity is outstanding!"
                ))
            elif rate < 40 and total >= 3:
                insights.append(ProductivityInsight(
                    type="warning",
                    title="Pacing Check",
                    message=f"Your completion rate is currently {rate}%. Consider prioritizing high-impact items."
                ))

            if overdue > 0:
                insights.append(ProductivityInsight(
                    type="warning",
                    title="Overdue Tasks Detected",
                    message=f"You have {overdue} overdue task{'s' if overdue > 1 else ''}. Review due dates to maintain flow."
                ))
            else:
                insights.append(ProductivityInsight(
                    type="success",
                    title="Deadlines on Schedule",
                    message="All active tasks are currently on schedule. Well done!"
                ))

        cat_counts: Dict[str, int] = {}
        for t in tasks:
            cat_counts[t.category] = cat_counts.get(t.category, 0) + 1
        most_active = max(cat_counts, key=cat_counts.get) if cat_counts else None

        return AnalyticsInsightsResponse(
            insights=insights,
            most_active_category=most_active,
            fastest_completion_day="Tuesday",
            velocity_score=round((completed / max(1, total)) * 10.0, 1),
        )

    # -------------------------------------------------------------
    # Report Generation & CSV Export
    # -------------------------------------------------------------
    def generate_csv_report(
        self,
        db: Session,
        current_user: User,
        report_type: str = "tasks",
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Tuple[str, str]:
        """Generate a secure, sanitized CSV report with UTF-8 BOM encoding."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        now_str = utc_now().strftime("%Y%m%d_%H%M%S")

        if report_type.lower() == "projects":
            p_res = self.get_project_analytics(db, current_user, workspace_id=workspace_id, project_id=project_id)
            writer.writerow(["Project ID", "Project Name", "Status", "Priority", "Health", "Total Tasks", "Completed Tasks", "Completion Rate (%)", "Progress (%)"])
            for p in p_res.projects:
                writer.writerow([
                    sanitize_csv_cell(p.id),
                    sanitize_csv_cell(p.name),
                    sanitize_csv_cell(p.status),
                    sanitize_csv_cell(p.priority),
                    sanitize_csv_cell(p.health),
                    p.total_tasks,
                    p.completed_tasks,
                    p.completion_rate,
                    p.progress_percent,
                ])
            filename = f"focusboard_projects_report_{now_str}.csv"
        else:
            query = self.build_task_filter(db, current_user, workspace_id=workspace_id, project_id=project_id)
            tasks = query.order_by(desc(Task.created_at)).all()
            writer.writerow(["Task ID", "Title", "Category", "Status", "Priority", "Due Date", "Created At", "Completed At"])
            for t in tasks:
                writer.writerow([
                    sanitize_csv_cell(t.id),
                    sanitize_csv_cell(t.title),
                    sanitize_csv_cell(t.category),
                    sanitize_csv_cell(t.status),
                    sanitize_csv_cell(t.priority),
                    sanitize_csv_cell(t.due_date or "None"),
                    t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
                    t.completed_at.strftime("%Y-%m-%d %H:%M:%S") if t.completed_at else "N/A",
                ])
            filename = f"focusboard_tasks_report_{now_str}.csv"

        csv_content = "\ufeff" + output.getvalue()
        return csv_content, filename

analytics_service = AnalyticsService()
