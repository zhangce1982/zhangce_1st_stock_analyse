import asyncio
from datetime import date

import httpx
import pandas as pd

from app.events.announcements import AkShareAnnouncementProvider
from app.events.classifier import classify_text
from app.events.policies import GovPolicyProvider


class FakeAnnouncementAk:
    @staticmethod
    def stock_notice_report(date):
        return pd.DataFrame(
            [
                ["600001", "测试股份", "关于股份回购进展的公告", "重大事项", "2026-08-08", "https://example.com/a"],
                ["600002", "其他股份", "日常公告", "其他", "2026-08-08", "https://example.com/b"],
            ]
        )


def test_classifier_maps_policy_to_industry():
    industries, direction, score, evidence = classify_text("支持人工智能和芯片产业加快发展")
    assert "计算机" in industries
    assert "电子" in industries
    assert direction == "positive"
    assert score > 50
    assert evidence


def test_announcement_provider_filters_watchlist():
    provider = AkShareAnnouncementProvider(["600001"], ak_module=FakeAnnouncementAk())
    events = asyncio.run(provider.list_events(date(2026, 8, 8)))
    assert len(events) == 1
    assert events[0].stock_codes == ["600001"]
    assert events[0].direction == "positive"


def test_policy_provider_parses_official_page():
    html = """
    <html><body><ul><li>
      <a href="https://www.gov.cn/zhengce/content/202608/example.htm">国务院关于支持人工智能产业发展的意见</a>
      <span>2026-08-08</span>
    </li></ul></body></html>
    """

    def handler(request):
        return httpx.Response(200, text=html, request=request)

    provider = GovPolicyProvider(transport=httpx.MockTransport(handler))
    events = asyncio.run(provider.list_events(date(2026, 8, 8)))
    assert len(events) == 1
    assert events[0].source == "中国政府网"
    assert events[0].direction == "positive"
    assert "计算机" in events[0].industries
