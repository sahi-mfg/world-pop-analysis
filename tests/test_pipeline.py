import json
import math

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")  # the pipeline extra
from rasterio.transform import from_origin  # noqa: E402

from worldpop_analysis.pipeline import cli, run, sources, urban  # noqa: E402
from worldpop_analysis.pipeline.config import City  # noqa: E402

PIXEL = 1 / 1200  # 3 arc-seconds, like WorldPop's 100 m grid
CITY = City("testville", "Testville", -5.0, 6.5, 300_000, "test")


def test_aggregate_sums_blocks_and_drops_partial_edges():
    pop = np.ones((25, 31))
    out = urban.aggregate(pop, 10)
    assert out.shape == (2, 3)
    assert (out == 100).all()


def test_row_areas_match_spherical_box():
    areas = urban.row_areas_km2(top_lat=7.0, cell_deg=0.1, rows=10, cols=10)
    r = urban.EARTH_RADIUS_KM
    expected = r**2 * math.radians(1.0) * (math.sin(math.radians(7)) - math.sin(math.radians(6)))
    assert areas.sum() == pytest.approx(expected)


def test_urban_centre_thresholds_gap_fill_and_majority_rule():
    pop = np.zeros((30, 30))
    area = np.ones_like(pop)
    pop[2:12, 2:12] = 2000  # 200,000 people at 2,000/km2: an urban centre
    pop[6, 6] = 0  # a park: enclosed gap, filled
    pop[20:23, 20:23] = 2000  # 18,000 people: dense but too small
    pop[12, 3:11] = 0  # a row just outside the block...
    labels = urban.urban_centres(pop, area)
    assert labels.max() == 1
    centre = labels == 1
    assert centre[6, 6]  # gap filled
    assert not centre[21, 21]
    assert centre[2:12, 2:12].all()


def test_majority_rule_adds_notches():
    pop = np.zeros((20, 20))
    area = np.ones_like(pop)
    pop[5:15, 5:15] = 1000
    pop[5:15, 5:15][pop[5:15, 5:15] > 0] = 2000
    pop[5, 9] = 0  # notch on the edge: 5 of 8 neighbours are urban
    labels = urban.urban_centres(pop, area)
    assert labels[5, 9] == 1


def test_centre_at_snaps_to_nearest_within_distance():
    pop = np.zeros((40, 40))
    area = np.ones_like(pop)
    pop[10:20, 10:20] = 3000
    labels = urban.urban_centres(pop, area)
    inside = urban.centre_at(labels, pop, area, 15, 15, cell_km=1)
    near = urban.centre_at(labels, pop, area, 15, 25, cell_km=1)
    far = urban.centre_at(labels, pop, area, 35, 35, cell_km=1)
    assert inside.population == pytest.approx(300_000)
    assert near.population == inside.population
    assert far is None


def test_rings_split_a_uniform_grid_by_area():
    n = 801
    lats = 6.5 + (np.arange(n)[::-1] - n // 2) * PIXEL
    lons = -5.0 + (np.arange(n) - n // 2) * PIXEL
    pop = np.ones((n, n))
    rings = urban.ring_populations(pop, lons, lats, -5.0, 6.5, edges_km=(0, 5, 10))
    # Annulus 5-10 km has 3x the area of the 0-5 km disc.
    assert rings[1] / rings[0] == pytest.approx(3, rel=0.02)


def test_tif_links_from_directory_index():
    html = '<a href="?C=N;O=D">Name</a> <a href="civ_pop_2020_CN_100m_R2025A_v1.tif">x</a>'
    base = "https://data.worldpop.org/GIS/x/2020/CIV/v1/100m/constrained/"
    assert sources.tif_links(html, base) == [base + "civ_pop_2020_CN_100m_R2025A_v1.tif"]


def _write_raster(path, radius_km, per_pixel=30.0):
    """1x1 degree around Testville: a dense disc on a thin rural background, a no-data corner."""
    n = 1200
    lats = 7.0 - (np.arange(n) + 0.5) * PIXEL
    lons = -5.5 + (np.arange(n) + 0.5) * PIXEL
    dx = (lons[None, :] - CITY.lon) * 111.32 * math.cos(math.radians(CITY.lat))
    dy = (lats[:, None] - CITY.lat) * 110.574
    pop = np.where(np.hypot(dx, dy) < radius_km, per_pixel, 0.1).astype("float32")
    pop[:50, :50] = -99999
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=n,
        width=n,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(-5.5, 7.0, PIXEL, PIXEL),
        nodata=-99999,
    ) as dst:
        dst.write(pop, 1)
    return pop


def test_build_end_to_end(tmp_path):
    p2015 = tmp_path / "civ_pop_2015_CN_100m_R2025A_v1.tif"
    p2025 = tmp_path / "civ_pop_2025_CN_100m_R2025A_v1.tif"
    pop15 = _write_raster(p2015, radius_km=5)
    _write_raster(p2025, radius_km=6)
    rasters = cli.local_rasters(tmp_path)
    assert sorted(rasters) == [2015, 2025]

    doc, footprints = run.build(rasters, cities=(CITY,))
    national = doc["national"][0]
    assert national["population"] == round(float(pop15[pop15 > 0].sum(dtype=np.float64)))
    assert national["urban_centres"] == 1

    s15, s25 = doc["cities"][0]["series"]
    disc_people = float(pop15[pop15 == 30].sum(dtype=np.float64))
    # Edge cells only partly covered by the disc fall under 1,500/km2 and stay out.
    assert 0.85 * disc_people < s15["urban_centre_population"] <= disc_people * 1.01
    assert s25["urban_centre_area_km2"] > s15["urban_centre_area_km2"] * 1.3
    assert sum(s15["rings"]) > disc_people  # disc plus rural background out to 30 km
    assert s15["rings"][0] == pytest.approx(disc_people, rel=0.01)  # the disc is the 0-5 km ring
    assert [f["properties"]["year"] for f in footprints["features"]] == [2015, 2025]
    assert footprints["features"][0]["geometry"]["type"] in ("Polygon", "MultiPolygon")

    run.write(doc, footprints, tmp_path / "out")
    loaded = json.loads((tmp_path / "out" / "civ.json").read_text())
    assert loaded["meta"]["years"] == [2015, 2025]


def test_admin_matches_sum_people_inside_units(tmp_path):
    path = tmp_path / "civ_pop_2021.tif"
    pop = _write_raster(path, radius_km=5)
    unit = {
        "type": "Feature",
        "properties": {"shapeName": "Sous-préfecture de Testville", "shapeID": "X1"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-5.5, 6.0], [-4.5, 6.0], [-4.5, 7.0], [-5.5, 7.0], [-5.5, 6.0]]],
        },
    }
    # Same footprint, other spelling: found because it contains the city centre.
    variant = {**unit, "properties": {"shapeName": "Testvile", "shapeID": "X2"}}
    away = {
        "type": "Feature",
        "properties": {"shapeName": "Elsewhere", "shapeID": "X3"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-5.5, 6.0], [-5.4, 6.0], [-5.4, 6.1], [-5.5, 6.1], [-5.5, 6.0]]],
        },
    }
    rows = run.admin_matches(path, {4: {"features": [unit, variant, away]}}, (CITY,))
    assert [r["unit"] for r in rows] == ["Sous-préfecture de Testville", "Testvile"]
    assert all(r["contains_centre"] for r in rows)
    assert rows[0]["worldpop"] == pytest.approx(float(pop[pop > 0].sum(dtype=np.float64)), rel=1e-4)
