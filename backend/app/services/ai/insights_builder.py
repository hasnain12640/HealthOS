"""
Builds the prompt for the unified dashboard AI insight.
Requests a strict JSON response so the insight can identify
cross-domain relationships between labs, lifestyle, and wearable data.

Biomarker statuses are pre-computed deterministically — the AI
receives the interpretation and explains it, never re-decides it.
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


def _lab_lines(biomarkers: list[Biomarker]) -> str:
    abnormal = [b for b in biomarkers if b.status != "normal"]
    if not abnormal:
        return "  All tested biomarkers within reference range."
    lines = []
    for b in abnormal:
        ref = _format_reference(b)
        ref_str = f" (ref: {ref})" if ref else ""
        lines.append(f"  - {b.name}: {b.value} {b.unit}{ref_str} [STATUS: {b.status.upper()}]")
    return "\n".join(lines)


def _nutrition_lines(nutrition: dict | None, nutrition_assessment: dict | None) -> str:
    if not nutrition:
        return "  No nutrition logged today."
    cal_target = nutrition_assessment.get("calorie_target", 2200) if nutrition_assessment else 2200
    protein_target = nutrition_assessment.get("protein_target_g", 56) if nutrition_assessment else 56
    return (
        f"  - Calories: {nutrition['total_calories']} / {cal_target} kcal target\n"
        f"  - Protein: {nutrition['total_protein_g']} / {protein_target} g target\n"
        f"  - Carbs: {nutrition['total_carbs_g']} g, Fat: {nutrition['total_fat_g']} g\n"
        f"  - Meals logged: {nutrition['meal_count']}"
    )


def _wearable_lines(wearable_summary: dict | None) -> str:
    if not wearable_summary:
        return "  No wearable device connected."
    device_type = wearable_summary.get("device_type") or "wearable"
    lines = [f"  - Device: {wearable_summary.get('device_name', 'Connected device')} ({device_type})"]
    if wearable_summary.get("steps") is not None:
        lines.append(f"  - Steps: {wearable_summary['steps']:,}")
    if wearable_summary.get("resting_heart_rate") is not None:
        lines.append(f"  - Resting HR: {wearable_summary['resting_heart_rate']} bpm")
    if wearable_summary.get("sleep_hours") is not None:
        lines.append(f"  - Sleep: {wearable_summary['sleep_hours']} hours")
    if wearable_summary.get("sleep_score"):
        lines.append(f"  - Sleep score: {wearable_summary['sleep_score']}")
    if wearable_summary.get("active_calories") is not None:
        lines.append(f"  - Active calories: {wearable_summary['active_calories']} kcal")
    if wearable_summary.get("hydration_liters") is not None:
        lines.append(f"  - Hydration: {wearable_summary['hydration_liters']} L")
    if wearable_summary.get("distance_km") is not None:
        lines.append(f"  - Distance: {wearable_summary['distance_km']} km")
    return "\n".join(lines)


def _priority_lines(priorities: list[dict]) -> str:
    if not priorities:
        return "  None identified."
    return "\n".join(
        f"  {i}. {p['title']} [severity: {p.get('severity', 'unknown')}] — {p['observed_data']}"
        for i, p in enumerate(priorities[:6], 1)
    )


_PHASE_LABELS = {
    "menstrual": "Menstrual",
    "follicular": "Follicular",
    "ovulatory": "Ovulatory",
    "luteal": "Luteal",
}


def _cycle_lines(cycle_summary: dict | None) -> str:
    if not cycle_summary:
        return ""
    lines = []
    if cycle_summary.get("current_cycle_day") is not None:
        phase = cycle_summary.get("current_phase") or ""
        phase_label = _PHASE_LABELS.get(phase, phase.title() if phase else "")
        lines.append(f"  - Cycle day: {cycle_summary['current_cycle_day']} ({phase_label} phase)")
    if cycle_summary.get("average_cycle_length") is not None:
        lines.append(f"  - Average cycle length: {cycle_summary['average_cycle_length']} days")
    if cycle_summary.get("average_period_length") is not None:
        lines.append(f"  - Average period length: {cycle_summary['average_period_length']} days")
    lines.append(f"  - Cycles tracked: {cycle_summary.get('cycles_tracked', 0)}")
    if cycle_summary.get("predicted_period_start"):
        lines.append(f"  - Estimated next period: {cycle_summary['predicted_period_start']} (estimate)")
    if cycle_summary.get("estimated_fertile_start") and cycle_summary.get("estimated_fertile_end"):
        lines.append(
            f"  - Estimated fertile window: {cycle_summary['estimated_fertile_start']} "
            f"to {cycle_summary['estimated_fertile_end']} (estimate)"
        )
    if cycle_summary.get("recent_symptoms"):
        parts = [
            f"{s['symptom_type'].replace('_', ' ')} ({s['severity']})"
            for s in cycle_summary["recent_symptoms"][:5]
        ]
        lines.append("  - Recent symptoms: " + ", ".join(parts))
    if not lines:
        return ""
    return (
        "\n=== WOMEN'S HEALTH ===\n" + "\n".join(lines) +
        "\n\n=== CYCLE-AWARE CONTEXT ===\n"
        "  All cycle dates and phases above were pre-computed by a deterministic engine —\n"
        "  never recalculate or contradict them. Connect the current phase with other\n"
        "  signals (sleep, hydration, energy, cramping) where relevant. NEVER diagnose\n"
        "  PCOS, endometriosis, or infertility; NEVER predict pregnancy or claim ovulation\n"
        "  occurred — the fertile window is a statistical estimate only.\n"
    )


def build_insight_prompt(
    profile: HealthProfile,
    biomarkers: list[Biomarker],
    hydration_pct: int,
    avg_sleep: float,
    priorities: list[dict],
    latest_report: LabReport | None = None,
    wearable_summary: dict | None = None,
    nutrition: dict | None = None,
    nutrition_assessment: dict | None = None,
    activity_pct: int = 0,
    bmi: float = 0.0,
    bmi_category: str = "",
    cycle_summary: dict | None = None,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_message) for unified insight generation.
    The AI must respond with valid JSON matching the structured schema.
    """
    sex_label = "male" if profile.sex == "male" else "female"
    first_name = profile.user_name.split()[0]
    report_date = latest_report.report_date if latest_report else "not available"

    system_prompt = f"""You are HealthOS AI, a health education assistant that identifies relationships BETWEEN health signals.
Generate a unified health insight for {profile.user_name}, a {profile.age}-year-old {sex_label} from {profile.city}.

=== USER PROFILE ===
Name: {profile.user_name}, Age: {profile.age}, Sex: {sex_label}
City: {profile.city}
BMI: {bmi} ({bmi_category})

=== LAB RESULTS ===
Report date: {report_date}
{_lab_lines(biomarkers)}

=== NUTRITION ===
{_nutrition_lines(nutrition, nutrition_assessment)}

=== HYDRATION ===
Today's intake: {hydration_pct}% of daily target

=== SLEEP ===
Average: {avg_sleep} hours/night (target 7–9 hours)

=== ACTIVITY ===
Weekly activity: {activity_pct}% of 150-minute target

=== WEARABLE DATA ===
{_wearable_lines(wearable_summary)}
{_cycle_lines(cycle_summary)}
=== DETERMINISTIC HEALTH PRIORITIES ===
(Pre-computed by deterministic rules — statuses are final, do not re-derive)
{_priority_lines(priorities)}

YOUR TASK:
Synthesize these signals into a unified insight. Do NOT simply repeat numbers —
identify meaningful relationships between domains (e.g. sleep + labs,
hydration + fatigue, wearable activity + recovery).

Return ONLY a valid JSON object with exactly this structure:
{{
  "headline": "<one-line personalized title, max 12 words>",
  "summary": "<2-3 sentence overview referencing specific data>",
  "observed_data": [
    {{"domain": "<labs|hydration|sleep|activity|nutrition|wearable|cycle>", "observation": "<what was measured>", "value": "<the value with unit>"}}
  ],
  "cross_domain_connections": [
    {{"domains": ["<domain1>", "<domain2>"], "relationship": "<short label>", "explanation": "<how these signals may relate, 1-2 sentences>"}}
  ],
  "priorities": [
    {{"title": "<short title>", "rationale": "<why this matters based on data>", "suggested_action": "<practical next step>", "related_domains": ["<domain>"], "urgency": "<high|medium|low>"}}
  ],
  "safety_note": "<educational disclaimer>"
}}

RULES:
1. Output ONLY valid JSON. No markdown fences, no preamble, no explanation outside JSON.
2. NEVER diagnose. NEVER say the user "has" any condition (no "you have diabetes/anemia/heart disease").
3. Use hedged language: "is outside the reference range", "may be worth discussing with a
   qualified healthcare professional", "there are multiple possible explanations".
4. observed_data must contain 4-6 items covering multiple domains actually present in context.
5. cross_domain_connections must contain 1-3 items linking DIFFERENT domains.
6. priorities must contain 3-5 items ordered by urgency, based on the combined context
   (not simply sorted by abnormal lab values).
7. Never invent values. If a domain has no data, omit it from observed_data.
8. Reference {first_name} naturally in the summary.
9. suggested_action must be practical lifestyle guidance, never medication or medical treatment."""

    user_message = f"Generate a structured health insight JSON for {profile.user_name}."
    return system_prompt, user_message


def get_mock_insight(
    profile: HealthProfile,
    biomarkers: list[Biomarker],
    hydration_pct: int,
    hydration_ml: int,
    hydration_target: int,
    avg_sleep: float,
    priorities: list[dict],
    wearable_summary: dict | None = None,
    nutrition: dict | None = None,
    activity_pct: int = 0,
    bmi: float = 0.0,
    bmi_category: str = "",
    cycle_summary: dict | None = None,
) -> dict:
    """
    Deterministic mock insight matching the structured schema, built from the
    caller's live health context. Used when AI_PROVIDER=mock or as fallback
    when Qwen fails. All values come from actual application data.
    """
    first_name = profile.user_name.split()[0]
    abnormal = sorted(
        [b for b in biomarkers if b.status != "normal"],
        key=lambda b: {"critical": 0, "high": 1, "low": 2}.get(b.status, 3),
    )
    wearable = wearable_summary or {}

    # --- observed_data ---
    observed_data: list[dict] = []
    for b in abnormal[:3]:
        ref = _format_reference(b)
        ref_str = f" (ref: {ref})" if ref else ""
        observed_data.append({
            "domain": "labs",
            "observation": f"{b.name} {b.status} relative to reference range",
            "value": f"{b.value} {b.unit}{ref_str}",
        })
    if avg_sleep > 0:
        observed_data.append({
            "domain": "sleep",
            "observation": "Average nightly sleep",
            "value": f"{avg_sleep} hours/night (target: 7)",
        })
    observed_data.append({
        "domain": "hydration",
        "observation": "Daily hydration",
        "value": f"{hydration_ml:,} ml of {hydration_target:,} ml target ({hydration_pct}%)",
    })
    if nutrition and nutrition.get("meal_count", 0) > 0:
        observed_data.append({
            "domain": "nutrition",
            "observation": "Calories logged today",
            "value": f"{nutrition['total_calories']:,} kcal across {nutrition['meal_count']} meals",
        })
    if wearable.get("steps") is not None:
        observed_data.append({
            "domain": "wearable",
            "observation": "Steps recorded by connected device",
            "value": f"{wearable['steps']:,} steps",
        })
    if wearable.get("resting_heart_rate") is not None:
        observed_data.append({
            "domain": "wearable",
            "observation": "Resting heart rate",
            "value": f"{wearable['resting_heart_rate']} bpm",
        })
    if cycle_summary and cycle_summary.get("current_cycle_day") is not None:
        phase = cycle_summary.get("current_phase") or ""
        phase_label = _PHASE_LABELS.get(phase, phase.title() if phase else "")
        observed_data.append({
            "domain": "cycle",
            "observation": f"Current cycle position ({phase_label} phase)",
            "value": f"Day {cycle_summary['current_cycle_day']} of ~{cycle_summary.get('average_cycle_length') or 28} day cycle",
        })
        if cycle_summary.get("recent_symptoms"):
            parts = [
                f"{s['symptom_type'].replace('_', ' ')} ({s['severity']})"
                for s in cycle_summary["recent_symptoms"][:3]
            ]
            observed_data.append({
                "domain": "cycle",
                "observation": "Recently logged cycle symptoms",
                "value": ", ".join(parts),
            })

    # --- cross_domain_connections ---
    connections: list[dict] = []
    if abnormal and 0 < avg_sleep < 7:
        connections.append({
            "domains": ["labs", "sleep"],
            "relationship": "Lab findings and short sleep may compound fatigue",
            "explanation": (
                f"Results outside the reference range combined with an average of "
                f"{avg_sleep} hours of sleep can both contribute to tiredness. "
                "There are multiple possible explanations for this pattern."
            ),
        })
    if hydration_pct < 60 and wearable.get("steps") is not None:
        connections.append({
            "domains": ["hydration", "wearable"],
            "relationship": "Low hydration alongside an active day",
            "explanation": (
                f"The connected device shows {wearable['steps']:,} steps, but fluid "
                "intake is well below target — even mild dehydration can amplify "
                "feelings of fatigue."
            ),
        })
    if abnormal and hydration_pct < 60:
        connections.append({
            "domains": ["labs", "hydration"],
            "relationship": "Low fluid intake can affect blood results",
            "explanation": (
                "Dehydration can make blood values slightly more concentrated, so "
                "low fluid intake and results outside the reference range can be "
                "related rather than independent findings."
            ),
        })
    if not connections and wearable.get("steps") is not None:
        connections.append({
            "domains": ["activity", "wearable"],
            "relationship": "Consistent activity tracking",
            "explanation": (
                "Logged activity and wearable-recorded steps are being tracked "
                "together, giving a reliable picture of daily movement."
            ),
        })
    if cycle_summary and cycle_summary.get("current_cycle_day") is not None:
        phase = cycle_summary.get("current_phase") or ""
        phase_label = _PHASE_LABELS.get(phase, phase.title() if phase else "")
        symptom_types = {s["symptom_type"] for s in cycle_summary.get("recent_symptoms", [])}
        if phase in ("luteal", "menstrual") and 0 < avg_sleep < 7:
            connections.append({
                "domains": ["cycle", "sleep"],
                "relationship": "Late-cycle phase and short sleep may compound fatigue",
                "explanation": (
                    f"The {phase_label.lower()} phase is often associated with lower energy, "
                    f"and an average of {avg_sleep} hours of sleep per night may amplify "
                    "tiredness during this part of the cycle. Multiple explanations are possible."
                ),
            })
        if symptom_types & {"cramps", "fatigue", "headache"} and hydration_pct < 60:
            connections.append({
                "domains": ["cycle", "hydration"],
                "relationship": "Cycle symptoms and low fluid intake",
                "explanation": (
                    "Logged cycle symptoms combined with hydration well below target can "
                    "reinforce each other — mild dehydration can worsen headaches and "
                    "feelings of fatigue. Staying hydrated may help ease these symptoms."
                ),
            })

    # --- priorities (mapped from the deterministic priorities) ---
    domain_by_source = {
        "lab": ["labs"],
        "hydration": ["hydration"],
        "sleep": ["sleep"],
        "activity": ["activity"],
        "profile": ["nutrition", "activity"],
    }
    insight_priorities = [
        {
            "title": p["title"],
            "rationale": p["observed_data"],
            "suggested_action": p["suggested_action"],
            "related_domains": domain_by_source.get(p.get("source", "profile"), ["labs"]),
            "urgency": p.get("severity", "low") if p.get("severity") in ("high", "medium", "low") else "low",
        }
        for p in priorities[:5]
    ]
    if not insight_priorities:
        insight_priorities = [{
            "title": "Maintain current health routine",
            "rationale": "No health signals outside expected ranges were identified",
            "suggested_action": "Keep logging meals, hydration, and sleep to preserve this picture over time.",
            "related_domains": ["sleep", "nutrition"],
            "urgency": "low",
        }]
    if (
        cycle_summary
        and cycle_summary.get("current_phase") in ("luteal", "menstrual")
        and cycle_summary.get("recent_symptoms")
    ):
        phase = cycle_summary.get("current_phase") or ""
        phase_label = _PHASE_LABELS.get(phase, phase.title() if phase else "")
        parts = [
            f"{s['symptom_type'].replace('_', ' ')} ({s['severity']})"
            for s in cycle_summary["recent_symptoms"][:3]
        ]
        insight_priorities.append({
            "title": f"Support your body through the {phase_label.lower()} phase",
            "rationale": (
                f"Cycle day {cycle_summary.get('current_cycle_day')} with recent symptoms: {', '.join(parts)}"
            ),
            "suggested_action": (
                "Prioritise rest, steady hydration, and iron-rich meals; gentle "
                "movement like walking may ease symptoms."
            ),
            "related_domains": ["cycle", "hydration"],
            "urgency": "low",
        })

    # --- headline + summary ---
    if abnormal and 0 < avg_sleep < 7:
        headline = "Lab results and sleep patterns warrant attention"
    elif abnormal:
        headline = "Lab results outside reference range need follow-up"
    elif 0 < avg_sleep < 7:
        headline = "Sleep below target is the main signal this week"
    else:
        headline = "Health signals are within expected ranges"

    summary_bits: list[str] = []
    if abnormal:
        plural = "biomarkers are" if len(abnormal) > 1 else "biomarker is"
        summary_bits.append(
            f"{len(abnormal)} {plural} outside their reference ranges "
            f"(including {abnormal[0].name} at {abnormal[0].value} {abnormal[0].unit})"
        )
    if 0 < avg_sleep < 7:
        summary_bits.append(f"average sleep is {avg_sleep} hours against a 7-hour target")
    if hydration_pct < 60:
        summary_bits.append(f"hydration has reached {hydration_pct}% of the daily target")
    if wearable.get("steps") is not None:
        summary_bits.append(f"the connected device recorded {wearable['steps']:,} steps")
    if cycle_summary and cycle_summary.get("current_cycle_day") is not None:
        phase = cycle_summary.get("current_phase") or ""
        phase_label = _PHASE_LABELS.get(phase, phase.title() if phase else "")
        summary_bits.append(
            f"the current cycle is on day {cycle_summary['current_cycle_day']} "
            f"({phase_label.lower()} phase)"
        )
    if not summary_bits:
        summary_bits.append("tracked health signals are within expected ranges")

    if len(summary_bits) == 1:
        lead = f"{first_name}'s current data shows {summary_bits[0]}"
    else:
        lead = f"{first_name}'s current data shows " + ", ".join(summary_bits[:-1]) + f", and {summary_bits[-1]}"
    summary = (
        lead + ". These patterns can have multiple explanations and are best "
        "reviewed together with a qualified professional."
    )

    return {
        "headline": headline,
        "summary": summary,
        "observed_data": observed_data,
        "cross_domain_connections": connections,
        "priorities": insight_priorities,
        "safety_note": (
            "This insight is for educational purposes only and does not constitute a diagnosis. "
            "Please consult a qualified healthcare professional for personalized medical advice."
        ),
    }
