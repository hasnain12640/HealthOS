import uuid
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Cycle, PeriodDay, CycleSymptom, TimelineEvent, HealthProfile
from app.services.cycle import cycle_engine
from app.services.cycle.schemas import CycleCreate, CycleEndRequest


def _timeline_event(db: Session, profile_id: str, event_date: str, event_type: str, title: str, description: str = "") -> None:
    existing = (
        db.query(TimelineEvent)
        .filter(
            TimelineEvent.profile_id == profile_id,
            TimelineEvent.date == event_date,
            TimelineEvent.event_type == event_type,
            TimelineEvent.title == title,
        )
        .first()
    )
    if existing:
        existing.description = description
        return
    db.add(TimelineEvent(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        date=event_date,
        event_type=event_type,
        title=title,
        description=description,
        is_ai_generated=False,
    ))


def _cycle_to_engine_dict(cycle: Cycle) -> dict:
    return {
        "start_date": cycle.start_date,
        "end_date": cycle.end_date,
        "cycle_length": cycle.cycle_length,
        "period_length": cycle.period_length,
        "period_days": [p.date for p in cycle.period_days],
        "period_day_records": [{"date": p.date, "flow_level": p.flow_level} for p in cycle.period_days],
    }


def _serialize_cycle(cycle: Cycle) -> dict:
    return {
        "id": cycle.id,
        "start_date": cycle.start_date,
        "end_date": cycle.end_date,
        "cycle_length": cycle.cycle_length,
        "period_length": cycle.period_length,
        "notes": cycle.notes,
        "created_at": cycle.created_at.isoformat() if cycle.created_at else None,
        "period_days": [
            {"date": p.date, "flow_level": p.flow_level} for p in cycle.period_days
        ],
    }


def get_cycles(profile_id: str, db: Session) -> list[dict]:
    cycles = (
        db.query(Cycle)
        .filter(Cycle.profile_id == profile_id)
        .order_by(Cycle.start_date.desc())
        .all()
    )
    return [_serialize_cycle(c) for c in cycles]


def get_cycle_by_id(profile_id: str, cycle_id: str, db: Session) -> Cycle:
    cycle = (
        db.query(Cycle)
        .filter(Cycle.id == cycle_id, Cycle.profile_id == profile_id)
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found.")
    return cycle


def create_cycle(profile: HealthProfile, data: CycleCreate, db: Session) -> dict:
    start = date.fromisoformat(data.start_date)
    if start > date.today():
        raise HTTPException(status_code=422, detail="Start date cannot be in the future.")

    latest = (
        db.query(Cycle)
        .filter(Cycle.profile_id == profile.id)
        .order_by(Cycle.start_date.desc())
        .first()
    )
    if latest:
        latest_start = date.fromisoformat(latest.start_date)
        if start <= latest_start:
            raise HTTPException(
                status_code=422,
                detail="Start date must be after your most recent cycle's start date.",
            )
        if latest.end_date is None:
            latest.end_date = data.start_date
            latest.cycle_length = (start - latest_start).days

    cycle = Cycle(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        start_date=data.start_date,
        period_length=data.period_length,
        notes=data.notes,
    )
    db.add(cycle)
    db.flush()

    period_length = data.period_length or cycle_engine.DEFAULT_PERIOD_LENGTH
    for i in range(period_length):
        db.add(PeriodDay(
            id=str(uuid.uuid4()),
            cycle_id=cycle.id,
            date=date.fromordinal(start.toordinal() + i).isoformat(),
            flow_level=None,
        ))

    _timeline_event(
        db, profile.id, data.start_date, "cycle", "Period started",
        f"New cycle started ({period_length} day period logged).",
    )
    db.commit()
    db.refresh(cycle)
    return _serialize_cycle(cycle)


def end_cycle(profile: HealthProfile, cycle_id: str, data: CycleEndRequest, db: Session) -> dict:
    cycle = get_cycle_by_id(profile.id, cycle_id, db)
    if cycle.end_date is not None:
        raise HTTPException(status_code=422, detail="This cycle is already ended.")
    end = date.fromisoformat(data.end_date)
    start = date.fromisoformat(cycle.start_date)
    if end < start:
        raise HTTPException(status_code=422, detail="End date cannot be before the start date.")
    if end > date.today():
        raise HTTPException(status_code=422, detail="End date cannot be in the future.")

    cycle.end_date = data.end_date
    cycle.cycle_length = (end - start).days
    _timeline_event(
        db, profile.id, data.end_date, "cycle", "Cycle ended",
        f"Cycle ended after {cycle.cycle_length} days.",
    )
    db.commit()
    db.refresh(cycle)
    return _serialize_cycle(cycle)


def get_current(profile_id: str, db: Session) -> dict:
    cycles = (
        db.query(Cycle)
        .filter(Cycle.profile_id == profile_id)
        .order_by(Cycle.start_date.desc())
        .all()
    )
    analysis = cycle_engine.analyze_cycles([_cycle_to_engine_dict(c) for c in cycles])
    return {
        "cycle": _serialize_cycle(cycles[0]) if cycles else None,
        "prediction": analysis,
    }


def get_prediction(profile_id: str, db: Session) -> dict:
    cycles = (
        db.query(Cycle)
        .filter(Cycle.profile_id == profile_id)
        .order_by(Cycle.start_date.desc())
        .all()
    )
    return cycle_engine.analyze_cycles([_cycle_to_engine_dict(c) for c in cycles])


def get_calendar(profile_id: str, year: int, month: int, db: Session) -> dict:
    if not (1 <= month <= 12):
        raise HTTPException(status_code=422, detail="Month must be 1-12.")
    if not (2000 <= year <= 2100):
        raise HTTPException(status_code=422, detail="Year out of range.")

    cycles = db.query(Cycle).filter(Cycle.profile_id == profile_id).all()
    symptoms = (
        db.query(CycleSymptom)
        .filter(CycleSymptom.profile_id == profile_id)
        .all()
    )
    return cycle_engine.calendar_month(
        [_cycle_to_engine_dict(c) for c in cycles],
        [{"date": s.date, "symptom_type": s.symptom_type} for s in symptoms],
        year, month,
    )


def get_womens_health_summary(profile: HealthProfile, db: Session) -> dict | None:
    """Compact summary for the dashboard card + AI context. Female profiles only."""
    if profile.sex != "female":
        return None
    cycles = (
        db.query(Cycle)
        .filter(Cycle.profile_id == profile.id)
        .order_by(Cycle.start_date.desc())
        .all()
    )
    analysis = cycle_engine.analyze_cycles([_cycle_to_engine_dict(c) for c in cycles])
    symptoms = (
        db.query(CycleSymptom)
        .filter(CycleSymptom.profile_id == profile.id)
        .order_by(CycleSymptom.date.desc())
        .limit(5)
        .all()
    )
    return {
        "cycles_tracked": analysis.get("cycles_tracked", 0),
        "current_cycle_day": analysis.get("current_cycle_day"),
        "current_phase": analysis.get("current_phase"),
        "average_cycle_length": analysis.get("average_cycle_length"),
        "average_period_length": analysis.get("average_period_length"),
        "predicted_period_start": analysis.get("predicted_period_start"),
        "estimated_fertile_start": analysis.get("estimated_fertile_start"),
        "estimated_fertile_end": analysis.get("estimated_fertile_end"),
        "needs_more_data": analysis.get("needs_more_data", True),
        "recent_symptoms": [
            {"date": s.date, "symptom_type": s.symptom_type, "severity": s.severity}
            for s in symptoms
        ],
    }
