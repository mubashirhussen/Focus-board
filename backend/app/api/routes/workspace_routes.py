from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.collaboration import (
    Workspace,
    WorkspaceMember,
    WorkspaceInvitation,
    Project,
    TaskComment,
    Activity,
)
from app.schemas.collaboration import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceMemberResponse,
    InvitationCreate,
    InvitationResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    CommentCreate,
    CommentResponse,
    ActivityResponse,
    AssignTaskRequest,
    TeamAnalyticsResponse,
)
from app.schemas.task import TaskCreate, TaskResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/workspaces", tags=["Workspaces & Team Collaboration"])

def verify_membership(db: Session, workspace_id: int, user_id: int, allowed_roles: Optional[List[str]] = None) -> WorkspaceMember:
    """Helper to verify user membership and role permissions within a workspace."""
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this workspace."
        )

    if allowed_roles and member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Action requires one of roles: {', '.join(allowed_roles)}. Your role is {member.role}."
        )

    return member

def log_activity(db: Session, workspace_id: int, actor_id: int, event_type: str, description: str, project_id: Optional[int] = None, task_id: Optional[str] = None):
    """Helper to record an activity event in the workspace audit feed."""
    activity = Activity(
        workspace_id=workspace_id,
        actor_id=actor_id,
        event_type=event_type,
        description=description,
        project_id=project_id,
        task_id=task_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(activity)
    db.commit()

# --- Workspace Management ---

@router.get("", response_model=List[WorkspaceResponse])
def get_user_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all workspaces that the user belongs to."""
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).all()
    workspace_ids = [m.workspace_id for m in memberships]
    workspaces = db.query(Workspace).filter(Workspace.id.in_(workspace_ids)).all()
    return workspaces

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    ws_in: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new team workspace and designate creator as OWNER."""
    now = datetime.now(timezone.utc)
    ws = Workspace(
        name=ws_in.name.strip(),
        description=ws_in.description.strip() if ws_in.description else "",
        owner_id=current_user.id,
        created_at=now,
        updated_at=now
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)

    # Add owner membership
    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=current_user.id,
        role="OWNER",
        joined_at=now
    )
    db.add(member)
    db.commit()

    log_activity(db, ws.id, current_user.id, "WORKSPACE_CREATED", f"Workspace '{ws.name}' was created.")
    return ws

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace_details(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workspace details (requires membership)."""
    verify_membership(db, workspace_id, current_user.id)
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return ws

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: int,
    ws_in: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update workspace details (OWNER or ADMIN)."""
    verify_membership(db, workspace_id, current_user.id, ["OWNER", "ADMIN"])
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    if ws_in.name is not None:
        ws.name = ws_in.name.strip()
    if ws_in.description is not None:
        ws.description = ws_in.description.strip()
    ws.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ws)
    return ws

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a workspace permanently (OWNER only)."""
    verify_membership(db, workspace_id, current_user.id, ["OWNER"])
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    db.delete(ws)
    db.commit()
    return None

# --- Members & Invitations ---

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
def get_workspace_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all members of a workspace."""
    verify_membership(db, workspace_id, current_user.id)
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).all()
    return members

@router.post("/{workspace_id}/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    workspace_id: int,
    inv_in: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invite a user by email to join the workspace (OWNER or ADMIN)."""
    verify_membership(db, workspace_id, current_user.id, ["OWNER", "ADMIN"])
    
    # Check if already a member
    existing_user = db.query(User).filter(User.email == inv_in.email.lower().strip()).first()
    if existing_user:
        already_member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == existing_user.id
        ).first()
        if already_member:
            raise HTTPException(status_code=400, detail="User is already a member of this workspace.")

    now = datetime.now(timezone.utc)
    token = uuid.uuid4().hex
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        inviter_id=current_user.id,
        invitee_email=inv_in.email.lower().strip(),
        token=token,
        role=inv_in.role or "MEMBER",
        status="PENDING",
        expires_at=now + timedelta(days=7),
        created_at=now
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    log_activity(db, workspace_id, current_user.id, "MEMBER_INVITED", f"Invited {invitation.invitee_email} as {invitation.role}.")
    return invitation

@router.post("/invitations/{token}/accept", status_code=status.HTTP_200_OK)
def accept_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a workspace invitation using its secure token."""
    now = datetime.now(timezone.utc)
    inv = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.token == token,
        WorkspaceInvitation.status == "PENDING"
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found or already accepted.")
    
    expires_at = inv.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise HTTPException(status_code=400, detail="Invitation has expired.")

    # Check if user already joined
    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == inv.workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not existing:
        member = WorkspaceMember(
            workspace_id=inv.workspace_id,
            user_id=current_user.id,
            role=inv.role,
            joined_at=now
        )
        db.add(member)

    inv.status = "ACCEPTED"
    db.commit()

    log_activity(db, inv.workspace_id, current_user.id, "MEMBER_JOINED", f"{current_user.name} joined the workspace.")
    return {"message": "Successfully joined workspace.", "workspace_id": inv.workspace_id}

# --- Shared Projects ---

@router.get("/{workspace_id}/projects", response_model=List[ProjectResponse])
def get_projects(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects in the workspace."""
    verify_membership(db, workspace_id, current_user.id)
    return db.query(Project).filter(Project.workspace_id == workspace_id).all()

@router.post("/{workspace_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    workspace_id: int,
    proj_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project in the workspace (OWNER or ADMIN)."""
    verify_membership(db, workspace_id, current_user.id, ["OWNER", "ADMIN"])
    now = datetime.now(timezone.utc)
    project = Project(
        workspace_id=workspace_id,
        name=proj_in.name.strip(),
        description=proj_in.description.strip() if proj_in.description else "",
        deadline=proj_in.deadline or "",
        status="ACTIVE",
        created_by=current_user.id,
        created_at=now,
        updated_at=now
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    log_activity(db, workspace_id, current_user.id, "PROJECT_CREATED", f"Project '{project.name}' was created.", project_id=project.id)
    return project

# --- Shared Tasks & Task Assignment ---

@router.get("/{workspace_id}/tasks", response_model=List[TaskResponse])
def get_workspace_tasks(
    workspace_id: int,
    project_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve shared tasks belonging to this workspace."""
    verify_membership(db, workspace_id, current_user.id)
    query = db.query(Task).filter(Task.workspace_id == workspace_id)

    if project_id:
        query = query.filter(Task.project_id == project_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)

    return query.order_by(Task.created_at.desc()).all()

@router.post("/{workspace_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_workspace_task(
    workspace_id: int,
    task_in: TaskCreate,
    project_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a shared task within the workspace."""
    verify_membership(db, workspace_id, current_user.id)
    
    if assignee_id:
        verify_membership(db, workspace_id, assignee_id)

    task_id = task_in.id or f"task-{int(datetime.now(timezone.utc).timestamp()*1000)}-{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone.utc)

    task = Task(
        id=task_id,
        title=task_in.title.strip(),
        description=task_in.description.strip() if task_in.description else "",
        category=task_in.category or "Design",
        status=task_in.status or "Todo",
        priority=task_in.priority or "Medium",
        due_date=task_in.due_date or "",
        user_id=current_user.id,
        workspace_id=workspace_id,
        project_id=project_id,
        assignee_id=assignee_id,
        created_at=now,
        updated_at=now
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    log_activity(db, workspace_id, current_user.id, "TASK_CREATED", f"Task '{task.title}' was added.", project_id=project_id, task_id=task.id)
    return task

@router.patch("/{workspace_id}/tasks/{task_id}/assign", response_model=TaskResponse)
def assign_task(
    workspace_id: int,
    task_id: str,
    req: AssignTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign or reassign a workspace task to a verified member."""
    verify_membership(db, workspace_id, current_user.id)
    task = db.query(Task).filter(Task.id == task_id, Task.workspace_id == workspace_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in this workspace.")

    if req.assignee_id:
        assignee_member = verify_membership(db, workspace_id, req.assignee_id)
        task.assignee_id = req.assignee_id
        assignee_user = db.query(User).filter(User.id == req.assignee_id).first()
        assignee_name = assignee_user.name if assignee_user else f"User {req.assignee_id}"
        log_activity(db, workspace_id, current_user.id, "TASK_ASSIGNED", f"Assigned '{task.title}' to {assignee_name}.", task_id=task.id)
    else:
        task.assignee_id = None
        log_activity(db, workspace_id, current_user.id, "TASK_UNASSIGNED", f"Unassigned '{task.title}'.", task_id=task.id)

    if req.project_id is not None:
        task.project_id = req.project_id

    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task

# --- Task Comments ---

@router.get("/{workspace_id}/tasks/{task_id}/comments", response_model=List[CommentResponse])
def get_task_comments(
    workspace_id: int,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve comments for a workspace task."""
    verify_membership(db, workspace_id, current_user.id)
    comments = db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at.asc()).all()
    return comments

@router.post("/{workspace_id}/tasks/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_task_comment(
    workspace_id: int,
    task_id: str,
    comm_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Post a comment on a workspace task."""
    verify_membership(db, workspace_id, current_user.id)
    task = db.query(Task).filter(Task.id == task_id, Task.workspace_id == workspace_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in this workspace.")

    now = datetime.now(timezone.utc)
    comment = TaskComment(
        task_id=task_id,
        author_id=current_user.id,
        content=comm_in.content.strip(),
        created_at=now,
        updated_at=now
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    log_activity(db, workspace_id, current_user.id, "COMMENT_ADDED", f"{current_user.name} commented on '{task.title}'.", task_id=task.id)
    return comment

# --- Activity Feed & Team Analytics ---

@router.get("/{workspace_id}/activities", response_model=List[ActivityResponse])
def get_workspace_activities(
    workspace_id: int,
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the recent workspace audit activity feed."""
    verify_membership(db, workspace_id, current_user.id)
    return db.query(Activity).filter(Activity.workspace_id == workspace_id).order_by(Activity.created_at.desc()).limit(limit).all()

@router.get("/{workspace_id}/analytics", response_model=TeamAnalyticsResponse)
def get_team_analytics(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregate productivity analytics across the shared workspace."""
    verify_membership(db, workspace_id, current_user.id)
    tasks = db.query(Task).filter(Task.workspace_id == workspace_id).all()
    total = len(tasks)
    completed = sum(1 for t in tasks if (t.status or "").lower() == "completed")
    pending = total - completed
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    overdue = sum(1 for t in tasks if t.due_date and t.due_date < now_date and (t.status or "").lower() != "completed")
    
    projects_count = db.query(Project).filter(Project.workspace_id == workspace_id, Project.status == "ACTIVE").count()
    members_count = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).count()

    return {
        "total_shared_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "overdue_tasks": overdue,
        "active_projects_count": projects_count,
        "members_count": members_count
    }
