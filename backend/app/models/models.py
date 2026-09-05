import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    profile: Mapped["HealthProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id"), unique=True, nullable=True, index=True
    )
    user_name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String(10))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    blood_group: Mapped[str] = mapped_column(String(5))
    city: Mapped[str] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    user: Mapped["User | None"] = relationship(back_populates="profile")
    lab_reports: Mapped[list["LabReport"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    hydration_logs: Mapped[list["HydrationLog"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    nutrition_logs: Mapped[list["NutritionLog"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    sleep_logs: Mapped[list["SleepLog"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    wearable_connections: Mapped[list["WearableConnection"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    insight_records: Mapped[list["InsightRecord"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    cycles: Mapped[list["Cycle"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    cycle_symptoms: Mapped[list["CycleSymptom"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"))
    filename: Mapped[str] = mapped_column(String(255))
    lab_name: Mapped[str] = mapped_column(String(200), default="")
    report_date: Mapped[str] = mapped_column(String(20))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    parsing_method: Mapped[str] = mapped_column(String(50), default="manual")
    upload_date: Mapped[str] = mapped_column(String(20))

    profile: Mapped["HealthProfile"] = relationship(back_populates="lab_reports")
    biomarkers: Mapped[list["Biomarker"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    report_id: Mapped[str] = mapped_column(String, ForeignKey("lab_reports.id"))
    name: Mapped[str] = mapped_column(String(200))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    reference_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="normal")
    category: Mapped[str] = mapped_column(String(50), default="other")

    report: Mapped["LabReport"] = relationship(back_populates="biomarkers")


class HydrationLog(Base):
    __tablename__ = "hydration_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"))
    date: Mapped[str] = mapped_column(String(20))
    amount_ml: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(50), default="water")

    profile: Mapped["HealthProfile"] = relationship(back_populates="hydration_logs")


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"))
    date: Mapped[str] = mapped_column(String(20))
    meal_type: Mapped[str] = mapped_column(String(20))
    food_name: Mapped[str] = mapped_column(String(200))
    quantity_g: Mapped[int] = mapped_column(Integer, default=0)
    calories: Mapped[int] = mapped_column(Integer, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    fat_g: Mapped[float] = mapped_column(Float, default=0)
    is_pakistani_food: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped["HealthProfile"] = relationship(back_populates="nutrition_logs")


class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"))
    date: Mapped[str] = mapped_column(String(20))
    hours_slept: Mapped[float] = mapped_column(Float)
    quality: Mapped[int] = mapped_column(Integer, default=3)

    profile: Mapped["HealthProfile"] = relationship(back_populates="sleep_logs")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"))
    date: Mapped[str] = mapped_column(String(20))
    activity_type: Mapped[str] = mapped_column(String(100))
    duration_min: Mapped[int] = mapped_column(Integer, default=0)
    steps: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(String(500), default="")

    profile: Mapped["HealthProfile"] = relationship(back_populates="activity_logs")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"))
    date: Mapped[str] = mapped_column(String(20))
    event_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    profile: Mapped["HealthProfile"] = relationship(back_populates="timeline_events")


class WearableConnection(Base):
    __tablename__ = "wearable_connections"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"))
    provider: Mapped[str] = mapped_column(String(50))
    device_name: Mapped[str] = mapped_column(String(100))
    device_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="connected")
    connected_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    last_synced_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    profile: Mapped["HealthProfile"] = relationship(back_populates="wearable_connections")
    metrics: Mapped[list["WearableMetric"]] = relationship(back_populates="connection", cascade="all, delete-orphan")
    syncs: Mapped[list["WearableSync"]] = relationship(back_populates="connection", cascade="all, delete-orphan")


class WearableMetric(Base):
    __tablename__ = "wearable_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    connection_id: Mapped[str] = mapped_column(String, ForeignKey("wearable_connections.id"))
    metric_type: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    recorded_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    source: Mapped[str] = mapped_column(String(50), default="mock")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    connection: Mapped["WearableConnection"] = relationship(back_populates="metrics")


class WearableSync(Base):
    __tablename__ = "wearable_synces"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    connection_id: Mapped[str] = mapped_column(String, ForeignKey("wearable_connections.id"))
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    records_synced: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    connection: Mapped["WearableConnection"] = relationship(back_populates="syncs")


class InsightRecord(Base):
    __tablename__ = "insight_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"), unique=True, index=True)
    insight_json: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(50))
    fingerprint: Mapped[str] = mapped_column(String(255))
    generated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    profile: Mapped["HealthProfile"] = relationship(back_populates="insight_records")


class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"), index=True)
    start_date: Mapped[str] = mapped_column(String(20))
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cycle_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    profile: Mapped["HealthProfile"] = relationship(back_populates="cycles")
    period_days: Mapped[list["PeriodDay"]] = relationship(back_populates="cycle", cascade="all, delete-orphan")


class PeriodDay(Base):
    __tablename__ = "period_days"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    cycle_id: Mapped[str] = mapped_column(String, ForeignKey("cycles.id"))
    date: Mapped[str] = mapped_column(String(20))
    flow_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    cycle: Mapped["Cycle"] = relationship(back_populates="period_days")


class CycleSymptom(Base):
    __tablename__ = "cycle_symptoms"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String, ForeignKey("health_profiles.id"), index=True)
    date: Mapped[str] = mapped_column(String(20))
    symptom_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    notes: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    profile: Mapped["HealthProfile"] = relationship(back_populates="cycle_symptoms")
