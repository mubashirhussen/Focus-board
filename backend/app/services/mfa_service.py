import hmac
import hashlib
import time
import struct
import base64
import secrets
import json
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.models.enterprise import UserMFA
from app.models.user import User

def generate_base32_secret(length: int = 16) -> str:
    """Generate cryptographically secure random base32 secret."""
    raw = secrets.token_bytes(length)
    return base64.b32encode(raw).decode("utf-8").replace("=", "")[:16]

def generate_totp_code(secret_b32: str, time_step: int = 30) -> str:
    """Compute RFC 6238 compliant 6-digit TOTP code."""
    # Normalize and pad base32 secret
    padded = secret_b32 + "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    counter = int(time.time() // time_step)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code_int % 1000000).zfill(6)

def verify_totp(secret_b32: str, code: str, window: int = 1) -> bool:
    """Verify code with time drift window."""
    code = code.strip()
    padded = secret_b32 + "=" * ((8 - len(secret_b32) % 8) % 8)
    try:
        key = base64.b32decode(padded, casefold=True)
    except Exception:
        return False

    current_counter = int(time.time() // 30)
    for step_offset in range(-window, window + 1):
        msg = struct.pack(">Q", current_counter + step_offset)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        code_int = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
        if str(code_int % 1000000).zfill(6) == code:
            return True
    return False

def hash_recovery_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()

class MFAService:
    def setup_mfa(self, db: Session, user: User) -> Tuple[str, str, List[str]]:
        secret = generate_base32_secret()
        qr_uri = f"otpauth://totp/FocusBoard:{user.email}?secret={secret}&issuer=FocusBoard"

        # Generate 8 single-use recovery codes
        raw_recovery = [secrets.token_hex(4).upper() for _ in range(8)]
        hashed_recovery = [hash_recovery_code(c) for c in raw_recovery]

        mfa_record = db.query(UserMFA).filter(UserMFA.user_id == user.id).first()
        if not mfa_record:
            mfa_record = UserMFA(
                user_id=user.id,
                secret_hash=secret,  # in real env encrypt with app secret
                is_enabled=False,
                recovery_codes_json=json.dumps(hashed_recovery)
            )
            db.add(mfa_record)
        else:
            mfa_record.secret_hash = secret
            mfa_record.is_enabled = False
            mfa_record.recovery_codes_json = json.dumps(hashed_recovery)

        db.commit()
        return secret, qr_uri, raw_recovery

    def verify_and_enable(self, db: Session, user: User, code: str) -> bool:
        mfa_record = db.query(UserMFA).filter(UserMFA.user_id == user.id).first()
        if not mfa_record:
            return False

        if verify_totp(mfa_record.secret_hash, code):
            mfa_record.is_enabled = True
            db.commit()
            return True
        return False

    def disable_mfa(self, db: Session, user: User, code_or_recovery: str) -> bool:
        mfa_record = db.query(UserMFA).filter(UserMFA.user_id == user.id).first()
        if not mfa_record:
            return False

        # Verify either TOTP code or recovery code
        is_totp = verify_totp(mfa_record.secret_hash, code_or_recovery)
        hashed_input = hash_recovery_code(code_or_recovery)
        recovery_list = json.loads(mfa_record.recovery_codes_json) if mfa_record.recovery_codes_json else []
        is_recovery = hashed_input in recovery_list

        if is_totp or is_recovery:
            mfa_record.is_enabled = False
            db.commit()
            return True
        return False

mfa_service = MFAService()
