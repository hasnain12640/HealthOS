import json
import logging
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.dates import today_iso
from app.api.deps import get_current_profile
from app.models.models import HealthProfile, LabReport, Biomarker, HydrationLog, SleepLog, ActivityLog
from app.services.ai.provider_factory import get_provider
from app.services.ai.plan_builder import build_plan_prompt, get_mock_plan
from app.services.deterministic.health_calculations import (
    calculate_hydration_target,
    calculate_hydration_today,
    calculate_avg_sleep,
    generate_health_priorities,
    assess_activity,
    assess_hydration,
)

logger = logging.getLogger("healthos.plan")

router = APIRouter()


@router.post("")
async def generate_plan(
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

    hydration_target = calculate_hydration_target(profile.weight_kg)
    hydration_ml = calculate_hydration_today(hydration_logs, today)
    avg_sleep = calculate_avg_sleep(sleep_logs)
    activity_info = assess_activity(activity_logs)
    hydration_info = assess_hydration(hydration_ml, hydration_target)

    priorities = generate_health_priorities(
        biomarkers=biomarkers,
        hydration_ml=hydration_ml,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
        activity_pct=activity_info["percent"],
    )

    system_prompt, user_message = build_plan_prompt(
        profile=profile,
        biomarkers=biomarkers,
        latest_report=latest_report,
        hydration_pct=hydration_info["percent"],
        avg_sleep=avg_sleep,
        activity_pct=activity_info["percent"],
        priorities=priorities,
    )

    used_provider = settings.AI_PROVIDER
    if settings.AI_PROVIDER == "mock":
        plan_data = get_mock_plan()
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
            plan_data = json.loads(clean)
        except Exception as exc:
            logger.warning("Qwen plan generation failed (%s). Serving mock fallback.", exc)
            plan_data = get_mock_plan()
            used_provider = "mock"

    return {
        "plan": plan_data,
        "provider": used_provider,
        "generated_at": date.today().isoformat(),
    }
