"""Preset areas of interest: fast-growing cities and a few reference points."""

from __future__ import annotations

from dataclasses import dataclass

from worldpop_analysis.geometry import BBox


@dataclass(frozen=True, slots=True)
class Region:
    key: str
    name: str
    country: str
    bbox: BBox


_REGIONS = [
    Region("abidjan", "Abidjan", "Côte d'Ivoire", BBox(-4.15, 5.20, -3.85, 5.45)),
    Region("lagos", "Lagos", "Nigeria", BBox(3.10, 6.38, 3.70, 6.70)),
    Region("kinshasa", "Kinshasa", "DR Congo", BBox(15.15, -4.50, 15.50, -4.25)),
    Region("nairobi", "Nairobi", "Kenya", BBox(36.65, -1.45, 37.05, -1.15)),
    Region("dakar", "Dakar", "Senegal", BBox(-17.55, 14.65, -17.15, 14.85)),
    Region("dhaka", "Dhaka", "Bangladesh", BBox(90.33, 23.68, 90.48, 23.90)),
    Region("paris", "Paris", "France", BBox(2.22, 48.81, 2.47, 48.91)),
    Region("tyrol", "Tyrol / Dolomites", "Austria & Italy", BBox(9.95, 45.98, 12.66, 47.86)),
]

REGIONS: dict[str, Region] = {r.key: r for r in _REGIONS}
