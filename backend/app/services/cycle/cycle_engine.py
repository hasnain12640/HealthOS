"""
Deterministic menstrual cycle analysis engine.

All dates and predictions are computed here with plain arithmetic — the AI
layer never calculates or overrides dates; it only explains them.

Assumptions and phase boundaries (documented, deterministic):
- Cycle day 1 = the day the period starts.
- Ovulation is estimated at (cycle_length - 14) days into the cycle, because
  the luteal phase is comparatively fixed at ~14 days across people.
- Phase boundaries for a cycle of length L and period length P:
    * Menstrual:   days 1 .. P
    * Follicular:  days P+1 .. O-2
    * Ovulatory:   days O-1 .. O+1   (3-day window around estimated ovulation)
    * Luteal:      days O+2 .. L     (days beyond L stay luteal — late period)
  where O = L - 14. Example for L=28, P=5: menstrual 1-5, follicular 6-12,
  ovulatory 13-15, luteal 16-28.
- Fertile window: days O-5 .. O+1 (sperm viability ~5 days, egg ~1 day).
- All predictions are estimates, never guarantees. With fewer than 2 cycles
  tracked, a 28-day clinical default is used and the result is flagged as
  needing more data.
"""
from datetime import date, timedelta

DEFAULT_CYCLE_LENGTH = 28
DEFAULT_PERIOD_LENGTH = 5
LUTEAL_PHASE_DAYS = 14
MIN_CONFIDENCE = 0.4

_MONTHS_AHEAD = 2


def _to_date(value: str) -> date:
    return date.fromisoformat(value)


def _completed_cycle_lengths(cycles: list[dict]) -> list[int]:
    lengths = []
    for c in cycles:
        if c.get("cycle_length") is not None:
            lengths.append(int(c["cycle_length"]))
        elif c.get("end_date"):
            length = (_to_date(c["end_date"]) - _to_date(c["start_date"])).days
            if length > 0:
                lengths.append(length)
    return lengths


def _average(values: list[int]) -> int:
    return round(sum(values) / len(values))


def _period_lengths(cycles: list[dict]) -> list[int]:
    lengths = []
    for c in cycles:
        days = c.get("period_days") or []
        if days:
            lengths.append(len(days))
        elif c.get("period_length") is not None:
            lengths.append(int(c["period_length"]))
    return lengths


def _phase_for_day(cycle_day: int, cycle_length: int, period_length: int) -> tuple[str, int]:
    ovulation_day = cycle_length - LUTEAL_PHASE_DAYS
    if cycle_day <= period_length:
        phase, day = "menstrual", cycle_day
    elif cycle_day <= ovulation_day - 2:
        phase, day = "follicular", cycle_day - period_length
    elif cycle_day <= ovulation_day + 1:
        phase, day = "ovulatory", cycle_day - (ovulation_day - 2)
    else:
        phase, day = "luteal", cycle_day - (ovulation_day + 1)
    return phase, day


def analyze_cycles(cycles: list[dict], today: date | None = None) -> dict:
    """
    Analyze a profile's cycles and return deterministic predictions.

    Each cycle dict: {start_date, end_date, cycle_length, period_length,
    period_days: [date_str]}.
    """
    today = today or date.today()
    if not cycles:
        return {
            "has_data": False,
            "needs_more_data": True,
            "message": "No cycles logged yet. Log your first period to start tracking.",
            "cycles_tracked": 0,
        }

    completed_lengths = _completed_cycle_lengths(cycles)
    period_lengths = _period_lengths(cycles)
    current = max(cycles, key=lambda c: c["start_date"])
    cycles_tracked = len(cycles)

    current_start = _to_date(current["start_date"])
    current_length = (
        int(current["cycle_length"])
        if current.get("cycle_length") is not None
        else None
    )
    cycle_day = (today - current_start).days + 1

    avg_cycle = _average(completed_lengths) if completed_lengths else None
    avg_period = _average(period_lengths) if period_lengths else None

    needs_more_data = cycles_tracked < 2
    if avg_cycle is None:
        avg_cycle = current_length if current_length is not None else DEFAULT_CYCLE_LENGTH
    if avg_period is None:
        avg_period = DEFAULT_PERIOD_LENGTH

    working_length = current_length if current_length is not None else avg_cycle
    phase, phase_day = _phase_for_day(max(cycle_day, 1), working_length, avg_period)

    next_period_start = current_start + timedelta(days=working_length)
    next_period_end = next_period_start + timedelta(days=avg_period - 1)
    ovulation_day = working_length - LUTEAL_PHASE_DAYS
    # Cycle day 1 is the start date itself, so cycle day D falls at start + (D-1).
    fertile_start = current_start + timedelta(days=ovulation_day - 6)  # cycle day O-5
    fertile_end = current_start + timedelta(days=ovulation_day)        # cycle day O+1

    is_on_period_today = False
    for d in current.get("period_days") or []:
        if _to_date(d) == today:
            is_on_period_today = True
            break
    if not current.get("period_days") and cycle_day <= avg_period and current.get("end_date") is None:
        is_on_period_today = True

    if completed_lengths:
        spread = max(completed_lengths) - min(completed_lengths)
        confidence = max(MIN_CONFIDENCE, min(0.9, 0.9 - spread * 0.05))
    else:
        confidence = MIN_CONFIDENCE

    message = None
    if needs_more_data:
        message = (
            "Predictions are rough estimates until you log another cycle. "
            "Log another cycle to improve predictions."
        )

    return {
        "has_data": True,
        "needs_more_data": needs_more_data,
        "message": message,
        "current_cycle_day": cycle_day,
        "current_phase": phase,
        "cycle_day_of_phase": phase_day,
        "current_cycle_length": current_length,
        "average_cycle_length": _average(completed_lengths) if completed_lengths else None,
        "average_period_length": _average(period_lengths) if period_lengths else None,
        "cycles_tracked": cycles_tracked,
        "predicted_period_start": next_period_start.isoformat(),
        "predicted_period_end": next_period_end.isoformat(),
        "estimated_fertile_start": fertile_start.isoformat(),
        "estimated_fertile_end": fertile_end.isoformat(),
        "is_on_period_today": is_on_period_today,
        "confidence": round(confidence, 2),
    }


def calendar_month(
    cycles: list[dict],
    symptoms: list[dict],
    year: int,
    month: int,
    today: date | None = None,
) -> dict:
    """Build a one-month calendar view with period/predicted/fertile/symptom markers."""
    today = today or date.today()
    analysis = analyze_cycles(cycles, today)

    first = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    num_days = (next_month - first).days

    period_dates: dict[str, str | None] = {}
    for c in cycles:
        flow_by_date = {p["date"]: p.get("flow_level") for p in c.get("period_day_records") or []}
        if c.get("period_days"):
            for d in c["period_days"]:
                period_dates[d] = flow_by_date.get(d)
        else:
            start = _to_date(c["start_date"])
            length = c.get("period_length") or DEFAULT_PERIOD_LENGTH
            for i in range(max(length, 1)):
                iso = (start + timedelta(days=i)).isoformat()
                if iso not in period_dates:
                    period_dates[iso] = None

    predicted_dates: set[str] = set()
    fertile_dates: set[str] = set()
    if analysis.get("has_data"):
        span = analysis_cycle_length(analysis)
        period_len = analysis.get("average_period_length") or DEFAULT_PERIOD_LENGTH
        base = _to_date(analysis["predicted_period_start"])
        fertile_base = _to_date(analysis["estimated_fertile_start"])
        fertile_end = _to_date(analysis["estimated_fertile_end"])
        for ahead in range(0, _MONTHS_AHEAD + 1):
            shift = timedelta(days=ahead * span)
            for i in range(period_len):
                predicted_dates.add((base + shift + timedelta(days=i)).isoformat())
            for i in range((fertile_end - fertile_base).days + 1):
                fertile_dates.add((fertile_base + shift + timedelta(days=i)).isoformat())

    symptom_by_date: dict[str, list[str]] = {}
    for s in symptoms:
        symptom_by_date.setdefault(s["date"], []).append(s["symptom_type"])

    days = []
    for i in range(num_days):
        d = first + timedelta(days=i)
        iso = d.isoformat()
        in_period = iso in period_dates
        days.append({
            "date": iso,
            "in_period": in_period,
            "is_predicted_period": iso in predicted_dates and not in_period,
            "is_fertile_window": iso in fertile_dates and not in_period,
            "is_today": d == today,
            "has_symptom": iso in symptom_by_date,
            "symptom_types": symptom_by_date.get(iso, []),
            "flow_level": period_dates.get(iso) if in_period else None,
        })

    return {
        "month": f"{year:04d}-{month:02d}",
        "days": days,
        "average_cycle_length": analysis.get("average_cycle_length"),
    }


def analysis_cycle_length(analysis: dict) -> int:
    """Working cycle length used by an analysis result (for projecting months)."""
    if analysis.get("current_cycle_length"):
        return int(analysis["current_cycle_length"])
    if analysis.get("average_cycle_length"):
        return int(analysis["average_cycle_length"])
    return DEFAULT_CYCLE_LENGTH
