import uuid
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import CycleSymptom, HealthProfile
from app.services.cycle.schemas import SymptomCreate

SYMPTOM_LABELS = {
    "cramps": "Cramps",
    "headache": "Headache",
    "bloating": "Bloating",
    "fatigue": "Fatigue",
    "mood_changes": "Mood changes",
    "breast_tenderness": "Breast tenderness",
    "acne": "Acne",
    "appetite_change": "Appetite change",
    "nausea": "Nausea",
    "back_pain": "Back pain",
    "other": "Other",
}


def _serialize(s: CycleSymptom) -> dict:
    return {
        "id": s.id,
        "date": s.date,
        "symptom_type": s.symptom_type,
        "severity": s.severity,
        "notes": s.notes,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def list_symptoms(profile_id: str, db: Session, limit: int = 50) -> list[dict]:
    symptoms = (
        db.query(CycleSymptom)
        .filter(CycleSymptom.profile_id == profile_id)
        .order_by(CycleSymptom.date.desc(), CycleSymptom.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_serialize(s) for s in symptoms]


def create_symptom(profile: HealthProfile, data: SymptomCreate, db: Session) -> dict:
    if date.fromisoformat(data.date) > date.today():
        raise HTTPException(status_code=422, detail="Symptom date cannot be in the future.")

    symptom = CycleSymptom(
        id=str(uuid.uuid4()),
        profile_id=profile.id,
        date=data.date,
        symptom_type=data.symptom_type,
        severity=data.severity,
        notes=data.notes,
    )
    db.add(symptom)

    from app.services.cycle.cycle_service import _timeline_event
    label = SYMPTOM_LABELS.get(data.symptom_type, data.symptom_type.replace("_", " ").title())
    _timeline_event(
        db, profile.id, data.date, "cycle_symptom", "Symptom logged",
        f"{label} ({data.severity})",
    )
    db.commit()
    db.refresh(symptom)
    return _serialize(symptom)


def delete_symptom(profile_id: str, symptom_id: str, db: Session) -> dict:
    symptom = (
        db.query(CycleSymptom)
        .filter(CycleSymptom.id == symptom_id, CycleSymptom.profile_id == profile_id)
        .first()
    )
    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found.")
    db.delete(symptom)
    db.commit()
    return {"deleted": True, "id": symptom_id}
