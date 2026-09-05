from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_profile
from app.core.database import get_db
from app.models.models import NutritionLog, HydrationLog, SleepLog, ActivityLog, HealthProfile
from app.services import lifestyle as lifestyle_service

router = APIRouter()


# ── Nutrition ─────────────────────────────────────────────────────────────────

class NutritionLogCreate(BaseModel):
    date: str
    meal_type: str
    food_name: str
    quantity_g: int = 0
    calories: int = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    is_pakistani_food: bool = True


class NutritionLogOut(BaseModel):
    id: str
    profile_id: str
    date: str
    meal_type: str
    food_name: str
    quantity_g: int
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    is_pakistani_food: bool

    class Config:
        from_attributes = True


@router.post("/nutrition", response_model=NutritionLogOut, status_code=201)
def log_nutrition(
    data: NutritionLogCreate,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return lifestyle_service.create_nutrition(
        profile.id,
        **data.model_dump(),
        db=db,
    )


@router.get("/nutrition", response_model=list[NutritionLogOut])
def get_nutrition(
    date: Optional[str] = None,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    q = db.query(NutritionLog).filter(NutritionLog.profile_id == profile.id)
    if date:
        q = q.filter(NutritionLog.date == date)
    return q.order_by(NutritionLog.date.desc()).all()


# ── Hydration ─────────────────────────────────────────────────────────────────

class HydrationLogCreate(BaseModel):
    date: str
    amount_ml: int
    source: str = "water"


class HydrationLogOut(BaseModel):
    id: str
    profile_id: str
    date: str
    amount_ml: int
    source: str

    class Config:
        from_attributes = True


@router.post("/hydration", response_model=HydrationLogOut, status_code=201)
def log_hydration(
    data: HydrationLogCreate,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return lifestyle_service.create_hydration(
        profile.id,
        **data.model_dump(),
        db=db,
    )


@router.get("/hydration", response_model=list[HydrationLogOut])
def get_hydration(
    date: Optional[str] = None,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    q = db.query(HydrationLog).filter(HydrationLog.profile_id == profile.id)
    if date:
        q = q.filter(HydrationLog.date == date)
    return q.order_by(HydrationLog.date.desc()).all()


# ── Sleep ─────────────────────────────────────────────────────────────────────

class SleepLogCreate(BaseModel):
    date: str
    hours_slept: float
    quality: int = 3


class SleepLogOut(BaseModel):
    id: str
    profile_id: str
    date: str
    hours_slept: float
    quality: int

    class Config:
        from_attributes = True


@router.post("/sleep", response_model=SleepLogOut, status_code=201)
def log_sleep(
    data: SleepLogCreate,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return lifestyle_service.create_sleep(
        profile.id,
        **data.model_dump(),
        db=db,
    )


@router.get("/sleep", response_model=list[SleepLogOut])
def get_sleep(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return (db.query(SleepLog)
            .filter(SleepLog.profile_id == profile.id)
            .order_by(SleepLog.date.desc())
            .limit(14).all())


# ── Activity ──────────────────────────────────────────────────────────────────

class ActivityLogCreate(BaseModel):
    date: str
    activity_type: str
    duration_min: int = 0
    steps: int = 0
    notes: str = ""


class ActivityLogOut(BaseModel):
    id: str
    profile_id: str
    date: str
    activity_type: str
    duration_min: int
    steps: int
    notes: str

    class Config:
        from_attributes = True


@router.post("/activity", response_model=ActivityLogOut, status_code=201)
def log_activity(
    data: ActivityLogCreate,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return lifestyle_service.create_activity(
        profile.id,
        **data.model_dump(),
        db=db,
    )


@router.get("/activity", response_model=list[ActivityLogOut])
def get_activity(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return (db.query(ActivityLog)
            .filter(ActivityLog.profile_id == profile.id)
            .order_by(ActivityLog.date.desc())
            .limit(14).all())
