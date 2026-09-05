from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

FlowLevel = Literal["light", "moderate", "heavy"]
Severity = Literal["mild", "moderate", "severe"]
SymptomType = Literal[
    "cramps", "headache", "bloating", "fatigue", "mood_changes",
    "breast_tenderness", "acne", "appetite_change", "nausea", "back_pain", "other",
]
CyclePhase = Literal["menstrual", "follicular", "ovulatory", "luteal"]


class CycleCreate(BaseModel):
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    period_length: int | None = Field(default=None, ge=1, le=14)
    notes: str = Field(default="", max_length=500)


class CycleEndRequest(BaseModel):
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class SymptomCreate(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    symptom_type: SymptomType
    severity: Severity
    notes: str = Field(default="", max_length=500)


class PeriodDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: str
    flow_level: str | None = None


class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    start_date: str
    end_date: str | None = None
    cycle_length: int | None = None
    period_length: int | None = None
    notes: str = ""
    created_at: str | None = None
    period_days: list[PeriodDayOut] = Field(default_factory=list)


class SymptomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    date: str
    symptom_type: str
    severity: str
    notes: str = ""
    created_at: str | None = None


class PredictionOut(BaseModel):
    has_data: bool
    needs_more_data: bool = False
    message: str | None = None
    current_cycle_day: int | None = None
    current_phase: CyclePhase | None = None
    cycle_day_of_phase: int | None = None
    current_cycle_length: int | None = None
    average_cycle_length: int | None = None
    average_period_length: int | None = None
    cycles_tracked: int = 0
    predicted_period_start: str | None = None
    predicted_period_end: str | None = None
    estimated_fertile_start: str | None = None
    estimated_fertile_end: str | None = None
    is_on_period_today: bool = False


class CalendarDay(BaseModel):
    date: str
    in_period: bool = False
    is_predicted_period: bool = False
    is_fertile_window: bool = False
    is_today: bool = False
    has_symptom: bool = False
    symptom_types: list[str] = Field(default_factory=list)
    flow_level: str | None = None


class CalendarOut(BaseModel):
    month: str
    days: list[CalendarDay]
    average_cycle_length: int | None = None
