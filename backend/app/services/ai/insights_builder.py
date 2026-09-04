"""
Builds the prompt for the dashboard AI insight summary.
Returns a short plain-text paragraph — no JSON, no headers.
"""
from app.models.models import HealthProfile, Biomarker

_MOCK_INSIGHT = (
    "Based on your lab results and lifestyle data, your fatigue may be related to "
    "low hemoglobin, Vitamin D deficiency, and insufficient sleep. "
    "These findings can have multiple explanations. "
    "Consider discussing your results with a qualified healthcare professional."
)


def build_insight_prompt(
    profile: HealthProfile,
    biomarkers: list[Biomarker],
    hydration_pct: int,
    avg_sleep: float,
    priorities: list[dict],
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_message) for insight generation.
    AI must return 2–3 plain sentences, no headers, no JSON.
    """
    sex_label = "male" if profile.sex == "male" else "female"
    abnormal = [b for b in biomarkers if b.status != "normal"]
    top_priorities = [p["title"] for p in priorities[:3]]

    system_prompt = f"""You are HealthOS AI, a health education assistant.
Write a 2–3 sentence personalised health insight summary for {profile.user_name}, a {profile.age}-year-old {sex_label} from {profile.city}.

HEALTH CONTEXT:
- {len(abnormal)} abnormal lab result(s): {", ".join(b.name for b in abnormal) if abnormal else "none"}
- Hydration: {hydration_pct}% of daily target
- Sleep: {avg_sleep} hours/night average (target 7–9 hours)
- Top priorities: {", ".join(top_priorities) if top_priorities else "none"}

RULES:
1. Write ONLY 2–3 plain sentences. No headers, no bullet points, no JSON.
2. Never diagnose. Use hedged language: "may be related to", "can have multiple explanations".
3. Reference specific findings (e.g. hemoglobin, Vitamin D) by name.
4. End with a recommendation to consult a qualified healthcare professional.
5. Be warm and encouraging, not alarming."""

    user_message = f"Write a 2–3 sentence health insight summary for {profile.user_name}."
    return system_prompt, user_message


def get_mock_insight() -> str:
    return _MOCK_INSIGHT
