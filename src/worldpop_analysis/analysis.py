"""Turning a yearly population series into growth metrics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd


def growth_table(series: Mapping[int, float], area_km2: float | None = None) -> pd.DataFrame:
    """Year-by-year table with absolute and relative change (and density if area is known)."""
    if not series:
        raise ValueError("empty population series")
    df = pd.DataFrame(sorted(series.items()), columns=["year", "population"])
    df["change"] = df["population"].diff()
    years_elapsed = df["year"].diff()
    # Annualised so that gaps in the series (e.g. 2000, 2005, 2010) stay comparable.
    df["annual_growth_pct"] = (
        (df["population"] / df["population"].shift()) ** (1 / years_elapsed) - 1
    ) * 100
    df["index_100"] = df["population"] / df["population"].iloc[0] * 100
    if area_km2:
        df["density_per_km2"] = df["population"] / area_km2
    return df


def cagr(start: float, end: float, years: float) -> float:
    """Compound annual growth rate, as a fraction (0.05 == 5 %/year)."""
    if start <= 0 or years <= 0:
        raise ValueError("start population and duration must be positive")
    return (end / start) ** (1 / years) - 1


def doubling_time(rate: float) -> float:
    """Years needed to double at a constant annual ``rate``; ``inf`` if not growing."""
    if rate <= 0:
        return math.inf
    return math.log(2) / math.log1p(rate)


@dataclass(frozen=True, slots=True)
class Summary:
    start_year: int
    end_year: int
    start_population: float
    end_population: float
    cagr: float
    doubling_years: float
    peak_growth_year: int | None

    @property
    def total_change_pct(self) -> float:
        return (self.end_population / self.start_population - 1) * 100


def summarize(series: Mapping[int, float]) -> Summary:
    """Headline numbers for a population series."""
    table = growth_table(series)
    first, last = table.iloc[0], table.iloc[-1]
    rate = (
        cagr(first.population, last.population, last.year - first.year) if len(table) > 1 else 0.0
    )
    growth = table["annual_growth_pct"].dropna()
    return Summary(
        start_year=int(first.year),
        end_year=int(last.year),
        start_population=float(first.population),
        end_population=float(last.population),
        cagr=rate,
        doubling_years=doubling_time(rate),
        peak_growth_year=int(table.loc[growth.idxmax(), "year"]) if not growth.empty else None,
    )
