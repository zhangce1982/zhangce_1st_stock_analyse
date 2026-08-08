from datetime import datetime, timezone

from app.models import StockSnapshot
from app.providers.base import MarketDataProvider


class MockMarketDataProvider(MarketDataProvider):
    def _items(self) -> list[StockSnapshot]:
        now = datetime.now(timezone.utc)
        return [
            StockSnapshot(
                code="600001",
                name="示例制造",
                industry="高端制造",
                revenue_growth=18.2,
                profit_growth=32.5,
                operating_cashflow_quality=78,
                shareholder_signal=22,
                policy_signal=45,
                valuation_signal=5,
                risk_penalty=8,
                updated_at=now,
            ),
            StockSnapshot(
                code="000002",
                name="示例能源",
                industry="新能源",
                revenue_growth=9.4,
                profit_growth=12.1,
                operating_cashflow_quality=64,
                shareholder_signal=-8,
                policy_signal=62,
                valuation_signal=-12,
                risk_penalty=15,
                updated_at=now,
            ),
            StockSnapshot(
                code="300003",
                name="示例科技",
                industry="电子",
                revenue_growth=26.8,
                profit_growth=41.3,
                operating_cashflow_quality=55,
                shareholder_signal=30,
                policy_signal=25,
                valuation_signal=-28,
                risk_penalty=18,
                updated_at=now,
            ),
        ]

    async def list_snapshots(self) -> list[StockSnapshot]:
        return self._items()

    async def get_snapshot(self, code: str) -> StockSnapshot | None:
        return next((item for item in self._items() if item.code == code), None)

