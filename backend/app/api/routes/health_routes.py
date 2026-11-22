import sys
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db, engine
from app.core.config import settings

router = APIRouter(tags=["Health & Observability"])

_START_TIME = time.time()

@router.get("/health")
def health_check():
    """Liveness probe indicating the API server is up and accepting HTTP traffic."""
    return {
        "status": "healthy",
        "service": "focusboard-api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/health/live")
def liveness_probe():
    """Kubernetes / container liveness check: validates process health."""
    return {
        "status": "alive",
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/health/ready")
@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe verifying database connectivity and primary dependency health."""
    try:
        t0 = time.perf_counter()
        db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "status": "ready",
            "database": {
                "status": "connected",
                "dialect": engine.dialect.name,
                "latency_ms": latency_ms
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection check failed: {str(exc)}"
        )

@router.get("/system/info")
def system_info():
    """Safe, non-confidential system and runtime metadata for operators."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "python_version": sys.version.split()[0],
        "database_dialect": engine.dialect.name,
        "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED,
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None
    }

@router.get("/metrics")
def get_prometheus_metrics(db: Session = Depends(get_db)):
    """Prometheus-compatible SRE observability metrics endpoint."""
    uptime_seconds = round(time.time() - _START_TIME, 2)
    db_status = 1
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = 0

    lines = [
        "# HELP focusboard_uptime_seconds Total seconds elapsed since API service initialization.",
        "# TYPE focusboard_uptime_seconds gauge",
        f"focusboard_uptime_seconds {uptime_seconds}",
        "# HELP focusboard_database_connected 1 if primary database is reachable, 0 otherwise.",
        "# TYPE focusboard_database_connected gauge",
        f"focusboard_database_connected {db_status}",
        "# HELP focusboard_api_status 1 if server is operating normally.",
        "# TYPE focusboard_api_status gauge",
        "focusboard_api_status 1",
    ]
    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4; charset=utf-8")
