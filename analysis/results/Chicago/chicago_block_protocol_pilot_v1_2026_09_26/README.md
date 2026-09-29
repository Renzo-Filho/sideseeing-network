# Chicago physical block protocol: small-pilot assessment v1

This is the first stage assessment under the [Chicago physical block protocol](../../../../docs/chicago/BLOCKS_M3_M4.md). It consolidates the already frozen 12-tile development sample, four newly selected CHI:49 motorway-context tiles, Cook parcel support, and the West Veterans Place gap case. The versioned source paths and SHA-256 hashes are in `assessment.json`; `stage_metrics.csv` is reproducible from the script below. `development_candidate_queue.csv` and `new_location_candidate_queue.csv` retain every proposed polygon's size, shape, motorway exposure and **provisional review action**. Neither queue is an accepted block table.

The later [established-method comparison](../chicago_block_method_comparison_v1_2026_09_26/README.md) adds the full 16-clear-sketch centerline/ROW diagnostic, exact source-matched polygonization check, and published shape/area artifact-filter test. The 11-sketch baseline below remains the original development result.

## Evaluation and iteration

| Method stage | Small-sample finding | Decision |
|---|---|---|
| Raw Cook ROW complement | Median IoU 0.386 against 11 independent rough sketches; ordinary blocks often split at alleys. | Improve topology. |
| Reopen mapped alleys | Median IoU 0.827; adding ordinary Road Edge yields 0.824. | Provisional candidate method for ordinary areas. |
| Established centerline baseline | `momepy.enclosures` on municipal streets reaches median IoU 0.758 on the same 11 rough sketches; it beats alley-open ROW on five individual cases. | Retain as a baseline. Sources differ, so this comparison does not isolate algorithm performance or establish overall superiority. |
| Inventory all closed tile components | 26 candidates in 12 tiles; at least nine visually false freeway islands. | Do not promote all components to blocks. |
| Use Cook parcel groups | Two distinct Loop blocks share a group; nine false freeway islands have high parcel support. | Reject parcel-group identity or parcel-presence acceptance. |
| Add motorway-context flag (40 m corridor, ≥30% area exposure) | Flags 9/9 known development islands and 0/11 sketched positives. This threshold was selected on those tiles. | Freeze and test at new locations. |
| Four new CHI:49 locations | 35 candidates, 22 flagged. Two of eight non-block controls fell inside pre-flag candidates and both were flagged. None of five clear residential sketches was flagged, and each had IoU ≥0.5. Two other sketches have ambiguous boundaries; the sketch set omitted visible blocks. | Supports a motorway **flag**, not citywide accuracy or automatic exclusion. |
| Named-street gap | West Veterans Place appears in municipal/OSM lines but lacks Cook ROW/Road Edge; a candidate merges across it. | Gap detection/repair required before release. |

The development and new-location samples intentionally stress known failure modes. They do **not** have a complete independent true-block census. Accordingly, there are no reported candidate precision/recall, citywide performance claims, 77-area block totals, or accepted M3/M4 model features. The [frozen development result](../chicago_m3_candidate_v1_2026_09_26/README.md) and [new-location result](../chicago_m3_motorway_holdout_2026_09_26/README.md) contain maps and case details.

The candidate-size distribution is sensitive to filtering: the median in the 12 development tiles changes from **5,809 to 14,441 m²** after the provisional motorway flag; in the four new locations it changes from **2,339 to 14,288 m²**. These are selected tile-contained land-complement components under the pilot area definition, not finalized gross-enclosure M3 or citywide estimates. They show why false islands cannot be left in the model and why a filter must also be checked for accidentally removing true blocks.

## Immediate next protocol cycle

1. Build a complete, blind reference inventory in a small set of large zones spanning ordinary streets, motorway-adjacent true blocks, parks, rail, private circulation and O'Hare, with every true and missed block enumerated.
2. Repair the West Veterans Place gap from a documented property-side edge or plat and verify the rule on other named street gaps.
3. Adjudicate the curving-street and cul-de-sac cases; keep their original rough sketches and mark ambiguity rather than retrofitting reference truth.
4. Freeze a new candidate version, then compare it with the named `momepy.enclosures` baseline and current ROW baseline on a fresh holdout. Include source-matched ablations to separate input coverage from algorithm effects. If the reference is complete, calculate precision, recall, split/merge, boundary displacement and M4 error.

Reproduce the assessment without network access:

```bash
.venv/bin/python analysis/scripts/evaluate_chicago_m3_momepy_baseline_2026_09_26.py
.venv/bin/python analysis/scripts/summarize_chicago_block_protocol_pilot_v1.py
```

The script checks candidate counts, one-to-one file joins, the frozen motorway rule and reference ambiguity before writing its tables. Upstream extraction scripts and raw-source receipts are linked from the two source result directories above.
