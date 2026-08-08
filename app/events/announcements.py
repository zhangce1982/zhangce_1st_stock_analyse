import asyncio
from datetime import date, datetime
from typing import Any

from app.events.classifier import classify_text, event_id
from app.models import MarketEvent


class AkShareAnnouncementProvider:
    def __init__(self, watchlist: list[str], ak_module: Any | None = None):
        if ak_module is None:
            import akshare as ak_module
        self.ak = ak_module
        self.watchlist = set(watchlist)

    async def list_events(self, target_date: date) -> list[MarketEvent]:
        return await asyncio.to_thread(self._list_events_sync, target_date)

    def _list_events_sync(self, target_date: date) -> list[MarketEvent]:
        frame = self.ak.stock_notice_report(date=target_date.strftime("%Y%m%d"))
        events = []
        for values in frame.itertuples(index=False, name=None):
            if len(values) < 6:
                continue
            code, _name, title, _category, published, url = values[:6]
            code = str(code).zfill(6)
            if self.watchlist and code not in self.watchlist:
                continue
            title = str(title)
            industries, direction, impact, evidence = classify_text(title)
            published_date = published if isinstance(published, date) else datetime.fromisoformat(str(published)).date()
            events.append(
                MarketEvent(
                    event_id=event_id("akshare-eastmoney", str(url), title),
                    event_type="announcement",
                    title=title,
                    published_date=published_date,
                    url=str(url),
                    source="AKShare/东方财富公告",
                    stock_codes=[code],
                    industries=industries,
                    direction=direction,
                    impact_score=impact,
                    evidence=evidence,
                )
            )
        return events[:300]
