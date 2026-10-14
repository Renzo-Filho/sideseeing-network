# Chicago Community Areas by 2020 census tract (13 October 2026)

**Superseded on 13 October 2026** by [`chicago_neighborhoods_2026_10_13`](../chicago_neighborhoods_2026_10_13/README.md): a tract (median 0.5 km²) is about 7 times smaller than Brás. The explorer no longer reads this folder; it is kept with the findings in `docs/harmonization/MODEL_REPORT.md` §10.2.

Script: `analysis/scripts/chicago_tract_breakdown.py` at commit `9e8220c9` (about 7 minutes; the file is now `chicago_neighborhoods.py`).

## What it is

A tract piece is the set of 2020 census blocks of one tract that lie inside one Community Area (`block_district_pieces`, the allocation support of U3 and U2), so pieces nest exactly in the 77 areas. There are 1,723 pieces, most of them boundary slivers. **801 are published**: those with at least 5% of their tract's city land and at least 0.05 km² of land. They cover 99.7% of the city's land and all 77 areas (median 10 per area, from 1 to 34; Near North Side and Near West Side 20, West Town 32, Lower West Side 11).

The 21 columns of `sp_chicago_model_v2` are recomputed for every piece with the accepted family scripts' own functions and rules:

| Family | How the piece value is built |
|---|---|
| U3, U2 | ACS 2020–2024 residents and LODES 2023 jobs allocated block → piece by land share (same rule as the areas), per km² of land |
| U6 | Classified Overture places on the piece's land per 100 ACS dwellings (same allocation), and the five log-ratios. The hybrid and all-relative columns are centred on the 77 areas' mean, as the areas' are. With no establishments the composition is missing |
| U4 | PTAL Access Index at the same 100 m resident points as the published run, averaged over the piece's residents. A piece without residents has no U4 |
| U1 | CMAP LUI 2023 occupied-land shares, missing under 10% classified occupied land (S7-4) |
| B1, BV, M1, M6, M3, M4, M7 | `evaluate_b1_step4.coverage`, `evaluate_bv_step5.ghsl`, `evaluate_m1_m6_step6.overture`, `evaluate_m3_m4_m7_step8.faces/summarise/m7_chicago` on the piece's land (M7 on its gross area) |

Names: `Tract NNNN[.NN]` from the census tract code, plus the City of Chicago neighbourhood (layer bbvz-uum9, downloaded 13 October 2026) that holds the piece's representative point. The City layer matches 63 of the 77 areas one-to-one; it does not split Lower West Side (Pilsen and Heart of Chicago).

## Checks (`checks.json`)

Summing the pieces reproduces each area's published counts, and the non-additive functions reproduce the published area values:

| Check | Max difference | Result |
|---|---|---|
| U3 residents, U2 jobs, U6 dwellings | ≤ 1.5e-11 | pass |
| B1 footprint m² | 4.9e-6 m² | pass |
| U1 commerce share | 2.7e-14 | pass |
| U6 establishments, M7 parcels | 0 | pass |
| BV, M3, M4 (function on the areas) | ≤ 1.8e-15 | pass |
| U4 (resident-weighted mean of pieces = area value) | 0 | pass |
| Land | 10,085 m² (0.09%, Hegewisch) | pass at 0.1% |
| M1 street km | 0.149 km (0.19%, East Side) | pass at 0.2% |

The land and M1 differences are gaps in the block support, not computing errors. The 2020 blocks stop short of the Illinois–Indiana line in East Side, leaving a 642 m² strip that holds 0.149 km of State Line Ave.

Thin data among the 801 published pieces: 480 have fewer than 100 classified establishments (a noisy U6 mix), 5 have no residents (no U4), and 10 have no U1 shares.

## Files

| File | Content |
|---|---|
| `tract_columns.csv` | All 1,723 pieces: area, tract, names, `published`, land, counts and the 21 model columns (plus raw U6 log-ratios for all-absolute scaling) |
| `tract_pieces.parquet` | Gross polygons of the 801 published pieces (EPSG:26916) |
| `checks.json` | The checks above and a summary |

## How the explorer uses it

Pieces are **scored, not refitted**. `export_viz_data.scored` standardizes each column with the mean and SD the fit uses (the 77 areas for a relative column, all 173 units for an absolute one), capped at ±3. The export asserts that this reproduces the areas' own rows. In the page, `projectedDistance` applies the current column weights, the calibration β of the 173-unit fit and the family budgets. Pieces do not change the model, its rankings or its match strength. Findings for Brás are in [`docs/harmonization/MODEL_REPORT.md` §10.2](../../../../docs/harmonization/MODEL_REPORT.md#102-census-tracts-first-attempt-superseded).
