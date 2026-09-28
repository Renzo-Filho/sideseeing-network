# Chicago M3/M4 external-source case test — 25 September 2026

## Scope and result

The [source search and CMAP review](../../../../docs/chicago/CHICAGO_BLOCK_EXTERNAL_SOURCE_REVIEW.md) identified OSM roads/grade tags and existing CMAP roadway/rail polygons as possible aids to Chicago physical-block validation. This pilot tested **13 previously imagery-labeled M3/M4 polygons**, a Loop stacked-road control, eight newly frozen cases, and eight low-Census-overlap challenge rows, with one small live OSM API tile per case. Raw XML and source hashes are saved under ignored `analysis/work/chicago_m3_external_sources_2026_09_25/`; [receipts](osm_receipts.json) give the exact URL and retrieval time. CMAP LUI 2023 and the installed 2020 Census blocks were read locally. No all-city OSM extraction or 77-area block rebuild occurred.

The previously frozen area ≥1,000 m² and rectangle width ≥15 m screen agreed with **12/13** earlier labels; it falsely retained the industrial-yard fragment. A screening hypothesis adds a requirement that ≥65% of candidate perimeter lie within 8 m of OSM **public** street lines (excluding `service` and other classes). It agreed with **13/13 earlier selected labels**, including rejection of the industrial-yard fragment. The same selected-case agreement holds at 3, 5 and 12 m buffers. Subsequent cases below show this rule fails on three newly reviewed false enclosures.

| Saved case | Reviewed label | Area (m²) | Census-reference best IoU | Public OSM road near perimeter | Old / new screen |
|---|---|---:|---:|---:|---|
| `H_M3_04` industrial-yard fragment | exclude | 2,462 | .033 | 0% | retain / exclude |
| `H_M3_03` rail-crossing sliver | exclude | 402 | .0009 | 100% | exclude / exclude |
| `H_M3_05` residential/commercial block | plausible | 20,479 | .997 | 100% | retain / retain |
| `H_M3_07` open-space block | plausible | 23,823 | .990 | 100% | retain / retain |

All 29 block-case rows, including service/rail-line support, CMAP overlap and source feature counts, are in [case_source_comparison.csv](case_source_comparison.csv). The Census IoU was independently recomputed from the installed block polygons with the original Community Area ownership rule; the earlier values match the saved candidate queue to floating-point precision. The [validation summary](validation_summary.json) records deduplicated cohort agreements and buffer sensitivity.

## New frozen cases and stress test

After that first pilot, [eight cases](new_case_selection.json) were frozen from four Chicago Community Areas without OSM, Census IoU, imagery or prior physical labels in the selection rule. Cook County 2025 [orthophoto receipts](imagery_receipts.json) and [single-reviewer labels](new_case_visual_labels.csv) show **8/8 visually plausible physical blocks**; both size/width and OSM-edge screens retain all eight. Their Census best IoU ranges from **0.375 to 0.982**, reinforcing that Census overlap is a diagnostic rather than physical truth. This set supplies positive cases only and cannot establish specificity.

A separate [low-Census-overlap challenge set](challenge_case_selection.json) deliberately stressed the screen. Its eight rows contain **six unique polygons**, and one of those six duplicates the previously reviewed industrial-yard polygon under another boundary mode. The five newly seen unique polygons include **two visually plausible blocks** and **three false enclosures**: a road median, a rail-edge strip, and a traffic-island/park-edge wedge. The frozen 8 m OSM-edge rule retains **all three false enclosures**. It rejects the duplicated industrial-yard polygon. At 3 m, the rail-edge strip is rejected too, but the road median and traffic wedge remain false retentions. See [labels](challenge_case_visual_labels.csv) and [cohort counts](validation_summary.json). These deliberate case sets and one analyst's imagery labels are **not a population accuracy estimate**.

This falsifies the proposed OSM public-edge rule as a sufficient physical-block screen. OSM confirms mapped road geometry around the median and traffic wedge but does not establish that the enclosed land is a block. The rail strip likewise has public-road proximity over 83% of its perimeter at 8 m. The road/rail/land distinction needs further topology or a land-surface source before M3/M4 can be accepted. Among 26 unique labeled polygons across all cohorts, 18 are retained by the OSM screen; **3 of those 18 are visually false**. Retained compactness IQR is **0.1685**, versus **0.0583** for the 15 visually plausible unique polygons. These selected-case M4 statistics are not a Community Area estimate.

## What each source actually contributed

- **OSM street lines:** The industrial fragment's perimeter is not near an OSM public road, whereas all five reviewed plausible blocks have full perimeter proximity. Public-road proximity alone does not identify a block: seven excluded small fragments also have near-complete proximity. Area/width and physical-boundary checks remain essential. OSM is a second mapped source, not independently surveyed truth.
- **OSM road-area polygons:** `area:highway` appears as two traffic islands in the Loop control tile and **none** in the original 13 block-case tiles. A few polygons occur in the new/challenge tiles, including two traffic islands near `C_M3_03`, but none overlaps the three newly false retained candidates. It cannot serve as a complete Chicago road-surface mask in this pilot. The Loop tile includes grade tags near the control (bridge, covered/tunnel and distinct layers), corroborating the need to preserve stacked roads; it does not reconstruct a ground-block boundary by itself.
- **CMAP `1511` rail and `1512` roadway parcels:** Both were available in some tiles, but no reviewed candidate had material `1512` overlap. The rail-crossing sliver overlaps rail ROW by about 22%; other rail fragments show little or none. These parcel polygons are useful local flags, not universal enclosure edges. Adding rail ROW edges to the prior candidate builder had already created false narrow polygons.
- **Census blocks:** The five plausible reviewed blocks have best IoU ≥.989; the eight excluded fragments have ≤.0335. These cases were selected partly for high/low reference agreement, so that separation is a **selection property**, not evidence that Census polygons certify physical blocks. Census statistical boundaries may follow invisible lines.

## M4 sensitivity and remaining gates

Among the six polygons retained by the old screen, compactness median/IQR are **0.7297/0.0662** and rectangle elongation median/IQR **1.8512/1.0036**. Removing the industrial fragment changes those selected-case summaries to **0.7322/0.0866** and **1.7145/0.9792**. This demonstrates that a false block can affect shape statistics even when median block area appears stable. These are selected polygons, **not** Community Area M4 estimates.

The new independent cases and challenge controls above expose false retentions, so the 65% OSM-edge rule is rejected as an acceptance rule. A revised method needs an explicit road-surface/median exclusion and a defensible rail-edge treatment, followed by new independent labels, candidate precision, physical-block recall and M4 shape-tail checks across the four sampled areas before any 77-area rebuild. The earlier Census-reference recall at IoU ≥0.5 was only **~11–25%** in no-link modes across these four areas, but Census blocks often subdivide physical blocks; that statistic is *not* physical-block recall. A separately named Census-tabulation-block size/shape feature remains a possible Chicago-only alternative with a changed estimand. **M3/M4 remain unaccepted; no model fit followed.**

## Reproduction

```bash
.venv/bin/python analysis/scripts/pilot_chicago_m3_external_sources_2026_09_25.py --fetch
.venv/bin/python analysis/scripts/pilot_chicago_m3_external_sources_2026_09_25.py
```

The second command uses cached raw OSM XML and does not need network access. The first makes only the specified small map-tile requests and reuses cached tiles when present. Both retain the 2023 CMAP, 2020 Census, 2025 imagery-label and live 2026 OSM vintage differences.
