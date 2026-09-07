from datetime import date as date_type
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_profile
from app.core.database import get_db
from app.models.models import ActivityLog, HealthProfile, HydrationLog, NutritionLog, SleepLog
from app.services import lifestyle as lifestyle_service

router = APIRouter()


class DatedLogCreate(BaseModel):
    date: str = Field(min_length=10, max_length=10)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        try:
            parsed = date_type.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Please provide a valid date in YYYY-MM-DD format.") from exc
        if parsed > date_type.today():
            raise ValueError("Date cannot be in the future.")
        return value


class NutritionLogCreate(DatedLogCreate):
    meal_type: Literal["breakfast", "lunch", "dinner", "snack", "meal", "other"]
    food_name: str = Field(max_length=200)
    quantity_g: int = Field(default=0, ge=0, le=10000)
    calories: int = Field(default=0, ge=0, le=10000)
    protein_g: float = Field(default=0, ge=0, le=1000)
    carbs_g: float = Field(default=0, ge=0, le=1000)
    fat_g: float = Field(default=0, ge=0, le=1000)
    is_pakistani_food: bool = True

    @field_validator("food_name")
    @classmethod
    def validate_food_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Food name cannot be empty.")
        return value


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
        timeline_event=lifestyle_service.TimelineEventInput(
            event_type="nutrition",
            title=f"Meal logged — {data.food_name}",
            description=f"Manual entry · {data.meal_type} · {data.calories} kcal",
        ),
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


class HydrationLogCreate(DatedLogCreate):
    amount_ml: int = Field(ge=1, le=5000)
    source: str = Field(default="water", max_length=50)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Source cannot be empty.")
        return value


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
        timeline_event=lifestyle_service.TimelineEventInput(
            event_type="hydration",
            title=f"Water logged — {data.amount_ml} ml",
            description="Manual entry",
        ),
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


class SleepLogCreate(DatedLogCreate):
    hours_slept: float = Field(ge=0.5, le=24)
    quality: int = Field(default=3, ge=1, le=5)


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
        timeline_event=lifestyle_service.TimelineEventInput(
            event_type="sleep",
            title=f"Sleep logged — {data.hours_slept:g} hours",
            description=f"Manual entry · Quality {data.quality}/5",
        ),
        db=db,
    )


@router.get("/sleep", response_model=list[SleepLogOut])
def get_sleep(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return (
        db.query(SleepLog)
        .filter(SleepLog.profile_id == profile.id)
        .order_by(SleepLog.date.desc())
        .limit(14)
        .all()
    )


class ActivityLogCreate(DatedLogCreate):
    activity_type: str = Field(max_length=100)
    duration_min: int = Field(default=0, ge=0, le=1440)
    steps: int = Field(default=0, ge=0, le=100000)
    notes: str = Field(default="", max_length=500)

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Activity type cannot be empty.")
        return value

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_activity_amount(self):
        if self.duration_min == 0 and self.steps == 0:
            raise ValueError("Enter duration, steps, or both.")
        return self


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
    details = []
    if data.duration_min:
        details.append(f"{data.duration_min} minutes")
    if data.steps:
        details.append(f"{data.steps:,} steps")
    return lifestyle_service.create_activity(
        profile.id,
        **data.model_dump(),
        timeline_event=lifestyle_service.TimelineEventInput(
            event_type="activity",
            title=f"Activity logged — {data.activity_type}",
            description=f"Manual entry · {' · '.join(details)}",
        ),
        db=db,
    )


@router.get("/activity", response_model=list[ActivityLogOut])
def get_activity(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.profile_id == profile.id)
        .order_by(ActivityLog.date.desc())
        .limit(14)
        .all()
    )
