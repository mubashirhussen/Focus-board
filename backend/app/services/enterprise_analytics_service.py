import io
import csv
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.collaboration import Project, Workspace, WorkspaceMember
from app.models.task import Task
from app.models.user import User
from app.models.enterprise_analytics import (
    ProjectMilestone,
    ProjectRisk,
    ResourceCapacity,
    AnalyticsReport,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class EnterpriseAnalyticsService:

    @staticmethod
    def calculate_project_health(db: Session, project_id: int) -> Dict[str, Any]:
        """Calculates deterministic health score (0-100), health category, explainable signals, and forecast."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        total_tasks = len(tasks)
        completed_tasks = [t for t in tasks if t.status in ("completed", "done")]
        in_progress_tasks = [t for t in tasks if t.status == "in_progress"]
        open_tasks = [t for t in tasks if t.status not in ("completed", "done", "cancelled")]

        now = utc_now()
        overdue_tasks = []
        for t in open_tasks:
            if t.due_date:
                # Handle ISO string or datetime
                due_dt = None
                if isinstance(t.due_date, datetime):
                    due_dt = t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)
                elif isinstance(t.due_date, str):
                    try:
                        due_dt = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))
                    except Exception:
                        pass
                if due_dt and due_dt < now:
                    overdue_tasks.append(t)

        milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).all()
        completed_milestones = [m for m in milestones if m.status == "COMPLETED"]
        active_risks = db.query(ProjectRisk).filter(
            ProjectRisk.project_id == project_id,
            ProjectRisk.status == "ACTIVE"
        ).all()

        signals = []

        if total_tasks == 0:
            return {
                "project_id": project.id,
                "project_name": project.name,
                "status": project.status,
                "deadline": project.deadline,
                "health_score": 100,
                "health_status": "INSUFFICIENT_DATA",
                "total_tasks": 0,
                "completed_tasks": 0,
                "overdue_tasks": 0,
                "in_progress_tasks": 0,
                "completion_rate": 0.0,
                "velocity_trend": "UNKNOWN",
                "signals": ["No tasks currently tracked in this project."],
                "forecast": {"status": "insufficient_data", "message": "Add tasks to project to generate delivery forecast."},
                "active_risks_count": len(active_risks),
                "milestones_total": len(milestones),
                "milestones_completed": len(completed_milestones),
            }

        # Scoring logic
        completion_rate = (len(completed_tasks) / total_tasks) * 100.0
        score = 100.0
        deductions = 0.0

        # Overdue penalty (max 40 pts)
        if open_tasks:
            overdue_ratio = len(overdue_tasks) / len(open_tasks)
            deduction_overdue = min(40.0, overdue_ratio * 40.0)
            deductions += deduction_overdue
            if len(overdue_tasks) > 0:
                signals.append(f"{len(overdue_tasks)} of {len(open_tasks)} open tasks are past their deadline.")

        # Risk penalty (max 35 pts)
        risk_penalty = 0.0
        for r in active_risks:
            if r.severity == "CRITICAL":
                risk_penalty += 20.0
            elif r.severity == "HIGH":
                risk_penalty += 10.0
            elif r.severity == "MEDIUM":
                risk_penalty += 5.0
        deductions += min(35.0, risk_penalty)
        if active_risks:
            high_critical = [r.title for r in active_risks if r.severity in ("CRITICAL", "HIGH")]
            if high_critical:
                signals.append(f"Active critical/high risks: {', '.join(high_critical[:2])}")

        # Deadline slippage penalty
        if project.deadline:
            dead_dt = None
            if isinstance(project.deadline, datetime):
                dead_dt = project.deadline if project.deadline.tzinfo else project.deadline.replace(tzinfo=timezone.utc)
            elif isinstance(project.deadline, str):
                try:
                    dead_dt = datetime.fromisoformat(project.deadline.replace("Z", "+00:00"))
                except Exception:
                    pass
            if dead_dt and dead_dt < now and len(open_tasks) > 0:
                deductions += 25.0
                signals.append(f"Project deadline passed on {dead_dt.strftime('%b %d, %Y')} with {len(open_tasks)} tasks still incomplete.")

        final_score = max(0, min(100, int(score - deductions)))

        if final_score >= 80:
            health_status = "HEALTHY"
        elif final_score >= 50:
            health_status = "AT_RISK"
        else:
            health_status = "CRITICAL"

        # Velocity Trend calculation (past 14 days vs prior 14 days)
        fourteen_days_ago = now - timedelta(days=14)
        twenty_eight_days_ago = now - timedelta(days=28)

        recent_completed = 0
        prior_completed = 0
        for t in completed_tasks:
            t_updated = t.updated_at if getattr(t, 'updated_at', None) else t.created_at
            if t_updated:
                t_dt = t_updated if t_updated.tzinfo else t_updated.replace(tzinfo=timezone.utc)
                if t_dt >= fourteen_days_ago:
                    recent_completed += 1
                elif t_dt >= twenty_eight_days_ago:
                    prior_completed += 1

        if recent_completed > prior_completed and recent_completed >= 2:
            velocity_trend = "INCREASING"
        elif recent_completed < prior_completed and prior_completed >= 2:
            velocity_trend = "DECLINING"
            signals.append("Completion velocity has declined compared to the previous sprint.")
        elif recent_completed > 0:
            velocity_trend = "STABLE"
        else:
            velocity_trend = "UNKNOWN"

        if not signals:
            signals.append("Project execution is on track with zero blocking risks.")

        # Completion Forecast
        forecast = {}
        if recent_completed >= 2 and len(open_tasks) > 0:
            tasks_per_day = recent_completed / 14.0
            days_needed = len(open_tasks) / tasks_per_day
            est_completion = now + timedelta(days=days_needed)
            forecast = {
                "status": "forecasted",
                "estimated_completion_date": est_completion.isoformat(),
                "estimated_days_remaining": round(days_needed, 1),
                "completion_range": f"{est_completion.strftime('%b %d')} - {(est_completion + timedelta(days=max(3, int(days_needed * 0.2)))).strftime('%b %d, %Y')}",
                "message": f"At current velocity ({round(tasks_per_day * 7, 1)} tasks/wk), completion estimated within {round(days_needed)} days."
            }
        else:
            forecast = {
                "status": "insufficient_data",
                "message": "More task completion history required to calculate a confident statistical forecast."
            }

        return {
            "project_id": project.id,
            "project_name": project.name,
            "status": project.status,
            "deadline": project.deadline,
            "health_score": final_score,
            "health_status": health_status,
            "total_tasks": total_tasks,
            "completed_tasks": len(completed_tasks),
            "overdue_tasks": len(overdue_tasks),
            "in_progress_tasks": len(in_progress_tasks),
            "completion_rate": round(completion_rate, 1),
            "velocity_trend": velocity_trend,
            "signals": signals,
            "forecast": forecast,
            "active_risks_count": len(active_risks),
            "milestones_total": len(milestones),
            "milestones_completed": len(completed_milestones),
        }

    @staticmethod
    def get_portfolio_health(db: Session, workspace_id: int) -> Dict[str, Any]:
        """Calculates portfolio-wide health assessment for all projects in a workspace."""
        projects = db.query(Project).filter(Project.workspace_id == workspace_id).all()
        project_healths = []
        healthy_count = 0
        at_risk_count = 0
        critical_count = 0
        insufficient_data_count = 0
        total_score = 0
        total_rate = 0.0

        for p in projects:
            health = EnterpriseAnalyticsService.calculate_project_health(db, p.id)
            if health:
                project_healths.append(health)
                status = health["health_status"]
                if status == "HEALTHY":
                    healthy_count += 1
                elif status == "AT_RISK":
                    at_risk_count += 1
                elif status == "CRITICAL":
                    critical_count += 1
                elif status == "INSUFFICIENT_DATA":
                    insufficient_data_count += 1
                total_score += health["health_score"]
                total_rate += health["completion_rate"]

        # Risk distribution across workspace
        active_risks = (
            db.query(ProjectRisk)
            .join(Project, Project.id == ProjectRisk.project_id)
            .filter(Project.workspace_id == workspace_id, ProjectRisk.status == "ACTIVE")
            .all()
        )
        risk_distribution = {"SCHEDULE": 0, "WORKLOAD": 0, "DEPENDENCY": 0, "EXECUTION": 0}
        for r in active_risks:
            if r.category in risk_distribution:
                risk_distribution[r.category] += 1

        count = len(project_healths)
        avg_health = round(total_score / count, 1) if count > 0 else 100.0
        avg_completion = round(total_rate / count, 1) if count > 0 else 0.0

        return {
            "workspace_id": workspace_id,
            "total_projects": count,
            "healthy_count": healthy_count,
            "at_risk_count": at_risk_count,
            "critical_count": critical_count,
            "insufficient_data_count": insufficient_data_count,
            "average_health_score": avg_health,
            "average_completion_rate": avg_completion,
            "risk_distribution": risk_distribution,
            "projects": project_healths,
        }

    @staticmethod
    def get_executive_summary(db: Session, workspace_id: int) -> Dict[str, Any]:
        """Calculates executive KPI roll-up metrics."""
        portfolio = EnterpriseAnalyticsService.get_portfolio_health(db, workspace_id)
        
        # Tasks in workspace
        tasks = (
            db.query(Task)
            .filter(Task.workspace_id == workspace_id)
            .all()
        )
        total_tasks = len(tasks)
        completed_tasks = [t for t in tasks if t.status in ("completed", "done")]
        
        # 30-day completed
        now = utc_now()
        thirty_days_ago = now - timedelta(days=30)
        completed_30d = 0
        for t in completed_tasks:
            t_dt = t.updated_at or t.created_at
            if t_dt:
                t_dt_tz = t_dt if t_dt.tzinfo else t_dt.replace(tzinfo=timezone.utc)
                if t_dt_tz >= thirty_days_ago:
                    completed_30d += 1

        # Overdue tasks
        overdue_count = 0
        open_tasks = [t for t in tasks if t.status not in ("completed", "done", "cancelled")]
        for t in open_tasks:
            if t.due_date:
                due_dt = None
                if isinstance(t.due_date, datetime):
                    due_dt = t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)
                elif isinstance(t.due_date, str):
                    try:
                        due_dt = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))
                    except Exception:
                        pass
                if due_dt and due_dt < now:
                    overdue_count += 1

        on_time_rate = 100.0
        if len(completed_tasks) + overdue_count > 0:
            on_time_rate = round((len(completed_tasks) / (len(completed_tasks) + overdue_count)) * 100.0, 1)

        # Active & Critical risks
        risks = (
            db.query(ProjectRisk)
            .join(Project, Project.id == ProjectRisk.project_id)
            .filter(Project.workspace_id == workspace_id, ProjectRisk.status == "ACTIVE")
            .all()
        )
        active_risks_count = len(risks)
        critical_risks_count = len([r for r in risks if r.severity == "CRITICAL"])

        # Workload saturation
        workload = EnterpriseAnalyticsService.get_team_workload(db, workspace_id)
        saturation_rate = workload.get("average_utilization_rate", 0.0)

        active_projects_count = len([p for p in portfolio["projects"] if p["status"] not in ("completed", "archived")])

        return {
            "workspace_id": workspace_id,
            "total_projects": portfolio["total_projects"],
            "active_projects": active_projects_count,
            "total_tasks": total_tasks,
            "completed_tasks_total": len(completed_tasks),
            "completed_tasks_30d": completed_30d,
            "overdue_tasks": overdue_count,
            "on_time_delivery_rate": on_time_rate,
            "active_risks_count": active_risks_count,
            "critical_risks_count": critical_risks_count,
            "portfolio_health_average": portfolio["average_health_score"],
            "workload_saturation_rate": saturation_rate,
        }

    @staticmethod
    def get_team_workload(db: Session, workspace_id: int) -> Dict[str, Any]:
        """Calculates workload capacity vs allocation across all workspace team members."""
        members = (
            db.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == workspace_id)
            .all()
        )

        member_workloads = []
        total_capacity = 0.0
        total_allocated = 0.0

        for m in members:
            user = db.query(User).filter(User.id == m.user_id).first()
            if not user:
                continue

            # Query capacity or fallback to 40.0 hours
            capacity_rec = (
                db.query(ResourceCapacity)
                .filter(ResourceCapacity.user_id == user.id, ResourceCapacity.workspace_id == workspace_id)
                .order_by(ResourceCapacity.created_at.desc())
                .first()
            )
            weekly_cap = capacity_rec.weekly_hours_capacity if capacity_rec else 40.0

            # Count tasks assigned to this user in this workspace
            active_tasks = (
                db.query(Task)
                .filter(
                    Task.workspace_id == workspace_id,
                    (Task.assignee_id == user.id) | (Task.user_id == user.id),
                    Task.status.notin_(["completed", "done", "cancelled"])
                )
                .all()
            )
            completed_tasks = (
                db.query(Task)
                .filter(
                    Task.workspace_id == workspace_id,
                    (Task.assignee_id == user.id) | (Task.user_id == user.id),
                    Task.status.in_(["completed", "done"])
                )
                .count()
            )

            # Standard 4 hours estimated per active task
            allocated_hours = len(active_tasks) * 4.0
            utilization = round((allocated_hours / weekly_cap) * 100.0, 1) if weekly_cap > 0 else 0.0

            if utilization > 100.0:
                status = "OVERLOADED"
            elif utilization < 40.0:
                status = "UNDERUTILIZED"
            else:
                status = "OPTIMAL"

            total_capacity += weekly_cap
            total_allocated += allocated_hours

            member_workloads.append({
                "user_id": user.id,
                "user_name": user.name or user.email,
                "user_email": user.email,
                "assigned_tasks_count": len(active_tasks),
                "completed_tasks_count": completed_tasks,
                "weekly_capacity_hours": weekly_cap,
                "estimated_allocated_hours": allocated_hours,
                "utilization_rate": utilization,
                "status": status,
            })

        avg_utilization = (
            round((total_allocated / total_capacity) * 100.0, 1) if total_capacity > 0 else 0.0
        )

        return {
            "workspace_id": workspace_id,
            "total_members": len(member_workloads),
            "total_active_tasks": sum(m["assigned_tasks_count"] for m in member_workloads),
            "total_capacity_hours": total_capacity,
            "total_allocated_hours": total_allocated,
            "average_utilization_rate": avg_utilization,
            "members": member_workloads,
        }

    @staticmethod
    def generate_report(db: Session, user_id: int, workspace_id: int, title: str, report_type: str, parameters: Optional[Dict[str, Any]] = None, fmt: str = "JSON") -> AnalyticsReport:
        """Generates an executive analytics report and stores it."""
        summary = {}
        if report_type == "EXECUTIVE_KPI":
            summary = EnterpriseAnalyticsService.get_executive_summary(db, workspace_id)
        elif report_type == "PORTFOLIO_HEALTH":
            summary = EnterpriseAnalyticsService.get_portfolio_health(db, workspace_id)
        elif report_type == "TEAM_WORKLOAD":
            summary = EnterpriseAnalyticsService.get_team_workload(db, workspace_id)
        elif report_type == "RISK_ASSESSMENT":
            risks = (
                db.query(ProjectRisk)
                .join(Project, Project.id == ProjectRisk.project_id)
                .filter(Project.workspace_id == workspace_id)
                .all()
            )
            summary = {
                "total_risks": len(risks),
                "active_risks": len([r for r in risks if r.status == "ACTIVE"]),
                "critical_risks": len([r for r in risks if r.severity == "CRITICAL"]),
                "risks": [
                    {
                        "id": r.id,
                        "project_id": r.project_id,
                        "title": r.title,
                        "category": r.category,
                        "severity": r.severity,
                        "status": r.status,
                        "mitigation_plan": r.mitigation_plan,
                    }
                    for r in risks
                ]
            }

        report = AnalyticsReport(
            user_id=user_id,
            workspace_id=workspace_id,
            title=title,
            report_type=report_type,
            parameters_json=json.dumps(parameters or {}),
            summary_json=json.dumps(summary),
            format=fmt,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def export_report_csv(report: AnalyticsReport) -> str:
        """Converts stored report data into a clean CSV string."""
        data = json.loads(report.summary_json)
        output = io.StringIO()
        writer = csv.writer(output)

        if report.report_type == "EXECUTIVE_KPI":
            writer.writerow(["Metric", "Value"])
            for k, v in data.items():
                writer.writerow([k.replace("_", " ").title(), v])
        elif report.report_type == "PORTFOLIO_HEALTH":
            writer.writerow(["Project ID", "Project Name", "Health Score", "Health Status", "Total Tasks", "Completed Tasks", "Overdue Tasks", "Completion Rate (%)"])
            for p in data.get("projects", []):
                writer.writerow([
                    p.get("project_id"),
                    p.get("project_name"),
                    p.get("health_score"),
                    p.get("health_status"),
                    p.get("total_tasks"),
                    p.get("completed_tasks"),
                    p.get("overdue_tasks"),
                    p.get("completion_rate"),
                ])
        elif report.report_type == "TEAM_WORKLOAD":
            writer.writerow(["User ID", "User Name", "Email", "Assigned Tasks", "Completed Tasks", "Weekly Capacity (hrs)", "Allocated (hrs)", "Utilization (%)", "Status"])
            for m in data.get("members", []):
                writer.writerow([
                    m.get("user_id"),
                    m.get("user_name"),
                    m.get("user_email"),
                    m.get("assigned_tasks_count"),
                    m.get("completed_tasks_count"),
                    m.get("weekly_capacity_hours"),
                    m.get("estimated_allocated_hours"),
                    m.get("utilization_rate"),
                    m.get("status"),
                ])
        else:
            writer.writerow(["Key", "Value"])
            for k, v in data.items():
                writer.writerow([k, str(v)])

        return output.getvalue()
