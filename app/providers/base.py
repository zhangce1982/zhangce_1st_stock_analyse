from abc import ABC, abstractmethod

from app.models import StockSnapshot


class MarketDataProvider(ABC):
    @abstractmethod
    async def list_snapshots(self) -> list[StockSnapshot]:
        """Return normalized snapshots without exposing vendor-specific fields."""

    @abstractmethod
    async def get_snapshot(self, code: str) -> StockSnapshot | None:
        """Return one normalized stock snapshot."""

