from datetime import date
from statistics import mean, median
from typing import Literal, Protocol

from app.backtest.prices import BaoStockHistoricalPriceProvider
from app.models import BacktestResult, DailyPrice, SignalObservation


class SignalStore(Protocol):
    async def list_signal_history(self, horizon: str) -> list[SignalObservation]: ...


class BacktestService:
    HOLDING_PERIODS = {"short": (5, 20), "medium": (60,)}

    def __init__(
        self,
        storage: SignalStore,
        price_provider: BaoStockHistoricalPriceProvider,
        minimum_samples: int = 20,
    ):
        self.storage = storage
        self.price_provider = price_provider
        self.minimum_samples = minimum_samples

    async def evaluate(
        self, horizon: Literal["short", "medium"]
    ) -> list[BacktestResult]:
        signals = await self.storage.list_signal_history(horizon)
        if not signals:
            return [self._empty_result(horizon, days, 0) for days in self.HOLDING_PERIODS[horizon]]
        start = min(item.calculated_at.date() for item in signals)
        prices = await self.price_provider.get_prices(
            sorted({item.code for item in signals}), start, date.today()
        )
        return [self._calculate(signals, prices, horizon, days) for days in self.HOLDING_PERIODS[horizon]]

    def _calculate(
        self,
        signals: list[SignalObservation],
        prices: dict[str, list[DailyPrice]],
        horizon: Literal["short", "medium"],
        holding_days: int,
    ) -> BacktestResult:
        returns = []
        for signal in signals:
            series = prices.get(signal.code, [])
            entry_index = next(
                (index for index, item in enumerate(series) if item.trade_date > signal.calculated_at.date()),
                None,
            )
            if entry_index is None or entry_index + holding_days >= len(series):
                continue
            entry = series[entry_index].close
            exit_price = series[entry_index + holding_days].close
            returns.append((exit_price / entry - 1) * 100)

        if not returns:
            return self._empty_result(horizon, holding_days, len(signals))
        evaluated = len(returns)
        return BacktestResult(
            horizon=horizon,
            holding_days=holding_days,
            total_signals=len(signals),
            evaluated_signals=evaluated,
            pending_signals=len(signals) - evaluated,
            status="ready" if evaluated >= self.minimum_samples else "insufficient_data",
            win_rate=round(sum(value > 0 for value in returns) / evaluated * 100, 2),
            average_return=round(mean(returns), 2),
            median_return=round(median(returns), 2),
            best_return=round(max(returns), 2),
            worst_return=round(min(returns), 2),
            methodology="Enter on the first close strictly after the signal date; hold by trading days.",
        )

    @staticmethod
    def _empty_result(
        horizon: Literal["short", "medium"], holding_days: int, total: int
    ) -> BacktestResult:
        return BacktestResult(
            horizon=horizon,
            holding_days=holding_days,
            total_signals=total,
            evaluated_signals=0,
            pending_signals=total,
            status="insufficient_data",
            methodology="Waiting for enough trading days after recorded signals.",
        )
