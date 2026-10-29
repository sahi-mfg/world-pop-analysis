import math

import pytest

from worldpop_analysis.geometry import BBox, dumps, polygon_feature_collection


def test_parse_roundtrip():
    assert BBox.parse(" -4.15, 5.2 ,-3.85,5.45") == BBox(-4.15, 5.2, -3.85, 5.45)


@pytest.mark.parametrize("text", ["1,2,3", "a,b,c,d", "10,0,5,1", "0,50,1,40", "0,0,200,1"])
def test_parse_rejects_bad_input(text):
    with pytest.raises(ValueError):
        BBox.parse(text)


def test_area_one_degree_at_equator():
    # 1°x1° at the equator is ~111.2 km x ~110.6 km.
    assert BBox(0, 0, 1, 1).area_km2() == pytest.approx(12_363, rel=1e-3)


def test_area_shrinks_with_latitude():
    equator = BBox(0, 0, 1, 1).area_km2()
    north = BBox(0, 60, 1, 61).area_km2()
    assert north == pytest.approx(equator * math.cos(math.radians(60.5)), rel=1e-2)


def test_geojson_shape():
    gj = BBox(0, 0, 1, 1).to_geojson()
    ring = gj["features"][0]["geometry"]["coordinates"][0]
    assert gj["type"] == "FeatureCollection"
    assert ring[0] == ring[-1] and len(ring) == 5
    assert " " not in dumps(gj)


def test_open_ring_rejected():
    with pytest.raises(ValueError):
        polygon_feature_collection([[0, 0], [1, 0], [1, 1], [0, 1]])
