from datetime import date, datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.events.classifier import classify_text, event_id
from app.models import MarketEvent


class GovPolicyProvider:
    source_url = "https://www.gov.cn/zhengce/index.htm"

    def __init__(self, timeout_seconds: float = 15, transport: httpx.AsyncBaseTransport | None = None):
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def list_events(self, target_date: date | None = None) -> list[MarketEvent]:
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "A-Share-Research/0.1 (+public policy reader)"},
            transport=self.transport,
        ) as client:
            response = await client.get(self.source_url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        events = []
        seen = set()
        for anchor in soup.select('a[href*="/zhengce/content/"]'):
            title = anchor.get_text(" ", strip=True)
            url = urljoin(self.source_url, anchor.get("href", ""))
            if not title or url in seen:
                continue
            date_node = anchor.find_next_sibling("span")
            if date_node is None:
                continue
            try:
                published = datetime.strptime(date_node.get_text(strip=True), "%Y-%m-%d").date()
            except ValueError:
                continue
            if target_date is not None and published != target_date:
                continue
            seen.add(url)
            industries, direction, impact, evidence = classify_text(title)
            if "国务院" in title:
                impact = min(100, impact + 10)
                evidence.append("发布层级：国务院")
            events.append(
                MarketEvent(
                    event_id=event_id("gov.cn", url, title),
                    event_type="policy",
                    title=title,
                    published_date=published,
                    url=url,
                    source="中国政府网",
                    industries=industries,
                    direction=direction,
                    impact_score=impact,
                    evidence=evidence,
                )
            )
        return events[:30]
