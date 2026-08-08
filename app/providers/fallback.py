from app.models import StockSnapshot
from app.providers.base import MarketDataProvider


class FallbackMarketDataProvider(MarketDataProvider):
    def __init__(self, primary: MarketDataProvider, fallback: MarketDataProvider):
        self.primary = primary
        self.fallback = fallback

    async def list_snapshots(self) -> list[StockSnapshot]:
        try:
            snapshots = await self.primary.list_snapshots()
            if snapshots:
                return snapshots
        except Exception:
            pass
        return await self.fallback.list_snapshots()

    async def get_snapshot(self, code: str) -> StockSnapshot | None:
        try:
            snapshot = await self.primary.get_snapshot(code)
            if snapshot is not None:
                return snapshot
        except Exception:
            pass
        return await self.fallback.get_snapshot(code)
