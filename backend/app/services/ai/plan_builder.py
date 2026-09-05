"""
Builds the prompt for 7-day wellness plan generation.
Requests a strict JSON response from the AI provider.
"""
from app.models.models import HealthProfile, Biomarker, LabReport

_DAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_MOCK_PLAN = {
    "summary": (
        "This 7-day plan is based on Bilal's lab results (low hemoglobin and Vitamin D), "
        "low daily hydration, insufficient sleep, and data from his Fitbit wearable "
        "(8,426 steps and 67 bpm resting heart rate). "
        "All tips are general wellness guidance — not medical advice."
    ),
    "days": [
        {
            "day": 1, "day_label": "Monday", "focus": "Iron & Energy",
            "nutrition": [
                "Add palak (spinach) or methi to lunch",
                "Include daal in at least one meal",
                "Replace one cup of chai with a glass of water",
            ],
            "hydration": "Drink 8 glasses of water — set a reminder every 2 hours",
            "activity": "20-minute walk — beat yesterday's 8,426 steps on your Fitbit",
            "sleep": "Aim for bed by 10:30 PM — no screens after 10 PM",
        },
        {
            "day": 2, "day_label": "Tuesday", "focus": "Vitamin D & Sunlight",
            "nutrition": [
                "Add eggs to breakfast for protein and Vitamin D",
                "Include a piece of fruit after lunch",
            ],
            "hydration": "Start the day with a full glass of water before chai",
            "activity": "Spend 15–20 minutes in morning sunlight (8–10 AM)",
            "sleep": "No screens 30 minutes before sleep",
        },
        {
            "day": 3, "day_label": "Wednesday", "focus": "Hydration Push",
            "nutrition": [
                "Choose grilled or baked chicken over fried",
                "Add a fresh salad or cucumber raita to dinner",
            ],
            "hydration": "Track each glass — target 2.5 litres today",
            "activity": "15-minute walk after dinner",
            "sleep": "Same bedtime target: 10:30 PM",
        },
        {
            "day": 4, "day_label": "Thursday", "focus": "Active Recovery",
            "nutrition": [
                "Chicken or fish at dinner for protein",
                "Add leafy greens to any meal",
            ],
            "hydration": "Drink a glass of water with every meal",
            "activity": "Rest day — 10 minutes of light stretching, check Fitbit sleep score",
            "sleep": "Aim for 7 full hours — your wearable recorded 6.7h recently",
        },
        {
            "day": 5, "day_label": "Friday", "focus": "Iron-rich Foods",
            "nutrition": [
                "Red meat (gosht) or liver if preferred — good iron source",
                "Reduce ghee quantity in cooking today",
            ],
            "hydration": "Continue 8-glass target — replace one chai with water",
            "activity": "25-minute brisk walk",
            "sleep": "Consistent bedtime — 10:30 PM",
        },
        {
            "day": 6, "day_label": "Saturday", "focus": "Protein & Strength",
            "nutrition": [
                "Add mixed nuts as a morning snack",
                "Include chana (chickpeas) in a meal today",
                "Fresh fruit or yoghurt as dessert",
            ],
            "hydration": "Lassi or fresh juice counts — still prioritise plain water",
            "activity": "30-minute walk or light exercise",
            "sleep": "Weekend — still aim for 7+ hours",
        },
        {
            "day": 7, "day_label": "Sunday", "focus": "Rest & Reflection",
            "nutrition": [
                "Focus on home-cooked food today",
                "Prepare healthy ingredients for the coming week",
            ],
            "hydration": "Full 2.5-litre target",
            "activity": "Light activity — family walk or 15-minute stretching",
            "sleep": "Review your sleep this week — consistent schedule next week",
        },
    ],
}


def _wearable_lines(wearable_summary: dict | None) -> str:
    if not wearable_summary:
        return "  - No wearable device connected."
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
    if wearable_summary.get("distance_km") is not None:
        lines.append(f"  - Distance: {wearable_summary['distance_km']} km")
    return "\n".join(lines)


def _nutrition_lines(nutrition: dict | None) -> str:
    if not nutrition:
        return "  - No nutrition logged today."
    return (
        f"  - Calories today: {nutrition['total_calories']} kcal\n"
        f"  - Protein: {nutrition['total_protein_g']} g, "
        f"Carbs: {nutrition['total_carbs_g']} g, Fat: {nutrition['total_fat_g']} g"
    )


def build_plan_prompt(
    profile: HealthProfile,
    biomarkers: list[Biomarker],
    latest_report: LabReport | None,
    hydration_pct: int,
    avg_sleep: float,
    activity_pct: int,
    priorities: list[dict],
    wearable_summary: dict | None = None,
    nutrition: dict | None = None,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_message) for 7-day plan generation.
    The AI must respond with valid JSON only — no surrounding text.
    """
    sex_label = "male" if profile.sex == "male" else "female"
    abnormal = [b for b in biomarkers if b.status != "normal"]

    bm_lines = []
    for b in abnormal:
        ref = ""
        if b.reference_low is not None and b.reference_high is not None:
            ref = f"{b.reference_low}–{b.reference_high} {b.unit}"
        bm_lines.append(f"  - {b.name}: {b.value} {b.unit} [{b.status.upper()}]" + (f" (ref: {ref})" if ref else ""))

    priority_lines = "\n".join(
        f"  {i+1}. {p['title']}" for i, p in enumerate(priorities[:6])
    )

    system_prompt = f"""You are a wellness plan generator for HealthOS. Your only job is to output a valid JSON object — no other text, no markdown fences, no explanation.

USER PROFILE: {profile.user_name}, {profile.age} year old {sex_label}, {profile.city}, Pakistan.

HEALTH CONTEXT:
- Abnormal lab results: {len(abnormal)} biomarker(s)
{chr(10).join(bm_lines) if bm_lines else "  - None"}
- Daily hydration: {hydration_pct}% of target
- Average sleep: {avg_sleep} hours/night (target 7–9 hours)
- Weekly activity: {activity_pct}% of 150-minute target

NUTRITION:
{_nutrition_lines(nutrition)}

WEARABLE DATA:
{_wearable_lines(wearable_summary)}

TOP HEALTH PRIORITIES:
{priority_lines if priority_lines else "  None"}

RULES:
1. Output ONLY valid JSON. No markdown, no preamble, no explanation.
2. Never diagnose or prescribe medication.
3. All tips are general wellness guidance only.
4. Use Pakistani food names naturally (paratha, daal, sabzi, gosht, chai, lassi, chana, palak, etc.)
5. Keep each tip under 15 words.
6. The summary must mention the user's first name and reference their specific health data.
7. Plan must address: iron/hemoglobin, Vitamin D, hydration, sleep, and activity.
8. If wearable data is available, reference specific wearable metrics (steps, resting HR,
   sleep hours) in relevant day recommendations.
9. If nutrition data is available, reference actual intake levels where relevant.

JSON SCHEMA (return exactly this structure):
{{
  "summary": "<2-sentence personalised intro referencing the user's specific findings>",
  "days": [
    {{
      "day": 1,
      "day_label": "Monday",
      "focus": "<5-word max theme>",
      "nutrition": ["<tip 1>", "<tip 2>", "<tip 3>"],
      "hydration": "<single hydration tip>",
      "activity": "<single activity recommendation>",
      "sleep": "<single sleep tip>"
    }}
  ]
}}
Generate all 7 days (Monday through Sunday)."""

    user_message = (
        f"Generate a 7-day wellness plan for {profile.user_name} "
        f"based on the health context above. Return valid JSON only."
    )
    return system_prompt, user_message


def get_mock_plan() -> dict:
    return _MOCK_PLAN
