import asyncio
import json

import httpx
import pytest

from worldpop_analysis.client import WorldPopClient, WorldPopError
from worldpop_analysis.geometry import BBox

GEOJSON = BBox(0, 0, 1, 1).to_geojson()


def run(coro):
    return asyncio.run(coro)


def make_client(handler, **kwargs):
    kwargs.setdefault("poll_interval", 0)
    return WorldPopClient(transport=httpx.MockTransport(handler), **kwargs)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    real_sleep = asyncio.sleep
    monkeypatch.setattr(asyncio, "sleep", lambda _s: real_sleep(0))


def finished(pop):
    return {"status": "finished", "error": False, "data": {"total_population": pop}}


def test_inline_result_and_query_params():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=finished(1234.5))

    async def go():
        async with make_client(handler) as wp:
            return await wp.total_population(GEOJSON, 2015)

    assert run(go()) == 1234.5
    params = seen[0].url.params
    assert seen[0].url.path == "/v1/services/stats"
    assert params["dataset"] == "wpgppop" and params["year"] == "2015"
    assert json.loads(params["geojson"]) == GEOJSON


def test_polls_task_until_finished():
    polls = iter([{"status": "started", "taskid": "abc"}, finished(42)])

    def handler(request):
        if request.url.path.endswith("/services/stats"):
            return httpx.Response(200, json={"status": "created", "taskid": "abc"})
        assert request.url.path == "/v1/tasks/abc"
        return httpx.Response(200, json=next(polls))

    async def go():
        async with make_client(handler) as wp:
            return await wp.total_population(GEOJSON, 2020)

    assert run(go()) == 42


def test_api_error_surfaces():
    def handler(request):
        return httpx.Response(
            200, json={"status": "finished", "error": True, "error_message": "too big"}
        )

    async def go():
        async with make_client(handler) as wp:
            await wp.total_population(GEOJSON, 2020)

    with pytest.raises(WorldPopError, match="too big"):
        run(go())


def test_retries_transient_errors():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=finished(1))

    async def go():
        async with make_client(handler, max_retries=3) as wp:
            return await wp.total_population(GEOJSON, 2020)

    assert run(go()) == 1 and calls["n"] == 3


def test_gives_up_after_max_retries():
    async def go():
        async with make_client(lambda r: httpx.Response(502), max_retries=1) as wp:
            await wp.total_population(GEOJSON, 2020)

    with pytest.raises(WorldPopError, match="HTTP 502"):
        run(go())


def test_client_errors_are_not_retried():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(400)

    async def go():
        async with make_client(handler) as wp:
            await wp.total_population(GEOJSON, 2020)

    with pytest.raises(WorldPopError, match="HTTP 400"):
        run(go())
    assert calls["n"] == 1


def test_non_json_body_is_reported():
    def handler(request):
        return httpx.Response(
            200, text="<html>Maintenance</html>", headers={"content-type": "text/html"}
        )

    async def go():
        async with make_client(handler) as wp:
            await wp.total_population(GEOJSON, 2020)

    with pytest.raises(WorldPopError, match=r"non-JSON content \(text/html.*Maintenance"):
        run(go())


def test_api_key_is_sent(monkeypatch):
    monkeypatch.setenv("WORLDPOP_API_KEY", "secret")

    def handler(request):
        assert request.url.params["key"] == "secret"
        return httpx.Response(200, json=finished(1))

    async def go():
        async with make_client(handler) as wp:
            return await wp.total_population(GEOJSON, 2020)

    assert run(go()) == 1


def test_year_out_of_range():
    async def go():
        async with make_client(lambda r: httpx.Response(200)) as wp:
            await wp.total_population(GEOJSON, 1999)

    with pytest.raises(ValueError):
        run(go())


def test_population_series_is_sorted_and_deduplicated():
    def handler(request):
        return httpx.Response(200, json=finished(int(request.url.params["year"]) - 2000))

    async def go():
        async with make_client(handler) as wp:
            return await wp.population_series(GEOJSON, [2010, 2000, 2005, 2010])

    assert run(go()) == {2000: 0, 2005: 5, 2010: 10}


def test_country_datasets():
    def handler(request):
        assert request.url.path == "/rest/data/pop/wpgp"
        assert request.url.params["iso3"] == "CIV"
        return httpx.Response(200, json={"data": [{"popyear": "2020", "title": "x"}]})

    async def go():
        async with make_client(handler) as wp:
            return await wp.country_datasets("civ")

    assert run(go()) == [{"popyear": "2020", "title": "x"}]
