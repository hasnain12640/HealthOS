from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_profile
from app.core.database import get_db
from app.models.models import HealthProfile
from app.services.history_service import build_history

router = APIRouter()


@router.get("")
def get_history(
    days: int = Query(30, ge=1, le=90, description="Number of days to include (1-90)"),
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    """Return a per-day health history for the authenticated profile."""
    return build_history(profile, db, days)
