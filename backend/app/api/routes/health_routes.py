from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

router = APIRouter(tags=["Health & Observability"])

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
