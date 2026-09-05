import random
from app.services.wearables.base import WearableProvider
from app.services.wearables.schemas import (
    DeviceInfo, DailyMetrics, DailyMetricItem,
    WeeklyMetrics, WeeklyDayEntry, SyncResult,
)

WEEKLY_STEPS = [
    ("Mon", 6421),
    ("Tue", 7892),
    ("Wed", 5731),
    ("Thu", 8102),
    ("Fri", 9221),
    ("Sat", 7845),
    ("Sun", 8426),
]

BASE_METRICS = [
    DailyMetricItem(metric_type="steps", value=8426, unit="steps", label="Steps", target=10000),
    DailyMetricItem(metric_type="active_calories", value=487, unit="kcal", label="Active Calories"),
    DailyMetricItem(metric_type="resting_heart_rate", value=67, unit="bpm", label="Resting HR"),
    DailyMetricItem(metric_type="avg_heart_rate", value=76, unit="bpm", label="Average HR"),
    DailyMetricItem(metric_type="sleep", value=6.7, unit="hours", label="Sleep", sub_text="Sleep score 78"),
    DailyMetricItem(metric_type="distance", value=5.8, unit="km", label="Distance"),
    DailyMetricItem(metric_type="water", value=1.8, unit="L", label="Hydration"),
    DailyMetricItem(metric_type="weight", value=82.0, unit="kg", label="Weight"),
]


class MockWearableProvider(WearableProvider):
    """Simulated Fitbit Charge 6 for demo purposes."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def get_device_info(self) -> DeviceInfo:
        return DeviceInfo(
            device_name="Fitbit Charge 6",
            device_type="fitness_tracker",
            provider="fitbit_mock",
            battery_percent=72,
            firmware_version="2.1.4",
        )

    def get_daily_metrics(self) -> DailyMetrics:
        return DailyMetrics(
            device=self.get_device_info(),
            metrics=[m.model_copy() for m in BASE_METRICS],
        )

    def get_weekly_metrics(self) -> list[WeeklyMetrics]:
        entries = [WeeklyDayEntry(day=d, steps=s) for d, s in WEEKLY_STEPS]
        total = sum(e.steps for e in entries)
        return [WeeklyMetrics(days=entries, total_steps=total, avg_steps=total // len(entries))]

    def sync(self) -> SyncResult:
        jitter = self._rng.randint(-200, 200)
        synced_metrics = [m.model_copy() for m in BASE_METRICS]
        for m in synced_metrics:
            if m.metric_type == "steps":
                m.value = max(1000, int(m.value) + jitter)
            elif m.metric_type == "active_calories":
                m.value = max(50, int(m.value) + self._rng.randint(-30, 30))
            elif m.metric_type == "resting_heart_rate":
                m.value = max(50, int(m.value) + self._rng.randint(-2, 2))
        record_count = 200 + self._rng.randint(20, 80)
        return SyncResult(records_synced=record_count, metrics=synced_metrics)
