import json
import re
from datetime import date

from pydantic import ValidationError

from app.core.config import settings
from app.services.ai.provider_factory import get_provider
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
    VoiceIntent,
    VoiceLanguage,
    VOICE_INTENT_ADAPTER,
)

URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ROMAN_URDU_MARKERS = (
    "pani", "neend", "mahwari", "mahawari", "qadam", "ghant", "minut", "dard",
    "main ne", "maine", "piya", "pii", "aaj", "sau", "paanch", "tees",
)

NUMBER_WORDS: tuple[tuple[str, float], ...] = (
    ("پانچ سو", 500),
    ("پانچسوم", 500),
    ("five hundred", 500),
    ("paanch sau", 500),
    ("panch sau", 500),
    ("تین سو", 300),
    ("three hundred", 300),
    ("دو سو", 200),
    ("two hundred", 200),
    ("ایک سو", 100),
    ("one hundred", 100),
    ("تیس", 30),
    ("thirty", 30),
    ("tees", 30),
    ("سات", 7),
    ("seven", 7),
    ("saat", 7),
    ("چھ", 6),
    ("six", 6),
    ("chay", 6),
    ("پانچ", 5),
    ("five", 5),
    ("چار", 4),
    ("four", 4),
    ("تین", 3),
    ("three", 3),
    ("دو", 2),
    ("two", 2),
    ("ایک", 1),
    ("one", 1),
)

INTENT_SYSTEM_PROMPT = """You classify HealthOS voice transcripts into a strict JSON command.
Return JSON only, with one allowed intent and a parameters object. Never include prose.
Allowed actions: log_hydration {amount_ml}, log_activity {activity_type,duration_minutes},
log_sleep {duration_hours}, log_nutrition {food_description,meal_type,estimated_calories_if_available},
start_cycle {date}, log_symptom {symptom_type,severity}.
Allowed queries: query_steps, query_sleep, query_hydration, query_cycle,
query_health_summary, query_priorities, query_plan, query_labs. Query parameters must be {}.
Do not infer missing amounts, dates, symptoms, or severity. If unclear, return {}.
Never perform actions, only classify the requested intent."""


def detect_language(transcript: str, hint: VoiceLanguage = "auto") -> DetectedLanguage:
    if hint in {"en", "ur"}:
        return hint
    if re.search(r"[\u0600-\u06ff]", transcript):
        return "ur"
    normalized = transcript.casefold()
    if any(marker in normalized for marker in ROMAN_URDU_MARKERS):
        return "ur"
    return "en"


def uses_roman_urdu(transcript: str, language: DetectedLanguage, hint: VoiceLanguage) -> bool:
    return language == "ur" and hint != "ur" and not re.search(r"[\u0600-\u06ff]", transcript)


_WAKE_NAME_PREFIX = re.compile(r"^\s*mira(?=$|[\s,،.:;!?۔—-])[\s,،.:;!?۔—-]*", re.IGNORECASE)


class VoiceClarificationError(ValueError):
    pass


def strip_leading_wake_name(transcript: str) -> str:
    return _WAKE_NAME_PREFIX.sub("", transcript, count=1).strip()


def _normalized(text: str) -> str:
    return text.translate(URDU_DIGITS).casefold()


def _number_from_text(text: str) -> float | None:
    normalized = _normalized(text)
    numeric = re.search(r"(?<![\w.])(\d+(?:\.\d+)?)", normalized)
    if numeric:
        return float(numeric.group(1))
    for phrase, value in NUMBER_WORDS:
        if phrase in normalized:
            return value
    return None


def _hydration_amount_ml(text: str, number: float) -> int:
    value = number * 1000 if re.search(r"(?<![a-z])(?:liters?|litres?|l)\b", text) else number
    amount_ml = round(value)
    if not 50 <= amount_ml <= 5000:
        raise VoiceClarificationError("Please log an amount between 50 ml and 5,000 ml.")
    return amount_ml


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _severity(text: str) -> str | None:
    if _contains_any(text, ("severe", "شدید", "shadeed")):
        return "severe"
    if _contains_any(text, ("moderate", "درمیان", "darmiyan", "medium")):
        return "moderate"
    if _contains_any(text, ("mild", "ہلکا", "halka", "halki")):
        return "mild"
    return None


def _symptom(text: str) -> str | None:
    patterns = (
        ("cramps", ("cramp", "cramps", "درد", "dard")),
        ("headache", ("headache", "سر درد", "sar dard")),
        ("bloating", ("bloating", "پیٹ پھولا", "pet phoola")),
        ("fatigue", ("fatigue", "تھکن", "thakan")),
        ("nausea", ("nausea", "متلی", "matli")),
        ("back_pain", ("back pain", "کمر درد", "kamar dard")),
        ("acne", ("acne", "مہاسے", "muhasay")),
    )
    for name, markers in patterns:
        if _contains_any(text, markers):
            return name
    return None


def parse_deterministic_intent(transcript: str) -> VoiceIntent | None:
    text = _normalized(transcript)
    number = _number_from_text(text)
    is_question = _contains_any(text, ("?", "how", "what", "which", "why", "kitne", "kya", "کتنے", "کیا", "کس"))

    if _contains_any(text, ("steps", "step", "قدم", "qadam")) and is_question:
        return StepsQueryIntent(intent="query_steps")
    if _contains_any(text, ("hydration", "water", "پانی", "pani")) and is_question:
        return HydrationQueryIntent(intent="query_hydration")
    if _contains_any(text, ("sleep", "slept", "نیند", "neend")) and is_question:
        return SleepQueryIntent(intent="query_sleep")
    if _contains_any(text, ("cycle phase", "cycle", "period due", "ماہواری", "mahwari")) and is_question:
        return CycleQueryIntent(intent="query_cycle")
    if _contains_any(text, ("priority", "priorities", "focus", "توجہ", "focus kar")):
        return PrioritiesQueryIntent(intent="query_priorities")
    if _contains_any(text, ("7-day plan", "seven day plan", "plan", "منصوبہ")) and is_question:
        return PlanQueryIntent(intent="query_plan")
    if _contains_any(text, ("vitamin", "lab", "result", "biomarker", "test", "رپورٹ")) and is_question:
        return LabQueryIntent(intent="query_labs")

    if _contains_any(text, ("period started", "period start", "ماہواری شروع", "mahwari shuru")):
        return CycleIntent(intent="start_cycle", parameters={"date": date.today().isoformat()})

    symptom = _symptom(text)
    severity = _severity(text)
    if symptom and severity:
        return SymptomIntent(
            intent="log_symptom",
            parameters={"symptom_type": symptom, "severity": severity},
        )

    if _contains_any(text, ("water", "hydration", "پانی", "pani")) and number is not None:
        return HydrationIntent(
            intent="log_hydration",
            parameters={"amount_ml": _hydration_amount_ml(text, number)},
        )

    if _contains_any(text, ("walk", "walked", "walking", "واک", "چلا", "chala", "walk ki")) and number is not None:
        activity_type = "walking"
        return ActivityIntent(
            intent="log_activity",
            parameters={"activity_type": activity_type, "duration_minutes": round(number)},
        )

    if _contains_any(text, ("sleep", "slept", "نیند", "neend")) and number is not None:
        return SleepIntent(intent="log_sleep", parameters={"duration_hours": number})

    if _contains_any(text, ("ate", "eaten", "meal", "کھایا", "کھائی", "khaya", "roti", "daal", "دال", "روٹی")):
        meal_type = "meal"
        if "breakfast" in text:
            meal_type = "breakfast"
        elif "lunch" in text:
            meal_type = "lunch"
        elif "dinner" in text:
            meal_type = "dinner"
        return NutritionIntent(
            intent="log_nutrition",
            parameters={"food_description": transcript.strip(), "meal_type": meal_type},
        )

    if is_question:
        return HealthSummaryQueryIntent(intent="query_health_summary")
    return None


def _extract_json(content: str) -> dict | None:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


async def parse_qwen_intent(transcript: str) -> VoiceIntent | None:
    if settings.AI_PROVIDER != "qwen":
        return None
    try:
        content = await get_provider().chat(
            messages=[{"role": "user", "content": transcript}],
            system_prompt=INTENT_SYSTEM_PROMPT,
        )
        candidate = _extract_json(content)
        if not candidate:
            return None
        return VOICE_INTENT_ADAPTER.validate_python(candidate)
    except (ValidationError, ValueError, TypeError, json.JSONDecodeError):
        return None
