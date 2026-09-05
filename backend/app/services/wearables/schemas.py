from pydantic import BaseModel


class DeviceInfo(BaseModel):
    device_name: str
    device_type: str
    provider: str
    battery_percent: int
    firmware_version: str


class DailyMetricItem(BaseModel):
    metric_type: str
    value: float
    unit: str
    label: str
    target: float | None = None
    sub_text: str | None = None


class DailyMetrics(BaseModel):
    device: DeviceInfo
    metrics: list[DailyMetricItem]


class WeeklyDayEntry(BaseModel):
    day: str
    steps: int


class WeeklyMetrics(BaseModel):
    days: list[WeeklyDayEntry]
    total_steps: int
    avg_steps: int


class SyncResult(BaseModel):
    records_synced: int
    metrics: list[DailyMetricItem]


class WearableInsight(BaseModel):
    title: str
    observed: str
    context: str
    suggested_action: str
