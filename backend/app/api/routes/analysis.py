from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dates import today_iso
from app.api.deps import get_current_profile
from app.models.models import (
    HealthProfile, Biomarker, LabReport,
    HydrationLog, NutritionLog, SleepLog, ActivityLog,
)
from app.services.deterministic.health_calculations import (
    calculate_bmi,
    calculate_hydration_target,
    calculate_hydration_today,
    calculate_avg_sleep,
    calculate_nutrition_today,
    assess_hydration,
    assess_sleep,
    assess_activity,
    assess_nutrition,
    generate_health_priorities,
)

router = APIRouter()


@router.get("")
def get_analysis(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    profile_id = profile.id
    today = today_iso()

    # --- Body metrics ---
    bmi_data = calculate_bmi(profile.weight_kg, profile.height_cm)
    hydration_target = calculate_hydration_target(profile.weight_kg)

    # --- Latest lab biomarkers ---
    latest_report = (db.query(LabReport)
                     .filter(LabReport.profile_id == profile_id)
                     .order_by(LabReport.report_date.desc())
                     .first())
    biomarkers = []
    if latest_report:
        biomarkers = db.query(Biomarker).filter(Biomarker.report_id == latest_report.id).all()

    # --- Lifestyle ---
    hydration_logs = db.query(HydrationLog).filter(HydrationLog.profile_id == profile_id).all()
    nutrition_logs = db.query(NutritionLog).filter(NutritionLog.profile_id == profile_id).all()
    sleep_logs = (db.query(SleepLog).filter(SleepLog.profile_id == profile_id)
                  .order_by(SleepLog.date.desc()).limit(7).all())
    activity_logs = (db.query(ActivityLog).filter(ActivityLog.profile_id == profile_id)
                     .order_by(ActivityLog.date.desc()).limit(7).all())

    # --- Calculations ---
    hydration_today = calculate_hydration_today(hydration_logs, today)
    nutrition_today = calculate_nutrition_today(nutrition_logs, today)
    avg_sleep = calculate_avg_sleep(sleep_logs)

    hydration_assessment = assess_hydration(hydration_today, hydration_target)
    sleep_assessment = assess_sleep(avg_sleep)
    activity_assessment = assess_activity(activity_logs)
    nutrition_assessment = assess_nutrition(profile.sex, profile.age, nutrition_today)

    # --- Full priority list ---
    priorities = generate_health_priorities(
        biomarkers=biomarkers,
        hydration_ml=hydration_today,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
        nutrition=nutrition_today,
        activity_pct=activity_assessment["percent"],
        bmi_category=bmi_data["category"],
    )

    return {
        "profile_id": profile_id,
        "body_metrics": {
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            **bmi_data,
        },
        "hydration": {
            "today_ml": hydration_today,
            "target_ml": hydration_target,
            **hydration_assessment,
            "logs_today": [
                {"id": h.id, "amount_ml": h.amount_ml, "source": h.source}
                for h in hydration_logs if h.date == today
            ],
            "weekly_avg_ml": round(
                sum(h.amount_ml for h in hydration_logs) / 7
            ) if hydration_logs else 0,
        },
        "nutrition": {
            **nutrition_today,
            **nutrition_assessment,
            "meals_today": [
                {
                    "id": n.id, "meal_type": n.meal_type,
                    "food_name": n.food_name, "calories": n.calories,
                    "protein_g": n.protein_g, "carbs_g": n.carbs_g,
                    "fat_g": n.fat_g, "is_pakistani_food": n.is_pakistani_food,
                }
                for n in nutrition_logs if n.date == today
            ],
        },
        "sleep": {
            "avg_hours": avg_sleep,
            **sleep_assessment,
            "logs": [
                {"date": s.date, "hours_slept": s.hours_slept, "quality": s.quality}
                for s in sleep_logs
            ],
        },
        "activity": {
            **activity_assessment,
            "recent": [
                {
                    "id": a.id, "date": a.date,
                    "activity_type": a.activity_type,
                    "duration_min": a.duration_min,
                    "steps": a.steps,
                    "notes": a.notes,
                }
                for a in activity_logs
            ],
        },
        "biomarkers": {
            "total": len(biomarkers),
            "abnormal": sum(1 for b in biomarkers if b.status != "normal"),
            "report_id": latest_report.id if latest_report else None,
            "report_date": latest_report.report_date if latest_report else None,
        },
        "priorities": priorities,
        "priority_count": len(priorities),
    }
