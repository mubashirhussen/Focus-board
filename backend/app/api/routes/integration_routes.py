from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.integration import ExternalIntegration
from app.schemas.integration import IntegrationResponse, AvailableIntegrationItem, ConnectResponse
from app.api.dependencies import get_current_user
from app.services.google_calendar_service import calendar_service

router = APIRouter(prefix="/integrations", tags=["External Integrations"])

AVAILABLE_CATALOG = [
    {
        "provider": "google_calendar",
        "name": "Google Calendar",
        "category": "Calendar",
        "description": "Two-way synchronization for scheduled tasks, deadlines, and smart meeting conflict detection.",
        "icon": "Calendar",
    },
    {
        "provider": "slack",
        "name": "Slack Notifications",
        "category": "Communication",
        "description": "Receive instant task updates, assignments, and daily AI summary briefings in your team channel.",
        "icon": "MessageSquare",
    },
    {
        "provider": "github",
        "name": "GitHub Issues",
        "category": "Development",
        "description": "Link engineering tasks directly with GitHub repository issues, branches, and pull requests.",
        "icon": "GitBranch",
    },
]

@router.get("", response_model=List[IntegrationResponse])
def get_user_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all external integrations connected by the authenticated user."""
    return db.query(ExternalIntegration).filter(ExternalIntegration.user_id == current_user.id).all()

@router.get("/available", response_model=List[AvailableIntegrationItem])
def get_available_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available integration hub catalog items with connection status."""
    connected_providers = {
        i.provider for i in db.query(ExternalIntegration).filter(
            ExternalIntegration.user_id == current_user.id,
            ExternalIntegration.status == "connected"
        ).all()
    }

    return [
        AvailableIntegrationItem(
            provider=cat["provider"],
            name=cat["name"],
            category=cat["category"],
            description=cat["description"],
            icon=cat["icon"],
            is_connected=(cat["provider"] in connected_providers)
        )
        for cat in AVAILABLE_CATALOG
    ]

@router.get("/google/connect", response_model=ConnectResponse)
def connect_google_calendar(
    redirect_uri: str = Query("http://localhost:5173/integrations/callback"),
    current_user: User = Depends(get_current_user)
):
    """Initiate Google OAuth flow for Calendar synchronization."""
    res = calendar_service.generate_auth_url(current_user.id, redirect_uri)
    return ConnectResponse(
        authorization_url=res["authorization_url"],
        state=res["state"]
    )

@router.get("/google/callback", response_model=IntegrationResponse)
def google_calendar_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth CSRF state"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Authorize Google Calendar and persist credentials."""
    integration = calendar_service.connect_account(db, current_user.id, code)
    return integration

@router.delete("/{integration_id}", status_code=status.HTTP_200_OK)
def disconnect_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disconnect and revoke integration."""
    integration = db.query(ExternalIntegration).filter(
        ExternalIntegration.id == integration_id,
        ExternalIntegration.user_id == current_user.id
    ).first()

    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    db.delete(integration)
    db.commit()
    return {"message": "Integration successfully disconnected"}
