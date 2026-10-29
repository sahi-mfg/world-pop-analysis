"""Downloading inputs: WorldPop rasters and geoBoundaries administrative units."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import urljoin

import httpx

from worldpop_analysis.pipeline import config

log = logging.getLogger(__name__)

_TIF_LINK = re.compile(r'href="([^"?#]+\.tif)"', re.IGNORECASE)
_TIMEOUT = httpx.Timeout(60.0, read=300.0)


def tif_links(index_html: str, base_url: str) -> list[str]:
    """Absolute URLs of the .tif files listed in an Apache directory index."""
    return sorted({urljoin(base_url, href) for href in _TIF_LINK.findall(index_html)})


def raster_url(client: httpx.Client, year: int, iso3: str = config.ISO3) -> str:
    """The country raster for ``year``, found by listing its directory, not guessing its name."""
    base = config.RASTER_DIR_URL.format(year=year, iso3=iso3)
    response = client.get(base)
    response.raise_for_status()
    links = tif_links(response.text, base)
    if len(links) != 1:
        raise RuntimeError(f"expected exactly one .tif in {base}, found {links}")
    return links[0]


def download(client: httpx.Client, url: str, dest: Path) -> Path:
    """Stream ``url`` to ``dest``; skip when a complete copy is already cached."""
    if dest.exists():
        head = client.head(url)
        size = int(head.headers.get("content-length", -1))
        if head.is_success and size == dest.stat().st_size:
            log.info("cached %s", dest.name)
            return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with tmp.open("wb") as fh:
            for chunk in response.iter_bytes(1 << 20):
                fh.write(chunk)
    tmp.replace(dest)
    log.info("downloaded %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
    return dest


def fetch_rasters(cache_dir: Path, years=config.YEARS) -> dict[int, Path]:
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        paths = {}
        for year in years:
            url = raster_url(client, year)
            paths[year] = download(client, url, cache_dir / url.rsplit("/", 1)[-1])
        return paths


def fetch_admin_units(level: int, iso3: str = config.ISO3) -> dict:
    """geoBoundaries (gbOpen) units at ``level``, as a simplified GeoJSON FeatureCollection."""
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        meta = client.get(config.GEOBOUNDARIES_API.format(iso3=iso3, level=level))
        meta.raise_for_status()
        url = meta.json()["simplifiedGeometryGeoJSON"]
        response = client.get(url)
        response.raise_for_status()
        return response.json()
