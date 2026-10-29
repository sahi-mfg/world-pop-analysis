"""Bounding boxes and the GeoJSON the WorldPop stats API expects."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True, slots=True)
class BBox:
    """A lon/lat bounding box in WGS84 degrees."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def __post_init__(self) -> None:
        if not -180 <= self.min_lon < self.max_lon <= 180:
            raise ValueError(f"invalid longitude range: {self.min_lon}..{self.max_lon}")
        if not -90 <= self.min_lat < self.max_lat <= 90:
            raise ValueError(f"invalid latitude range: {self.min_lat}..{self.max_lat}")

    @classmethod
    def parse(cls, text: str) -> BBox:
        """Parse ``"min_lon,min_lat,max_lon,max_lat"``."""
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be 'min_lon,min_lat,max_lon,max_lat'")
        return cls(*(float(p) for p in parts))

    @property
    def center(self) -> tuple[float, float]:
        """(lat, lon) of the box centre."""
        return (self.min_lat + self.max_lat) / 2, (self.min_lon + self.max_lon) / 2

    @property
    def ring(self) -> list[list[float]]:
        """Closed, counter-clockwise exterior ring as [lon, lat] pairs."""
        return [
            [self.min_lon, self.min_lat],
            [self.max_lon, self.min_lat],
            [self.max_lon, self.max_lat],
            [self.min_lon, self.max_lat],
            [self.min_lon, self.min_lat],
        ]

    def area_km2(self) -> float:
        """Exact area of the box on a spherical Earth."""
        lat1, lat2 = math.radians(self.min_lat), math.radians(self.max_lat)
        dlon = math.radians(self.max_lon - self.min_lon)
        return EARTH_RADIUS_KM**2 * dlon * (math.sin(lat2) - math.sin(lat1))

    def to_geojson(self) -> dict[str, Any]:
        return polygon_feature_collection(self.ring)


def polygon_feature_collection(ring: list[list[float]]) -> dict[str, Any]:
    """Wrap a single polygon ring in the FeatureCollection shape WorldPop accepts."""
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise ValueError("polygon ring must be closed and have at least 4 positions")
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        ],
    }


def dumps(geojson: dict[str, Any]) -> str:
    """Compact JSON, keeping the query string as short as possible."""
    return json.dumps(geojson, separators=(",", ":"))
