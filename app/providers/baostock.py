import asyncio
from datetime import datetime, timezone
from typing import Any

from app.models import StockSnapshot
from app.providers.base import MarketDataProvider
from app.providers.utils import baostock_code, clamp, first_value


def _result_rows(result: Any) -> list[dict[str, str]]:
    rows = []
    while result.error_code == "0" and result.next():
        rows.append(dict(zip(result.fields, result.get_row_data(), strict=False)))
    return rows


class BaoStockMarketDataProvider(MarketDataProvider):
    """BaoStock fallback for post-market fundamentals."""

    def __init__(self, watchlist: list[str], bs_module: Any | None = None):
        if bs_module is None:
            import baostock as bs_module
        self.bs = bs_module
        self.watchlist = watchlist

    async def list_snapshots(self) -> list[StockSnapshot]:
        return await asyncio.to_thread(self._list_snapshots_sync)

    async def get_snapshot(self, code: str) -> StockSnapshot | None:
        return await asyncio.to_thread(self._single_session, code)

    def _single_session(self, code: str) -> StockSnapshot | None:
        login = self.bs.login()
        if login.error_code != "0":
            raise RuntimeError(f"BaoStock 登录失败: {login.error_msg}")
        try:
            return self._get_snapshot_logged_in(code)
        finally:
            self.bs.logout()

    def _list_snapshots_sync(self) -> list[StockSnapshot]:
        login = self.bs.login()
        if login.error_code != "0":
            raise RuntimeError(f"BaoStock 登录失败: {login.error_msg}")
        try:
            snapshots = [self._get_snapshot_logged_in(code) for code in self.watchlist]
            return [item for item in snapshots if item is not None]
        finally:
            self.bs.logout()

    def _get_snapshot_logged_in(self, code: str) -> StockSnapshot | None:
        symbol = baostock_code(code)
        basic_rows = _result_rows(self.bs.query_stock_basic(code=symbol))
        if not basic_rows:
            return None
        basic = basic_rows[0]
        industry_rows = _result_rows(self.bs.query_stock_industry(code=symbol))
        industry = industry_rows[0].get("industry", "未知行业") if industry_rows else "未知行业"

        today = datetime.now()
        growth_rows: list[dict[str, str]] = []
        profit_rows: list[dict[str, str]] = []
        cash_rows: list[dict[str, str]] = []
        for year in (today.year, today.year - 1):
            for quarter in (4, 3, 2, 1):
                if not growth_rows:
                    growth_rows = _result_rows(self.bs.query_growth_data(symbol, year, quarter))
                if not profit_rows:
                    profit_rows = _result_rows(self.bs.query_profit_data(symbol, year, quarter))
                if not cash_rows:
                    cash_rows = _result_rows(self.bs.query_cash_flow_data(symbol, year, quarter))
                if growth_rows and profit_rows and cash_rows:
                    break
            if growth_rows and profit_rows and cash_rows:
                break

        growth = growth_rows[0] if growth_rows else {}
        profit = profit_rows[0] if profit_rows else {}
        cash = cash_rows[0] if cash_rows else {}
        profit_growth = first_value(growth, ("YOYNI", "YOYPNI")) * 100
        # BaoStock growth data does not expose revenue growth directly. Do not
        # mislabel total-asset growth as revenue growth.
        revenue_growth = 0.0
        cash_to_asset = first_value(cash, ("NCFToAsset", "CFOToOR"))
        cash_quality = clamp(50 + cash_to_asset * 100, 0, 100)

        missing = [
            "revenue_growth",
            "shareholder_signal",
            "policy_signal",
            "valuation_signal",
        ]
        if not growth_rows:
            missing.append("profit_growth")
        if not cash_rows:
            missing.append("operating_cashflow_quality")

        return StockSnapshot(
            code=code,
            name=basic.get("code_name", code),
            industry=industry,
            revenue_growth=revenue_growth,
            profit_growth=profit_growth,
            operating_cashflow_quality=cash_quality,
            shareholder_signal=0,
            policy_signal=0,
            valuation_signal=0,
            risk_penalty=8 + len(missing) * 2,
            updated_at=datetime.now(timezone.utc),
            source="baostock",
            missing_fields=missing,
        )
