# Chicago local attribute baseline: calculation and processing

Release `chi_local_2026_09_16_v1`, constructed 16 September 2026. Read [data requirements](CHICAGO_DATA_REQUIREMENTS.md) before analysis. These are **exploratory Chicago measurements**, including provisional and experimental fields. They are not replacements for the SP definitions or inputs approved for cross-city similarity.

## Reproduction and files

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

## Shared geographic processing

IDs are `CHI:01` through `CHI:77`; local IDs are two-character strings. Validate the two boundary ID fields agree and all 77 occur exactly once. Compute gross area from geometry in **NAD83/UTM 16N, EPSG:26916**. Source GeoJSON is WGS84; CMAP is Web Mercator and is reprojected before measurement.

Invalid polygon geometry is repaired with `make_valid`; retain polygonal components, remove empty/zero-area results, record input invalid/null counts and area change. Land equals Community Area geometry minus the union of CMAP primary `LANDUSE=5000` polygons. Record gross, water and land areas and require their conservation. This water layer is a **land-use parcel proxy**; unmapped water can remain in the land denominator. Parks are not removed.

Whole-object assignment selects the district with the greatest positive overlap; an exact tie goes to the lowest district ID. Areas/shapes are measured on the whole object. Clipped densities instead retain each positive in-district piece. Boundary-coincident road pieces belong only to the first district in sorted ID order.

## M1: municipal street density

Select source classes `1,2,3,4,7,9,99` and status `N`. This is an explicit exploratory filter, pending complete status documentation. Exclude named alleys (`5`), sidewalks (`S`), river (`RIV`) and extent (`E`) lines. Preserve class 99 as unknown; do not relabel Local. Class 4 is reported by code because the reviewed official renderer did not label it.

Remove exactly identical normalized line geometry duplicates. Clip to districts and remove pieces already assigned to lower IDs. Sum geometric metres, convert to km, divide by projected gross km². Retain numerator/denominator. Confirm the total assigned length equals the city-clipped selected-source length. This does not resolve near duplicates, all carriageway representations or access status; it is not yet a common Overture road universe.

## M6: municipal class composition

For each of the seven selected source codes, divide its assigned in-district length by the **same M1 total length**. Shares sum to one where the denominator is positive. Empty support would remain missing, not a fabricated all-zero composition. These seven code shares have different semantics from SP's six GeoSampa classes and cannot be passed into that model unchanged.

## M2: supplemental endpoint diagnostic (not an accepted feature)

`scripts/audit_chicago_road_topology.py` preserves each single-part source line's coordinate direction, pairs its start/end with `fnode_id`/`tnode_id` and endpoint level, and counts incident arms per `(node ID, level)`. Exactly duplicated geometry has already been removed. Groups with three or more arms are candidates; zero/empty node IDs are excluded. Points intersecting multiple districts are assigned to the lowest ID, and outside-city candidates are kept in the audit residual.

The supplied selected network has 35,873 node/level groups, with zero coordinate spread within each group. It yields 24,846 candidates: 24,652 inside Chicago and 194 outside. [The supplementary table](results/Chicago/chi_local_2026_09_16_v1/tables/m2_endpoint_candidates.csv) provides counts and gross-area densities for review. It is deliberately separate from the main feature matrix: incident-arm counts have not yet passed divided-road/ramp or common SP-definition tests. The principal M2 value remains unavailable.

## M3/M4: experimental planar enclosures

Union/planarize the selected municipal network, then polygonize closed rings. Retain positive-area whole polygons intersecting the city; assign by largest overlap. Exclude polygons crossing or touching the city boundary from district statistics and preserve an edge flag in the working layer.

- M3: median and IQR of natural-log whole polygon area in m².
- M4 compactness: `4π × area / perimeter²`, with all polygon boundaries represented by the geometry.
- M4 elongation: longest side / shortest side of the minimum rotated rectangle.
- For both shapes, publish unweighted median and IQR. Quantiles use pandas' linear interpolation.

**These are experiments, not accepted physical blocks.** No traffic-island threshold, dual-carriageway merging or rail/water barrier rule has been validated. Boundary-touching exclusions may bias peripheral units. Do not mistake these enclosures for the SP cadastral Quadra definition or for routable topology. M2 is explicitly withheld.

## B1: mapped footprint union coverage

Select ACTIVE records. Repair geometry, combine geometries for duplicated valid building IDs, and retain mapped objects without inventing missing floor values. Query the building spatial index within disjoint 2 km tiles intersecting each Community Area. Intersect building polygons with each tile and take an exact union. Sum tile-union areas; tile boundaries have zero area.

- `building_coverage_municipal_land`: union intersected with the land proxy / land-proxy area.
- `building_coverage_municipal_gross`: union / gross area.
- `footprint_overlap_excess_fraction`: (sum of clipped individual areas − union area) / sum; zero for no footprint mass.

This prevents overlaps/parts from inflating coverage. Geometric area is m²; source `shape_area` and unmaintained sqft are not used. Source observation age and inclusion of ancillary/nonstandard structures remain limitations. The publisher's metadata says August 2015; a September 2026 filename does not make the footprints a 2026 survey.

## B2: reported building stories

For each unique ACTIVE building, use the `stories` field only when numeric and strictly positive. Assign whole buildings by largest overlap. Duplicated IDs are dissolved; conflicting reported values are withheld. Compute unweighted median and P90 among eligible reports, plus positive-report count / all assigned ACTIVE building entities.

Zeros are missing reports, **not zero-storey buildings**; missing reports are never defaulted to one. The truncated `no_stories` field means **below-ground stories**, according to the attached publisher dictionary. Do not combine it with or treat it as a competing total. Building entities differ from SP's cadastral entities; source reporting coverage may be strongly selective. `z_coord` is not a height measure and `bldg_sq_fo` is not actively maintained. B3 remains missing.

## U1: observed primary-use area composition

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

## U3: supplied ACS aggregate resident density

Require 77 unique source names and one-to-one exact normalized name agreement with the boundary names; save the resulting ID crosswalk. Divide each provided `total_population` by projected gross km², conserving the complete supplied population total. Do not perform tract allocation or fabricate block populations from these aggregates.

The CSV labels all rows 2023, but its source period, margins of error and Community Area estimation method are unresolved. Status is `provisional_population_provenance`; the year suffix describes the **supplied label**, not a verified point-in-time census. A Census-block version is still required for the planned common support and U4.

## Missing features and interpretation

M2, M7, B3, U2 and U4 each have an explicit `*_unavailable` column/long-table row with null value and a reason. This preserves all 13 planned families without pretending construction is complete. M5/U5 remain dropped. All records set `strict_cross_city_accepted=false`.

Use the local output for source-quality review and descriptive exploration. No Chicago-to-Brás ranking, fitted model, paired SP reconstruction, or claim of complete model readiness is produced by this release. The data requirements document gives the next acquisition and acceptance tasks.
