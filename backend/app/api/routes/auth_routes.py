from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.task import Task
from app.models.notification import Notification, NotificationPreference
from app.models.collaboration import WorkspaceMember, TaskComment
from app.models.audit import AuditLog
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, Token
from app.schemas.user_export import UserDataExportResponse, UserProfileData
from app.api.dependencies import get_current_user
from app.services.audit_service import record_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user account and return JWT access token."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or "Member",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))

    record_audit_log(
        db=db,
        event_type="AUTH_REGISTER",
        actor_id=user.id,
        resource_type="USER",
        resource_id=str(user.id),
        request=request,
        metadata={"email": user.email, "role": user.role}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive JWT access token."""
    user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        record_audit_log(
            db=db,
            event_type="AUTH_LOGIN_FAILED",
            resource_type="USER",
            request=request,
            metadata={"attempted_email": credentials.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been disabled."
        )

    token = create_access_token(subject=str(user.id))

    record_audit_log(
        db=db,
        event_type="AUTH_LOGIN_SUCCESS",
        actor_id=user.id,
        resource_type="USER",
        resource_id=str(user.id),
        request=request,
        metadata={"email": user.email}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log out user session and record security audit log."""
    record_audit_log(
        db=db,
        event_type="AUTH_LOGOUT",
        actor_id=current_user.id,
        resource_type="USER",
        resource_id=str(current_user.id),
        request=request,
    )
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile."""
    return current_user

@router.get("/export-data", response_model=UserDataExportResponse)
def export_user_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR Article 20 - Right to Data Portability.
    Export complete machine-readable copy of all user personal data, tasks,
    notifications, preferences, and workspace relationships.
    """
    # 1. User tasks
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    tasks_data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date,
            "workspace_id": t.workspace_id,
            "project_id": t.project_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]

    # 2. Notifications & Preferences
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).all()
    notifications_data = [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "status": n.status,
            "delivery_channel": n.delivery_channel,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]

    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == current_user.id).first()
    pref_data = {
        "email_enabled": pref.email_enabled,
        "in_app_enabled": pref.in_app_enabled,
        "due_date_reminders": pref.due_date_reminders,
        "daily_digest": pref.daily_digest,
    } if pref else None

    # 3. Workspaces & Comments
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).all()
    memberships_data = [
        {
            "workspace_id": m.workspace_id,
            "role": m.role,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None
        }
        for m in memberships
    ]

    comments = db.query(TaskComment).filter(TaskComment.author_id == current_user.id).all()
    comments_data = [
        {
            "id": c.id,
            "task_id": c.task_id,
            "content": c.content,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in comments
    ]

    # 4. Audit summary
    audit_logs = db.query(AuditLog).filter(AuditLog.actor_id == current_user.id).all()
    audit_summary: Dict[str, int] = {}
    for a in audit_logs:
        audit_summary[a.event_type] = audit_summary.get(a.event_type, 0) + 1

    record_audit_log(
        db=db,
        event_type="USER_DATA_EXPORT",
        actor_id=current_user.id,
        resource_type="USER",
        resource_id=str(current_user.id),
        request=request,
        metadata={"total_tasks": len(tasks_data), "total_notifications": len(notifications_data)}
    )

    return UserDataExportResponse(
        exported_at=datetime.now(timezone.utc),
        user_profile=UserProfileData(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at
        ),
        tasks=tasks_data,
        notifications=notifications_data,
        notification_preferences=pref_data,
        workspace_memberships=memberships_data,
        comments=comments_data,
        audit_summary=audit_summary
    )

@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_user_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR Article 17 - Right to Erasure ('Right to be Forgotten').
    Permanently deletes the authenticated user's account and cascades all personal records.
    """
    user_id = current_user.id
    email = current_user.email

    record_audit_log(
        db=db,
        event_type="ACCOUNT_DELETION",
        actor_id=user_id,
        resource_type="USER",
        resource_id=str(user_id),
        request=request,
        metadata={"deleted_email": email}
    )

    db.delete(current_user)
    db.commit()

    return {"message": "Account and associated personal data successfully deleted."}
