from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import jwt
import bcrypt
from app.core.config import settings

import secrets
import hashlib

def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically strong URL-safe random token."""
    return secrets.token_urlsafe(nbytes)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely compare a plaintext password with a stored bcrypt hash."""
    try:
        pw_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generate a secure salted bcrypt hash for a plaintext password."""
    pw_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode('utf-8')

def create_access_token(
    subject: Union[str, Any, None] = None,
    session_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    data: Optional[dict] = None,
) -> str:
    """Generate a signed JWT bearer token containing user identity and expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    if data:
        to_encode.update(data)
    if isinstance(subject, dict):
        if "sub" in subject:
            to_encode["sub"] = str(subject["sub"])
        to_encode.update(subject)
    elif subject is not None:
        to_encode["sub"] = str(subject)
    if session_id:
        to_encode["session_id"] = str(session_id)
        to_encode["sid"] = str(session_id)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any, None] = None,
    session_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    data: Optional[dict] = None,
) -> str:
    """Generate a signed JWT refresh token with extended lifecycle."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }
    if data:
        to_encode.update(data)
    if isinstance(subject, dict):
        if "sub" in subject:
            to_encode["sub"] = str(subject["sub"])
        to_encode.update(subject)
    elif subject is not None:
        to_encode["sub"] = str(subject)
    if session_id:
        to_encode["session_id"] = str(session_id)
        to_encode["sid"] = str(session_id)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a signed JWT token. Returns None on expiry or invalid signature."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[dict]:
    """Decode and validate a signed JWT token with optional token type enforcement."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None

def hash_token(token: str) -> str:
    """SHA-256 digest for safe database persistence of session and recovery tokens."""
    import hashlib
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
