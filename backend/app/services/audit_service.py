import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger("focusboard.audit")

SENSITIVE_KEYS = {"password", "secret", "token", "access_token", "hashed_password", "authorization"}

def sanitize_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scrub sensitive keys (passwords, tokens, credentials) from metadata."""
    if not isinstance(data, dict):
        return data
    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_metadata(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_metadata(v) if isinstance(v, dict) else v for v in value]
        else:
            sanitized[key] = value
    return sanitized

def record_audit_log(
    db: Session,
    event_type: str,
    actor_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    request: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Safely log security-relevant actions to the immutable audit trail."""
    request_id = None
    ip_address = None
    user_agent = None

    if request:
        request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
        # Extract client IP respecting forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host
        user_agent = request.headers.get("User-Agent")

    sanitized_meta = sanitize_metadata(metadata) if metadata else None
    metadata_json = json.dumps(sanitized_meta) if sanitized_meta else None

    log_entry = AuditLog(
        actor_id=actor_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent[:255] if user_agent else None,
        metadata_json=metadata_json,
    )
    db.add(log_entry)
    try:
        db.commit()
        db.refresh(log_entry)
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to commit audit log entry: {exc}")

    return log_entry
