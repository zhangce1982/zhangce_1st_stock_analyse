import asyncio
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from app.models import MarketEvent, Opportunity


class ResearchStorage:
    """Small normalized store for reproducibility, not a vendor-data mirror."""

    def __init__(self, database_path: str):
        self.path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS market_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                published_date TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                stock_codes_json TEXT NOT NULL,
                industries_json TEXT NOT NULL,
                direction TEXT NOT NULL,
                impact_score REAL NOT NULL,
                evidence_json TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_market_events_date
                ON market_events(published_date DESC);
            CREATE TABLE IF NOT EXISTS opportunity_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                horizon TEXT NOT NULL,
                score REAL NOT NULL,
                confidence TEXT NOT NULL,
                source TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                risks_json TEXT NOT NULL,
                data_updated_at TEXT NOT NULL,
                calculated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_opportunity_code_time
                ON opportunity_history(code, calculated_at DESC);
            """
        )
        return connection

    async def save_events(self, events: list[MarketEvent]) -> None:
        if events:
            await asyncio.to_thread(self._save_events_sync, events)

    def _save_events_sync(self, events: list[MarketEvent]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO market_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    title=excluded.title,
                    industries_json=excluded.industries_json,
                    direction=excluded.direction,
                    impact_score=excluded.impact_score,
                    evidence_json=excluded.evidence_json,
                    fetched_at=excluded.fetched_at
                """,
                [
                    (
                        event.event_id,
                        event.event_type,
                        event.title,
                        event.published_date.isoformat(),
                        event.url,
                        event.source,
                        json.dumps(event.stock_codes, ensure_ascii=False),
                        json.dumps(event.industries, ensure_ascii=False),
                        event.direction,
                        event.impact_score,
                        json.dumps(event.evidence, ensure_ascii=False),
                        now,
                    )
                    for event in events
                ],
            )

    async def list_events(self, target_date: date | None = None, limit: int = 100) -> list[MarketEvent]:
        return await asyncio.to_thread(self._list_events_sync, target_date, limit)

    def _list_events_sync(self, target_date: date | None, limit: int) -> list[MarketEvent]:
        with self._connect() as connection:
            if target_date:
                rows = connection.execute(
                    "SELECT * FROM market_events WHERE published_date = ? ORDER BY impact_score DESC LIMIT ?",
                    (target_date.isoformat(), limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM market_events ORDER BY published_date DESC, impact_score DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [
            MarketEvent(
                event_id=row["event_id"],
                event_type=row["event_type"],
                title=row["title"],
                published_date=date.fromisoformat(row["published_date"]),
                url=row["url"],
                source=row["source"],
                stock_codes=json.loads(row["stock_codes_json"]),
                industries=json.loads(row["industries_json"]),
                direction=row["direction"],
                impact_score=row["impact_score"],
                evidence=json.loads(row["evidence_json"]),
            )
            for row in rows
        ]

    async def save_opportunities(self, opportunities: list[Opportunity]) -> None:
        if opportunities:
            await asyncio.to_thread(self._save_opportunities_sync, opportunities)

    def _save_opportunities_sync(self, opportunities: list[Opportunity]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO opportunity_history
                    (code, horizon, score, confidence, source, reasons_json, risks_json, data_updated_at, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.code,
                        item.horizon,
                        item.score,
                        item.confidence,
                        item.source,
                        json.dumps(item.reasons, ensure_ascii=False),
                        json.dumps(item.risks, ensure_ascii=False),
                        item.data_updated_at.isoformat(),
                        now,
                    )
                    for item in opportunities
                ],
            )
