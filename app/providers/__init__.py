from app.config import settings
from app.providers.base import MarketDataProvider
from app.providers.mock import MockMarketDataProvider


def create_provider() -> MarketDataProvider:
    if settings.data_provider == "mock":
        return MockMarketDataProvider()
    raise RuntimeError(
        f"数据提供器 {settings.data_provider!r} 尚未配置；"
        "接入真实 API 前请提供接口文档和授权方式。"
    )

