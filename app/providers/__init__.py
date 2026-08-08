from app.config import settings
from app.providers.base import MarketDataProvider
from app.providers.fallback import FallbackMarketDataProvider
from app.providers.mock import MockMarketDataProvider


def create_provider() -> MarketDataProvider:
    if settings.data_provider == "mock":
        return MockMarketDataProvider()
    if settings.data_provider == "akshare":
        from app.providers.akshare import AkShareMarketDataProvider

        primary = AkShareMarketDataProvider(settings.watchlist_codes)
        if settings.provider_fallback == "baostock":
            from app.providers.baostock import BaoStockMarketDataProvider

            return FallbackMarketDataProvider(
                primary, BaoStockMarketDataProvider(settings.watchlist_codes)
            )
        return primary
    if settings.data_provider == "baostock":
        from app.providers.baostock import BaoStockMarketDataProvider

        return BaoStockMarketDataProvider(settings.watchlist_codes)
    raise RuntimeError(
        f"数据提供器 {settings.data_provider!r} 尚未配置；"
        "接入真实 API 前请提供接口文档和授权方式。"
    )
