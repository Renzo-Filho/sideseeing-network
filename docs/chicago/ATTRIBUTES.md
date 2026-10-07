> **Model definitions (6 October 2026).** The 12 families in the frozen Chicago model, with sources, checks and limits, are in [MODEL_REPORT.md](MODEL_REPORT.md) §3 and the contract `analysis/config/chicago_model_v1.json`. The text below is the earlier local baseline (16 September 2026), kept as a record; where it differs (for example U1 entropy, M3/M4 municipal enclosures, M7 unavailable, U2 2022, U3 2020, U4 bus-only), the model report governs.

# Chicago attributes

## Chicago local attribute baseline: calculation and processing

Release `chi_local_2026_09_16_v1`, constructed 16 September 2026. Read [data requirements](DATA_SOURCES.md) before analysis. These are **exploratory Chicago measurements**, including provisional and experimental fields. They are not replacements for the SP definitions or inputs approved for cross-city similarity.

### Reproduction and files

From the repository root:

```bash
.venv/bin/python analysis/scripts/prepare_chicago.py
.venv/bin/python analysis/scripts/audit_chicago_road_topology.py
.venv/bin/python analysis/scripts/validate_chicago_attributes.py
MPLCONFIGDIR=/tmp/chicago-matplotlib .venv/bin/python analysis/scripts/plot_chicago_attribute_qa.py
.venv/bin/python -m unittest discover -s analysis/tests -p test_chicago_harmonization.py -v
```

Use the frozen configuration at `config/chicago_attributes_v1.json`. Runtime paths resolve relative to the script, not the shell working directory. The endpoint audit is supplemental; it does not promote the M2 candidate table into the main feature matrix. Keep construction manifests associated with their original run. Input changes require a new reviewed release/config; preserve published outputs before rerunning. Source building GeoParquet is a read-performance cache bound to the raw file SHA-256. Original raw files and frozen SP releases are not edited.

- `results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.csv`: one row per Community Area, including explicit missing-family columns.
- `tables/attributes_long.csv` / `.parquet`: one row per unit/feature, numerator, denominator, source count where applicable, method, status and strict-acceptance flag.
- `tables/attribute_dictionary.csv`: exhaustive field definitions and status.
- `tables/population_crosswalk.csv`: reproducible aggregate population join.
- `spatial/chicago_community_attributes.gpkg`: attributes and land-proxy layers, EPSG:26916.
- `validation/`: source and run manifests, geometry/accounting checks.
- `work/prepared/Chicago/chi_local_2026_09_16_v1/`: source metadata, cached buildings, repaired/projected inputs, district land, roads and experimental blocks. These are reproducible intermediates, not additional competing releases.

### Shared geographic processing

IDs are `CHI:01` through `CHI:77`; local IDs are two-character strings. Validate the two boundary ID fields agree and all 77 occur exactly once. Compute gross area from geometry in **NAD83/UTM 16N, EPSG:26916**. Source GeoJSON is WGS84; CMAP is Web Mercator and is reprojected before measurement.

Invalid polygon geometry is repaired with `make_valid`; retain polygonal components, remove empty/zero-area results, record input invalid/null counts and area change. Land equals Community Area geometry minus the union of CMAP primary `LANDUSE=5000` polygons. Record gross, water and land areas and require their conservation. This water layer is a **land-use parcel proxy**; unmapped water can remain in the land denominator. Parks are not removed.

Whole-object assignment selects the district with the greatest positive overlap; an exact tie goes to the lowest district ID. Areas/shapes are measured on the whole object. Clipped densities instead retain each positive in-district piece. Boundary-coincident road pieces belong only to the first district in sorted ID order.

### M1: municipal street density

Select source classes `1,2,3,4,7,9,99` and status `N`. Per the [city data dictionary](DATA_SOURCES.md) (retrieved 2026-09-30) these are: 1 expressway, 2 arterials, 3 collectors, 4 **other streets**, 7 tiered, 9 ramps, 99 unclassified; status `N` is "no status". Exclude named alleys (`5`), sidewalks (`S`), river (`RIV`) and extent (`E`) lines, and the non-`N` statuses (`P` private, `UC` under construction, `V` vacant, `C` closed, `UR` under review). Preserve class 99 as unknown; do not relabel Local. Class 4 is the residual "other streets" class, about 70% of retained length; keep it by code and do not call it Local wholesale. A [2026-09-30 cross-check](../../analysis/results/Chicago/chicago_centerline_class_review_2026_09_30/README.md) against the nearest raw Overture road class finds class 4 ≈ 80% residential-type, ≈ 10% service-type and ≈ 7% tertiary/secondary by length, while classes 1–3 match Overture's motorway/primary/secondary/tertiary ladder. No official definition beyond the dictionary label exists.

Size of the filters (raw file, `LENGTH` feet × 0.3048, before de-duplication and clipping; 2026-09-30 check): retained ≈ 6,952 km, of which class 4 ≈ 4,906 km, 3 ≈ 762, 2 ≈ 680, 1 ≈ 286, 9 ≈ 157, 99 ≈ 146, 7 ≈ 14. The non-`N` status filter removes only ≈ 69 km (of which private class 4 ≈ 57.5 km), about 1% of core-class length; it is not a material driver of the Overture/local gap. Named alleys (`5`) are only ≈ 9 km in the file, so this layer is not a complete alley inventory. Overture M1 does not exclude private roads, so this is a small definitional difference between the two.

Remove exactly identical normalized line geometry duplicates. Clip to districts and remove pieces already assigned to lower IDs. Sum geometric metres, convert to km, divide by projected gross km². Retain numerator/denominator. Confirm the total assigned length equals the city-clipped selected-source length. This does not resolve near duplicates, all carriageway representations or access status; it is not yet a common Overture road universe.

### M6: municipal class composition

For each of the seven selected source codes, divide its assigned in-district length by the **same M1 total length**. Shares sum to one where the denominator is positive. Empty support would remain missing, not a fabricated all-zero composition. These seven code shares have different semantics from SP's six GeoSampa classes and cannot be passed into that model unchanged.

### M2: supplemental endpoint diagnostic (not an accepted feature)

`scripts/audit_chicago_road_topology.py` preserves each single-part source line's coordinate direction, pairs its start/end with `fnode_id`/`tnode_id` and endpoint level, and counts incident arms per `(node ID, level)`. Exactly duplicated geometry has already been removed. Groups with three or more arms are candidates; zero/empty node IDs are excluded. Points intersecting multiple districts are assigned to the lowest ID, and outside-city candidates are kept in the audit residual.

The supplied selected network has 35,873 node/level groups, with zero coordinate spread within each group. It yields 24,846 candidates: 24,652 inside Chicago and 194 outside. [The supplementary table](../../analysis/results/Chicago/chi_local_2026_09_16_v1/tables/m2_endpoint_candidates.csv) provides counts and gross-area densities for review. It is deliberately separate from the main feature matrix: incident-arm counts have not yet passed divided-road/ramp or common SP-definition tests. The principal M2 value remains unavailable.

### M3/M4: experimental planar enclosures

Union/planarize the selected municipal network, then polygonize closed rings. Retain positive-area whole polygons intersecting the city; assign by largest overlap. Exclude polygons crossing or touching the city boundary from district statistics and preserve an edge flag in the working layer.

- M3: median and IQR of natural-log whole polygon area in m².
- M4 compactness: `4π × area / perimeter²`, with all polygon boundaries represented by the geometry.
- M4 elongation: longest side / shortest side of the minimum rotated rectangle.
- For both shapes, publish unweighted median and IQR. Quantiles use pandas' linear interpolation.

**These are experiments, not accepted physical blocks.** No traffic-island threshold, dual-carriageway merging or rail/water barrier rule has been validated. Boundary-touching exclusions may bias peripheral units. Do not mistake these enclosures for the SP cadastral Quadra definition or for routable topology. M2 is explicitly withheld.

### B1: mapped footprint union coverage

Select ACTIVE records. Repair geometry, combine geometries for duplicated valid building IDs, and retain mapped objects without inventing missing floor values. Query the building spatial index within disjoint 2 km tiles intersecting each Community Area. Intersect building polygons with each tile and take an exact union. Sum tile-union areas; tile boundaries have zero area.

- `building_coverage_municipal_land`: union intersected with the land proxy / land-proxy area.
- `building_coverage_municipal_gross`: union / gross area.
- `footprint_overlap_excess_fraction`: (sum of clipped individual areas − union area) / sum; zero for no footprint mass.

This prevents overlaps/parts from inflating coverage. Geometric area is m²; source `shape_area` and unmaintained sqft are not used. Source observation age and inclusion of ancillary/nonstandard structures remain limitations. The publisher's metadata says August 2015; a September 2026 filename does not make the footprints a 2026 survey.

### B2: reported building stories

For each unique ACTIVE building, use the `stories` field only when numeric and strictly positive. Assign whole buildings by largest overlap. Duplicated IDs are dissolved; conflicting reported values are withheld. Compute unweighted median and P90 among eligible reports, plus positive-report count / all assigned ACTIVE building entities.

Zeros are missing reports, **not zero-storey buildings**; missing reports are never defaulted to one. The truncated `no_stories` field means **below-ground stories**, according to the attached publisher dictionary. Do not combine it with or treat it as a competing total. Building entities differ from SP's cadastral entities; source reporting coverage may be strongly selective. `z_coord` is not a height measure and `bldg_sq_fo` is not actively maintained. B3 remains missing.

### U1: observed primary-use area composition

Read the CMAP regional layer with a bounding-box filter in its source CRS, then exact spatial filtering. Repair and project polygons. Use primary `LANDUSE`; do not double-count secondary `LANDUSE2` codes as additional polygons. Group code prefixes into **eight** categories:

| Prefix | Group |
|---|---|
| 11 | Residential |
| 12 | Commercial (includes primary mixed commercial/residential codes) |
| 13 | Institutional |
| 14 | Industrial |
| 15 | Transportation/utilities |
| 2 | Agriculture |
| 3 | Open space |
| 4 | Vacant/under construction |

Water 5000, nonparcel 6000 and unknown 9999 are outside the classified entropy denominator. Intersect each polygon with each district, union within each group, remove areas claimed by different groups, restrict to the land proxy, and compute `p = group area / total classified area`, and entropy `−Σ(p log p)/log(8)` over positive shares. Report all eight shares. No classified area means missing entropy, not zero diversity.

Publish LUI union coverage/gross area, overlap excess/gross area, classified area/land proxy, and fraction of intersected source area carrying any secondary-use code. Report ambiguous cross-category area/gross area separately. Within-category overlaps are unioned; cross-category conflicts are withheld from all entropy categories. This was added after the first run detected 51.08 m² of overlapping LUI in Rogers Park. Unknown/unclassified/ROW support is visible through coverage, not silently allocated to categories. This is an **eight-category area** measure, not the original **seven-category entity-count** SP entropy.

### U3: supplied ACS aggregate resident density

Require 77 unique source names and one-to-one exact normalized name agreement with the boundary names; save the resulting ID crosswalk. Divide each provided `total_population` by projected gross km², conserving the complete supplied population total. Do not perform tract allocation or fabricate block populations from these aggregates.

The CSV labels all rows 2023, but its source period, margins of error and Community Area estimation method are unresolved. Status is `provisional_population_provenance`; the year suffix describes the **supplied label**, not a verified point-in-time census. A Census-block version is still required for the planned common support and U4.

### Missing features and interpretation

M2, M7, B3, U2 and U4 each have an explicit `*_unavailable` column/long-table row with null value and a reason. This preserves all 13 planned families without pretending construction is complete. M5/U5 remain dropped. All records set `strict_cross_city_accepted=false`.

Use the local output for source-quality review and descriptive exploration. No Chicago-to-Brás ranking, fitted model, paired SP reconstruction, or claim of complete model readiness is produced by this release. The data requirements document gives the next acquisition and acceptance tasks.

## Chicago functional extension and matched-source acquisition

16 September 2026. New functional release: `chi_functional_2026_09_16_v2`. The previous local Chicago release and all original SP measurements remain unchanged. This is a completed construction milestone when its independent audit passes, **not completion of cross-city harmonization**. Checkpoint history is in the [Chicago execution log](EXECUTION_LOG.md).

### New supplied inputs

- `tl_2022_17_tabblock20`: all 369,978 Illinois 2020 tabulation blocks in the 2022 TIGER release, EPSG:4269. The supplied feature-catalog XML defines `POP20` as the 2020 Census count adjusted by the Disclosure Avoidance System. Population is already supplied; another population download is unnecessary. State population sums to 12,812,508.
- `il_wac_S000_JT00_2022.csv`: 91,481 workplace blocks, 5,825,390 jobs statewide. `C000` is the total; demographic and industry columns are not added to it. All supplied IDs match the statewide block geography. Sparse absent WAC rows mean no published jobs under this source, not missing population. The file carries `createdate=20240920`; original compressed-download checksum/transfer lineage was not supplied. External completeness beyond the supplied statewide file is not claimed.
- `google_transit/`: CTA static bus/rail feed. All 5,920,320 stop-time records were checked for trip/stop references. The bus selection has 124 routes, 91,196 trips and 5,787,775 stop-time records. Calendars span September 11–November 30, 2026; there are 85 exception rows and zero frequency-template rows. America/Chicago is the declared timezone. Original extracted files and developer license remain intact.
- `Hydro_20260916.geojson`: 605 valid municipal polygons, including rivers, canals and Lake Michigan. Original records include historical edit dates, often March 2001, and 2015 portal creation timestamps. The download date is not a hydrographic observation year. It is a stronger supplied area-water source than a land-use parcel proxy, but not a certified current shoreline.

Local inputs and executable code are hashed in `validation/source_code_manifest.json`. Publisher references and qualifications are in `validation/publisher_register.json`; user-supplied files are not misrepresented as downloads made by this pipeline.

### U2/U3 allocation

Preserve 15-character GEOIDs, project blocks to EPSG:26916, and intersect whole block polygons with all 77 Community Areas. Each positive piece receives `source count × piece area / whole block area`. The support is gross polygon area, matching the original SP population support convention; reported Census `ALAND20` and `AWATER20` remain in the prepared block table and are not substituted for projected polygon area. Counts are fractional estimates after allocation, not exact official Community Area totals.

The selected 39,498 positive-overlap blocks cover Cook and DuPage. Retain every outside-city remainder and all unmatched job rows (zero here). Boundary-vintage differences leave 11,884.19 m², approximately 0.002%, uncovered by blocks. The gap geometry is saved under prepared work. No residents/jobs are invented in those gaps. The original strict 0.001% coverage check failed; investigation identified a small geometry mismatch, now explicitly reported and gated at 0.1% maximum rather than silently treated as complete coverage. Independent city-union clipping checks the allocated mass without reusing district pieces.

Allocated population is **2,745,500.3508** and allocated jobs **1,409,454.0400**. The border-block outside residuals are **36,978.6492 residents** and **48,808.9600 jobs**. The full matched-state jobs outside Chicago total **4,415,935.9600**. Gross-area density is the default. The supplied ACS aggregate is retained as a different-period/provenance diagnostic, not an equality target. Chicago Census 2020 and SP Census 2022 remain different observation periods. The uniform-allocation assumption behind the area split, the share of residents in blocks cut by a boundary (8.0% straddling two areas, 2.8% partly outside the city), and the possibility of a developed-land denominator are recorded in [DECISIONS.md](../DECISIONS.md) ("Open question: uniform-allocation assumption and a developed-land denominator").

U2 is an **extended area-weighted baseline**. CMAP business-area sensitivity, RAIS/LODES universe reconciliation and external file-completeness checks remain open; no strict shared employment feature is accepted.

### U4 bus service

Scenarios are Wednesday September 16, 2026, 07:00–09:00; Saturday September 19 and Sunday September 20, 09:00–11:00. All are local service windows, interpreted as half-open intervals. Apply regular calendars plus additions/removals, including prior service dates for departures after 24:00. The largest supplied departure is 25:30. Filter `route_type=3`, exclude `pickup_type=1`, retain route directions and stops outside Chicago. Rail contributes nothing. No Pace feed is included.

Split positive-population block∩district support by an origin-zero 250 m projected grid, weighting each piece by its share of the whole block area. Representative points lie inside pieces. At 400 m and 800 m Euclidean radii, take the maximum reachable stop departure count for each route/direction, then sum across route/directions. Population-weight these supplies over each district. Preserve numerator, population denominator, reached population, point count and six scenario rows per area (462 rows total). Assert pointwise radius monotonicity and district population conservation.

The supplied feed has no frequency templates. The pipeline explicitly rejects a changed feed containing them rather than silently double-counting its templates. Supporting generic frequency feeds is a future extension, not a tested capability of this release. Unknown or malformed bus times, duplicate sequences, reverse departure chronology and missing references fail construction. The current supplied feed passed these checks. Independent pilot validation uses coordinate-tree neighborhoods and an explicit per-route/direction maximum rather than the construction spatial-index join. A separate pandas audit of all raw stop times exactly reproduces 148,915 weekday, 100,950 Saturday and 89,597 Sunday scheduled stop calls; these are feed stop-call counts, not the resident-weighted index.

### Hydrography

Union all supplied hydro polygons, intersect with each Community Area, and compute land as gross minus water. Gross = land + water passes. Water inside Community Areas is **13.91398 km²**, versus **1.24108 km²** under the prior CMAP parcel proxy. Neither the original B1 values nor their frozen denominators are overwritten. New footprint pilots report both gross and hydro-land coverage and retain the source-age limitation.

### Matched Overture work

The frozen SP extraction manifest and current publisher catalog agree on `2026-08-19.0`. New acquisitions use each city's metric union buffered by 2 km, converted to WGS84 bounds. STAC asset bounds prune files; remote Parquet bbox **intersection** predicates preserve crossing objects. Each selected partition is streamed into `.part`, validated, atomically renamed and hashed; exact city filtering happens in the review stage. All source attributes and attribution fields are retained. This is buffered bounding-box extraction, not a claim of exact municipal feature membership.

`acquire_harmonized_overture.py` acquires Chicago buildings, roads/connectors for Chicago and SP. Original SP buildings are reused from the matching release. Acquisitions live under `data/<city>/overture_2026_08_19/`; catalogs under `work/prepared/shared/overture_2026_08_19/`. Each source directory has its own query/schema/count/hash manifest. Buffered extraction counts are Chicago: 1,381,239 buildings, 350,885 segments and 689,832 connectors; SP: 423,904 segments and 452,539 connectors. All extracted IDs are unique. Results of `review_matched_overture.py` live separately under `results/<city>/overture_2026_08_19_review_v1/`.

The paired road candidate excludes all service/alleys/driveways and nonmotor classes, retains motorway through residential, living streets, unclassified/unknown and link ramps, and keeps carriageways separate. It reports class shares, unknown mass and source class inventories. Access restrictions are counted but not resolved. Connector diagnostics count one arm at endpoints and two at interior connector positions; they have not passed physical-arm duplication, divided-road consolidation or access-policy review. These are candidates, **not accepted M2 or physical blocks**. No M3/M4 claim is made.

### Reproduction and remaining work

```bash
.venv/bin/python analysis/scripts/prepare_chicago_functional.py
.venv/bin/python analysis/scripts/validate_chicago_functional.py
.venv/bin/python -m unittest discover -s analysis/tests -v
.venv/bin/python analysis/scripts/review_matched_overture.py
```

The functional constructor has source/config/code signatures, stage-owned artifact hashes and checkpoints. Changed signatures fail under the same run ID. Identical completed invocations verify/reuse outputs. Development's initial coverage failure and pre-fix checkpoint are preserved under prepared work. New raw sources or changed method definitions require a new release/config. Acquisition scripts require network permission; source partition signatures prevent stale reuse.

Remaining work: business-support jobs sensitivity; cadastral stock/parent semantics for M7/B2/B3; common U1 weighting/ontology and paired SP construction; road-access/carriageway/connector fixtures; physical-block definition/pilots; geographic completeness and source comparisons; accepted common feature contract. Then, and only then, fit SP-anchored transforms and rank Chicago against Brás. No cross-city ranks or accepted common matrix are published in this milestone.
