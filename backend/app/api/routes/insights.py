import datetime
import json
import logging
from uuid import uuid4
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.dates import today_iso
from app.api.deps import get_current_profile
from app.models.models import (
    HealthProfile, LabReport, Biomarker, HydrationLog, SleepLog,
    NutritionLog, ActivityLog, TimelineEvent, InsightRecord,
)
from app.services.ai.provider_factory import get_provider
from app.services.ai.insights_builder import build_insight_prompt, get_mock_insight
from app.services.deterministic.health_calculations import (
    calculate_bmi,
    calculate_hydration_target,
    calculate_hydration_today,
    calculate_avg_sleep,
    calculate_nutrition_today,
    assess_nutrition,
    assess_activity,
    generate_health_priorities,
    assess_hydration,
)
from app.services.wearables import service as wearable_service
from app.services.cycle import cycle_service

logger = logging.getLogger("healthos.insights")

router = APIRouter()


def _insight_fingerprint(
    latest_report: LabReport | None,
    hydration_logs: list[HydrationLog],
    nutrition_logs: list[NutritionLog],
    activity_log_count: int,
    wearable_summary: dict | None,
    cycle_summary: dict | None = None,
) -> str:
    """
    Snapshot of every data source the insight is built from. Any change
    (new lab report, logged meal/water/activity, wearable sync, cycle or
    symptom log) produces a different fingerprint and forces regeneration.
    The wearable sync is captured through last_synced_at, so an insight is
    never older than the latest wearable sync.
    """
    cycle_part = "none"
    if cycle_summary:
        symptoms_part = ",".join(
            s["symptom_type"] for s in cycle_summary.get("recent_symptoms", [])
        )
        cycle_part = (
            f"{cycle_summary.get('cycles_tracked', 0)}:"
            f"{cycle_summary.get('current_cycle_day')}:{symptoms_part}"
        )
    return "|".join([
        f"labs:{latest_report.id if latest_report else 'none'}",
        f"hyd:{len(hydration_logs)}",
        f"nut:{len(nutrition_logs)}",
        f"act:{activity_log_count}",
        f"wear:{wearable_summary.get('last_synced_at') if wearable_summary else 'none'}",
        f"cyc:{cycle_part}",
    ])


@router.post("")
async def generate_insight(
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
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
        .order_by(SleepLog.date.desc()).limit(7).all()
    )
    activity_logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.profile_id == profile_id)
        .order_by(ActivityLog.date.desc()).limit(7).all()
    )
    nutrition_logs = db.query(NutritionLog).filter(NutritionLog.profile_id == profile_id).all()

    hydration_target = calculate_hydration_target(profile.weight_kg)
    hydration_ml = calculate_hydration_today(hydration_logs, today)
    avg_sleep = calculate_avg_sleep(sleep_logs)
    hydration_info = assess_hydration(hydration_ml, hydration_target)
    activity_info = assess_activity(activity_logs)
    nutrition_today = calculate_nutrition_today(nutrition_logs, today)
    nutrition_assessment = assess_nutrition(profile.sex, profile.age, nutrition_today)
    bmi_data = calculate_bmi(profile.weight_kg, profile.height_cm)

    priorities = generate_health_priorities(
        biomarkers=biomarkers,
        hydration_ml=hydration_ml,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
        nutrition=nutrition_today,
        activity_pct=activity_info["percent"],
        bmi_category=bmi_data["category"],
    )

    wearable_summary = wearable_service.get_connected_summary(profile_id, db)
    cycle_summary = cycle_service.get_womens_health_summary(profile, db)
    activity_log_count = (
        db.query(ActivityLog.id)
        .filter(ActivityLog.profile_id == profile_id)
        .count()
    )
    fingerprint = _insight_fingerprint(
        latest_report=latest_report,
        hydration_logs=hydration_logs,
        nutrition_logs=nutrition_logs,
        activity_log_count=activity_log_count,
        wearable_summary=wearable_summary,
        cycle_summary=cycle_summary,
    )

    cached = (
        db.query(InsightRecord)
        .filter(InsightRecord.profile_id == profile_id)
        .first()
    )
    if (
        cached
        and cached.generated_at.date() == datetime.date.today()
        and cached.fingerprint == fingerprint
    ):
        try:
            insight_data = json.loads(cached.insight_json)
        except json.JSONDecodeError:
            insight_data = None
        if insight_data is not None:
            logger.info("Serving cached insight generated at %s", cached.generated_at)
            return {
                "insight": insight_data,
                "text": insight_data.get("summary", ""),
                "provider": cached.provider,
                "date": cached.generated_at.date().isoformat(),
            }

    system_prompt, user_message = build_insight_prompt(
        profile=profile,
        biomarkers=biomarkers,
        hydration_pct=hydration_info["percent"],
        avg_sleep=avg_sleep,
        priorities=priorities,
        latest_report=latest_report,
        wearable_summary=wearable_summary,
        nutrition=nutrition_today,
        nutrition_assessment=nutrition_assessment,
        activity_pct=activity_info["percent"],
        bmi=bmi_data["bmi"],
        bmi_category=bmi_data["category"],
        cycle_summary=cycle_summary,
    )

    mock_kwargs = dict(
        profile=profile,
        biomarkers=biomarkers,
        hydration_pct=hydration_info["percent"],
        hydration_ml=hydration_ml,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
        priorities=priorities,
        wearable_summary=wearable_summary,
        nutrition=nutrition_today,
        activity_pct=activity_info["percent"],
        bmi=bmi_data["bmi"],
        bmi_category=bmi_data["category"],
        cycle_summary=cycle_summary,
    )

    used_provider = settings.AI_PROVIDER
    if settings.AI_PROVIDER == "mock":
        insight_data = get_mock_insight(**mock_kwargs)
    else:
        try:
            provider = get_provider()
            raw = await provider.chat(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=system_prompt,
            )
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1]
                clean = clean.rsplit("```", 1)[0]
            insight_data = json.loads(clean)
        except Exception as exc:
            logger.warning("Qwen insight failed (%s). Serving mock fallback.", exc)
            insight_data = get_mock_insight(**mock_kwargs)
            used_provider = "mock"

    reason = (
        "new" if cached is None
        else "day-changed" if cached.generated_at.date() != datetime.date.today()
        else "data-changed"
    )
    logger.info("Regenerating insight (provider=%s, reason=%s)", used_provider, reason)

    now = datetime.datetime.utcnow()
    if cached:
        cached.insight_json = json.dumps(insight_data)
        cached.provider = used_provider
        cached.fingerprint = fingerprint
        cached.generated_at = now
        cached.updated_at = now
    else:
        db.add(InsightRecord(
            id=str(uuid4()),
            profile_id=profile_id,
            insight_json=json.dumps(insight_data),
            provider=used_provider,
            fingerprint=fingerprint,
            generated_at=now,
            updated_at=now,
        ))

    headline = insight_data.get("headline", "Personalized health insight generated.")

    existing_event = (
        db.query(TimelineEvent)
        .filter(
            TimelineEvent.profile_id == profile_id,
            TimelineEvent.event_type == "ai_insight",
            TimelineEvent.date == today,
        )
        .first()
    )
    if existing_event:
        existing_event.description = headline
    else:
        db.add(TimelineEvent(
            id=str(uuid4()),
            profile_id=profile_id,
            date=today,
            event_type="ai_insight",
            title="AI Health Insight Generated",
            description=headline,
            is_ai_generated=True,
        ))

    db.commit()

    return {
        "insight": insight_data,
        "text": insight_data.get("summary", ""),
        "provider": used_provider,
        "date": today,
    }
