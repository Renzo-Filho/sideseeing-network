# Chicago functional extension and matched-source acquisition

16 September 2026. New functional release: `chi_functional_2026_09_16_v2`. The previous local Chicago release and all original SP measurements remain unchanged. This is a completed construction milestone when its independent audit passes, **not completion of cross-city harmonization**.

## New supplied inputs

- `tl_2022_17_tabblock20`: all 369,978 Illinois 2020 tabulation blocks in the 2022 TIGER release, EPSG:4269. The supplied feature-catalog XML defines `POP20` as the 2020 Census count adjusted by the Disclosure Avoidance System. Population is already supplied; another population download is unnecessary. State population sums to 12,812,508.
- `il_wac_S000_JT00_2022.csv`: 91,481 workplace blocks, 5,825,390 jobs statewide. `C000` is the total; demographic and industry columns are not added to it. All supplied IDs match the statewide block geography. Sparse absent WAC rows mean no published jobs under this source, not missing population. The file carries `createdate=20240920`; original compressed-download checksum/transfer lineage was not supplied. External completeness beyond the supplied statewide file is not claimed.
- `google_transit/`: CTA static bus/rail feed. All 5,920,320 stop-time records were checked for trip/stop references. The bus selection has 124 routes, 91,196 trips and 5,787,775 stop-time records. Calendars span September 11–November 30, 2026; there are 85 exception rows and zero frequency-template rows. America/Chicago is the declared timezone. Original extracted files and developer license remain intact.
- `Hydro_20260916.geojson`: 605 valid municipal polygons, including rivers, canals and Lake Michigan. Original records include historical edit dates, often March 2001, and 2015 portal creation timestamps. The download date is not a hydrographic observation year. It is a stronger supplied area-water source than a land-use parcel proxy, but not a certified current shoreline.

Local inputs and executable code are hashed in `validation/source_code_manifest.json`. Publisher references and qualifications are in `validation/publisher_register.json`; user-supplied files are not misrepresented as downloads made by this pipeline.

## U2/U3 allocation

Preserve 15-character GEOIDs, project blocks to EPSG:26916, and intersect whole block polygons with all 77 Community Areas. Each positive piece receives `source count × piece area / whole block area`. The support is gross polygon area, matching the original SP population support convention; reported Census `ALAND20` and `AWATER20` remain in the prepared block table and are not substituted for projected polygon area. Counts are fractional estimates after allocation, not exact official Community Area totals.

The selected 39,498 positive-overlap blocks cover Cook and DuPage. Retain every outside-city remainder and all unmatched job rows (zero here). Boundary-vintage differences leave 11,884.19 m², approximately 0.002%, uncovered by blocks. The gap geometry is saved under prepared work. No residents/jobs are invented in those gaps. The original strict 0.001% coverage check failed; investigation identified a small geometry mismatch, now explicitly reported and gated at 0.1% maximum rather than silently treated as complete coverage. Independent city-union clipping checks the allocated mass without reusing district pieces.

Allocated population is **2,745,500.3508** and allocated jobs **1,409,454.0400**. The border-block outside residuals are **36,978.6492 residents** and **48,808.9600 jobs**. The full matched-state jobs outside Chicago total **4,415,935.9600**. Gross-area density is the default. The supplied ACS aggregate is retained as a different-period/provenance diagnostic, not an equality target. Chicago Census 2020 and SP Census 2022 remain different observation periods.

U2 is an **extended area-weighted baseline**. CMAP business-area sensitivity, RAIS/LODES universe reconciliation and external file-completeness checks remain open; no strict shared employment feature is accepted.

## U4 bus service

Scenarios are Wednesday September 16, 2026, 07:00–09:00; Saturday September 19 and Sunday September 20, 09:00–11:00. All are local service windows, interpreted as half-open intervals. Apply regular calendars plus additions/removals, including prior service dates for departures after 24:00. The largest supplied departure is 25:30. Filter `route_type=3`, exclude `pickup_type=1`, retain route directions and stops outside Chicago. Rail contributes nothing. No Pace feed is included.

Split positive-population block∩district support by an origin-zero 250 m projected grid, weighting each piece by its share of the whole block area. Representative points lie inside pieces. At 400 m and 800 m Euclidean radii, take the maximum reachable stop departure count for each route/direction, then sum across route/directions. Population-weight these supplies over each district. Preserve numerator, population denominator, reached population, point count and six scenario rows per area (462 rows total). Assert pointwise radius monotonicity and district population conservation.

The supplied feed has no frequency templates. The pipeline explicitly rejects a changed feed containing them rather than silently double-counting its templates. Supporting generic frequency feeds is a future extension, not a tested capability of this release. Unknown or malformed bus times, duplicate sequences, reverse departure chronology and missing references fail construction. The current supplied feed passed these checks. Independent pilot validation uses coordinate-tree neighborhoods and an explicit per-route/direction maximum rather than the construction spatial-index join. A separate pandas audit of all raw stop times exactly reproduces 148,915 weekday, 100,950 Saturday and 89,597 Sunday scheduled stop calls; these are feed stop-call counts, not the resident-weighted index.

## Hydrography

Union all supplied hydro polygons, intersect with each Community Area, and compute land as gross minus water. Gross = land + water passes. Water inside Community Areas is **13.91398 km²**, versus **1.24108 km²** under the prior CMAP parcel proxy. Neither the original B1 values nor their frozen denominators are overwritten. New footprint pilots report both gross and hydro-land coverage and retain the source-age limitation.

## Matched Overture work

The frozen SP extraction manifest and current publisher catalog agree on `2026-08-19.0`. New acquisitions use each city's metric union buffered by 2 km, converted to WGS84 bounds. STAC asset bounds prune files; remote Parquet bbox **intersection** predicates preserve crossing objects. Each selected partition is streamed into `.part`, validated, atomically renamed and hashed; exact city filtering happens in the review stage. All source attributes and attribution fields are retained. This is buffered bounding-box extraction, not a claim of exact municipal feature membership.

`acquire_harmonized_overture.py` acquires Chicago buildings, roads/connectors for Chicago and SP. Original SP buildings are reused from the matching release. Acquisitions live under `data/<city>/overture_2026_08_19/`; catalogs under `work/prepared/shared/overture_2026_08_19/`. Each source directory has its own query/schema/count/hash manifest. Buffered extraction counts are Chicago: 1,381,239 buildings, 350,885 segments and 689,832 connectors; SP: 423,904 segments and 452,539 connectors. All extracted IDs are unique. Results of `review_matched_overture.py` live separately under `results/<city>/overture_2026_08_19_review_v1/`.

The paired road candidate excludes all service/alleys/driveways and nonmotor classes, retains motorway through residential, living streets, unclassified/unknown and link ramps, and keeps carriageways separate. It reports class shares, unknown mass and source class inventories. Access restrictions are counted but not resolved. Connector diagnostics count one arm at endpoints and two at interior connector positions; they have not passed physical-arm duplication, divided-road consolidation or access-policy review. These are candidates, **not accepted M2 or physical blocks**. No M3/M4 claim is made.

## Reproduction and remaining work

```bash
.venv/bin/python analysis/scripts/prepare_chicago_functional.py
.venv/bin/python analysis/scripts/validate_chicago_functional.py
.venv/bin/python -m unittest discover -s analysis/tests -v
.venv/bin/python analysis/scripts/review_matched_overture.py
```

The functional constructor has source/config/code signatures, stage-owned artifact hashes and checkpoints. Changed signatures fail under the same run ID. Identical completed invocations verify/reuse outputs. Development's initial coverage failure and pre-fix checkpoint are preserved under prepared work. New raw sources or changed method definitions require a new release/config. Acquisition scripts require network permission; source partition signatures prevent stale reuse.

Remaining work: business-support jobs sensitivity; cadastral stock/parent semantics for M7/B2/B3; common U1 weighting/ontology and paired SP construction; road-access/carriageway/connector fixtures; physical-block definition/pilots; geographic completeness and source comparisons; accepted common feature contract. Then, and only then, fit SP-anchored transforms and rank Chicago against Brás. No cross-city ranks or accepted common matrix are published in this milestone.
