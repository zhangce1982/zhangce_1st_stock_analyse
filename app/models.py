from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class StockSnapshot(BaseModel):
    code: str
    name: str
    industry: str
    revenue_growth: float
    profit_growth: float
    operating_cashflow_quality: float = Field(ge=0, le=100)
    shareholder_signal: float = Field(ge=-100, le=100)
    policy_signal: float = Field(ge=-100, le=100)
    valuation_signal: float = Field(ge=-100, le=100)
    risk_penalty: float = Field(ge=0, le=100)
    updated_at: datetime
    source: str = "unknown"
    missing_fields: list[str] = Field(default_factory=list)


class Opportunity(BaseModel):
    code: str
    name: str
    industry: str
    horizon: Literal["short", "medium"]
    score: float = Field(ge=0, le=100)
    confidence: Literal["low", "medium", "high"]
    reasons: list[str]
    risks: list[str]
    data_updated_at: datetime
    source: str
    missing_fields: list[str]


class MarketEvent(BaseModel):
    event_id: str
    event_type: Literal["announcement", "policy"]
    title: str
    published_date: date
    url: str
    source: str
    stock_codes: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    direction: Literal["positive", "negative", "neutral", "uncertain"]
    impact_score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
