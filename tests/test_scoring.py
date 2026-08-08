from datetime import datetime, timezone

from app.models import StockSnapshot
from app.services.scoring import score_snapshot


def test_score_is_explainable_and_bounded():
    snapshot = StockSnapshot(
        code="600001",
        name="测试公司",
        industry="制造",
        revenue_growth=20,
        profit_growth=30,
        operating_cashflow_quality=80,
        shareholder_signal=20,
        policy_signal=40,
        valuation_signal=0,
        risk_penalty=5,
        updated_at=datetime.now(timezone.utc),
    )
    result = score_snapshot(snapshot, "short")
    assert 0 <= result.score <= 100
    assert result.reasons
    assert result.risks

