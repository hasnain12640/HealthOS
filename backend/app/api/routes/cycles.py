from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_profile
from app.models.models import HealthProfile
from app.services.cycle import cycle_service, symptom_service
from app.services.cycle.schemas import (
    CycleCreate, CycleEndRequest, SymptomCreate,
    CycleOut, PredictionOut, CalendarOut, SymptomOut,
)

router = APIRouter()


def require_female(profile: HealthProfile = Depends(get_current_profile)) -> HealthProfile:
    """Women's Health data is only served to profiles registered as female."""
    if profile.sex != "female":
        raise HTTPException(
            status_code=403,
            detail="Women's Health features are only available for female profiles.",
        )
    return profile


@router.get("/cycles", response_model=list[CycleOut])
def list_cycles(
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return cycle_service.get_cycles(profile.id, db)


@router.post("/cycles", response_model=CycleOut, status_code=201)
def create_cycle(
    data: CycleCreate,
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return cycle_service.create_cycle(profile, data, db)


@router.get("/cycles/current")
def get_current_cycle(
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return cycle_service.get_current(profile.id, db)


@router.get("/cycles/current/prediction", response_model=PredictionOut)
def get_current_prediction(
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return cycle_service.get_prediction(profile.id, db)


@router.get("/cycles/calendar", response_model=CalendarOut)
def get_calendar(
    year: int,
    month: int,
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return cycle_service.get_calendar(profile.id, year, month, db)


@router.post("/cycles/{cycle_id}/end", response_model=CycleOut)
def end_cycle(
    cycle_id: str,
    data: CycleEndRequest,
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return cycle_service.end_cycle(profile, cycle_id, data, db)


@router.get("/cycle-symptoms", response_model=list[SymptomOut])
def list_symptoms(
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return symptom_service.list_symptoms(profile.id, db)


@router.post("/cycle-symptoms", response_model=SymptomOut, status_code=201)
def create_symptom(
    data: SymptomCreate,
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return symptom_service.create_symptom(profile, data, db)


@router.delete("/cycle-symptoms/{symptom_id}")
def delete_symptom(
    symptom_id: str,
    profile: HealthProfile = Depends(require_female),
    db: Session = Depends(get_db),
):
    return symptom_service.delete_symptom(profile.id, symptom_id, db)
