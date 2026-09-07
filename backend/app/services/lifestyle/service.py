import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.models import ActivityLog, HydrationLog, NutritionLog, SleepLog, TimelineEvent


@dataclass(frozen=True)
class TimelineEventInput:
    event_type: str
    title: str
    description: str
    deduplicate: bool = False


def _add_timeline_event(
    db: Session,
    profile_id: str,
    date: str,
    timeline_event: TimelineEventInput,
) -> None:
    if timeline_event.deduplicate:
        event = (
            db.query(TimelineEvent)
            .filter(
                TimelineEvent.profile_id == profile_id,
                TimelineEvent.date == date,
                TimelineEvent.event_type == timeline_event.event_type,
                TimelineEvent.title == timeline_event.title,
            )
            .first()
        )
        if event:
            event.description = timeline_event.description
            return

    db.add(
        TimelineEvent(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            date=date,
            event_type=timeline_event.event_type,
            title=timeline_event.title,
            description=timeline_event.description,
            is_ai_generated=False,
        )
    )


def _save_entry(
    db: Session,
    entry: NutritionLog | HydrationLog | SleepLog | ActivityLog,
    timeline_event: TimelineEventInput | None,
):
    db.add(entry)
    if timeline_event:
        _add_timeline_event(db, entry.profile_id, entry.date, timeline_event)
    db.commit()
    db.refresh(entry)
    return entry


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
    timeline_event: TimelineEventInput | None = None,
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
    return _save_entry(db, entry, timeline_event)


def create_hydration(
    profile_id: str,
    *,
    date: str,
    amount_ml: int,
    source: str = "water",
    timeline_event: TimelineEventInput | None = None,
    db: Session,
) -> HydrationLog:
    entry = HydrationLog(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=date,
        amount_ml=amount_ml,
        source=source,
    )
    return _save_entry(db, entry, timeline_event)


def create_sleep(
    profile_id: str,
    *,
    date: str,
    hours_slept: float,
    quality: int = 3,
    timeline_event: TimelineEventInput | None = None,
    db: Session,
) -> SleepLog:
    entry = SleepLog(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=date,
        hours_slept=hours_slept,
        quality=quality,
    )
    return _save_entry(db, entry, timeline_event)


def create_activity(
    profile_id: str,
    *,
    date: str,
    activity_type: str,
    duration_min: int = 0,
    steps: int = 0,
    notes: str = "",
    timeline_event: TimelineEventInput | None = None,
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
    return _save_entry(db, entry, timeline_event)
