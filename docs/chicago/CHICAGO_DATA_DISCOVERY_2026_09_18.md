# Chicago missing-data discovery and validation — 18 September 2026

> **September 19 update:** nine Chicago-filtered datasets are now downloaded and independently validated. See the [acquisition checkpoint](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md). The sample-only status below describes the earlier discovery stage.

## Outcome and scope

The user paused modeling to prioritize finding and validating data. This investigation used Firecrawl search/scrape on official publisher pages, then direct public Socrata and ArcGIS API queries to check schemas, counts and small samples. No model, feature values or accepted common definitions were changed.

**Parcel geometry and useful assessor records are accessible. Complete, comparable building floors and constructed area are still not established.** Most importantly, a field's presence in a schema does not establish that it contains usable data: commercial `stories` and `gross_building_area` are entirely null in the 2024 slice tested.

Downloaded material consists of documentation, metadata, aggregate query results and small samples—not full county inventories. Raw evidence is local in `.firecrawl/chicago-data-2026-09-18/` (Git-ignored). The [evidence directory](../../analysis/results/Chicago/data_discovery_2026_09_18/) contains request URLs/results, sample geometry checks and SHA-256 inventory. Counts below are observations on the retrieval date, not guarantees about future API responses.

## Attribute priorities

| Attribute | What these sources provide | What remains unresolved |
|---|---|---|
| M7: parcel structure | Cook dated parcel polygons; DuPage polygons; PIN and related-PIN fields | Physical parcel definition, condo/unit collapse, multi-parcel entities, exact city coverage and matching vintages |
| B2: building floors | Residential story categories; commercial schema has stories | Exact counts above three floors; split-level interpretation; commercial 2024 stories absent; condo/DuPage stock coverage |
| B3: constructed area | Residential exterior-measured area; condo unit/building areas; commercial building/rentable areas; benchmarking GFA | Area definitions, missing stock, repeated parent areas, campus/multi-building attribution and comparable SP denominator |
| U1: use mix | Assessor classes/use fields; DuPage property classes; benchmarking primary use | Harmonized ontology, observed versus fiscal use, mixed-use allocation and entity versus area weights |
| B1: footprint coverage | Newly discovered official Cook 2022 footprints | Independent alternative/QA only; source/date consistency and exact Chicago coverage need evaluation |

Population, employment, CTA schedules, CMAP land use and matched Overture extracts already exist locally. This investigation targeted the remaining cadastral/building gaps rather than reacquiring those inputs.

## Dataset register

### D01 — Cook County parcels, tax year 2024

**Found through:** Firecrawl search of Cook Central. **Publisher:** Cook County GIS; boundaries maintained by the County Clerk. [Catalog](https://hub-cookcountyil.opendata.arcgis.com/datasets/cookcountyil::parcels-historical-2024/about), [live layer/API](https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer/2024).

**What it is:** dated tax-parcel polygons for 2024. API confirms **1,431,510 features**, polygon geometry, EPSG:3435, 2,000-record query limit. Actual fields include `Name` (alias PIN14), `PIN10`, `PARCELTYPE`, `AssessorBLDGclass` and municipality. Ten geometry-bearing records were retrieved; sampled rings are nonempty and valid.

**Helps:** M7 geometry and assessor joins; U1 classification context. **Limits:** tax parcels are not automatically physical lots or buildings. Full geometry duplication/overlap and PIN uniqueness have not been tested. Preserve text keys and interpret `PARCELTYPE` before filtering. Dates are assessment-year boundaries, not a 2026 cadastral snapshot. This is a verified candidate, not a claim that 2024 is the newest available release.

**Acquisition:** page ArcGIS query results using object IDs or stable ordering; reconcile counts and record hashes. Project geometry to EPSG:26916 before metric work. Publisher item carries an as-is/no-warranty disclaimer.

### D02 — Cook Assessor Parcel Universe

**Found through:** [Assessor's official data hub](https://datacatalog.cookcountyil.gov/stories/s/Assessor-s-Open-Data/gzdr-q7c4/). [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe/nj4t-kc8j), [metadata](https://datacatalog.cookcountyil.gov/api/views/nj4t-kc8j.json).

**What it is:** historical PIN/year records with class, geographic assignments and location information. The catalog reports history from 1999 and semi-monthly updates. API schema and 100 selected-field records for 2024 were retrieved successfully. A whole-history grouped count timed out after 90 seconds; no independently verified full row count is claimed.

**Helps:** join spine for M7/B2/B3/U1, missing-record denominators and Chicago assignments. `pin`, `pin10`, `year`, `class`, `chicago_community_area_num` are present. **Limits:** not parcel polygons; geography may be centroid-based or derived from tax districts, and those assignments can disagree. Current-year records may be unfinished. PINs need leading-zero preservation. Older geography can be backfilled. The current-year view `pabr-t5kh` was identified in the official hub but not separately sampled; use the historical source for reproducible year selection.

### D03 — Cook single- and multi-family improvement characteristics

**Found through:** Assessor hub. [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Single-and-Multi-Family-Improvement-Chara/x54s-btds), [metadata](https://datacatalog.cookcountyil.gov/api/views/x54s-btds.json).

**What it is:** residential improvement/building records keyed by PIN, year and card, rather than one row per parcel. API schema and 100 records for 2024 validated. Relevant fields: `card`, `pin_num_cards`, `tieback_key_pin`, proration rates, `char_bldg_sf`, `char_type_resd`, `char_use`, `char_ncu`, `class`.

**Helps:** B2 categorical stories, B3 residential area, M7 related-PIN investigation, U1 use context. The publisher describes area as exterior-measured; its garage field documents subtraction of included garage area. This is not automatically equivalent to SP total constructed area.

**Actual 2024 county-wide story counts:** 423,268 one-story; 113,088 1.5-story; 431,119 two-story; 38,535 “3 Story +”; 96,639 split-level; 23 null. Total **1,102,672 improvement rows**. These are county figures, not Chicago coverage estimates. The independent whole-history year-count request timed out; the narrower story aggregation succeeded.

**Limits:** top-coded and split-level categories cannot yield exact floor-count medians/P90 without a justified policy. Residential coverage is not all building stock. Tieback/card proration describes taxable-value allocation, not a proven floor-area allocation rule. Multi-card and tieback records require duplicate-area checks. [Publisher transformation source](https://github.com/ccao-data/data-architecture/blob/master/dbt/models/default/default.vw_card_res_char.sql) confirms the residence-type field originates from the stories field; downloaded categories are already descriptive strings.

### D04 — Cook residential condominium characteristics

**Found through:** Assessor hub. [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Residential-Condominium-Unit-Characterist/3r7i-mrz4), [metadata](https://datacatalog.cookcountyil.gov/api/views/3r7i-mrz4.json).

**What it is:** unit PIN/year records, with `pin10`, `char_building_sf`, `char_unit_sf`, `tieback_key_pin`, `is_parking_space`, `is_common_area`, `bldg_is_mixed_use` and unit counts. Metadata, 100 2024 records and year counts validated: **457,304 rows for 2024; 456,849 for 2026**. The current year remains provisional.

**Helps:** M7 tax-unit grouping; B3 unit/building-area candidates; U1 mixed-use and non-livable-unit distinctions. **Limits:** publisher describes sparse characteristics collected from listings and other sources, expanded by triad since 2021. Building area repeats on unit records: never sum it per unit. `pin10` is a grouping lead, not a validated one-to-one footprint ID; reconcile complexes, multiple buildings and tiebacks. No exact stories field appears in the validated schema. Sample retrieval does not establish area completeness or consistency within each parent.

### D05 — Cook commercial valuation data

**Found through:** Assessor hub. [Dataset](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Commercial-Valuation-Data/csik-bsws), [metadata](https://datacatalog.cookcountyil.gov/api/views/csik-bsws.json).

**What it is:** reassessment inputs consolidated from township workbooks. `keypin` identifies a commercial valuation entity and `pins` lists associated parcels. Fields include `bldgsf`, `gross_building_area`, `netrentablesf`, `stories`, `property_type_use` (through 2023), and `subclass2` (2024 onward).

**Validation:** schema, 100 2024 records, year totals and whole-2024 non-null counts succeeded. Years present: 2021–2025. **2024: 32,931 rows; 30,166 have `bldgsf`; 5,983 have `netrentablesf`; zero have `gross_building_area`; zero have `stories`.** These counts measure non-null entries, not positive/accurate values or unique buildings.

**Helps:** B3 commercial-area candidates, M7 related-PIN links, U1 fiscal-use context. **Does not currently solve B2 for the tested 2024 slice.** Each year covers the reassessed triad, not all county properties. Multiple rows per key PIN can represent classes/models; publisher explicitly warns that no combination of columns is guaranteed unique. First-pass valuation data does not incorporate later appeal changes. Building and net-rentable areas must remain distinct; neither should be silently substituted for missing GFA.

The [source valuation workbook page](https://www.cookcountyassessor.com/valuation-reports) is a publisher-linked follow-up lead, not a workbook acquisition completed here. Next inspect the relevant Chicago-year workbooks for floor counts and area definitions; their existence does not guarantee missing values can be recovered.

### D06 — DuPage ParcelsRealEstate

**Found through:** Firecrawl search and official county digital-map directory. [Catalog](https://gisdata-dupage.opendata.arcgis.com/datasets/DuPage::parcelsrealestate/about), [API layer](https://gis.dupageco.org/arcgis/rest/services/DuPage_County_IL/ParcelsWithRealEstateCC/FeatureServer/0), [item metadata and terms](https://www.arcgis.com/sharing/rest/content/items/b47d0bd9cef14b2fbeec45bc0df50935?f=pjson).

**What it is:** assessment polygons joined to real-estate records, described as updated weekly. API confirms **337,345 features**, EPSG:3435, polygon geometry and 1,000-record query limit. Catalog update timestamps are from 2025; weekly-refresh wording alone does not prove the effective vintage of every current record.

**Actual fields:** `PIN` (10-character key), `ACREAGE`, `ACRE_SOURCE`, `MUNICIPALITY`, `REA017_PROP_CLASS`, `GIS_Prop_Class`, assessed-value fields and district codes. Catalog prose names `PROPCLASS`; the live API uses different names. Schema inspection found no building floor-area or stories fields. Improvement valuation is money, not floor area.

**Validation:** total count and 10 county-wide geometry records succeeded. Exact `UPPER(MUNICIPALITY) = 'CHICAGO'` returned **504 records**; 10 of those were sampled with geometry. A preliminary contains-Chicago query returned 8,115 and included West Chicago—it is explicitly rejected as a city filter. Both sample sets have valid, nonempty rings. No exact spatial intersection with project boundaries has yet been run.

**Helps:** M7 Cook/DuPage coverage and U1 broad fiscal-use classes. **Limits:** not a B2/B3 source; exact Chicago coverage, historical matching, condominium geometry duplication and acreage semantics still require auditing. `ACRE_SOURCE` distinguishes calculated/deeded/unverified values. Never combine DuPage PINs with Cook PINs without county-qualified keys.

**Terms:** the item's license text prohibits repackaging/reselling/distributing the real-estate information without written county permission. Retain raw downloads locally; do not publish or redistribute this source layer. Whether a proposed derived publication is permitted needs review against those terms. No permission request was sent.

### D07 — Cook County building footprints, 2022

**Found through:** [Cook Central What's New](https://hub-cookcountyil.opendata.arcgis.com/pages/whats-new), which announces a January 2026 release. [Catalog](https://hub-cookcountyil.opendata.arcgis.com/maps/7c4f47a3b32944e58c5f18652880fc05), [API](https://gis.cookcountyil.gov/traditional/rest/services/buildingFootprint_2022/MapServer/0).

**What it is:** polygons extracted from 2022 LiDAR/imagery, with `Area_SQFT`, `Year`, `Ground_Z`, `Max_Point`, `Height`; county-provided parcels informed splitting. API confirms **1,960,186 features**, EPSG:6455 and 2,000-record limit. Ten geometry records retrieved; sampled rings valid/nonempty. Publisher documents height from the highest interior LiDAR point relative to ground.

**Helps:** B1 alternative/independent footprint QA; height diagnostics. **Limits:** footprint area is not total floor area. Height cannot be converted to stories for B2 without a separately justified model. Vertical units/datum still need confirmation before height analysis. The count is county-wide and includes structures, not just principal occupied buildings. Source vintage is 2022 despite publication in 2026. It does not replace matched cross-city Overture inputs automatically. As-is disclaimer applies.

### D08 — Chicago Energy Benchmarking

**Found through:** Firecrawl search of Chicago's official data portal. [Dataset](https://data.cityofchicago.org/Environment-Sustainable-Development/Chicago-Energy-Benchmarking/xq83-jr8c), [metadata](https://data.cityofchicago.org/api/views/xq83-jr8c.json).

**What it is:** annual property reporting for large buildings, with GFA, primary use, reporting status and building count per property. Schema, 100 records and annual counts validated. API years are **2014–2023**; **3,438 rows for 2023**. Publication/update date is not the reporting year.

**Helps:** B3 independent checks for large properties; U1 primary-use cross-check. `gross_floor_area_buildings_sq_ft` includes interior tenant/common/basement/storage space but excludes interior parking. `of_buildings` flags campus/multi-building reporting; `id` is a benchmarking property ID, not a PIN. **Limits:** reporting scope is buildings over 50,000 ft²; not all-stock coverage. Non-submission/exemption and campus boundaries matter. Do not add these areas to assessor areas or infer one record equals one building.

### D09 — Chicago Energy Benchmarking covered-building register

**Found through:** same search. [Dataset](https://data.cityofchicago.org/Environment-Sustainable-Development/Chicago-Energy-Benchmarking-Covered-Buildings/g5i5-yz37), [metadata](https://data.cityofchicago.org/api/views/g5i5-yz37.json).

**Validation:** schema, **3,693 records** count and 100-record sample. Contains `building_id`, `cohort_sector`, `cohort_size`, verification year and location. **Helps:** D08 reporting coverage and joins. **Limits:** coverage list rather than measured GFA inventory; cohort-size category is not precise area. Version alignment with annual D08 reporting remains untested.

### D10 — Cook class definitions and data documentation

**Found through:** official dataset descriptions. [Classification PDF](https://prodassets.cookcountyassessor.com/s3fs-public/form_documents/classcode.pdf), [publisher data SOP](https://github.com/ccao-data/wiki/blob/master/SOPs/Open-Data.md).

**Validation:** Firecrawl extracted the PDF definitions and SOP successfully. Categories distinguish exempt, vacant, residential, commercial and other assessment types. **Helps:** U1 interpretation and M7/B2/B3 class-specific coverage checks. **Limits:** a tax classification is not a complete observed-use ontology or precise stories field. Current definitions may not match historical years; codebook version/effective date must be frozen. PDF extraction should be checked against the original before implementing a crosswalk. No ontology mapping was constructed.

## Other leads and rejected substitutes

- [DuPage property lookup](https://www.dupagecounty.gov/government/departments/supervisor_of_assessments/property_lookup_portal.php) and [township assessor directory](https://www.dupagecounty.gov/government/departments/supervisor_of_assessments/township_assessor_directory.php): official pages verified. County directs characteristics to township assessors. These are discovery routes, not a validated bulk improvement dataset. Determine intersecting townships spatially before pursuing their exports.
- [DuPage digital map page](https://www.dupagecounty.gov/elected_officials/county_clerk/clerk_data_request/digital_map_data.php): verifies county open-data route. Dataset-specific license above is more directly relevant than generic download availability.
- [DuPage ParcelViewer](https://gis.dupageco.org/parcelviewer/): scraper received unsupported-browser content; no successful data validation claimed.
- [CookViewer](https://maps.cookcountyil.gov/cookviewer/): scrape showed an outage notice/UI documentation; not an acquisition endpoint. [Comparable-property page](https://www.cookcountyassessoril.gov/find-comparable-properties) and [property details page](https://www.cookcountyassessoril.gov/assessor-property-details) are lookup aids, not bulk stock sources.
- [2023 Assessor refresh notice](https://datacatalog.cookcountyil.gov/stories/s/Assessor-2023-Open-Data-Refresh/9bqn-cfsv/): useful migration evidence. Avoid superseded archived tables. The current hub, not the historical notice, selected D02–D05.
- Cook 2021 parcels are linked from the Universe documentation but were not downloaded; D01 provides the dated 2024 polygon candidate validated here.
- Assessed values, sales, permits, appeals, addresses and neighborhood tables linked by the hub were not pursued as new stock measurements. They do not establish missing all-stock floors/GFA. Tax-exempt stock remains an explicit coverage gap; a list of exempt parcels alone would not fill it.

## Next data-collection checkpoint — modeling remains paused

1. Download and freeze **city-intersecting** Cook 2024/DuPage parcel candidates using pagination/count reconciliation, exact boundary intersections and county-qualified keys. Resolve DuPage effective year and terms before redistribution. Validate overlap, repeated geometries, PIN lengths and condo cases.
2. Acquire matching assessor slices and build a **coverage audit only**, including missing/positive area rates by class and district; inspect tiebacks, condo parents, multiple cards and repeated commercial entities. Do not calculate accepted attributes yet.
3. Inspect Chicago commercial source workbooks for missing stories/GFA and document each file's year, sheet, definitions, joins and actual populated fields. If unavailable, record the gap rather than treating schema fields as data.
4. Locate township building/improvement exports for the spatially verified DuPage part of Chicago, including exempt/airport stock where applicable. Needed fields: dated county/PIN, improvement/building ID, parent relationships, stories, area and area definition, actual use, coverage exclusions and reuse terms. No township bulk source has been validated yet.
5. For large buildings, evaluate benchmarking GFA and campus matching as corroboration. Keep parking exclusions and source-year differences explicit. Consider Cook 2022 footprint acquisition only for a planned QA comparison.
6. Update this register with each acquisition's validation outcome. Resume modeling only when the user returns to that work. Exact stories across all stock and a common constructed-area definition remain unresolved; finding public sources alone does not complete Chicago's model.
