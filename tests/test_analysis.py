import math

import pytest

from worldpop_analysis.analysis import cagr, doubling_time, growth_table, summarize

SERIES = {2000: 100.0, 2005: 121.0, 2010: 133.1}


def test_growth_table_annualises_gaps():
    table = growth_table({2000: 100.0, 2002: 121.0})
    assert table["annual_growth_pct"].iloc[1] == pytest.approx(10.0)


def test_growth_table_columns_and_density():
    table = growth_table({2010: 50.0, 2000: 40.0}, area_km2=10)
    assert table["year"].tolist() == [2000, 2010]
    assert table["change"].iloc[1] == 10
    assert table["index_100"].iloc[1] == pytest.approx(125)
    assert table["density_per_km2"].tolist() == [4.0, 5.0]


def test_growth_table_empty():
    with pytest.raises(ValueError):
        growth_table({})


def test_cagr_and_doubling():
    assert cagr(100, 200, 10) == pytest.approx(2**0.1 - 1)
    assert doubling_time(cagr(100, 200, 10)) == pytest.approx(10)
    assert doubling_time(0) == math.inf
    with pytest.raises(ValueError):
        cagr(0, 10, 1)


def test_summarize():
    s = summarize(SERIES)
    assert (s.start_year, s.end_year) == (2000, 2010)
    assert s.total_change_pct == pytest.approx(33.1)
    assert s.peak_growth_year == 2005


def test_summarize_single_point():
    s = summarize({2020: 5.0})
    assert s.cagr == 0 and s.peak_growth_year is None
