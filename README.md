# 🌍 world-pop-analysis

[![CI](https://github.com/sahi-mfg/world-pop-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/sahi-mfg/world-pop-analysis/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230)

**How fast are the world's cities growing?** This project answers that for any area on Earth
by querying [WorldPop](https://www.worldpop.org/) — 100 m resolution gridded population
estimates for 2000–2020 — and turning the result into growth metrics, served by a FastAPI
backend to a React + MapLibre web app (and a CLI).

## Features

- **Async API client** (`httpx` + `asyncio`) for the WorldPop zonal-statistics service:
  concurrent per-year requests with a bounded semaphore, transparent polling of
  server-side tasks, exponential-backoff retries on 429/5xx, typed errors.
- **Geometry helpers**: bounding boxes → GeoJSON, exact spherical area for densities.
- **Analytics** with pandas: annualised growth (robust to uneven sampling), CAGR,
  doubling time, density, base-100 index.
- **FastAPI backend** exposing `/api/regions` and `/api/series`, with response caching and
  clean 422/502 errors; it also serves the built frontend, so the app ships as one process.
- **Web app** (React 19, TypeScript, Vite, Tailwind CSS 4, MapLibre GL, Recharts, TanStack
  Query): pick a featured city or drag a rectangle on the map, explore KPIs, charts and the
  data table, download the CSV.
- **CLI** for scripting and reproducible exports.
- **Tested offline**: HTTP is mocked with `httpx.MockTransport`, the API is exercised with
  FastAPI's `TestClient`, frontend helpers with Vitest. CI lints, tests and builds both sides.
- **One-command deploy** with a multi-stage `Dockerfile`.

## Quick start

Requires [uv](https://docs.astral.sh/uv/) and Node.js 22+.

```bash
git clone https://github.com/sahi-mfg/world-pop-analysis.git
cd world-pop-analysis
uv sync
npm --prefix web install
```

Web app (two terminals, Vite proxies `/api` to the backend):

```bash
uv run worldpop-api
```

```bash
npm --prefix web run dev
```

Then open http://localhost:5173.

Or everything in one container, on http://localhost:8000:

```bash
docker build -t worldpop-explorer . && docker run --rm -p 8000:8000 worldpop-explorer
```

If WorldPop requires an API key for your usage, set `WORLDPOP_API_KEY`; it is sent as the
`key` query parameter.

CLI:

```bash
uv run worldpop regions
uv run worldpop series --region abidjan --start 2000 --end 2020 --step 5 --out abidjan.csv
uv run worldpop series --bbox "3.10,6.38,3.70,6.70" --step 1
uv run worldpop datasets CIV
```

Library:

```python
import asyncio
from worldpop_analysis import REGIONS, WorldPopClient, growth_table, summarize

async def main():
    bbox = REGIONS["lagos"].bbox
    async with WorldPopClient() as wp:
        series = await wp.population_series(bbox.to_geojson(), range(2000, 2021, 5))
    print(growth_table(series, area_km2=bbox.area_km2()))
    print(summarize(series))

asyncio.run(main())
```

## How it works

```
 bbox / preset region ──► GeoJSON ──► GET /v1/services/stats?dataset=wpgppop&year=…
                                          │
                       finished inline ◄──┴──► taskid ──► poll /v1/tasks/{id}
                                          │
                        {year: population} (one request per year, run concurrently)
                                          │
                         pandas growth table ──► FastAPI ──► React app · CLI · CSV
```

| Module | Responsibility |
| --- | --- |
| `geometry.py` | `BBox` validation, GeoJSON serialisation, spherical area |
| `client.py` | `WorldPopClient`: retries, task polling, concurrency limit, dataset catalogue |
| `analysis.py` | `growth_table`, `cagr`, `doubling_time`, `summarize` |
| `regions.py` | Preset areas (Abidjan, Lagos, Kinshasa, Nairobi, Dakar, Dhaka, Paris, Tyrol) |
| `api.py` | FastAPI app (`worldpop-api`), caching, static frontend |
| `cli.py` | `worldpop` command |
| `web/` | React frontend: map with rectangle drawing, KPIs, charts, table |

## Development

```bash
uv run pytest --cov=worldpop_analysis
uv run ruff check . && uv run ruff format .
npm --prefix web test && npm --prefix web run build
```

## Data & limitations

- Dataset: WorldPop *Global 100 m unconstrained population counts* (`wpgppop`), 2000–2020.
  Values are modelled estimates, not census counts; see the
  [WorldPop methods](https://www.worldpop.org/methods/populations/).
- Preset regions are rectangular approximations of metropolitan areas, not administrative
  boundaries.
- The public stats API limits the size of the query polygon; keep areas below a few tens of
  thousands of km².

Basemap © [CARTO](https://carto.com/attributions) · © OpenStreetMap contributors.
Data © WorldPop (www.worldpop.org), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
