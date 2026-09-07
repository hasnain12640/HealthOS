"""
30-day Health History aggregation service.

This service pulls together every deterministic signal HealthOS stores — labs,
lifestyle logs, wearables, timeline events, and cycle data — into a single
per-day view. It contains no AI: status values come from the existing
deterministic health calculations module.
"""
import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.dates import days_ago_iso, today_iso
from app.models.models import (
    ActivityLog,
    Biomarker,
    Cycle,
    CycleSymptom,
    HealthProfile,
    HydrationLog,
    InsightRecord,
    LabReport,
    NutritionLog,
    SleepLog,
    TimelineEvent,
    WearableConnection,
    WearableMetric,
)
from app.services.cycle.cycle_engine import _phase_for_day
from app.services.deterministic.health_calculations import (
    assess_activity,
    assess_biomarker_status,
    assess_hydration,
    assess_sleep,
    calculate_avg_sleep,
    calculate_bmi,
    calculate_hydration_target,
    calculate_nutrition_today,
    generate_health_priorities,
)


def _to_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_range(days: int) -> tuple[date, date]:
    today = date.today()
    start = today - timedelta(days=days - 1)
    return start, today


def _iso_range(days: int) -> tuple[str, str]:
    start, end = _date_range(days)
    return start.isoformat(), end.isoformat()


def _dt_start(iso: str) -> datetime:
    return datetime.combine(_to_date(iso), time.min)


def _dt_end(iso: str) -> datetime:
    return datetime.combine(_to_date(iso), time.max)


def _hydration_for_date(
    logs: list[HydrationLog], date_str: str, target_ml: int
) -> dict:
    amount = sum(h.amount_ml for h in logs if h.date == date_str)
    assessment = assess_hydration(amount, target_ml)
    return {
        "amount_ml": amount,
        "target_ml": target_ml,
        "percent": assessment["percent"],
        "status": assessment["status"],
        "label": assessment["label"],
    }


def _sleep_for_date(logs: list[SleepLog], date_str: str) -> Optional[dict]:
    entries = [s for s in logs if s.date == date_str]
    if not entries:
        return None
    hours = round(sum(s.hours_slept for s in entries) / len(entries), 1)
    quality = round(sum(s.quality for s in entries) / len(entries))
    assessment = assess_sleep(hours)
    return {
        "hours_slept": hours,
        "quality": quality,
        "status": assessment["status"],
        "label": assessment["label"],
    }


def _activity_for_date(logs: list[ActivityLog], date_str: str) -> dict:
    entries = [a for a in logs if a.date == date_str]
    return {
        "steps": sum(a.steps for a in entries),
        "duration_min": sum(a.duration_min for a in entries),
        "sessions": len(entries),
    }


def _nutrition_for_date(logs: list[NutritionLog], date_str: str) -> dict:
    return calculate_nutrition_today(logs, date_str)


def _labs_for_date(reports: list[LabReport], date_str: str) -> list[dict]:
    return [
        {
            "id": r.id,
            "lab_name": r.lab_name,
            "report_date": r.report_date,
            "upload_date": r.upload_date,
            "biomarkers": [
                {
                    "id": b.id,
                    "name": b.name,
                    "value": b.value,
                    "unit": b.unit,
                    "reference_low": b.reference_low,
                    "reference_high": b.reference_high,
                    "status": b.status,
                    "category": b.category,
                }
                for b in r.biomarkers
            ],
        }
        for r in reports
        if r.report_date == date_str
    ]


def _events_for_date(events: list[TimelineEvent], date_str: str) -> list[dict]:
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "is_ai_generated": e.is_ai_generated,
        }
        for e in events
        if e.date == date_str
    ]


def _build_cycle_lookup(cycles: list[Cycle]) -> tuple[list[dict], int, int]:
    """Normalize cycle rows into date-aware structs plus average lengths."""
    infos = []
    completed_lengths = []
    period_lengths = []

    for c in cycles:
        start = _to_date(c.start_date)
        end = _to_date(c.end_date) if c.end_date else None
        period_days = set()
        flow_by_date = {}
        for p in c.period_days:
            period_days.add(p.date)
            flow_by_date[p.date] = p.flow_level

        infos.append(
            {
                "start": start,
                "end": end,
                "period_days": period_days,
                "flow_by_date": flow_by_date,
                "cycle_length": c.cycle_length,
                "period_length": c.period_length,
            }
        )

        if c.cycle_length:
            completed_lengths.append(c.cycle_length)
        if c.period_length:
            period_lengths.append(c.period_length)

    avg_cycle = round(sum(completed_lengths) / len(completed_lengths)) if completed_lengths else 28
    avg_period = round(sum(period_lengths) / len(period_lengths)) if period_lengths else 5
    return infos, avg_cycle, avg_period


def _cycle_for_date(
    cycle_infos: list[dict],
    avg_cycle: int,
    avg_period: int,
    symptoms_by_date: dict[str, list[str]],
    d: date,
) -> Optional[dict]:
    active = None
    for c in cycle_infos:
        if c["start"] <= d and (c["end"] is None or d <= c["end"]):
            active = c
            break
    if not active:
        return None

    cycle_day = (d - active["start"]).days + 1
    length = active["cycle_length"] or avg_cycle
    period_len = active["period_length"] or avg_period
    phase, phase_day = _phase_for_day(cycle_day, length, period_len)

    iso = d.isoformat()
    is_period = iso in active["period_days"]
    flow_level = active["flow_by_date"].get(iso) if is_period else None

    ovulation_day = length - 14
    is_fertile = ovulation_day - 5 <= cycle_day <= ovulation_day + 1

    return {
        "phase": phase,
        "phase_day": phase_day,
        "cycle_day": cycle_day,
        "is_period": is_period,
        "flow_level": flow_level,
        "is_fertile_window": is_fertile,
        "symptoms": symptoms_by_date.get(iso, []),
    }


def _wearable_metrics_by_date(
    connection_id: str, start_iso: str, end_iso: str, db: Session
) -> dict[str, dict[str, float]]:
    """Return {date_iso: {metric_type: value}} for the active wearable."""
    metrics = (
        db.query(WearableMetric)
        .filter(
            WearableMetric.connection_id == connection_id,
            WearableMetric.recorded_at >= _dt_start(start_iso),
            WearableMetric.recorded_at <= _dt_end(end_iso),
        )
        .order_by(desc(WearableMetric.recorded_at))
        .all()
    )

    # Keep the latest value per metric_type per date.
    best: dict[str, dict[str, tuple[datetime, float]]] = defaultdict(dict)
    for m in metrics:
        d = m.recorded_at.date().isoformat()
        current = best[d].get(m.metric_type)
        if current is None or m.recorded_at > current[0]:
            best[d][m.metric_type] = (m.recorded_at, m.value)

    return {d: {k: v[1] for k, v in per_type.items()} for d, per_type in best.items()}


def _metric(day: dict[str, float], key: str) -> Optional[float | int]:
    val = day.get(key)
    return None if val is None else val


def build_history(profile: HealthProfile, db: Session, days: int = 30) -> dict:
    days = max(1, min(90, days))
    start_iso, end_iso = _iso_range(days)
    profile_id = profile.id
    today = today_iso()

    # --- Core lifestyle logs in range ---
    hydration_logs = (
        db.query(HydrationLog)
        .filter(HydrationLog.profile_id == profile_id)
        .all()
    )
    nutrition_logs = (
        db.query(NutritionLog)
        .filter(NutritionLog.profile_id == profile_id)
        .all()
    )
    sleep_logs = (
        db.query(SleepLog)
        .filter(SleepLog.profile_id == profile_id)
        .all()
    )
    activity_logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.profile_id == profile_id)
        .all()
    )
    reports = (
        db.query(LabReport)
        .filter(
            LabReport.profile_id == profile_id,
            LabReport.report_date >= start_iso,
            LabReport.report_date <= end_iso,
        )
        .all()
    )
    # Eager-load biomarkers for the reports in range.
    report_ids = [r.id for r in reports]
    biomarkers = (
        db.query(Biomarker)
        .filter(Biomarker.report_id.in_(report_ids))
        .all()
    )
    biomarkers_by_report: dict[str, list[Biomarker]] = defaultdict(list)
    for b in biomarkers:
        biomarkers_by_report[b.report_id].append(b)
    for r in reports:
        r.biomarkers = biomarkers_by_report.get(r.id, [])

    timeline_events = (
        db.query(TimelineEvent)
        .filter(
            TimelineEvent.profile_id == profile_id,
            TimelineEvent.date >= start_iso,
            TimelineEvent.date <= end_iso,
        )
        .all()
    )

    # --- Wearable data in range ---
    wearable_conn = (
        db.query(WearableConnection)
        .filter(
            WearableConnection.profile_id == profile_id,
            WearableConnection.status == "connected",
        )
        .first()
    )
    wearable_by_date: dict[str, dict[str, float]] = {}
    wearable_summary = None
    if wearable_conn:
        wearable_by_date = _wearable_metrics_by_date(
            wearable_conn.id, start_iso, end_iso, db
        )
        wearable_summary = {
            "connection_id": wearable_conn.id,
            "device_name": wearable_conn.device_name,
            "device_type": wearable_conn.device_type,
            "provider": wearable_conn.provider,
            "last_synced_at": wearable_conn.last_synced_at.isoformat(),
        }

    # --- Cycle data (female profiles only) ---
    cycle_infos, avg_cycle, avg_period = [], 28, 5
    symptoms_by_date: dict[str, list[str]] = defaultdict(list)
    if profile.sex == "female":
        cycles = db.query(Cycle).filter(Cycle.profile_id == profile_id).all()
        # Eager-load period days.
        for c in cycles:
            _ = c.period_days
        cycle_infos, avg_cycle, avg_period = _build_cycle_lookup(cycles)
        symptoms = db.query(CycleSymptom).filter(CycleSymptom.profile_id == profile_id).all()
        for s in symptoms:
            symptoms_by_date[s.date].append(s.symptom_type)

    # --- Per-day assembly ---
    target_ml = calculate_hydration_target(profile.weight_kg)
    start_date, end_date = _date_range(days)
    result_days = []
    for offset in range(days):
        d = start_date + timedelta(days=offset)
        iso = d.isoformat()

        w_day = wearable_by_date.get(iso, {})
        wearable_day = {
            "steps": int(_metric(w_day, "steps")) if _metric(w_day, "steps") is not None else None,
            "active_calories": int(_metric(w_day, "active_calories"))
            if _metric(w_day, "active_calories") is not None
            else None,
            "resting_heart_rate": int(_metric(w_day, "resting_heart_rate"))
            if _metric(w_day, "resting_heart_rate") is not None
            else None,
            "avg_heart_rate": int(_metric(w_day, "avg_heart_rate"))
            if _metric(w_day, "avg_heart_rate") is not None
            else None,
            "sleep_hours": _metric(w_day, "sleep"),
            "distance_km": _metric(w_day, "distance"),
            "water_ml": int(_metric(w_day, "water")) if _metric(w_day, "water") is not None else None,
            "weight_kg": _metric(w_day, "weight"),
        }

        day_entry = {
            "date": iso,
            "is_today": iso == today,
            "wearable": wearable_day,
            "hydration": _hydration_for_date(hydration_logs, iso, target_ml),
            "sleep": _sleep_for_date(sleep_logs, iso),
            "activity": _activity_for_date(activity_logs, iso),
            "nutrition": _nutrition_for_date(nutrition_logs, iso),
            "labs": _labs_for_date(reports, iso),
            "events": _events_for_date(timeline_events, iso),
        }
        if profile.sex == "female":
            day_entry["cycle"] = _cycle_for_date(
                cycle_infos, avg_cycle, avg_period, symptoms_by_date, d
            )

        result_days.append(day_entry)

    # --- Summary aggregates ---
    step_days = [d["wearable"]["steps"] for d in result_days if d["wearable"]["steps"] is not None]
    sleep_days = [d["sleep"]["hours_slept"] for d in result_days if d["sleep"]]
    hydration_pcts = [d["hydration"]["percent"] for d in result_days]
    activity_mins = [d["activity"]["duration_min"] for d in result_days if d["activity"]["duration_min"] > 0]
    all_biomarkers = [b for r in reports for b in r.biomarkers]
    abnormal_biomarkers = [b for b in all_biomarkers if b.status != "normal"]

    period_days = 0
    fertile_days = 0
    if profile.sex == "female":
        for d in result_days:
            c = d.get("cycle")
            if c:
                if c["is_period"]:
                    period_days += 1
                if c["is_fertile_window"]:
                    fertile_days += 1

    # --- Current deterministic priorities ---
    bmi_data = calculate_bmi(profile.weight_kg, profile.height_cm)
    latest_report = (
        db.query(LabReport)
        .filter(LabReport.profile_id == profile_id)
        .order_by(desc(LabReport.report_date))
        .first()
    )
    latest_biomarkers = []
    if latest_report:
        latest_biomarkers = (
            db.query(Biomarker)
            .filter(Biomarker.report_id == latest_report.id)
            .all()
        )
    hydration_today = sum(h.amount_ml for h in hydration_logs if h.date == today)
    sleep_7 = (
        db.query(SleepLog)
        .filter(SleepLog.profile_id == profile_id)
        .order_by(desc(SleepLog.date))
        .limit(7)
        .all()
    )
    activity_7 = (
        db.query(ActivityLog)
        .filter(ActivityLog.profile_id == profile_id)
        .order_by(desc(ActivityLog.date))
        .limit(7)
        .all()
    )
    nutrition_today = calculate_nutrition_today(nutrition_logs, today)
    activity_info = assess_activity(activity_7)

    priorities = generate_health_priorities(
        biomarkers=latest_biomarkers,
        hydration_ml=hydration_today,
        hydration_target=target_ml,
        avg_sleep=calculate_avg_sleep(sleep_7),
        nutrition=nutrition_today,
        activity_pct=activity_info["percent"],
        bmi_category=bmi_data["category"],
    )

    # --- Latest AI insight (if any) ---
    latest_insight = (
        db.query(InsightRecord)
        .filter(InsightRecord.profile_id == profile_id)
        .order_by(desc(InsightRecord.generated_at))
        .first()
    )
    ai_insight = None
    if latest_insight and latest_insight.insight_json:
        try:
            ai_insight = json.loads(latest_insight.insight_json)
        except json.JSONDecodeError:
            ai_insight = None

    summary = {
        "days_count": len(result_days),
        "avg_steps": round(sum(step_days) / len(step_days)) if step_days else 0,
        "avg_sleep_hours": round(sum(sleep_days) / len(sleep_days), 1) if sleep_days else 0.0,
        "avg_hydration_percent": round(sum(hydration_pcts) / len(hydration_pcts)) if hydration_pcts else 0,
        "avg_hydration_ml": round(
            sum(d["hydration"]["amount_ml"] for d in result_days) / days
        ),
        "total_activity_minutes": sum(activity_mins),
        "total_reports": len(reports),
        "total_biomarkers": len(all_biomarkers),
        "abnormal_biomarker_count": len(abnormal_biomarkers),
        "period_days": period_days,
        "fertile_window_days": fertile_days,
        "priorities": priorities,
        "ai_insight": ai_insight,
    }

    return {
        "profile": {
            "id": profile.id,
            "user_name": profile.user_name,
            "age": profile.age,
            "sex": profile.sex,
            "weight_kg": profile.weight_kg,
            "height_cm": profile.height_cm,
            "bmi": bmi_data["bmi"],
            "bmi_category": bmi_data["category"],
        },
        "days": days,
        "date_range": {"start": start_iso, "end": end_iso},
        "summary": summary,
        "wearable": wearable_summary,
        "daily": result_days,
    }
