import time
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

router = APIRouter(tags=["Health & Observability"])

_START_TIME = time.time()

@router.get("/health")
def health_check():
    """Liveness probe indicating the API server is up and accepting HTTP traffic."""
    return {
        "status": "healthy",
        "service": "focusboard-api",
        "timestamp": True
    }

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe verifying database connectivity."""
    try:
        # Execute light ping query
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(exc)}"
        )

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
