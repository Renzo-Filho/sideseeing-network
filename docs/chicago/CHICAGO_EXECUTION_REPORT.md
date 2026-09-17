# Chicago construction report and continuation handoff

## September 16 continuation: new data processed

The newly supplied Census blocks, LODES WAC, CTA GTFS and hydrography have been processed in a separate [functional extension](CHICAGO_FUNCTIONAL_EXTENSION.md), release `chi_functional_2026_09_16_v2`. It contains population/job densities for 77 Community Areas, six population-weighted bus-service scenarios (462 rows), hydrographic denominator diagnostics and explicit border residuals. **163 independent checks and 41 repository tests passed.** All strict cross-city flags remain false.

Matched Overture `2026-08-19.0` buildings for Chicago and road segments/connectors for both cities have also been acquired; paired candidate reviews are separate from the frozen releases. The older missing-data statements below describe the original v1 baseline. Current pending work concerns business-use jobs sensitivity, common morphology/entity definitions, paired SP companions and acceptance—not absence of blocks, bus schedules or workplace data.

**Date:** 16 September 2026. **Release:** `chi_local_2026_09_16_v1`.

## Purpose and scope

The user supplied additional Chicago data and authorized attribute construction under the harmonization plan. We implemented a separate Chicago pipeline to turn supported local sources into inspectable Community Area measurements, expose missing information, and preserve the frozen SP reference. This is the local construction stage of harmonization, not completion of the common model or a Chicago-to-Brás ranking.

Current definitions and source gates are in [CHICAGO_ATTRIBUTE_DOCUMENTATION.md](CHICAGO_ATTRIBUTE_DOCUMENTATION.md) and [CHICAGO_DATA_REQUIREMENTS.md](CHICAGO_DATA_REQUIREMENTS.md). The updated [harmonization plan](CHICAGO_HARMONIZATION_PLAN.md) retains its original inventory explicitly as history and links to current readiness, rather than leaving obsolete absence claims as current facts.

## Executed work and decisions

| Task | Work performed | Evidence / disposition |
|---|---|---|
| H01 local inventory | Listed all Chicago files; streamed SHA-256 of raw sources, including contextual files; inspected vector schemas, CRSs, CSV rows and names | Published source manifest. Source filenames retained as provided, including `steet_center_lines` typo |
| H01 publisher metadata | Retrieved Chicago building API metadata and attached PDF dictionary; retrieved official municipal transportation renderer; reviewed CMAP classification and CTA/LODES source documentation | Original fetched metadata retained under prepared work; public references in data requirements |
| H02 reporting geography | Validated the exact 77-ID universe, ID-field agreement, metric projection and district overlap; built water/land proxy from CMAP 5000 | Prepared district and land GeoParquet; GeoPackage support layer; area conservation checks |
| H04 geometry helpers | Implemented polygon repair, deterministic whole-object ownership, tiled exact footprint union and category-overlap accounting | `scripts/harmonization/geometry.py`; targeted synthetic fixtures |
| H04 local road preparation | Declared classes/statuses, removed exact normalized duplicate lines, clipped lengths with single boundary ownership, constructed source-code shares | Prepared roads, long-table numerator/denominator, city-length conservation |
| H04 block experiment | Planarized/polygonized the local road selection and calculated whole-enclosure log area, compactness and rectangle elongation | Explicit experimental status; edge exclusion flags. No acceptance as SP-equivalent physical blocks |
| H05 building assessment | Selected ACTIVE polygons, repaired geometry, combined duplicate nonzero IDs, separated positive stories from missing reports | B1 union coverage; B2 median/P90 and coverage; B3 withheld |
| H06 land use | Classified primary CMAP codes into eight broad groups; repaired overlaps; calculated area entropy and shares; retained coverage/secondary-use diagnostics | Distinct from SP count-based U1; no zoning substitution |
| H06 population baseline | Validated all 77 aggregate names against IDs; preserved total population; calculated gross-area density | Published crosswalk and provisional provenance flag; no fabricated block population |
| H08 contract | Saved executable configuration and exhaustive dictionary with acceptance status | `config/chicago_attributes_v1.json`; all strict cross-city flags false |
| H09 local release | Wrote wide/long CSV/Parquet and metric GeoPackage; made missing-family reasons explicit | Release links below; final validation evidence is authoritative |
| Documentation | Added data requirements, complete Chicago attribute definitions, this execution report, release/root navigation and updated harmonization status | Original SP documentation and outputs retained; no raw source replacement or Git publication |

## Issues found, why they matter, and treatment

1. **Download year differs from source vintage.** City building API metadata says August 2015. September 2026 filenames reflect retrieval. The local dataset is treated as a historical municipal baseline; a matched contemporary Overture extraction and source comparison remain required.
2. **Two similarly named stories fields have different meanings.** The publisher dictionary defines `STORIES` as stories and `NO_STORIES_BELOW` as below-ground stories. The truncated export name `no_stories` would be easy to misread. Only positive `stories` enters B2; basement reports are separate audit information.
3. **Zero floor reports are common.** Raw `stories=0` occurs in 392,608 records. These are excluded from reported-floor statistics, with source coverage shown. Defaulting to one would manufacture a distribution. Geographic/selective reporting bias remains unresolved.
4. **Building IDs are not perfectly unique.** Eight raw records share placeholder ID `0`, all outside the ACTIVE selection. ACTIVE ID `882804` occurs twice. Its geometry is unioned into one entity; conflicting numeric attributes are withheld. The final building-entity table must have unique nonzero IDs.
5. **Gross floor area is not supplied reliably.** The publisher labels `BLDG_SQ_FOOTAGE` not actively maintained and `Z_COORD` not maintained. Neither is used for B3 or height; permit fees/costs/events do not repair this gap.
6. **CMAP contains overlapping geometry.** The initial overlap assertion failed in Community Area 01 with 51.0755 m² excess. Rather than relaxing a threshold, the revised algorithm unions same-category pieces and withholds cross-category ambiguous areas. A synthetic overlap fixture checks both cases. Entropy coverage and ambiguous mass are reported separately.
7. **Water classification is a proxy.** CMAP code 5000 describes predominantly water parcels; it is not a precise shoreline inventory. Land-area normalization is labeled accordingly. Geometric conservation passes do not certify a hydrological boundary.
8. **Street taxonomy differs by source.** The city renderer lists expressway/arterial/collector/tiered/ramp/airport-unknown codes; code 4 is retained by raw code because it is not labeled in that renderer. The Cook County code mapping is not imported. Non-N statuses are excluded explicitly pending semantics; no false claim of complete current street coverage.
9. **Planar enclosures are not validated blocks or intersections.** Street crossings at different elevations, dual-carriageway slivers, alleys, parks and missing barriers alter polygonization. M3/M4 are experiments; M2 stays missing until physical-arm and common SP rules pass. An additional endpoint audit found 35,873 node/level groups with zero within-group coordinate spread and 24,846 ≥3-arm candidates (24,652 assigned inside Chicago, 194 outside). The supplementary `tables/m2_endpoint_candidates.csv` supports review and is not promoted into the feature matrix. Reproduce it with `scripts/audit_chicago_road_topology.py`.
10. **Observed-use weighting differs.** The local U1 uses eight area categories from primary CMAP codes; SP uses seven entity-count categories. Secondary uses remain diagnostics; they are not duplicated as extra mass. A harmonized ontology/weighting is a prerequisite to comparison.
11. **The business extract is narrowly filtered.** It contains 20 records for one account and two address strings, including multiple licenses/renewals. It cannot estimate employment. U2 requires workplace job counts and matching geography.
12. **Rail-stop locations are not bus frequency.** The supplied CTA file has 302 directional L stop records. U4 requires bus GTFS/calendar processing and fine population support, not this list.
13. **ACS provenance is incomplete.** Names and total mass can be validated locally, but the CSV's exact source period, MOE and aggregation method are not established. Density is provisional. Aggregate values are not disaggregated into fabricated exact block populations.
14. **Placeholder morphology is not data.** The single `ca=99` Brás row with all zeros is excluded from Chicago processing.

## Generated artifacts

Start with the [Chicago release README](../../analysis/results/Chicago/chi_local_2026_09_16_v1/README.md). It distinguishes feature tables, spatial output and validation evidence. Prepared per-object data stay under `work/prepared/Chicago/chi_local_2026_09_16_v1/`, which is ignored by Git. Published aggregates stay under `results/Chicago/chi_local_2026_09_16_v1/`.

The wide matrix preserves all 13 planned families structurally: M1/M6/B1/B2/U1 local measurements, U3 provisional density, M3/M4 experiments, and null M2/M7/B3/U2/U4 with explicit reasons. M5/U5 remain dropped. No common model-ready matrix is implied.

## Validation and results

The pipeline checks unique IDs, valid metric geometry, gross/land/water conservation, road-length conservation, LUI exclusive-area bounds, footprint union bounds, finite available values and GeoPackage attribute round-trip. Independent validation reconstructs all stored ratios, checks compositions and missingness, compares CSV/Parquet/long/wide/GeoPackage, verifies output checksums, and recomputes B1 by a **full untiled union** in five predeclared pilot Community Areas. It independently reconstructs B2 percentiles there.

Synthetic tests cover metre projection, invalid polygon repair, whole-object tie ownership, overlapping footprints, water masking, no-mass entropy, within-category duplicates and cross-category ambiguity. These test arithmetic and accounting; they do not prove source completeness or SP–Chicago measurement equivalence. **Completed validation:** 36 repository tests passed (six new Chicago tests), and **87 independent release checks passed with zero failures**. Untiled B1 unions and independent B2 P90 calculations agreed in West Town (24), Near West Side (28), South Lawndale (30), Loop (32) and O'Hare (76). The six-panel QA map was generated and visually inspected; it is descriptive and does not certify object-level source completeness.

| Result | Validated value |
|---|---:|
| Community Areas | 77 |
| Feature/diagnostic fields, including five explicit unavailable placeholders | 40 |
| Long-table records | 3,080 |
| Gross / CMAP water-proxy / land-proxy area | 597.6984 / 1.2411 / 596.4573 km² |
| District geometric overlap (roundoff scale) | 0.00000155 m² |
| Selected municipal road records | 54,172 |
| Assigned selected road length | 6,898.6635 km |
| Assigned-vs-city-clipped road difference | −0.02662 m over 6.899 million m; within declared floating-point tolerance |
| Exact duplicate selected line geometries | 0 |
| Planar enclosures / edge exclusions | 19,359 / 505 |
| ACTIVE building records before duplicate-ID union | 820,456 |
| Unique ACTIVE building entities | 820,455 |
| Entities assigned inside / outside Chicago | 820,395 / 60 |
| Invalid ACTIVE building geometries repaired | 9; aggregate area change 0 m² |
| Assigned positive stories reports | 427,924 (52.16% of assigned entities) |
| District stories reporting coverage | 20.90% Near South Side to 76.78% Loop |
| CMAP bbox-read / city-intersecting records | 228,223 / 177,032 |
| Minimum CMAP union coverage / gross area | 94.13%, Oakland |
| Classified-use area / land proxy | 49.42% to 96.96%; excluded support is not silently reassigned |
| Maximum cross-category ambiguous area / gross area | 0.003283% |
| Supplied ACS population conserved | 2,647,621 |

Available computed columns contain no missing/nonfinite values. The only null columns are the five explicitly unavailable principal families. Local numeric completeness is **not** semantic/model readiness. In particular, the water proxy covers only 1.241 km² and still needs a hydrographic completeness check; the small value must not be mistaken for validated total water area.

## Exact continuation instructions

1. Read this report, data requirements and the release dictionary. Do not reuse the old SP loader for Chicago; it correctly enforces SP's 96-ID contract.
2. Confirm `validation/checks.json` says `complete_local_baseline=true`, and `validation/independent_checks.json` has zero failures. If absent, construction/validation is incomplete; inspect `/tmp/chicago_construction.log` and the prepared checkpoints. The construction entry point is `scripts/prepare_chicago.py`; validation is `scripts/validate_chicago_attributes.py`.
3. Preserve the baseline for comparison. New source inputs or changed definitions should receive a new release/config. The current entry point writes its configured release; it is not an immutable release manager. Source caching only reuses the building GeoParquet if its recorded raw hash matches.
4. Next complete common physical-source acquisition, topology and true block pilots; then Census/LODES and CTA service support. Close cadastral semantics separately. Follow the acquisition queue in the requirements document, including DuPage coverage for O'Hare and outside-city transit stops.
5. Reconstruct the necessary SP companions with the **same** accepted definitions, preserving original SP attributes and v2 outputs. Freeze the common family list and coverage gates before examining Chicago-to-Brás ranks.
6. Only then fit the SP-anchored harmonized transform/calibration, apply unchanged to Chicago, and run the proposed source/weight/support sensitivities. These local calculations do not authorize pretending all original features are available.

No commits or pushes were made for this task. Pre-existing SP fixes, notebook edits, and user deletions of the old PDF/helper were left in their existing working-tree state.
