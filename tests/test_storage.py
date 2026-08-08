import asyncio
from datetime import date

from app.models import MarketEvent
from app.storage import ResearchStorage


def test_event_round_trip(tmp_path):
    storage = ResearchStorage(str(tmp_path / "test.db"))
    event = MarketEvent(
        event_id="event-1",
        event_type="policy",
        title="支持人工智能产业发展",
        published_date=date(2026, 8, 8),
        url="https://www.gov.cn/example",
        source="中国政府网",
        industries=["计算机"],
        direction="positive",
        impact_score=78,
        evidence=["方向关键词：支持"],
    )
    asyncio.run(storage.save_events([event]))
    result = asyncio.run(storage.list_events(date(2026, 8, 8)))
    assert result == [event]
