"""
Deterministic health calculations — no AI, pure Python math.
These functions never call an external API.
"""
from typing import Optional


# ── Body metrics ──────────────────────────────────────────────────────────────

def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5:
        category, severity = "Underweight", "medium"
    elif bmi < 25.0:
        category, severity = "Normal weight", "none"
    elif bmi < 30.0:
        category, severity = "Overweight", "low"
    else:
        category, severity = "Obese", "medium"
    return {"bmi": round(bmi, 1), "category": category, "severity": severity}


# ── Hydration ─────────────────────────────────────────────────────────────────

def calculate_hydration_target(weight_kg: float) -> int:
    """30–35 ml per kg body weight — standard general guideline."""
    return int(weight_kg * 32)


def calculate_hydration_today(hydration_logs: list, date: str) -> int:
    return sum(h.amount_ml for h in hydration_logs if h.date == date)


def assess_hydration(today_ml: int, target_ml: int) -> dict:
    pct = round(today_ml / target_ml * 100) if target_ml > 0 else 0
    if pct >= 90:
        status, label = "good", "On target"
    elif pct >= 60:
        status, label = "fair", "Below target"
    else:
        status, label = "low", "Significantly below target"
    return {"percent": pct, "status": status, "label": label,
            "remaining_ml": max(0, target_ml - today_ml)}


# ── Nutrition ─────────────────────────────────────────────────────────────────

def calculate_nutrition_today(nutrition_logs: list, date: str) -> dict:
    today = [n for n in nutrition_logs if n.date == date]
    return {
        "total_calories": sum(n.calories for n in today),
        "total_protein_g": round(sum(n.protein_g for n in today), 1),
        "total_carbs_g": round(sum(n.carbs_g for n in today), 1),
        "total_fat_g": round(sum(n.fat_g for n in today), 1),
        "meal_count": len(today),
    }


def assess_nutrition(profile_sex: str, profile_age: int, nutrition: dict) -> dict:
    """
    Simple deterministic nutrition assessment against general targets.
    These are general population guidelines — not medical recommendations.
    """
    cal = nutrition["total_calories"]
    protein = nutrition["total_protein_g"]

    # Rough calorie targets by sex/age (general guideline only)
    if profile_sex == "male":
        cal_target = 2200 if profile_age < 50 else 2000
    else:
        cal_target = 1800 if profile_age < 50 else 1600

    # Protein target: 0.8g/kg body weight (we don't have weight here, use 0.8*70=56g as fallback)
    protein_target = 56 if profile_sex == "male" else 46

    cal_pct = round(cal / cal_target * 100) if cal_target > 0 else 0
    protein_pct = round(protein / protein_target * 100) if protein_target > 0 else 0

    return {
        "calorie_target": cal_target,
        "calorie_percent": cal_pct,
        "protein_target_g": protein_target,
        "protein_percent": protein_pct,
        "calorie_status": "good" if 80 <= cal_pct <= 120 else ("low" if cal_pct < 80 else "high"),
        "protein_status": "good" if protein_pct >= 80 else "low",
    }


# ── Sleep ─────────────────────────────────────────────────────────────────────

def calculate_avg_sleep(sleep_logs: list) -> float:
    if not sleep_logs:
        return 0.0
    return round(sum(s.hours_slept for s in sleep_logs) / len(sleep_logs), 1)


def assess_sleep(avg_hours: float) -> dict:
    if avg_hours >= 7:
        status, label, severity = "good", "Meeting target", "none"
    elif avg_hours >= 6:
        status, label, severity = "fair", "Slightly below target", "low"
    else:
        status, label, severity = "poor", "Below recommended range", "medium"
    return {"status": status, "label": label, "severity": severity,
            "target_hours": 7.0, "deficit_hours": round(max(0, 7.0 - avg_hours), 1)}


# ── Activity ──────────────────────────────────────────────────────────────────

def assess_activity(activity_logs: list, days: int = 7) -> dict:
    total_sessions = len(activity_logs)
    total_minutes = sum(a.duration_min for a in activity_logs)
    total_steps = sum(a.steps for a in activity_logs)

    # WHO guideline: 150 min moderate activity per week
    weekly_target_min = 150
    pct = round(total_minutes / weekly_target_min * 100) if weekly_target_min > 0 else 0

    if pct >= 100:
        status, label = "good", "Meeting weekly target"
    elif pct >= 50:
        status, label = "fair", "Partially meeting target"
    else:
        status, label = "low", "Below recommended activity"

    return {
        "sessions": total_sessions,
        "total_minutes": total_minutes,
        "total_steps": total_steps,
        "weekly_target_min": weekly_target_min,
        "percent": pct,
        "status": status,
        "label": label,
    }


# ── Biomarker status ──────────────────────────────────────────────────────────

def assess_biomarker_status(
    value: float,
    reference_low: Optional[float],
    reference_high: Optional[float],
) -> str:
    """
    Assign status based purely on reference range comparison.
    This is deterministic — AI never sets status values.
    """
    if reference_low is None and reference_high is None:
        return "normal"

    below_low = reference_low is not None and value < reference_low
    above_high = reference_high is not None and value > reference_high

    if not below_low and not above_high:
        return "normal"

    if below_low and reference_low is not None and reference_low > 0:
        pct_deviation = (reference_low - value) / reference_low
    elif above_high and reference_high is not None and reference_high > 0:
        pct_deviation = (value - reference_high) / reference_high
    else:
        pct_deviation = 0

    if pct_deviation >= 0.5:
        return "critical"
    return "low" if below_low else "high"


# ── Health priorities ─────────────────────────────────────────────────────────

def generate_health_priorities(
    biomarkers: list,
    hydration_ml: int,
    hydration_target: int,
    avg_sleep: float,
    nutrition: Optional[dict] = None,
    activity_pct: int = 0,
    bmi_category: str = "",
) -> list[dict]:
    """
    Build health priorities deterministically from all structured data sources.
    AI enriches interpretation text in Milestone 5 — trigger logic never changes.
    Priority order: critical biomarkers → high biomarkers → lifestyle factors.
    """
    priorities = []

    # --- Biomarker priorities ---
    # Sort: critical first, then high, then low
    abnormal = [b for b in biomarkers if b.status in ("low", "high", "critical")]
    abnormal.sort(key=lambda b: {"critical": 0, "high": 1, "low": 2}[b.status])

    for b in abnormal:
        severity = "high" if b.status in ("critical", "high") else "medium"
        ref_str = ""
        if b.reference_low is not None and b.reference_high is not None:
            ref_str = f"{b.reference_low}–{b.reference_high} {b.unit}"
        elif b.reference_high is not None:
            ref_str = f"< {b.reference_high} {b.unit}"
        elif b.reference_low is not None:
            ref_str = f"> {b.reference_low} {b.unit}"

        priorities.append({
            "id": f"priority-bm-{b.id}",
            "title": f"{b.status.title()} {b.name}",
            "observed_data": f"{b.name}: {b.value} {b.unit}"
                             + (f" — Reference: {ref_str}" if ref_str else ""),
            "ai_interpretation": (
                f"This result is {b.status} relative to the reference range shown on your report. "
                "This finding can have multiple explanations."
            ),
            "suggested_action": "Consider discussing this result with a qualified healthcare professional.",
            "severity": severity,
            "category": b.category,
            "source": "lab",
        })

    # --- Hydration priority ---
    hydration_pct = round(hydration_ml / hydration_target * 100) if hydration_target > 0 else 100
    if hydration_pct < 60:
        priorities.append({
            "id": "priority-hydration",
            "title": "Low Daily Hydration",
            "observed_data": f"Today's intake: {hydration_ml} ml — Target: {hydration_target} ml ({hydration_pct}%)",
            "ai_interpretation": (
                "Your recorded water intake is below the recommended target. "
                "Dehydration can contribute to fatigue and reduced concentration."
            ),
            "suggested_action": (
                "Aim to drink water regularly throughout the day. "
                "Replacing one cup of chai with water can help reach your target."
            ),
            "severity": "medium",
            "category": "Hydration",
            "source": "hydration",
        })

    # --- Sleep priority ---
    if 0 < avg_sleep < 7:
        sleep_assessment = assess_sleep(avg_sleep)
        priorities.append({
            "id": "priority-sleep",
            "title": "Insufficient Sleep",
            "observed_data": f"Average sleep: {avg_sleep} hours/night — Recommended: 7–9 hours",
            "ai_interpretation": (
                "Your average sleep duration is below the recommended range. "
                "Poor sleep is strongly associated with fatigue, mood changes, and impaired recovery."
            ),
            "suggested_action": "Aim for a consistent sleep schedule. Avoid screens 30 minutes before bed and keep a fixed wake time.",
            "severity": sleep_assessment["severity"],
            "category": "Sleep",
            "source": "sleep",
        })

    # --- Activity priority ---
    if 0 < activity_pct < 50:
        priorities.append({
            "id": "priority-activity",
            "title": "Low Physical Activity",
            "observed_data": f"Weekly activity: {activity_pct}% of recommended 150 minutes",
            "ai_interpretation": (
                "Your recorded physical activity is below the general recommendation of "
                "150 minutes of moderate activity per week."
            ),
            "suggested_action": "Consider adding a short daily walk. Even 20–30 minutes of brisk walking can make a significant difference.",
            "severity": "low",
            "category": "Activity",
            "source": "activity",
        })

    # --- BMI priority ---
    if bmi_category in ("Overweight", "Obese"):
        priorities.append({
            "id": "priority-bmi",
            "title": f"BMI: {bmi_category}",
            "observed_data": f"BMI classification: {bmi_category} — based on height and weight",
            "ai_interpretation": (
                "BMI is a general screening metric and does not diagnose any health condition. "
                "It can have multiple contributing factors."
            ),
            "suggested_action": "Discuss healthy weight management strategies with a qualified healthcare professional.",
            "severity": "low",
            "category": "Body Metrics",
            "source": "profile",
        })

    return priorities
