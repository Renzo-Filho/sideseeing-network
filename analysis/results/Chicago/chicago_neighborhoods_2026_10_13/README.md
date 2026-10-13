# Chicago Community Areas by City neighborhood (13 October 2026)

Script: `analysis/scripts/chicago_neighborhoods.py` (about 7 minutes). Read by `analysis/scripts/export_viz_data.py` for the explorer's **Chicago neighborhoods** tab. It replaces the census-tract version ([`chicago_tract_breakdown_2026_10_13`](../chicago_tract_breakdown_2026_10_13/README.md)), whose pieces were about 7 times smaller than Brás.

## What it is

A neighborhood piece is the set of 2020 census-block pieces of one Community Area (`block_district_pieces`, the allocation support of U3 and U2) whose representative point lies in one of the City of Chicago's 98 neighborhoods (layer bbvz-uum9, downloaded 13 October 2026; the City calls it approximate and unofficial). Pieces therefore follow block edges and nest exactly in the 77 areas. There are 107 pieces, and **102 are published**: those with at least 5% of their neighborhood's city land and at least 0.05 km² of land. They cover 99.99% of the land. The five left out are slivers such as Magnificent Mile (0.01 km² after the cut).

The median published piece has 5.1 km² of land; Brás has 3.6 km². 13 areas split into 2 to 5 neighborhoods:

| Area | Neighborhoods |
|---|---|
| Near North Side | River North, Streeterville, Gold Coast, Rush & Division, Old Town |
| West Town | West Town, Wicker Park, Ukrainian Village, East Village, Humboldt Park |
| Near West Side | West Loop, United Center, Little Italy and UIC, Greektown |
| Loop | Loop, Printers Row, Millennium Park, Grant Park |
| Lake View | Lake View, Wrigleyville, Boystown |
| Lincoln Park | Lincoln Park, Sheffield & DePaul, Old Town |
| Logan Square | Logan Square, Bucktown |
| Austin | Austin, Galewood |
| Near South Side | Near South Side, Museum Campus |
| Armour Square | Armour Square, Chinatown |
| Hyde Park | Hyde Park, Jackson Park |
| Woodlawn | Woodlawn, Jackson Park |
| Edgewater | Edgewater, Andersonville |

The other 64 areas keep one neighborhood equal to the area, Lower West Side among them, so Pilsen cannot be isolated. The smallest published pieces are Greektown (0.14 km²), Printers Row (0.20 km²) and Millennium Park (0.26 km²).

The 21 columns of `sp_chicago_model_v2` are recomputed for every piece with the accepted family scripts' own functions and rules, exactly as in the tract version:
- U3, U2, U6 dwellings and the U4 resident points come from the block allocation;
- B1, BV, M1, M6, M3, M4, M7, U1 and the U6 places are computed on the piece's land, with M7 on its gross area.

## Checks (`checks.json`)

| Check | Max difference | Result |
|---|---|---|
| U3 residents, U2 jobs, U6 dwellings (sum of pieces = area) | ≤ 2.9e-11 | pass |
| B1 footprint m² | 4.9e-6 m² | pass |
| U1 commerce share | 2.7e-14 | pass |
| U6 establishments, M7 parcels | 0 | pass |
| BV, M3, M4 (function on the areas) | ≤ 1.8e-15 | pass |
| U4 (resident-weighted mean of pieces = area value) | 0 | pass |
| Land | 10,085 m² (0.09%, Hegewisch) | pass at 0.1% |
| M1 street km | 0.149 km (0.19%, East Side) | pass at 0.2% |

The land and M1 differences are gaps in the block support along the Illinois–Indiana line, not computing errors. Among published pieces, 6 have fewer than 100 classified establishments and 4 have no U1 shares.

## Files

| File | Content |
|---|---|
| `neighborhood_columns.csv` | All 107 pieces: area, neighborhood name, `published`, land, counts and the 21 model columns (plus raw U6 log-ratios for all-absolute scaling) |
| `neighborhood_pieces.parquet` | Gross polygons of the 102 published pieces (EPSG:26916) |
| `checks.json` | The checks above and a summary |

## How the explorer uses it

Pieces are **scored, not refitted**: `export_viz_data.scored` standardizes each column with the fit's mean and SD (the 77 areas for a relative column, all 173 units for an absolute one), capped at ±3, and the export asserts that this reproduces the areas' own rows. In the page, `projectedDistance` applies the current column weights, the calibration β of the 173-unit fit and the family budgets. Findings for Brás are in [`docs/harmonization/SETTINGS_DISCUSSION.md` §10](../../../../docs/harmonization/SETTINGS_DISCUSSION.md#10-city-neighborhoods-inside-each-area-13-october-2026).
