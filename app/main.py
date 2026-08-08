from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models import Opportunity
from app.providers import create_provider
from app.services.scoring import score_snapshot

app = FastAPI(title="A股事件机会雷达", version="0.1.0")
provider = create_provider()
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
    return sorted(
        (score_snapshot(item, horizon) for item in snapshots),
        key=lambda item: item.score,
        reverse=True,
    )


@app.get("/api/stocks/{code}/opportunity", response_model=Opportunity)
async def stock_opportunity(
    code: str,
    horizon: Literal["short", "medium"] = Query(default="short"),
) -> Opportunity:
    snapshot = await provider.get_snapshot(code)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="未找到该股票")
    return score_snapshot(snapshot, horizon)
