from datetime import date, timedelta


def test_manual_lifestyle_entries_update_derived_views(client, male_headers):
    today = date.today().isoformat()

    hydration = client.post(
        "/api/v1/lifestyle/hydration",
        json={"date": today, "amount_ml": 650, "source": "water"},
        headers=male_headers,
    )
    nutrition = client.post(
        "/api/v1/lifestyle/nutrition",
        json={
            "date": today,
            "meal_type": "lunch",
            "food_name": "Daal Chawal",
            "quantity_g": 300,
            "calories": 560,
            "protein_g": 18,
            "carbs_g": 82,
            "fat_g": 12,
        },
        headers=male_headers,
    )
    sleep = client.post(
        "/api/v1/lifestyle/sleep",
        json={"date": today, "hours_slept": 7.5, "quality": 4},
        headers=male_headers,
    )
    activity = client.post(
        "/api/v1/lifestyle/activity",
        json={"date": today, "activity_type": "Walking", "duration_min": 35},
        headers=male_headers,
    )

    for response in (hydration, nutrition, sleep, activity):
        assert response.status_code == 201, response.text

    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    assert dashboard["hydration"]["today_ml"] == 650
    assert dashboard["nutrition"]["meals"][0]["food_name"] == "Daal Chawal"
    assert dashboard["sleep"]["logs"][0]["hours_slept"] == 7.5
    assert dashboard["activity"]["recent"][0]["duration_min"] == 35
    assert {event["event_type"] for event in dashboard["timeline"]} >= {
        "hydration",
        "nutrition",
        "sleep",
        "activity",
    }

    analysis = client.get("/api/v1/analysis", headers=male_headers).json()
    assert analysis["activity"]["recent"][0]["notes"] == ""

    history = client.get("/api/v1/history?days=1", headers=male_headers).json()
    day = history["daily"][0]
    assert day["hydration"]["amount_ml"] == 650
    assert day["nutrition"]["total_calories"] == 560
    assert day["sleep"]["hours_slept"] == 7.5
    assert day["activity"]["duration_min"] == 35
    assert {event["event_type"] for event in day["events"]} >= {
        "hydration",
        "nutrition",
        "sleep",
        "activity",
    }


def test_lifestyle_rejects_invalid_manual_entries(client, male_headers):
    today = date.today().isoformat()
    future_date = (date.today() + timedelta(days=1)).isoformat()
    invalid_requests = [
        ("/api/v1/lifestyle/hydration", {"date": future_date, "amount_ml": 500}),
        ("/api/v1/lifestyle/hydration", {"date": today, "amount_ml": 5001}),
        (
            "/api/v1/lifestyle/nutrition",
            {"date": today, "meal_type": "lunch", "food_name": "   "},
        ),
        (
            "/api/v1/lifestyle/nutrition",
            {"date": today, "meal_type": "lunch", "food_name": "Daal", "calories": -1},
        ),
        ("/api/v1/lifestyle/sleep", {"date": today, "hours_slept": 24.5}),
        ("/api/v1/lifestyle/activity", {"date": today, "activity_type": "Walking"}),
    ]

    for path, payload in invalid_requests:
        response = client.post(path, json=payload, headers=male_headers)
        assert response.status_code == 422, response.text
