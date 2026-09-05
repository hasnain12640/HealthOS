"""
Builds the AI system prompt from live health data.
All data comes from ORM objects passed in — no extra DB calls.

The prompt uses clearly separated labeled sections so the AI
receives structured values and statuses rather than a text blob.
Biomarker status is deterministic — the AI receives the
pre-computed interpretation and explains it, never re-decides it.
"""
from app.models.models import HealthProfile, Biomarker, LabReport


def _format_reference(b: Biomarker) -> str:
    if b.reference_low is not None and b.reference_high is not None:
        return f"{b.reference_low}–{b.reference_high} {b.unit}"
    if b.reference_high is not None:
        return f"< {b.reference_high} {b.unit}"
    if b.reference_low is not None:
        return f"> {b.reference_low} {b.unit}"
    return ""


def _lab_results_section(biomarkers: list[Biomarker], latest_report: LabReport | None) -> str:
    abnormal = [b for b in biomarkers if b.status != "normal"]
    report_date = latest_report.report_date if latest_report else "not available"

    lines = [
        f"Report date: {report_date}",
        f"Biomarkers tested: {len(biomarkers)}",
        f"Outside reference range: {len(abnormal)}",
    ]
    if abnormal:
        lines.append("Abnormal biomarkers (status is pre-computed and deterministic):")
        for b in abnormal:
            ref = _format_reference(b)
            ref_str = f" (reference: {ref})" if ref else ""
            lines.append(f"  - {b.name}: {b.value} {b.unit}{ref_str} [STATUS: {b.status.upper()}]")
    else:
        lines.append("All tested biomarkers are within their reference ranges.")
    return "\n".join(lines)


def _nutrition_section(nutrition: dict | None, nutrition_assessment: dict | None) -> str:
    if not nutrition:
        return "No nutrition logged today."
    cal_target = nutrition_assessment.get("calorie_target", 2200) if nutrition_assessment else 2200
    protein_target = nutrition_assessment.get("protein_target_g", 56) if nutrition_assessment else 56
    return (
        f"Calories: {nutrition['total_calories']} / {cal_target} kcal target\n"
        f"Protein: {nutrition['total_protein_g']} / {protein_target} g target\n"
        f"Carbs: {nutrition['total_carbs_g']} g\n"
        f"Fat: {nutrition['total_fat_g']} g\n"
        f"Meals logged: {nutrition['meal_count']}"
    )


def _hydration_section(hydration_ml: int, hydration_target: int) -> str:
    pct = round(hydration_ml / hydration_target * 100) if hydration_target > 0 else 0
    status = "good" if pct >= 90 else "fair" if pct >= 60 else "low"
    return (
        f"Today's intake: {hydration_ml} ml / {hydration_target} ml target ({pct}%)\n"
        f"Status: {status}"
    )


def _sleep_section(avg_sleep: float) -> str:
    status = "good" if avg_sleep >= 7 else "fair" if avg_sleep >= 6 else "poor"
    return (
        f"Average (last 7 nights): {avg_sleep} hours/night\n"
        f"Target: 7–9 hours\n"
        f"Status: {status}"
    )


def _activity_section(activity_minutes: int) -> str:
    pct = round(activity_minutes / 150 * 100) if activity_minutes > 0 else 0
    status = "good" if pct >= 100 else "fair" if pct >= 50 else "low"
    return (
        f"Weekly total: {activity_minutes} min / 150 min target ({pct}%)\n"
        f"Status: {status}"
    )


def _wearable_section(wearable_summary: dict | None) -> str:
    if not wearable_summary:
        return "No wearable device connected."
    device_type = wearable_summary.get("device_type") or "wearable"
    lines = [f"Device: {wearable_summary.get('device_name', 'Connected device')} ({device_type})"]
    if wearable_summary.get("steps") is not None:
        lines.append(f"Steps: {wearable_summary['steps']:,}")
    if wearable_summary.get("resting_heart_rate") is not None:
        lines.append(f"Resting heart rate: {wearable_summary['resting_heart_rate']} bpm")
    if wearable_summary.get("sleep_hours") is not None:
        lines.append(f"Sleep: {wearable_summary['sleep_hours']} hours")
    if wearable_summary.get("sleep_score"):
        lines.append(f"Sleep score: {wearable_summary['sleep_score']}")
    if wearable_summary.get("active_calories") is not None:
        lines.append(f"Active calories: {wearable_summary['active_calories']} kcal")
    if wearable_summary.get("hydration_liters") is not None:
        lines.append(f"Hydration: {wearable_summary['hydration_liters']} L")
    if wearable_summary.get("distance_km") is not None:
        lines.append(f"Distance: {wearable_summary['distance_km']} km")
    return "\n".join(lines)


def _priorities_section(priorities: list[dict]) -> str:
    if not priorities:
        return "None identified."
    lines = []
    for i, p in enumerate(priorities[:6], 1):
        lines.append(
            f"  {i}. {p['title']} [severity: {p.get('severity', 'unknown')}]\n"
            f"     Observed: {p['observed_data']}"
        )
    return "\n".join(lines)


_PHASE_LABELS = {
    "menstrual": "Menstrual",
    "follicular": "Follicular",
    "ovulatory": "Ovulatory",
    "luteal": "Luteal",
}


def _cycle_section(cycle_summary: dict | None) -> str:
    if not cycle_summary:
        return ""
    lines = []
    if cycle_summary.get("current_cycle_day") is not None:
        phase = cycle_summary.get("current_phase") or ""
        phase_label = _PHASE_LABELS.get(phase, phase.title() if phase else "")
        lines.append(f"Cycle day: {cycle_summary['current_cycle_day']} ({phase_label} phase)")
    if cycle_summary.get("average_cycle_length") is not None:
        lines.append(f"Average cycle length: {cycle_summary['average_cycle_length']} days")
    if cycle_summary.get("average_period_length") is not None:
        lines.append(f"Average period length: {cycle_summary['average_period_length']} days")
    lines.append(f"Cycles tracked: {cycle_summary.get('cycles_tracked', 0)}")
    if cycle_summary.get("predicted_period_start"):
        lines.append(f"Estimated next period: {cycle_summary['predicted_period_start']} (estimate)")
    if cycle_summary.get("estimated_fertile_start") and cycle_summary.get("estimated_fertile_end"):
        lines.append(
            f"Estimated fertile window: {cycle_summary['estimated_fertile_start']} "
            f"to {cycle_summary['estimated_fertile_end']} (estimate)"
        )
    if cycle_summary.get("recent_symptoms"):
        parts = [
            f"{s['symptom_type'].replace('_', ' ')} ({s['severity']})"
            for s in cycle_summary["recent_symptoms"][:5]
        ]
        lines.append("Recent symptoms: " + ", ".join(parts))
    if cycle_summary.get("needs_more_data"):
        lines.append("Note: not enough cycle history for reliable predictions yet.")

    body = "\n".join(lines) if lines else "No cycle data logged yet."

    return f"""
=== WOMEN'S HEALTH ===
{body}

=== CYCLE-AWARE CONTEXT ===
- All cycle dates and phases above were pre-computed by a deterministic engine.
  NEVER recalculate dates, and never contradict or "correct" them.
- Cycle phase can influence energy, sleep, mood, cramping, and hydration needs —
  connect the phase with other health signals when relevant.
- NEVER diagnose PCOS, endometriosis, infertility, or any condition from cycle data.
- NEVER predict pregnancy or claim ovulation occurred. The fertile window is a
  statistical estimate only — cycle tracking cannot confirm ovulation or pregnancy.
"""


def build_system_prompt(
    profile: HealthProfile,
    biomarkers: list[Biomarker],
    latest_report: LabReport | None,
    hydration_ml: int,
    hydration_target: int,
    avg_sleep: float,
    activity_minutes: int,
    priorities: list[dict],
    bmi: float = 0.0,
    bmi_category: str = "",
    nutrition: dict | None = None,
    nutrition_assessment: dict | None = None,
    wearable_summary: dict | None = None,
    cycle_summary: dict | None = None,
) -> str:
    sex_label = "M" if profile.sex == "male" else "F"
    first_name = profile.user_name.split()[0]

    return f"""You are HealthOS AI Assistant — a health education tool, NOT a diagnostic tool.

=== USER PROFILE ===
Name: {profile.user_name}
Age/Sex: {profile.age} / {sex_label}
City: {profile.city}
Height: {profile.height_cm} cm
Weight: {profile.weight_kg} kg
BMI: {bmi} ({bmi_category})
Blood group: {profile.blood_group}

=== LAB RESULTS ===
{_lab_results_section(biomarkers, latest_report)}

=== NUTRITION ===
{_nutrition_section(nutrition, nutrition_assessment)}

=== HYDRATION ===
{_hydration_section(hydration_ml, hydration_target)}

=== SLEEP ===
{_sleep_section(avg_sleep)}

=== ACTIVITY ===
{_activity_section(activity_minutes)}

=== WEARABLE DATA ===
{_wearable_section(wearable_summary)}
{_cycle_section(cycle_summary)}
=== DETERMINISTIC HEALTH PRIORITIES ===
(Pre-computed by deterministic rules — do not re-derive statuses)
{_priorities_section(priorities)}

MANDATORY RESPONSE RULES:
1. NEVER diagnose. NEVER say the user "has" any condition or disease.
2. Always hedge: say "this result is outside the reference range" — not "you have anaemia".
3. Structure EVERY response using exactly these three bold headers on their own lines:
   **Observed Data:** [what the data shows]
   **AI Interpretation:** [educational explanation, hedged language]
   **Suggested Action:** [general guidance; always recommend a qualified professional]
4. End EVERY response with this exact line:
   *This response is for educational purposes only. Not a substitute for professional medical advice.*
5. Keep responses under 250 words. Be clear and direct.
6. Refer to the user by first name ({first_name}) when appropriate.
7. If asked something outside health education scope, politely decline and redirect.
8. When relevant, identify relationships BETWEEN health signals (e.g. sleep and labs,
   hydration and fatigue) rather than repeating individual numbers.
9. If data for a domain is missing or "not available", say so — never invent values."""
