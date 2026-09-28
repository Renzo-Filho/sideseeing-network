# Paired M2 source-topology review — diagnostic only

Reproduce with `.venv/bin/python analysis/scripts/review_junction_complexes_v2.py`, `.venv/bin/python analysis/scripts/review_junction_link_context_v2.py`, and `.venv/bin/python analysis/scripts/review_junction_fixture_sources.py`. Shared candidate logic is in `analysis/scripts/harmonization/junctions_v2.py`; four fixture tests are in `analysis/tests/test_junctions_v2.py`. The files `pilot_summary.csv`, `short_source_links.csv`, `road_context_summary.csv`, `linked_components.json`, and `fixture_source_evidence.json` retain the complete pilot evidence. No H1–H3 source was changed.

A pair is linked only when both source connector IDs occur consecutively on one selected Overture road within 20 m along the road and 20 m straight-line distance. A disjoint-set pass groups linked pairs; groups over 35 m diameter are flagged. This is source topology, **not** a physical-arm deduplication rule. Selected roads still include ramp/link and grade-separated segments; `road_context_summary.csv` flags these as reasons not to promote linked pairs automatically. Segment-level grade flags may cover only part of a segment, so this context summary is conservative.

| Unit | Near pairs ≤10 m | Near pairs with short source link | All short source links | Short links on possible ramp/grade road |
|---|---:|---:|---:|---:|
| CHI:24 | 61 | 55 | 94 | 2 |
| CHI:28 | 54 | 50 | 189 | 4 |
| CHI:30 | 1 | 1 | 9 | 1 |
| CHI:32 | 71 | 34 | 114 | 40 |
| CHI:76 | 5 | 5 | 45 | 5 |
| SP:10 | 13 | 13 | 51 | 7 |
| SP:30 | 198 | 180 | 453 | 10 |
| SP:35 | 52 | 40 | 187 | 5 |

The [Loop close-pair map](../fixture_maps/loop_close_4arm_pair.png) and raw source record show a 2.49 m Euclidean pair on different levels: upper Randolph/Columbus is `+1` and bridge-flagged; lower Randolph/Columbus is `-1`/`-2` and covered. They must not be merged by distance. The [Brás pair map](../fixture_maps/bras_close_4arm_pair.png) shows an 8.28 m pair connected by a same-level Rua Monsenhor Andrade source span with no bridge/tunnel flag. It is a plausible linked complex, but its physical arm count still needs local annotation. Overture documents connectors as physical segment connections, while [level rules](https://docs.overturemaps.org/schema/reference/transportation/types/level_rule/) and [road flags](https://docs.overturemaps.org/schema/reference/transportation/types/road_flag_rule/) may be scoped to intervals.

**Gate:** label physical junction identity and each incident arm in matched divided-road, ramp, T, loop and stacked-road fixtures. Then specify scoped grade checks and arm deduplication, test threshold stability and independently reconstruct paired district counts. M2 stays unaccepted.
