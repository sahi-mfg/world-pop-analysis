"""Turn yearly country rasters into the JSON the website reads."""

from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import rasterio.mask
from affine import Affine
from rasterio import features
from shapely import set_precision, unary_union
from shapely.geometry import Point, mapping, shape

from worldpop_analysis.pipeline import config, urban
from worldpop_analysis.pipeline.config import City

log = logging.getLogger(__name__)


def _read_population(src: rasterio.DatasetReader) -> np.ndarray:
    """Band 1 as float64 people per pixel, with no-data and negative fill values as 0."""
    if src.crs is None or not src.crs.is_geographic or src.transform.b or src.transform.d:
        raise ValueError(f"{src.name}: expected a north-up lon/lat raster")
    pop = src.read(1, masked=True).astype(np.float64).filled(0.0)
    pop[~np.isfinite(pop) | (pop < 0)] = 0.0
    return pop


def _footprint(mask: np.ndarray, transform: Affine, tolerance: float) -> dict[str, Any]:
    polygons = [
        shape(geom)
        for geom, value in features.shapes(mask.astype(np.uint8), mask=mask, transform=transform)
        if value
    ]
    merged = unary_union(polygons).simplify(tolerance, preserve_topology=True)
    return mapping(set_precision(merged, 1e-4))


def measure_year(path: Path, cities: tuple[City, ...]) -> dict[str, Any]:
    """National totals, urban centres and per-city measures for one year's raster."""
    with rasterio.open(path) as src:
        pop = _read_population(src)
        t = src.transform
    pixel = t.a
    cell = pixel * config.AGGREGATION
    pop_1km = urban.aggregate(pop)
    areas = urban.row_areas_km2(t.f, cell, *pop_1km.shape)
    labels = urban.urban_centres(pop_1km, areas)
    agg_transform = Affine(cell, 0, t.c, 0, -cell, t.f)
    cell_km = cell * 111.32

    n_centres = int(labels.max())
    centre_pop = float(pop_1km[labels > 0].sum())
    result: dict[str, Any] = {
        "national": {
            "population": float(pop.sum()),
            "urban_centres": n_centres,
            "urban_centre_population": centre_pop,
        },
        "cities": {},
    }

    reach_km = config.RING_EDGES_KM[-1] + 1
    for city in cities:
        row = math.floor((t.f - city.lat) / cell)
        col = math.floor((city.lon - t.c) / cell)
        centre = urban.centre_at(labels, pop_1km, areas, row, col, cell_km)

        # Rings on the 100 m grid, in a window just large enough for the outer ring.
        dlat = reach_km / 110.574
        dlon = reach_km / (111.320 * math.cos(math.radians(city.lat)))
        r0 = max(0, math.floor((t.f - city.lat - dlat) / pixel))
        r1 = min(pop.shape[0], math.ceil((t.f - city.lat + dlat) / pixel))
        c0 = max(0, math.floor((city.lon - dlon - t.c) / pixel))
        c1 = min(pop.shape[1], math.ceil((city.lon + dlon - t.c) / pixel))
        lats = t.f - (np.arange(r0, r1) + 0.5) * pixel
        lons = t.c + (np.arange(c0, c1) + 0.5) * pixel
        rings = urban.ring_populations(pop[r0:r1, c0:c1], lons, lats, city.lon, city.lat)

        result["cities"][city.key] = {
            "urban_centre_population": centre.population if centre else None,
            "urban_centre_area_km2": centre.area_km2 if centre else None,
            "rings": rings,
            "footprint": _footprint(centre.mask, agg_transform, cell / 4) if centre else None,
        }
    return result


def _normalise(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]+", " ", ascii_name.lower()).strip()


def admin_matches(
    path: Path, units_by_level: dict[int, dict], cities: tuple[City, ...]
) -> list[dict]:
    """WorldPop population of the administrative units each city's census figure may refer to.

    A unit qualifies when it contains the city's centre point or carries the city's name
    (names alone miss spelling variants such as "Bouake" against "Bouaké"). This is a
    diagnostic: it shows which unit the census figure most plausibly describes.
    """
    rows = []
    with rasterio.open(path) as src:
        for level, units in sorted(units_by_level.items()):
            for feature in units["features"]:
                unit_name = feature["properties"].get("shapeName", "")
                geometry = shape(feature["geometry"])
                for city in cities:
                    by_name = _normalise(city.name) in _normalise(unit_name)
                    by_point = geometry.contains(Point(city.lon, city.lat))
                    if not (by_name or by_point):
                        continue
                    data, _ = rasterio.mask.mask(
                        src, [feature["geometry"]], crop=True, filled=True, nodata=0
                    )
                    values = data[0].astype(np.float64)
                    values[~np.isfinite(values) | (values < 0)] = 0
                    rows.append(
                        {
                            "city": city.key,
                            "level": f"ADM{level}",
                            "unit": unit_name,
                            "unit_id": feature["properties"].get("shapeID"),
                            "contains_centre": bool(by_point),
                            "worldpop": round(float(values.sum())),
                            "census_2021": city.census_2021,
                        }
                    )
    return sorted(rows, key=lambda r: (r["city"], r["level"]))


def _round(value: float | None, digits: int = 0) -> float | int | None:
    if value is None:
        return None
    return round(value) if digits == 0 else round(value, digits)


def build(
    rasters: dict[int, Path],
    cities: tuple[City, ...] = config.CITIES,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The site's data document and the footprints FeatureCollection."""
    years = sorted(rasters)
    per_year = {}
    for year in years:
        log.info("measuring %s", year)
        per_year[year] = measure_year(rasters[year], cities)

    national = [
        {
            "year": y,
            "population": _round(per_year[y]["national"]["population"]),
            "urban_centres": per_year[y]["national"]["urban_centres"],
            "urban_centre_population": _round(per_year[y]["national"]["urban_centre_population"]),
        }
        for y in years
    ]
    city_docs = []
    footprints = []
    for city in cities:
        series = []
        for y in years:
            m = per_year[y]["cities"][city.key]
            series.append(
                {
                    "year": y,
                    "urban_centre_population": _round(m["urban_centre_population"]),
                    "urban_centre_area_km2": _round(m["urban_centre_area_km2"], 1),
                    "rings": [_round(v) for v in m["rings"]],
                }
            )
            if m["footprint"]:
                footprints.append(
                    {
                        "type": "Feature",
                        "properties": {"city": city.key, "year": y},
                        "geometry": m["footprint"],
                    }
                )
            if m["urban_centre_population"] is not None:
                assert m["urban_centre_population"] <= per_year[y]["national"]["population"] + 1
        city_docs.append(
            {
                "key": city.key,
                "name": city.name,
                "center": [city.lon, city.lat],
                "census_2021": {
                    "population": city.census_2021,
                    "source": city.census_source,
                    "approximate": city.census_approx,
                },
                "series": series,
            }
        )

    doc = {
        "meta": {
            "country": config.ISO3,
            "dataset": config.DATASET,
            "years": years,
            "last_census_year": config.LAST_CENSUS_YEAR,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "method": {
                "urban_centre": (
                    "Degree of Urbanisation stage 1: contiguous (4-connected) ~1 km cells with "
                    f">= {config.URBAN_DENSITY:g} people/km2 and "
                    f">= {config.URBAN_MIN_POPULATION:g} people, gaps <= "
                    f"{config.MAX_GAP_CELLS} cells filled, majority rule smoothing"
                ),
                "ring_edges_km": list(config.RING_EDGES_KM),
            },
        },
        "national": national,
        "cities": city_docs,
    }
    return doc, {"type": "FeatureCollection", "features": footprints}


def write(doc: dict, footprints: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "civ.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    (out_dir / "footprints.geojson").write_text(
        json.dumps(footprints, separators=(",", ":")) + "\n"
    )
