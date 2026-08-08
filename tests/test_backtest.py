import asyncio
from datetime import date, datetime, timezone

from app.backtest.service import BacktestService
from app.models import DailyPrice, SignalObservation


class FakeSignalStore:
    async def list_signal_history(self, horizon):
        return [
            SignalObservation(
                code="600001",
                horizon=horizon,
                score=75,
                confidence="high",
                source="test",
                calculated_at=datetime(2026, 1, 2, 12, tzinfo=timezone.utc),
            )
        ]


class FakePriceProvider:
    async def get_prices(self, codes, start_date, end_date):
        closes = [100, 101, 102, 103, 104, 110, 112]
        dates = [date(2026, 1, day) for day in range(2, 9)]
        return {
            "600001": [
                DailyPrice(code="600001", trade_date=trade_date, close=close)
                for trade_date, close in zip(dates, closes, strict=True)
            ]
        }


def test_backtest_enters_after_signal_date():
    service = BacktestService(FakeSignalStore(), FakePriceProvider(), minimum_samples=1)
    results = asyncio.run(service.evaluate("short"))
    five_day = results[0]
    # Entry is Jan 3 at 101, not signal-day Jan 2 at 100; exit is Jan 8 at 112.
    assert five_day.average_return == 10.89
    assert five_day.win_rate == 100
    assert five_day.status == "ready"


def test_empty_history_is_reported_honestly():
    class EmptyStore:
        async def list_signal_history(self, horizon):
            return []

    service = BacktestService(EmptyStore(), FakePriceProvider())
    results = asyncio.run(service.evaluate("medium"))
    assert results[0].status == "insufficient_data"
    assert results[0].evaluated_signals == 0
