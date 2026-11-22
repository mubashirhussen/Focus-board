import re
import uuid
import json
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.task import Task
from app.models.collaboration import Project, Workspace
from app.models.support import KnowledgeBaseArticle
from app.services import support_service

class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        handler: Callable,
        requires_approval: bool = False,
        permission_required: str = "Member",
    ):
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
        self.handler = handler
        self.requires_approval = requires_approval
        self.permission_required = permission_required

    def execute(self, db: Session, user_id: int, workspace_id: Optional[int], args: Dict[str, Any]) -> Dict[str, Any]:
        return self.handler(db=db, user_id=user_id, workspace_id=workspace_id, **args)

# Tool Implementations
def tool_list_tasks(db: Session, user_id: int, workspace_id: Optional[int] = None, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    query = db.query(Task).filter(Task.user_id == user_id)
    if workspace_id:
        query = query.filter(Task.workspace_id == workspace_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    return {
        "count": len(tasks),
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date,
                "project_id": t.project_id,
            }
            for t in tasks
        ],
    }

def tool_get_task(db: Session, user_id: int, workspace_id: Optional[int], task_id: str) -> Dict[str, Any]:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return {"error": f"Task {task_id} not found or access denied"}
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }

def tool_search_tasks(db: Session, user_id: int, workspace_id: Optional[int], query: str) -> Dict[str, Any]:
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id, or_(Task.title.ilike(f"%{query}%"), Task.description.ilike(f"%{query}%")))
        .limit(10)
        .all()
    )
    return {
        "query": query,
        "matches": [
            {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority}
            for t in tasks
        ],
    }

def tool_create_task(db: Session, user_id: int, workspace_id: Optional[int], title: str, description: Optional[str] = None, priority: str = "medium", due_date: Optional[str] = None, project_id: Optional[int] = None) -> Dict[str, Any]:
    task_id = f"task-{int(datetime.now(timezone.utc).timestamp()*1000)}-{uuid.uuid4().hex[:6]}"
    task = Task(
        id=task_id,
        title=title,
        description=description or "",
        priority=priority.capitalize() if priority else "Medium",
        status="Todo",
        due_date=due_date or "",
        user_id=user_id,
        workspace_id=workspace_id,
        project_id=project_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
    }

def tool_update_task(db: Session, user_id: int, workspace_id: Optional[int], task_id: str, title: Optional[str] = None, status: Optional[str] = None, priority: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return {"error": f"Task {task_id} not found or access denied"}

    if title:
        task.title = title
    if status:
        task.status = status.lower()
    if priority:
        task.priority = priority.lower()
    if due_date:
        try:
            task.due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except Exception:
            pass

    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "updated": True,
    }

def tool_delete_task(db: Session, user_id: int, workspace_id: Optional[int], task_id: str) -> Dict[str, Any]:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        return {"error": f"Task {task_id} not found or access denied"}
    title = task.title
    db.delete(task)
    db.commit()
    return {"id": task_id, "title": title, "deleted": True}

def tool_list_projects(db: Session, user_id: int, workspace_id: Optional[int] = None) -> Dict[str, Any]:
    query = db.query(Project)
    if workspace_id:
        query = query.filter(Project.workspace_id == workspace_id)
    projects = query.limit(20).all()
    return {
        "count": len(projects),
        "projects": [{"id": p.id, "name": p.name, "description": p.description} for p in projects],
    }

def tool_create_project(db: Session, user_id: int, workspace_id: Optional[int], name: str, description: Optional[str] = None, color: Optional[str] = "#4f46e5") -> Dict[str, Any]:
    ws_id = workspace_id
    if not ws_id:
        ws = db.query(Workspace).filter(Workspace.owner_id == user_id).first()
        if not ws:
            ws = Workspace(name="Personal Workspace", owner_id=user_id)
            db.add(ws)
            db.commit()
            db.refresh(ws)
        ws_id = ws.id

    project = Project(
        name=name,
        description=description or "",
        workspace_id=ws_id,
        created_by=user_id,
        status="ACTIVE",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "created": True}

def tool_get_productivity_analytics(db: Session, user_id: int, workspace_id: Optional[int] = None) -> Dict[str, Any]:
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.status == "completed"])
    now = datetime.now(timezone.utc)
    overdue = len([t for t in tasks if t.status != "completed" and t.due_date and t.due_date.replace(tzinfo=timezone.utc if t.due_date.tzinfo is None else t.due_date.tzinfo) < now])
    rate = round((completed / total * 100), 1) if total > 0 else 0.0

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "overdue_tasks": overdue,
        "completion_rate_pct": rate,
    }

def tool_create_daily_plan(db: Session, user_id: int, workspace_id: Optional[int] = None, available_hours: int = 6) -> Dict[str, Any]:
    tasks = db.query(Task).filter(Task.user_id == user_id, Task.status != "completed").all()
    # Prioritize high priority and overdue first
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (0 if t.priority == "high" else 1 if t.priority == "medium" else 2)
    )
    allocated = sorted_tasks[:min(len(sorted_tasks), 4)]
    return {
        "target_hours": available_hours,
        "recommended_tasks": [
            {"id": t.id, "title": t.title, "priority": t.priority, "suggested_duration_mins": 45}
            for t in allocated
        ],
    }

def tool_search_knowledge_base(db: Session, user_id: int, workspace_id: Optional[int], query: str) -> Dict[str, Any]:
    support_service.seed_default_knowledge_base(db)
    articles = (
        db.query(KnowledgeBaseArticle)
        .filter(
            KnowledgeBaseArticle.status == "PUBLISHED",
            or_(KnowledgeBaseArticle.title.ilike(f"%{query}%"), KnowledgeBaseArticle.content.ilike(f"%{query}%")),
        )
        .limit(3)
        .all()
    )
    return {
        "query": query,
        "results": [
            {"id": a.id, "title": a.title, "content_snippet": a.content[:200]}
            for a in articles
        ],
    }

def tool_create_support_ticket(db: Session, user_id: int, workspace_id: Optional[int], title: str, description: str, priority: str = "NORMAL", category: str = "technical_issue") -> Dict[str, Any]:
    ticket = support_service.create_support_ticket(
        db,
        user_id=user_id,
        title=title,
        description=description,
        category=category,
        priority=priority,
        workspace_id=workspace_id,
    )
    return {
        "ticket_id": ticket.id,
        "title": ticket.title,
        "priority": ticket.priority,
        "sla_deadline": ticket.sla_deadline.isoformat() if ticket.sla_deadline else None,
        "status": ticket.status,
    }

# Tool Registry
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "list_tasks": ToolDefinition(
        name="list_tasks",
        description="Retrieve user's active tasks filtered by status or priority.",
        parameters_schema={"type": "object", "properties": {"status": {"type": "string"}, "priority": {"type": "string"}, "limit": {"type": "integer"}}},
        handler=tool_list_tasks,
        requires_approval=False,
    ),
    "get_task": ToolDefinition(
        name="get_task",
        description="Get full task details by task ID.",
        parameters_schema={"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]},
        handler=tool_get_task,
        requires_approval=False,
    ),
    "search_tasks": ToolDefinition(
        name="search_tasks",
        description="Search user tasks matching a keyword.",
        parameters_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        handler=tool_search_tasks,
        requires_approval=False,
    ),
    "create_task": ToolDefinition(
        name="create_task",
        description="Create a new task in user's workspace.",
        parameters_schema={"type": "object", "properties": {"title": {"type": "string"}, "priority": {"type": "string"}, "due_date": {"type": "string"}, "description": {"type": "string"}}, "required": ["title"]},
        handler=tool_create_task,
        requires_approval=False,
    ),
    "update_task": ToolDefinition(
        name="update_task",
        description="Update an existing task status, priority, title, or deadline.",
        parameters_schema={"type": "object", "properties": {"task_id": {"type": "string"}, "status": {"type": "string"}, "priority": {"type": "string"}, "title": {"type": "string"}}, "required": ["task_id"]},
        handler=tool_update_task,
        requires_approval=False,
    ),
    "delete_task": ToolDefinition(
        name="delete_task",
        description="Permanently delete a task. Sensitive action requiring user approval.",
        parameters_schema={"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]},
        handler=tool_delete_task,
        requires_approval=True,  # SENSITIVE!
    ),
    "list_projects": ToolDefinition(
        name="list_projects",
        description="List projects in current workspace.",
        parameters_schema={"type": "object", "properties": {}},
        handler=tool_list_projects,
        requires_approval=False,
    ),
    "create_project": ToolDefinition(
        name="create_project",
        description="Create a new project container.",
        parameters_schema={"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}}, "required": ["name"]},
        handler=tool_create_project,
        requires_approval=False,
    ),
    "get_productivity_analytics": ToolDefinition(
        name="get_productivity_analytics",
        description="Get real task completion ratios and overdue task metrics.",
        parameters_schema={"type": "object", "properties": {}},
        handler=tool_get_productivity_analytics,
        requires_approval=False,
    ),
    "create_daily_plan": ToolDefinition(
        name="create_daily_plan",
        description="Generate an optimal daily work schedule based on current workload.",
        parameters_schema={"type": "object", "properties": {"available_hours": {"type": "integer"}}},
        handler=tool_create_daily_plan,
        requires_approval=False,
    ),
    "search_knowledge_base": ToolDefinition(
        name="search_knowledge_base",
        description="Search self-service documentation and knowledge base guides.",
        parameters_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        handler=tool_search_knowledge_base,
        requires_approval=False,
    ),
    "create_support_ticket": ToolDefinition(
        name="create_support_ticket",
        description="Open an enterprise customer support ticket with SLA guarantee.",
        parameters_schema={"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string"}}, "required": ["title", "description"]},
        handler=tool_create_support_ticket,
        requires_approval=False,
    ),
}
