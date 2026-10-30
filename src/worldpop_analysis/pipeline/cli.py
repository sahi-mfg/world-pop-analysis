"""``worldpop-pipeline``: download, measure, write. Needs the ``pipeline`` extra."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

from worldpop_analysis.pipeline import buildings, config, run, sources

ROOT = Path(__file__).resolve().parents[3]
log = logging.getLogger("worldpop_analysis.pipeline")


def local_rasters(directory: Path) -> dict[int, Path]:
    """Rasters already on disk, keyed by the 4-digit year in their file name."""
    found = {}
    for path in sorted(directory.glob("*.tif")):
        match = re.search(r"(20\d\d)", path.name)
        if match and int(match.group(1)) in config.YEARS:
            found[int(match.group(1))] = path
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="worldpop-pipeline", description=__doc__)
    parser.add_argument(
        "--cache", type=Path, default=ROOT / ".cache" / "worldpop", help="raster cache"
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "web" / "public" / "data", help="site data folder"
    )
    parser.add_argument("--offline", action="store_true", help="use cached rasters only")
    parser.add_argument(
        "--admin", action="store_true", help="also match census figures to geoBoundaries units"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    rasters = local_rasters(args.cache) if args.offline else sources.fetch_rasters(args.cache)
    if not rasters:
        parser.error(f"no rasters for {config.YEARS.start}-{config.YEARS.stop - 1} in {args.cache}")

    doc, footprints = run.build(rasters)
    run.write(doc, footprints, args.out)
    for city in doc["cities"]:
        first, last = city["series"][0], city["series"][-1]
        log.info(
            "%-13s urban centre %s -> %s people, %s -> %s km2; census 2021 %s",
            city["name"],
            first["urban_centre_population"],
            last["urban_centre_population"],
            first["urban_centre_area_km2"],
            last["urban_centre_area_km2"],
            city["census_2021"]["population"],
        )

    if args.admin and config.LAST_CENSUS_YEAR in rasters:
        units = {}
        for level in (2, 3, 4):
            try:
                units[level] = sources.fetch_admin_units(level)
            except Exception as exc:  # diagnostics must not sink the data build
                log.warning("geoBoundaries ADM%s unavailable: %s", level, exc)
        matches = run.admin_matches(rasters[config.LAST_CENSUS_YEAR], units, config.CITIES)
        diag = ROOT / "data" / "admin_matches.json"
        diag.parent.mkdir(exist_ok=True)
        diag.write_text(json.dumps(matches, ensure_ascii=False, indent=1) + "\n")
        for m in matches:
            log.info(
                "%-12s %s %-30s WorldPop %9d  census %9d",
                m["city"],
                m["level"],
                m["unit"],
                m["worldpop"],
                m["census_2021"],
            )
    return 0


def main_buildings(argv: list[str] | None = None) -> int:
    """``worldpop-buildings``: add Open Buildings counts to the pipeline's output."""
    parser = argparse.ArgumentParser(prog="worldpop-buildings", description=main_buildings.__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "open-buildings")
    parser.add_argument("--data", type=Path, default=ROOT / "web" / "public" / "data")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    doc = json.loads((args.data / "civ.json").read_text())
    footprints = json.loads((args.data / "footprints.geojson").read_text())
    counts = buildings.build(config.CITIES, footprints, args.cache)
    footprint_year = max(f["properties"]["year"] for f in footprints["features"])
    doc = buildings.merge_into(doc, counts, footprint_year)
    (args.data / "civ.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    for key, series in counts.items():
        first, last = series[0], series[-1]
        log.info(
            "%-13s buildings within 30 km %s -> %s (%+.1f%%), in urban centre %s -> %s",
            key,
            sum(first["rings"]),
            sum(last["rings"]),
            (sum(last["rings"]) / max(sum(first["rings"]), 1) - 1) * 100,
            first["urban_centre"],
            last["urban_centre"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
