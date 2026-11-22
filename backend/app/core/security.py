from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import jwt
import bcrypt
from app.core.config import settings

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

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT bearer token containing user identity and expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": now,
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a signed JWT token. Returns None on expiry or invalid signature."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
