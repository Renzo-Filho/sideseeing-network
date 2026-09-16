# Copy-ready continuation prompt

Act as a senior Spatial Data Engineer, GIS Analyst and Data Science Engineer. Continue the existing São Paulo–Chicago urban similarity research in this repository. Read the project evidence before changing definitions. Implement, acquire data, validate and document the remaining attribute work; do not stop after restating a plan.

## Objective and current boundary

The research characterizes urban morphology and functional structure, initially comparing Brás with São Paulo's other districts, then comparing Brás with Chicago under demonstrably compatible measurements. Pedestrian/accessibility outcomes are a separate later study.

The SP district attributes and corrected SP similarity model v2 are complete. A first **Chicago local-source baseline** is also complete and validated, but it is **not an accepted harmonized model matrix**. Your immediate task is to acquire missing public inputs, construct the remaining supported Chicago attributes, resolve measurement differences, and create separately versioned harmonized SP companion attributes where required. Do not fit Chicago-to-Brás rankings until the common feature contract passes. Do not fill gaps by substituting unrelated data.

M5 and U5 were explicitly dropped. The remaining 13 families are M1/M2/M3/M4/M6/M7/B1/B2/B3/U1/U2/U3/U4. The user values concise communication, persistent execution, organized folders and detailed handoff documentation. Routine public-data acquisition and reversible implementation are within the requested work; follow environment permissions when network access needs escalation. Ask only for genuinely missing decisions or unavailable information, and keep working on independent tasks.

## Repository and environment

Repository root on the current machine:
`/home/renzo/Documents/GitHub/sideseeing-network`

Use repository-relative paths below from that root. The Python environment is `.venv/bin/python`; pinned packages are in `analysis/requirements.txt`. It already includes GeoPandas, Pyogrio, Shapely, PyArrow, DuckDB, NumPy, pandas and scientific/modeling dependencies. Check applicable AGENTS.md instructions and `git status --short` first. Do not install a second environment unnecessarily.

The working tree contains earlier SP corrections and new Chicago work that were not committed by the previous agent. Preserve unrelated edits. In particular, deletions of `analysis/model_analysis.pdf` and `analysis/patch_notebook.py` predate this Chicago task. Do not restore them, reset the working tree, commit everything together, or push without a current request. No subagents are requested by this prompt.

## Read first, in this order

1. `analysis/CHICAGO_EXECUTION_REPORT.md` — completed tasks, issues/causes/treatments, exact validation findings and continuation instructions.
2. `analysis/CHICAGO_DATA_REQUIREMENTS.md` — current source inventory, missing inputs, acceptance gates and official references.
3. `analysis/CHICAGO_ATTRIBUTE_DOCUMENTATION.md` — actual local formulas and exclusions.
4. `analysis/CHICAGO_HARMONIZATION_PLAN.md` — full shared-feature protocol, paired SP recomputation and model policy. Its original September 15 inventory is explicitly historical; the requirements document supersedes it.
5. `analysis/README.md` and `plan.md` — project navigation and research objectives.
6. `analysis/ATTRIBUTE_DOCUMENTATION.md` — frozen **SP** definitions, not Chicago definitions.
7. `analysis/SP_MODEL_FIXES.md` and `analysis/URBAN_MODEL_IMPLEMENTATION_PLAN.md` — corrected SP mathematics and modeling protocol. `SP_MODEL_VALIDATION.md` preserves the original failed review with a resolved-status notice; do not confuse that historical failure with the corrected v2 result.

Read selectively after these entry points. Avoid dumping huge files or repeating completed full-city processing just to rediscover the current state.

## Where the actual data, results and code are

| Location | Purpose |
|---|---|
| `analysis/data/Chicago/` | Canonical raw Chicago source root; preserve original files |
| `analysis/data/SP/` | Original SP sources; preserve |
| `analysis/results/Chicago/chi_local_2026_09_16_v1/` | Completed Chicago baseline: tables, spatial output, reports and validation |
| `.../tables/attributes_wide.csv` and `.parquet` | 77 rows; 40 feature/diagnostic columns plus identifiers/areas |
| `.../tables/attributes_long.csv` and `.parquet` | 3,080 records with methods, statuses, numerator/denominator and coverage |
| `.../tables/attribute_dictionary.csv` | Exhaustive field dictionary |
| `.../tables/m2_endpoint_candidates.csv` | Supplemental graph experiment, not accepted M2 |
| `.../spatial/chicago_community_attributes.gpkg` | `community_attributes` and `community_land_proxy`, EPSG:26916 |
| `.../reports/attribute_qa.png` | Six descriptive QA maps, already visually inspected |
| `.../validation/` | Construction/independent checks, source/run manifests, publisher metadata register and final release checksums |
| `analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/` | Projected/repaired buildings, roads, land use, districts/land, experimental blocks, graph candidates, cached source buildings, publisher metadata PDF/JSON, logs and progress.json |
| `analysis/config/chicago_attributes_v1.json` | Executed local-source contract |
| `analysis/scripts/prepare_chicago.py` | Local construction entry point |
| `analysis/scripts/harmonization/geometry.py` | Polygon repair, whole-object ownership, tiled footprint union, exclusive-category areas, entropy |
| `analysis/scripts/audit_chicago_road_topology.py` | Supplemental endpoint audit |
| `analysis/scripts/validate_chicago_attributes.py` | Independent ratio/format/hash checks and five-pilot B1/B2 reconstruction |
| `analysis/scripts/plot_chicago_attribute_qa.py` | QA maps |
| `analysis/tests/test_chicago_harmonization.py` | Six geometry/accounting tests |
| `analysis/results/SP/tables/` and `spatial/` | Frozen original SP attribute release, 96 districts |
| `analysis/results/SP/models/sp_urban_model_v2/` | Corrected SP model, reports, ranks and robustness outputs |
| `analysis/scripts/sp_attributes/`, `sp_v3/`, `sp_model/` | Existing SP construction/preparation/model code; read and reuse appropriate logic |
| `analysis/work/prepared/SP/sp_prep_2026_09_10_v3/` | Frozen SP integration inputs; earlier v2 also preserved |
| `analysis/model_analysis.ipynb` and `.py` | Corrected SP exploration, not a Chicago implementation |

`analysis/outputs` and `analysis/processed` are legacy compatibility links. Do not recreate parallel output trees there. Raw and prepared data are ignored by Git; curated aggregate results belong in `analysis/results/`. An agent on another machine may need the ignored data transferred separately: Git alone does not contain the large inputs.

The current Chicago entry point writes its hard-coded/configured release and is **not an immutable release manager**. Do not rerun it with changed sources/definitions over v1. Create a new release/config and adapt validation paths. Introduce explicit source/code signatures, stage checkpoints and safe resume behavior in the next pipeline rather than repeatedly rebuilding completed stages.

## Established facts and important traps

- Chicago: 77 Community Areas, IDs `CHI:01`–`CHI:77`; SP: 96 districts, `SP:01`–`SP:96`, Brás `SP:10`. Never join cities by bare ID.
- Geometry: Chicago EPSG:26916, SP EPSG:31983. CMAP source is EPSG:3857; most supplied GeoJSON is EPSG:4326. Calculate metric properties only after appropriate projection. Attribute ft² conversion is 0.09290304, only after verifying field units/meaning.
- The baseline passed **36 repository tests** and **87 independent release checks**. B1 was independently reconstructed with untiled unions in West Town 24, Near West Side 28, South Lawndale 30, Loop 32 and O'Hare 76. Arithmetic validity does not establish measurement equivalence.
- Principal M2/M7/B3/U2/U4 are explicitly null. M3/M4 are experimental enclosures. M1/M6/B1/B2/U1 are local alternatives; U3 is provisional. Every strict cross-city acceptance flag is false.
- Municipal footprints: 820,606 raw records. Metadata says **current as of August 2015**, despite a 2026 download filename. `stories` is stories; truncated `no_stories` means **below-ground stories**. `bldg_sq_fo` is not actively maintained; `z_coord` is not maintained, not building height.
- ACTIVE building ID 882804 occurred twice and was dissolved; eight raw placeholder ID=0 records were not ACTIVE. Nine invalid ACTIVE polygons were repaired. Final unique ACTIVE entities: 820,455; inside Chicago: 820,395; positive stories: 427,924, approximately 52.16%. District coverage ranges 20.90%–76.78%. Do not turn missing stories into one or treat this selective sample as complete stock.
- Building permits are events, not existing stock or GFA. The business extract has only 20 records for one account/two address strings, not employment. The 302 CTA L-stop records are rail, not bus service. The one-row zero-valued `morphological_data.csv` is a dummy Brás row and is excluded.
- Municipal roads: 56,338 raw, 54,172 in the declared class/status selection. Code 4 is retained by code; its label was absent from the reviewed city renderer. Do not import Cook County's different code mapping. Chicago code 99 remains unknown. SP's prior “unclassified = Local” decision is SP-specific.
- Endpoint audit: 35,873 node/level groups, zero coordinate spread; 24,846 ≥3-arm candidates, 24,652 inside and 194 outside. This has not validated physical arm duplication, ramps/consolidation or equivalence to SP's M2 proxy.
- SP M2 uses the user-approved 5 m structure exclusion with 0.984% reduction. Preserve that original result; a new shared graph rule requires separately recomputed SP M2.
- CMAP 2023: 177,032 city-intersecting records. Within-category geometry is unioned; cross-category overlap is excluded as ambiguous. Do not revert to raw area sums: an initial run caught overlapping polygons.
- U1 local baseline uses **eight primary-use area groups**. SP uses **seven entity-count groups**. Same “entropy” label does not make them comparable. CMAP secondary-use codes are diagnostics, not extra duplicated area.
- CMAP 5000 is a predominantly-water parcel proxy, not a precise shoreline. It removes only 1.2411 km² from 597.6984 gross km². Hydrographic completeness remains unresolved. Parks stay land.
- Provided ACS population totals 2,647,621 with exact 77-name crosswalk, but source period/MOE/aggregation provenance remain unresolved. Do not call it a 2023 census or fabricate exact block populations from these aggregates.

## Missing data: how to obtain and process it

Use public official downloads/APIs or cloud queries. Discover current schemas before coding crosswalks. Save the original URL, access date, observation period, release/geography vintage, license, byte size, SHA-256, schema, query and completeness counts. Download to `.part`, validate response/content/archive, then rename atomically. Use timeouts/retries and resumable partitions. Never treat an HTML error page as a dataset. For APIs, verify full pagination against a count query; a default 1,000-row response is not complete.

### 1. Census blocks and resident population — U3 and U4 support

Start at the official [2020 tabulation block directory](https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/). Select the Illinois archive (state FIPS 17) from the actual listing; verify archive name/schema rather than guessing a county-only filename. Alternatively use a documented Census block service with complete pagination and matching 2020 boundaries.

Cover the **entire Community Area union**, including O'Hare and DuPage. Cook is county FIPS 031 and DuPage 043; verify spatial coverage instead of assuming every Chicago point is Cook County. Preserve GEOIDs as 15-character strings. Check whether the selected geography release actually contains population; do not assume TIGER geometry always does.

If counts are absent, obtain the 2020 Decennial PL 94-171 total population field `P1_001N` through the [official Census API documentation](https://api.census.gov/data/2020/dec/pl.html), querying blocks within the required Illinois counties using supported predicates, partitioning if necessary. Verify the variable definition and geographic keys before merging. Require one count per block and distinguish actual zero population from missing joins. Retain population, land/water areas and source geography lineage.

Allocate to districts by positive intersection-area weights under a declared support rule, retaining outside-city residuals and conserving counts. If using land-only support, construct it explicitly and document the change relative to SP. Compare resulting district totals with the supplied ACS aggregate as a **different-period** diagnostic, not an equality test. Record Chicago 2020 versus SP 2022 timing. Reuse these block intersections for U4 population integration.

### 2. Workplace jobs — U2

The official [Illinois LODES8 WAC listing](https://lehd.ces.census.gov/data/lodes/LODES8/il/wac/) was checked when writing this handoff and lists:
`https://lehd.ces.census.gov/data/lodes/LODES8/il/wac/il_wac_S000_JT00_2022.csv.gz`

Download this candidate and the release's official technical documentation from the [Census LEHD data page](https://lehd.ces.census.gov/data/). Recheck that S000/JT00 represents the intended all-job universe and that the block vintage matches the acquired geography. Expected candidate keys are `w_geocode` and total `C000`; verify them from the downloaded schema. Do not add demographic/industry subtotals to C000, stack incompatible job types, or substitute RAC/OD/primary-job-only data.

Join workplace block IDs as strings. Keep all blocks with positive city overlap, including cross-border blocks. Establish a mass-conserving area-weighted baseline and an observed business-use-area sensitivity using CMAP after validating the employment-support categories. Do not automatically use residential population as job weights. If ancillary support is zero, use a documented fallback and flag it; do not drop jobs. Preserve unmatched and outside allocations separately. Publish source totals, accepted mass, unresolved mass and scenario differences. Compare RAIS job-link coverage/reference timing with LODES before promoting U2 beyond the extended functional comparison.

### 3. CTA bus schedules — U4

Use the official [CTA GTFS guidance](https://www.transitchicago.com/developers/gtfs/) and [download directory](https://www.transitchicago.com/downloads/sch_data/). Select the ZIP currently listed; do not invent a permanent filename or assume a downloaded feed reproduces past September service. Retain its license and inspect date ranges before choosing scenarios.

Read agency/stops/routes/trips/stop_times/calendar/calendar_dates and frequencies when present. Filter bus routes using the verified GTFS route types; do not mix rail into Chicago while SP remains bus-only. Keep all relevant stops outside the city within at least 800 m of population support. Namespace agency/route/stop IDs if multiple feeds are later added. Pace is a separately declared extension requiring comparable SP scope.

Implement the SP supply definition: population-weighted expected departures in a two-hour window; at each support point take the **maximum reachable stop supply per route/direction**, then sum across route/directions. Do not sum nearby stops on the same route as separate service. Use origin-zero 250 m projected grid intersections with block∩district population support and representative points inside pieces. Weekday 07:00–09:00, Saturday/Sunday 09:00–11:00; 400 m primary and 800 m sensitivities. Validate calendar exceptions, service dates, frequency templates, after-midnight times and timezone. Conserve population weights and require 800 m supply ≥400 m. Compare with `analysis/scripts/sp_attributes/spatial.py` and `analysis/scripts/sp_v3/transit.py`; inspect interfaces before reuse.

### 4. Common physical geometry — M1/M2/M3/M4/M6/B1

Use [Overture Transportation](https://docs.overturemaps.org/guides/transportation/) and [Buildings](https://docs.overturemaps.org/guides/buildings/) documentation. Inspect SP's existing extraction manifest to verify its frozen release; project documentation identifies 2026-08-19.0 as the existing candidate. Check availability before reuse. Do not silently substitute “latest” for only one city.

Use DuckDB with spatial/httpfs as needed, anonymous S3 access and bbox predicate pushdown over the verified release paths:

```text
s3://overturemaps-us-west-2/release/<verified-release>/theme=buildings/type=building/*
s3://overturemaps-us-west-2/release/<verified-release>/theme=transportation/type=segment/*
s3://overturemaps-us-west-2/release/<verified-release>/theme=transportation/type=connector/*
```

These are path templates: verify schema and actual release content. Derive WGS84 extraction bounds from metric-buffered city geometry, then apply exact spatial filtering. Use a sufficient network/block margin and at least the 800 m transit margin where relevant. Stream remote filtered results into local GeoParquet before GeoPandas processing; do not fetch global datasets into RAM. Record memory limits, query and ID/count checks. Existing SP Overture preparation/extraction scripts are implementation references; do not run their SP bbox unchanged for Chicago.

Freeze a common road universe, alley/service/ramp/access policy, carriageway handling and class mapping. Preserve unknown mass. Use source connector topology for M2 and validate bridge/tunnel, divided-road, slip-lane, loop and segmentation fixtures. Morphological polygonization is a different 2D construct from routable topology. For M3/M4 resolve carriageway islands, rail/water barriers, large campuses and extraction-edge blocks, then calculate whole-object statistics under the same rule in both cities. For B1 use exact unions, source completeness comparisons and a reviewed land mask. Do not mutate the original SP release to make the comparison appear compatible.

### 5. Hydrography / land support — B1/B3 and denominator sensitivity

Acquire authoritative water polygons through Census TIGER area hydrography or a suitable official county/city hydrography service. Start from [Census TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html), discover the correct year/county files, and cover every intersecting county. Inspect Lake Michigan edges, rivers, canals, islands and airports; do not use water centerlines as area polygons. Union water, intersect with each Community Area, validate gross=land+water, and compare against the current CMAP proxy. Preserve gross-density and land-coverage conventions unless a paired SP sensitivity explicitly changes them.

### 6. Physical parcels, floors and constructed area — M7/B2/B3

Investigate official Cook County GIS parcel geometry and the [Assessor Parcel Universe](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe/nj4t-kc8j). The [commercial valuation candidate](https://dev.socrata.com/foundry/datacatalog.cookcountyil.gov/csik-bsws/embed) is a discovery lead, **not a verified complete all-stock GFA source**. Use current official catalog metadata/field documentation to discover residential improvements, condominium/unit-parent relationships and commercial records. Acquire DuPage equivalents or document coverage gaps where the city crosses the county boundary.

For Socrata, inspect dataset metadata, select an explicit tax/snapshot year, retrieve counts, and use stable pagination/key ordering. For ArcGIS, inspect fields/domains/CRS and `maxRecordCount`; retrieve IDs/counts and batch all requested features. Apply Chicago spatial selection without losing whole parcel geometry or parent records.

Build physical entity IDs with unit/parent lineage. Do not count each condominium PIN as a separate physical parcel. Resolve duplicate building area repeated across units. Determine whether each floor-area field means gross, living, rentable or unit area; mixed meanings must not be summed as GFA. Convert documented sqft once. Evaluate residential/commercial/condominium coverage separately. Missing floors stay missing. If source semantics cannot support a common M7/B2/B3, document the evidence and omit that family from both cities' strict model rather than fabricate a proxy. A footprint×estimated-floors alternative must be explicitly labeled and reconstructed in both cities.

### 7. Use ontology and metadata closure — U1 plus supporting gates

Reuse the supplied CMAP LUI 2023 file; no duplicate download is needed. Review the [publisher classification guide](https://cmap-repos.github.io/LUI-wiki/field_guide_index.html) and inventory documentation. Freeze a defensible shared ontology and weighting with SP. Treat mixed/secondary use, vacant/construction, transport/right-of-way, unknown and water support explicitly. Retain exclusive-category overlap handling. The current local eight-area-group entropy cannot be compared directly with SP's seven-entity-group entropy.

Trace the ACS CSV to its original official dataset and estimate period; obtain MOE/aggregation methodology where available. Resolve municipal road code/status meanings from the actual city source, not another jurisdiction's taxonomy. Keep all metadata uncertainties visible until resolved.

## Recommended execution order and deliverables

1. Inspect current files/working tree and existing validation; establish a new versioned run with source register, progress ledger and resumable stages. Do not recompute the completed baseline without a reason.
2. Acquire Census geography/population, LODES WAC and CTA GTFS; these can close U2/U3/U4 without waiting for difficult cadastral reconciliation. Inspect schemas and dates first; report genuine access failures precisely.
3. Acquire matched Overture physical sources and hydrography; pilot Chicago contrasts and SP Brás/Itaim Bibi/Grajaú. Validate common roads, intersections, blocks, hierarchy and footprint support.
4. Resolve cadastral extension and common observed-use policy. Separate unavailable data from unvalidated semantics; explain the exact blocking evidence.
5. Construct all supported Chicago attributes and separately versioned harmonized SP companions. Publish qualified IDs, numerators, denominators, coverage, unknown/outside mass, source dates, explicit null reasons and an exhaustive dictionary. Require population/jobs/area conservation, unique entity identities and meaningful synthetic/independent checks.
6. Freeze the strict/common and extended feature sets **before** examining similarity ranks. Exclude unsupported families symmetrically; no pairwise available-feature distances or zero imputation. Only then prepare model fitting.
7. For the eventual comparison, fit transforms/scales/family calibration on the harmonized SP reference and apply the same saved state to Chicago. Do not separately standardize cities. Existing SP model code is SP-only by design; build a separate qualified-ID loader rather than weakening it. Follow the plan for city-balanced pooled sensitivity, source/weight robustness and later MAUP/grid assessment.

Keep new raw acquisitions in organized subdirectories of `analysis/data/Chicago/`; processed intermediates in `analysis/work/prepared/Chicago/<new_run>/`; curated outputs in `analysis/results/Chicago/<new_release>/`. Use a separate harmonized SP release and reserve `analysis/results/SP_CHI/<model>/` for actual accepted comparison outputs. Avoid scattering numbered folders without README explanations.

Maintain documentation during execution: issue, why it occurs, decision, method/experiment, evidence, test result, remaining uncertainty and next action. Update requirements, attribute definitions, execution report and navigation when milestones finish. Do not overwrite historical validation evidence or label partial construction “model ready.” Leave a machine-readable progress/checkpoint file and concise copy-ready handoff if interrupted.

Your first response should briefly state the verified current stage and start inspecting/acquiring the next missing inputs. Deliver actual code/data/validated attributes where possible, with explicit evidence for any remaining blockers; do not return only another broad plan.
