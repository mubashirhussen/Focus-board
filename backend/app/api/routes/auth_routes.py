"""
FocusBoard Authentication, Identity & Session Management Routes (Phase B2).
Provides complete authentication flows, JWT session tokens, token rotation,
password resets, email verifications, multi-device tracking, and user profile management.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
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
from app.models.auth import EmailVerificationToken, PasswordResetToken, AuthAuditLog, UserSession, EmailOTPVerification
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
    EmailAuthStartRequest,
    EmailAuthStartResponse,
    UsernameCheckResponse,
    EmailRegisterRequest,
    VerifyOTPRequest,
    ResendOTPRequest,
    GoogleAuthRequest,
    GoogleAuthUrlResponse,
)
from app.services.otp_service import otp_service
from app.services.google_oauth_service import google_oauth_service

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


def _create_authenticated_session(
    user: User,
    request: Request,
    db: Session,
    device_name: Optional[str] = None,
    event_type: str = "login_success",
    metadata: Optional[dict] = None,
) -> dict:
    ip, user_agent = _get_client_info(request)
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
        device_name=device_name or "Web Browser",
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

    sec_meta = {"sid": session_id}
    if metadata:
        sec_meta.update(metadata)
    _record_security_event(db, event_type, user.id, ip, user_agent, sec_meta)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


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
    
    name_val = user_in.username.strip() if user_in.username else (user_in.name or user_in.full_name or user_in.email.split("@")[0])
    user = User(
        email=user_in.email.lower().strip(),
        name=name_val,
        hashed_password=get_password_hash(user_in.password),
        display_name=user_in.display_name or user_in.full_name or user_in.name or user_in.username or "",
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
    
    # Generate direct access token for backward compatibility
    access_token = create_access_token(subject=str(user.id), data={"email": user.email, "role": user.role, "type": "access"})
    resp = UserResponse.model_validate(user)
    resp.access_token = access_token
    return resp


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
    
    return _create_authenticated_session(user, request, db, device_name=login_data.device_name, event_type="login_success")


# ============================================================================
# Passwordless Email & OTP Authentication Endpoints
# ============================================================================

@router.post("/email/start", response_model=EmailAuthStartResponse)
def email_auth_start(req: EmailAuthStartRequest, request: Request, db: Session = Depends(get_db)):
    """
    Step 1 of Passwordless Auth:
    Validates email. If user exists, dispatches login OTP.
    If user is new, prompts registration step with name and username collection.
    """
    ip, user_agent = _get_client_info(request)
    normalized_email = req.email.lower().strip()

    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()

    if user:
        if not user.is_active or user.status == "suspended":
            _record_security_event(db, "email_start_blocked_suspended", user.id, ip, user_agent, {"email": normalized_email})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated or suspended.")

        session_id, _ = otp_service.create_otp_session(db, normalized_email, purpose="login")
        _record_security_event(db, "login_otp_dispatched", user.id, ip, user_agent, {"email": normalized_email, "sid": session_id})

        return EmailAuthStartResponse(
            success=True,
            message="Verification code sent to your email.",
            is_new_user=False,
            verification_session_id=session_id,
            email=normalized_email,
            expires_in=settings.OTP_EXPIRATION_SECONDS,
            resend_after=settings.OTP_RESEND_COOLDOWN_SECONDS,
        )

    # User does not exist -> proceed to registration step
    return EmailAuthStartResponse(
        success=True,
        message="Account does not exist yet. Please enter your name and username.",
        is_new_user=True,
        verification_session_id=None,
        email=normalized_email,
        expires_in=None,
        resend_after=None,
    )


@router.get("/username/check", response_model=UsernameCheckResponse)
def check_username_availability(username: str = Query(..., min_length=1, max_length=50), db: Session = Depends(get_db)):
    """
    Validates username format, length, reserved terms, and database uniqueness.
    """
    cleaned = username.strip().lower()

    if len(cleaned) < 3 or len(cleaned) > 30:
        return UsernameCheckResponse(
            available=False,
            username=cleaned,
            message="Username must be between 3 and 30 characters.",
        )

    if not re.match(r"^[a-zA-Z0-9_-]+$", cleaned):
        return UsernameCheckResponse(
            available=False,
            username=cleaned,
            message="Username may only contain letters, numbers, underscores, and hyphens.",
        )

    reserved_names = {
        "admin", "administrator", "root", "system", "focusboard",
        "support", "help", "security", "api", "auth", "guest", "mod", "null",
    }
    if cleaned in reserved_names:
        return UsernameCheckResponse(
            available=False,
            username=cleaned,
            message="This username is reserved and cannot be selected.",
        )

    # Check database collision against User.name or User.display_name
    collision = db.query(User).filter(func.lower(User.name) == cleaned).first()
    if collision:
        return UsernameCheckResponse(
            available=False,
            username=cleaned,
            message="This username is already taken. Please choose another.",
        )

    return UsernameCheckResponse(
        available=True,
        username=cleaned,
        message="Username is available.",
    )


@router.post("/email/register")
def register_with_email_otp(req: EmailRegisterRequest, request: Request, db: Session = Depends(get_db)):
    """
    Step 2 of Passwordless Registration:
    Collects full name, username, and email. Validates input and dispatches a 6-digit registration OTP.
    """
    ip, user_agent = _get_client_info(request)
    normalized_email = req.email.lower().strip()
    cleaned_name = req.name.strip()
    cleaned_username = req.username.strip().lower()

    if len(cleaned_name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please enter a valid full name (minimum 2 characters).")

    # Username checks
    if len(cleaned_username) < 3 or len(cleaned_username) > 30 or not re.match(r"^[a-zA-Z0-9_-]+$", cleaned_username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be 3-30 characters alphanumeric, underscore or hyphen.")

    # Duplicate checks
    if db.query(User).filter(func.lower(User.email) == normalized_email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email address already exists. Please sign in.")

    if db.query(User).filter(func.lower(User.name) == cleaned_username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This username is already taken. Please choose another.")

    session_id, _ = otp_service.create_otp_session(
        db=db,
        email=normalized_email,
        purpose="registration",
        metadata={
            "name": cleaned_name,
            "username": cleaned_username,
            "role": req.role or "member",
        },
    )

    _record_security_event(db, "registration_otp_dispatched", None, ip, user_agent, {"email": normalized_email, "username": cleaned_username})

    return {
        "success": True,
        "message": "Verification code dispatched to your email. Enter code to complete registration.",
        "verification_session_id": session_id,
        "email": normalized_email,
        "expires_in": settings.OTP_EXPIRATION_SECONDS,
        "resend_after": settings.OTP_RESEND_COOLDOWN_SECONDS,
    }


@router.post("/email/verify-otp", response_model=Token)
def verify_email_otp(req: VerifyOTPRequest, request: Request, db: Session = Depends(get_db)):
    """
    Step 3 of Email Auth:
    Verifies 6-digit OTP. For registration, provisions the new user account with verified status.
    For login, confirms active status. Issues JWT access & refresh tokens and user session.
    """
    ip, user_agent = _get_client_info(request)
    normalized_email = req.email.lower().strip()
    purpose = req.purpose or "login"

    is_valid, err_msg, metadata = otp_service.verify_otp(
        db=db,
        email=normalized_email,
        otp=req.otp,
        session_id=req.verification_session_id,
        purpose=purpose,
    )

    if not is_valid:
        _record_security_event(db, "otp_verification_failed", None, ip, user_agent, {"email": normalized_email, "reason": err_msg})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    if purpose == "registration":
        # Check if already provisioned (avoid race conditions)
        user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
        if not user:
            name_val = metadata.get("username") or normalized_email.split("@")[0]
            display_val = metadata.get("name") or name_val
            role_val = metadata.get("role") or "member"
            random_pw = generate_secure_token(32)

            user = User(
                email=normalized_email,
                name=name_val,
                display_name=display_val,
                hashed_password=get_password_hash(random_pw),
                role=role_val,
                is_active=True,
                is_verified=True,
                status="active",
                timezone="UTC",
                locale="en",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return _create_authenticated_session(
            user=user,
            request=request,
            db=db,
            device_name=req.device_name or "Web Browser",
            event_type="registration_otp_verified",
        )

    # Existing user login OTP
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    if not user.is_active or user.status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated or suspended.")

    user.is_verified = True
    db.commit()

    return _create_authenticated_session(
        user=user,
        request=request,
        db=db,
        device_name=req.device_name or "Web Browser",
        event_type="login_otp_verified",
    )


@router.post("/email/resend-otp")
def resend_email_otp(req: ResendOTPRequest, request: Request, db: Session = Depends(get_db)):
    """
    Resends OTP with cooldown rate limiting and previous code invalidation.
    """
    ip, user_agent = _get_client_info(request)
    normalized_email = req.email.lower().strip()
    purpose = req.purpose or "login"

    success, msg, cooldown, expires = otp_service.resend_otp(
        db=db,
        email=normalized_email,
        session_id=req.verification_session_id,
        purpose=purpose,
    )

    if not success:
        _record_security_event(db, "otp_resend_throttled", None, ip, user_agent, {"email": normalized_email})
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)

    _record_security_event(db, "otp_resend_success", None, ip, user_agent, {"email": normalized_email})
    return {
        "success": True,
        "message": msg,
        "resend_after": cooldown,
        "expires_in": expires,
    }


# ============================================================================
# Google OAuth 2.0 & Identity Endpoints
# ============================================================================

@router.get("/google/url", response_model=GoogleAuthUrlResponse)
def get_google_auth_url(state: Optional[str] = None):
    """
    Generates and returns the Google OAuth authorization URL configured with
    account selection prompt and redirect parameters.
    """
    url = google_oauth_service.get_authorization_url(state=state)
    return GoogleAuthUrlResponse(
        url=url,
        enabled=google_oauth_service.enabled,
        client_id=google_oauth_service.client_id,
    )


@router.post("/google/verify", response_model=Token)
def verify_google_authentication(req: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    """
    Verifies Google OAuth ID token or profile payload.
    Maps to an existing user or provisions a new user with verified email.
    Creates an authenticated session and issues JWT tokens.
    """
    ip, user_agent = _get_client_info(request)

    try:
        verified_profile = google_oauth_service.verify_identity(
            id_token_str=req.id_token,
            code=req.code,
            profile=req.model_dump(),
        )
    except Exception as exc:
        _record_security_event(db, "google_auth_failed", None, ip, user_agent, {"error": str(exc)})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google authentication failed: {exc}")

    try:
        user, is_new = google_oauth_service.authenticate_or_register_user(db, verified_profile)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to provision user: {exc}")

    event_type = "google_auth_new_user" if is_new else "google_auth_login"
    return _create_authenticated_session(
        user=user,
        request=request,
        db=db,
        device_name=req.device_name or "Google OAuth Session",
        event_type=event_type,
        metadata={"google_sub": verified_profile.get("sub")},
    )


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
