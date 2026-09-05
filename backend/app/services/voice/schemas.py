from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


VoiceLanguage = Literal["auto", "en", "ur"]
DetectedLanguage = Literal["en", "ur"]
VoiceActionStatus = Literal[
    "answered",
    "executed",
    "confirmation_required",
    "clarification_required",
    "unavailable",
]


class EmptyParameters(BaseModel):
    pass


class HydrationParameters(BaseModel):
    amount_ml: int = Field(ge=50, le=5000)


class ActivityParameters(BaseModel):
    activity_type: str = Field(min_length=2, max_length=100)
    duration_minutes: int = Field(ge=1, le=1440)


class SleepParameters(BaseModel):
    duration_hours: float = Field(ge=0.5, le=24)


class NutritionParameters(BaseModel):
    food_description: str = Field(min_length=2, max_length=200)
    meal_type: Literal["breakfast", "lunch", "dinner", "snack", "meal", "other"] = "other"
    estimated_calories_if_available: int | None = Field(default=None, ge=0, le=10000)


class CycleParameters(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class SymptomParameters(BaseModel):
    symptom_type: Literal[
        "cramps",
        "headache",
        "bloating",
        "fatigue",
        "mood_changes",
        "breast_tenderness",
        "acne",
        "appetite_change",
        "nausea",
        "back_pain",
        "other",
    ]
    severity: Literal["mild", "moderate", "severe"]


class HydrationIntent(BaseModel):
    intent: Literal["log_hydration"]
    parameters: HydrationParameters


class ActivityIntent(BaseModel):
    intent: Literal["log_activity"]
    parameters: ActivityParameters


class SleepIntent(BaseModel):
    intent: Literal["log_sleep"]
    parameters: SleepParameters


class NutritionIntent(BaseModel):
    intent: Literal["log_nutrition"]
    parameters: NutritionParameters


class CycleIntent(BaseModel):
    intent: Literal["start_cycle"]
    parameters: CycleParameters


class SymptomIntent(BaseModel):
    intent: Literal["log_symptom"]
    parameters: SymptomParameters


class StepsQueryIntent(BaseModel):
    intent: Literal["query_steps"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


class SleepQueryIntent(BaseModel):
    intent: Literal["query_sleep"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


class HydrationQueryIntent(BaseModel):
    intent: Literal["query_hydration"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


class CycleQueryIntent(BaseModel):
    intent: Literal["query_cycle"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


class HealthSummaryQueryIntent(BaseModel):
    intent: Literal["query_health_summary"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


class PrioritiesQueryIntent(BaseModel):
    intent: Literal["query_priorities"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


class PlanQueryIntent(BaseModel):
    intent: Literal["query_plan"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


class LabQueryIntent(BaseModel):
    intent: Literal["query_labs"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)


VoiceIntent = Annotated[
    Union[
        HydrationIntent,
        ActivityIntent,
        SleepIntent,
        NutritionIntent,
        CycleIntent,
        SymptomIntent,
        StepsQueryIntent,
        SleepQueryIntent,
        HydrationQueryIntent,
        CycleQueryIntent,
        HealthSummaryQueryIntent,
        PrioritiesQueryIntent,
        PlanQueryIntent,
        LabQueryIntent,
    ],
    Field(discriminator="intent"),
]
VOICE_INTENT_ADAPTER = TypeAdapter(VoiceIntent)


class TranscriptionResult(BaseModel):
    transcript: str = Field(min_length=1, max_length=3000)
    language: DetectedLanguage
    provider: str


class TranscriptionResponse(TranscriptionResult):
    pass


class VoiceCommandResponse(BaseModel):
    transcript: str = ""
    language: DetectedLanguage
    intent: str = "unknown"
    action: VoiceActionStatus
    requires_confirmation: bool = False
    confirmation_token: str | None = None
    result: dict[str, Any] | None = None
    response_text: str
    provider: str
    refresh_scopes: list[str] = Field(default_factory=list)


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    language: DetectedLanguage


class SpeakFallbackResponse(BaseModel):
    mode: Literal["browser_fallback"] = "browser_fallback"
    text: str
    language: DetectedLanguage
    provider: str
