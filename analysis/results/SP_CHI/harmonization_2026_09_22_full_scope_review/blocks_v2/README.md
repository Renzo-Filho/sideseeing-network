# Paired M3/M4 block-boundary sensitivity — diagnostic only

Reproduce with `.venv/bin/python analysis/scripts/review_block_boundary_pilots_v2.py`; interval logic is `analysis/scripts/harmonization/road_intervals.py` with three focused fixtures in `analysis/tests/test_road_intervals.py`. The eight pilot units, source roads and 250 m extraction buffer match the previous paired fixtures. Polygonized whole enclosures touching the extraction boundary are withheld; remaining polygons are assigned to the district with largest overlap, never clipped to that district. `paired_boundary_sensitivity.csv` has all four modes and per-unit shape statistics. `sp_quadra_reference.csv` contains São Paulo municipal Quadra counts as a city-specific reference, not a shared input.

Modes: (1) all selected mapped streets, (2) remove `subclass=link`, (3) additionally remove whole segments with any bridge/tunnel flag, and (4) retain only portions without scoped `link`, nonzero level, bridge, tunnel, covered or link flags. Mode 4 respects Overture `between` fractions; an absent fraction applies to the whole road. It retains portions with missing status. The whole-segment filter in mode 3 may discard at-grade intervals. Conversely, Overture [level](https://docs.overturemaps.org/schema/reference/transportation/types/level_rule/) is a visual Z-order, so level zero or absent level is not proof of ground-level block boundary. [Road flags](https://docs.overturemaps.org/schema/reference/transportation/types/road_flag_rule/) are also interval-scoped. Both filters are sensitivity scenarios, not accepted physical boundaries.

| Unit | All streets: owned / narrow <6 m | No links: owned / narrow | Whole-segment grade filter: owned / narrow | Interval-aware: owned / narrow |
|---|---:|---:|---:|---:|
| CHI:24 | 719 / 55 | 664 / 50 | 611 / 49 | 606 / 49 |
| CHI:28 | 939 / 25 | 765 / 5 | 607 / 4 | 605 / 4 |
| CHI:30 | 310 / 5 | 294 / 2 | 283 / 2 | 280 / 2 |
| CHI:32 | 453 / 125 | 366 / 96 | 238 / 26 | 184 / 0 |
| CHI:76 | 218 / 5 | 152 / 1 | 114 / 0 | 114 / 0 |
| SP:10 | 243 / 2 | 203 / 0 | 176 / 0 | 176 / 0 |
| SP:30 | 1554 / 13 | 1528 / 10 | 1494 / 10 | 1493 / 10 |
| SP:35 | 922 / 12 | 772 / 6 | 719 / 4 | 719 / 4 |

Loop's median owned enclosure area rises from 921 m² with all streets to 9,591 m² with interval-aware filtering, while Brás rises from 9,661 to 12,965 m². The dramatic Loop change could include both removal of carriageway slivers and loss of real block edges. Zero narrow enclosures is not a validation target. The polygonizer omits rail/water barriers and cannot certify campuses, traffic islands or true physical block perimeters. The municipality's Quadra layer helps diagnose SP, but there is no equivalent shared Chicago reference. M3 identity and M4 shape population remain unaccepted.

**Gate:** inspect and annotate paired polygons against imagery/local references, classify false slivers versus real blocks and missing barriers, then freeze one shared boundary/perimeter rule. Rebuild both cities only after matched fixture review and distribution checks; no automatic narrow-polygon deletion.

## Local reference continuation

The [eight-unit bidirectional reference comparison](reference_fixtures/README.md) found that grade filtering increases agreement among surviving candidate polygons while reducing coverage of Chicago Census blocks and São Paulo municipal Quadra. It rejects the grade-filtered modes as complete physical-block networks; M3/M4 remain unaccepted.
