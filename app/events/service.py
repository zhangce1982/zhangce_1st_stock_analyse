import asyncio
from datetime import date

from app.events.announcements import AkShareAnnouncementProvider
from app.events.policies import GovPolicyProvider
from app.models import MarketEvent
from app.storage import ResearchStorage


class EventService:
    def __init__(self, watchlist: list[str], storage: ResearchStorage):
        self.announcements = AkShareAnnouncementProvider(watchlist)
        self.policies = GovPolicyProvider()
        self.storage = storage

    async def list_events(self, target_date: date | None = None) -> list[MarketEvent]:
        policy_date = target_date
        announcement_date = target_date or date.today()
        results = await asyncio.gather(
            self.announcements.list_events(announcement_date),
            self.policies.list_events(policy_date),
            return_exceptions=True,
        )
        events = []
        for result in results:
            if isinstance(result, list):
                events.extend(result)
        events = sorted(events, key=lambda item: (item.published_date, item.impact_score), reverse=True)
        if events:
            await self.storage.save_events(events)
            return events
        return await self.storage.list_events(target_date)
