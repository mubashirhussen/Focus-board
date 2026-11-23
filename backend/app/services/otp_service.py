"""
FocusBoard Secure OTP (One-Time Password) Service.
Provides cryptographically secure 6-digit OTP generation, SHA-256 hashing,
expiration enforcement, attempt limits, resend throttling, and email dispatch.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import secrets
from typing import Dict, Optional, Tuple
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.auth import EmailOTPVerification
from app.services.email_service import email_service

logger = logging.getLogger("focusboard.otp")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OTPService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generates a cryptographically secure numeric random code."""
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @staticmethod
    def hash_otp(otp: str, salt: str = "") -> str:
        """Hashes the OTP with SHA-256 to avoid storing plaintext in database."""
        raw = f"{otp}:{salt}" if salt else otp
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def create_otp_session(
        self,
        db: Session,
        email: str,
        purpose: str = "login",
        metadata: Optional[dict] = None,
    ) -> Tuple[str, str]:
        """
        Creates a new verification session, stores the hashed OTP,
        invalidates prior active sessions for this email/purpose, and dispatches the email.
        Returns (session_id, raw_otp).
        """
        normalized_email = email.strip().lower()

        # Invalidate previous unused sessions for this email & purpose
        db.query(EmailOTPVerification).filter(
            func.lower(EmailOTPVerification.email) == normalized_email,
            EmailOTPVerification.purpose == purpose,
            EmailOTPVerification.is_consumed == False,
        ).update({"is_consumed": True})
        db.commit()

        raw_otp = self.generate_otp(getattr(settings, "OTP_LENGTH", 6))
        otp_hash = self.hash_otp(raw_otp)
        session_id = f"otp_sess_{uuid.uuid4().hex}"
        expiration_secs = getattr(settings, "OTP_EXPIRATION_SECONDS", 300)
        expires_at = utc_now() + timedelta(seconds=expiration_secs)

        otp_record = EmailOTPVerification(
            session_id=session_id,
            email=normalized_email,
            otp_hash=otp_hash,
            purpose=purpose,
            metadata_json=json.dumps(metadata or {}),
            attempts=0,
            max_attempts=getattr(settings, "OTP_MAX_ATTEMPTS", 5),
            is_verified=False,
            is_consumed=False,
            expires_at=expires_at,
            last_sent_at=utc_now(),
            created_at=utc_now(),
        )
        db.add(otp_record)
        db.commit()

        # Dispatch verification email
        email_service.send_otp_email(
            to_email=normalized_email,
            otp=raw_otp,
            purpose=purpose,
            expires_minutes=expiration_secs // 60,
        )

        return session_id, raw_otp

    def verify_otp(
        self,
        db: Session,
        email: str,
        otp: str,
        session_id: Optional[str] = None,
        purpose: str = "login",
    ) -> Tuple[bool, str, dict]:
        """
        Validates OTP against active session.
        Enforces expiration, max attempts, and marks code as consumed upon success.
        Returns (is_valid, message, metadata).
        """
        normalized_email = email.strip().lower()
        cleaned_otp = otp.strip()

        query = db.query(EmailOTPVerification).filter(
            func.lower(EmailOTPVerification.email) == normalized_email,
            EmailOTPVerification.purpose == purpose,
            EmailOTPVerification.is_consumed == False,
        )

        if session_id:
            query = query.filter(EmailOTPVerification.session_id == session_id)

        record = query.order_by(EmailOTPVerification.created_at.desc()).first()

        if not record:
            return False, "Invalid or expired verification session.", {}

        # Check expiration
        now = utc_now()
        # Handle naive vs aware datetime from SQLite
        rec_expires = record.expires_at
        if rec_expires.tzinfo is None:
            rec_expires = rec_expires.replace(tzinfo=timezone.utc)

        if rec_expires < now:
            record.is_consumed = True
            db.commit()
            return False, "Verification code has expired. Please request a new code.", {}

        # Check attempt count
        if record.attempts >= record.max_attempts:
            record.is_consumed = True
            db.commit()
            return False, "Maximum verification attempts exceeded. Code has been invalidated. Please request a new code.", {}

        record.attempts += 1
        expected_hash = self.hash_otp(cleaned_otp)

        if record.otp_hash != expected_hash:
            db.commit()
            remaining = max(0, record.max_attempts - record.attempts)
            return False, f"Incorrect verification code. {remaining} attempt(s) remaining.", {}

        # Verification successful
        record.is_verified = True
        record.is_consumed = True
        db.commit()

        metadata = {}
        try:
            metadata = json.loads(record.metadata_json or "{}")
        except Exception:
            pass

        return True, "Email verified successfully.", metadata

    def resend_otp(
        self,
        db: Session,
        email: str,
        session_id: Optional[str] = None,
        purpose: str = "login",
    ) -> Tuple[bool, str, int, int]:
        """
        Resends an OTP subject to cooldown throttling.
        Returns (success, message, resend_after_secs, expires_in_secs).
        """
        normalized_email = email.strip().lower()
        query = db.query(EmailOTPVerification).filter(
            func.lower(EmailOTPVerification.email) == normalized_email,
            EmailOTPVerification.purpose == purpose,
            EmailOTPVerification.is_consumed == False,
        )

        if session_id:
            query = query.filter(EmailOTPVerification.session_id == session_id)

        record = query.order_by(EmailOTPVerification.created_at.desc()).first()

        cooldown_secs = getattr(settings, "OTP_RESEND_COOLDOWN_SECONDS", 60)
        expiration_secs = getattr(settings, "OTP_EXPIRATION_SECONDS", 300)

        if record:
            now = utc_now()
            last_sent = record.last_sent_at
            if last_sent.tzinfo is None:
                last_sent = last_sent.replace(tzinfo=timezone.utc)
            elapsed = (now - last_sent).total_seconds()

            if elapsed < cooldown_secs:
                remaining = int(cooldown_secs - elapsed)
                return False, f"Please wait {remaining} seconds before requesting a new code.", remaining, expiration_secs

        # Create fresh session and dispatch
        new_sess_id, _ = self.create_otp_session(
            db=db,
            email=normalized_email,
            purpose=purpose,
            metadata=json.loads(record.metadata_json) if record and record.metadata_json else None,
        )

        return True, "A new verification code has been dispatched to your email.", cooldown_secs, expiration_secs


otp_service = OTPService()
