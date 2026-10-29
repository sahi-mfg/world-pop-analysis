"""Retrieve and analyse WorldPop gridded population estimates."""

from worldpop_analysis.analysis import cagr, doubling_time, growth_table, summarize
from worldpop_analysis.client import WorldPopClient, WorldPopError
from worldpop_analysis.geometry import BBox
from worldpop_analysis.regions import REGIONS, Region

__all__ = [
    "REGIONS",
    "BBox",
    "Region",
    "WorldPopClient",
    "WorldPopError",
    "cagr",
    "doubling_time",
    "growth_table",
    "summarize",
]

__version__ = "0.3.0"
