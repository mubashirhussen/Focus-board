from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.regional import (
    UserRegionalSettingResponse,
    UserRegionalSettingUpdate,
    SupportedLocalesResponse,
)
from app.services import regional_service

router = APIRouter(prefix="/regional", tags=["Global SaaS & Regional Settings"])

@router.get("/settings", response_model=UserRegionalSettingResponse)
def get_user_regional_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the user's localized preferences (language, timezone, date/time format, currency, RTL)."""
    settings = regional_service.get_or_create_regional_settings(db, current_user.id)
    return UserRegionalSettingResponse(
        language=settings.language,
        locale=settings.locale,
        timezone=settings.timezone,
        date_format=settings.date_format,
        time_format=settings.time_format,
        week_start=settings.week_start,
        currency=settings.currency,
        number_format=settings.number_format,
        direction=settings.direction,
        updated_at=settings.updated_at,
    )

@router.put("/settings", response_model=UserRegionalSettingResponse)
@router.patch("/settings", response_model=UserRegionalSettingResponse)
def update_user_regional_settings(
    payload: UserRegionalSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update global localization preferences with strict validation."""
    try:
        updated = regional_service.update_regional_settings(
            db=db,
            user_id=current_user.id,
            language=payload.language,
            locale=payload.locale,
            timezone=payload.timezone,
            date_format=payload.date_format,
            time_format=payload.time_format,
            week_start=payload.week_start,
            currency=payload.currency,
            number_format=payload.number_format,
            direction=payload.direction,
        )
        return UserRegionalSettingResponse(
            language=updated.language,
            locale=updated.locale,
            timezone=updated.timezone,
            date_format=updated.date_format,
            time_format=updated.time_format,
            week_start=updated.week_start,
            currency=updated.currency,
            number_format=updated.number_format,
            direction=updated.direction,
            updated_at=updated.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/locales", response_model=SupportedLocalesResponse)
def get_supported_locales():
    """List all officially supported platform languages, currencies, and IANA timezones."""
    return SupportedLocalesResponse(
        languages=regional_service.SUPPORTED_LANGUAGES,
        currencies=regional_service.SUPPORTED_CURRENCIES,
        timezones=regional_service.SUPPORTED_TIMEZONES,
        date_formats=regional_service.SUPPORTED_DATE_FORMATS,
    )
