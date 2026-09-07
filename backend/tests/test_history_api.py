"""Tests for the 30-day Health History aggregation API."""
from datetime import date, timedelta

from tests.conftest import days_ago, female_headers, male_headers


def _create_logs(client, headers, profile_id: str):
    """Create deterministic hydration, nutrition, sleep and activity logs
    across the last 7 days for the authenticated profile."""
    for i in range(7):
        d = days_ago(i)
        client.post(
            "/api/v1/lifestyle/hydration",
            json={"date": d, "amount_ml": 300 + i * 50, "source": "water"},
            headers=headers,
        )
        client.post(
            "/api/v1/lifestyle/nutrition",
            json={
                "date": d,
                "meal_type": "lunch",
                "food_name": "Daal Chawal",
                "quantity_g": 300,
                "calories": 500 + i * 10,
                "protein_g": 15,
                "carbs_g": 70,
                "fat_g": 10,
            },
            headers=headers,
        )
        client.post(
            "/api/v1/lifestyle/sleep",
            json={"date": d, "hours_slept": 6.0 + (i % 3) * 0.5, "quality": 3},
            headers=headers,
        )
        client.post(
            "/api/v1/lifestyle/activity",
            json={
                "date": d,
                "activity_type": "Walking",
                "duration_min": 20 + i * 5,
                "steps": 2000 + i * 500,
            },
            headers=headers,
        )


def test_history_returns_7_days_for_male(client, male_headers):
    _create_logs(client, male_headers, "")

    response = client.get("/api/v1/history?days=7", headers=male_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["days"] == 7
    assert len(body["daily"]) == 7
    assert body["summary"]["days_count"] == 7
    assert body["profile"]["sex"] == "male"
    assert "cycle" not in body["daily"][0]

    today = body["daily"][-1]
    assert today["is_today"] is True
    assert today["hydration"]["amount_ml"] == 300
    assert today["nutrition"]["total_calories"] == 500
    assert today["sleep"]["hours_slept"] == 6.0
    assert today["activity"]["steps"] == 2000

    # Averages should reflect the deterministic backfill.
    assert body["summary"]["avg_hydration_ml"] > 0
    assert body["summary"]["total_activity_minutes"] > 0


def test_history_includes_labs_and_timeline_events(client, male_headers):
    report_date = days_ago(2)
    report = client.post(
        "/api/v1/lab/manual",
        json={
            "lab_name": "Manual",
            "report_date": report_date,
            "biomarkers": [
                {"name": "Hemoglobin", "value": 11.8, "unit": "g/dL", "reference_low": 13.0, "reference_high": 17.0, "category": "CBC"}
            ],
        },
        headers=male_headers,
    ).json()

    response = client.get("/api/v1/history?days=7", headers=male_headers)
    body = response.json()
    day = next(d for d in body["daily"] if d["date"] == report_date)
    assert len(day["labs"]) == 1
    assert day["labs"][0]["id"] == report["id"]
    assert len(day["labs"][0]["biomarkers"]) == 1
    assert day["labs"][0]["biomarkers"][0]["status"] == "low"

    # Timeline lab event is grouped on the report date.
    assert any(e["event_type"] == "lab" for e in day["events"])
    assert body["summary"]["abnormal_biomarker_count"] == 1


def test_history_includes_cycle_data_for_female(client, female_headers):
    from tests.conftest import create_cycle

    create_cycle(client, female_headers, days_ago(20))
    client.post(
        "/api/v1/cycle-symptoms",
        json={"date": days_ago(1), "symptom_type": "cramps", "severity": "moderate"},
        headers=female_headers,
    )

    response = client.get("/api/v1/history?days=7", headers=female_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["sex"] == "female"

    for day in body["daily"]:
        assert "cycle" in day
        if day["cycle"]:
            assert "phase" in day["cycle"]
            assert "is_period" in day["cycle"]
            assert "is_fertile_window" in day["cycle"]

    yesterday = next(d for d in body["daily"] if d["date"] == days_ago(1))
    assert yesterday["cycle"] is not None
    assert "cramps" in yesterday["cycle"]["symptoms"]


def test_history_days_clamped_to_valid_range(client, male_headers):
    assert client.get("/api/v1/history?days=0", headers=male_headers).status_code == 422
    assert client.get("/api/v1/history?days=91", headers=male_headers).status_code == 422
    assert client.get("/api/v1/history?days=30", headers=male_headers).status_code == 200


def test_history_requires_auth(client):
    assert client.get("/api/v1/history?days=7").status_code == 401
