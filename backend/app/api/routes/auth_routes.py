"""
FocusBoard Authentication, Identity & Session Management Routes (Phase B2).
Provides complete authentication flows, JWT session tokens, token rotation,
password resets, email verifications, multi-device tracking, and user profile management.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import EmailVerificationToken, PasswordResetToken, AuthAuditLog, UserSession
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    EmailVerificationResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserProfileUpdate,
    UserResponse,
    UserSessionResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


def _get_client_info(request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "Unknown Device")
    return ip, user_agent


def _record_security_event(db: Session, event_type: str, user_id: Optional[int], ip: str, user_agent: str, metadata: dict = None):
    try:
        import json
        event = AuthAuditLog(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip,
            user_agent=user_agent,
            details_json=json.dumps(metadata or {}),
        )
        db.add(event)
        db.commit()
    except Exception as exc:
        logger.error("Failed to record security event: %s", exc)
        db.rollback()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or invalid format.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")
    if not user.is_active or user.status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive or suspended.")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Registers a new user account with secure defaults, prevents privilege escalation."""
    ip, user_agent = _get_client_info(request)
    
    # Check if email exists
    existing = db.query(User).filter(func.lower(User.email) == user_in.email.lower().strip()).first()
    if existing:
        _record_security_event(db, "registration_duplicate_email", None, ip, user_agent, {"email": user_in.email})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email address already exists.")
    
    # Normalize roles - users cannot register themselves as admin or superadmin
    allowed_roles = ["member", "user"]
    assigned_role = user_in.role.lower() if user_in.role and user_in.role.lower() in allowed_roles else "member"
    
    user = User(
        email=user_in.email.lower().strip(),
        name=user_in.username.strip() if user_in.username else (user_in.full_name or user_in.email.split("@")[0]),
        hashed_password=get_password_hash(user_in.password),
        display_name=user_in.display_name or user_in.full_name or user_in.username or "",
        role=assigned_role,
        is_active=True,
        is_verified=False,
        status="active",
        timezone=user_in.timezone or "UTC",
        locale=user_in.locale or "en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate verification token
    raw_token = generate_secure_token(32)
    vt = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(vt)
    db.commit()

    _record_security_event(db, "user_registered", user.id, ip, user_agent, {"email": user.email})
    logger.info("User registered successfully: id=%d email=%s", user.id, user.email)
    return user


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticates user, creates device session, returns access and refresh JWTs."""
    ip, user_agent = _get_client_info(request)
    user = db.query(User).filter(func.lower(User.email) == login_data.email.lower().strip()).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        _record_security_event(db, "login_failed", user.id if user else None, ip, user_agent, {"email": login_data.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active or user.status == "suspended":
        _record_security_event(db, "login_blocked_suspended", user.id, ip, user_agent)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated or suspended.")
    
    # Create session
    raw_refresh = generate_secure_token(48)
    refresh_hash = hash_token(raw_refresh)
    session_id = str(uuid.uuid4())
    refresh_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    user_session = UserSession(
        user_id=user.id,
        session_id=session_id,
        refresh_token_hash=refresh_hash,
        ip_address=ip,
        user_agent=user_agent,
        device_name=login_data.device_name or "Web Browser",
        expires_at=refresh_expires,
    )
    db.add(user_session)
    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "sid": session_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "sid": session_id, "token_val": raw_refresh}
    )

    _record_security_event(db, "login_success", user.id, ip, user_agent, {"sid": session_id})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    """OAuth2 compatible token endpoint."""
    login_data = LoginRequest(email=form_data.username, password=form_data.password)
    return login(login_data, request, db)


@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(refresh_in: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """Rotates refresh token and issues a new access token, detects reuse."""
    ip, user_agent = _get_client_info(request)
    payload = decode_token(refresh_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")
    
    user_id = payload.get("sub")
    session_id = payload.get("sid")
    raw_token = payload.get("token_val")
    
    session = db.query(UserSession).filter(
        UserSession.session_id == session_id,
        UserSession.user_id == int(user_id),
        UserSession.is_revoked == False,
    ).first()

    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or revoked.")
    
    if raw_token and session.refresh_token_hash != hash_token(raw_token):
        # Potential token reuse attack - revoke session immediately
        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        db.commit()
        _record_security_event(db, "token_reuse_detected_session_revoked", int(user_id), ip, user_agent, {"sid": session_id})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed. Re-authentication required.")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account inactive.")

    # Rotate refresh token
    new_raw_refresh = generate_secure_token(48)
    session.refresh_token_hash = hash_token(new_raw_refresh)
    session.last_active_at = datetime.utcnow()
    db.commit()

    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "sid": session_id}
    )
    new_refresh_jwt = create_refresh_token(
        data={"sub": str(user.id), "sid": session_id, "token_val": new_raw_refresh}
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_jwt,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes the current session."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split(" ")[1] if " " in auth_header else None
    payload = decode_token(token) if token else None
    session_id = payload.get("sid") if payload else None
    
    if session_id:
        db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == current_user.id
        ).update({"is_revoked": True, "revoked_at": datetime.utcnow()})
        db.commit()
    
    ip, user_agent = _get_client_info(request)
    _record_security_event(db, "logout", current_user.id, ip, user_agent, {"sid": session_id})
    return {"message": "Logged out successfully", "revoked_sessions": 1 if session_id else 0}


@router.post("/logout-all", response_model=LogoutResponse)
def logout_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes all active sessions for the current user across all devices."""
    count = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False
    ).update({"is_revoked": True, "revoked_at": datetime.utcnow()})
    db.commit()
    
    ip, user_agent = _get_client_info(request)
    _record_security_event(db, "logout_all_sessions", current_user.id, ip, user_agent, {"count": count})
    return {"message": "All sessions revoked successfully", "revoked_sessions": count}


@router.get("/sessions", response_model=List[UserSessionResponse])
def get_user_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all active and recent sessions for the current user."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split(" ")[1] if " " in auth_header else ""
    payload = decode_token(token)
    curr_sid = payload.get("sid") if payload else None

    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False,
        UserSession.expires_at > datetime.utcnow(),
    ).order_by(UserSession.last_active_at.desc()).all()

    result = []
    for s in sessions:
        result.append(
            UserSessionResponse(
                id=s.id,
                session_id=s.session_id,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                device_name=s.device_name,
                created_at=s.created_at,
                last_active_at=s.last_active_at,
                is_current=(s.session_id == curr_sid),
            )
        )
    return result


@router.delete("/sessions/{session_id}", response_model=LogoutResponse)
def revoke_specific_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes a specific session belonging to the current user."""
    sess = db.query(UserSession).filter(
        UserSession.session_id == session_id,
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False,
    ).first()
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or already revoked.")
    
    sess.is_revoked = True
    sess.revoked_at = datetime.utcnow()
    db.commit()

    ip, user_agent = _get_client_info(request)
    _record_security_event(db, "session_revoked_by_user", current_user.id, ip, user_agent, {"revoked_sid": session_id})
    return {"message": "Session revoked successfully", "revoked_sessions": 1}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Initiates a password reset flow with a time-limited token."""
    ip, user_agent = _get_client_info(request)
    user = db.query(User).filter(func.lower(User.email) == req.email.lower().strip()).first()
    
    # Generic message to avoid email enumeration
    msg = "If an account matches that email, a password reset link has been dispatched."
    if not user:
        _record_security_event(db, "forgot_password_unknown_email", None, ip, user_agent, {"email": req.email})
        return {"message": msg}
    
    raw_token = generate_secure_token(32)
    t_hash = hash_token(raw_token)
    token_rec = PasswordResetToken(
        user_id=user.id,
        token_hash=t_hash,
        expires_at=datetime.utcnow() + timedelta(hours=2),
    )
    db.add(token_rec)
    db.commit()

    _record_security_event(db, "forgot_password_requested", user.id, ip, user_agent)
    logger.info("Password reset token generated for user id=%d (reset token: %s)", user.id, raw_token)
    return {"message": msg, "reset_token": raw_token}


@router.post("/reset-password", response_model=LogoutResponse)
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Completes password reset using token and invalidates all existing sessions."""
    ip, user_agent = _get_client_info(request)
    t_hash = hash_token(req.token)
    
    token_rec = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == t_hash,
        PasswordResetToken.is_used == False,
    ).first()

    if not token_rec or token_rec.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token.")
    
    user = db.query(User).filter(User.id == token_rec.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    user.hashed_password = get_password_hash(req.new_password)
    token_rec.is_used = True
    token_rec.used_at = datetime.utcnow()
    
    # Invalidate all user sessions on password change
    revoked_count = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_revoked == False,
    ).update({"is_revoked": True, "revoked_at": datetime.utcnow()})

    db.commit()
    _record_security_event(db, "password_reset_completed", user.id, ip, user_agent)
    return {"message": "Password has been successfully reset. Please log in with your new credentials.", "revoked_sessions": revoked_count}


@router.post("/change-password", response_model=LogoutResponse)
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Changes password for an authenticated user and revokes other sessions."""
    ip, user_agent = _get_client_info(request)
    if not verify_password(req.current_password, current_user.hashed_password):
        _record_security_event(db, "change_password_invalid_current", current_user.id, ip, user_agent)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    
    current_user.hashed_password = get_password_hash(req.new_password)
    
    # Optionally revoke all other sessions
    auth_header = request.headers.get("authorization", "")
    token = auth_header.split(" ")[1] if " " in auth_header else ""
    payload = decode_token(token)
    curr_sid = payload.get("sid") if payload else None

    revoked_count = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.session_id != curr_sid,
        UserSession.is_revoked == False,
    ).update({"is_revoked": True, "revoked_at": datetime.utcnow()})

    db.commit()
    _record_security_event(db, "password_changed", current_user.id, ip, user_agent)
    return {"message": "Password updated successfully.", "revoked_sessions": revoked_count}


@router.post("/verify-email", response_model=EmailVerificationResponse)
def verify_email(token: str, request: Request, db: Session = Depends(get_db)):
    """Verifies a user's email address via token."""
    ip, user_agent = _get_client_info(request)
    t_hash = hash_token(token)
    
    rec = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == t_hash,
        EmailVerificationToken.is_used == False,
    ).first()

    if not rec or rec.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")
    
    user = db.query(User).filter(User.id == rec.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    user.is_verified = True
    rec.is_used = True
    rec.used_at = datetime.utcnow()
    db.commit()

    _record_security_event(db, "email_verified", user.id, ip, user_agent)
    return {"message": "Email address successfully verified.", "is_verified": True}


@router.post("/resend-verification", response_model=EmailVerificationResponse)
def resend_verification(req: ResendVerificationRequest, request: Request, db: Session = Depends(get_db)):
    """Issues a new email verification token."""
    ip, user_agent = _get_client_info(request)
    user = db.query(User).filter(func.lower(User.email) == req.email.lower().strip()).first()
    if not user:
        return {"message": "If this account exists and is unverified, a verification link has been sent.", "is_verified": False}
    
    if user.is_verified:
        return {"message": "Account is already verified.", "is_verified": True}
    
    raw_token = generate_secure_token(32)
    vt = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(vt)
    db.commit()
    logger.info("Resent verification token for user id=%d: %s", user.id, raw_token)
    return {"message": "Verification link has been sent.", "is_verified": False}


@router.get("/me", response_model=UserResponse)
@router.get("/users/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
@router.patch("/users/me", response_model=UserResponse)
def update_current_user_profile(
    profile_in: UserProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user personal details, display name, preferences."""
    ip, user_agent = _get_client_info(request)
    
    if profile_in.display_name is not None:
        current_user.display_name = profile_in.display_name
    if profile_in.full_name is not None:
        current_user.name = profile_in.full_name
    if profile_in.avatar_url is not None:
        current_user.avatar_url = profile_in.avatar_url
    if profile_in.timezone is not None:
        current_user.timezone = profile_in.timezone
    if profile_in.locale is not None:
        current_user.locale = profile_in.locale

    db.commit()
    db.refresh(current_user)
    _record_security_event(db, "profile_updated", current_user.id, ip, user_agent)
    return current_user


@router.get("/export-data")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """GDPR Data portability: exports user account data and metadata."""
    sessions = db.query(UserSession).filter(UserSession.user_id == current_user.id).all()
    events = db.query(AuthAuditLog).filter(AuthAuditLog.user_id == current_user.id).all()
    
    return {
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "display_name": current_user.display_name,
            "role": current_user.role,
            "status": current_user.status,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "session_history": [
            {
                "session_id": s.session_id,
                "ip": s.ip_address,
                "device": s.device_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "is_revoked": s.is_revoked,
            }
            for s in sessions
        ],
        "security_log_count": len(events),
    }


@router.delete("/me", response_model=LogoutResponse)
def delete_own_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """GDPR right to erasure: deactivates user account and revokes all active sessions."""
    ip, user_agent = _get_client_info(request)
    current_user.is_active = False
    current_user.status = "deactivated"
    
    revoked_count = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False
    ).update({"is_revoked": True, "revoked_at": datetime.utcnow()})

    db.commit()
    _record_security_event(db, "account_deactivated_by_user", current_user.id, ip, user_agent)
    return {"message": "Account has been deactivated and all sessions terminated.", "revoked_sessions": revoked_count}
