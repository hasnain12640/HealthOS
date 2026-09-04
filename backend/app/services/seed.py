"""
Seeds the Bilal Ahmed synthetic demo profile into SQLite on startup.
Only runs if the profile does not already exist — safe to call on every restart.
Demo credentials are read from environment; seeding is skipped if DEMO_PASSWORD is unset.
"""
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dates import today_iso, days_ago_iso
from app.core.security import hash_password
from app.models.models import (
    User, HealthProfile, LabReport, Biomarker,
    HydrationLog, NutritionLog, SleepLog, ActivityLog, TimelineEvent,
)

DEMO_USER_ID = "demo-user-001"
DEMO_PROFILE_ID = "demo-001"


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
