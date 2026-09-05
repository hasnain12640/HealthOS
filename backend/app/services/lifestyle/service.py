import uuid

from sqlalchemy.orm import Session

from app.models.models import ActivityLog, HydrationLog, NutritionLog, SleepLog


def create_nutrition(
    profile_id: str,
    *,
    date: str,
    meal_type: str,
    food_name: str,
    quantity_g: int = 0,
    calories: int = 0,
    protein_g: float = 0,
    carbs_g: float = 0,
    fat_g: float = 0,
    is_pakistani_food: bool = True,
    db: Session,
) -> NutritionLog:
    entry = NutritionLog(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=date,
        meal_type=meal_type,
        food_name=food_name,
        quantity_g=quantity_g,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        is_pakistani_food=is_pakistani_food,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_hydration(
    profile_id: str,
    *,
    date: str,
    amount_ml: int,
    source: str = "water",
    db: Session,
) -> HydrationLog:
    entry = HydrationLog(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=date,
        amount_ml=amount_ml,
        source=source,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_sleep(
    profile_id: str,
    *,
    date: str,
    hours_slept: float,
    quality: int = 3,
    db: Session,
) -> SleepLog:
    entry = SleepLog(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=date,
        hours_slept=hours_slept,
        quality=quality,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_activity(
    profile_id: str,
    *,
    date: str,
    activity_type: str,
    duration_min: int = 0,
    steps: int = 0,
    notes: str = "",
    db: Session,
) -> ActivityLog:
    entry = ActivityLog(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=date,
        activity_type=activity_type,
        duration_min=duration_min,
        steps=steps,
        notes=notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
