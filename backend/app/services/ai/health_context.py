from sqlalchemy.orm import Session

from app.core.dates import today_iso
from app.models.models import ActivityLog, Biomarker, HealthProfile, HydrationLog, LabReport, NutritionLog, SleepLog
from app.services.ai.context_builder import build_system_prompt
from app.services.cycle import cycle_service
from app.services.deterministic.health_calculations import (
    assess_activity,
    assess_nutrition,
    calculate_avg_sleep,
    calculate_bmi,
    calculate_hydration_target,
    calculate_hydration_today,
    calculate_nutrition_today,
    generate_health_priorities,
)
from app.services.wearables import service as wearable_service


def build_health_system_prompt(profile: HealthProfile, db: Session) -> str:
    profile_id = profile.id
    today = today_iso()
    latest_report = (
        db.query(LabReport)
        .filter(LabReport.profile_id == profile_id)
        .order_by(LabReport.report_date.desc())
        .first()
    )
    biomarkers = (
        db.query(Biomarker).filter(Biomarker.report_id == latest_report.id).all()
        if latest_report else []
    )
    hydration_logs = db.query(HydrationLog).filter(HydrationLog.profile_id == profile_id).all()
    sleep_logs = (
        db.query(SleepLog)
        .filter(SleepLog.profile_id == profile_id)
        .order_by(SleepLog.date.desc())
        .limit(7)
        .all()
    )
    activity_logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.profile_id == profile_id)
        .order_by(ActivityLog.date.desc())
        .limit(7)
        .all()
    )
    nutrition_logs = db.query(NutritionLog).filter(NutritionLog.profile_id == profile_id).all()

    hydration_target = calculate_hydration_target(profile.weight_kg)
    hydration_ml = calculate_hydration_today(hydration_logs, today)
    avg_sleep = calculate_avg_sleep(sleep_logs)
    activity_info = assess_activity(activity_logs)
    bmi_data = calculate_bmi(profile.weight_kg, profile.height_cm)
    nutrition_today = calculate_nutrition_today(nutrition_logs, today)
    nutrition_assessment = assess_nutrition(profile.sex, profile.age, nutrition_today)
    priorities = generate_health_priorities(
        biomarkers=biomarkers,
        hydration_ml=hydration_ml,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
        nutrition=nutrition_today,
        activity_pct=activity_info["percent"],
        bmi_category=bmi_data["category"],
    )

    return build_system_prompt(
        profile=profile,
        biomarkers=biomarkers,
        latest_report=latest_report,
        hydration_ml=hydration_ml,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
        activity_minutes=activity_info["total_minutes"],
        priorities=priorities,
        bmi=bmi_data["bmi"],
        bmi_category=bmi_data["category"],
        nutrition=nutrition_today,
        nutrition_assessment=nutrition_assessment,
        wearable_summary=wearable_service.get_connected_summary(profile_id, db),
        cycle_summary=cycle_service.get_womens_health_summary(profile, db),
    )
