# Chicago data sources

## Chicago data requirements and readiness

Updated 16 September 2026. This document supersedes the pre-addition local inventory in the harmonization plan. The current construction target is `chi_local_2026_09_16_v1`: a **Chicago local-source baseline**, not an accepted SP–Chicago feature matrix. Original SP attributes and model v2 remain frozen. Checkpoint history is in the [Chicago execution log](EXECUTION_LOG.md).

### What the new files resolve

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

### Family acceptance and missing work

| Family | Local construction | Requirement before a shared model |
|---|---|---|
| M1 | Municipal line density, declared source-code/status filter | Validate status N and code 4 semantics; obtain matched Overture segments for both cities; reconcile alleys, ramps, carriageways and completeness |
| M2 | **Deferred from the planned Chicago model and future cross-city score**; endpoint experiment remains historical | No current acquisition or construction requirement. Reopening would require an explicit decision and paired physical-junction/grade validation; the SP 5 m proxy is not a transferable Chicago graph rule. |
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

### Acquisition queue and acceptance tests

1. **Common physical geometry:** freeze one Overture release; query Buildings, Transportation segments and connectors over Chicago plus a buffer, and obtain the SP road companion. Record S3 paths, full query and counts; validate unique IDs, snapshot date and licenses. Reuse SP's existing matched Buildings snapshot where appropriate. Audit local-vs-Overture coverage on Loop, Near West Side, West Town, South Lawndale and O'Hare. Keep old local data as a historical comparison.
2. **Population and workplace support:** obtain 2020 block polygons/counts across the complete Chicago footprint and a matching LODES geography. Download Illinois WAC all-jobs 2022, not RAC, OD, or primary-job-only files. Preserve any nonmatched/outside totals. Run area-weighted boundary allocation with business-area sensitivity; never allocate jobs by residential population by default.
3. **Bus feed:** snapshot CTA GTFS with timestamp/hash/license. The official page publishes one current package; inspect calendar ranges before picking scenarios, rather than claiming it reproduces a historical September date. Fine population support is a prerequisite for population-weighted U4; no area-uniform or rail-only substitute is promoted.
4. **Cadastral extension:** acquire Cook parcel/condo-parent and improvement records with field documentation. Pilot mixed commercial/condominium properties before summing areas or accepting M7/B2/B3. If comparable stock measures remain unavailable, explicitly omit these families from both cities' common metric.
5. **Metadata closure:** establish the ACS CSV's exact original dataset and estimate period; document road statuses/code 4. Obtain a shoreline/hydrography source to evaluate the CMAP water proxy. Supply mixed-use allocation and common use-category policy before paired U1 construction.
6. **Paired acceptance:** reconstruct harmonized SP companions; publish matching dictionary, counts, coverage and fixture results. Freeze included families before any Chicago-to-Brás ranking. Fit/apply the same SP-anchored state to both cities only after this gate.

### Primary references

- [City building metadata API](https://data.cityofchicago.org/api/views/syp8-uezg.json) and [attached attribute dictionary](https://data.cityofchicago.org/api/assets/003C600C-3A66-4605-8E7E-2477AAE95E16).
- [City transportation layer and renderer](https://gisapps.chicago.gov/arcgis/rest/services/ExternalApps/TransLegend/MapServer/1?f=pjson). Code 4 is absent from the reviewed renderer; retain the code rather than inventing a validated label.
- [CMAP inventory](https://cmap.illinois.gov/data/land-use/land-use-inventory/) and [publisher's classification guide](https://cmap-repos.github.io/LUI-wiki/field_guide_index.html).
- [Overture Transportation](https://docs.overturemaps.org/guides/transportation/) and [Buildings](https://docs.overturemaps.org/guides/buildings/).
- [Census TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html), [LODES products](https://lehd.ces.census.gov/data/), [ACS period guidance](https://www.census.gov/programs-surveys/acs/guidance/estimates.html), and [CTA GTFS](https://www.transitchicago.com/developers/gtfs/).

## Chicago missing-data discovery and validation — 18 September 2026

> **September 19 update:** nine Chicago-filtered datasets are now downloaded and independently validated. See the [acquisition checkpoint](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md). The sample-only status below describes the earlier discovery stage.

### Outcome and scope

The user paused modeling to prioritize finding and validating data. This investigation used Firecrawl search/scrape on official publisher pages, then direct public Socrata and ArcGIS API queries to check schemas, counts and small samples. No model, feature values or accepted common definitions were changed.

**Parcel geometry and useful assessor records are accessible. Complete, comparable building floors and constructed area are still not established.** Most importantly, a field's presence in a schema does not establish that it contains usable data: commercial `stories` and `gross_building_area` are entirely null in the 2024 slice tested.

Downloaded material consists of documentation, metadata, aggregate query results and small samples—not full county inventories. Raw evidence is local in `.firecrawl/chicago-data-2026-09-18/` (Git-ignored). The [evidence directory](../../analysis/results/Chicago/data_discovery_2026_09_18/) contains request URLs/results, sample geometry checks and SHA-256 inventory. Counts below are observations on the retrieval date, not guarantees about future API responses.

### Attribute priorities

| Attribute | What these sources provide | What remains unresolved |
|---|---|---|
| M7: parcel structure | Cook dated parcel polygons; DuPage polygons; PIN and related-PIN fields | Physical parcel definition, condo/unit collapse, multi-parcel entities, exact city coverage and matching vintages |
| B2: building floors | Residential story categories; commercial schema has stories | Exact counts above three floors; split-level interpretation; commercial 2024 stories absent; condo/DuPage stock coverage |
| B3: constructed area | Residential exterior-measured area; condo unit/building areas; commercial building/rentable areas; benchmarking GFA | Area definitions, missing stock, repeated parent areas, campus/multi-building attribution and comparable SP denominator |
| U1: use mix | Assessor classes/use fields; DuPage property classes; benchmarking primary use | Harmonized ontology, observed versus fiscal use, mixed-use allocation and entity versus area weights |
| B1: footprint coverage | Newly discovered official Cook 2022 footprints | Independent alternative/QA only; source/date consistency and exact Chicago coverage need evaluation |

Population, employment, CTA schedules, CMAP land use and matched Overture extracts already exist locally. This investigation targeted the remaining cadastral/building gaps rather than reacquiring those inputs.

### Dataset register

#### D01 — Cook County parcels, tax year 2024

**Found through:** Firecrawl search of Cook Central. **Publisher:** Cook County GIS; boundaries maintained by the County Clerk. [Catalog](https://hub-cookcountyil.opendata.arcgis.com/datasets/cookcountyil::parcels-historical-2024/about), [live layer/API](https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer/2024).

**What it is:** dated tax-parcel polygons for 2024. API confirms **1,431,510 features**, polygon geometry, EPSG:3435, 2,000-record query limit. Actual fields include `Name` (alias PIN14), `PIN10`, `PARCELTYPE`, `AssessorBLDGclass` and municipality. Ten geometry-bearing records were retrieved; sampled rings are nonempty and valid.

**Helps:** M7 geometry and assessor joins; U1 classification context. **Limits:** tax parcels are not automatically physical lots or buildings. Full geometry duplication/overlap and PIN uniqueness have not been tested. Preserve text keys and interpret `PARCELTYPE` before filtering. Dates are assessment-year boundaries, not a 2026 cadastral snapshot. This is a verified candidate, not a claim that 2024 is the newest available release.

**Acquisition:** page ArcGIS query results using object IDs or stable ordering; reconcile counts and record hashes. Project geometry to EPSG:26916 before metric work. Publisher item carries an as-is/no-warranty disclaimer.

#### D02 — Cook Assessor Parcel Universe

**Found through:** [Assessor's official data hub](https://datacatalog.cookcountyil.gov/stories/s/Assessor-s-Open-Data/gzdr-q7c4/). [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe/nj4t-kc8j), [metadata](https://datacatalog.cookcountyil.gov/api/views/nj4t-kc8j.json).

**What it is:** historical PIN/year records with class, geographic assignments and location information. The catalog reports history from 1999 and semi-monthly updates. API schema and 100 selected-field records for 2024 were retrieved successfully. A whole-history grouped count timed out after 90 seconds; no independently verified full row count is claimed.

**Helps:** join spine for M7/B2/B3/U1, missing-record denominators and Chicago assignments. `pin`, `pin10`, `year`, `class`, `chicago_community_area_num` are present. **Limits:** not parcel polygons; geography may be centroid-based or derived from tax districts, and those assignments can disagree. Current-year records may be unfinished. PINs need leading-zero preservation. Older geography can be backfilled. The current-year view `pabr-t5kh` was identified in the official hub but not separately sampled; use the historical source for reproducible year selection.

#### D03 — Cook single- and multi-family improvement characteristics

**Found through:** Assessor hub. [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Single-and-Multi-Family-Improvement-Chara/x54s-btds), [metadata](https://datacatalog.cookcountyil.gov/api/views/x54s-btds.json).

**What it is:** residential improvement/building records keyed by PIN, year and card, rather than one row per parcel. API schema and 100 records for 2024 validated. Relevant fields: `card`, `pin_num_cards`, `tieback_key_pin`, proration rates, `char_bldg_sf`, `char_type_resd`, `char_use`, `char_ncu`, `class`.

**Helps:** B2 categorical stories, B3 residential area, M7 related-PIN investigation, U1 use context. The publisher describes area as exterior-measured; its garage field documents subtraction of included garage area. This is not automatically equivalent to SP total constructed area.

**Actual 2024 county-wide story counts:** 423,268 one-story; 113,088 1.5-story; 431,119 two-story; 38,535 “3 Story +”; 96,639 split-level; 23 null. Total **1,102,672 improvement rows**. These are county figures, not Chicago coverage estimates. The independent whole-history year-count request timed out; the narrower story aggregation succeeded.

**Limits:** top-coded and split-level categories cannot yield exact floor-count medians/P90 without a justified policy. Residential coverage is not all building stock. Tieback/card proration describes taxable-value allocation, not a proven floor-area allocation rule. Multi-card and tieback records require duplicate-area checks. [Publisher transformation source](https://github.com/ccao-data/data-architecture/blob/master/dbt/models/default/default.vw_card_res_char.sql) confirms the residence-type field originates from the stories field; downloaded categories are already descriptive strings.

#### D04 — Cook residential condominium characteristics

**Found through:** Assessor hub. [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Residential-Condominium-Unit-Characterist/3r7i-mrz4), [metadata](https://datacatalog.cookcountyil.gov/api/views/3r7i-mrz4.json).

**What it is:** unit PIN/year records, with `pin10`, `char_building_sf`, `char_unit_sf`, `tieback_key_pin`, `is_parking_space`, `is_common_area`, `bldg_is_mixed_use` and unit counts. Metadata, 100 2024 records and year counts validated: **457,304 rows for 2024; 456,849 for 2026**. The current year remains provisional.

**Helps:** M7 tax-unit grouping; B3 unit/building-area candidates; U1 mixed-use and non-livable-unit distinctions. **Limits:** publisher describes sparse characteristics collected from listings and other sources, expanded by triad since 2021. Building area repeats on unit records: never sum it per unit. `pin10` is a grouping lead, not a validated one-to-one footprint ID; reconcile complexes, multiple buildings and tiebacks. No exact stories field appears in the validated schema. Sample retrieval does not establish area completeness or consistency within each parent.

#### D05 — Cook commercial valuation data

**Found through:** Assessor hub. [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Commercial-Valuation-Data/csik-bsws), [metadata](https://datacatalog.cookcountyil.gov/api/views/csik-bsws.json).

**What it is:** reassessment inputs consolidated from township workbooks. `keypin` identifies a commercial valuation entity and `pins` lists associated parcels. Fields include `bldgsf`, `gross_building_area`, `netrentablesf`, `stories`, `property_type_use` (through 2023), and `subclass2` (2024 onward).

**Validation:** schema, 100 2024 records, year totals and whole-2024 non-null counts succeeded. Years present: 2021–2025. **2024: 32,931 rows; 30,166 have `bldgsf`; 5,983 have `netrentablesf`; zero have `gross_building_area`; zero have `stories`.** These counts measure non-null entries, not positive/accurate values or unique buildings.

**Helps:** B3 commercial-area candidates, M7 related-PIN links, U1 fiscal-use context. **Does not currently solve B2 for the tested 2024 slice.** Each year covers the reassessed triad, not all county properties. Multiple rows per key PIN can represent classes/models; publisher explicitly warns that no combination of columns is guaranteed unique. First-pass valuation data does not incorporate later appeal changes. Building and net-rentable areas must remain distinct; neither should be silently substituted for missing GFA.

The [source valuation workbook page](https://www.cookcountyassessor.com/valuation-reports) is a publisher-linked follow-up lead, not a workbook acquisition completed here. Next inspect the relevant Chicago-year workbooks for floor counts and area definitions; their existence does not guarantee missing values can be recovered.

#### D06 — DuPage ParcelsRealEstate

**Found through:** Firecrawl search and official county digital-map directory. [Catalog](https://gisdata-dupage.opendata.arcgis.com/datasets/DuPage::parcelsrealestate/about), [API layer](https://gis.dupageco.org/arcgis/rest/services/DuPage_County_IL/ParcelsWithRealEstateCC/FeatureServer/0), [item metadata and terms](https://www.arcgis.com/sharing/rest/content/items/b47d0bd9cef14b2fbeec45bc0df50935?f=pjson).

**What it is:** assessment polygons joined to real-estate records, described as updated weekly. API confirms **337,345 features**, EPSG:3435, polygon geometry and 1,000-record query limit. Catalog update timestamps are from 2025; weekly-refresh wording alone does not prove the effective vintage of every current record.

**Actual fields:** `PIN` (10-character key), `ACREAGE`, `ACRE_SOURCE`, `MUNICIPALITY`, `REA017_PROP_CLASS`, `GIS_Prop_Class`, assessed-value fields and district codes. Catalog prose names `PROPCLASS`; the live API uses different names. Schema inspection found no building floor-area or stories fields. Improvement valuation is money, not floor area.

**Validation:** total count and 10 county-wide geometry records succeeded. Exact `UPPER(MUNICIPALITY) = 'CHICAGO'` returned **504 records**; 10 of those were sampled with geometry. A preliminary contains-Chicago query returned 8,115 and included West Chicago—it is explicitly rejected as a city filter. Both sample sets have valid, nonempty rings. No exact spatial intersection with project boundaries has yet been run.

**Helps:** M7 Cook/DuPage coverage and U1 broad fiscal-use classes. **Limits:** not a B2/B3 source; exact Chicago coverage, historical matching, condominium geometry duplication and acreage semantics still require auditing. `ACRE_SOURCE` distinguishes calculated/deeded/unverified values. Never combine DuPage PINs with Cook PINs without county-qualified keys.

**Terms:** the item's license text prohibits repackaging/reselling/distributing the real-estate information without written county permission. Retain raw downloads locally; do not publish or redistribute this source layer. Whether a proposed derived publication is permitted needs review against those terms. No permission request was sent.

#### D07 — Cook County building footprints, 2022

**Found through:** [Cook Central What's New](https://hub-cookcountyil.opendata.arcgis.com/pages/whats-new), which announces a January 2026 release. [Catalog](https://hub-cookcountyil.opendata.arcgis.com/maps/7c4f47a3b32944e58c5f18652880fc05), [API](https://gis.cookcountyil.gov/traditional/rest/services/buildingFootprint_2022/MapServer/0).

**What it is:** polygons extracted from 2022 LiDAR/imagery, with `Area_SQFT`, `Year`, `Ground_Z`, `Max_Point`, `Height`; county-provided parcels informed splitting. API confirms **1,960,186 features**, EPSG:6455 and 2,000-record limit. Ten geometry records retrieved; sampled rings valid/nonempty. Publisher documents height from the highest interior LiDAR point relative to ground.

**Helps:** B1 alternative/independent footprint QA; height diagnostics. **Limits:** footprint area is not total floor area. Height cannot be converted to stories for B2 without a separately justified model. Vertical units/datum still need confirmation before height analysis. The count is county-wide and includes structures, not just principal occupied buildings. Source vintage is 2022 despite publication in 2026. It does not replace matched cross-city Overture inputs automatically. As-is disclaimer applies.

#### D08 — Chicago Energy Benchmarking

**Found through:** Firecrawl search of Chicago's official data portal. [Dataset](https://data.cityofchicago.org/Environment-Sustainable-Development/Chicago-Energy-Benchmarking/xq83-jr8c), [metadata](https://data.cityofchicago.org/api/views/xq83-jr8c.json).

**What it is:** annual property reporting for large buildings, with GFA, primary use, reporting status and building count per property. Schema, 100 records and annual counts validated. API years are **2014–2023**; **3,438 rows for 2023**. Publication/update date is not the reporting year.

**Helps:** B3 independent checks for large properties; U1 primary-use cross-check. `gross_floor_area_buildings_sq_ft` includes interior tenant/common/basement/storage space but excludes interior parking. `of_buildings` flags campus/multi-building reporting; `id` is a benchmarking property ID, not a PIN. **Limits:** reporting scope is buildings over 50,000 ft²; not all-stock coverage. Non-submission/exemption and campus boundaries matter. Do not add these areas to assessor areas or infer one record equals one building.

#### D09 — Chicago Energy Benchmarking covered-building register

**Found through:** same search. [Dataset](https://data.cityofchicago.org/Environment-Sustainable-Development/Chicago-Energy-Benchmarking-Covered-Buildings/g5i5-yz37), [metadata](https://data.cityofchicago.org/api/views/g5i5-yz37.json).

**Validation:** schema, **3,693 records** count and 100-record sample. Contains `building_id`, `cohort_sector`, `cohort_size`, verification year and location. **Helps:** D08 reporting coverage and joins. **Limits:** coverage list rather than measured GFA inventory; cohort-size category is not precise area. Version alignment with annual D08 reporting remains untested.

#### D10 — Cook class definitions and data documentation

**Found through:** official dataset descriptions. [Classification PDF](https://prodassets.cookcountyassessor.com/s3fs-public/form_documents/classcode.pdf), [publisher data SOP](https://github.com/ccao-data/wiki/blob/master/SOPs/Open-Data.md).

**Validation:** Firecrawl extracted the PDF definitions and SOP successfully. Categories distinguish exempt, vacant, residential, commercial and other assessment types. **Helps:** U1 interpretation and M7/B2/B3 class-specific coverage checks. **Limits:** a tax classification is not a complete observed-use ontology or precise stories field. Current definitions may not match historical years; codebook version/effective date must be frozen. PDF extraction should be checked against the original before implementing a crosswalk. No ontology mapping was constructed.

### Other leads and rejected substitutes

- [DuPage property lookup](https://www.dupagecounty.gov/government/departments/supervisor_of_assessments/property_lookup_portal.php) and [township assessor directory](https://www.dupagecounty.gov/government/departments/supervisor_of_assessments/township_assessor_directory.php): official pages verified. County directs characteristics to township assessors. These are discovery routes, not a validated bulk improvement dataset. Determine intersecting townships spatially before pursuing their exports.
- [DuPage digital map page](https://www.dupagecounty.gov/elected_officials/county_clerk/clerk_data_request/digital_map_data.php): verifies county open-data route. Dataset-specific license above is more directly relevant than generic download availability.
- [DuPage ParcelViewer](https://gis.dupageco.org/parcelviewer/): scraper received unsupported-browser content; no successful data validation claimed.
- [CookViewer](https://maps.cookcountyil.gov/cookviewer/): scrape showed an outage notice/UI documentation; not an acquisition endpoint. [Comparable-property page](https://www.cookcountyassessoril.gov/find-comparable-properties) and [property details page](https://www.cookcountyassessoril.gov/assessor-property-details) are lookup aids, not bulk stock sources.
- [2023 Assessor refresh notice](https://datacatalog.cookcountyil.gov/stories/s/Assessor-2023-Open-Data-Refresh/9bqn-cfsv/): useful migration evidence. Avoid superseded archived tables. The current hub, not the historical notice, selected D02–D05.
- Cook 2021 parcels are linked from the Universe documentation but were not downloaded; D01 provides the dated 2024 polygon candidate validated here.
- Assessed values, sales, permits, appeals, addresses and neighborhood tables linked by the hub were not pursued as new stock measurements. They do not establish missing all-stock floors/GFA. Tax-exempt stock remains an explicit coverage gap; a list of exempt parcels alone would not fill it.

### Next data-collection checkpoint — modeling remains paused

1. Download and freeze **city-intersecting** Cook 2024/DuPage parcel candidates using pagination/count reconciliation, exact boundary intersections and county-qualified keys. Resolve DuPage effective year and terms before redistribution. Validate overlap, repeated geometries, PIN lengths and condo cases.
2. Acquire matching assessor slices and build a **coverage audit only**, including missing/positive area rates by class and district; inspect tiebacks, condo parents, multiple cards and repeated commercial entities. Do not calculate accepted attributes yet.
3. Inspect Chicago commercial source workbooks for missing stories/GFA and document each file's year, sheet, definitions, joins and actual populated fields. If unavailable, record the gap rather than treating schema fields as data.
4. Locate township building/improvement exports for the spatially verified DuPage part of Chicago, including exempt/airport stock where applicable. Needed fields: dated county/PIN, improvement/building ID, parent relationships, stories, area and area definition, actual use, coverage exclusions and reuse terms. No township bulk source has been validated yet.
5. For large buildings, evaluate benchmarking GFA and campus matching as corroboration. Keep parking exclusions and source-year differences explicit. Consider Cook 2022 footprint acquisition only for a planned QA comparison.
6. Update this register with each acquisition's validation outcome. Resume modeling only when the user returns to that work. Exact stories across all stock and a common constructed-area definition remain unresolved; finding public sources alone does not complete Chicago's model.

## Manual acquisition: remaining Chicago building data

Updated September 21, 2026. Validation and modeling are paused at the user's request. The following are acquisition instructions; no requests have been sent and no subscription purchased.

Save received files in `analysis/data/Chicago/manual_acquisition_2026_09_21/incoming/`, retaining their original names. The available public baseline datasets are already downloaded; there is no need to download them again.

### 1. Addison / DuPage — first priority

Open [Addison Property Search](https://www.addisontownship.com/property-search/), follow its database link, and search **0301100003** (industrial) first, then **0301200006** (leasehold). The [direct lookup](https://search.addisontownship.com/webdb/sd/addison/assessordb/search.aspx) accepts parcel numbers with or without dashes. Our earlier browser attempt stalled without a record result; this does not mean the parcel is absent.

On each matching record, download any available property record card, building/improvement details and sketch. If only a displayed detail page is available, use the browser's Print → Save as PDF. Include all pages/tabs that show stories, building area and area units/definition. Save as `<PIN>_record.pdf` (and `<PIN>_sketch.pdf` if separate). Do not save only a tax-bill/value summary; it lacks the physical attributes needed.

Start with those two records rather than manually repeating all 81 searches immediately. The exact [81-PIN list](../../analysis/data/Chicago/manual_acquisition_2026_09_21/addison_chicago_81_parcels.csv) is prepared for a batch export or later lookups. Most are exempt/airport parcels, so a residential-only dataset is insufficient.

If the lookup lacks cards or export, use the [Assessor's Office page](https://www.addisontownship.com/assessors-office/) or [county township directory](https://www.dupagecounty.gov/government/departments/supervisor_of_assessments/township_assessor_directory.php) to contact the responsible office. Ready-to-copy [Addison request text](../../analysis/data/Chicago/manual_acquisition_2026_09_21/addison_request.txt) specifies the exact records/fields and accepts an available vintage if 2024 is unavailable. Attach the 81-PIN CSV. Requested formats are preferences, not claims that those exports already exist.

**Addresses:** missing DuPage building stories, constructed area and improvement relationships (B2/B3/M7), with use information supporting U1.

### 2. Cook County — missing physical building characteristics

Use the official [data-subscription page](https://www.cookcountyassessoril.gov/data-subscription), which offers subscription inquiry, subscriber access and an official records-request route. The page does not publish a freely downloadable file that resolves the missing fields. Availability of exact stories and GFA in the subscription service is **not confirmed**; ask before purchasing anything.

Use [Cook request text](../../analysis/data/Chicago/manual_acquisition_2026_09_21/cook_request.txt) and attach [Chicago PIN scope ZIP](../../analysis/data/Chicago/manual_acquisition_2026_09_21/cook_chicago_pin_scope.zip). The ZIP contains the already acquired Chicago-linked tax PINs and PIN10 grouping keys; preserve leading zeros. This avoids requesting the whole county.

Needed: exact stories/floors; defined gross/constructed area; condo unit/building areas; physical building/card/parent keys; multi-parcel relations; and exempt/institutional stock coverage. Ask for the existing data dictionary and effective date. A new copy of the public commercial valuation table will not resolve its empty stories/GFA fields.

Official routes: [subscription inquiry/contact](https://www.cookcountyassessoril.gov/contact) and [FOIA information](https://www.cookcountyassessoril.gov/foia-freedom-information). Submit only if you choose; nothing has been sent on your behalf.

**Addresses:** remaining Cook B2/B3 gaps and M7 physical-parent relationships; use fields support U1.

### 3. Original commercial workbooks — optional, lower priority

Direct downloads returned HTTP 403 from the publisher's CloudFront file server. Firecrawl already extracted their visible table content, so retrieving the original XLSX files would recover originals/formulas but is **not known to fill the missing stories/GFA fields**. Prioritize items 1–2 above.

If your browser can download them, open the official [2024 Chicago valuation reports](https://www.cookcountyassessoril.gov/valuation-reports) and use each township's Commercial → Methodology Worksheets link. Exact links:

| Original filename | Direct XLSX | Publisher page |
|---|---|---|
| 2024.T75.PublicModel TJS_RPSC.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T75.PublicModel%20TJS_RPSC.xlsx) | [Report](https://www.cookcountyassessor.com/rogers-park-2024-commercial) |
| 2024.T77.PublicModel_2.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T77.PublicModel_2.xlsx) | [Report](https://www.cookcountyassessor.com/west-chicago-commercial-valuations) |
| 2024.T71.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T71.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/jefferson-commercial-valuations) |
| 2024.T74.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T74.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/north-chicago-commercial-valuations) |
| 2024.T76.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T76.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/south-chicago-commercial-valuations) |
| 2024.T72.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T72.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/lake-commercial-valuations) |
| 2024.T73.PublicModel_LV.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T73.PublicModel_LV.xlsx) | [Report](https://www.cookcountyassessor.com/lake-view-commercial-valuations) |
| 2024.T70.PublicModel 12-09-2025.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024.T70.PublicModel%2012-09-2025.xlsx) | [Report](https://www.cookcountyassessor.com/hyde-park-commercial-valuations) |

### What to return

Place downloaded records/exports and any supplied dictionary in the `incoming/` directory. For a manual property lookup, two initial record cards are enough to establish what the site provides before doing all 81. For an office response, keep its dataset description, effective date and usage terms alongside the files. Do not send account passwords or subscription credentials.

### Acquisition status

This pass searched official acquisition routes and prepared scoped lists/request text. It did **not** acquire new building-characteristic records, rerun data validation, or resume modeling. Actual failures are distinguished above: Addison browser lookup stalled; workbook binaries returned 403; Cook's additional-data route requires inquiry/subscriber access rather than offering a known public file.

## Chicago M3/M4 external-source review — updated 27 September 2026

### Finding

External data can improve Chicago block construction and validation, but no reviewed source is yet a complete, verified polygon layer of physical street blocks. The [26 September bounded ROW/land pilot](../../analysis/results/Chicago/chicago_m3_row_land_2026_09_26/README.md) tested the most promising Cook sources and acquired DuPage cadastral block polygons for O'Hare. The Chicago-only model does not require a São Paulo counterpart for this work.

| Source | What it can resolve | Limitation / current status |
|---|---|---|
| [CMAP LUI 2023 transportation codes](https://cmap-repos.github.io/LUI-wiki/1500_TransportationCommunicationsUtilities.html) | `1511` rail right-of-way and `1512` roadway parcels supply some actual polygon edges. The source is already local. | These are classified parcels, not a complete road-surface or physical-block layer. Adding rail edges already created false narrow polygons in the Chicago pilot. |
| [Cook 2025 right-of-way polygons](https://gis.cookcountyil.gov/traditional/rest/services/RightOfWay_Cadastre/MapServer/2025) | Direct polygon candidate for active road/rail corridors; Cook describes the source as [tax-exempt ROW digitized from recorded plats](https://catalog.data.gov/dataset/rightofway). | New bounded checks below are promising, but citywide completeness, alley treatment and legal-versus-physical boundaries remain unverified. Filter out vacated, abandoned and private ROW; the layer year is not a survey date. Cook excludes Chicago's DuPage portion. |
| [Cook Road Edge polygons](https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/7) | Mapped pavement polygons distinguish ordinary roads from alleys (`TYPE=5`) and can check ROW gaps. | Geometry vintage is not established by this layer; pavement excludes some sidewalk/ROW land and is not the block boundary by itself. |
| [DuPage Parcel Blocks](https://gis.dupageco.org/arcgis/rest/services/ParcelSearch/DuPageAssessmentParcelViewer/MapServer/0) | Official cadastral block polygons cover the held DuPage parcel area in O'Hare and can support a county-boundary join. | Tax/cadastral block polygons are not yet verified physical street blocks or road ROW; airport parcels need a separate rule. |
| [DuPage deeded ROW](https://gis.dupageco.org/arcgis/rest/services/OpenData/ROW/MapServer/0) | Direct polygon source for some rights-of-way in the DuPage part of O'Hare. | The bounded extract adds only 0.100 km² in O'Hare and barely changes Road Edge outside-ROW area. Its returned numeric `ROW_TYPE` values do not match the published named domain, so active-road filtering remains unresolved. |
| [DuPage hydrography polygons](https://gis.dupageco.org/arcgis/rest/services/Hydrography/DPMS_LakesPonds_Service/MapServer/0) | Additional water source for O'Hare's DuPage side; five polygons intersect the Community Area in the bounded extract. | The fresh airport water control is on the Cook side, so this layer cannot be judged against that point; source imagery vintages are older/mixed. |
| [Cook Lake polygons](https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/8) | Covers both fresh Cook-side water controls, including Lake O'Hare omitted from Chicago's local Hydro layer. | Bounded two-point result only; evaluate the county source more broadly before a citywide water exclusion. |
| [Cook 2024 ground parcels](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md) | Already acquired 613,802 Chicago-intersecting parcel rows; ground-parcel continuity can distinguish a land block from an enclosure cutting through property. | Some false street fragments still contain parcels. Leasehold/elevated/condo records overlap ground parcels; alleys divide parcel unions. The first seven PIN digits indicate a [tax block **or quarter section**](https://tax.illinois.gov/content/dam/soi/en/web/tax/localgovernments/property/documents/ptax-1-t.pdf), not a guaranteed physical block. |
| [OSM Illinois extract](https://download.geofabrik.de/north-america/us/illinois.html) | Road classes, service/driveway distinctions, bridges, tunnels, layer tags, and selected [road-area/traffic-island polygons](https://wiki.openstreetmap.org/wiki/Key:area:highway). | Another mapped source, not independent ground truth or guaranteed complete road-area mapping. Inspect coverage by selected case before using its edges. A statewide extract is available, but no new download is needed until a small query is specified. |
| [2020 Census blocks](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2020.html) | Ready-made Chicago-area polygons already acquired; useful as a reference and as a separately named *tabulation-block* size/shape alternative. | Census blocks can follow non-street boundaries, so their sizes/shapes cannot silently be labeled physical street blocks. [Census documentation](https://catalog.data.gov/dataset/tiger-line-shapefile-2024-state-illinois-il-2020-census-block) explicitly includes invisible administrative and line-of-sight boundaries. |
| [URBANE Chicago block data](https://zenodo.org/records/19931112) | A newly published external comparator reporting 14,291 Chicago block polygons. | Its record says geometry comes from OSM streets and Microsoft building footprints, not independently checked property-side public-street boundaries. It cannot serve as ground truth for this M3/M4 contract. The distributed Chicago file is a Python pickle, which would require a safe conversion workflow before local use. |
| [Chicago sidewalk polygons](https://catalog.data.gov/dataset/sidewalks-097b1) and [Cook orthophotos](https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/info/iteminfo) | Sidewalk edges and current imagery can help reviewers label where a candidate block boundary lies. | The sidewalk release is marked draft and last updated in 2012; imagery is a visual reference rather than a block dataset. Cook imagery was already used in the held-out review. |

### Bounded check of existing CMAP polygons

Using the local `LUI_2023_view_332920193481040239.gpkg`, read only `LANDUSE='1511'` and `LANDUSE='1512'` within the Chicago bounding box, project to the existing district CRS and intersect four contrasting Community Areas. These are **source-area diagnostics**, not block boundaries or a completeness estimate:

| Community Area | Rail ROW 1511 area (km²) | Roadway 1512 area (km²) | 1512 share of gross area |
|---|---:|---:|---:|
| Loop (`CHI:32`) | 0.0925 | 0.0886 | 2.061% |
| South Lawndale (`CHI:30`) | 0.7656 | 0.0760 | 0.640% |
| Roseland (`CHI:49`) | 0.4902 | 0.4219 | 3.384% |
| O'Hare (`CHI:76`) | 0.2743 | 0.0181 | 0.052% |

The source field guide defines `1512` as a **linear parcel dominated by roadway**; it does not claim all paved streets are represented. The low and variable mapped share rules it out as a stand-alone universal street-surface mask. The previous rail-ROW addition produced false slivers, so `1511` must also remain case evidence rather than an automatic block edge.

### Bounded pilot outcome

The [30-tile case test](../../analysis/results/Chicago/chicago_m3_external_sources_2026_09_25/README.md) compares 13 previously reviewed block polygons, a Loop grade control, eight newly frozen cases and eight low-Census-overlap challenge rows with OSM, CMAP `1511/1512`, Census blocks and Cook orthophotos. OSM public-road perimeter support rejects the known industrial-yard false block and retains all eight new visually plausible blocks, but also **retains three newly reviewed false enclosures**: a road median, a rail-edge strip and a traffic wedge. Two challenge-mode duplicates and one repeat of the known industrial polygon are counted once for evidence. OSM `area:highway` and CMAP road/rail parcels are incomplete polygon layers. The proposed OSM-edge rule therefore fails as a physical-block acceptance rule; M3/M4 remain unaccepted.

### More promising polygon-first alternative — 26 September 2026

A bounded, read-only spatial intersection of six saved cases with the official Cook ROW service found **100% active road-ROW overlap** for the false road median, rail-edge strip and traffic wedge. Two visually plausible centerline-enclosed blocks had **29.3% and 38.0%** overlap: their old geometry includes part of the surrounding street corridors. The false industrial-yard fragment had **0%** road-ROW overlap, so ROW coverage alone cannot reject interior subdivisions. The official Road Edge polygon layer covers the road median completely, the traffic wedge by 63.5%, and the rail-edge strip by 41.1%; it is corroboration rather than a complete mask. These are case checks, not a citywide completeness result.

The existing Cook parcel polygons provide the complementary land test. Three new false median/rail/wedge cases had **0% parcel overlap**, while two plausible cases had **62.0–71.6%** overlap. Parcel occupancy alone also fails: the industrial fragment is fully parcel covered, but its polygon cuts across two much larger ground parcels. Thus the construction should start from **land and ROW polygons**, not polygonized street axes: active road ROW separates land islands; ground parcels and public-land polygons support the land side and reveal cuts across parcels; alley gaps are rejoined by an explicit alley rule; road-edge polygons and orthophotos check omissions. Define the block boundary at the property/ROW edge before calculating M3 area or M4 perimeter. Treat rail ROW, water and stacked roads separately rather than adding every line as a divider.

This is a **proposed method**, not approved M3/M4. The next section records the bounded test. [Chicago's airport spans Cook and DuPage](https://www.flychicago.com/business/CDA/factsfigures/Pages/facility.aspx), so a Cook-only ROW layer cannot complete all 77 Community Areas.

### 26 September Cook ROW, land and DuPage block pilot

The [reproducible case report](../../analysis/results/Chicago/chicago_m3_row_land_2026_09_26/README.md) acquired six bounded Cook ROW and Road Edge extracts, compared 29 saved review rows (26 distinct polygons) with ROW land components and 2024 BaseParcels, and acquired the official DuPage Parcel Blocks around O'Hare. Eight of 11 distinct visually false enclosures fall wholly inside active road ROW. Raw ROW cuts plausible street blocks along alleys; an exploratory alley-open variant matches 14 of 15 plausible old candidates at IoU ≥0.90 after ROW is subtracted. That match is **not independent validation** of the property-side outline.

The exceptions matter. `C_M3_01` joins a much larger land component where the Cook ROW divider is absent or ambiguous. An industrial-yard false enclosure sits inside a much larger land component and tax group despite 100% parcel coverage. Median compactness changes from 0.696 for centerline candidates to 0.578 for matched land components, so M4 cannot inherit centerline shape. In O'Hare, 73.7% of ordinary road-edge area lies outside Cook active-road ROW. The acquired 27 DuPage Parcel Block polygons cover 99.942% of the held DuPage parcel union, but their physical street-boundary meaning is untested. These are selected-case and bounded-area diagnostics, not 77-area accuracy estimates. **M3/M4 remain unaccepted.**

The [fresh, source-blind tile continuation](../../analysis/results/Chicago/chicago_m3_fresh_tiles_2026_09_26/README.md) chose 12 locations before viewing source imagery or block candidates. One analyst then sketched 11 fully visible blocks in six tiles and four non-block controls from orthophotos. Raw ROW matches only 3/11 sketches at IoU ≥0.5, while an alley-open ROW variant matches 11/11 (median IoU 0.827). These hand-sketched rectangles are a small new diagnostic, **not** citywide recall. A freeway median remains a 5,306 m² land component under ROW alone; Road Edge reduces it to 873 m². Water and airport open land remain separate false-component risks.

The `C_M3_01` divider is **West Veterans Place**: OSM names it as a residential street, a class-4 municipal centerline runs about 98 m along the candidate side, and adjacent parcels change tax group. Cook ROW and Road Edge omit this side. A [topology follow-up](../../analysis/results/Chicago/chicago_m3_veterans_repair_2026_09_27/README.md) found that the earlier 8–12 m seam was caused by subtracting the existing ROW before union, a numerical overlay artifact of about 8 × 10⁻⁹ m². Directly unioning the centerline-guided nonparcel corridor isolates the six-parcel face at every tested 6–20 m search width. These parcels are inputs to the corridor, so that overlap is not independent boundary accuracy; no width or general repair rule is accepted. The official DuPage deeded ROW layer adds just 0.100 km² inside O'Hare, leaving the Road Edge outside combined ROW fraction at 73.64% versus 73.74% Cook-only. The queried `ROW_TYPE` values conflict with the layer's published domain labels. Chicago's local Hydro layer misses one fresh O'Hare pond, but Cook's Lake polygon layer covers it; the point is outside DuPage, so DuPage hydro is not the relevant source there.

### Next pilot

#### 2022 classified LiDAR follow-up

The [targeted point-cloud test](../../analysis/results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26/README.md) extracted two Cook 2022 LAS tiles through HTTP byte ranges, without downloading the countywide archive. In a motorway core, building-class returns support a narrow genuine frontage block (29% of returns) while the two false slivers with strong raster height have zero building-class and 44–57% vegetation-class returns. At West Veterans Place, road-surface-class returns follow the 71 m gap in the present ROW/Road Edge masks. A bridge-deck cluster sits about 6.38 m above local ground. These observations make LiDAR useful for a context-aware review and gap-repair queue. They do not supply public-road status or a property-side M4 boundary, and one mapped street control had almost no road-class returns. The delivered class metadata also contains a code-label inconsistency, so source and class provenance must be checked before citywide use.

The [11-alert named-street screen](../../analysis/results/Chicago/chicago_m3_named_gap_repair_2026_09_27/README.md) found only the West Veterans case gains an additional closed local face from a 10 m parcel-gap corridor. Several other municipal alert lines overlap mapped parcels or have stacked-road context; two downtown corridors add substantial area without closing a face. Preserve these as unresolved alerts pending grade and boundary review.

The [new six-window reference test](../../analysis/results/Chicago/chicago_m3_reference_zones_v2_2026_09_27/README.md) compared selected ordinary blocks in CHI:49, 57 and 63. ROW + Road Edge + 3 m alley reopening has a 1.0–7.6% median absolute area error by zone against single-analyst rectangular orthophoto outlines, compared with 28.0–34.3% for municipal-centerline enclosures. This supports further M3 development, but the CHI:57 and CHI:63 reference inventories omitted candidate faces. One apparent CHI:57 split is excluded because mapped W 46th Street stops short of S Tripp Avenue and the continuation's public status is unproven. The rectangular sketches are weak M4 references; a 10 m simplification can greatly change compactness and changes one matched candidate area by 10.4%. Neither M3 nor M4 passes the Chicago release gate.

1. Resolve the confirmed named-street ROW gap (`C_M3_01`) with a stable centerline-guided parcel-gap rule and independent legal/physical boundary review; define alley, rail, water, park, private-road, airport and grade rules without accepting every tax-group edge as a street edge.
2. Use the newly acquired DuPage deeded ROW and hydro layers only after checking their type/vintage and airport coverage. Freeze construction and rejection rules and trace a larger independent reference that inventories **all true and missed** physical blocks in selected zones. Measure precision, recall, boundary displacement and M4 shape tails by context.
3. If the polygon-first method passes, rebuild/QA all 77 areas. If it cannot pass citywide support, a separately named **2020 Census tabulation-block size/shape** feature remains an alternative with a changed estimand.

## Chicago M3/M4 storage audit — 27 September 2026

### Decision before a citywide run

The proposed **2D candidate generation and manual repair ledger can be designed to fit the current disk**, but it must stream small geographic batches and enforce a storage budget. Do not download citywide LiDAR or retain full-resolution imagery for every block. The current filesystem has **13,908,897,792 bytes free (12.95 GiB)** and is 95% used. `/tmp`, Curio, and this repository are on the **same filesystem**; moving files among them does not create free space. No files were deleted in this audit.

| Directory | Measured disk use | Interpretation |
|---|---:|---|
| `/home/renzo/Documents/GitHub/curio` | ~50 GiB | Includes ~17.3 GiB of registered application artifacts, ~16 GiB of scratch data, ~6.8 GiB of Git history, and ~1.9 GiB of webpack cache. |
| This `sideseeing-network` repository | ~32 GiB | Includes ~16 GiB `analysis/data`, ~7.6 GiB `analysis/work`, ~6 GiB Git history, and ~1.7 GiB Python environment. |
| Current M3 classified-LAS working directory | ~2.2 GiB | Two downloaded LAS files; small analytical outputs and receipts are elsewhere. |
| Current M3 results directories | Generally <70 MiB each | Maps dominate these pilot outputs; vector/CSV result files are small. |

#### Size of the proposed operation

The six locally cached Cook ROW and Road Edge extracts total **38.9 MiB of GeoJSON** across Community Areas covering **68.2 of 597.7 km²** (11.4% of Chicago's Community Area area). A simple area extrapolation gives **~341 MiB** of raw 2D source GeoJSON citywide. This is an order-of-magnitude estimate, not a peak-space guarantee: road density, halo overlap, exceptional districts, temporary geometry files, and repeated renderings can raise it. A compressed GeoParquet or GeoPackage candidate/repair table should be much smaller than a full-city orthophoto or point cloud; measure actual bytes and face counts after the first tenth of the city before setting a final budget.

The expensive scenario is **retaining 3D and imagery everywhere**. The two targeted Cook LAS tiles already occupy ~2.2 GiB, and the LiDAR pilot used only two tiles. The next citywide stage should therefore use 2D generation, an audit queue, and imagery viewed or cached only for selected cases. For flagged 3D cases, extract one LAS tile at a time, keep derived class/profile metrics and a small evidence image, then remove the raw tile after its receipt and hash have been recorded if it is no longer needed. Do not turn the entire point cloud or all orthophotos into a local citywide cache.

**Execution budget:** run one geographic batch at a time, retain a single canonical compressed block table plus repair ledger, and cap new persistent M3 files at **3 GiB** during the pilot. Keep **at least 8 GiB free**; stop and inspect before crossing that floor. The 3 GiB cap is a design constraint, not a measured citywide requirement. Start with about one tenth of the city and record source, temporary, candidate, image, and evidence sizes separately; revise the cap only from observed growth. Ensure global block IDs and seam stitching work without keeping every tile's intermediate polygon copy.

### Cleanup proposals, ranked

These are **proposals only**. Curio is outside this task's writable workspace, and its application data must be cleaned with its references intact.

| Priority | Candidate | Potential recovery | Condition / cost |
|---|---|---:|---|
| 1 | Curio frontend webpack cache: `/home/renzo/Documents/GitHub/curio/utk_curio/frontend/urban-workflows/node_modules/.cache/webpack` | ~1.9 GiB | Generated build cache; will rebuild when Curio frontend runs. No Curio/webpack process was seen during this audit. |
| 2 | This repository's two raw LAS files in `analysis/work/chicago_m3_lidar_point_pilot_2026_09_26/` | ~2.14 GiB | Keep the small results, receipts, hashes, scripts and figures. Reproducing point-level tests later requires re-downloading the two 633.7/764.9 MB compressed ZIP members and extracting them. Preserve if the immediate next run needs point-level checks. |
| 3 | This repository's old `.git/objects/pack/tmp_pack_*` files | ~1.10 GiB | Five temporary pack files date from 10–14 September; no Git packing process was observed. Verify Git is idle and repository integrity before removal. **Do not delete normal `pack-*.pack` files.** Curio has a further ~0.09 GiB old temporary pack. |
| 4 | Curio's `.curio/data/artifacts` repeated large Parquet payloads | Up to **16.09 GiB** without losing distinct bytes | 27 files of 417.6 MiB have one identical SHA-256; 37 files of 156.0 MiB have another identical SHA-256. All but two tiny artifact files are registered in Curio's DuckDB catalog. Do **not** unlink them wholesale. First determine whether old sessions can be pruned through Curio. If all paths must remain, consider a separately reviewed byte-identical deduplication preserving every filename and database reference, with Curio stopped and a rollback plan; hard links are unsafe if any payload is edited in place. |
| 5 | Curio `scratch_data` copies of source files already in this repository | At least **8.16 GiB** among three verified examples | SHA-256 confirms identical independent copies of SP building morphology (4.37 GiB), Chicago building permits (2.76 GiB), and Chicago building footprints (1.03 GiB). The footprint file also appears in Curio's catalog and installed user dataset copies. Map Curio path dependencies before replacing a scratch copy with a reference to the canonical source; do not remove catalog-installed data solely because its bytes match. Other scratch copies may add savings after checksums. |
| 6 | Curio's `.curio/test-large-df-data` | ~0.11 GiB | Test output, likely regenerable; inspect test needs before removal. |

Large directories **not recommended for direct deletion**: either repository's normal `.git/objects/pack/pack-*.pack` files; Curio's entire `.curio/data/artifacts` directory or DuckDB catalog; either repository's active virtual environment; source data referenced by model scripts; and reference annotations, adjudication ledgers, receipts or compact QA reports. The `sideseeing-network` SP morphology file is referenced by several scripts, so its presence should be preserved unless those paths are intentionally migrated.

### Evidence and measurement notes

- `df -B1` on the repository returned 13,908,897,792 available bytes; both projects share the same device.
- `du -x` found Curio ~50 GiB and this repository ~32 GiB. `du` totals are rounded and nested directories must not be added to their parents.
- Curio's artifact directory has 1,293 files totaling 17.32 GiB; the DuckDB `artifacts` table has 1,396 rows. Of filesystem files, only two small files totaling 356,602 bytes lacked a matching artifact ID. The large repeated payloads are registered outputs of `curio.builtin/data-loading` and `data-loading@1`, not orphaned scratch files.
- SHA-256 was calculated for all 64 large repeated Curio artifacts. It found two exact-content groups, with 26 + 36 redundant physical copies; their combined deduplication opportunity is 16.09 GiB.
- SHA-256 was also checked for the three named Curio/`sideseeing-network` duplicate source examples; filenames, lengths and digests match. They are separate inodes with link count 1, so they currently consume separate space.
- This audit is read-only. A future cleanup should record before/after `df`, preserve path and content manifests, and perform application-level smoke checks.
