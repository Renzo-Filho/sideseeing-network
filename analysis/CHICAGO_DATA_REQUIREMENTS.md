# Chicago data requirements and readiness

## September 16 continuation: new data processed

The newly supplied Census blocks, LODES WAC, CTA GTFS and hydrography have been processed in a separate [functional extension](CHICAGO_FUNCTIONAL_EXTENSION.md), release `chi_functional_2026_09_16_v2`. It contains population/job densities for 77 Community Areas, six population-weighted bus-service scenarios (462 rows), hydrographic denominator diagnostics and explicit border residuals. **163 independent checks and 41 repository tests passed.** All strict cross-city flags remain false.

Matched Overture `2026-08-19.0` buildings for Chicago and road segments/connectors for both cities have also been acquired; paired candidate reviews are separate from the frozen releases. The older missing-data statements below describe the original v1 baseline. Current pending work concerns business-use jobs sensitivity, common morphology/entity definitions, paired SP companions and acceptance—not absence of blocks, bus schedules or workplace data.

Updated 16 September 2026. This document supersedes the pre-addition local inventory in the harmonization plan. The current construction target is `chi_local_2026_09_16_v1`: a **Chicago local-source baseline**, not an accepted SP–Chicago feature matrix. Original SP attributes and model v2 remain frozen.

## What the new files resolve

| Source | Verified content / role | Remaining qualification |
|---|---|---|
| Community Areas GeoJSON, downloaded 2026-08-31 | 77 reporting units, two agreeing ID fields, WGS84 geometries | Project to EPSG:26916; validate overlap and water accounting |
| Building Footprints GeoJSON, downloaded 2026-09-15 | 820,606 records; `bldg_id`, status, polygons and `stories` | Download date is not observation date. Official metadata says **current as of August 2015**. Most footprint provenance values are `AERIALS98`; that field is internal provenance, not proof every building dates to 1998 |
| Building metadata, fetched from publisher | `STORIES`: number of stories; `NO_STORIES_BELOW`: below-ground stories; `BLDG_SQ_FOOTAGE`: **not actively maintained** | The exported truncated `no_stories` is not an alternative total-floor field. `z_coord` is not maintained, so it is not building height |
| Municipal street centerlines | 56,338 records, classes, status, node IDs and endpoint levels | Graph and status-code semantics require validation. Class labels differ from both SP and Cook County; do not import a county crosswalk |
| CMAP LUI 2023 GeoPackage | Observed primary/secondary land-use codes and polygons, source **EPSG:3857** | Reproject before area calculation; eight-group primary-area entropy is a local alternative, not SP seven-group entity entropy. CMAP 5000 supplies a **parcel-based water proxy**, not a surveyed shoreline |
| ACS Community Area CSV | 77 rows labeled 2023, resident totals, names | Validated exact geographic-name crosswalk; source period, aggregation method and margins of error are not supplied. Provisional aggregate density only |
| Zoning GeoJSON, downloaded 2026-09-15 | Regulatory polygons | Context, not observed land use. Old inventory's invalid count belonged to the previous file; do not transfer it to this replacement |
| Building Permits GeoJSON | Permit events, descriptions, fees, dates and points | Context only. Permit issuance does not enumerate existing buildings, completed construction, floors, or gross stock area |
| `business_2652811-20190701_20260915.geojson` | 20 licensing records, one account, two address strings, with repeated renewals/licenses | Neither a full establishment census nor employee/job counts; no U2 substitution |
| CTA L stops CSV | 302 directional **rail** stop records | No bus schedules, departures, service calendars or bus-only U4 support |
| Sidewalk shapefile | Future pedestrian-outcome/context source | Not a substitute for the street graph or physical blocks |
| Cook tract population 2019 CSV | Historical tract attributes, no geometry | Not current fine-scale support |
| `morphological_data.csv` | Dummy Brás row, `ca=99`, all metrics zero | Excluded. Never interpret these as Chicago zeros |

The complete local source file list, byte sizes and SHA-256 values are in the release's `validation/source_manifest.json`. Large contextual inputs are hashed, not interpreted as model-ready data just because they are present.

## Family acceptance and missing work

| Family | Local construction | Requirement before a shared model |
|---|---|---|
| M1 | Municipal line density, declared source-code/status filter | Validate status N and code 4 semantics; obtain matched Overture segments for both cities; reconcile alleys, ramps, carriageways and completeness |
| M2 | Principal measure withheld; separate endpoint candidate experiment | Validate endpoint node/level topology, overpasses and divided roads; implement the same counting/consolidation rule in SP. Existing SP 5 m exclusion is not a transferable Chicago graph rule |
| M3/M4 | Experimental planar road-enclosure size and shape | Shared physical-block definition and paired SP reconstruction; eliminate carriageway slivers, review barriers, city-edge exclusions and large peripheral enclosures. Experimental values must not enter similarity fitting |
| M6 | Seven raw-source-code length shares | Shared ontology and unknown-mass review in both cities. Chicago 99 stays unclassified; SP's prior “unclassified = Local” decision does not silently change Chicago |
| M7 | Missing | Cook physical parcel polygons, dated tax/parent keys, condominium-unit crosswalk; distinguish tax units from physical entities |
| B1 | Exact union coverage from ACTIVE local polygons, gross and proxy-land denominators | Contemporary matched Overture release and municipal completeness comparison; reviewed hydrographic land mask in both cities |
| B2 | Positive `stories` median/P90 and coverage by whole building | Coverage bias, ancillary structures, fractional-floor semantics and building-versus-fiscal-entity reconciliation. Do not impute missing stories to one or convert height to stories |
| B3 | Missing | Verified all-stock constructed-area semantics, units and unique parent/entity allocation. Unmaintained source sqft and permits do not satisfy this requirement |
| U1 | Eight-group primary-use **area** entropy, shares and coverage diagnostics | Agreed ontology/weighting shared with SP; account for mixed/secondary uses, ROW, vacancy and unknown mass. Current eight categories are not the original SP seven-vector |
| U2 | Missing | Illinois LODES WAC 2022 all-jobs totals plus matching Census block polygons for **Cook and DuPage** coverage (O'Hare). Confirm release/geographic vintage, deduplicate totals, conserve border-block/outside mass, compare coverage with RAIS |
| U3 | Provisional supplied ACS density | Trace CSV source/period/MOE; acquire 2020 Census block counts/geometries and retain 2020-versus-2022 mismatch; validate aggregate totals and boundary allocation |
| U4 | Missing | CTA **static GTFS** bus service plus fine-scale population; select valid dates/windows, handle exceptions/frequencies/after-midnight, include outside-city stops within 800 m |

No family is yet accepted into the strict cross-city model. This is an explicit measurement-equivalence gate, not a numerical missing-value threshold. Do not zero-fill absent families or fit the original SP 23-coordinate model to these differently defined columns.

## Acquisition queue and acceptance tests

1. **Common physical geometry:** freeze one Overture release; query Buildings, Transportation segments and connectors over Chicago plus a buffer, and obtain the SP road companion. Record S3 paths, full query and counts; validate unique IDs, snapshot date and licenses. Reuse SP's existing matched Buildings snapshot where appropriate. Audit local-vs-Overture coverage on Loop, Near West Side, West Town, South Lawndale and O'Hare. Keep old local data as a historical comparison.
2. **Population and workplace support:** obtain 2020 block polygons/counts across the complete Chicago footprint and a matching LODES geography. Download Illinois WAC all-jobs 2022, not RAC, OD, or primary-job-only files. Preserve any nonmatched/outside totals. Run area-weighted boundary allocation with business-area sensitivity; never allocate jobs by residential population by default.
3. **Bus feed:** snapshot CTA GTFS with timestamp/hash/license. The official page publishes one current package; inspect calendar ranges before picking scenarios, rather than claiming it reproduces a historical September date. Fine population support is a prerequisite for population-weighted U4; no area-uniform or rail-only substitute is promoted.
4. **Cadastral extension:** acquire Cook parcel/condo-parent and improvement records with field documentation. Pilot mixed commercial/condominium properties before summing areas or accepting M7/B2/B3. If comparable stock measures remain unavailable, explicitly omit these families from both cities' common metric.
5. **Metadata closure:** establish the ACS CSV's exact original dataset and estimate period; document road statuses/code 4. Obtain a shoreline/hydrography source to evaluate the CMAP water proxy. Supply mixed-use allocation and common use-category policy before paired U1 construction.
6. **Paired acceptance:** reconstruct harmonized SP companions; publish matching dictionary, counts, coverage and fixture results. Freeze included families before any Chicago-to-Brás ranking. Fit/apply the same SP-anchored state to both cities only after this gate.

## Primary references

- [City building metadata API](https://data.cityofchicago.org/api/views/syp8-uezg.json) and [attached attribute dictionary](https://data.cityofchicago.org/api/assets/003C600C-3A66-4605-8E7E-2477AAE95E16).
- [City transportation layer and renderer](https://gisapps.chicago.gov/arcgis/rest/services/ExternalApps/TransLegend/MapServer/1?f=pjson). Code 4 is absent from the reviewed renderer; retain the code rather than inventing a validated label.
- [CMAP inventory](https://cmap.illinois.gov/data/land-use/land-use-inventory/) and [publisher's classification guide](https://cmap-repos.github.io/LUI-wiki/field_guide_index.html).
- [Overture Transportation](https://docs.overturemaps.org/guides/transportation/) and [Buildings](https://docs.overturemaps.org/guides/buildings/).
- [Census TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html), [LODES products](https://lehd.ces.census.gov/data/), [ACS period guidance](https://www.census.gov/programs-surveys/acs/guidance/estimates.html), and [CTA GTFS](https://www.transitchicago.com/developers/gtfs/).
