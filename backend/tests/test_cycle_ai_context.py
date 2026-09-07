"""Tests for AI cycle-aware context: female inclusion, male exclusion,
safety rules, and no fabricated data (mock provider)."""
import pytest

from app.models.models import HealthProfile
from app.services.ai.context_builder import build_system_prompt, _cycle_section
from app.services.ai.insights_builder import build_insight_prompt, get_mock_insight
from tests.conftest import FEMALE_PROFILE, create_cycle, days_ago


@pytest.fixture
def female_profile():
    return HealthProfile(**FEMALE_PROFILE)


CYCLE_SUMMARY = {
    "cycles_tracked": 3,
    "current_cycle_day": 21,
    "current_phase": "luteal",
    "average_cycle_length": 28,
    "average_period_length": 5,
    "predicted_period_start": "2026-09-10",
    "estimated_fertile_start": "2026-08-24",
    "estimated_fertile_end": "2026-08-30",
    "needs_more_data": False,
    "recent_symptoms": [
        {"date": "2026-09-01", "symptom_type": "cramps", "severity": "moderate"},
    ],
}


# --- Context builder (chat prompt) --------------------------------------


def test_cycle_section_empty_when_no_data():
    # Male profiles produce cycle_summary=None — the section must vanish.
    assert _cycle_section(None) == ""
    assert _cycle_section({}) == ""


def test_cycle_section_contains_data_and_safety_rules():
    section = _cycle_section(CYCLE_SUMMARY)
    assert "=== WOMEN'S HEALTH ===" in section
    assert "=== CYCLE-AWARE CONTEXT ===" in section
    assert "Cycle day: 21 (Luteal phase)" in section
    assert "Average cycle length: 28 days" in section
    assert "Cycles tracked: 3" in section
    assert "2026-09-10" in section and "(estimate)" in section
    assert "cramps (moderate)" in section
    # Safety rails the AI must obey.
    assert "NEVER diagnose PCOS" in section
    assert "NEVER predict pregnancy" in section
    assert "cannot confirm ovulation" in section
    assert "NEVER recalculate" in section


def test_cycle_section_notes_insufficient_history():
    section = _cycle_section({**CYCLE_SUMMARY, "needs_more_data": True})
    assert "not enough cycle history" in section


def test_build_system_prompt_includes_cycle_for_female(female_profile):
    prompt = build_system_prompt(
        female_profile, [], None,
        hydration_ml=1500, hydration_target=2500, avg_sleep=7.0,
        activity_minutes=120, priorities=[],
        cycle_summary=CYCLE_SUMMARY,
    )
    assert "=== WOMEN'S HEALTH ===" in prompt
    assert "=== CYCLE-AWARE CONTEXT ===" in prompt
    assert "Cycle day: 21 (Luteal phase)" in prompt


def test_build_system_prompt_excludes_cycle_for_male():
    male_profile = HealthProfile(
        user_name="Bilal Test", age=34, sex="male", city="Lahore",
        height_cm=172.0, weight_kg=75.0, blood_group="O+",
    )
    prompt = build_system_prompt(
        male_profile, [], None,
        hydration_ml=1500, hydration_target=2500, avg_sleep=7.0,
        activity_minutes=120, priorities=[],
        cycle_summary=None,
    )
    assert "WOMEN'S HEALTH" not in prompt
    assert "CYCLE-AWARE" not in prompt


def test_system_prompt_always_carries_no_diagnosis_rules(female_profile):
    prompt = build_system_prompt(
        female_profile, [], None,
        hydration_ml=1500, hydration_target=2500, avg_sleep=7.0,
        activity_minutes=120, priorities=[],
        cycle_summary=CYCLE_SUMMARY,
    )
    assert "NEVER diagnose" in prompt
    assert "never invent values" in prompt
    assert "educational purposes only" in prompt


# --- Insight prompt -----------------------------------------------------


def test_insight_prompt_includes_cycle_for_female(female_profile):
    system_prompt, user_message = build_insight_prompt(
        female_profile, [], hydration_pct=60, avg_sleep=6.5, priorities=[],
        cycle_summary=CYCLE_SUMMARY,
    )
    assert "=== WOMEN'S HEALTH ===" in system_prompt
    assert "=== CYCLE-AWARE CONTEXT ===" in system_prompt
    assert "cycle" in system_prompt  # cycle appears as an allowed JSON domain
    assert user_message


def test_insight_prompt_excludes_cycle_for_male():
    male_profile = HealthProfile(
        user_name="Bilal Test", age=34, sex="male", city="Lahore",
        height_cm=172.0, weight_kg=75.0, blood_group="O+",
    )
    system_prompt, _ = build_insight_prompt(
        male_profile, [], hydration_pct=60, avg_sleep=6.5, priorities=[],
        cycle_summary=None,
    )
    assert "=== WOMEN'S HEALTH ===" not in system_prompt


# --- Mock insight (deterministic, built from real data) ------------------


def test_mock_insight_includes_cycle_domain(female_profile):
    insight = get_mock_insight(
        profile=female_profile, biomarkers=[], hydration_pct=50,
        hydration_ml=1250, hydration_target=2500, avg_sleep=8.0,
        priorities=[], cycle_summary=CYCLE_SUMMARY,
    )
    cycle_observations = [o for o in insight["observed_data"] if o["domain"] == "cycle"]
    assert len(cycle_observations) == 2  # cycle day + recent symptoms
    assert cycle_observations[0]["value"] == "Day 21 of ~28 day cycle"
    assert "cramps" in cycle_observations[1]["value"]
    assert "day 21" in insight["summary"]
    # Luteal phase + symptoms produce a cycle-aware priority.
    cycle_priorities = [p for p in insight["priorities"] if "cycle" in p["related_domains"]]
    assert len(cycle_priorities) == 1
    assert "luteal" in cycle_priorities[0]["title"].lower()
    assert "diagnosis" in insight["safety_note"]


def test_mock_insight_excludes_cycle_for_male():
    male_profile = HealthProfile(
        user_name="Bilal Test", age=34, sex="male", city="Lahore",
        height_cm=172.0, weight_kg=75.0, blood_group="O+",
    )
    insight = get_mock_insight(
        profile=male_profile, biomarkers=[], hydration_pct=100,
        hydration_ml=2500, hydration_target=2500, avg_sleep=8.0,
        priorities=[], cycle_summary=None,
    )
    assert all(o["domain"] != "cycle" for o in insight["observed_data"])
    assert all(
        "cycle" not in c["domains"] for c in insight["cross_domain_connections"]
    )
    assert all("cycle" not in p["related_domains"] for p in insight["priorities"])


# --- API-level (mock provider) ------------------------------------------


def test_insights_endpoint_female_includes_real_cycle_data(client, female_headers):
    create_cycle(client, female_headers, days_ago(20))
    client.post(
        "/api/v1/cycle-symptoms",
        json={"date": days_ago(1), "symptom_type": "cramps", "severity": "moderate"},
        headers=female_headers,
    )

    response = client.post("/api/v1/insights", headers=female_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"

    cycle_observations = [
        o for o in body["insight"]["observed_data"] if o["domain"] == "cycle"
    ]
    assert len(cycle_observations) >= 1
    # No fabricated values — the observation must match the logged data (day 21).
    assert cycle_observations[0]["value"] == "Day 21 of ~28 day cycle"
    assert "day 21" in body["insight"]["summary"]
    assert "diagnosis" in body["insight"]["safety_note"]


def test_insights_endpoint_male_excludes_cycle(client, male_headers):
    response = client.post("/api/v1/insights", headers=male_headers)
    assert response.status_code == 200
    insight = response.json()["insight"]
    assert all(o["domain"] != "cycle" for o in insight["observed_data"])
    assert all(
        "cycle" not in c["domains"] for c in insight["cross_domain_connections"]
    )


def test_chat_endpoint_female_and_male_work(client, female_headers, male_headers):
    payload = {"message": "How is my health today?", "history": []}
    female_reply = client.post("/api/v1/chat", json=payload, headers=female_headers)
    assert female_reply.status_code == 200
    assert female_reply.json()["provider"] == "mock"
    assert "**Observed Data:**" in female_reply.json()["reply"]
    assert "educational purposes only" in female_reply.json()["reply"]

    male_reply = client.post("/api/v1/chat", json=payload, headers=male_headers)
    assert male_reply.status_code == 200
    assert male_reply.json()["provider"] == "mock"


def test_mock_provider_metadata_is_truthful(client, male_headers):
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["ai_provider"] == "mock"
    assert health.json()["ai_model"] is None

    chat = client.post(
        "/api/v1/chat",
        json={"message": "How is my health today?", "history": []},
        headers=male_headers,
    )
    assert chat.status_code == 200
    assert chat.json()["provider"] == "mock"
    assert chat.json()["model"] is None

    plan = client.post("/api/v1/plan", headers=male_headers)
    assert plan.status_code == 200
    assert plan.json()["provider"] == "mock"
    assert plan.json()["model"] is None
