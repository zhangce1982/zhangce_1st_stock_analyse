import asyncio
from datetime import datetime, timezone
from typing import Any

from app.models import StockSnapshot
from app.providers.base import MarketDataProvider
from app.providers.utils import clamp, exchange_code, first_value


class AkShareMarketDataProvider(MarketDataProvider):
    """AKShare adapter. Vendor fields are normalized at this boundary."""

    def __init__(self, watchlist: list[str], ak_module: Any | None = None):
        if ak_module is None:
            import akshare as ak_module
        self.ak = ak_module
        self.watchlist = watchlist

    async def list_snapshots(self) -> list[StockSnapshot]:
        results = await asyncio.gather(
            *(self.get_snapshot(code) for code in self.watchlist),
            return_exceptions=True,
        )
        snapshots = [item for item in results if isinstance(item, StockSnapshot)]
        if not snapshots:
            errors = [str(item) for item in results if isinstance(item, Exception)]
            raise RuntimeError(f"AKShare 未返回可用数据: {'; '.join(errors[:2])}")
        return snapshots

    async def get_snapshot(self, code: str) -> StockSnapshot | None:
        return await asyncio.to_thread(self._get_snapshot_sync, code)

    def _get_snapshot_sync(self, code: str) -> StockSnapshot:
        info_df = self.ak.stock_individual_info_em(symbol=code, timeout=10)
        info = dict(zip(info_df["item"], info_df["value"], strict=False))
        finance_df = self.ak.stock_financial_analysis_indicator_em(
            symbol=exchange_code(code), indicator="按报告期"
        )
        if finance_df.empty:
            raise ValueError(f"{code} 没有财务指标")
        finance = finance_df.iloc[0].to_dict()

        revenue_growth = first_value(
            finance,
            ("TOTALOPERATEREVETZ", "TOTAL_OPERATE_INCOME_YOY", "营业总收入同比增长"),
        )
        profit_growth = first_value(
            finance,
            ("PARENTNETPROFITTZ", "PARENT_NETPROFIT_YOY", "归母净利润同比增长"),
        )
        cash_ratio = first_value(
            finance,
            ("NETCASHOPERATE", "NET_CASHFLOW_OPERATE", "经营现金流量净额"),
        )
        net_profit = abs(
            first_value(finance, ("PARENTNETPROFIT", "PARENT_NETPROFIT", "归母净利润"))
        )
        cash_quality = 50.0 if not net_profit else clamp(cash_ratio / net_profit * 50, 0, 100)
        pe = first_value(info, ("市盈率(动态)", "市盈率"))
        valuation = 0.0 if pe <= 0 else clamp(35 - pe)

        missing = []
        if not revenue_growth:
            missing.append("revenue_growth")
        if not profit_growth:
            missing.append("profit_growth")
        if not cash_ratio or not net_profit:
            missing.append("operating_cashflow_quality")
        missing.extend(["shareholder_signal", "policy_signal"])

        return StockSnapshot(
            code=code,
            name=str(info.get("股票简称", code)),
            industry=str(info.get("行业", "未知行业")),
            revenue_growth=revenue_growth,
            profit_growth=profit_growth,
            operating_cashflow_quality=cash_quality,
            shareholder_signal=0,
            policy_signal=0,
            valuation_signal=valuation,
            risk_penalty=5 + len(missing) * 2,
            updated_at=datetime.now(timezone.utc),
            source="akshare",
            missing_fields=missing,
        )
