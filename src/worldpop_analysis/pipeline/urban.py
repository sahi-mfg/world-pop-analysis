"""Grid arithmetic: 1 km aggregation and Degree of Urbanisation urban centres.

Everything here works on plain numpy arrays so it can be tested without rasters.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from worldpop_analysis.pipeline import config

EARTH_RADIUS_KM = 6371.0088
_ROOK = ndimage.generate_binary_structure(2, 1)  # 4-connectivity, as DEGURBA prescribes
_QUEEN = np.ones((3, 3), dtype=bool)


def aggregate(pop: np.ndarray, factor: int = config.AGGREGATION) -> np.ndarray:
    """Sum ``factor`` x ``factor`` blocks; trailing rows/columns short of a block are dropped."""
    h, w = (pop.shape[0] // factor) * factor, (pop.shape[1] // factor) * factor
    return pop[:h, :w].reshape(h // factor, factor, w // factor, factor).sum(axis=(1, 3))


def row_areas_km2(top_lat: float, cell_deg: float, rows: int, cols: int) -> np.ndarray:
    """Area of every cell of a north-up lon/lat grid on a spherical Earth, shape (rows, cols)."""
    edges = np.radians(top_lat - cell_deg * np.arange(rows + 1))
    per_row = EARTH_RADIUS_KM**2 * math.radians(cell_deg) * (np.sin(edges[:-1]) - np.sin(edges[1:]))
    return np.repeat(per_row[:, None], cols, axis=1)


def urban_centres(
    pop_1km: np.ndarray,
    area_km2: np.ndarray,
    density: float = config.URBAN_DENSITY,
    min_population: float = config.URBAN_MIN_POPULATION,
    max_gap: int = config.MAX_GAP_CELLS,
) -> np.ndarray:
    """Label array of urban centres (0 = not urban centre), labels 1..n."""
    dense = pop_1km / area_km2 >= density
    labels, n = ndimage.label(dense, structure=_ROOK)
    if n == 0:
        return labels
    sizes = ndimage.sum(pop_1km, labels, index=np.arange(1, n + 1))
    keep = np.zeros(n + 1, dtype=bool)
    keep[1:] = sizes >= min_population
    mask = keep[labels]

    # Fill small enclosed gaps (parks, a lagoon inlet), then apply the majority rule:
    # a cell with at least 5 of its 8 neighbours in a centre joins it, until nothing changes.
    holes, n_holes = ndimage.label(ndimage.binary_fill_holes(mask) & ~mask, structure=_ROOK)
    if n_holes:
        hole_sizes = np.bincount(holes.ravel())
        small = hole_sizes <= max_gap
        small[0] = False
        mask |= small[holes]
    while True:
        neighbours = (
            ndimage.convolve(mask.astype(np.int8), _QUEEN.astype(np.int8), mode="constant") - mask
        )
        grow = ~mask & (neighbours >= 5)
        if not grow.any():
            break
        mask |= grow
    labels, _ = ndimage.label(mask, structure=_ROOK)
    return labels


@dataclass(frozen=True, slots=True)
class Centre:
    mask: np.ndarray
    population: float
    area_km2: float


def centre_at(
    labels: np.ndarray,
    pop_1km: np.ndarray,
    area_km2: np.ndarray,
    row: int,
    col: int,
    cell_km: float,
    snap_km: float = config.SNAP_DISTANCE_KM,
) -> Centre | None:
    """The urban centre containing (row, col), or the nearest one within ``snap_km``."""
    label = labels[row, col] if 0 <= row < labels.shape[0] and 0 <= col < labels.shape[1] else 0
    if label == 0:
        rows, cols = np.nonzero(labels)
        if rows.size == 0:
            return None
        dist = np.hypot(rows - row, cols - col) * cell_km
        nearest = int(dist.argmin())
        if dist[nearest] > snap_km:
            return None
        label = labels[rows[nearest], cols[nearest]]
    mask = labels == label
    return Centre(
        mask=mask, population=float(pop_1km[mask].sum()), area_km2=float(area_km2[mask].sum())
    )


def ring_populations(
    pop: np.ndarray,
    lons: np.ndarray,
    lats: np.ndarray,
    lon0: float,
    lat0: float,
    edges_km: tuple[float, ...] = config.RING_EDGES_KM,
) -> list[float]:
    """People living between consecutive distances from (lon0, lat0), on the 100 m grid.

    ``lons`` and ``lats`` are the pixel-centre coordinates of the columns and rows of ``pop``.
    Distances use an equirectangular approximation, accurate to well under 1 % at 30 km.
    """
    dx = (lons[None, :] - lon0) * 111.320 * math.cos(math.radians(lat0))
    dy = (lats[:, None] - lat0) * 110.574
    dist = np.hypot(dx, dy)
    return [float(pop[(dist >= lo) & (dist < hi)].sum()) for lo, hi in itertools.pairwise(edges_km)]
