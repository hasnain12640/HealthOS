from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.core.dates import today_iso
from app.api.deps import get_current_profile
from app.models.models import (
    HealthProfile, LabReport, Biomarker,
    HydrationLog, NutritionLog, SleepLog, ActivityLog, TimelineEvent,
)
from app.services.deterministic.health_calculations import (
    calculate_bmi,
    calculate_hydration_target,
    calculate_avg_sleep,
    calculate_hydration_today,
    calculate_nutrition_today,
    generate_health_priorities,
)

router = APIRouter()


@router.get("")
def get_dashboard(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    profile_id = profile.id
    today = today_iso()

    # --- Body metrics ---
    bmi_data = calculate_bmi(profile.weight_kg, profile.height_cm)
    hydration_target = calculate_hydration_target(profile.weight_kg)

    # --- Lab data ---
    reports = db.query(LabReport).filter(LabReport.profile_id == profile_id).order_by(desc(LabReport.report_date)).all()
    latest_report = reports[0] if reports else None
    biomarkers = []
    if latest_report:
        biomarkers = db.query(Biomarker).filter(Biomarker.report_id == latest_report.id).all()

    # --- Lifestyle logs ---
    hydration_logs = db.query(HydrationLog).filter(HydrationLog.profile_id == profile_id).all()
    nutrition_logs = db.query(NutritionLog).filter(NutritionLog.profile_id == profile_id).all()
    sleep_logs = db.query(SleepLog).filter(SleepLog.profile_id == profile_id).order_by(SleepLog.date.desc()).limit(7).all()
    activity_logs = db.query(ActivityLog).filter(ActivityLog.profile_id == profile_id).order_by(ActivityLog.date.desc()).limit(5).all()

    # --- Deterministic calculations ---
    hydration_today = calculate_hydration_today(hydration_logs, today)
    nutrition_today = calculate_nutrition_today(nutrition_logs, today)
    avg_sleep = calculate_avg_sleep(sleep_logs)

    # --- Health priorities ---
    priorities = generate_health_priorities(
        biomarkers=biomarkers,
        hydration_ml=hydration_today,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
    )

    # --- Timeline ---
    timeline = db.query(TimelineEvent).filter(
        TimelineEvent.profile_id == profile_id
    ).order_by(TimelineEvent.date.desc()).all()

    return {
        "profile": {
            "id": profile.id,
            "user_name": profile.user_name,
            "age": profile.age,
            "sex": profile.sex,
            "city": profile.city,
            "language": profile.language,
            "bmi": bmi_data["bmi"],
            "bmi_category": bmi_data["category"],
        },
        "lab_summary": {
            "report_id": latest_report.id if latest_report else None,
            "lab_name": latest_report.lab_name if latest_report else None,
            "report_date": latest_report.report_date if latest_report else None,
            "total_biomarkers": len(biomarkers),
            "abnormal_count": sum(1 for b in biomarkers if b.status != "normal"),
            "biomarkers": [
                {
                    "id": b.id,
                    "name": b.name,
                    "value": b.value,
                    "unit": b.unit,
                    "reference_low": b.reference_low,
                    "reference_high": b.reference_high,
                    "status": b.status,
                    "category": b.category,
                }
                for b in biomarkers
            ],
        },
        "hydration": {
            "today_ml": hydration_today,
            "target_ml": hydration_target,
            "percent": round(hydration_today / hydration_target * 100) if hydration_target > 0 else 0,
            "logs": [
                {"id": h.id, "amount_ml": h.amount_ml, "source": h.source, "date": h.date}
                for h in hydration_logs if h.date == today
            ],
        },
        "nutrition": {
            **nutrition_today,
            "meals": [
                {
                    "id": n.id,
                    "meal_type": n.meal_type,
                    "food_name": n.food_name,
                    "calories": n.calories,
                    "protein_g": n.protein_g,
                    "is_pakistani_food": n.is_pakistani_food,
                }
                for n in nutrition_logs if n.date == today
            ],
        },
        "sleep": {
            "avg_hours": avg_sleep,
            "target_hours": 7.0,
            "logs": [
                {"date": s.date, "hours_slept": s.hours_slept, "quality": s.quality}
                for s in sleep_logs
            ],
        },
        "activity": {
            "recent": [
                {
                    "id": a.id,
                    "date": a.date,
                    "activity_type": a.activity_type,
                    "duration_min": a.duration_min,
                    "steps": a.steps,
                }
                for a in activity_logs
            ]
        },
        "priorities": priorities,
        "timeline": [
            {
                "id": t.id,
                "date": t.date,
                "event_type": t.event_type,
                "title": t.title,
                "description": t.description,
                "is_ai_generated": t.is_ai_generated,
            }
            for t in timeline
        ],
        "ai_insight": {
            "text": "Based on your lab results and lifestyle data, your fatigue may be related to low hemoglobin, Vitamin D deficiency, and insufficient sleep. These findings can have multiple explanations. Consider discussing your results with a qualified healthcare professional.",
            "generated_by": "mock",
            "date": today,
        },
    }
