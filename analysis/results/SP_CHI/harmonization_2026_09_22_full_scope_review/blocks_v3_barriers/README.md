# Paired rail and water boundary pilots — 22 September 2026

This checkpoint tests the next M3/M4 hypothesis after the [eight-unit reference review](../blocks_v2/reference_fixtures/README.md) rejected whole-grade and interval-aware road filters as complete block networks. It **does not accept** a physical-block definition or rebuild the 96/77 family table.

`analysis/scripts/review_block_barrier_pilots_v3.py` polygonizes the same no-link street baseline with (a) at-grade Overture `standard_gauge` rail line portions, (b) the boundary of the local water-polygon union, and (c) both, in all eight pilots. Explicit nonzero rail levels and bridge/tunnel/covered intervals are excluded before reprojection; unknown levels remain candidates. The water inputs are Chicago `Hydro_20260916.geojson` and São Paulo `massa_d_agua.gpkg`; these are city-specific local masks with different vintages and coverage. All lines are diagnostic; a rail centerline is not automatically a right-of-way edge and a shoreline can enclose water. Whole polygons retain largest-overlap district ownership and are compared bidirectionally with local Census blocks or municipal Quadra at best IoU ≥ 0.50. The 32 rows and polygons are saved in `paired_barrier_sensitivity.csv` and unit/mode Parquet files.

Adding individual rail centerlines causes severe over-segmentation in places. In CHI:28 it changes **765 to 1,404** owned candidate enclosures and **5 to 359** under 6 m width; candidate-reference match falls **.634 to .350** while reference-candidate match rises only **.534 to .542**. In Brás, 203 candidates and no narrow enclosures become 229 and 10, with no reference-coverage gain. Rail centerlines are therefore **rejected as direct block boundaries**.

Adding shorelines creates water polygons. In SP:30, the 1,528 no-link candidates become 1,793, of which **262** have more than half their area in the water mask. `analysis/scripts/review_block_water_land_filter_v3.py` removes majority-water polygons *only from saved shoreline variants* and recomputes reference coverage; `land_only_sensitivity.csv` preserves those results. This threshold is a diagnostic, not a frozen exclusion rule.

| Unit | No-link candidate / reference match | Shoreline + land-only candidate / reference match | Land-only candidate count |
|---|---:|---:|---:|
| CHI:32 | .372 / .397 | .394 / .452 | 393 |
| CHI:28 | .634 / .534 | .638 / .540 | 768 |
| CHI:76 | .316 / .197 | .313 / .209 | 163 |
| SP:10 | .690 / .915 | .690 / .915 | 203 |
| SP:30 | .795 / .820 | .794 / .821 | 1,531 |
| SP:35 | .690 / .945 | .689 / .945 | 774 |

The other two units and full-precision values are in the CSV. Shoreline plus land-only is a **promising bounded sensitivity**, particularly in Loop, but remains unaccepted: it can generate small land slivers, depends on local water masks, and does not resolve divided carriageways, rail yards or nonstreet barriers.

`analysis/scripts/review_rail_corridor_pilots_v3.py` tests dissolved rail corridors 10/20/30 m wide in CHI:28, CHI:32, SP:10 and SP:30. The 20 m corridor reduces CHI:28's added narrow enclosures from 359 (centerlines) to 24, but candidate-reference match is still **.565** versus **.634** baseline and reference coverage **.533** versus **.534**. In Brás it produces two narrow enclosures and lowers reference coverage **.915 to .908**. `rail_corridor_sensitivity.csv` and saved polygons retain all 12 scenarios. Width is an arbitrary pilot parameter, not a defensible right-of-way measurement. **No tested rail corridor is promoted to M3/M4.**

Next: map the unmatched physical block edges against verified ground-level street and rail rights-of-way, inspect water-adjacent land polygons and true carriageway slivers in paired imagery, and define one shared treatment that preserves reference coverage. Keep M3/M4 and dependent M2 fit gates open.
