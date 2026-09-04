import logging
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.dates import today_iso
from app.api.deps import get_current_profile
from app.models.models import HealthProfile, LabReport, Biomarker, HydrationLog, SleepLog
from app.services.ai.provider_factory import get_provider
from app.services.ai.insights_builder import build_insight_prompt, get_mock_insight
from app.services.deterministic.health_calculations import (
    calculate_hydration_target,
    calculate_hydration_today,
    calculate_avg_sleep,
    generate_health_priorities,
    assess_hydration,
)

logger = logging.getLogger("healthos.insights")

router = APIRouter()


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

    hydration_target = calculate_hydration_target(profile.weight_kg)
    hydration_ml = calculate_hydration_today(hydration_logs, today)
    avg_sleep = calculate_avg_sleep(sleep_logs)
    hydration_info = assess_hydration(hydration_ml, hydration_target)

    priorities = generate_health_priorities(
        biomarkers=biomarkers,
        hydration_ml=hydration_ml,
        hydration_target=hydration_target,
        avg_sleep=avg_sleep,
    )

    system_prompt, user_message = build_insight_prompt(
        profile=profile,
        biomarkers=biomarkers,
        hydration_pct=hydration_info["percent"],
        avg_sleep=avg_sleep,
        priorities=priorities,
    )

    used_provider = settings.AI_PROVIDER
    if settings.AI_PROVIDER == "mock":
        text = get_mock_insight()
    else:
        try:
            provider = get_provider()
            text = await provider.chat(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=system_prompt,
            )
        except Exception as exc:
            logger.warning("Qwen insight failed (%s). Serving mock fallback.", exc)
            text = get_mock_insight()
            used_provider = "mock"

    return {
        "text": text.strip(),
        "provider": used_provider,
        "date": date.today().isoformat(),
    }
