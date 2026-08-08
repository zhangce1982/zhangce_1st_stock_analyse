import asyncio
from datetime import date
from typing import Any

from app.models import DailyPrice
from app.providers.utils import baostock_code


class BaoStockHistoricalPriceProvider:
    def __init__(self, bs_module: Any | None = None):
        if bs_module is None:
            import baostock as bs_module
        self.bs = bs_module

    async def get_prices(
        self, codes: list[str], start_date: date, end_date: date
    ) -> dict[str, list[DailyPrice]]:
        return await asyncio.to_thread(self._get_prices_sync, codes, start_date, end_date)

    def _get_prices_sync(
        self, codes: list[str], start_date: date, end_date: date
    ) -> dict[str, list[DailyPrice]]:
        login = self.bs.login()
        if login.error_code != "0":
            raise RuntimeError(f"BaoStock login failed: {login.error_msg}")
        output: dict[str, list[DailyPrice]] = {}
        try:
            for code in codes:
                result = self.bs.query_history_k_data_plus(
                    baostock_code(code),
                    "date,code,close,tradestatus",
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    frequency="d",
                    adjustflag="2",
                )
                prices = []
                while result.error_code == "0" and result.next():
                    row = dict(zip(result.fields, result.get_row_data(), strict=False))
                    if row.get("tradestatus") != "1" or not row.get("close"):
                        continue
                    close = float(row["close"])
                    if close > 0:
                        prices.append(
                            DailyPrice(
                                code=code,
                                trade_date=date.fromisoformat(row["date"]),
                                close=close,
                            )
                        )
                output[code] = prices
        finally:
            self.bs.logout()
        return output
