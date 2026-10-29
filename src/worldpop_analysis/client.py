"""Async client for the WorldPop REST and zonal-statistics APIs.

API docs: https://www.worldpop.org/sdi/introapi/

The stats endpoint runs zonal statistics server-side: it either answers inline or
returns a ``taskid`` that has to be polled at ``/v1/tasks/{taskid}``. Both paths are
handled transparently by :meth:`WorldPopClient.total_population`.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Any, Self

import httpx

from worldpop_analysis.geometry import dumps

log = logging.getLogger(__name__)

STATS_API = "https://api.worldpop.org/v1"
CATALOG_API = "https://www.worldpop.org/rest/data"

# Global unconstrained 100 m population counts, available yearly 2000-2020.
DEFAULT_DATASET = "wpgppop"
AVAILABLE_YEARS = range(2000, 2021)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class WorldPopError(RuntimeError):
    """The API answered, but not with usable data."""


class WorldPopClient:
    """Thin async wrapper around the WorldPop APIs.

    Use as an async context manager::

        async with WorldPopClient() as wp:
            pop = await wp.total_population(bbox.to_geojson(), 2020)
    """

    def __init__(
        self,
        *,
        timeout: float = 60.0,
        max_retries: int = 3,
        poll_interval: float = 2.0,
        poll_timeout: float = 300.0,
        concurrency: int = 4,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._http = httpx.AsyncClient(
            timeout=timeout,
            transport=transport,
            headers={
                "User-Agent": "world-pop-analysis (+https://github.com/sahi-mfg/world-pop-analysis)"
            },
            follow_redirects=True,
        )
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout
        self._semaphore = asyncio.Semaphore(concurrency)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET with exponential backoff on transient failures."""
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http.get(url, params=params)
            except httpx.TransportError as exc:
                if attempt == self.max_retries:
                    raise WorldPopError(f"network error calling {url}: {exc}") from exc
            else:
                if response.status_code not in _RETRYABLE_STATUS:
                    response.raise_for_status()
                    return response.json()
                if attempt == self.max_retries:
                    raise WorldPopError(f"{url} kept failing with HTTP {response.status_code}")
            delay = 2**attempt * 0.5
            log.warning("retrying %s in %.1fs (attempt %d)", url, delay, attempt + 1)
            await asyncio.sleep(delay)
        raise AssertionError("unreachable")

    async def total_population(
        self, geojson: dict[str, Any], year: int, dataset: str = DEFAULT_DATASET
    ) -> float:
        """Estimated number of people living inside ``geojson`` in ``year``."""
        if dataset == DEFAULT_DATASET and year not in AVAILABLE_YEARS:
            raise ValueError(f"{dataset} covers {AVAILABLE_YEARS.start}-{AVAILABLE_YEARS.stop - 1}")
        params = {"dataset": dataset, "year": year, "geojson": dumps(geojson), "runasync": "false"}
        async with self._semaphore:
            payload = await self._get_json(f"{STATS_API}/services/stats", params)
            payload = await self._wait_for_task(payload)
        return _extract_population(payload)

    async def _wait_for_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.poll_timeout
        while payload.get("status") != "finished" and not payload.get("error"):
            task_id = payload.get("taskid") or payload.get("task_id")
            if not task_id:
                raise WorldPopError(f"unexpected response: {payload}")
            if loop.time() > deadline:
                raise WorldPopError(f"task {task_id} did not finish in {self.poll_timeout}s")
            await asyncio.sleep(self.poll_interval)
            payload = await self._get_json(f"{STATS_API}/tasks/{task_id}")
        return payload

    async def population_series(
        self,
        geojson: dict[str, Any],
        years: Iterable[int],
        dataset: str = DEFAULT_DATASET,
    ) -> dict[int, float]:
        """Population for every year, fetched concurrently (bounded by ``concurrency``)."""
        years = sorted(set(years))
        values = await asyncio.gather(*(self.total_population(geojson, y, dataset) for y in years))
        return dict(zip(years, values, strict=True))

    async def country_datasets(
        self, iso3: str, alias: str = "pop", level: str = "wpgp"
    ) -> list[dict]:
        """Raster datasets published for a country (titles, years and download links)."""
        payload = await self._get_json(f"{CATALOG_API}/{alias}/{level}", {"iso3": iso3.upper()})
        return payload.get("data", [])


def _extract_population(payload: dict[str, Any]) -> float:
    if payload.get("error"):
        raise WorldPopError(payload.get("error_message") or "WorldPop returned an error")
    try:
        return float(payload["data"]["total_population"])
    except (KeyError, TypeError, ValueError) as exc:
        raise WorldPopError(f"no total_population in response: {payload}") from exc
