# São Paulo attribute documentation

## Chicago documentation

This document continues to describe the frozen **SP** release. For Chicago, use [CHICAGO_ATTRIBUTE_DOCUMENTATION.md](../chicago/CHICAGO_ATTRIBUTE_DOCUMENTATION.md); its local-source definitions and acceptance statuses differ.


This document describes the **implemented** release `sp_attributes_2026_09_11_v1`: 96 municipal districts, 13 families, 23 primary candidate columns and 77 total columns. M5 and U5 were removed. It covers inputs, source processing, formulas, interpretation and limitations. No similarity model has been fitted.

Start with the [primary table](../../analysis/results/SP/tables/attributes_primary.csv), [full table](../../analysis/results/SP/tables/attributes_wide.csv), and [long table with provenance](../../analysis/results/SP/tables/attributes_long.parquet). Every exact output-column name is listed in the catalogue at the end. The [construction report](../../analysis/results/SP/reports/ATTRIBUTE_REPORT.md) records execution and validation; the [method decisions](SP_METHOD_DECISIONS.md) explain the M2/M6/U2 experiments.

## 1. Shared definitions and processing

### Geography and aggregation

The reporting unit is the municipal district, **not a neighborhood inferred from postal codes and not the entire metropolitan extraction rectangle**. IDs are two-character strings: Brás `10`, Itaim Bibi `35`, Grajaú `30`. All geometric measurements use **SIRGAS 2000 / UTM zone 23S, EPSG:31983**, with coordinates in metres.

For district d:

- `G_d`: gross district area in m²; `A_d = G_d / 1,000,000` in km².
- `W_d`: area of the unioned supplied water polygons inside the district.
- `L_d = G_d − W_d`: land area in m². Parks and other open land are retained.
- `Q_p(x)`: unweighted sample quantile at probability p, using pandas' default linear interpolation. `median = Q_0.5`; `IQR = Q_0.75 − Q_0.25`. Quantiles of discrete floors can therefore be fractional.

District preparation repairs geometries, assigns small inter-district overlaps to ascending district ID, and preserves existing holes. The removed overlap excess was 22.067 m². Streets and footprint areas are clipped to district geometry; source objects used for counts and shape statistics retain whole-object ownership. Blocks use largest district overlap. Accepted cadastral entities inherit the prepared largest-overlap assignment; they were not reallocated for the small N02 boundary correction.

**Denominator choice matters:** M1/M2/M7/U2/U3 use gross district km²; B1 primary and B3 use land m². U4 uses allocated population. M3/M4/B2 summarize object distributions rather than dividing by district area. U1/M6 use their respective classified mass/length.

### Inputs and lineage

Paths below are relative to `analysis/`. `V3` means [work/prepared/SP/sp_prep_2026_09_10_v3](../../analysis/work/prepared/SP/sp_prep_2026_09_10_v3); `V2` means [work/prepared/SP/sp_prep_2026_09_09_v2](../../analysis/work/prepared/SP/sp_prep_2026_09_09_v2). Prepared records are intermediate inputs, not observed final district attributes.

| Source | Processing and prepared input | Families |
|---|---|---|
| Supplied municipal districts and water | Geometry repair, deterministic overlap ownership, union water, intersect district and subtract; `V3/N02/districts.parquet`, `district_land.parquet` | Common support, B1/B3 land denominators |
| Municipal logradouro street lines and classvias classification | Canonical duplicate flag, class matching and lineage; `V3/N04/edges.parquet` | M1/M6 |
| Street crossings and supplied bridge/viaduct/tunnel structures | Planar candidate generation and proximity scenarios; `V3/N05`, plus approved selection in `work/evidence/job_allocation_experiments/m2_selection_overlay.parquet` | M2 |
| Municipal cadastral blocks | Repair, eligible `Quadra` filter and whole-block district ownership; `V3/N06/blocks.parquet` | M3/M4 |
| Cadastral parcel polygons and IPTU 2026 fiscal records/dictionary | Entity resolution, unique-account area aggregation, floor eligibility and seven-category use mapping; `V3/N03`; geometry in `V2/02_parcels_tax/parcel_records` | M7/B2/B3/U1; U2 support |
| Overture mapped building polygons, release 2026-08-19.0 | Existing indexed `data/SP/Edificacoes/sao_paulo_building_morphology.gpkg`; exact tiled footprint unions in N10 | B1 |
| RAIS 2022 formal employment by CEP, IPTU and CNEFE address evidence | Postal normalization, fixed located baseline, CEP/district ancillary weights and explicit unresolved bucket; `V3/N07` and `work/evidence/job_allocation_experiments` | U2 |
| Census 2022 sectors and population | Unique sector records and district intersection-area allocation; `V3/N07/census_sectors.parquet`, `census_district_allocation.parquet` | U3/U4 |
| Supplied bus GTFS | Validated keys, calendars, times/frequencies and expected stop departures; `V3/N08/stops.parquet`, `stop_route_service.parquet` | U4 |

The [frozen source manifest](../../analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N01/manifest.json) identifies exact raw paths and hashes. It is not a complete licensing catalogue. The [attribute configuration](../../analysis/config/sp_attributes_2026_09_11.json) binds methods; old `outputs`/`processed` paths still resolve through compatibility links. Mixed source years are intentional and must not be interpreted as one simultaneous city snapshot. Structures largely reference 2004; the GTFS scenario dates do not prove feed observation date. Source periods not established are recorded as mixed vintage rather than invented.

### Shared cadastral preparation

For noncondominiums, an entity uses sector–block–lot (SQL). Condominium lot codes commonly equal `0000`, so condominiums use sector–block–condominium instead. Ambiguous/multiple-geometry identities and competing links remain excluded. N10 accepts `geometry_status = unique_geometry_candidate` with an assigned district, joins fiscal profiles, and computes positive projected polygon areas. Entity keys and parcel candidate IDs are unique in the accepted table: **1,667,297 entities**.

Fiscal accounts are distinct from physical parcels and building polygons. A condominium can have multiple accounts, and a parcel can overlap multiple buildings. Accepted accounts are counted once; account floor area is not multiplied through building–parcel overlaps. This distinction underlies M7, B2, B3, U1 and U2.

## 2. M1 — Street density

**Purpose:** describe the amount of mapped street linework relative to district size.

**Data and processing:** use canonical valid `V3/N04/edges.parquet` lines. Nine exact duplicate geometries are excluded by the canonical flag. Source carriageways remain separate; the pipeline does not collapse them into road centre lines. Intersect each line with the district, discard zero-length contacts, and assign boundary-coincident length once to ascending district ID. Self-retraced geometry is measured once by the intersection operation; separate source edges are retained.

**Formula:** `street_density_km_km2 = (sum clipped length in metres / 1,000) / A_d`.

**Primary:** one column, km/km². Larger values mean more mapped line length per gross area, not necessarily better walkability. Divided-road representation and source completeness affect the value.

**Validation:** district lengths sum to 19,369,524.694861 m and reconcile with the independent normalized city clip. Two retraced source lines initially caused a 40.00085 m audit discrepancy; aligning the audit's geometric measure resolved it without changing district values.

## 3. M2 — Intersection-density proxy

**Purpose:** approximate the density of street junction candidates while reducing obvious grade-separated false crossings.

**Data and processing:** N05 identifies planar crossings and incident source arms. Use municipal candidates with at least three source arms, then the approved `selected_m2_proxy` overlay. Exclude candidates at distance **≤5 m** from supplied `PONTE`, `VIADUTO` or `TUNEL` geometry. Count each selected candidate in its assigned district. The old `accepted_m2_junction` flag describes certified physical connectivity and is not the selection flag used here.

**Formula:** `intersection_density_proxy_5m_km2 = selected candidate count / A_d`.

**Primary:** the 5 m version. **Sensitivity:** otherwise comparable 0, 10 and 20 m exclusion versions. Zero metres still excludes geometric contact; it is not necessarily the unrestricted candidate count.

**Validation:** 107,685 municipal candidates become **106,625**, a reduction of 1,060 or approximately **0.984%**; Brás retains 244.

**Limits:** nearby valid approach junctions can be removed, while unmapped/offset structures can leave false crossings. No edge-level grade inference, validated routing graph or comprehensive carriageway consolidation is claimed.

## 4. M3 — Block size

**Purpose:** describe typical block size and within-district variation.

**Data and processing:** retain `eligible_type` blocks with a non-null district assignment, corresponding to municipal `Quadra` objects. Exclude other supplied types such as `Praca_Canteiro`, `Borda`, `CET` and `Ilha`. There are **46,798 eligible municipal blocks**. Measure the area of the whole block polygon, including the effect of holes; do not clip a border block into smaller statistical observations.

For each block b, `a_b = area(b)` in m² and `z_b = ln(a_b / 1 m²)`.

**Primary:** `block_log_area_median = Q_0.5(z)` and `block_log_area_iqr = Q_0.75(z) − Q_0.25(z)`.

**Diagnostics:** raw-area median, P25, P75 and IQR in m². Quantiles are computed on log values for the log columns; log IQR is not the logarithm of raw-area IQR. Every block has equal statistical weight.

**Limits:** results describe the eligible municipal block definition, which may differ from a road-polygonized block definition. Marsilac's log-size median and dispersion are flagged as distribution extremes, not removed as errors.

## 5. M4 — Block shape

**Purpose:** measure compactness and elongation independently of absolute block size.

**Data:** the same whole eligible block polygons as M3.

**Compactness:** for block area a and total polygon perimeter p, `C = 4πa / p²`. Hole boundaries contribute to perimeter. A circle approaches 1; more irregular or elongated polygons have lower values. A square gives π/4.

**Elongation:** calculate the minimum rotated bounding rectangle; `E = longest rectangle side / shortest rectangle side`. A square gives 1, an elongated rectangle gives a larger ratio. This measures bounding-rectangle shape, not street connectivity or orientation.

**Primary:** median and IQR of C, and median and IQR of E: four dimensionless columns. Every eligible block is equally weighted. Degenerate nonpolygon rectangles would yield missing elongation; the published primary matrix is complete.

**Validation:** synthetic square/rectangle tests, compactness bounds and elongation ≥1. Geometry resolution, holes and source block segmentation influence results.

## 6. M6 — Street-class composition

**Purpose:** describe how mapped street length is distributed among supplied road classes.

**Data and preparation:** same clipped canonical lengths as M1. N04 matches classification using normalized CODLOG, compatible address ranges and geometric coverage; the main spatial criterion is at least 80% coverage by a class's 2 m buffer, with alternative-class conflicts retained. A strict fallback requires a unique class and ≤1 m whole-geometry Hausdorff distance. The approved overlay assigns every remaining unclassified edge **Local**, including previously quarantined residuals, while preserving observed classes and imputation flags.

For class c, `model_share_c = model-class length_c / total canonical district length`. Six primary shares correspond to `arterial`, `coletora`, `local`, `rodovia`, `via_de_pedestres`, `vtr`; labels are preserved from the source rather than given unverified expanded meanings.

**Observed diagnostics:** `observed_share_c = observed-class length_c / the same total length`. These are **not renormalized to observed-only length**, so their sum is the observed fraction rather than one. `street_class_imputed_share = 1 − observed_length / total_length`.

**Validation/limits:** six model shares sum to one. About 23.85% of source length is imputed Local; classification completeness is not observed accuracy. The six primary shares are compositionally dependent and need appropriate treatment during modeling. Source matching and imputation flags remain available for sensitivity review.

## 7. M7 — Cadastral parcel density

**Purpose:** approximate parcel subdivision intensity using accepted cadastral entities.

**Data and processing:** shared entity preparation above, with projected physical polygon areas from v2 geometry. Count each unique accepted entity once in its prepared district. Do not count tax accounts, apartments or building footprints as parcels.

**Primary formula:** `cadastral_parcel_density_km2 = accepted entity count / A_d`.

**Diagnostics:** `parcel_log_area_median` and `parcel_log_area_iqr`, using `ln(physical polygon area / 1 m²)` and unweighted entity quantiles.

**Validation/limits:** municipal count reconciles to 1,667,297. This is a cadastral proxy; excluded identities, parcel-type semantics and uneven mapped coverage can affect district comparisons. Its coverage field does not establish the proportion of all real parcels captured.

## 8. B1 — Building footprint coverage

**Purpose:** estimate the fraction of district land occupied by mapped building footprints.

**Data and processing:** spatially query the existing Overture building GeoPackage in EPSG:31983. Within each district, intersect candidate polygons with disjoint 2 km tiles clipped to the district, keep positive-area pieces, union footprints within each tile, and sum union area. Intersect each union with district land for the primary numerator. Tile boundaries have zero area, and footprint overlaps do not inflate coverage. A building spanning districts contributes its actual clipped area to each, regardless of its whole-building owner in preparation.

Let `U_d` be the unioned footprint area inside gross district geometry; `U_land_d` its area on land; `S_d` the sum of individual clipped footprint areas before union.

- **Primary:** `building_coverage_land = U_land_d / L_d`.
- **Sensitivity:** `building_coverage_gross = U_d / G_d`.
- **Diagnostic:** `footprint_overlap_excess_fraction = (S_d − U_d) / S_d` (implemented as zero if S_d is zero).

All are fractions. Overlap excess quantifies duplicate spatial coverage, not a building-error probability. Validation checks union ≤ summed area and appropriate denominator area, plus a synthetic overlapping-roof tile test.

**Limits:** footprint mapping is not independently complete. Building height, floor count and footprint-times-floors from the source building GeoPackage are **not inputs to the chosen B2/B3 attributes**. Building–parcel overlap candidates are not accepted tax transfers.

## 9. B2 — Cadastral floor-count distribution

**Purpose:** represent typical and upper-tail reported floors using an explicit cadastral proxy.

**Data and processing:** join accepted entities to `V3/N03/parcel_fiscal_profiles.parquet`. Require `floor_proxy_eligible`, a non-null candidate and one distinct positive eligible floor report per entity. Ancillary autonomous garage/storage reports and conflicting floor reports are excluded. Multiple accounts repeating the same report do not create multiple observations. Never sum floors across apartments or substitute one floor for missing B2 reports.

**Primary:** median and P90 of eligible entity floor counts. **Diagnostic:** P75. Units are floors, not metres. Entity weighting is uniform rather than weighted by floor area, accounts or population.

**Coverage:** number of eligible floor profiles / all accepted district entities; `n_missing` counts accepted entities without an eligible value. Municipal eligible profiles reconcile to **1,548,308**.

**Limits:** cadastral entities and physical buildings are different units. Fractional quantiles can result from interpolation; they are summary statistics, not observed fractional storeys. No building-height conversion or surveyed floor-count completeness is claimed.

## 10. B3 — Cadastral constructed-area density

**Purpose:** approximate built floor-space intensity relative to district land.

**Data and processing:** use unique IPTU fiscal records with `accepted_area_aggregation`. Preserve each eligible fiscal unit's `constructed_area_m2` once, assigned through its accepted cadastral location. Sum unit areas; do not multiply through building overlaps, sum repeated parcel totals, or apply ideal fractions a second time. Unresolved accounts remain outside the accepted numerator.

**Primary formula:** `cadastral_floor_area_density = sum accepted fiscal-unit constructed area / L_d`, in m²/m². Values above one are possible with multiple floors. This is a district-wide intensity measure, not a parcel regulatory FAR calculation.

**Validation:** 3,842,434 accepted accounts contribute **581,313,100 m²** from a source total of 597,424,198 m²; 16,111,098 m² remain outside accepted allocation. The city source-area match is approximately 97.3032%.

**Limits:** that percentage measures allocation of the supplied tax source, not coverage of all real buildings. District completeness is unknown and `coverage_fraction` is null. Common-area interpretation and cadastral source scope remain limitations. This attribute is not surveyed actual gross floor area and is not calculated as footprint × floors.

## 11. U1 — Cadastral land-use composition and diversity

**Purpose:** summarize the mix of uses represented by accepted cadastral entities.

**Data and processing:** map all 38 observed use labels using the prepared dictionary to seven fixed categories: residential; commerce/services; industry/warehouse; institutional; transport/utilities; vacant; mixed/other. Entity use comes from the prepared profile. Residential ancillary garages/storage follow residential use; office ancillary garages follow commerce/services; standalone garages map to transport/utilities. Keep each entity once. Mixed/other is one category, not an invented fractional decomposition.

Two weights are calculated for classified entities: count (one vote per entity) and land area (projected whole-entity polygon area). For category c, `p_c = category weight / total classified weight`.

**Entropy formula:** `H = −sum(p_c × ln(p_c)) / ln(7)`, omitting zero terms. H=0 for a single category and H=1 for equal weights across all seven. The denominator remains ln(7), even if fewer categories occur. No usable classified mass yields missing entropy rather than zero diversity.

**Primary:** `land_use_entropy_count`. **Sensitivity:** `land_use_entropy_land_area`. **Diagnostics:** all seven category shares for each weighting (14 columns).

**Coverage:** classified entity count / accepted entity count, or classified physical area / accepted physical area for area weighting. Unknowns are excluded from entropy but retained in missing/coverage metadata. Area-weighted entropy represents cadastral land area, not floor-space composition or an areal zoning map. Larger entropy is not automatically better urban performance.

## 12. U2 — Formal employment density with CEP allocation

**Purpose:** estimate the spatial intensity of RAIS 2022 formal job links while preserving uncertainty in postal geography. Job links are not necessarily unique employed people and exclude informal work.

**Data and processing:** normalize postal keys and use the prepared RAIS totals, accepted IPTU fiscal-unit constructed area by CEP/district, and deduplicated CNEFE establishment-address evidence. Keep **3,194,165 previously located jobs fixed**. For unresolved CEP c, construct nonnegative district support `S_cd`; allocate `J_cd = J_c × S_cd / sum_d(S_cd)`. Preserve fractional jobs and the CEP total. There are no authoritative CEP polygons in the input; support is keyed to the same CEP, not arbitrary whole-district area.

Business area includes commerce/services, industry/warehouse, institutional and transport/utilities. Fiscal support retains whole-parcel district assignment; CNEFE uses prepared point assignment. The experiments did **not** split each border-crossing parcel again. Footprint/business/CEP attribution remains unresolved and pure business-footprint weighting was not executed.

**Primary `area_first`:** use business constructed-area weights; if absent, establishment-address weights; if neither is available, residential-area weights. If all are absent, keep jobs in `UNLOCATED`, outside district primary totals. Municipal allocation is **4,878,630**, leaving **508,844** unlocated, from 5,387,474 source jobs. Allocated mass contains 1,667,542 workplace-weighted and 16,923 residential-fallback jobs in addition to the fixed baseline.

**Formula for every output:** `formal_job_density_<scenario>_km2 = scenario district job total / A_d`.

| Scenario | Weighting / residual handling |
|---|---|
| area_first | Primary business area → establishment addresses → residential area; retain unlocated |
| address_first | Establishment addresses → business area → residential fallback |
| hybrid | 50/50 mixture of separately normalized business-area/address weights when both exist; otherwise available support and residential fallback |
| equal_workplace | Equal shares among districts with positive workplace evidence; residential fallback |
| residential_first | Residential area first, then workplace support; stress test |
| area_mixed | Add mixed/other fiscal area to business support, then address/residential fallbacks; 4,894,553 allocated |
| area_first_business_prior / address_first_business_prior | Corresponding base scenario plus residual spread by municipality-wide accepted business-area distribution |
| area_first_located_jobs_prior / address_first_located_jobs_prior | Corresponding base scenario plus residual spread by fixed v3 located-job distribution |

The four prior variants allocate all source jobs by assumption; they do not establish complete observed geolocation. `coverage_fraction` is the **citywide** allocated fraction repeated across districts, not measured district completeness. `n_entities` records contributing CEP allocation rows, not establishments or workers.

**Validation/limits:** CEP and city mass conservation pass. Area-first vs address-first moves 275,226.71 job links between districts; 11 districts differ by more than 10%. Code `99999999` contains 351,576 jobs without geographic support. Uneven cadastral evidence, equal-jobs-per-address assumptions, mixed source years and large-employer CEPs matter. IPTU supports both U2 allocation and B3, so their association is not independent corroboration. Independent establishment-level employment and verified addresses remain valuable additional data.

## 13. U3 — Population density

**Purpose:** estimate resident intensity within each reporting district.

**Data and processing:** use unique 2022 census sectors and source population. For sector s and district d, allocate `P_sd = P_s × area(s ∩ d) / area(s)`. Sum contributing sectors. Sectors spanning borders are split by area; population outside the district union remains an explicit residual rather than being renormalized into the city.

**Primary formula:** `population_density_km2 = sum_s(P_sd) / A_d`, people/km². Fractional counts result from allocation. `n_entities` is the number of contributing unique sectors.

**Validation:** allocated population totals **11,446,054.473149512** from source population 11,451,999; the outside residual is approximately 5,944.527. Coverage reports this citywide intersection fraction.

**Limits:** area weighting assumes uniform within-sector population, including uninhabited portions. Values are allocated census estimates, not a direct observation of each district's current population.

## 14. U4 — Population-weighted expected bus-service access

**Purpose:** estimate the bus service supply available near a typical allocated resident; it is not observed ridership, accessibility to destinations, or a walking-route travel-time measure.

**Population support:** intersect an origin-(0,0) **250 m grid** in EPSG:31983 with each positive-population census sector and district. Each positive-area piece receives an interior representative point and weight `P_j = sector population × piece area / full sector area`. This preserves U3 district population. A representative point need not be the centroid; this is a numerical integration approximation, not a household location.

**Service processing:** validate GTFS keys, service calendar, stop times and frequency intervals. For `exact_times=0`, expected service uses continuous interval/headway exposure; scheduled/exact rows count discrete departures. The prepared service is keyed by stop, route, direction and scenario window. Scenarios are weekday **2026-09-09 07:00–09:00**, Saturday **2026-09-12 09:00–11:00**, and Sunday **2026-09-13 09:00–11:00**. Missing calendar exceptions limit holiday-specific claims; the scenarios are not synchronized with 2022 population/jobs.

**Catchment and formula:** at each point j, find all stops within Euclidean radius r (400 or 800 m), including stops across district borders. For each route/direction k, take the **maximum** reachable stop departure count, then sum over k: `S_j = sum_k max_reachable_stop(expected departures_k)`. No reachable service gives zero. This avoids adding repeated nearby stops of the same route/direction as independent supply.

`bus_service_access_<window>_<radius>m = sum_j(P_j × S_j) / sum_j(P_j)`.

**Primary:** weekday/400 m. **Sensitivity:** the other five window/radius combinations. The stored unit is “expected departures per 2h per resident”: interpret it as a population-weighted mean of nearby route-direction supply over a two-hour window, not total district departures divided by residents.

**Reach diagnostics:** `population_bus_service_reach_<window>_<radius>m = sum population weights with S_j > 0 / total population weight`. These six fractions require positive service in that scenario, not merely the existence of a nearby stop.

**Validation:** all 96 population supports conserve mass; saved point-level service reconstructs district values; 800 m supply is never below 400 m. A 125 m grid refinement changes weekday/400 m by +0.57% in Brás, −0.67% in Itaim Bibi and +1.28% in Grajaú. This tests approximation sensitivity, not ground-truth accuracy.

**Limits:** uniform within-sector population, bus-only feed, representative-point approximation, Euclidean distance, missing calendar exceptions, route/direction grouping and expected rather than observed operations. Rivers, barriers, actual walking paths, rail service, reliability and destination opportunities are not modeled.

## 15. How to read quality metadata and validation

The long table supplies `family_id`, `feature_name`, `value`, `unit`, `numerator`, `denominator`, `source_version`, `observation_period`, `coverage_fraction`, `coverage_definition`, `n_entities`, `n_missing`, `method_version`, `quality_status`, `missing_reason`, and `primary_feature`.

- Ratios preserve their numerator and denominator. Distribution summaries and entropy generally have null numerator/denominator because they are not simple stored mass ratios.
- Coverage is **feature-specific**. A value of 1 can mean all eligible supplied records were consumed, not that all real-world objects were observed. Read the coverage definition. B3 completeness is explicitly unknown; U2/U3 citywide fractions are not district accuracy measures.
- `n_entities` has different units: edges, nodes, blocks, cadastral entities, fiscal accounts, CEP rows, sectors or population support points depending on the family. These counts cannot be added across families.
- `n_missing=0` does not prove complete source coverage. Explicit missing counts are particularly used for B2/U1; unlocated U2 jobs remain in experiment outputs, not in that field.
- All 23 primary columns are populated in all 96 districts. Imputed/proxy values remain identified; complete numeric matrices are not equivalent to complete observed data.
- Validation covers 96×77 unique keys, finite values, bounds, share sums, geometry, city totals, source preservation and population-service reconstruction. Five synthetic tests and 20 independent release-review checks passed. These test implementation and consistency, not independent empirical accuracy.
- There are 38 raw distribution flags using Q1−3×IQR and Q3+3×IQR. Zero-IQR columns are skipped by that rule. No flagged values were deleted, winsorized or transformed by the review.

Before similarity fitting: review proxy dependence and outliers, choose transformations and scaling, handle the dependent M6 composition, balance families with unequal column counts, and test U2/M2/B1/U4 alternatives. Source-license/observation-date documentation, cadastral semantics, improved employment geography and independent coverage checks remain improvement tasks. Chicago harmonization and grid-based morphological attributes are separate future work.

## 16. Exact output-column catalogue

This catalogue is generated from the released dictionary and includes **every one of the 77 numeric columns exactly once**. “Primary” denotes a raw candidate in the 23-column primary matrix; other columns are sensitivity or diagnostic outputs described above. ID/name fields are identifiers, not attributes. Statistical suffixes and scenario names follow the formulas in each family section.

### M1 columns

| Exact column name | Unit | Role |
|---|---|---|
| `street_density_km_km2` | km/km² | Primary |

### M2 columns

| Exact column name | Unit | Role |
|---|---|---|
| `intersection_density_proxy_5m_km2` | nodes/km² | Primary |
| `intersection_density_proxy_0m_km2` | nodes/km² | Sensitivity / diagnostic |
| `intersection_density_proxy_10m_km2` | nodes/km² | Sensitivity / diagnostic |
| `intersection_density_proxy_20m_km2` | nodes/km² | Sensitivity / diagnostic |

### M3 columns

| Exact column name | Unit | Role |
|---|---|---|
| `block_area_median` | m² | Sensitivity / diagnostic |
| `block_area_p25` | m² | Sensitivity / diagnostic |
| `block_area_p75` | m² | Sensitivity / diagnostic |
| `block_area_iqr` | m² | Sensitivity / diagnostic |
| `block_log_area_median` | ln(m²/1m²) | Primary |
| `block_log_area_iqr` | ln(m²/1m²) | Primary |

### M4 columns

| Exact column name | Unit | Role |
|---|---|---|
| `block_compactness_median` | dimensionless | Primary |
| `block_compactness_iqr` | dimensionless | Primary |
| `block_elongation_median` | dimensionless | Primary |
| `block_elongation_iqr` | dimensionless | Primary |

### M6 columns

| Exact column name | Unit | Role |
|---|---|---|
| `street_class_model_share_arterial` | fraction | Primary |
| `street_class_observed_share_arterial` | fraction | Sensitivity / diagnostic |
| `street_class_model_share_coletora` | fraction | Primary |
| `street_class_observed_share_coletora` | fraction | Sensitivity / diagnostic |
| `street_class_model_share_local` | fraction | Primary |
| `street_class_observed_share_local` | fraction | Sensitivity / diagnostic |
| `street_class_model_share_rodovia` | fraction | Primary |
| `street_class_observed_share_rodovia` | fraction | Sensitivity / diagnostic |
| `street_class_model_share_via_de_pedestres` | fraction | Primary |
| `street_class_observed_share_via_de_pedestres` | fraction | Sensitivity / diagnostic |
| `street_class_model_share_vtr` | fraction | Primary |
| `street_class_observed_share_vtr` | fraction | Sensitivity / diagnostic |
| `street_class_imputed_share` | fraction | Sensitivity / diagnostic |

### M7 columns

| Exact column name | Unit | Role |
|---|---|---|
| `cadastral_parcel_density_km2` | entities/km² | Primary |
| `parcel_log_area_median` | ln(m²/1m²) | Sensitivity / diagnostic |
| `parcel_log_area_iqr` | ln(m²/1m²) | Sensitivity / diagnostic |

### B1 columns

| Exact column name | Unit | Role |
|---|---|---|
| `building_coverage_land` | fraction | Primary |
| `building_coverage_gross` | fraction | Sensitivity / diagnostic |
| `footprint_overlap_excess_fraction` | fraction | Sensitivity / diagnostic |

### B2 columns

| Exact column name | Unit | Role |
|---|---|---|
| `cadastral_floor_count_median` | floors | Primary |
| `cadastral_floor_count_p75` | floors | Sensitivity / diagnostic |
| `cadastral_floor_count_p90` | floors | Primary |

### B3 columns

| Exact column name | Unit | Role |
|---|---|---|
| `cadastral_floor_area_density` | m²/m² | Primary |

### U1 columns

| Exact column name | Unit | Role |
|---|---|---|
| `land_use_entropy_count` | normalized entropy | Primary |
| `land_use_count_share_residential` | fraction | Sensitivity / diagnostic |
| `land_use_count_share_commerce_services` | fraction | Sensitivity / diagnostic |
| `land_use_count_share_industry_warehouse` | fraction | Sensitivity / diagnostic |
| `land_use_count_share_institutional` | fraction | Sensitivity / diagnostic |
| `land_use_count_share_transport_utilities` | fraction | Sensitivity / diagnostic |
| `land_use_count_share_vacant` | fraction | Sensitivity / diagnostic |
| `land_use_count_share_mixed_other` | fraction | Sensitivity / diagnostic |
| `land_use_entropy_land_area` | normalized entropy | Sensitivity / diagnostic |
| `land_use_land_area_share_residential` | fraction | Sensitivity / diagnostic |
| `land_use_land_area_share_commerce_services` | fraction | Sensitivity / diagnostic |
| `land_use_land_area_share_industry_warehouse` | fraction | Sensitivity / diagnostic |
| `land_use_land_area_share_institutional` | fraction | Sensitivity / diagnostic |
| `land_use_land_area_share_transport_utilities` | fraction | Sensitivity / diagnostic |
| `land_use_land_area_share_vacant` | fraction | Sensitivity / diagnostic |
| `land_use_land_area_share_mixed_other` | fraction | Sensitivity / diagnostic |

### U2 columns

| Exact column name | Unit | Role |
|---|---|---|
| `formal_job_density_address_first_business_prior_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_address_first_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_address_first_located_jobs_prior_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_area_first_business_prior_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_area_first_km2` | job links/km² | Primary |
| `formal_job_density_area_first_located_jobs_prior_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_area_mixed_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_equal_workplace_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_hybrid_km2` | job links/km² | Sensitivity / diagnostic |
| `formal_job_density_residential_first_km2` | job links/km² | Sensitivity / diagnostic |

### U3 columns

| Exact column name | Unit | Role |
|---|---|---|
| `population_density_km2` | people/km² | Primary |

### U4 columns

| Exact column name | Unit | Role |
|---|---|---|
| `bus_service_access_saturday_am_400m` | expected departures per 2h per resident | Sensitivity / diagnostic |
| `population_bus_service_reach_saturday_am_400m` | fraction | Sensitivity / diagnostic |
| `bus_service_access_saturday_am_800m` | expected departures per 2h per resident | Sensitivity / diagnostic |
| `population_bus_service_reach_saturday_am_800m` | fraction | Sensitivity / diagnostic |
| `bus_service_access_sunday_am_400m` | expected departures per 2h per resident | Sensitivity / diagnostic |
| `population_bus_service_reach_sunday_am_400m` | fraction | Sensitivity / diagnostic |
| `bus_service_access_sunday_am_800m` | expected departures per 2h per resident | Sensitivity / diagnostic |
| `population_bus_service_reach_sunday_am_800m` | fraction | Sensitivity / diagnostic |
| `bus_service_access_weekday_am_400m` | expected departures per 2h per resident | Primary |
| `population_bus_service_reach_weekday_am_400m` | fraction | Sensitivity / diagnostic |
| `bus_service_access_weekday_am_800m` | expected departures per 2h per resident | Sensitivity / diagnostic |
| `population_bus_service_reach_weekday_am_800m` | fraction | Sensitivity / diagnostic |

## 17. Reproduction references

- [Construction entry point](../../analysis/scripts/construct_sp_attributes.py): pilot-first execution, validation and exports.
- [Tabular calculations](../../analysis/scripts/sp_attributes/tabular.py): M1/M2/M3/M4/M6/M7/B2/B3/U1/U2/U3.
- [Spatial calculations](../../analysis/scripts/sp_attributes/spatial.py): B1 unions and U4 population/service integration.
- [Shared formulas and metadata](../../analysis/scripts/sp_attributes/core.py): quantification conventions and metadata defaults.
- [U2 experiments](../../analysis/scripts/experiment_sp_allocations.py): CEP weighting and scenario construction.
- [Release review](../../analysis/scripts/review_sp_attribute_release.py) and [synthetic tests](../../analysis/tests/test_sp_attributes.py).
- [Workspace architecture](README.md) and [result navigation](../../analysis/results/SP/README.md).

The release and its frozen inputs were not changed to produce this documentation. This file is the canonical SP attribute reference. Historical source and output paths in code remain supported by compatibility links.
