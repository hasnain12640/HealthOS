"""Unit tests for the deterministic cycle analysis engine."""
from datetime import date, timedelta

from app.services.cycle import cycle_engine


def _cycle(start: str, period_days: list[str] | None = None, end_date: str | None = None,
           cycle_length: int | None = None, period_length: int | None = None) -> dict:
    if period_days is None and period_length is None:
        period_days = [(date.fromisoformat(start) + timedelta(days=i)).isoformat() for i in range(5)]
    return {
        "start_date": start,
        "end_date": end_date,
        "cycle_length": cycle_length,
        "period_length": period_length,
        "period_days": period_days or [],
        "period_day_records": [{"date": d, "flow_level": None} for d in period_days or []],
    }


def test_no_cycles():
    result = cycle_engine.analyze_cycles([], today=date(2026, 9, 4))
    assert result["has_data"] is False
    assert result["needs_more_data"] is True
    assert result["cycles_tracked"] == 0
    assert "first period" in result["message"].lower()


def test_single_cycle_uses_defaults_and_needs_more_data():
    result = cycle_engine.analyze_cycles(
        [_cycle("2026-08-01")], today=date(2026, 8, 3)
    )
    assert result["has_data"] is True
    assert result["needs_more_data"] is True
    assert result["cycles_tracked"] == 1
    assert result["current_cycle_day"] == 3
    assert result["current_phase"] == "menstrual"
    assert result["average_cycle_length"] is None  # no completed cycles yet
    assert result["average_period_length"] == 5
    assert result["confidence"] == cycle_engine.MIN_CONFIDENCE
    assert "another cycle" in result["message"].lower()
    # Default 28-day projection from the single start date.
    assert result["predicted_period_start"] == "2026-08-29"


def test_two_cycles_stable_28_day_pattern():
    previous = _cycle("2026-07-01", period_days=None, end_date=None,
                      cycle_length=28, period_length=5)
    current = _cycle("2026-07-29")
    result = cycle_engine.analyze_cycles(
        [previous, current], today=date(2026, 8, 10)
    )
    assert result["cycles_tracked"] == 2
    assert result["needs_more_data"] is False
    assert result["message"] is None
    assert result["average_cycle_length"] == 28
    assert result["confidence"] == 0.9  # zero spread between cycle lengths
    assert result["current_cycle_day"] == 13
    assert result["current_phase"] == "ovulatory"


def test_varying_cycle_lengths_reduce_confidence():
    cycles = [
        _cycle("2026-05-01", cycle_length=26, period_length=5),
        _cycle("2026-05-27", cycle_length=30, period_length=5),
        _cycle("2026-06-26", cycle_length=34, period_length=5),
        _cycle("2026-07-30"),
    ]
    result = cycle_engine.analyze_cycles(cycles, today=date(2026, 8, 5))
    assert result["average_cycle_length"] == 30  # round((26+30+34)/3)
    spread = 34 - 26
    assert result["confidence"] == round(max(0.4, 0.9 - spread * 0.05), 2)
    assert result["current_cycle_day"] == 7
    # Working length falls back to the average (30): ovulation day 16,
    # so day 7 is follicular.
    assert result["current_phase"] == "follicular"
    assert result["predicted_period_start"] == "2026-08-29"  # start + 30


def test_confidence_floor_at_high_variance():
    cycles = [
        _cycle("2026-06-01", cycle_length=21, period_length=5),
        _cycle("2026-06-22", cycle_length=45, period_length=5),
        _cycle("2026-08-06"),
    ]
    result = cycle_engine.analyze_cycles(cycles, today=date(2026, 8, 10))
    assert result["confidence"] == cycle_engine.MIN_CONFIDENCE


def test_phase_boundaries_standard_28_day_cycle():
    start = date(2026, 8, 1)
    expectations = [
        (1, "menstrual", 1),
        (3, "menstrual", 3),
        (5, "menstrual", 5),
        (6, "follicular", 1),
        (12, "follicular", 7),
        (13, "ovulatory", 1),
        (15, "ovulatory", 3),
        (16, "luteal", 1),
        (28, "luteal", 13),
        (30, "luteal", 15),  # late period stays luteal
    ]
    for day, phase, phase_day in expectations:
        result = cycle_engine.analyze_cycles(
            [_cycle(start.isoformat())], today=start + timedelta(days=day - 1)
        )
        assert result["current_cycle_day"] == day
        assert result["current_phase"] == phase, f"day {day} should be {phase}"
        assert result["cycle_day_of_phase"] == phase_day, f"day {day} phase day"


def test_predicted_period_dates():
    result = cycle_engine.analyze_cycles(
        [_cycle("2026-07-29")], today=date(2026, 8, 10)
    )
    assert result["predicted_period_start"] == "2026-08-26"  # start + 28
    assert result["predicted_period_end"] == "2026-08-30"    # + period length 5 - 1


def test_fertile_window_around_estimated_ovulation():
    # Ovulation estimated at day 14 for a 28-day cycle; window is days 9..15.
    result = cycle_engine.analyze_cycles(
        [_cycle("2026-07-29")], today=date(2026, 8, 10)
    )
    assert result["estimated_fertile_start"] == "2026-08-06"
    assert result["estimated_fertile_end"] == "2026-08-12"


def test_is_on_period_today_true_and_false():
    start = date(2026, 8, 1)
    on_period = cycle_engine.analyze_cycles(
        [_cycle(start.isoformat())], today=start + timedelta(days=2)
    )
    assert on_period["is_on_period_today"] is True

    after_period = cycle_engine.analyze_cycles(
        [_cycle(start.isoformat())], today=start + timedelta(days=9)
    )
    assert after_period["is_on_period_today"] is False


def test_is_on_period_today_inferred_from_period_length():
    # No explicit period days: an open cycle within the average period length
    # is treated as on-period today.
    cycle = _cycle("2026-08-01", period_days=None, period_length=5)
    result = cycle_engine.analyze_cycles([cycle], today=date(2026, 8, 3))
    assert result["is_on_period_today"] is True


def test_cycle_day_one_on_start_day():
    result = cycle_engine.analyze_cycles(
        [_cycle("2026-08-01")], today=date(2026, 8, 1)
    )
    assert result["current_cycle_day"] == 1
    assert result["current_phase"] == "menstrual"


def test_calendar_month_markers():
    previous = _cycle("2026-07-04", cycle_length=28, period_length=5)
    current = _cycle("2026-08-01")
    symptoms = [{"date": "2026-08-07", "symptom_type": "cramps"}]
    cal = cycle_engine.calendar_month(
        [previous, current], symptoms, 2026, 8, today=date(2026, 8, 10)
    )
    assert cal["month"] == "2026-08"
    assert len(cal["days"]) == 31
    assert cal["average_cycle_length"] == 28
    by_date = {d["date"]: d for d in cal["days"]}

    assert by_date["2026-08-03"]["in_period"] is True
    assert by_date["2026-08-07"]["has_symptom"] is True
    assert by_date["2026-08-07"]["symptom_types"] == ["cramps"]
    assert by_date["2026-08-10"]["is_today"] is True
    # Fertile window days 9..15 of a cycle starting Aug 1.
    assert by_date["2026-08-10"]["is_fertile_window"] is True
    assert by_date["2026-08-16"]["is_fertile_window"] is False
    # Predicted period starts Aug 29 (28 days after Aug 1).
    assert by_date["2026-08-29"]["is_predicted_period"] is True
    assert by_date["2026-08-29"]["in_period"] is False
    # A quiet day carries no markers.
    quiet = by_date["2026-08-20"]
    assert not any([
        quiet["in_period"], quiet["is_predicted_period"],
        quiet["is_fertile_window"], quiet["is_today"], quiet["has_symptom"],
    ])


def test_calendar_infers_period_days_for_cycles_without_records():
    previous = _cycle("2026-07-04", cycle_length=28, period_length=5)
    cal = cycle_engine.calendar_month(
        [previous], [], 2026, 7, today=date(2026, 7, 10)
    )
    by_date = {d["date"]: d for d in cal["days"]}
    assert by_date["2026-07-04"]["in_period"] is True
    assert by_date["2026-07-08"]["in_period"] is True  # 5th day of period
    assert by_date["2026-07-09"]["in_period"] is False


def test_calendar_actual_period_takes_precedence_over_estimates():
    # A logged period day inside the estimated fertile window must be marked
    # in_period, not fertile.
    previous = _cycle("2026-07-01", cycle_length=28, period_length=5)
    current = _cycle("2026-07-29", period_days=[
        f"2026-07-{d:02d}" for d in range(29, 32)
    ] + ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04",
         "2026-08-05", "2026-08-06", "2026-08-07", "2026-08-08", "2026-08-09", "2026-08-10"])
    cal = cycle_engine.calendar_month(
        [previous, current], [], 2026, 8, today=date(2026, 7, 30)
    )
    by_date = {d["date"]: d for d in cal["days"]}
    assert by_date["2026-08-08"]["in_period"] is True
    assert by_date["2026-08-08"]["is_fertile_window"] is False


def test_calendar_month_without_any_data():
    cal = cycle_engine.calendar_month([], [], 2026, 2, today=date(2026, 2, 10))
    assert cal["month"] == "2026-02"
    assert len(cal["days"]) == 28
    assert cal["average_cycle_length"] is None
    assert all(
        not d["in_period"] and not d["is_predicted_period"]
        and not d["is_fertile_window"] and not d["has_symptom"]
        for d in cal["days"]
    )
