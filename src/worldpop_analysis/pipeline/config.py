"""What the pipeline measures, and where the inputs come from."""

from __future__ import annotations

from dataclasses import dataclass

ISO3 = "CIV"
YEARS = range(2015, 2026)
# Last census year: everything after it is a WorldPop projection.
LAST_CENSUS_YEAR = 2021

DATASET = {
    "name": "WorldPop Global2 population counts, constrained, 100 m",
    "release": "R2025A v1",
    "doi": "10.5258/SOTON/WP00839",
    "url": "https://hub.worldpop.org/geodata/listing?id=135",
    "license": "CC BY 4.0",
}
RASTER_DIR_URL = "https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/{year}/{iso3}/v1/100m/constrained/"

# Degree of Urbanisation, stage 1 (UN Statistical Commission, 2020): an urban centre is a
# cluster of contiguous 1 km² cells with at least 1,500 people/km² and 50,000 people in total.
AGGREGATION = 10  # 3" pixels per side of a 30" (~1 km) cell
URBAN_DENSITY = 1500.0
URBAN_MIN_POPULATION = 50_000.0
MAX_GAP_CELLS = 15  # holes up to ~15 km² inside a centre are filled
# A city point that falls just outside its centre (a park, a lagoon) snaps to the nearest one.
SNAP_DISTANCE_KM = 10.0

RING_EDGES_KM = (0, 5, 10, 20, 30)

GEOBOUNDARIES_API = "https://www.geoboundaries.org/api/current/gbOpen/{iso3}/ADM{level}/"


@dataclass(frozen=True, slots=True)
class City:
    key: str
    name: str
    lon: float
    lat: float
    #: Results of the 2021 general census (RGPH 2021), as published; ``approx`` when only a
    #: rounded figure from secondary reporting was found.
    census_2021: int
    census_source: str
    census_approx: bool = False


_UNHABITAT = "UN-Habitat, Programme pays Côte d'Ivoire (2023), from RGPH 2021"
_PRESS = "Connexion Ivoirienne (2022-08-03), RGPH 2021 ranking, rounded"

CITIES = (
    City("abidjan", "Abidjan", -4.0197, 5.3236, 5_616_633, _UNHABITAT),
    City("bouake", "Bouaké", -5.0300, 7.6900, 832_371, _UNHABITAT),
    City("korhogo", "Korhogo", -5.6296, 9.4580, 440_926, _UNHABITAT),
    City("daloa", "Daloa", -6.4502, 6.8774, 421_879, _UNHABITAT),
    City("san-pedro", "San-Pédro", -6.6363, 4.7485, 390_000, _PRESS, census_approx=True),
    City("yamoussoukro", "Yamoussoukro", -5.2893, 6.8276, 340_000, _PRESS, census_approx=True),
)
