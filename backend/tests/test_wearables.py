"""Tests for current-day wearable metric reads."""
from datetime import date, datetime, time, timedelta
from uuid import uuid4

from app.models.models import WearableMetric
from tests.conftest import TestingSessionLocal, male_headers


def test_today_wearable_endpoints_exclude_previous_day_metrics(client, male_headers):
    connection_response = client.post(
        "/api/v1/wearables/demo/connect", headers=male_headers
    )
    assert connection_response.status_code == 200
    connection_id = connection_response.json()["id"]

    db = TestingSessionLocal()
    try:
        db.query(WearableMetric).filter(
            WearableMetric.connection_id == connection_id
        ).delete(synchronize_session=False)
        db.add_all([
            WearableMetric(
                id=str(uuid4()),
                connection_id=connection_id,
                metric_type="steps",
                value=9876,
                unit="steps",
                recorded_at=datetime.combine(
                    date.today() - timedelta(days=1), time(hour=18)
                ),
            ),
            WearableMetric(
                id=str(uuid4()),
                connection_id=connection_id,
                metric_type="sleep",
                value=7.5,
                unit="hours",
                recorded_at=datetime.combine(
                    date.today() - timedelta(days=1), time(hour=18)
                ),
            ),
        ])
        db.commit()
    finally:
        db.close()

    today_metrics = client.get(
        f"/api/v1/wearables/{connection_id}/metrics/today", headers=male_headers
    )
    assert today_metrics.status_code == 200
    assert today_metrics.json() == []

    status_response = client.get("/api/v1/wearables/status", headers=male_headers)
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["connected"] is True
    assert status["insight"] is None
    assert status["device"] is not None
    for field in (
        "steps", "resting_heart_rate", "sleep_hours", "active_calories",
        "hydration_liters", "distance_km",
    ):
        assert status["device"][field] is None
