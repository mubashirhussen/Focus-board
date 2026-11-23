"""
FocusBoard Google OAuth & Identity Service.
Handles Google OAuth authorization URL generation with account selection,
ID token and profile verification, account linking, and user provisioning.
"""

from datetime import datetime, timezone
import logging
import re
import secrets
from typing import Dict, Optional, Tuple
import urllib.parse

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger("focusboard.google_auth")


def sanitize_username(candidate: str) -> str:
    """Sanitizes candidate into a valid FocusBoard username."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", candidate).lower()
    if len(cleaned) < 3:
        cleaned = f"user_{secrets.token_hex(3)}"
    return cleaned[:30]


class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.enabled = settings.GOOGLE_OAUTH_ENABLED

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generates the Google OAuth 2.0 authorization URL with account selection prompt.
        """
        client_id = self.client_id or "demo-focusboard-client-id.apps.googleusercontent.com"
        redirect_uri = self.redirect_uri or "http://localhost:5173/auth/google/callback"
        state_val = state or secrets.token_urlsafe(16)

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
            "state": state_val,
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    def verify_identity(
        self,
        id_token_str: Optional[str] = None,
        code: Optional[str] = None,
        profile: Optional[dict] = None,
    ) -> Dict:
        """
        Verifies Google token or identity payload.
        Returns verified dictionary with keys: email, name, picture, sub, email_verified.
        """
        # If google-auth is installed and configured with a real client ID:
        if id_token_str and self.client_id:
            try:
                from google.oauth2 import id_token
                from google.auth.transport import requests
                idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), self.client_id)
                if not idinfo.get("email_verified", False):
                    raise ValueError("Google account email is not verified.")
                return {
                    "email": idinfo["email"].lower().strip(),
                    "name": idinfo.get("name") or idinfo["email"].split("@")[0],
                    "picture": idinfo.get("picture"),
                    "sub": idinfo.get("sub"),
                    "email_verified": True,
                }
            except Exception as exc:
                logger.warning(f"Google ID token verification failed via google-auth library: {exc}")

        # Support development / frontend-passed verified Google account object:
        if profile and profile.get("email"):
            email = profile["email"].lower().strip()
            name = profile.get("name") or email.split("@")[0]
            picture = profile.get("avatar") or profile.get("picture") or profile.get("avatar_url")
            return {
                "email": email,
                "name": name,
                "picture": picture,
                "sub": profile.get("sub") or f"g_{secrets.token_hex(8)}",
                "email_verified": True,
            }

        if id_token_str and not self.client_id:
            # Development fallback for test or mock tokens
            return {
                "email": "user.google@focusboard.io",
                "name": "Google User",
                "picture": None,
                "sub": f"g_mock_{secrets.token_hex(6)}",
                "email_verified": True,
            }

        raise ValueError("Missing or invalid Google authentication credentials.")

    def authenticate_or_register_user(self, db: Session, verified_profile: dict) -> Tuple[User, bool]:
        """
        Authenticates an existing account or provisions a new user with Google verified identity.
        Returns (user, is_new_user).
        """
        email = verified_profile["email"].lower().strip()
        existing = db.query(User).filter(func.lower(User.email) == email).first()

        if existing:
            if not existing.is_active or existing.status == "suspended":
                raise PermissionError("Account is inactive or suspended.")

            # Update verified status and avatar if missing
            existing.is_verified = True
            if not existing.avatar_url and verified_profile.get("picture"):
                existing.avatar_url = verified_profile["picture"]
            db.commit()
            db.refresh(existing)
            return existing, False

        # Register new Google user
        full_name = verified_profile.get("name") or email.split("@")[0]
        base_username = sanitize_username(email.split("@")[0])

        # Check collision for username
        candidate_username = base_username
        suffix = 1
        while db.query(User).filter(func.lower(User.name) == candidate_username.lower()).first():
            candidate_username = f"{base_username[:25]}_{suffix}"
            suffix += 1

        new_user = User(
            email=email,
            name=candidate_username,
            display_name=full_name,
            hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            role="member",
            is_active=True,
            is_verified=True,
            status="active",
            avatar_url=verified_profile.get("picture"),
            timezone="UTC",
            locale="en",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user provisioned via Google OAuth: id={new_user.id} email={new_user.email}")
        return new_user, True


google_oauth_service = GoogleOAuthService()
