"""API tests for cycle tracking and cycle symptoms: CRUD, validation,
gender gating, and cross-user isolation."""
from datetime import date, timedelta

from tests.conftest import (
    FEMALE_PROFILE, MALE_PROFILE, create_cycle, days_ago, register_and_login,
)

PROTECTED_CYCLE_ENDPOINTS = [
    ("get", "/api/v1/cycles"),
    ("post", "/api/v1/cycles"),
    ("get", "/api/v1/cycles/current"),
    ("get", "/api/v1/cycles/current/prediction"),
    ("get", "/api/v1/cycles/calendar?year=2026&month=9"),
    ("get", "/api/v1/cycle-symptoms"),
    ("post", "/api/v1/cycle-symptoms"),
]


# --- Cycle CRUD ---------------------------------------------------------


def test_create_and_list_cycle(client, female_headers):
    created = create_cycle(client, female_headers, days_ago(10))
    assert created["start_date"] == days_ago(10)
    assert created["end_date"] is None
    assert created["cycle_length"] is None
    assert len(created["period_days"]) == 5
    assert created["period_days"][0]["date"] == days_ago(10)

    listed = client.get("/api/v1/cycles", headers=female_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == created["id"]


def test_second_cycle_auto_ends_previous(client, female_headers):
    create_cycle(client, female_headers, days_ago(40))
    second = create_cycle(client, female_headers, days_ago(10))

    cycles = client.get("/api/v1/cycles", headers=female_headers).json()
    assert len(cycles) == 2
    previous = cycles[1]
    assert previous["end_date"] == days_ago(10)
    assert previous["cycle_length"] == 30
    assert cycles[0]["id"] == second["id"]
    assert cycles[0]["end_date"] is None


def test_current_cycle_and_prediction(client, female_headers):
    start = days_ago(20)
    create_cycle(client, female_headers, start)

    current = client.get("/api/v1/cycles/current", headers=female_headers).json()
    assert current["cycle"]["start_date"] == start
    prediction = current["prediction"]
    assert prediction["has_data"] is True
    assert prediction["cycles_tracked"] == 1
    assert prediction["needs_more_data"] is True
    assert prediction["current_cycle_day"] == 21
    assert prediction["current_phase"] == "luteal"
    assert prediction["average_period_length"] == 5

    direct = client.get("/api/v1/cycles/current/prediction", headers=female_headers)
    assert direct.status_code == 200
    assert direct.json()["current_cycle_day"] == 21
    expected_next = (date.fromisoformat(start) + timedelta(days=28)).isoformat()
    assert direct.json()["predicted_period_start"] == expected_next


def test_prediction_without_cycles(client, female_headers):
    prediction = client.get("/api/v1/cycles/current/prediction", headers=female_headers)
    assert prediction.status_code == 200
    body = prediction.json()
    assert body["has_data"] is False
    assert body["needs_more_data"] is True
    assert body["cycles_tracked"] == 0

    current = client.get("/api/v1/cycles/current", headers=female_headers).json()
    assert current["cycle"] is None


def test_calendar_endpoint(client, female_headers):
    start = date.fromisoformat(days_ago(20))
    create_cycle(client, female_headers, start.isoformat())
    client.post(
        "/api/v1/cycle-symptoms",
        json={"date": days_ago(1), "symptom_type": "cramps", "severity": "moderate"},
        headers=female_headers,
    )

    def month_calendar(target: date) -> dict:
        response = client.get(
            f"/api/v1/cycles/calendar?year={target.year}&month={target.month}",
            headers=female_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["month"] == f"{target.year:04d}-{target.month:02d}"
        return {d["date"]: d for d in body["days"]}

    # The cycle start and the symptom date can fall in different months.
    start_month = month_calendar(start)
    assert start_month[start.isoformat()]["in_period"] is True

    symptom_date = date.fromisoformat(days_ago(1))
    symptom_month = month_calendar(symptom_date)
    assert symptom_month[symptom_date.isoformat()]["has_symptom"] is True
    assert symptom_month[symptom_date.isoformat()]["symptom_types"] == ["cramps"]


def test_calendar_invalid_month_and_year(client, female_headers):
    assert client.get(
        "/api/v1/cycles/calendar?year=2026&month=13", headers=female_headers
    ).status_code == 422
    assert client.get(
        "/api/v1/cycles/calendar?year=1999&month=6", headers=female_headers
    ).status_code == 422


def test_end_cycle_flow(client, female_headers):
    cycle = create_cycle(client, female_headers, days_ago(35))
    response = client.post(
        f"/api/v1/cycles/{cycle['id']}/end",
        json={"end_date": days_ago(5)},
        headers=female_headers,
    )
    assert response.status_code == 200
    assert response.json()["end_date"] == days_ago(5)
    assert response.json()["cycle_length"] == 30

    again = client.post(
        f"/api/v1/cycles/{cycle['id']}/end",
        json={"end_date": days_ago(4)},
        headers=female_headers,
    )
    assert again.status_code == 422
    assert "already ended" in again.json()["detail"].lower()


def test_end_cycle_invalid_dates(client, female_headers):
    cycle = create_cycle(client, female_headers, days_ago(20))
    before_start = client.post(
        f"/api/v1/cycles/{cycle['id']}/end",
        json={"end_date": days_ago(25)},
        headers=female_headers,
    )
    assert before_start.status_code == 422

    future = client.post(
        f"/api/v1/cycles/{cycle['id']}/end",
        json={"end_date": days_ago(-1)},
        headers=female_headers,
    )
    assert future.status_code == 422


def test_end_cycle_of_another_user_returns_404(client, female_headers, second_female_headers):
    cycle = create_cycle(client, female_headers, days_ago(20))
    response = client.post(
        f"/api/v1/cycles/{cycle['id']}/end",
        json={"end_date": days_ago(5)},
        headers=second_female_headers,
    )
    assert response.status_code == 404


# --- Cycle validation ---------------------------------------------------


def test_create_cycle_rejects_future_start(client, female_headers):
    response = client.post(
        "/api/v1/cycles",
        json={"start_date": days_ago(-1), "period_length": 5},
        headers=female_headers,
    )
    assert response.status_code == 422
    assert "future" in response.json()["detail"].lower()


def test_create_cycle_rejects_start_before_latest(client, female_headers):
    create_cycle(client, female_headers, days_ago(10))
    response = client.post(
        "/api/v1/cycles",
        json={"start_date": days_ago(15), "period_length": 5},
        headers=female_headers,
    )
    assert response.status_code == 422


def test_create_cycle_rejects_out_of_range_period_length(client, female_headers):
    for bad_length in (0, 15):
        response = client.post(
            "/api/v1/cycles",
            json={"start_date": days_ago(10), "period_length": bad_length},
            headers=female_headers,
        )
        assert response.status_code == 422


def test_create_cycle_rejects_bad_date_format(client, female_headers):
    response = client.post(
        "/api/v1/cycles",
        json={"start_date": "10/08/2026", "period_length": 5},
        headers=female_headers,
    )
    assert response.status_code == 422


# --- Symptoms -----------------------------------------------------------


def test_symptom_crud(client, female_headers):
    created = client.post(
        "/api/v1/cycle-symptoms",
        json={"date": days_ago(1), "symptom_type": "cramps", "severity": "moderate"},
        headers=female_headers,
    )
    assert created.status_code == 201
    symptom = created.json()
    assert symptom["symptom_type"] == "cramps"
    assert symptom["severity"] == "moderate"

    listed = client.get("/api/v1/cycle-symptoms", headers=female_headers).json()
    assert [s["id"] for s in listed] == [symptom["id"]]

    deleted = client.delete(
        f"/api/v1/cycle-symptoms/{symptom['id']}", headers=female_headers
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    assert client.get("/api/v1/cycle-symptoms", headers=female_headers).json() == []
    assert client.delete(
        f"/api/v1/cycle-symptoms/{symptom['id']}", headers=female_headers
    ).status_code == 404


def test_symptom_invalid_inputs(client, female_headers):
    invalid_payloads = [
        {"date": days_ago(1), "symptom_type": "cramps", "severity": "extreme"},
        {"date": days_ago(1), "symptom_type": "dizziness", "severity": "mild"},
        {"date": "2026/08/01", "symptom_type": "cramps", "severity": "mild"},
        {"date": days_ago(-1), "symptom_type": "cramps", "severity": "mild"},
    ]
    for payload in invalid_payloads:
        response = client.post("/api/v1/cycle-symptoms", json=payload, headers=female_headers)
        assert response.status_code == 422, payload


# --- Gender gating ------------------------------------------------------


def test_male_profile_blocked_from_all_cycle_endpoints(client, male_headers):
    for method, path in PROTECTED_CYCLE_ENDPOINTS:
        kwargs = {"headers": male_headers}
        if method == "post" and path.endswith("/cycles"):
            kwargs["json"] = {"start_date": days_ago(10), "period_length": 5}
        elif method == "post":
            kwargs["json"] = {"date": days_ago(1), "symptom_type": "cramps", "severity": "mild"}
        response = client.request(method, path, **kwargs)
        assert response.status_code == 403, f"{method.upper()} {path} should be blocked"
    assert "only available for female" in response.json()["detail"].lower()


def test_cycle_endpoints_require_auth(client):
    for method, path in PROTECTED_CYCLE_ENDPOINTS:
        kwargs = {}
        if method == "post" and path.endswith("/cycles"):
            kwargs["json"] = {"start_date": days_ago(10), "period_length": 5}
        elif method == "post":
            kwargs["json"] = {"date": days_ago(1), "symptom_type": "cramps", "severity": "mild"}
        response = client.request(method, path, **kwargs)
        assert response.status_code == 401, f"{method.upper()} {path} should require auth"


def test_female_profile_gets_access(client, female_headers):
    for method, path in PROTECTED_CYCLE_ENDPOINTS:
        kwargs = {"headers": female_headers}
        if method == "post" and path.endswith("/cycles"):
            kwargs["json"] = {"start_date": days_ago(10), "period_length": 5}
        elif method == "post":
            kwargs["json"] = {"date": days_ago(1), "symptom_type": "cramps", "severity": "mild"}
        response = client.request(method, path, **kwargs)
        assert response.status_code in (200, 201), f"{method.upper()} {path} should work"


def test_no_profile_cannot_access_cycles(client):
    headers = register_and_login(client, "noprofile@example.com", "No Profile")
    response = client.get("/api/v1/cycles", headers=headers)
    assert response.status_code == 404  # get_current_profile requires an onboarded profile


# --- Cross-user isolation ----------------------------------------------


def test_cross_user_cycle_isolation(client, female_headers, second_female_headers):
    create_cycle(client, female_headers, days_ago(20))
    client.post(
        "/api/v1/cycle-symptoms",
        json={"date": days_ago(1), "symptom_type": "fatigue", "severity": "mild"},
        headers=female_headers,
    )

    assert client.get("/api/v1/cycles", headers=second_female_headers).json() == []
    assert client.get("/api/v1/cycle-symptoms", headers=second_female_headers).json() == []

    # Second user's dashboard summary must not leak the first user's data.
    dashboard = client.get("/api/v1/dashboard", headers=second_female_headers).json()
    assert dashboard["womens_health"]["cycles_tracked"] == 0

    symptom_id = client.get("/api/v1/cycle-symptoms", headers=female_headers).json()[0]["id"]
    assert client.delete(
        f"/api/v1/cycle-symptoms/{symptom_id}", headers=second_female_headers
    ).status_code == 404


# --- Dashboard + timeline integration ----------------------------------


def test_dashboard_womens_health_female(client, female_headers):
    create_cycle(client, female_headers, days_ago(20))
    client.post(
        "/api/v1/cycle-symptoms",
        json={"date": days_ago(1), "symptom_type": "cramps", "severity": "moderate"},
        headers=female_headers,
    )

    dashboard = client.get("/api/v1/dashboard", headers=female_headers).json()
    wh = dashboard["womens_health"]
    assert wh is not None
    assert wh["cycles_tracked"] == 1
    assert wh["current_cycle_day"] == 21
    assert wh["current_phase"] == "luteal"
    assert wh["average_period_length"] == 5
    assert wh["needs_more_data"] is True
    assert wh["predicted_period_start"] is not None
    assert wh["estimated_fertile_start"] is not None
    assert wh["estimated_fertile_end"] is not None
    assert [s["symptom_type"] for s in wh["recent_symptoms"]] == ["cramps"]


def test_dashboard_womens_health_null_for_male(client, male_headers):
    dashboard = client.get("/api/v1/dashboard", headers=male_headers).json()
    assert dashboard["womens_health"] is None


def test_timeline_cycle_events(client, female_headers):
    create_cycle(client, female_headers, days_ago(20))
    client.post(
        "/api/v1/cycle-symptoms",
        json={"date": days_ago(1), "symptom_type": "cramps", "severity": "moderate"},
        headers=female_headers,
    )

    timeline = client.get("/api/v1/dashboard", headers=female_headers).json()["timeline"]
    types = {e["event_type"] for e in timeline}
    assert "cycle" in types
    assert "cycle_symptom" in types

    cycle_events = [e for e in timeline if e["event_type"] == "cycle"]
    assert cycle_events[0]["title"] == "Period started"
    assert cycle_events[0]["is_ai_generated"] is False


def test_timeline_dedupes_repeated_symptom_logs(client, female_headers):
    payload = {"date": days_ago(1), "symptom_type": "cramps", "severity": "moderate"}
    client.post("/api/v1/cycle-symptoms", json=payload, headers=female_headers)
    client.post("/api/v1/cycle-symptoms", json=payload, headers=female_headers)

    timeline = client.get("/api/v1/dashboard", headers=female_headers).json()["timeline"]
    symptom_events = [e for e in timeline if e["event_type"] == "cycle_symptom"]
    assert len(symptom_events) == 1
