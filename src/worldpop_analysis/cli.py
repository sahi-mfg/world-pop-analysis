"""Command-line interface: ``worldpop --help``."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from worldpop_analysis.analysis import growth_table, summarize
from worldpop_analysis.client import AVAILABLE_YEARS, WorldPopClient, WorldPopError
from worldpop_analysis.geometry import BBox
from worldpop_analysis.regions import REGIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worldpop", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true", help="log HTTP activity")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("regions", help="list the preset regions")

    series = sub.add_parser("series", help="population time series for an area")
    area = series.add_mutually_exclusive_group(required=True)
    area.add_argument("--region", choices=sorted(REGIONS), help="preset region key")
    area.add_argument("--bbox", type=BBox.parse, help="min_lon,min_lat,max_lon,max_lat")
    series.add_argument("--start", type=int, default=2000)
    series.add_argument("--end", type=int, default=2020)
    series.add_argument("--step", type=int, default=5, help="years between samples")
    series.add_argument("--out", type=Path, help="write the table to this CSV file")

    datasets = sub.add_parser("datasets", help="raster datasets published for a country")
    datasets.add_argument("iso3", help="ISO 3166-1 alpha-3 code, e.g. CIV")
    return parser


def sample_years(start: int, end: int, step: int) -> list[int]:
    if step < 1:
        raise ValueError("step must be >= 1")
    if start not in AVAILABLE_YEARS or end not in AVAILABLE_YEARS or start > end:
        raise ValueError(f"years must satisfy {AVAILABLE_YEARS.start} <= start <= end <= 2020")
    years = list(range(start, end + 1, step))
    if years[-1] != end:
        years.append(end)
    return years


async def _series(args: argparse.Namespace) -> int:
    bbox = REGIONS[args.region].bbox if args.region else args.bbox
    years = sample_years(args.start, args.end, args.step)
    async with WorldPopClient() as wp:
        series = await wp.population_series(bbox.to_geojson(), years)

    table = growth_table(series, area_km2=bbox.area_km2())
    print(table.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))
    s = summarize(series)
    print(
        f"\n{s.start_year}->{s.end_year}: {s.total_change_pct:+.1f}% "
        f"(CAGR {s.cagr:.2%}, doubling time {s.doubling_years:.0f} years)"
    )
    if args.out:
        table.to_csv(args.out, index=False)
        print(f"saved {args.out}")
    return 0


async def _datasets(args: argparse.Namespace) -> int:
    async with WorldPopClient() as wp:
        rows = await wp.country_datasets(args.iso3)
    for row in rows:
        print(f"{row.get('popyear', '?'):>6}  {row.get('title', '')}")
    print(f"{len(rows)} datasets")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.command == "regions":
        for r in REGIONS.values():
            print(f"{r.key:<10} {r.name}, {r.country}  ({r.bbox.area_km2():,.0f} km²)")
        return 0
    try:
        handler = _series if args.command == "series" else _datasets
        return asyncio.run(handler(args))
    except (WorldPopError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
