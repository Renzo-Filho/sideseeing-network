# Chicago M3/M4 polygon-first source pilot — 26 September 2026

## Decision

**Keep M3/M4 unaccepted for the Chicago-only model.** A property-side boundary is feasible in many sampled places and fixes the most obvious centerline median errors, but this pilot does not yet define complete, verified physical blocks for all 77 Community Areas. In particular, a Cook ROW land component merges a visually plausible block with adjacent land in one saved case; ROW alone also leaves a false industrial-yard fragment inside a much larger land component. The [fresh-tile continuation](../chicago_m3_fresh_tiles_2026_09_26/README.md) identifies the merged side as a named municipal street missing from Cook ROW/Road Edge and tests the newly found DuPage deeded ROW layer.

## Sources and reproducibility

The pilot downloaded **bounded extracts outside this repository's prior source inventory**: [Cook 2025 right-of-way polygons](https://gis.cookcountyil.gov/traditional/rest/services/RightOfWay_Cadastre/MapServer/2025), [Cook Road Edge polygons](https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/7), and [DuPage Parcel Blocks](https://gis.dupageco.org/arcgis/rest/services/ParcelSearch/DuPageAssessmentParcelViewer/MapServer/0). The six 250 m buffered Community Area envelopes were CHI:11, 49, 57, 63, 32 (Loop), and 76 (O'Hare). Raw GeoJSON is cached in ignored `analysis/work/chicago_m3_row_land_2026_09_26/`; SHA-256, query and feature counts are in `source_receipts.json` and `dupage_parcel_block_receipt.json`. The Cook parcel comparison uses the previously acquired 2024 BaseParcel polygons.

Run the three scripts without `--fetch` to recompute from cached data:

```bash
.venv/bin/python analysis/scripts/pilot_chicago_m3_row_land_2026_09_26.py
.venv/bin/python analysis/scripts/pilot_chicago_m3_parcel_groups_2026_09_26.py
.venv/bin/python analysis/scripts/pilot_chicago_m3_dupage_blocks_2026_09_26.py
```

`--fetch` downloads missing bounded county extracts. Cook ROW `ROWTYPE` 1/4/5 supplied the active road mask; 2/4 supplied a separate rail diagnostic. Cook Road Edge `TYPE=1` supplied the ordinary road mask and `TYPE=5` identified alleys. The diagnostic land components are the extraction polygon minus each mask. The `alley_open` variant removes a 1 m buffer around mapped alleys from the ROW mask to test reconnection; this is **not** a certified topology rule. Road Edge has no established observation vintage in this layer, and the 2025 ROW layer name denotes a published snapshot of digitized plat ROW, not a 2025 ground survey. The source geometries were repaired with `make_valid` for analysis; raw responses and hashes were preserved.

## Results

The saved comparison has 29 case rows from the prior visual review, representing **26 distinct polygons** after geometry deduplication: 15 visually plausible and 11 visually false. The sample was selected for problem cases; these proportions are **not** citywide precision or recall. The old centerline polygon is a comparison shape, not surveyed ground truth.

| Check | Observed result | Interpretation |
|---|---|
| False road enclosures | 8 of 11 false polygons lie wholly in active road ROW. | ROW immediately excludes medians, wedges and paved fragments that the centerline method admitted. |
| Alley topology | Raw ROW splits ordinary blocks into alley-separated strips. For 14 of 15 plausible polygons, the best `alley_open` land component has IoU at least 0.90 with the old candidate after its ROW area is removed. | Alleys need an explicit rule. This agreement is diagnostic, because the old outline is not independent truth. |
| Remaining plausible mismatch | `C_M3_01` has IoU 0.35: the ROW complement joins its candidate land to a substantially larger component. | A missing/ambiguous divider must be checked against parcels, plats and imagery; ROW-only components cannot be promoted. |
| Interior false case | The industrial-yard fragment `H_M3_04` occupies about 2,462 m² inside a ~67,939 m² `alley_open` land component and covers only 4.8% of its dominant tax parcel group. | A component/parcel-continuity check is needed; parcel occupancy by itself is insufficient. |
| Parcel evidence | All 15 plausible distinct cases intersect one dominant seven-digit PIN tax grouping; eight false cases have no BaseParcel support, while three false cases do overlap parcels. | Parcel containment and group scale help reject interior cuts. The first seven PIN digits can mean a tax block **or quarter section**, so the grouping is not a physical-block identity rule. |
| Shape sensitivity | Median compactness of the plausible centerline polygons is 0.696, versus 0.578 for the matched alley-open land components. | M4 changes materially when measured at property-side boundaries; neither value is an accepted M4 feature. |
| O'Hare support | In CHI:76, 73.7% of mapped ordinary road-edge area lies outside Cook active road ROW, versus 3.8–23.3% in the other five areas. | A Cook-only road-ROW construction is incomplete there; these are area-mask comparisons, not measured missing-road rates. |
| DuPage source | 27 DuPage Parcel Block polygons intersect O'Hare with positive area. Their union overlaps 99.942% of the 81 locally held DuPage parcels' union. | The new official source fills **cadastral block coverage** in the DuPage parcel area; physical street-block equivalence, especially at the airport, is unverified. |

The source-area and case-level measurements are in `area_row_coverage.csv`, `case_row_land_comparison.csv`, `case_parcel_group_comparison.csv`, `validation_summary.json`, and `dupage_parcel_block_summary.json`. Four illustrative raw-versus-alley-open maps are in `maps/`. Full extraction-component counts include tiny seam pieces and extraction-edge pieces; they are not block counts.

## Remaining acceptance test

1. Define a Chicago physical block as a contiguous ground-land unit bounded by public road ROW, with a documented rule for alleys, rail, water, parks, airport land, private roads and grade-separated facilities. Use the property/ROW boundary for area and perimeter. Do not turn tax groups or Census blocks into physical blocks by label alone.
2. Use cadastral continuity to identify ROW gaps (including `C_M3_01`), then independently trace a fresh, geographically spread reference sample of true blocks **and missed blocks** from current orthophotos/recorded plats. Freeze construction and rejection rules before testing that sample.
3. Validate the acquired DuPage deeded ROW layer's coding and airport relevance; it adds only a small O'Hare polygon area in the bounded continuation. The DuPage Parcel Block layer is a candidate cadastral support layer, not a substitute for physical-road validation or an explicit airport-area rule.
4. Measure precision, recall, boundary displacement, area error and M4 compactness/elongation tails by neighborhood and special context. Only then rebuild all 77 areas and decide whether M3/M4 enter a Chicago-only model contract.

This was a bounded source and method test. No M3/M4 release, feature matrix, model fit or ranking was changed.
