# Chicago M3/M4 reference-zone test, 27 September 2026

## Decision

The ROW + Road Edge + 3 m mapped-alley candidate gives more accurate **selected ordinary block areas** than municipal-centerline enclosures in these three new locations. It is still **not an accepted Chicago M3/M4 source**. The hand-traced reference is approximate, its candidate inventory is incomplete in CHI:57 and CHI:63, one apparent split in CHI:57 has unresolved public-street status, and non-block filtering and citywide seams remain unvalidated. The present M4 compactness calculation is also sensitive to jagged source edges.

These are selected-outline diagnostics. The match counts below are **not** block recall, and this study does **not** estimate candidate precision.

## Frozen design and data

The [zone selection](zone_selection.json) picked six new 700 m-square orthophoto windows from district interiors and distance to prior pilots, with seed 20260927. Candidate geometry was not used for selection. A 400 m-square center core was used for face inventory. The [download receipts](imagery_receipts.json) record the Cook County orthophoto requests and hashes; the [candidate-blind contact sheet](candidate_blind_contact_sheet.jpg) was inspected before candidate outputs. The raw imagery is cached under ignored `analysis/work/chicago_m3_reference_zones_v2_2026_09_27/`.

The [first visual reference](visual_reference_v1.json) contained six CHI:49 ordinary outlines, four CHI:63 ordinary outlines, two CHI:49 rail-edge special controls, and three CHI:76 airport negative points. The [second visual reference](visual_reference_v2.json) added six CHI:57 outlines. The files were frozen with SHA-256 hashes in [v1](reference_freeze.json) and [v2](reference_v2_freeze.json) before their respective candidate evaluations. Their outlines were traced by one analyst from the image and are not survey-grade street edges. The annotation revisions after seeing output are isolated in the [post-freeze adjudication](reference_v2_postfreeze_adjudication.json); the frozen polygons were not silently changed.

The candidate uses Cook road ROW of types 1, 4 and 5, ordinary Road Edge type 1, and a 3 m reopening around mapped Road Edge alleys of type 5. The comparison is `momepy.enclosures` on municipal eligible road centerlines. Both are clipped to the same 700 m window. The [evaluation code](../../../scripts/evaluate_chicago_m3_reference_v2_2026_09_27.py) uses one-to-one maximum-total-IoU assignment with a predeclared 0.5 match cutoff. It reports relative area error, raw compactness, convex-hull compactness, 10 m simplification area change, and bidirectional sampled boundary displacement. The [row-level comparison](reference_v2_comparison.csv) and [summary](evaluation_v2_summary.json) retain exact values.

## Selected ordinary outlines

The following medians use only the matched, admissible hand-traced outlines. The CHI:57 row excludes `CHI57_B1` after the separate street-status review. Absolute area error is relative to the traced area; M4 error is absolute compactness difference on a 0–1 scale.

| Zone | Method | Matched selected outlines | Median IoU | Median absolute area error | Median absolute raw compactness error | Median boundary p95 |
|---|---|---:|---:|---:|---:|---:|
| CHI:49 | Municipal centerlines | 6/6 | 0.758 | 31.9% | 0.024 | 13.5 m |
| CHI:49 | ROW + Road Edge + alley 3 m | 6/6 | 0.908 | 3.4% | 0.085 | 4.9 m |
| CHI:57 | Municipal centerlines | 5/5 | 0.744 | 34.3% | 0.029 | 14.9 m |
| CHI:57 | ROW + Road Edge + alley 3 m | 5/5 | 0.872 | 1.0% | 0.106 | 6.8 m |
| CHI:63 | Municipal centerlines | 4/4 | 0.751 | 28.0% | 0.019 | 16.4 m |
| CHI:63 | ROW + Road Edge + alley 3 m | 4/4 | 0.850 | 7.6% | 0.110 | 9.7 m |

The area advantage is encouraging for M3 in these ordinary settings, but the sample is small and selectively traced. The source comparison does not isolate algorithm effects: the centerline and ROW candidate use different input geometries. **All positive visual references here are four-corner rectangles**, so their compactness is an especially weak shape reference. The raw compactness errors go in the other direction, but they may reflect reference simplification as well as jagged source edges. Convex-hull compactness has smaller median error in CHI:49 and CHI:63 (0.019 and 0.030 for ROW), but reaches 0.077 in CHI:57 and erases genuine indentations. Neither smoothing nor a hull has been approved as the M4 definition.

A post-reference development sweep of 2, 5 and 10 m topology-preserving simplification shows why M4 needs a separate geometry study. Across the 15 selected ROW matches, median absolute compactness error falls from 0.102 raw to 0.095 at 2 m, 0.089 at 5 m and 0.008 at 10 m. At 10 m, median absolute area change is 1.3%, but one CHI:57 face changes by 10.4%. The corresponding centerline compactness error is about 0.026 raw and remains about 0.026 after 10 m. This sweep is **development evidence only**: it uses the same rectangular references to inspect alternatives and may reward erasing real street-edge form. The 10 m value cannot be reported as independent M4 validation or applied citywide without new, carefully traced irregular boundaries and an untouched holdout.

## Reference and topology audit

The core-face inventory exposed a reference defect that a selected-block match count would hide. In CHI:49 the six selected ordinary faces and two rail-edge special controls account for the eight core candidate faces. CHI:76's one core candidate is an airport operating face touching the image halo; the negative points identify its context, not its full operating boundary. CHI:57 has eight core candidate faces against six original traced outlines, leaving two unadjudicated, and CHI:63 has eleven against four, leaving seven unadjudicated. These are **unadjudicated candidates**, not proven false positives. The reference files' original `complete_zones` label is superseded by the post-freeze inventory finding. No pooled precision, recall, or false-positive rate may be calculated from them.

`CHI57_B1` initially appeared to be a candidate merge. The [street-status audit](CHI_57_B1_street_status.json) instead found a 44.0 m municipal W 46th Street stub and corresponding Overture segment; their ends are 64.8 m and 68.5 m from S Tripp Avenue. Visible pavement continuing west is not established as a through public street. A stub may legitimately fail to divide a whole block. The trace is therefore excluded from summary accuracy; it is **not** evidence of a confirmed ROW failure or of private status. Its original row remains in the comparison for audit. The [overlay](CHI_57_B1_merge_diagnostic.png) is an apparent-split diagnostic only.

Rail-adjacent CHI:49 faces and the CHI:76 airport face demonstrate why automatic use of all closed faces would contaminate M3/M4. Their controls were selected before output, but no accepted, independently verified filter for these contexts is yet available. The CHI:76 face touching the halo also confirms that a tile boundary can masquerade as a block boundary unless globally stitched.

## Reproduction and next gate

Run from the repository root with the prepared local data:

```bash
.venv/bin/python analysis/scripts/select_chicago_m3_reference_zones_v2_2026_09_27.py
.venv/bin/python analysis/scripts/evaluate_chicago_m3_reference_v2_2026_09_27.py --version 2
.venv/bin/python analysis/scripts/audit_chicago_m3_chi57_street_status_2026_09_27.py
```

The selector's download step needs the public Cook County imagery service; cached image checksums and freezes should be preserved when reproducing the comparison. The next acceptance test needs a complete, candidate-blind census of *all* ordinary, special and ambiguous faces in each small core, road-status adjudication at questionable connections, and preferably a second reviewer. A subsequent frozen candidate must be tested on new zones after repair/filter choices are fixed. A citywide run then needs seam, exclusion, coverage and Community Area aggregation QA before either M3 area or M4 shape enters the Chicago model.
