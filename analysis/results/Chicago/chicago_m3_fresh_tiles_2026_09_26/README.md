# Chicago M3/M4 fresh tile and source-gap continuation — 26 September 2026

## Decision

**M3/M4 remain unaccepted.** The polygon-first approach performs better on a small, newly selected imagery sample, but the source gaps examined here show why a 77-area physical-block release is premature. A named ordinary street is absent from both Cook ROW and Road Edge; deeded DuPage ROW barely changes O'Hare coverage. Freeway medians and airport open land still need explicit rejection or land-support rules. Newly found Cook Lake polygons resolve the two fresh water controls, but that source has not been tested citywide.

## Fresh reference design

`tile_selection.json` freezes 12 locations (two each in CHI:11, 49, 57, 63, Loop 32 and O'Hare 76) using seed 20260926. Points were sampled from the interior of each Community Area, at least 500 m apart and at least 280 m from previous saved case centers, **without block candidates, Census blocks, OSM or imagery**. [Cook 2025 orthophotos](https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer) were then cached with hashes in `imagery_receipts.json` and ignored `analysis/work/chicago_m3_fresh_tiles_2026_09_26/`. The `contact_sheet.jpg` shows all 12 tiles. `image_extent_validation.json` verifies the image service preserved the requested metric extent to less than 1 mm in a sample tile.

One analyst viewed only raw orthophotos and sketched 11 approximate, fully visible property-side blocks in six tiles; four non-block control points were also frozen before viewing ROW outputs. `visual_reference.json` stores the pixel rings/points and the definition: ordinary public streets divide ground-land blocks, interior alleys do not; parks bounded by streets count; highway medians, water and airport open land do not. Two tiles with industrial/private-access and institution boundaries were left unadjudicated. These rough orthophoto rectangles are **not surveyed boundaries or a complete census of blocks within the tiles**. Thus the following is a fresh diagnostic, not citywide precision or recall.

The evaluator compares each reference with the best overlapping component of three source masks inside its 320 m square tile: Cook active road ROW raw; ROW with mapped Road Edge alleys opened; and ROW plus ordinary Road Edge with mapped alleys opened. No threshold was fitted to these sketches.

| Result on 11 positive sketches | Raw ROW | Alley-open ROW | ROW + Road Edge, alley-open |
|---|---:|---:|---:|
| Median IoU with rough independent sketch | 0.386 | **0.827** | 0.824 |
| Sketches with IoU ≥0.5 | 3/11 | **11/11** | 11/11 |

The first result reproduces the alley-splitting defect without using old centerline candidates as reference. The alley-open variants improve whole-block construction, including two Loop commercial blocks and a park block. The worst alley-open agreement is 0.625, and some components extend beyond or fall inside the rough sketch. Candidate boundaries still need independent, more precise checking. See `positive_reference_comparison.csv` and six `*_comparison.png` overlays.

The four negative controls show distinct risks (`negative_reference_comparison.csv`):

- A freeway/interchange grass median is a **5,306 m² closed land component** under Cook ROW alone. Adding ordinary Road Edge reduces the component containing the control point to **873 m²**; this supports a combined road-surface check, but one control does not validate an area cutoff.
- Marina water and airport open land become components touching the tile edge. Tile-clipped component area is not a physical-block area. Chicago's existing Hydro polygon covers the marina water point but omits the airport pond point.
- A jurisdiction check puts both airport negative points on the **Cook** side, outside DuPage's county polygon and parcel blocks. The bounded [DuPage hydrography](https://gis.dupageco.org/arcgis/rest/services/Hydrography/DPMS_LakesPonds_Service/MapServer/0) extract is therefore not expected to cover them. Five of its polygons intersect O'Hare elsewhere; `dupage_hydro_summary.json` and its receipt preserve that source check.
- The newly acquired [Cook Lake polygon layer](https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/8) **does** cover both water controls. The airport point lies in its “LAKE O'HARE” polygon (LIDAR source year 2022), and the marina point lies in Lake Michigan (orthophoto source year 2020). `cook_lake_summary.json` and two raw receipts preserve the check. A county water mask is feasible for these cases; broader completeness remains unmeasured.

## Cook street gap: `C_M3_01`

The [parcel/orthophoto overlay](../chicago_m3_row_land_2026_09_26/maps/C_M3_01_parcel_orthophoto.png) revises the earlier interpretation. The north-side passage is **West Veterans Place**: the municipal street source records `W VETERANS PL`, class 4, and its centerline (`trans_id=154550`) follows about **98 m** of that side. The cached OSM tile independently names it as a residential street. It is **not** Cook Road Edge `TYPE=5` alley, and neither active road ROW nor ordinary Road Edge maps the passage there. Six candidate-intersecting BaseParcels share tax prefix `1309323`; parcels north of the street have other prefixes. This is a concrete ROW/Road Edge omission, not evidence that the old label should be changed to an alley.

As an initial diagnostic, we intersected the local nonparcel gap with a buffer around that municipal centerline and added it to the road mask. At 6, 15 and 20 m search widths, the candidate land separated from the oversized northern component; at 8–12 m, the first implementation left connecting seams. `c_m3_01_parcel_orthophoto_summary.json` preserves that original result. A [27 September follow-up](../chicago_m3_veterans_repair_2026_09_27/README.md) isolated its cause: subtracting the existing ROW from the new corridor before union created near-zero-area numerical seams. Direct union or a 0.01 m precision grid separates the parcel-anchored face at all six widths. This corrects the earlier inference that the search width itself caused the topology change. The six parcels are part of the repair construction, so their high overlap is not independent boundary validation; no width or general repair rule is yet accepted. The [Cook ROW source](https://gis.cookcountyil.gov/traditional/rest/services/RightOfWay_Cadastre/MapServer/2025) is based on digitized tax-exempt platted rights-of-way, so a missing represented polygon cannot be filled by assuming every centerline buffer has the same legal or physical width.

## Newly acquired DuPage ROW and hydro

An overlooked official [DuPage deeded ROW polygon layer](https://gis.dupageco.org/arcgis/rest/services/OpenData/ROW/MapServer/0) was acquired for the buffered O'Hare envelope. Of 162 returned features, only 13 intersect O'Hare with positive area, covering **0.100 km²**. Combining all of them with Cook active-road ROW changes the fraction of ordinary Cook Road Edge area outside ROW in O'Hare only from **73.7408% to 73.6418%**. This is a mask-overlap diagnostic, not a missing-public-road percentage: airport paving includes nonstreet surfaces. The service advertises type labels such as Dedicated, Vacated, ROW and Private, but these queried records return numeric strings (`0`, `2`, `3`, or null), so a valid active-road filter cannot yet be inferred from its published type domain. Results and raw receipt are in `../chicago_m3_row_land_2026_09_26/dupage_row_summary.json` and `dupage_row_receipt.json`.

The separately acquired DuPage **Parcel Blocks** cover held DuPage cadastral parcels well; they still do not certify physical street boundaries. The deeded ROW service does not solve the airport support problem. Rail, taxiways, roads and private circulation need separate definitions and source checks there. For water, the Cook Lake source resolves the two Cook-side controls here; DuPage hydro should be evaluated on actual DuPage-side cases.

## Reproduction and next acceptance gate

```bash
.venv/bin/python analysis/scripts/select_chicago_m3_fresh_tiles_2026_09_26.py
.venv/bin/python analysis/scripts/evaluate_chicago_m3_fresh_tiles_2026_09_26.py
.venv/bin/python analysis/scripts/review_chicago_m3_c_m3_01_2026_09_26.py
.venv/bin/python analysis/scripts/pilot_chicago_m3_dupage_row_2026_09_26.py
.venv/bin/python analysis/scripts/pilot_chicago_m3_dupage_hydro_2026_09_26.py
.venv/bin/python analysis/scripts/pilot_chicago_m3_cook_lake_2026_09_26.py
```

Cached acquisitions are verified against receipts. `--fetch` is needed only to acquire a missing bounded remote extract. The evaluator requires the earlier Cook ROW/Road Edge cache described in the [preceding pilot](../chicago_m3_row_land_2026_09_26/README.md).

Next, predeclare a citywide candidate rule for ordinary street ROW, alley reconnection, centerline-guided **parcel-gap** repair, false median rejection, county water masks and nonstreet land exclusion. Test it on a larger, independently traced reference that inventories both all true blocks and missed blocks in selected zones, including private-road, rail, park, water, stacked-road and airport controls. Report boundary displacement, area and shape error, precision and recall by context. The present 11 hand-sketched positives and four controls are too small and incomplete for those estimates. No 77-area M3/M4 table or Chicago-only model was fitted.
