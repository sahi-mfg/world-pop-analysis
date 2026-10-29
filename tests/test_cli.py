import pytest

from worldpop_analysis import cli
from worldpop_analysis.regions import REGIONS


def test_sample_years_includes_end():
    assert cli.sample_years(2000, 2012, 5) == [2000, 2005, 2010, 2012]
    assert cli.sample_years(2020, 2020, 5) == [2020]


@pytest.mark.parametrize("args", [(1990, 2000, 1), (2010, 2000, 1), (2000, 2020, 0)])
def test_sample_years_rejects(args):
    with pytest.raises(ValueError):
        cli.sample_years(*args)


def test_regions_command(capsys):
    assert cli.main(["regions"]) == 0
    out = capsys.readouterr().out
    assert all(key in out for key in REGIONS)


def test_series_command(monkeypatch, capsys, tmp_path):
    async def fake_series(self, geojson, years, dataset="wpgppop"):
        return {y: 1000.0 * 1.05 ** (y - 2000) for y in years}

    monkeypatch.setattr(cli.WorldPopClient, "population_series", fake_series)
    out_file = tmp_path / "out.csv"
    code = cli.main(["series", "--region", "abidjan", "--step", "10", "--out", str(out_file)])
    assert code == 0
    assert "CAGR 5.00%" in capsys.readouterr().out
    assert out_file.read_text().startswith("year,population")


def test_series_command_reports_errors(capsys):
    assert cli.main(["series", "--bbox", "0,0,1,1", "--start", "1990"]) == 1
    assert "error:" in capsys.readouterr().err


def test_regions_are_valid():
    for region in REGIONS.values():
        assert 0 < region.bbox.area_km2() < 100_000
