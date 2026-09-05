"""
Seeds the Bilal Ahmed synthetic demo profile into SQLite on startup.
Only runs if the profile does not already exist — safe to call on every restart.
Demo credentials are read from environment; seeding is skipped if DEMO_PASSWORD is unset.

Also seeds the Ayesha Khan female demo profile (Women's Health showcase),
kept separate from the male demo and never modified by it.
"""
from datetime import date, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dates import today_iso, days_ago_iso
from app.core.security import hash_password
from app.models.models import (
    User, HealthProfile, LabReport, Biomarker,
    HydrationLog, NutritionLog, SleepLog, ActivityLog, TimelineEvent,
    Cycle, PeriodDay, CycleSymptom,
)

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
