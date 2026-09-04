import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.config import settings
from app.core.dates import today_iso
from app.api.deps import get_current_profile
from app.models.models import HealthProfile, LabReport, Biomarker, HydrationLog, SleepLog, ActivityLog, NutritionLog
from app.services.ai.provider_factory import get_provider
from app.services.ai.mock_provider import MockProvider
from app.services.ai.context_builder import build_system_prompt
from app.services.deterministic.health_calculations import (
    calculate_bmi,
    calculate_hydration_target,
    calculate_hydration_today,
    calculate_avg_sleep,
    calculate_nutrition_today,
    assess_nutrition,
    generate_health_priorities,
    assess_activity,
)

logger = logging.getLogger("healthos.chat")

router = APIRouter()


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryItem] = []


class ChatResponse(BaseModel):
    reply: str
    provider: str


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    profile_id = profile.id
    today = today_iso()

    # Gather health context
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

    hydration_target = calculate_hydration_target(profile.weight_kg)
    hydration_ml = calculate_hydration_today(hydration_logs, today)
    avg_sleep = calculate_avg_sleep(sleep_logs)
    activity_info = assess_activity(activity_logs)

    bmi_data = calculate_bmi(profile.weight_kg, profile.height_cm)
    nutrition_logs = db.query(NutritionLog).filter(NutritionLog.profile_id == profile_id).all()
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

    system_prompt = build_system_prompt(
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
    )

    # Keep last 6 messages (3 exchanges) to bound token usage
    history = [{"role": h.role, "content": h.content} for h in body.history[-6:]]
    history.append({"role": "user", "content": body.message})

    provider_name = settings.AI_PROVIDER
    try:
        provider = get_provider()
        reply = await provider.chat(messages=history, system_prompt=system_prompt)
    except Exception as exc:
        if settings.AI_PROVIDER == "qwen":
            # Never hide a Qwen failure: log it and clearly label the fallback reply.
            logger.warning("Qwen chat failed (%s). Serving MockProvider fallback reply.", exc)
            try:
                fallback = MockProvider()
                reply = await fallback.chat(messages=history, system_prompt=system_prompt)
                provider_name = "mock"
            except Exception:
                raise HTTPException(
                    status_code=503,
                    detail="AI service temporarily unavailable. Please try again.",
                )
        else:
            raise HTTPException(
                status_code=503,
                detail="AI service temporarily unavailable. Please try again.",
            )

    return ChatResponse(reply=reply, provider=provider_name)
