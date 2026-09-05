from abc import ABC, abstractmethod
from app.services.wearables.schemas import DeviceInfo, DailyMetrics, WeeklyMetrics, SyncResult


class WearableProvider(ABC):
    @abstractmethod
    def get_device_info(self) -> DeviceInfo:
        ...

    @abstractmethod
    def get_daily_metrics(self) -> DailyMetrics:
        ...

    @abstractmethod
    def get_weekly_metrics(self) -> list[WeeklyMetrics]:
        ...

    @abstractmethod
    def sync(self) -> SyncResult:
        ...
