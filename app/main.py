from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.backtest.prices import BaoStockHistoricalPriceProvider
from app.backtest.service import BacktestService
from app.config import settings
from app.events.service import EventService
from app.models import BacktestResult, MarketEvent, Opportunity
from app.providers import create_provider
from app.services.scoring import score_snapshot
from app.storage import ResearchStorage

app = FastAPI(title="A股事件机会雷达", version="0.1.0")
provider = create_provider()
storage = ResearchStorage(settings.database_path)
event_service = EventService(settings.watchlist_codes, storage)
backtest_service = BacktestService(storage, BaoStockHistoricalPriceProvider())
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env, "provider": settings.data_provider}


@app.get("/api/opportunities", response_model=list[Opportunity])
async def opportunities(
    horizon: Literal["short", "medium"] = Query(default="short"),
) -> list[Opportunity]:
    snapshots = await provider.list_snapshots()
    results = sorted(
        (score_snapshot(item, horizon) for item in snapshots),
        key=lambda item: item.score,
        reverse=True,
    )
    await storage.save_opportunities(results)
    return results


@app.get("/api/stocks/{code}/opportunity", response_model=Opportunity)
async def stock_opportunity(
    code: str,
    horizon: Literal["short", "medium"] = Query(default="short"),
) -> Opportunity:
    snapshot = await provider.get_snapshot(code)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="未找到该股票")
    result = score_snapshot(snapshot, horizon)
    await storage.save_opportunities([result])
    return result


@app.get("/api/events", response_model=list[MarketEvent])
async def events(target_date: date | None = Query(default=None)) -> list[MarketEvent]:
    return await event_service.list_events(target_date)


@app.get("/api/backtest", response_model=list[BacktestResult])
async def backtest(
    horizon: Literal["short", "medium"] = Query(default="short"),
) -> list[BacktestResult]:
    return await backtest_service.evaluate(horizon)
