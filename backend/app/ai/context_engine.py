from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.collaboration import Workspace, WorkspaceMember, Activity
from app.models.ai_agent import AIPersistentPreference
from app.services.analytics_service import analytics_service

class ContextRetrievalEngine:
    """
    Retrieves authorized FocusBoard application context strictly scoped
    to the user's permissions and tenant boundary.
    """

    @staticmethod
    def get_accessible_workspaces(db: Session, user: User) -> List[int]:
        ws_ids = set()
        owned = db.query(Workspace.id).filter(Workspace.owner_id == user.id, Workspace.is_active == True).all()
        for w in owned:
            ws_ids.add(w[0])

        memberships = db.query(WorkspaceMember.workspace_id).filter(WorkspaceMember.user_id == user.id).all()
        for m in memberships:
            ws_ids.add(m[0])

        return list(ws_ids)

    def assemble_context(
        self,
        db: Session,
        current_user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[str] = None,
        max_tasks: int = 15,
    ) -> Dict[str, Any]:
        """Fetch real, validated contextual data from transactional records."""
        accessible_ws = self.get_accessible_workspaces(db, current_user)
        if workspace_id and workspace_id not in accessible_ws:
            workspace_id = None  # Block cross-tenant access

        today_str = date.today().strftime("%Y-%m-%d")

        # 1. Fetch user persistent preferences
        pref = db.query(AIPersistentPreference).filter(AIPersistentPreference.user_id == current_user.id).first()
        pref_data = {
            "planning_style": pref.planning_style if pref else "balanced",
            "preferred_work_hours": pref.preferred_work_hours if pref else 6,
            "summary_format": pref.summary_format if pref else "bullet_points",
            "prioritization_approach": pref.prioritization_approach if pref else "deadline_first",
        }

        # 2. Fetch accessible tasks
        task_query = db.query(Task).filter(Task.is_deleted == False)
        if workspace_id:
            task_query = task_query.filter(Task.workspace_id == workspace_id)
        elif project_id:
            # Verify project accessibility
            proj = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
            if proj and proj.workspace_id in accessible_ws:
                task_query = task_query.filter(Task.project_id == project_id)
            else:
                task_query = task_query.filter(or_(Task.user_id == current_user.id, Task.assignee_id == current_user.id))
        else:
            task_query = task_query.filter(
                or_(
                    Task.user_id == current_user.id,
                    Task.assignee_id == current_user.id,
                    and_(Task.workspace_id.in_(accessible_ws), Task.workspace_id.isnot(None)) if accessible_ws else False
                )
            )

        all_tasks = task_query.all()
        incomplete_tasks = [t for t in all_tasks if (t.status or "").lower() != "completed"]
        completed_tasks = [t for t in all_tasks if (t.status or "").lower() == "completed"]

        overdue_tasks = [t for t in incomplete_tasks if t.due_date and t.due_date < today_str]
        due_today_tasks = [t for t in incomplete_tasks if t.due_date and t.due_date == today_str]
        high_priority_tasks = [t for t in incomplete_tasks if (t.priority or "").lower() in ("high", "critical")]

        # Clean tasks representation (protect against prompt injection)
        def clean_task(t: Task) -> Dict[str, Any]:
            # Sanitize control characters
            title = (t.title or "").replace("\r", " ").replace("\n", " ")[:120]
            desc = (t.description or "").replace("\r", " ").replace("\n", " ")[:200]
            return {
                "id": t.id,
                "title": title,
                "description": desc,
                "status": t.status or "Todo",
                "priority": t.priority or "Medium",
                "category": t.category or "General",
                "due_date": t.due_date,
                "project_id": t.project_id,
            }

        # 3. Project context if requested
        project_data = None
        if project_id:
            proj = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
            if proj and (not proj.workspace_id or proj.workspace_id in accessible_ws):
                p_tasks = [t for t in all_tasks if t.project_id == proj.id]
                p_comp = sum(1 for t in p_tasks if (t.status or "").lower() == "completed")
                p_overdue = sum(1 for t in p_tasks if (t.status or "").lower() != "completed" and t.due_date and t.due_date < today_str)
                project_data = {
                    "id": proj.id,
                    "name": proj.name,
                    "status": proj.status,
                    "priority": proj.priority,
                    "health": proj.health,
                    "total_tasks": len(p_tasks),
                    "completed_tasks": p_comp,
                    "overdue_tasks": p_overdue,
                    "completion_rate": round((p_comp / len(p_tasks)) * 100, 1) if p_tasks else 0.0,
                }

        # 4. Analytics Summary
        summary = analytics_service.get_dashboard_summary(db, current_user, workspace_id=workspace_id, project_id=project_id)

        # 5. Recent Activity
        activities = (
            db.query(Activity)
            .filter(Activity.actor_id == current_user.id)
            .order_by(Activity.created_at.desc())
            .limit(5)
            .all()
        )
        recent_activity_events = [
            f"{a.event_type}: {a.description}" for a in activities
        ]

        return {
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "preferences": pref_data,
            },
            "metrics": {
                "total_tasks": summary.total,
                "completed": summary.completed,
                "in_progress": summary.in_progress,
                "todo": summary.todo,
                "overdue": summary.overdue,
                "due_today": summary.due_today,
                "completion_rate": summary.completion_rate,
                "weekly_velocity": getattr(summary, "weekly_velocity", 0),
            },
            "tasks_summary": {
                "active_count": len(incomplete_tasks),
                "overdue_count": len(overdue_tasks),
                "due_today_count": len(due_today_tasks),
                "high_priority_count": len(high_priority_tasks),
                "overdue_sample": [clean_task(t) for t in overdue_tasks[:5]],
                "due_today_sample": [clean_task(t) for t in due_today_tasks[:5]],
                "high_priority_sample": [clean_task(t) for t in high_priority_tasks[:5]],
                "recent_active_tasks": [clean_task(t) for t in incomplete_tasks[:max_tasks]],
            },
            "project": project_data,
            "recent_activity": recent_activity_events,
        }

    def format_context_string(self, context_dict: Dict[str, Any]) -> str:
        """Format retrieved application context into clean, prompt-delimited text."""
        u = context_dict["user"]
        m = context_dict["metrics"]
        ts = context_dict["tasks_summary"]

        lines = [
            "<focusboard_authorized_context>",
            f"User: {u['name']} (ID: {u['id']})",
            f"Work Style: {u['preferences']['planning_style']}, Preferred Hours: {u['preferences']['preferred_work_hours']}h/day",
            "",
            "=== METRICS SUMMARY ===",
            f"Total Tasks: {m['total_tasks']} | Completed: {m['completed']} ({m['completion_rate']}%) | In Progress: {m['in_progress']} | Todo: {m['todo']}",
            f"Overdue: {m['overdue']} | Due Today: {m['due_today']}",
            "",
            "=== ACTIVE WORKLOAD ===",
        ]

        if ts["overdue_sample"]:
            lines.append("Overdue Tasks (URGENT):")
            for t in ts["overdue_sample"]:
                lines.append(f"  - [{t['id']}] {t['title']} (Due: {t['due_date']}, Priority: {t['priority']})")

        if ts["due_today_sample"]:
            lines.append("Due Today Tasks:")
            for t in ts["due_today_sample"]:
                lines.append(f"  - [{t['id']}] {t['title']} (Priority: {t['priority']})")

        if ts["high_priority_sample"]:
            lines.append("High Priority Backlog:")
            for t in ts["high_priority_sample"]:
                lines.append(f"  - [{t['id']}] {t['title']} (Status: {t['status']}, Due: {t['due_date'] or 'None'})")

        if context_dict.get("project"):
            p = context_dict["project"]
            lines.extend([
                "",
                "=== ACTIVE PROJECT ===",
                f"Project: {p['name']} (ID: {p['id']}, Health: {p['health']}, Status: {p['status']})",
                f"Tasks: {p['total_tasks']} total, {p['completed_tasks']} completed ({p['completion_rate']}%), {p['overdue_tasks']} overdue",
            ])

        if context_dict.get("recent_activity"):
            lines.extend([
                "",
                "=== RECENT ACTIVITY ===",
                *[f"  - {act}" for act in context_dict["recent_activity"][:4]],
            ])

        lines.append("</focusboard_authorized_context>")
        return "\n".join(lines)

context_engine = ContextRetrievalEngine()
