# West Veterans Place boundary-repair and topology check, 27 September 2026

**Decision:** A centerline-guided *nonparcel corridor* can separate the known merged `C_M3_01` land face in this local case, without cutting the six target BaseParcels. The earlier apparent failure at 8–12 m was a vector-topology artifact from subtracting the existing road mask before union. This is a **case repair diagnostic**, not a validated general rule or accepted M3/M4 block.

## Evidence and construction

West Veterans Place is a named municipal street (`trans_id=154550`, about 98 m), visible in the 2025 Cook orthophoto. The [2022 classified LiDAR pilot](../chicago_m3_lidar_point_pilot_2026_09_26/README.md) found a class-11 road trace along its 71 m county-mask gap. The six BaseParcels on the block side have PINs `1309323015`–`1309323020`; their union supplies a **cadastral anchor**, not independent accuracy truth. The working 2D street barrier is active-road Cook ROW plus ordinary Road Edge, with mapped alleys reopened by 3 m. All geometry is evaluated in EPSG:26916.

For each search width 6, 8, 10, 12, 15 or 20 m, we intersect the municipal line buffer with the local space outside Cook BaseParcels, then union that potential street corridor with the existing barrier. The face containing the greatest portion of the six-parcel anchor is scored. The [full sensitivity table](repair_sensitivity.csv) also repeats ROW-only and 1 m alley variants, tests operation order, and retains the face geometry. [Overlay](repair_sensitivity_overlay.png): red is the land face, yellow is the six-parcel union and cyan is the municipal line.

| ROW + Road Edge, 3 m alley opening | Baseline | 6 m search | 8–20 m search |
|---|---:|---:|---:|
| Selected face area | 16,617 m² | 5,668 m² | 5,585–5,586 m² |
| Face reaches the 150 m analysis boundary | Yes | No | No |
| Face / six-parcel union IoU | 0.333 | 0.960 | 0.973–0.974 |
| Parcel-union area retained in face | 97.44% | 97.44% | 97.44% |

The same block-side face isolates under ROW-only and 1 m alley variants when the nonparcel corridor is **unioned directly**. The 8–20 m range is stable in this local topology, but it is a *search envelope*, not an inferred street width. The parcel-overlap values are expected to be high because parcels define the candidate corridor; they cannot be used as independent boundary accuracy. About 2.56% of the six-parcel union remains outside the ROW + Road Edge face even after repair, due to existing mask/parcel disagreement. This matters for precise M3 area and M4 perimeter.

## Why the prior width test appeared unstable

The earlier experiment first calculated `corridor.difference(existing_ROW)` and then unioned the result back with `existing_ROW`. In exact set arithmetic that is equivalent to a direct union. In the actual vector overlay, the masks differ from direct union by only about **7–8 × 10⁻⁹ m²**. Nevertheless, for ROW-only plus 1 m alley reopening, that nearly zero-area numerical seam leaves the parcel-anchored face connected to a 15,390–15,715 m² exterior component at 8, 10 and 12 m. At 6, 15 and 20 m it separates. This reproduces the [older sensitivity result](../chicago_m3_row_land_2026_09_26/c_m3_01_parcel_orthophoto_summary.json).

Direct union avoids the redundant subtraction and isolates the same parcel-anchored face at every tested width. Snapping the older mask to a 0.01 m coordinate grid also closes the seam at 8–12 m (face area about 5,646 m²). A 0.1 m grid also closes it, with larger shape perturbation. **The repair implementation should union directly and use a frozen precision grid for robustness**, while auditing any change the grid causes to small true features. This is a numerical-topology finding, not evidence that a particular buffer width captures the legal street edge.

## Release implication

This case now has a plausible, reproducible split. It still requires an independently checked property-side boundary and street status, plus a test that the same procedure does not split legitimate parcels or create false blocks at other named-street gaps. The six parcels and the rough visual outline were known before this repair; this case is development data. Freeze a rule and score it on complete unseen zones before accepting Chicago M3/M4. Any citywide implementation should preserve the unrepaired geometry and reason-coded repair record.

Reproduce with:

```bash
MPLCONFIGDIR=/tmp/mpl-veterans-repair .venv/bin/python analysis/scripts/pilot_chicago_m3_veterans_repair_2026_09_27.py
```

The [summary](summary.json) records source hashes, parcel-union hash and all sensitivity measurements. The script reads cached official parcels, ROW, Road Edge, municipal roads and the saved orthophoto; it does not download data.
