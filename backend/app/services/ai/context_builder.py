"""
Builds the AI system prompt from live health data.
All data comes from ORM objects passed in — no extra DB calls.
"""
from app.models.models import HealthProfile, Biomarker, LabReport


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
) -> str:
    sex_label = "M" if profile.sex == "male" else "F"

    # Abnormal biomarkers
    abnormal = [b for b in biomarkers if b.status != "normal"]
    bm_lines = []
    for b in abnormal:
        ref = ""
        if b.reference_low is not None and b.reference_high is not None:
            ref = f"{b.reference_low}–{b.reference_high} {b.unit}"
        elif b.reference_high is not None:
            ref = f"< {b.reference_high} {b.unit}"
        elif b.reference_low is not None:
            ref = f"> {b.reference_low} {b.unit}"
        ref_str = f" (reference: {ref})" if ref else ""
        bm_lines.append(f"  - {b.name}: {b.value} {b.unit}{ref_str} [{b.status.upper()}]")

    bm_section = "\n".join(bm_lines) if bm_lines else "  - All tested biomarkers within reference range"

    report_date = latest_report.report_date if latest_report else "not available"
    total_bm = len(biomarkers)
    abnormal_count = len(abnormal)

    hydration_pct = round(hydration_ml / hydration_target * 100) if hydration_target > 0 else 0
    activity_pct = round(activity_minutes / 150 * 100) if activity_minutes > 0 else 0

    priority_lines = []
    for i, p in enumerate(priorities[:6], 1):
        priority_lines.append(f"  {i}. {p['title']}: {p['observed_data']}")
    priority_section = "\n".join(priority_lines) if priority_lines else "  None identified"

    nutrition_section = "  - No nutrition logged today"
    if nutrition:
        cal_target = nutrition_assessment.get("calorie_target", 2200) if nutrition_assessment else 2200
        protein_target = nutrition_assessment.get("protein_target_g", 56) if nutrition_assessment else 56
        nutrition_section = (
            f"  - Today's Nutrition: {nutrition['total_calories']} kcal / {cal_target} kcal target, "
            f"{nutrition['total_protein_g']} g protein / {protein_target} g target, "
            f"{nutrition['total_carbs_g']} g carbs, {nutrition['total_fat_g']} g fat "
            f"across {nutrition['meal_count']} meals"
        )

    return f"""You are HealthOS AI Assistant — a health education tool, NOT a diagnostic tool.
You are assisting: {profile.user_name}, {profile.age}{sex_label}, {profile.city}.
Body: {profile.height_cm} cm, {profile.weight_kg} kg, BMI {bmi} ({bmi_category}), blood group {profile.blood_group}.

CURRENT HEALTH CONTEXT:
- Lab Report Date: {report_date}
- Lab Results: {abnormal_count} of {total_bm} biomarkers outside reference range
{bm_section}
- Today's Hydration: {hydration_ml} ml / {hydration_target} ml target ({hydration_pct}%)
- Average Sleep (last 7 nights): {avg_sleep} hours/night (target: 7–9 hours)
- Weekly Physical Activity: {activity_minutes} min / 150 min target ({activity_pct}%)
{nutrition_section}

ACTIVE HEALTH PRIORITIES:
{priority_section}

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
6. Refer to the user by first name ({profile.user_name.split()[0]}) when appropriate.
7. If asked something outside health education scope, politely decline and redirect."""
