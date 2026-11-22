import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc

from app.models.collaboration import Activity, Workspace, WorkspaceMember
from app.models.organization import OrganizationMember
from app.models.project import Project, ProjectMember
from app.models.team import Team, TeamMember
from app.models.task import Task
from app.models.user import User

class ActivityService:
    @staticmethod
    def record_activity(
        db: Session,
        actor_id: int,
        event_type: str,
        description: str,
        entity_type: Optional[str] = "TASK",
        entity_id: Optional[str] = None,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[str] = None,
        parent_entity_id: Optional[str] = None,
        target_user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Activity:
        """Centralized helper to persist activity records across collaboration domains."""
        # Derive task_id / project_id if not explicitly passed
        eff_task_id = task_id or (entity_id if entity_type == "TASK" else None)
        eff_project_id = project_id or (int(entity_id) if entity_type == "PROJECT" and str(entity_id).isdigit() else None)

        metadata_str = json.dumps(metadata) if metadata else None

        activity = Activity(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=eff_project_id,
            task_id=eff_task_id,
            actor_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            parent_entity_id=str(parent_entity_id) if parent_entity_id is not None else None,
            target_user_id=target_user_id,
            description=description,
            metadata_json=metadata_str,
            created_at=datetime.utcnow(),
        )
        db.add(activity)
        try:
            db.commit()
            db.refresh(activity)
        except Exception:
            db.rollback()
            raise
        return activity

    @staticmethod
    def get_feed(
        db: Session,
        current_user: User,
        organization_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        event_type: Optional[str] = None,
        actor_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Activity]:
        """
        Query activity feed enforcing multi-tenant isolation.
        Returns activities belonging to authorized entities.
        """
        query = db.query(Activity).options(joinedload(Activity.actor))

        # Check tenant authorization if specific filters passed
        if task_id or (entity_type == "TASK" and entity_id):
            tid = task_id or entity_id
            task = db.query(Task).filter(Task.id == tid).first()
            if not task:
                raise ValueError("Task not found")
            query = query.filter(
                or_(
                    Activity.task_id == tid,
                    and_(Activity.entity_type == "TASK", Activity.entity_id == str(tid))
                )
            )
        elif project_id or (entity_type == "PROJECT" and entity_id):
            pid = project_id or int(entity_id)
            project = db.query(Project).filter(Project.id == pid, Project.is_deleted == False).first()
            if not project:
                raise ValueError("Project not found")
            query = query.filter(
                or_(
                    Activity.project_id == pid,
                    and_(Activity.entity_type == "PROJECT", Activity.entity_id == str(pid))
                )
            )
        elif workspace_id or (entity_type == "WORKSPACE" and entity_id):
            wid = workspace_id or int(entity_id)
            wm = db.query(WorkspaceMember).filter(
                WorkspaceMember.workspace_id == wid,
                WorkspaceMember.user_id == current_user.id
            ).first()
            ws = db.query(Workspace).filter(Workspace.id == wid).first()
            if not ws:
                raise ValueError("Workspace not found")
            if ws.owner_id != current_user.id and not wm:
                raise ValueError("Workspace not found")
            query = query.filter(
                or_(
                    Activity.workspace_id == wid,
                    and_(Activity.entity_type == "WORKSPACE", Activity.entity_id == str(wid))
                )
            )
        elif organization_id or (entity_type == "ORGANIZATION" and entity_id):
            oid = organization_id or int(entity_id)
            om = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == oid,
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_active == True
            ).first()
            if not om:
                raise ValueError("Organization not found")
            query = query.filter(Activity.organization_id == oid)
        else:
            # Default feed: user's organizations and workspaces
            user_org_ids = [
                m.organization_id for m in db.query(OrganizationMember.organization_id).filter(
                    OrganizationMember.user_id == current_user.id,
                    OrganizationMember.is_active == True
                ).all()
            ]
            user_ws_ids = [
                m.workspace_id for m in db.query(WorkspaceMember.workspace_id).filter(
                    WorkspaceMember.user_id == current_user.id
                ).all()
            ]
            query = query.filter(
                or_(
                    Activity.actor_id == current_user.id,
                    Activity.organization_id.in_(user_org_ids),
                    Activity.workspace_id.in_(user_ws_ids)
                )
            )

        if entity_type and not (entity_type in ["TASK", "PROJECT", "WORKSPACE", "ORGANIZATION"] and entity_id):
            query = query.filter(Activity.entity_type == entity_type.upper())
        if entity_id and not (entity_type in ["TASK", "PROJECT", "WORKSPACE", "ORGANIZATION"]):
            query = query.filter(Activity.entity_id == str(entity_id))
        if event_type:
            query = query.filter(Activity.event_type == event_type)
        if actor_id:
            query = query.filter(Activity.actor_id == actor_id)
        if from_date:
            from_naive = from_date.replace(tzinfo=None) if from_date.tzinfo else from_date
            query = query.filter(Activity.created_at >= from_naive)
        if to_date:
            to_naive = to_date.replace(tzinfo=None) if to_date.tzinfo else to_date
            query = query.filter(Activity.created_at <= to_naive)

        return query.order_by(desc(Activity.created_at)).offset(skip).limit(limit).all()

activity_service = ActivityService()
