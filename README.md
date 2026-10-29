# 🌍 world-pop-analysis

[![CI](https://github.com/sahi-mfg/world-pop-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/sahi-mfg/world-pop-analysis/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230)

**How fast are the world's cities growing?** This project answers that for any area on Earth
by querying [WorldPop](https://www.worldpop.org/) — 100 m resolution gridded population
estimates for 2000–2020 — and turning the result into growth metrics, a CLI and an
interactive Streamlit dashboard.

## Features

- **Async API client** (`httpx` + `asyncio`) for the WorldPop zonal-statistics service:
  concurrent per-year requests with a bounded semaphore, transparent polling of
  server-side tasks, exponential-backoff retries on 429/5xx, typed errors.
- **Geometry helpers**: bounding boxes → GeoJSON, exact spherical area for densities.
- **Analytics** with pandas: annualised growth (robust to uneven sampling), CAGR,
  doubling time, density, base-100 index.
- **Streamlit dashboard**: pick a preset city or draw your own bounding box, see it on a
  map, explore KPIs and charts, download the CSV.
- **CLI** for scripting and reproducible exports.
- **Tested offline**: HTTP is mocked with `httpx.MockTransport`, the dashboard is
  exercised with Streamlit's `AppTest`; CI runs lint, format and tests on Python 3.12/3.13.

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/sahi-mfg/world-pop-analysis.git
cd world-pop-analysis
uv sync
```

Dashboard:

```bash
uv run streamlit run streamlit_app.py
```

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
                         pandas growth table ──► CLI · Streamlit · CSV
```

| Module | Responsibility |
| --- | --- |
| `geometry.py` | `BBox` validation, GeoJSON serialisation, spherical area |
| `client.py` | `WorldPopClient`: retries, task polling, concurrency limit, dataset catalogue |
| `analysis.py` | `growth_table`, `cagr`, `doubling_time`, `summarize` |
| `regions.py` | Preset areas (Abidjan, Lagos, Kinshasa, Nairobi, Dakar, Dhaka, Paris, Tyrol) |
| `cli.py` | `worldpop` command |
| `streamlit_app.py` | Dashboard |

## Development

```bash
uv run pytest --cov=worldpop_analysis
uv run ruff check . && uv run ruff format .
```

## Data & limitations

- Dataset: WorldPop *Global 100 m unconstrained population counts* (`wpgppop`), 2000–2020.
  Values are modelled estimates, not census counts; see the
  [WorldPop methods](https://www.worldpop.org/methods/populations/).
- Preset regions are rectangular approximations of metropolitan areas, not administrative
  boundaries.
- The public stats API limits the size of the query polygon; keep areas below a few tens of
  thousands of km².

Data © WorldPop (www.worldpop.org), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
