import pytest
from fastapi.testclient import TestClient

from worldpop_analysis import api
from worldpop_analysis.client import WorldPopError


class FakeClient:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = 0

    async def population_series(self, geojson, years, dataset="wpgppop"):
        self.calls += 1
        if self.fail:
            raise WorldPopError("upstream exploded")
        return {y: 1000.0 * 1.04 ** (y - 2000) for y in years}


@pytest.fixture
def fake():
    return FakeClient()


@pytest.fixture
def http(fake):
    api.app.dependency_overrides[api.get_client] = lambda: fake
    with TestClient(api.app) as client:
        yield client
    api.app.dependency_overrides.clear()


def test_regions(http):
    body = http.get("/api/regions").json()
    lagos = next(r for r in body if r["key"] == "lagos")
    assert lagos["bbox"] == [3.10, 6.38, 3.70, 6.70]
    assert lagos["area_km2"] > 0


def test_series(http):
    res = http.get("/api/series", params={"bbox": "0,0,1,1", "step": 10})
    assert res.status_code == 200
    body = res.json()
    assert [r["year"] for r in body["rows"]] == [2000, 2010, 2020]
    assert body["rows"][0]["annual_growth_pct"] is None
    assert body["summary"]["cagr"] == pytest.approx(0.04)
    assert body["rows"][0]["density_per_km2"] == pytest.approx(1000 / body["area_km2"])


def test_series_is_cached(http, fake):
    for _ in range(2):
        http.get("/api/series", params={"bbox": "0,0,1,1"})
    assert fake.calls == 1


@pytest.mark.parametrize(
    "params", [{"bbox": "nope"}, {"bbox": "0,0,1,1", "start": 1990}, {"bbox": "0,0,1,1", "step": 0}]
)
def test_series_validation(http, params):
    assert http.get("/api/series", params=params).status_code == 422


def test_upstream_errors_become_502(http, fake):
    fake.fail = True
    res = http.get("/api/series", params={"bbox": "0,0,2,2"})
    assert res.status_code == 502
    assert "upstream exploded" in res.json()["detail"]
