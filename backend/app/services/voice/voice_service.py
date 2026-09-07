import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dates import today_iso
from app.models.models import HealthProfile
from app.services import lifestyle as lifestyle_service
from app.services.ai.health_context import build_health_system_prompt
from app.services.ai.mock_provider import MockProvider
from app.services.ai.provider_factory import get_provider
from app.services.cycle import cycle_service, symptom_service
from app.services.cycle.schemas import CycleCreate, SymptomCreate
from app.services.voice.asr_provider import BaseASRProvider
from app.services.voice.intent_engine import (
    VoiceClarificationError,
    detect_language,
    parse_deterministic_intent,
    parse_qwen_intent,
    strip_leading_wake_name,
    uses_roman_urdu,
)
from app.services.voice.mock_asr_provider import MockASRProvider
from app.services.voice.mock_tts_provider import MockTTSProvider
from app.services.voice.qwen_asr_provider import QwenASRProvider
from app.services.voice.qwen_tts_provider import QwenTTSProvider
from app.services.voice.schemas import (
    ActivityIntent,
    CycleIntent,
    CycleQueryIntent,
    DetectedLanguage,
    HealthSummaryQueryIntent,
    HydrationIntent,
    HydrationQueryIntent,
    LabQueryIntent,
    NutritionIntent,
    PlanQueryIntent,
    PrioritiesQueryIntent,
    SleepIntent,
    SleepQueryIntent,
    StepsQueryIntent,
    SymptomIntent,
    TranscriptionResult,
    VoiceCommandResponse,
    VoiceIntent,
    VoiceLanguage,
    VOICE_INTENT_ADAPTER,
)
from app.services.voice.tts_provider import BaseTTSProvider, SpeechSynthesisResult

_CONSUMED_CONFIRMATIONS: set[str] = set()


def _voice_provider_name() -> str:
    return settings.VOICE_PROVIDER or settings.AI_PROVIDER


def get_asr_provider() -> BaseASRProvider:
    if _voice_provider_name() == "qwen":
        return QwenASRProvider()
    return MockASRProvider()


def get_tts_provider() -> BaseTTSProvider:
    if _voice_provider_name() == "qwen":
        return QwenTTSProvider()
    return MockTTSProvider()


def _message(english: str, urdu: str, roman_urdu: str, language: DetectedLanguage, roman: bool) -> str:
    if language == "en":
        return english
    return roman_urdu if roman else urdu


def _result_for_entry(entry, *fields: str) -> dict:
    return {"id": entry.id, **{field: getattr(entry, field) for field in fields}}


def _confirmation_token(profile_id: str, intent: VoiceIntent) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.VOICE_CONFIRMATION_TTL_SECONDS)
    return jwt.encode(
        {
            "sub": profile_id,
            "kind": "voice_confirmation",
            "jti": str(uuid.uuid4()),
            "command": intent.model_dump(),
            "exp": expires_at,
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def _load_confirmation(token: str, profile_id: str) -> VoiceIntent:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=422, detail="This voice confirmation has expired or is invalid.") from exc

    token_id = payload.get("jti")
    if (
        payload.get("kind") != "voice_confirmation"
        or payload.get("sub") != profile_id
        or not isinstance(token_id, str)
        or token_id in _CONSUMED_CONFIRMATIONS
    ):
        raise HTTPException(status_code=422, detail="This voice confirmation is no longer valid.")

    try:
        intent = VOICE_INTENT_ADAPTER.validate_python(payload["command"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="This voice confirmation is invalid.") from exc

    if not isinstance(intent, (CycleIntent, SymptomIntent)):
        raise HTTPException(status_code=422, detail="This command cannot be confirmed.")
    _CONSUMED_CONFIRMATIONS.add(token_id)
    return intent


def _validate_date(value: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Please provide a valid date in YYYY-MM-DD format.") from exc


def _ensure_womens_health_available(profile: HealthProfile) -> None:
    if profile.sex != "female":
        raise HTTPException(
            status_code=403,
            detail="Women's Health voice features are only available for female profiles.",
        )


async def transcribe_audio(
    *,
    audio: bytes,
    filename: str,
    content_type: str,
    language_hint: VoiceLanguage,
    browser_transcript: str | None = None,
) -> TranscriptionResult:
    provider = get_asr_provider()
    transcript = await provider.transcribe(
        audio=audio,
        filename=filename,
        content_type=content_type,
        language_hint=language_hint,
        browser_transcript=browser_transcript,
    )
    transcript = transcript.strip()
    if not transcript:
        raise ValueError("Voice transcription was empty. Please try again.")
    return TranscriptionResult(
        transcript=transcript,
        language=detect_language(transcript, language_hint),
        provider=provider.name,
    )


async def _parse_intent(transcript: str) -> VoiceIntent | None:
    return parse_deterministic_intent(transcript) or await parse_qwen_intent(transcript)


async def _answer_query(
    transcript: str,
    profile: HealthProfile,
    db: Session,
    language: DetectedLanguage,
    roman_urdu: bool,
) -> tuple[str, str]:
    response_language = "English" if language == "en" else ("Roman Urdu" if roman_urdu else "Urdu script")
    system_prompt = (
        f"{build_health_system_prompt(profile, db)}\n\n"
        "This is a health-information voice query. Answer only from the supplied context, "
        "be concise and non-diagnostic, and retain the safety guidance. "
        f"Reply in {response_language}."
    )
    provider_name = settings.AI_PROVIDER
    try:
        response = await get_provider().chat(
            messages=[{"role": "user", "content": transcript}],
            system_prompt=system_prompt,
        )
        return response, provider_name
    except Exception:
        if settings.AI_PROVIDER == "qwen":
            response = await MockProvider().chat(
                messages=[{"role": "user", "content": transcript}],
                system_prompt=system_prompt,
            )
            return response, "mock"
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable. Please try again.")


def _execute_action(
    intent: VoiceIntent,
    profile: HealthProfile,
    db: Session,
    language: DetectedLanguage,
    roman_urdu: bool,
) -> tuple[dict, str, list[str]]:
    today = today_iso()

    if isinstance(intent, HydrationIntent):
        entry = lifestyle_service.create_hydration(
            profile.id,
            date=today,
            amount_ml=intent.parameters.amount_ml,
            source="voice",
            timeline_event=lifestyle_service.TimelineEventInput(
                event_type="voice_hydration",
                title=f"Hydration logged via Voice — {intent.parameters.amount_ml} ml",
                description="Mira",
                deduplicate=True,
            ),
            db=db,
        )
        return (
            _result_for_entry(entry, "date", "amount_ml", "source"),
            _message(
                f"Logged {entry.amount_ml} ml of water.",
                f"{entry.amount_ml} ملی لیٹر پانی لاگ کر دیا گیا ہے۔",
                f"{entry.amount_ml} ml pani log kar diya gaya hai.",
                language,
                roman_urdu,
            ),
            ["dashboard"],
        )

    if isinstance(intent, ActivityIntent):
        entry = lifestyle_service.create_activity(
            profile.id,
            date=today,
            activity_type=intent.parameters.activity_type,
            duration_min=intent.parameters.duration_minutes,
            notes="Mira",
            timeline_event=lifestyle_service.TimelineEventInput(
                event_type="voice_activity",
                title=f"Activity logged via Voice — {intent.parameters.activity_type}",
                description=f"{intent.parameters.duration_minutes} minutes",
                deduplicate=True,
            ),
            db=db,
        )
        return (
            _result_for_entry(entry, "date", "activity_type", "duration_min"),
            _message(
                f"Logged {entry.duration_min} minutes of {entry.activity_type}.",
                f"{entry.activity_type} کے {entry.duration_min} منٹ لاگ کر دیے گئے ہیں۔",
                f"{entry.activity_type} ke {entry.duration_min} minute log kar diye gaye hain.",
                language,
                roman_urdu,
            ),
            ["dashboard"],
        )

    if isinstance(intent, SleepIntent):
        entry = lifestyle_service.create_sleep(
            profile.id,
            date=today,
            hours_slept=intent.parameters.duration_hours,
            timeline_event=lifestyle_service.TimelineEventInput(
                event_type="voice_sleep",
                title=f"Sleep logged via Voice — {intent.parameters.duration_hours:g} hours",
                description="Mira",
                deduplicate=True,
            ),
            db=db,
        )
        return (
            _result_for_entry(entry, "date", "hours_slept", "quality"),
            _message(
                f"Logged {entry.hours_slept:g} hours of sleep.",
                f"{entry.hours_slept:g} گھنٹے کی نیند لاگ کر دی گئی ہے۔",
                f"{entry.hours_slept:g} ghante ki neend log kar di gayi hai.",
                language,
                roman_urdu,
            ),
            ["dashboard"],
        )

    if isinstance(intent, NutritionIntent):
        entry = lifestyle_service.create_nutrition(
            profile.id,
            date=today,
            meal_type=intent.parameters.meal_type,
            food_name=intent.parameters.food_description,
            calories=intent.parameters.estimated_calories_if_available or 0,
            timeline_event=lifestyle_service.TimelineEventInput(
                event_type="voice_nutrition",
                title=f"Nutrition logged via Voice — {intent.parameters.meal_type}",
                description=intent.parameters.food_description,
                deduplicate=True,
            ),
            db=db,
        )
        return (
            _result_for_entry(entry, "date", "meal_type", "food_name", "calories"),
            _message(
                "Logged your meal.",
                "آپ کا کھانا لاگ کر دیا گیا ہے۔",
                "Aap ka khana log kar diya gaya hai.",
                language,
                roman_urdu,
            ),
            ["dashboard"],
        )

    if isinstance(intent, CycleIntent):
        _ensure_womens_health_available(profile)
        _validate_date(intent.parameters.date)
        cycle = cycle_service.create_cycle(
            profile, CycleCreate(start_date=intent.parameters.date), db
        )
        return (
            cycle,
            _message(
                "Your period start has been recorded.",
                "آپ کی ماہواری کا آغاز ریکارڈ کر دیا گیا ہے۔",
                "Aap ki mahawari ka aghaz record kar diya gaya hai.",
                language,
                roman_urdu,
            ),
            ["dashboard", "womens_health"],
        )

    if isinstance(intent, SymptomIntent):
        _ensure_womens_health_available(profile)
        symptom = symptom_service.create_symptom(
            profile,
            SymptomCreate(
                date=today,
                symptom_type=intent.parameters.symptom_type,
                severity=intent.parameters.severity,
            ),
            db,
        )
        return (
            symptom,
            _message(
                "Your symptom has been recorded.",
                "آپ کی علامت ریکارڈ کر دی گئی ہے۔",
                "Aap ki alamat record kar di gayi hai.",
                language,
                roman_urdu,
            ),
            ["dashboard", "womens_health"],
        )

    raise ValueError("This voice command cannot be executed.")


async def command_from_transcript(
    *,
    transcription: TranscriptionResult,
    language_hint: VoiceLanguage,
    profile: HealthProfile,
    db: Session,
) -> VoiceCommandResponse:
    command_transcript = strip_leading_wake_name(transcription.transcript)
    command_language = detect_language(command_transcript, language_hint)
    roman_urdu = uses_roman_urdu(command_transcript, command_language, language_hint)
    try:
        intent = await _parse_intent(command_transcript)
    except VoiceClarificationError as exc:
        return VoiceCommandResponse(
            transcript=transcription.transcript,
            language=command_language,
            action="clarification_required",
            response_text=_message(
                str(exc),
                "براہ کرم 50 سے 5,000 ملی لیٹر کے درمیان مقدار درج کریں۔",
                "Barah-e-karam 50 se 5,000 ml ke darmiyan miktar log karein.",
                command_language,
                roman_urdu,
            ),
            provider=transcription.provider,
        )
    if intent is None:
        return VoiceCommandResponse(
            transcript=transcription.transcript,
            language=command_language,
            action="clarification_required",
            response_text=_message(
                "I could not identify a supported command. Please state a health question or a specific log entry.",
                "میں معاون کمانڈ کو نہیں سمجھ سکا۔ براہ کرم صحت سے متعلق سوال یا واضح لاگ انٹری کہیں۔",
                "Main supported command samajh nahi saka. Sehat ka sawal ya wazeh log entry bolen.",
                command_language,
                roman_urdu,
            ),
            provider=transcription.provider,
        )

    if isinstance(intent, (CycleIntent, SymptomIntent, CycleQueryIntent)) and profile.sex != "female":
        return VoiceCommandResponse(
            transcript=transcription.transcript,
            language=command_language,
            intent=intent.intent,
            action="unavailable",
            response_text=_message(
                "Women's Health voice features are not available for this profile.",
                "اس پروفائل کے لیے ویمنز ہیلتھ وائس فیچرز دستیاب نہیں ہیں۔",
                "Is profile ke liye Women's Health voice features dastiyab nahi hain.",
                command_language,
                roman_urdu,
            ),
            provider=transcription.provider,
        )

    if isinstance(intent, (CycleIntent, SymptomIntent)):
        try:
            if isinstance(intent, CycleIntent):
                _validate_date(intent.parameters.date)
            token = _confirmation_token(profile.id, intent)
        except ValueError as exc:
            return VoiceCommandResponse(
                transcript=transcription.transcript,
                language=command_language,
                intent=intent.intent,
                action="clarification_required",
                response_text=str(exc),
                provider=transcription.provider,
            )
        return VoiceCommandResponse(
            transcript=transcription.transcript,
            language=command_language,
            intent=intent.intent,
            action="confirmation_required",
            requires_confirmation=True,
            confirmation_token=token,
            result={"parameters": intent.parameters.model_dump()},
            response_text=_message(
                "Please confirm before I record this Women's Health entry.",
                "ویمنز ہیلتھ انٹری ریکارڈ کرنے سے پہلے براہ کرم تصدیق کریں۔",
                "Women's Health entry record karne se pehle barah-e-karam tasdeeq karein.",
                command_language,
                roman_urdu,
            ),
            provider=transcription.provider,
        )

    if isinstance(
        intent,
        (
            StepsQueryIntent,
            SleepQueryIntent,
            HydrationQueryIntent,
            CycleQueryIntent,
            HealthSummaryQueryIntent,
            PrioritiesQueryIntent,
            PlanQueryIntent,
            LabQueryIntent,
        ),
    ):
        response_text, answer_provider = await _answer_query(
            command_transcript,
            profile,
            db,
            command_language,
            roman_urdu,
        )
        return VoiceCommandResponse(
            transcript=transcription.transcript,
            language=command_language,
            intent=intent.intent,
            action="answered",
            result={"answer_provider": answer_provider},
            response_text=response_text,
            provider=transcription.provider,
        )

    try:
        result, response_text, refresh_scopes = _execute_action(
            intent,
            profile,
            db,
            command_language,
            roman_urdu,
        )
    except (ValueError, HTTPException) as exc:
        if isinstance(exc, HTTPException):
            raise
        return VoiceCommandResponse(
            transcript=transcription.transcript,
            language=command_language,
            intent=intent.intent,
            action="clarification_required",
            response_text=str(exc),
            provider=transcription.provider,
        )

    return VoiceCommandResponse(
        transcript=transcription.transcript,
        language=command_language,
        intent=intent.intent,
        action="executed",
        result=result,
        response_text=response_text,
        provider=transcription.provider,
        refresh_scopes=refresh_scopes,
    )


def confirm_command(
    *,
    confirmation_token: str,
    profile: HealthProfile,
    db: Session,
) -> VoiceCommandResponse:
    intent = _load_confirmation(confirmation_token, profile.id)
    if isinstance(intent, (CycleIntent, SymptomIntent)) and profile.sex != "female":
        raise HTTPException(status_code=403, detail="Women's Health voice features are not available for this profile.")

    result, response_text, refresh_scopes = _execute_action(
        intent,
        profile,
        db,
        "en",
        False,
    )
    return VoiceCommandResponse(
        language="en",
        intent=intent.intent,
        action="executed",
        result=result,
        response_text=response_text,
        provider=_voice_provider_name(),
        refresh_scopes=refresh_scopes,
    )


async def synthesize_speech(text: str, language: DetectedLanguage) -> SpeechSynthesisResult:
    provider = get_tts_provider()
    try:
        return await provider.synthesize(text, language)
    except Exception:
        return SpeechSynthesisResult(audio=None, media_type=None, provider=provider.name)
