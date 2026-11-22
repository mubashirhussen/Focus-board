from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.regional_settings import UserRegionalSetting

SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native": "English", "direction": "ltr"},
    {"code": "hi", "name": "Hindi", "native": "हिन्दी", "direction": "ltr"},
    {"code": "te", "name": "Telugu", "native": "తెలుగు", "direction": "ltr"},
    {"code": "ta", "name": "Tamil", "native": "தமிழ்", "direction": "ltr"},
    {"code": "es", "name": "Spanish", "native": "Español", "direction": "ltr"},
    {"code": "ar", "name": "Arabic", "native": "العربية", "direction": "rtl"},
]

SUPPORTED_CURRENCIES = [
    {"code": "USD", "symbol": "$", "name": "US Dollar"},
    {"code": "INR", "symbol": "₹", "name": "Indian Rupee"},
    {"code": "EUR", "symbol": "€", "name": "Euro"},
    {"code": "GBP", "symbol": "£", "name": "British Pound"},
    {"code": "AED", "symbol": "د.إ", "name": "UAE Dirham"},
    {"code": "JPY", "symbol": "¥", "name": "Japanese Yen"},
]

SUPPORTED_TIMEZONES = [
    "UTC",
    "Asia/Kolkata",
    "Asia/Dubai",
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Singapore",
    "Asia/Tokyo",
    "Australia/Sydney",
]

SUPPORTED_DATE_FORMATS = [
    "YYYY-MM-DD",
    "DD/MM/YYYY",
    "MM/DD/YYYY",
]

def get_or_create_regional_settings(db: Session, user_id: int) -> UserRegionalSetting:
    setting = db.query(UserRegionalSetting).filter(UserRegionalSetting.user_id == user_id).first()
    if not setting:
        setting = UserRegionalSetting(
            user_id=user_id,
            language="en",
            locale="en-US",
            timezone="Asia/Kolkata",
            date_format="YYYY-MM-DD",
            time_format="12h",
            week_start=1,
            currency="USD",
            number_format="standard",
            direction="ltr",
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

def update_regional_settings(
    db: Session,
    user_id: int,
    language: Optional[str] = None,
    locale: Optional[str] = None,
    timezone: Optional[str] = None,
    date_format: Optional[str] = None,
    time_format: Optional[str] = None,
    week_start: Optional[int] = None,
    currency: Optional[str] = None,
    number_format: Optional[str] = None,
    direction: Optional[str] = None,
) -> UserRegionalSetting:
    setting = get_or_create_regional_settings(db, user_id)

    if language:
        lang_match = next((l for l in SUPPORTED_LANGUAGES if l["code"] == language.lower()), None)
        if not lang_match:
            raise ValueError(f"Language '{language}' is not supported.")
        setting.language = lang_match["code"]
        # Auto-update direction if not explicitly set
        if not direction:
            setting.direction = lang_match["direction"]

    if locale:
        setting.locale = locale

    if timezone:
        if timezone not in SUPPORTED_TIMEZONES:
            # Soft fallback or validation
            setting.timezone = timezone
        else:
            setting.timezone = timezone

    if date_format:
        if date_format not in SUPPORTED_DATE_FORMATS:
            raise ValueError(f"Date format '{date_format}' is not supported.")
        setting.date_format = date_format

    if time_format:
        if time_format not in ["12h", "24h"]:
            raise ValueError(f"Time format '{time_format}' must be '12h' or '24h'.")
        setting.time_format = time_format

    if week_start is not None:
        setting.week_start = week_start

    if currency:
        curr_match = next((c for c in SUPPORTED_CURRENCIES if c["code"] == currency.upper()), None)
        if not curr_match:
            raise ValueError(f"Currency '{currency}' is not supported.")
        setting.currency = curr_match["code"]

    if number_format:
        setting.number_format = number_format

    if direction:
        setting.direction = direction.lower()

    db.commit()
    db.refresh(setting)
    return setting
