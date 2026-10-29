# Côte d'Ivoire's cities, 2015–2025

## The question

How fast are Côte d'Ivoire's largest cities growing, where does that growth happen, and how
far can satellite-based population models be trusted for them?

## Audience

- **Recruiters and data teams:** a reproducible pipeline, a documented method, tests.
- **People in Côte d'Ivoire** (journalists, NGOs, urban planning): sourced findings they can
  quote, in plain language.

## Data

| Input | Use | Source |
| --- | --- | --- |
| WorldPop Global2 R2025A, constrained, 100 m, 2015–2025 | All population measures | [hub.worldpop.org](https://hub.worldpop.org/geodata/listing?id=135), CC BY 4.0, DOI 10.5258/SOTON/WP00839 |
| RGPH 2021 city figures | Census comparison | INS, as reported by UN-Habitat (2023) and the press |
| geoBoundaries gbOpen, ADM2–ADM4 | Matching census figures to administrative units | [geoboundaries.org](https://www.geoboundaries.org) |

Caveats stated on the site:

- 2022–2025 are WorldPop projections (the last census is 2021).
- R2025A is labelled alpha by WorldPop and may be revised.
- R2025A uses the 2021 census as an input, so comparing against it tests how people are
  distributed inside cities, not whether the model recovers the totals.
- The 2000–2020 WorldPop series uses a different method and is not joined to this one.

## Method

- **City extent:** Degree of Urbanisation urban centres (UN Statistical Commission, 2020):
  contiguous ~1 km cells with at least 1,500 people/km² and at least 50,000 people,
  recomputed every year. Gives each city a population and a footprint by one international
  definition.
- **Where growth happens:** people per distance ring around each city centre (0–5, 5–10,
  10–20, 20–30 km), every year.
- **National context:** total population, number of urban centres and their combined
  population; Abidjan's share.

Cities: Abidjan, Bouaké, Korhogo, Daloa, San-Pédro (top five, RGPH 2021) and Yamoussoukro
(political capital).

## Deliverables

1. **Pipeline** (`worldpop-pipeline`, Data workflow): rasters → `web/public/data/*.json`. Done.
2. **Static site** on GitHub Pages: a short story page with 3–5 findings, the census
   comparison, the footprint map 2015 → 2025, then a city explorer. Replaces the live API.
3. **Write-up** for LinkedIn: the findings with one chart and a link.

## Open points

- Confirm San-Pédro and Yamoussoukro RGPH 2021 figures against INS publications.
- Choose the administrative unit each census figure refers to, from `data/admin_matches.json`.
