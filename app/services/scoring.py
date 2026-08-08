from typing import Literal

from app.models import Opportunity, StockSnapshot


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def score_snapshot(
    snapshot: StockSnapshot, horizon: Literal["short", "medium"]
) -> Opportunity:
    growth = _clamp((snapshot.revenue_growth + snapshot.profit_growth) / 2 + 40)
    weights = (
        {"growth": 0.25, "cash": 0.15, "shareholder": 0.20, "policy": 0.20, "valuation": 0.20}
        if horizon == "short"
        else {"growth": 0.32, "cash": 0.23, "shareholder": 0.10, "policy": 0.25, "valuation": 0.10}
    )
    normalized_shareholder = (snapshot.shareholder_signal + 100) / 2
    normalized_policy = (snapshot.policy_signal + 100) / 2
    normalized_valuation = (snapshot.valuation_signal + 100) / 2
    raw_score = (
        growth * weights["growth"]
        + snapshot.operating_cashflow_quality * weights["cash"]
        + normalized_shareholder * weights["shareholder"]
        + normalized_policy * weights["policy"]
        + normalized_valuation * weights["valuation"]
        - snapshot.risk_penalty * 0.35
    )
    score = round(_clamp(raw_score), 1)

    reasons = []
    if snapshot.profit_growth >= 20:
        reasons.append(f"净利润同比增长 {snapshot.profit_growth:.1f}%")
    if snapshot.operating_cashflow_quality >= 70:
        reasons.append("经营现金流质量较好")
    if snapshot.policy_signal >= 30:
        reasons.append("所属产业存在较强政策正向信号")
    if snapshot.shareholder_signal >= 20:
        reasons.append("股东行为信号偏正面")
    if not reasons:
        reasons.append("多项指标处于中性区间")

    risks = []
    if snapshot.valuation_signal <= -20:
        risks.append("估值信号偏高")
    if snapshot.risk_penalty >= 15:
        risks.append("存在需要复核的风险扣分项")
    if snapshot.missing_fields:
        risks.append("部分字段缺失，评分已采用中性值")
    if not risks:
        risks.append("仍需关注市场波动与数据更新风险")

    confidence = "high" if score >= 75 else "medium" if score >= 55 else "low"
    return Opportunity(
        code=snapshot.code,
        name=snapshot.name,
        industry=snapshot.industry,
        horizon=horizon,
        score=score,
        confidence=confidence,
        reasons=reasons,
        risks=risks,
        data_updated_at=snapshot.updated_at,
        source=snapshot.source,
        missing_fields=snapshot.missing_fields,
    )
