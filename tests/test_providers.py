import asyncio

import pandas as pd

from app.providers.akshare import AkShareMarketDataProvider
from app.providers.base import MarketDataProvider
from app.providers.fallback import FallbackMarketDataProvider


class FakeAkShare:
    @staticmethod
    def stock_individual_info_em(symbol, timeout):
        return pd.DataFrame(
            {
                "item": ["股票简称", "行业", "市盈率(动态)"],
                "value": ["测试股份", "制造业", "20.5"],
            }
        )

    @staticmethod
    def stock_financial_analysis_indicator_em(symbol, indicator):
        assert symbol == "600001.SH"
        assert indicator == "按报告期"
        return pd.DataFrame(
            [
                {
                    "TOTALOPERATEREVETZ": "18.2%",
                    "PARENTNETPROFITTZ": "31.4%",
                    "NETCASHOPERATE": "800,000",
                    "PARENTNETPROFIT": "1,000,000",
                }
            ]
        )


class BrokenProvider(MarketDataProvider):
    async def list_snapshots(self):
        raise RuntimeError("upstream unavailable")

    async def get_snapshot(self, code):
        raise RuntimeError("upstream unavailable")


class StaticProvider(MarketDataProvider):
    def __init__(self, snapshots):
        self.snapshots = snapshots

    async def list_snapshots(self):
        return self.snapshots

    async def get_snapshot(self, code):
        return next((item for item in self.snapshots if item.code == code), None)


def test_akshare_fields_are_normalized():
    provider = AkShareMarketDataProvider(["600001"], ak_module=FakeAkShare())
    snapshot = asyncio.run(provider.get_snapshot("600001"))
    assert snapshot is not None
    assert snapshot.name == "测试股份"
    assert snapshot.industry == "制造业"
    assert snapshot.revenue_growth == 18.2
    assert snapshot.profit_growth == 31.4
    assert snapshot.source == "akshare"


def test_fallback_is_used_when_primary_fails():
    sample = asyncio.run(
        AkShareMarketDataProvider(["600001"], ak_module=FakeAkShare()).get_snapshot("600001")
    )
    provider = FallbackMarketDataProvider(BrokenProvider(), StaticProvider([sample]))
    snapshots = asyncio.run(provider.list_snapshots())
    assert snapshots[0].code == "600001"
