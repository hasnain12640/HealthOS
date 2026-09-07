"""
Seeds the Bilal Ahmed synthetic demo profile into SQLite on startup.
Only runs if the profile does not already exist — safe to call on every restart.
Demo credentials are read from environment; seeding is skipped if DEMO_PASSWORD is unset.

Also seeds the Ayesha Khan female demo profile (Women's Health showcase),
kept separate from the male demo and never modified by it.
"""
import random
from datetime import date, datetime, time, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dates import today_iso, days_ago_iso
from app.core.security import hash_password
from app.models.models import (
    User, HealthProfile, LabReport, Biomarker,
    HydrationLog, NutritionLog, SleepLog, ActivityLog, TimelineEvent,
    Cycle, PeriodDay, CycleSymptom,
    WearableConnection, WearableMetric,
)
from app.services.deterministic.health_calculations import (
    calculate_hydration_target,
    assess_biomarker_status,
)
from app.services.deterministic.biomarker_parser import BIOMARKER_DEFAULTS

DEMO_USER_ID = "demo-user-001"
DEMO_PROFILE_ID = "demo-001"

FEMALE_DEMO_USER_ID = "demo-user-002"
FEMALE_DEMO_PROFILE_ID = "demo-002"


def _refresh_demo_dates(db: Session) -> None:
    """Re-anchor synthetic demo logs to today so 'today' views and the AI
    health context show live values instead of zeros on a long-lived database."""
    today = today_iso()

    for log in db.query(HydrationLog).filter(HydrationLog.profile_id == DEMO_PROFILE_ID).all():
        log.date = today
    for log in db.query(NutritionLog).filter(NutritionLog.profile_id == DEMO_PROFILE_ID).all():
        log.date = today
    for log in db.query(ActivityLog).filter(ActivityLog.profile_id == DEMO_PROFILE_ID).all():
        log.date = today

    sleep_logs = (
        db.query(SleepLog)
        .filter(SleepLog.profile_id == DEMO_PROFILE_ID)
        .order_by(SleepLog.date.desc())
        .all()
    )
    for i, log in enumerate(sleep_logs):
        log.date = days_ago_iso(i)

    report = db.query(LabReport).filter(LabReport.id == "report-001").first()
    if report:
        report.report_date = days_ago_iso(1)

    # Keep the 30-day demo history window current relative to today.
    _clear_demo_historical_logs(db, DEMO_PROFILE_ID)
    _seed_demo_history(db, DEMO_PROFILE_ID)


# ── Deterministic 30-day demo history backfill ───────────────────────────────

_DEMO_FOODS = [
    ("Paratha with Chai", 380, 8, 48, 18),
    ("Daal Chawal", 520, 18, 82, 12),
    ("Chicken Karahi with Roti", 650, 42, 55, 22),
    ("Aloo Keema", 480, 24, 52, 18),
    ("Saiji with Naan", 620, 35, 68, 24),
    ("Fruit Chaat", 180, 2, 42, 1),
    ("Yogurt Lassi", 150, 6, 18, 5),
    ("Boiled Eggs", 140, 12, 1, 10),
    ("Chana Chaat", 260, 10, 40, 7),
    ("Grilled Fish with Rice", 540, 38, 58, 14),
]

_DEMO_MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]

_DEMO_HYDRATION_SOURCES = ["water", "tea", "lassi", "water"]


def _clear_demo_historical_logs(db: Session, profile_id: str) -> None:
    """Remove historical demo logs older than today so the 30-day window can be
    re-anchored freshly on every restart. Today is preserved."""
    today = today_iso()

    for model in (HydrationLog, NutritionLog, SleepLog, ActivityLog):
        db.query(model).filter(
            model.profile_id == profile_id,
            model.date < today,
        ).delete(synchronize_session=False)

    conn = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.profile_id == profile_id,
            WearableConnection.status == "connected",
        )
        .first()
    )
    if conn:
        db.query(WearableMetric).filter(
            WearableMetric.connection_id == conn.id,
            WearableMetric.recorded_at < datetime.combine(date.today(), time.min),
        ).delete(synchronize_session=False)


def _seed_demo_history(db: Session, profile_id: str) -> None:
    """Generate reproducible 30-day history for a demo profile.

    Skips today and any date that already has real user data so the backfill
    never overwrites manually logged records.
    """
    from app.services.wearables import service as wearable_service

    profile = db.query(HealthProfile).filter(HealthProfile.id == profile_id).first()
    if not profile:
        return

    rng = random.Random(f"{profile_id}-history-42")
    today = today_iso()
    target_ml = calculate_hydration_target(profile.weight_kg)

    # Ensure a connected demo wearable exists; we'll mirror metrics into it.
    conn = wearable_service.demo_connect(profile_id, db)
    connection_id = conn.id

    # Build date -> has-data maps to avoid overwriting existing records.
    existing_hydration_dates = {
        h.date for h in db.query(HydrationLog).filter(HydrationLog.profile_id == profile_id).all()
    }
    existing_nutrition_dates = {
        n.date for n in db.query(NutritionLog).filter(NutritionLog.profile_id == profile_id).all()
    }
    existing_sleep_dates = {
        s.date for s in db.query(SleepLog).filter(SleepLog.profile_id == profile_id).all()
    }
    existing_activity_dates = {
        a.date for a in db.query(ActivityLog).filter(ActivityLog.profile_id == profile_id).all()
    }

    for i in range(1, 30):
        d = days_ago_iso(i)
        d_date = date.today() - timedelta(days=i)

        # --- Hydration ---
        if d not in existing_hydration_dates:
            log_count = rng.randint(2, 4)
            target_pct = rng.uniform(0.5, 1.1)
            total_target = int(target_ml * target_pct)
            portions = [rng.randint(200, 500) for _ in range(log_count)]
            scale = total_target / sum(portions) if sum(portions) else 1
            for idx in range(log_count):
                db.add(HydrationLog(
                    id=str(uuid4()),
                    profile_id=profile_id,
                    date=d,
                    amount_ml=int(portions[idx] * scale),
                    source=rng.choice(_DEMO_HYDRATION_SOURCES),
                ))

        # --- Nutrition ---
        if d not in existing_nutrition_dates:
            meal_count = rng.randint(2, 3)
            chosen = rng.sample(_DEMO_FOODS, k=meal_count)
            for idx, (food_name, cal, prot, carb, fat) in enumerate(chosen):
                db.add(NutritionLog(
                    id=str(uuid4()),
                    profile_id=profile_id,
                    date=d,
                    meal_type=_DEMO_MEAL_TYPES[idx],
                    food_name=food_name,
                    quantity_g=rng.randint(180, 450),
                    calories=int(cal * rng.uniform(0.85, 1.15)),
                    protein_g=round(prot * rng.uniform(0.85, 1.15), 1),
                    carbs_g=round(carb * rng.uniform(0.85, 1.15), 1),
                    fat_g=round(fat * rng.uniform(0.85, 1.15), 1),
                    is_pakistani_food=True,
                ))

        # --- Sleep ---
        if d not in existing_sleep_dates:
            db.add(SleepLog(
                id=str(uuid4()),
                profile_id=profile_id,
                date=d,
                hours_slept=round(rng.uniform(5.5, 8.0), 1),
                quality=rng.randint(2, 4),
            ))

        # --- Activity ---
        if d not in existing_activity_dates:
            steps = rng.randint(1500, 9000)
            db.add(ActivityLog(
                id=str(uuid4()),
                profile_id=profile_id,
                date=d,
                activity_type="Walking",
                duration_min=max(10, int(steps / 120)),
                steps=steps,
                notes="Demo activity",
            ))

        # --- Wearable metrics (one snapshot per historical day) ---
        recorded_at = datetime.combine(d_date, time(8, 0))
        base_steps = rng.randint(3000, 9500)
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="steps",
            value=float(base_steps),
            unit="steps",
            recorded_at=recorded_at,
            source="mock",
        ))
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="active_calories",
            value=float(max(50, int(base_steps * 0.055))),
            unit="kcal",
            recorded_at=recorded_at,
            source="mock",
        ))
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="resting_heart_rate",
            value=float(rng.randint(60, 75)),
            unit="bpm",
            recorded_at=recorded_at,
            source="mock",
        ))
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="avg_heart_rate",
            value=float(rng.randint(70, 85)),
            unit="bpm",
            recorded_at=recorded_at,
            source="mock",
        ))
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="sleep",
            value=round(rng.uniform(5.5, 7.8), 1),
            unit="hours",
            recorded_at=recorded_at,
            source="mock",
        ))
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="distance",
            value=round(base_steps * 0.0007, 1),
            unit="km",
            recorded_at=recorded_at,
            source="mock",
        ))
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="water",
            value=round(rng.uniform(1.0, 2.2), 1),
            unit="L",
            recorded_at=recorded_at,
            source="mock",
        ))
        db.add(WearableMetric(
            id=str(uuid4()),
            connection_id=connection_id,
            metric_type="weight",
            value=round(profile.weight_kg + rng.uniform(-1.0, 1.0), 1),
            unit="kg",
            recorded_at=recorded_at,
            source="mock",
        ))

    db.commit()


def seed_demo_data(db: Session) -> None:
    if not settings.SEED_DEMO_DATA or not settings.DEMO_PASSWORD:
        return

    # --- Demo user ---
    user = db.query(User).filter(User.email == settings.DEMO_EMAIL).first()
    if not user:
        user = User(
            id=DEMO_USER_ID,
            email=settings.DEMO_EMAIL,
            password_hash=hash_password(settings.DEMO_PASSWORD),
            name="Bilal Ahmed",
        )
        db.add(user)
        db.flush()

    # --- Existing orphaned profile adoption (e.g. after schema upgrade) ---
    existing_profile = db.query(HealthProfile).filter(HealthProfile.id == DEMO_PROFILE_ID).first()
    if existing_profile:
        if existing_profile.user_id is None:
            existing_profile.user_id = user.id
        _refresh_demo_dates(db)
        db.commit()
        seed_female_demo_data(db)
        return

    # --- Profile ---
    today = today_iso()
    profile = HealthProfile(
        id=DEMO_PROFILE_ID,
        user_id=user.id,
        user_name="Bilal Ahmed",
        age=34,
        sex="male",
        height_cm=172.0,
        weight_kg=82.0,
        blood_group="B+",
        city="Lahore",
        language="en",
    )
    db.add(profile)

    # --- Lab Report ---
    report = LabReport(
        id="report-001",
        profile_id=DEMO_PROFILE_ID,
        filename="bilal_cbc_report_aug2024.pdf",
        lab_name="Chughtai Lab, Lahore",
        report_date=days_ago_iso(1),
        parsing_method="pdf_text",
        upload_date=today,
    )
    db.add(report)

    # --- Biomarkers ---
    biomarkers = [
        Biomarker(id="bm-001", report_id="report-001", name="Hemoglobin",
                  value=11.8, unit="g/dL", reference_low=13.0, reference_high=17.0,
                  status="low", category="CBC"),
        Biomarker(id="bm-002", report_id="report-001", name="Fasting Blood Glucose",
                  value=108.0, unit="mg/dL", reference_low=70.0, reference_high=100.0,
                  status="high", category="metabolic"),
        Biomarker(id="bm-003", report_id="report-001", name="Total Cholesterol",
                  value=215.0, unit="mg/dL", reference_low=None, reference_high=200.0,
                  status="high", category="lipid"),
        Biomarker(id="bm-004", report_id="report-001", name="Vitamin D (25-OH)",
                  value=18.0, unit="ng/mL", reference_low=30.0, reference_high=100.0,
                  status="low", category="vitamin"),
        Biomarker(id="bm-005", report_id="report-001", name="TSH",
                  value=2.4, unit="mIU/L", reference_low=0.4, reference_high=4.0,
                  status="normal", category="thyroid"),
        Biomarker(id="bm-006", report_id="report-001", name="Creatinine",
                  value=0.9, unit="mg/dL", reference_low=0.7, reference_high=1.2,
                  status="normal", category="metabolic"),
        Biomarker(id="bm-007", report_id="report-001", name="WBC Count",
                  value=7200.0, unit="/µL", reference_low=4000.0, reference_high=11000.0,
                  status="normal", category="CBC"),
        Biomarker(id="bm-008", report_id="report-001", name="Platelets",
                  value=245000.0, unit="/µL", reference_low=150000.0, reference_high=400000.0,
                  status="normal", category="CBC"),
    ]
    db.add_all(biomarkers)

    # --- Hydration logs (today) ---
    hydration = [
        HydrationLog(id="h-001", profile_id=DEMO_PROFILE_ID, date=today, amount_ml=300, source="tea"),
        HydrationLog(id="h-002", profile_id=DEMO_PROFILE_ID, date=today, amount_ml=400, source="water"),
        HydrationLog(id="h-003", profile_id=DEMO_PROFILE_ID, date=today, amount_ml=250, source="lassi"),
        HydrationLog(id="h-004", profile_id=DEMO_PROFILE_ID, date=today, amount_ml=400, source="water"),
    ]
    db.add_all(hydration)

    # --- Nutrition logs ---
    nutrition = [
        NutritionLog(id="n-001", profile_id=DEMO_PROFILE_ID, date=today,
                     meal_type="breakfast", food_name="Paratha with Chai",
                     quantity_g=200, calories=380, protein_g=8, carbs_g=48, fat_g=18, is_pakistani_food=True),
        NutritionLog(id="n-002", profile_id=DEMO_PROFILE_ID, date=today,
                     meal_type="lunch", food_name="Daal Chawal",
                     quantity_g=400, calories=520, protein_g=18, carbs_g=82, fat_g=12, is_pakistani_food=True),
        NutritionLog(id="n-003", profile_id=DEMO_PROFILE_ID, date=today,
                     meal_type="dinner", food_name="Chicken Karahi with Roti",
                     quantity_g=450, calories=650, protein_g=42, carbs_g=55, fat_g=22, is_pakistani_food=True),
    ]
    db.add_all(nutrition)

    # --- Sleep logs (7 days ending today) ---
    sleep = [
        SleepLog(id="s-001", profile_id=DEMO_PROFILE_ID, date=today, hours_slept=5.5, quality=2),
        SleepLog(id="s-002", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(1), hours_slept=6.0, quality=3),
        SleepLog(id="s-003", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(2), hours_slept=5.8, quality=2),
        SleepLog(id="s-004", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(3), hours_slept=6.2, quality=3),
        SleepLog(id="s-005", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(4), hours_slept=5.5, quality=2),
        SleepLog(id="s-006", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(5), hours_slept=6.5, quality=3),
        SleepLog(id="s-007", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(6), hours_slept=5.0, quality=2),
    ]
    db.add_all(sleep)

    # --- Activity logs ---
    activity = [
        ActivityLog(id="a-001", profile_id=DEMO_PROFILE_ID, date=today,
                    activity_type="Walking", duration_min=20, steps=2400, notes="Morning walk"),
    ]
    db.add_all(activity)

    # --- Timeline events ---
    timeline = [
        TimelineEvent(id="tl-001", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(1),
                      event_type="lab", title="Blood Test — Chughtai Lab",
                      description="8 biomarkers analyzed. 4 outside reference range.",
                      is_ai_generated=False),
        TimelineEvent(id="tl-002", profile_id=DEMO_PROFILE_ID, date=today,
                      event_type="ai_insight", title="AI Health Priorities Generated",
                      description="HealthOS identified 4 personalized priorities based on your data.",
                      is_ai_generated=True),
        TimelineEvent(id="tl-003", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(1),
                      event_type="activity", title="Light Walking — 20 minutes",
                      description="2,400 steps recorded.",
                      is_ai_generated=False),
        TimelineEvent(id="tl-004", profile_id=DEMO_PROFILE_ID, date=days_ago_iso(5),
                      event_type="plan", title="7-Day Action Plan Created",
                      description="Personalized plan based on lab results and lifestyle data.",
                      is_ai_generated=True),
    ]
    db.add_all(timeline)

    db.commit()

    # Backfill 30 days of deterministic demo history for the male profile.
    _clear_demo_historical_logs(db, DEMO_PROFILE_ID)
    _seed_demo_history(db, DEMO_PROFILE_ID)

    seed_female_demo_data(db)


# ── Female demo profile (Women's Health showcase) ────────────────────────────

_AYESHA_CYCLE_LENGTH = 28
_AYESHA_PERIOD_LENGTH = 5
# Current cycle started 20 days ago → today is cycle day 21 (Luteal phase),
# with the next period estimated at day 29 (~1 week away).
_AYESHA_CURRENT_DAY = 20
_AYESHA_CYCLES_COMPLETED = 4


def _ayesha_cycle_dates() -> list[tuple[str, str | None]]:
    """(start_date, end_date|None) for Ayesha's cycles, oldest first.

    The last cycle is open and started 20 days ago, so the engine always
    reports day 21 of a 28-day cycle (Luteal phase, next period estimated
    at day 29) no matter when the demo is viewed.
    """
    today = date.today()
    current_start = today - timedelta(days=_AYESHA_CURRENT_DAY)
    total = _AYESHA_CYCLES_COMPLETED + 1
    rows = []
    for i in range(total):
        start = current_start - timedelta(days=(total - 1 - i) * _AYESHA_CYCLE_LENGTH)
        end = start + timedelta(days=_AYESHA_CYCLE_LENGTH) if i < total - 1 else None
        rows.append((start.isoformat(), end.isoformat() if end else None))
    return rows


def _flow_levels() -> list[str]:
    return ["light", "moderate", "heavy", "moderate", "light"]


def _reset_ayesha_cycle_data(db: Session) -> None:
    """Delete and recreate Ayesha's cycles/symptoms anchored to today, so the
    demo always shows the intended cycle position. Only touches demo-002."""
    for cycle in db.query(Cycle).filter(Cycle.profile_id == FEMALE_DEMO_PROFILE_ID).all():
        db.query(PeriodDay).filter(PeriodDay.cycle_id == cycle.id).delete()
        db.delete(cycle)
    db.query(CycleSymptom).filter(CycleSymptom.profile_id == FEMALE_DEMO_PROFILE_ID).delete()
    db.query(TimelineEvent).filter(
        TimelineEvent.profile_id == FEMALE_DEMO_PROFILE_ID,
        TimelineEvent.event_type.in_(["cycle", "cycle_symptom"]),
    ).delete(synchronize_session=False)

    dates = _ayesha_cycle_dates()
    flows = _flow_levels()
    for i, (start_iso, end_iso) in enumerate(dates):
        cycle = Cycle(
            id=f"demo-cycle-{i+1:03d}",
            profile_id=FEMALE_DEMO_PROFILE_ID,
            start_date=start_iso,
            end_date=end_iso,
            cycle_length=_AYESHA_CYCLE_LENGTH if end_iso else None,
            period_length=_AYESHA_PERIOD_LENGTH,
            notes="",
        )
        db.add(cycle)
        db.flush()

        start = date.fromisoformat(start_iso)
        for d in range(_AYESHA_PERIOD_LENGTH):
            db.add(PeriodDay(
                id=f"demo-pd-{i+1:03d}-{d+1}",
                cycle_id=cycle.id,
                date=(start + timedelta(days=d)).isoformat(),
                flow_level=flows[d % len(flows)],
            ))

        is_current = end_iso is None
        db.add(TimelineEvent(
            id=f"demo-tl-cycle-{i+1:03d}",
            profile_id=FEMALE_DEMO_PROFILE_ID,
            date=start_iso,
            event_type="cycle",
            title="Period started",
            description=(
                f"New cycle started ({_AYESHA_PERIOD_LENGTH} day period logged)."
                if is_current else
                f"Cycle ended after {_AYESHA_CYCLE_LENGTH} days."
            ),
            is_ai_generated=False,
        ))

    symptoms = [
        ("demo-sym-001", days_ago_iso(1), "fatigue", "moderate"),
        ("demo-sym-002", days_ago_iso(2), "bloating", "mild"),
    ]
    for sym_id, sym_date, sym_type, severity in symptoms:
        db.add(CycleSymptom(
            id=sym_id,
            profile_id=FEMALE_DEMO_PROFILE_ID,
            date=sym_date,
            symptom_type=sym_type,
            severity=severity,
            notes="",
        ))
        label = {"fatigue": "Fatigue", "bloating": "Bloating"}[sym_type]
        db.add(TimelineEvent(
            id=f"demo-tl-{sym_id}",
            profile_id=FEMALE_DEMO_PROFILE_ID,
            date=sym_date,
            event_type="cycle_symptom",
            title="Symptom logged",
            description=f"{label} ({severity})",
            is_ai_generated=False,
        ))


def seed_female_demo_data(db: Session) -> None:
    """Idempotent seed for the Ayesha Khan female demo profile. Independent of
    the male (Bilal) demo — never creates or modifies it."""
    if not settings.SEED_DEMO_DATA or not settings.DEMO_PASSWORD:
        return

    from app.services.wearables import service as wearable_service

    user = db.query(User).filter(User.email == settings.FEMALE_DEMO_EMAIL).first()
    if not user:
        user = User(
            id=FEMALE_DEMO_USER_ID,
            email=settings.FEMALE_DEMO_EMAIL,
            password_hash=hash_password(settings.DEMO_PASSWORD),
            name="Ayesha Khan",
        )
        db.add(user)
        db.flush()

    profile = db.query(HealthProfile).filter(HealthProfile.id == FEMALE_DEMO_PROFILE_ID).first()
    if not profile:
        profile = HealthProfile(
            id=FEMALE_DEMO_PROFILE_ID,
            user_id=user.id,
            user_name="Ayesha Khan",
            age=28,
            sex="female",
            height_cm=161.0,
            weight_kg=57.0,
            blood_group="O+",
            city="Lahore",
            language="en",
        )
        db.add(profile)
        db.flush()

    _reset_ayesha_cycle_data(db)
    db.commit()

    # Connect the simulated Fitbit for the female demo (idempotent).
    wearable_service.demo_connect(FEMALE_DEMO_PROFILE_ID, db)

    # Backfill 30 days of deterministic demo history for the female profile.
    _clear_demo_historical_logs(db, FEMALE_DEMO_PROFILE_ID)
    _seed_demo_history(db, FEMALE_DEMO_PROFILE_ID)
