# Chicago M3/M4 candidate inventory and failure audit — 26 September 2026

## Decision

**Do not accept M3 block polygons or M4 shape for the Chicago-only model yet.** The Cook property-side road masks with mapped alleys reopened fit the 11 earlier, independently sketched ordinary blocks well, but they also create many false freeway/interchange land enclosures. Cook parcel groups cannot certify a physical block or reject those false polygons. A named ordinary street remains missing from Cook ROW and Road Edge, so some true blocks can merge. This audit establishes concrete failure modes before any 77-area release.

## Declared diagnostic candidate construction

The [earlier fresh-tile selection](../chicago_m3_fresh_tiles_2026_09_26/README.md) fixed 12 locations in six Chicago Community Areas before imagery or candidate viewing. This continuation inventories **all tile-contained land components** in those same 320 m squares under a declared diagnostic rule: subtract Cook active road ROW and ordinary Road Edge from the tile; reopen mapped Road Edge `TYPE=5` alleys using a 1 m buffer; subtract cached Cook Lake polygons where available; retain closed tile components of at least 1,000 m². These are trial parameters, not an accepted block definition. Components touching the tile boundary are excluded from the inventory because their whole-block area is unknown.

The rule generates **26 candidates** in seven tiles. The remaining five tiles contain no qualifying tile-contained components. `component_inventory.csv` contains their geometry, area, perimeter and compactness; `*_inventory.png` overlays each tile. `inventory_review.csv` links 11 candidates to the frozen positive imagery sketches. Image review identifies **nine unambiguous grass/woodland islands inside the CHI:49 freeway/ramp complex** (`P05`–`P13`). Six other candidates remain unadjudicated. Thus at least 9/26 (34.6%) of this deliberately selected candidate inventory are visibly false. This is **not a citywide precision estimate**: the sketches do not cover every true block, and one analyst reviewed the freeway islands after viewing candidate outlines. It is enough to fail the present construction rule. The previously documented West Veterans Place ROW gap is an independent merge failure.

## Parcel and motorway diagnostics

We scanned all 625 locally held Cook parcel parquet parts and retained 2,211 BaseParcels near the 12 tiles. Each of the 11 positive sketches overlaps one dominant seven-digit PIN group, with median group coverage of the rough sketch 0.771. However, the **two distinct Loop blocks R10 and R11 share group `1716212`**, so the group is not a physical block ID. At the negative controls, both the freeway median and airport open land have a PIN group. Every one of the nine false freeway islands is **95.6%–99.2% covered by a dominant parcel group**. Parcel presence or grouping therefore cannot reject them. The first seven PIN digits may represent a tax block or quarter section, and the cached groups were clipped to a 50 m expansion of the tile set. See `parcel_positive_comparison.csv`, `parcel_negative_comparison.csv`, `parcel_candidate_support.csv` and `parcel_summary.json`.

We also measured each candidate's area within 15, 25 and 40 m of the locally held Overture 2026-08-19 `class=motorway` centerlines. On this **development sample**, a 40 m corridor and 30% area-exposure threshold flags all nine obvious freeway islands and none of the 11 sketched blocks; it also flags two unadjudicated candidates. At 25 m and 30%, it flags eight of nine islands, none of the 11 sketched blocks and one unadjudicated candidate. The threshold was examined **after** the islands were identified. It is a hypothesis for a new holdout, not a validated exclusion rule. A legitimate street block beside a freeway could also have motorway exposure. `motorway_context.csv` preserves all candidate values, and `motorway_summary.json` records 19 nearby motorway segments.

## What must be tested next

1. Freeze the **physical** rule: ordinary through-street boundaries divide blocks; mapped interior alleys reconnect; motorway ramps and medians, railway yards, water and airport operating/open land are excluded; parks bounded by ordinary streets remain eligible. Use property-side road geometry for area and shape. Resolve the legal/physical status of private circulation and grade-separated paths case by case.
2. Treat a Cook parcel-group change or a municipal/OSM road without ROW as a **gap alert**. The West Veterans Place omission needs a width and closure method supported by an independent road edge, recorded plat or orthophoto trace. A PIN prefix or fixed centerline buffer cannot be promoted to a physical boundary automatically.
3. Freeze a motorway-island classifier before a **new** geographically spread, independently traced sample. Include ordinary blocks beside expressways, multiple interchanges, parks, rail, private access, water and both Cook and DuPage sides of O'Hare. Inventory all true and missed blocks in each reference zone, then measure candidate precision/recall, boundary displacement, area error and M4 shape error by context.
4. If that passes, construct the citywide 77-area table with source coverage and unresolved-case flags, then decide whether M3/M4 enter the Chicago-only contract. M4 depends on accepted M3 boundaries.

The [next four-tile motorway stress check](../chicago_m3_motorway_holdout_2026_09_26/README.md) was run after this audit. Its frozen 40 m/30% motorway flag removes candidate land at two freeway landscape controls and leaves seven positive-sketch matches unflagged, but two sketches have ambiguous boundaries and the sketch set missed visible blocks. It therefore supports further method work without satisfying the independent complete-inventory gate.

Reproduce this continuation after the earlier caches exist:

```bash
.venv/bin/python analysis/scripts/inventory_chicago_m3_tiles_2026_09_26.py
.venv/bin/python analysis/scripts/evaluate_chicago_m3_parcel_references_2026_09_26.py
.venv/bin/python analysis/scripts/evaluate_chicago_m3_motorway_context_2026_09_26.py
.venv/bin/python analysis/scripts/review_chicago_m3_inventory_2026_09_26.py
```

Source context: [Cook ROW](https://gis.cookcountyil.gov/traditional/rest/services/RightOfWay_Cadastre/MapServer/2025), [Cook Road Edge](https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/7), [Cook Lake polygons](https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/8), and locally held Overture transportation release manifest. [Cook's ROW description](https://catalog.data.gov/dataset/rightofway) identifies digitized tax-exempt platted rights-of-way; it is not a complete current ground-road survey. [Cook's route hierarchy service](https://gis.cookcountyil.gov/traditional/rest/services/DOTHlayers/MapServer/layers) provides an independent expressway/tollway class to consider for the next gate, but is linework rather than a complete motorway land polygon. No 77-area M3/M4 table or Chicago-only model fit was changed.
