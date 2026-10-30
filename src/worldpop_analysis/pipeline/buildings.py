"""Building counts from Google Open Buildings 2.5D Temporal (yearly, 2016-2023).

The dataset is published as Cloud-Optimized GeoTIFF tiles (12.5 km, UTM, 0.5 m storage of a
~4 m product) listed by Earth Engine manifests in a public bucket. Each tile is read over HTTP
at a reduced resolution with average resampling, so sums stay exact while only a small part
of each file is transferred. Band 1, ``building_fractional_count``, sums to a building count.

Neighbouring tiles overlap; inside an overlap each tile holds valid data only on part of it
(no-data elsewhere), and the values agree where both are valid. Tiles are therefore merged
like a mosaic: a point is counted by the first tile, in a fixed order, with valid data there.
"""

from __future__ import annotations

import itertools
import json
import logging
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform as warp_transform
from shapely import contains_xy
from shapely.geometry import shape

from worldpop_analysis.pipeline import config
from worldpop_analysis.pipeline.config import City

log = logging.getLogger(__name__)

BUCKET = "https://storage.googleapis.com/open-buildings-temporal-data/"
YEARS = range(2016, 2024)
DATASET = {
    "name": "Google Open Buildings 2.5D Temporal",
    "release": "v1",
    "url": "https://sites.research.google/gr/open-buildings/temporal/",
    "license": "CC BY 4.0 and ODbL v1.0",
}
# 0.5 m storage x 25 = 12.5 m cells: building sums match full resolution to ~0.2 %.
READ_FACTOR = 25


@dataclass(frozen=True, slots=True)
class Tile:
    url: str
    crs: str
    left: float
    top: float
    size_m: float

    def overlaps(self, other: Tile) -> bool:
        return (
            self.crs == other.crs
            and self.left < other.left + other.size_m
            and other.left < self.left + self.size_m
            and self.top > other.top - other.size_m
            and other.top > self.top - self.size_m
        )


@dataclass(frozen=True, slots=True)
class Grid:
    """One tile read at ``READ_FACTOR``: building counts and where the tile has valid data."""

    tile: Tile
    counts: np.ndarray  # float32, buildings per cell
    valid: np.ndarray  # bool
    cell: float

    def lookup(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Whether this grid has valid data at each point (False outside the tile)."""
        cols = np.floor((xs - self.tile.left) / self.cell).astype(np.int64)
        rows = np.floor((self.tile.top - ys) / self.cell).astype(np.int64)
        n_rows, n_cols = self.valid.shape
        inside = (rows >= 0) & (rows < n_rows) & (cols >= 0) & (cols < n_cols)
        out = np.zeros(xs.shape, dtype=bool)
        out[inside] = self.valid[rows[inside], cols[inside]]
        return out


def utm_epsg(lon: float, lat: float) -> int:
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def manifest_names(client: httpx.Client) -> list[str]:
    names, marker = [], ""
    while True:
        params = {"prefix": "v1/manifests/", "max-keys": "1000"}
        if marker:
            params["marker"] = marker
        text = client.get(BUCKET, params=params).raise_for_status().text
        keys = [k.split("<Key>")[1] for k in text.split("</Key>")[:-1]]
        names += [k for k in keys if k.endswith(".json")]
        if "<IsTruncated>true" not in text:
            return names
        marker = keys[-1]


def load_tiles(client: httpx.Client, cache: Path, name: str) -> list[Tile]:
    """Tiles of one manifest (one S2 cell, one UTM zone, one year), cached on disk."""
    path = cache / name.rsplit("/", 1)[-1]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(client.get(BUCKET + name).raise_for_status().content)
    manifest = json.loads(path.read_text())
    prefix = manifest["uriPrefix"].replace("gs://open-buildings-temporal-data/", BUCKET)
    tiles = []
    for tileset in manifest["tilesets"]:
        for src in tileset["sources"]:
            t = src["affineTransform"]
            tiles.append(
                Tile(
                    url=prefix + src["uris"][0],
                    crs=tileset["crs"],
                    left=t["translateX"],
                    top=t["translateY"],
                    size_m=t["scaleX"] * src["dimensions"]["width"],
                )
            )
    return tiles


def _disc_bounds_utm(city: City, epsg: int, radius_km: float) -> tuple[float, float, float, float]:
    dlat = radius_km / 110.574
    dlon = radius_km / (111.320 * math.cos(math.radians(city.lat)))
    lons = [city.lon - dlon, city.lon + dlon, city.lon - dlon, city.lon + dlon]
    lats = [city.lat - dlat, city.lat - dlat, city.lat + dlat, city.lat + dlat]
    xs, ys = warp_transform("EPSG:4326", f"EPSG:{epsg}", lons, lats)
    return min(xs), min(ys), max(xs), max(ys)


def tiles_near(city: City, tiles: list[Tile], radius_km: float) -> list[Tile]:
    """Tiles in the city's UTM zone that intersect the box around its outer ring."""
    epsg = utm_epsg(city.lon, city.lat)
    x0, y0, x1, y1 = _disc_bounds_utm(city, epsg, radius_km)
    return [
        t
        for t in tiles
        if t.crs == f"EPSG:{epsg}"
        and t.left < x1
        and t.left + t.size_m > x0
        and t.top > y0
        and t.top - t.size_m < y1
    ]


def read_grid(tile: Tile) -> Grid:
    with rasterio.open(tile.url) as src:
        n_rows, n_cols = src.height // READ_FACTOR, src.width // READ_FACTOR
        data = src.read(1, out_shape=(n_rows, n_cols), resampling=Resampling.average, masked=True)
        cell = src.transform.a * READ_FACTOR
    valid = ~np.ma.getmaskarray(data)
    counts = (data.filled(0) * READ_FACTOR**2).astype(np.float32)
    return Grid(tile=tile, counts=counts, valid=valid, cell=cell)


def mosaic_points(grids: list[Grid]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(x, y, buildings) of every cell with buildings, each location counted once."""
    order = sorted(grids, key=lambda g: g.tile.url)
    xs_all, ys_all, values_all = [np.empty(0)], [np.empty(0)], [np.empty(0)]
    for i, grid in enumerate(order):
        rows, cols = np.nonzero(grid.valid & (grid.counts > 0))
        xs = grid.tile.left + (cols + 0.5) * grid.cell
        ys = grid.tile.top - (rows + 0.5) * grid.cell
        keep = np.ones(xs.shape, dtype=bool)
        for earlier in order[:i]:
            if earlier.tile.overlaps(grid.tile):
                keep &= ~earlier.lookup(xs, ys)
        xs_all.append(xs[keep])
        ys_all.append(ys[keep])
        values_all.append(grid.counts[rows, cols][keep].astype(np.float64))
    return np.concatenate(xs_all), np.concatenate(ys_all), np.concatenate(values_all)


def measure_points(
    xs: np.ndarray,
    ys: np.ndarray,
    values: np.ndarray,
    crs: str,
    city: City,
    footprint,
    edges_km=config.RING_EDGES_KM,
) -> np.ndarray:
    """Buildings per distance ring, then inside ``footprint`` (last element)."""
    out = np.zeros(len(edges_km))
    if values.size == 0:
        return out
    lons, lats = warp_transform(crs, "EPSG:4326", xs, ys)
    lons, lats = np.asarray(lons), np.asarray(lats)
    dx = (lons - city.lon) * 111.320 * math.cos(math.radians(city.lat))
    dy = (lats - city.lat) * 110.574
    dist = np.hypot(dx, dy)
    for i, (lo, hi) in enumerate(itertools.pairwise(edges_km)):
        out[i] = values[(dist >= lo) & (dist < hi)].sum()
    if footprint is not None:
        out[-1] = values[contains_xy(footprint, lons, lats)].sum()
    return out


def build(
    cities: tuple[City, ...],
    footprints: dict,
    cache: Path,
    years=YEARS,
    workers: int = 16,
) -> dict[str, list[dict]]:
    """Per city and year: buildings per distance ring and inside the latest urban centre."""
    latest = {}
    for f in footprints["features"]:
        key, year = f["properties"]["city"], f["properties"]["year"]
        if key not in latest or year > latest[key][0]:
            latest[key] = (year, shape(f["geometry"]))
    radius = config.RING_EDGES_KM[-1] + 1
    results: dict[str, list[dict]] = {c.key: [] for c in cities}
    with (
        httpx.Client(timeout=120, follow_redirects=True) as client,
        ThreadPoolExecutor(workers) as pool,
    ):
        names = manifest_names(client)
        for year in years:
            suffix = f"_{year}_06_30.json"
            year_tiles = []
            for epsg in sorted({utm_epsg(c.lon, c.lat) for c in cities}):
                for name in names:
                    if name.endswith(f"EPSG_{epsg}{suffix}"):
                        year_tiles += load_tiles(client, cache / "manifests", name)
            for city in cities:
                near = tiles_near(city, year_tiles, radius)
                grids = list(pool.map(read_grid, near))
                xs, ys, values = mosaic_points(grids)
                crs = f"EPSG:{utm_epsg(city.lon, city.lat)}"
                footprint = latest.get(city.key, (0, None))[1]
                total = measure_points(xs, ys, values, crs, city, footprint)
                log.info(
                    "buildings %s %-13s %3d tiles, %9.0f within %s km",
                    year,
                    city.name,
                    len(near),
                    total[:-1].sum(),
                    config.RING_EDGES_KM[-1],
                )
                results[city.key].append(
                    {
                        "year": year,
                        "rings": [round(float(v)) for v in total[:-1]],
                        "urban_centre": round(float(total[-1])),
                    }
                )
    return results


def merge_into(doc: dict, buildings: dict[str, list[dict]], footprint_year: int | None) -> dict:
    doc["meta"]["buildings_dataset"] = {**DATASET, "years": list(YEARS)}
    doc["meta"]["method"]["buildings"] = (
        "Sum of building_fractional_count read at 12.5 m (average resampling), tiles merged "
        f"as a mosaic, per distance ring and inside the {footprint_year} urban-centre footprint"
    )
    for city in doc["cities"]:
        city["buildings"] = buildings.get(city["key"], [])
    return doc
