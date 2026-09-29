# Graph Report - sideseeing-network  (2026-09-29)

## Corpus Check
- 241 files · ~168,842 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: .zip 5, (none) 4, .ipynb 2)

## Summary
- 1171 nodes · 3107 edges · 63 communities (55 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 90 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- SP Urban Model & Distances
- Block/Rail Boundary Review + Roads
- U1 POI/OSM Pilots
- Curio Graph Install Scripts
- Docs & M3 Provisional Faces
- M3 Gap Audits & H4 Review
- SP Input Preparation
- Chicago Functional Accessibility
- M3 DuPage Pilots
- Chicago Cadastral Acquisition
- SP Buildings & Curio Catalog
- U1 Source Samples
- SP v3 Attribute Modules
- M3 Fresh Tiles & Holdouts
- Review Queue & Dashboard Data
- Curio Model Nodes (B/M/U)
- M3 External Sources
- M3 Complete Zones & Alley Repair
- Viz Dashboard Spec
- Chicago Preparation & Geometry Tests
- M3 Established Methods
- Chicago Employment
- M3 LiDAR Pilots
- M3 Veterans Repair
- SP Attribute Core & Tests
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 60
- Community 62

## God Nodes (most connected - your core abstractions)
1. `transform()` - 26 edges
2. `source_geometries()` - 25 edges
3. `PROTOCOL` - 19 edges
4. `polygonal()` - 17 edges
5. `SP attribute documentation` - 16 edges
6. `match_best()` - 15 edges
7. `largest_overlap()` - 14 edges
8. `summarize_cells()` - 14 edges
9. `compute_distances()` - 14 edges
10. `chicago_only_8_family_candidate_v0 model` - 14 edges

## Surprising Connections (you probably didn't know these)
- `Chicago attributes doc` --semantically_similar_to--> `SP attribute documentation`  [INFERRED] [semantically similar]
  docs/chicago/ATTRIBUTES.md → docs/sp/ATTRIBUTES.md
- `Work evidence README` --conceptually_related_to--> `M6: unclassified streets become Local`  [INFERRED]
  analysis/work/evidence/README.md → docs/DECISIONS.md
- `Work evidence README` --conceptually_related_to--> `U2 job allocation: area-first with unlocated bucket`  [INFERRED]
  analysis/work/evidence/README.md → docs/DECISIONS.md
- `PROTOCOL` --references--> `Chicago 77 Community Areas`  [EXTRACTED]
  docs/PROTOCOL.md → README.md
- `PROTOCOL` --references--> `Sao Paulo municipal districts (Bras=10)`  [EXTRACTED]
  docs/PROTOCOL.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Curio three-lane feature dataflow** — curio_lanes, curio_dataflow, chicago_only_8_family_candidate_v0 [EXTRACTED 0.95]
- **Chicago M3/M4 block pilot scripts** — analysis_scripts_evaluate_chicago_m3_fresh_tiles_2026_09_26, analysis_scripts_evaluate_chicago_m3_momepy_baseline_2026_09_26, analysis_scripts_build_chicago_m3_provisional_faces_2026_09_27, analysis_scripts_evaluate_chicago_m3_reference_v2_2026_09_27 [INFERRED 0.85]
- **Survey document set** — docs_survey_advisor_brief, docs_survey_data_resource_survey, docs_survey_experiment_ledger, docs_survey_methods_field_guide, docs_survey_readme [EXTRACTED 0.90]

## Communities (63 total, 8 thin omitted)

### Community 0 - "SP Urban Model & Distances"
Cohesion: 0.06
Nodes (47): Download 2022 RAIS formal jobs for São Paulo from Base dos Dados, aggregated by…, dump(), Versioned, immutable SP model release, including prespecified robustness…, run_model(), Compact descriptive maps; not a similarity-model visualization., Descriptive QA maps for the functional extension, not a similarity ranking., Plot the six-feature SP attribute pilot bar chart (Brás, Itaim Bibi, Grajaú)…, Render local-vs-Overture street maps for the two M1 coverage outliers. (+39 more)

### Community 1 - "Block/Rail Boundary Review + Roads"
Cohesion: 0.07
Nodes (45): largest_overlap(), Metric geometry helpers with deterministic ownership and exact union areas., Whole-object owner by positive intersection area; ties use smallest district ID., _active(), boundary_parts(), Interval-aware road portions for diagnostic block-boundary construction.…, Retain source-road parts lacking explicit link or elevated/covered status.…, _span() (+37 more)

### Community 2 - "U1 POI/OSM Pilots"
Cohesion: 0.06
Nodes (44): fetch(), main(), Check only public Cook parcel-service metadata and seven saved M7 keys. Raw…, main(), rank(), Preselect seven named POI cases from the six-tile OSM/Overture comparison. The…, main(), Inspect nearby pinned Overture records for selected OSM-only POIs. This tests… (+36 more)

### Community 3 - "Curio Graph Install Scripts"
Cohesion: 0.06
Nodes (42): Install one Chicago feature per Curio node, preserving agent sessions and…, chart_specs(), edge(), main(), mutate(), Install four linked Vega views on the Chicago copy for interaction testing., uid(), main() (+34 more)

### Community 4 - "Docs & M3 Provisional Faces"
Cohesion: 0.06
Nodes (56): Curio nodes README, Analysis workspace README, build_unit(), digest(), main(), polygon_parts(), Path, Build a lossless provisional Chicago land-face inventory from cached Cook… (+48 more)

### Community 5 - "M3 Gap Audits & H4 Review"
Cohesion: 0.05
Nodes (32): main(), Publish H1–H3 candidate companions, preserving all model acceptance gates., digest(), line_parts(), main(), Path, Screen municipal named streets absent from Cook ROW/Road Edge masks., main() (+24 more)

### Community 6 - "SP Input Preparation"
Cohesion: 0.10
Nodes (30): main(), Seal candidate construction receipts without accepting or fitting a common…, sha(), assign_polygons(), checkpoint_valid(), con(), copy(), districts() (+22 more)

### Community 7 - "Chicago Functional Accessibility"
Cohesion: 0.10
Nodes (23): active_services(), allocate(), population_grid(), Independent Chicago functional-support primitives; metric inputs required., Gross-area allocation, retaining whole-block denominators and outside residuals., Maximum stop supply per route/direction, summed over route/directions., Reuse one spatial join for all windows; preserve route/direction maxima., seconds() (+15 more)

### Community 8 - "M3 DuPage Pilots"
Cohesion: 0.10
Nodes (23): pixel_point(), main(), Run established momepy street-enclosure baseline on frozen Chicago tiles., main(), Compare Cook BaseParcel PIN groups with frozen, rough imagery references., get(), main(), Bounded Cook Lake polygon check for fresh Loop and O'Hare water controls. (+15 more)

### Community 9 - "Chicago Cadastral Acquisition"
Cohesion: 0.13
Nodes (27): main(), One end-to-end Curio executor check using the last successful feature outputs., run(), module(), Construct one feature from Curio's installed catalog files, outside the UI., Stream source-year CSV exports and retain only Chicago parcel-linked rows. Bulk…, run(), matches() (+19 more)

### Community 10 - "SP Buildings & Curio Catalog"
Cohesion: 0.11
Nodes (26): main(), metadata(), Export Chicago model inputs into a local Curio Data Catalog. This script adds…, Replace an unsupported, directory-pointing GeoJSONL manifest with GeoParquet., register(), repair_microsoft(), get_item(), intersects_bbox() (+18 more)

### Community 11 - "U1 Source Samples"
Cohesion: 0.13
Nodes (24): accepted_sp_uses(), main(), normalized_entropy(), GeoDataFrame, Geometry, Exact six-unit U1 land support check; no citywide U1 construction., raw_sp_lots(), source_partition() (+16 more)

### Community 12 - "SP v3 Attribute Modules"
Cohesion: 0.08
Nodes (9): polygon_only(), fiscal(), use_category(), classes(), normalize_code(), range_compatible(), gc, home_renzo_documents_github_sideseeing_network_analysis_scripts_sp_v3_init_py (+1 more)

### Community 13 - "M3 Fresh Tiles & Holdouts"
Cohesion: 0.18
Nodes (22): audit(), fetch_buildings(), main(), Diagnostic only: intersect Overture buildings with saved motorway candidates., main(), motorway_corridor(), Apply frozen 3m alley opening to prior CHI:49 motorway challenge tiles., components() (+14 more)

### Community 14 - "Review Queue & Dashboard Data"
Cohesion: 0.12
Nodes (7): Construct selected installed-Curio features and execute the three model stages., Join citywide face diagnostics into an exhaustive, non-destructive review queue., Reproducible paired M1/M6 scope and local-baseline audit., Independent arithmetic and lineage checks for paired barrier diagnostics., Cross-artifact checks for local rail and matched M1/M6 scope review., numpy, pandas

### Community 15 - "Curio Model Nodes (B/M/U)"
Cohesion: 0.12
Nodes (7): main(), Paired road candidates and Chicago footprint pilots; explicitly not model…, check(), main(), Independent release checks and pilot reconstruction for Chicago's local…, geopandas, shapely

### Community 16 - "M3 External Sources"
Cohesion: 0.15
Nodes (18): endpoints(), main(), Check the candidate-blind CHI57_B1 outline against street source extent., main(), Measure Overture motorway exposure around tile-contained land components., transform(), fetch(), fraction_near() (+10 more)

### Community 17 - "M3 Complete Zones & Alley Repair"
Cohesion: 0.24
Nodes (19): main(), Diagnostic alley-opening width sweep on the frozen valid development cores., compactness(), core_polygon(), digest(), main(), match_reference(), parts() (+11 more)

### Community 18 - "Viz Dashboard Spec"
Cohesion: 0.10
Nodes (19): labelFontSize, titleFontSize, config, axis, title, view, name, data (+11 more)

### Community 19 - "Chicago Preparation & Geometry Tests"
Cohesion: 0.14
Nodes (12): exclusive_category_areas(), normalized_entropy(), Union within categories; withhold area contested by different categories., add(), dump(), main(), metric_polygons(), Build a transparent local Chicago baseline. Does not fit cross-city similarity.… (+4 more)

### Community 20 - "M3 Established Methods"
Cohesion: 0.15
Nodes (16): artifact_index(), compactness(), digest(), fit_published_threshold(), iou(), main(), ndarray, Path (+8 more)

### Community 21 - "Chicago Employment"
Cohesion: 0.20
Nodes (8): allocate_jobs(), exclusive_support(), partition_block(), Conservative land-use support and whole-block employment accounting., Ascending district ownership plus an explicit outside-city polygon., Union exact primary codes; withhold cross-code conflicts, including excluded…, EmploymentTests, Counterexamples for whole-block ancillary employment support.

### Community 22 - "M3 LiDAR Pilots"
Cohesion: 0.20
Nodes (16): audit(), bridge_profile(), fetch_member(), main(), parse_header(), DataFrame, Path, Extract one Cook 2022 LAS ZIP member and audit point classes in M3 faces. (+8 more)

### Community 23 - "M3 Veterans Repair"
Cohesion: 0.21
Nodes (14): isolated(), main(), pieces(), Screen frozen named-street gap alerts for parcel-guided repair effects. This is…, draw(), faces(), local_parcels(), main() (+6 more)

### Community 24 - "SP Attribute Core & Tests"
Cohesion: 0.13
Nodes (4): block_metrics(), entropy(), Features, AttributeInvariants

### Community 25 - "Community 25"
Cohesion: 0.30
Nodes (17): B1 building footprint coverage, B2 floor count, B3 constructed-area intensity, M1 street density, M2 intersection-density proxy, M3 block size, M4 block shape, M6 street-class composition (+9 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (17): SP U4 bus-only correction, SP model validation audit, Urban similarity model implementation plan, Harmonization execution log, SP-Chicago harmonization plan, SP model corrections and revalidation, Experiment ledger, Methods field guide (+9 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (12): log(), main(), cached(), Checkpointed N10 attribute construction, pilots before municipal release. No…, validate(), population_points(), transit_access(), linear_parts() (+4 more)

### Community 28 - "Community 28"
Cohesion: 0.20
Nodes (11): clipped(), main(), Paired M1 linework proximity against each city's independent local baseline.…, sampled_near_fractions(), main(), parts_for(), Attribute city-local M1 linework gaps by published local road class., main() (+3 more)

### Community 29 - "Community 29"
Cohesion: 0.16
Nodes (10): Generate pilot input QA maps; no model attributes., Small accounting and service-policy counterexamples., Small fixtures for real spatial accounting failure modes., Scientific boundary/identity tests; no model attributes are constructed., Boundary and frequency conservation tests for preparation, not model attributes., importlib_util, sp_v3, sys (+2 more)

### Community 30 - "Community 30"
Cohesion: 0.24
Nodes (7): choose_weights(), main(), check(), save(), normalize(), M2 approved proxy and U2 mass-conserving experiments; no model attributes., AllocationTests

### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (7): linked_components(), Topology-constrained candidate junction complexes for paired review. This…, Return unique candidate pairs joined consecutively on one short road span. A…, Group linked candidates; flag chains larger than a single local complex., short_connector_links(), fixture(), JunctionComplexFixtures

### Community 32 - "Community 32"
Cohesion: 0.27
Nodes (11): guard(), main(), Acquire Cook ROW and Road Edge per Chicago Community Area with disk guards. The…, size_raw(), fetch_area(), get_json(), load_area(), main() (+3 more)

### Community 33 - "Community 33"
Cohesion: 0.29
Nodes (11): allocate_jobs(), exclusive_support(), partition_block(), Conservative land-use support and whole-block employment accounting., Ascending district ownership plus an explicit outside-city polygon., Union exact primary codes; withhold cross-code conflicts, including excluded…, polygonal(), dump() (+3 more)

### Community 34 - "Community 34"
Cohesion: 0.23
Nodes (9): Disjoint tiles avoid summing overlapping building areas or double-counting…, union_coverage(), batches(), inspect_city(), main(), Paired Microsoft footprint/height pilots, with unchanged Overture B1 reference., main(), Full Chicago footprint union, paired SP reuse and independent SP pilot checks. (+1 more)

### Community 35 - "Community 35"
Cohesion: 0.26
Nodes (8): native_cells(), Native-grid GHSL aggregation; no building-level interpretation or interpolation., digest(), main(), Paired GHSL pilots; report candidate statistics, never fit a model., digest(), main(), Full paired GHSL candidates; no model fitting or acceptance.

### Community 36 - "Community 36"
Cohesion: 0.31
Nodes (3): Allocate extensive mass uniformly; average intensive values by valid area. Zero…, summarize_cells(), NativeRasterAccounting

### Community 37 - "Community 37"
Cohesion: 0.24
Nodes (4): expected_frequency(), time_seconds(), transit(), PreparationInvariants

### Community 38 - "Community 38"
Cohesion: 0.33
Nodes (9): boundary_distances(), compactness(), evaluate(), main(), pixel_point(), pixel_polygon(), polygon_parts(), Evaluate frozen candidate-blind Chicago block reference zones. (+1 more)

### Community 39 - "Community 39"
Cohesion: 0.33
Nodes (8): digest(), fetch(), main(), Path, Freeze candidate-blind Chicago block reference zones and fetch orthophotos.…, select_zones(), main(), Freeze one new CHI:11 motorway core before viewing candidates there.

### Community 40 - "Community 40"
Cohesion: 0.33
Nodes (7): main(), Check Cook ground-parcel continuity and tax-block groups in frozen M3 cases., case_records(), fetch(), main(), Freeze new motorway and near-motorway tiles without block candidates or imagery., select()

### Community 42 - "Community 42"
Cohesion: 0.25
Nodes (5): main(), Independent table-level audit of H1–H3 candidates; no family acceptance., rasterio, rasterio_windows, zipfile

### Community 43 - "Community 43"
Cohesion: 0.43
Nodes (7): download(), main(), Acquire public GHSL candidates; preserve native cells, no model fitting or…, save(), sha(), concurrent_futures, rasterio_merge

### Community 44 - "Community 44"
Cohesion: 0.46
Nodes (7): fetch(), main(), item(), quote(), Acquire matched, buffered Overture sources with STAC pruning and atomic…, save(), sha()

### Community 45 - "Community 45"
Cohesion: 0.32
Nodes (6): bytes_from_size(), main(), quadkey_bounds(), Locate Microsoft global building tiles for the paired city supports. This reads…, math, urllib_parse

### Community 46 - "Community 46"
Cohesion: 0.32
Nodes (6): fetch(), main(), Freeze independent Chicago block review locations and cache orthophoto tiles., select(), Independently recount CTA bus stop calls from raw GTFS and assert they match…, datetime

### Community 47 - "Community 47"
Cohesion: 0.52
Nodes (6): chicago_image(), get_bytes(), main(), Bounded independent physical-cover audit of saved U1 diagnostic points.…, sp_image(), street_distance()

### Community 48 - "Community 48"
Cohesion: 0.43
Nodes (6): acquire(), main(), Path, Bounded Cook 2022 DTM/DSM structural check on frozen CHI:11 motorway faces., sha(), rasterio_features

### Community 49 - "Community 49"
Cohesion: 0.52
Nodes (6): fetch(), main(), previous_centers(), Freeze new candidate-blind Chicago M3/M4 reference zones and images., select(), sha()

### Community 50 - "Community 50"
Cohesion: 0.47
Nodes (4): main(), read(), Read-only audit of existing candidate releases; write a separate dated…, sha()

### Community 52 - "Community 52"
Cohesion: 0.60
Nodes (4): lines(), link_candidates(), main(), Queue named municipal streets that cross provisional faces outside Cook masks.…

### Community 53 - "Community 53"
Cohesion: 0.50
Nodes (3): main(), Independent accounting, sampled geometry and artifact checks for U2 sensitivity., sha()

### Community 54 - "Community 54"
Cohesion: 0.60
Nodes (4): check(), main(), Independent release audit and publication of the Chicago functional extension., sha()

### Community 55 - "Community 55"
Cohesion: 0.67
Nodes (3): dominance(), main(), Six-unit SP explicit-dominance sensitivity for mixed/other fiscal use.

### Community 57 - "Community 57"
Cohesion: 0.50
Nodes (4): Chicago M3/M4 polygon pilot and validation, Chicago block construction protocol (M3/M4), Chicago data sources, Chicago construction log

## Knowledge Gaps
- **38 isolated node(s):** `$schema`, `text`, `subtitle`, `name`, `params` (+33 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 348 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `chicago_only_8_family_candidate_v0 model` connect `Docs & M3 Provisional Faces` to `Curio Graph Install Scripts`, `Review Queue & Dashboard Data`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `Script INDEX` connect `Docs & M3 Provisional Faces` to `M3 DuPage Pilots`, `Curio Graph Install Scripts`, `M3 Fresh Tiles & Holdouts`, `Community 38`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `$schema`, `text`, `subtitle` to the rest of the system?**
  _38 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `SP Urban Model & Distances` be split into smaller, more focused modules?**
  _Cohesion score 0.05647517039922103 - nodes in this community are weakly interconnected._
- **Should `Block/Rail Boundary Review + Roads` be split into smaller, more focused modules?**
  _Cohesion score 0.06804214223002635 - nodes in this community are weakly interconnected._
- **Should `U1 POI/OSM Pilots` be split into smaller, more focused modules?**
  _Cohesion score 0.059322033898305086 - nodes in this community are weakly interconnected._
- **Should `Curio Graph Install Scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.05827067669172932 - nodes in this community are weakly interconnected._