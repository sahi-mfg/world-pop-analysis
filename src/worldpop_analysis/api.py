"""HTTP API consumed by the web frontend: ``uv run worldpop-api``.

When ``web/dist`` exists (``npm run build``), the built frontend is served from ``/`` so the
whole app ships as a single process.
"""

from __future__ import annotations

import math
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from worldpop_analysis.analysis import growth_table, summarize
from worldpop_analysis.client import WorldPopClient, WorldPopError, sample_years
from worldpop_analysis.geometry import BBox
from worldpop_analysis.regions import REGIONS

WEB_DIST = Path(os.environ.get("WORLDPOP_WEB_DIST", Path(__file__).parents[2] / "web" / "dist"))
CACHE_TTL_SECONDS = 24 * 3600


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with WorldPopClient() as client:
        app.state.client = client
        app.state.cache = {}
        yield


app = FastAPI(title="WorldPop Explorer API", version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("WORLDPOP_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET"],
)


def get_client(request: Request) -> WorldPopClient:
    return request.app.state.client


def _clean(value: Any) -> Any:
    """JSON has no NaN: first-year growth becomes ``null``."""
    return None if isinstance(value, float) and math.isnan(value) else value


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/regions")
def regions() -> list[dict[str, Any]]:
    return [
        {
            "key": r.key,
            "name": r.name,
            "country": r.country,
            "bbox": [r.bbox.min_lon, r.bbox.min_lat, r.bbox.max_lon, r.bbox.max_lat],
            "area_km2": r.bbox.area_km2(),
        }
        for r in REGIONS.values()
    ]


@app.get("/api/series")
async def series(
    request: Request,
    client: Annotated[WorldPopClient, Depends(get_client)],
    bbox: Annotated[str, Query(description="min_lon,min_lat,max_lon,max_lat")],
    start: int = 2000,
    end: int = 2020,
    step: Annotated[int, Query(ge=1, le=20)] = 5,
) -> dict[str, Any]:
    try:
        box = BBox.parse(bbox)
        years = tuple(sample_years(start, end, step))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    cache: dict[tuple, tuple[float, dict[int, float]]] = request.app.state.cache
    key = (box, years)
    hit = cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL_SECONDS:
        data = hit[1]
    else:
        try:
            data = await client.population_series(box.to_geojson(), years)
        except WorldPopError as exc:
            raise HTTPException(502, str(exc)) from exc
        cache[key] = (time.monotonic(), data)

    area = box.area_km2()
    table = growth_table(data, area_km2=area)
    s = summarize(data)
    return {
        "bbox": [box.min_lon, box.min_lat, box.max_lon, box.max_lat],
        "area_km2": area,
        "rows": [{k: _clean(v) for k, v in row.items()} for row in table.to_dict("records")],
        "summary": {
            "start_year": s.start_year,
            "end_year": s.end_year,
            "start_population": s.start_population,
            "end_population": s.end_population,
            "total_change_pct": s.total_change_pct,
            "cagr": s.cagr,
            "doubling_years": None if math.isinf(s.doubling_years) else s.doubling_years,
            "peak_growth_year": s.peak_growth_year,
        },
    }


if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")


def main() -> None:
    import uvicorn

    uvicorn.run(
        "worldpop_analysis.api:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
