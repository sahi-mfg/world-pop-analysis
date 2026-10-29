from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from worldpop_analysis import client

APP = str(Path(__file__).parents[1] / "streamlit_app.py")


@pytest.fixture(autouse=True)
def clear_cache():
    st.cache_data.clear()


def test_app_renders_metrics(monkeypatch):
    async def fake_series(self, geojson, years, dataset="wpgppop"):
        return {y: 1_000_000 * 1.04 ** (y - 2000) for y in years}

    monkeypatch.setattr(client.WorldPopClient, "population_series", fake_series)
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert [m.label for m in at.metric][:2] == ["Population 2020", "Change since 2000"]
    assert at.metric[2].value == "4.00%"


def test_app_shows_api_errors(monkeypatch):
    async def failing(self, geojson, years, dataset="wpgppop"):
        raise client.WorldPopError("service down")

    monkeypatch.setattr(client.WorldPopClient, "population_series", failing)
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "service down" in at.error[0].value
