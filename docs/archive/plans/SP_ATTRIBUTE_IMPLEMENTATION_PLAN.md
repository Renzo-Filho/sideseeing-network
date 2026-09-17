# São Paulo attribute implementation plan

Version 3 — 10 September 2026. Current methods for 13 active families: M1–M4, M6–M7, B1–B3 and U1–U4. M5 and U5 remain removed. Pair this specification with `SP_DATA_RESOLUTION_HANDOFF.md` for observed data quality and completed work.

**Execution boundary:** N10 was authorized and completed on 11 September 2026. All 96 districts have 77 numeric attributes/diagnostics/sensitivities across 13 families, with 23 primary candidate columns. U2 uses area-first allocation with unlocated jobs retained separately. M2/M6 use approved overlays. See the [construction report](../../../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md), current handoff and attribute dictionary. N11 fitting/ranking has not started.

**Baseline protection:** use `analysis/scripts/prepare_sp_v3.py` with `analysis/config/sp_preparation_v3.json`. The runner freezes raw/config hashes, checks output checkpoints and preserves the historical `sp_prep_2026_09_09_v2` baseline. Never run the old hard-coded v2 entry point against the expanded source folder. If inputs or frozen configuration change, create a new run ID.

## 1. Decision and study contract

The v3 preparation covers all 96 districts, with input QA maps and geometry checks for Brás (10), Itaim Bibi (35) and Grajaú (30). These checks do not independently certify crossing levels, parcel legal semantics or source completeness. Do not declare the complete similarity model ready merely because its input filenames exist. Publish an attribute only after its source, joins, geographic coverage and validation pass the criteria below. Keep incomplete variants separate and explicitly labeled.

The analysis unit is the **municipal district**, not subprefeitura, colloquial neighborhood, census district without a crosswalk, or the bounding box of the metropolitan building extraction. Use `cd_distrito_municipal` padded to two characters; Brás is `10`. The metropolitan building dataset contains neighboring municipalities and must be spatially restricted to the municipal district system. `in_rmsp=1` alone is insufficient.

Freeze these choices in a versioned configuration:

| Choice | Proposed version-1 definition |
|---|---|
| Metric CRS | EPSG:31983 for all geometric measurements; retain original CRS and source geometry lineage |
| Primary comparison | Brás against the other 95 municipal districts; one row per district, including Brás only once |
| Time interpretation | Mixed-date baseline: 2022 population and formal employment, 2026 tax register and Overture release, source-specific street/block/structure/transit vintages. Do not label it a synchronized 2026 census. |
| Geometry precision | Preserve source precision. Calibrate any snap tolerance with Brás inspection and sensitivity tests before freezing it. |
| Area denominators | `district_area_km2` for M1/M2/M7/U2/U3 and stop density. `district_land_area_m2` for B1/B3, requiring a documented surface-water mask. If unavailable, publish a separately named gross-area variant. |
| Missingness | Null with reason, never implicit zero. Confirmed absence may be zero. Keep numerator, denominator and coverage alongside every ratio. |
| Attribute variants | Primary B2 is now a cadastral floor-count proxy, U2 is RAIS formal employment, and U4 targets service-weighted bus access. Observed height, imputed road class and any inferred allocation remain separately labeled. |
| Grids | 250 m primary robustness grid and 500 m sensitivity grid, aligned to a fixed projected origin (0,0); clip analysis cells to the municipal boundary. |

The 13 active entries (M1–M4, M6–M7, B1–B3 and U1–U4) are **attribute families**, not necessarily 13 numeric columns. M5 and U5 are excluded from configuration, computation and model selection. Distribution summaries and road-class shares expand the matrix. Record which columns enter each model run so families with more summaries do not automatically receive more influence.

## 2. Reproducible pipeline and data products

Keep `analysis/data/SP` read-only. Store normalized/intermediate data in a new `analysis/processed/SP/<run_id>/` directory and final attributes in `analysis/outputs/sp_attributes/<run_id>/`. Retain the existing building GeoPackage unchanged; write enrichments to keyed tables or new layers.

Recommended modules and execution order:

| Module | Input/dependency | Required output |
|---|---|---|
| `00_inventory` | Raw files and source dictionaries | Manifest: path, bytes, checksum, observation date, download date, CRS, schema, source URL, license and processing version |
| `01_districts` | District polygons + `massa_d_agua.gpkg` | Valid district layer, municipal union, gross/land areas and boundary QA |
| `02_parcels_tax` | All 96 lot files + IPTU | Canonical physical parcels, normalized tax records, audited tax-to-parcel crosswalk and use mapping |
| `03_streets` | Logradouro + `classvias.gpkg` + `obra_arte.gpkg` | Canonical edges, junctions, class crosswalk, unmatched/conflicting records and topology QA |
| `04_blocks_buildings` | Road blocks + Overture + modules 01/02 | Clean blocks, municipal buildings, district intersections/assignments, building-to-parcel crosswalk |
| `05_population_activity_transit` | Census, RAIS/CEP crosswalk, CNEFE for allocation only, GTFS, stops/stations, module 01 | Normalized census, formal-job allocations and dated transit-service tables with district assignments |
| `06_features` | Normalized entities and assignments | Long-form feature table and 96-row wide table |
| `07_feature_qa` | Features and source reconciliation | Coverage tables, invariants, maps/outlier diagnostics and eligibility decisions |
| `08_similarity` | Eligible features only | Fitted transformations, loadings/covariance, distances to Brás, rankings and robustness results |
| `09_grid_and_accessibility` | Same normalized inputs; pedestrian graph when ready | Grid features and separate accessibility outputs |

Use DuckDB for large CSV scans and tabular joins; GeoPandas/Shapely for projected geometry operations; spatial indexes and tiled/batched processing for buildings and point data. A full metropolitan GeoDataFrame is unnecessary. Cache compact typed Parquet/GeoParquet intermediates. Persist rejected rows with reasons rather than silently dropping them. Checkpoint completed stages so an error in a later join does not require another source extraction.

Every long-form feature row must contain: `run_id`, `district_id`, `family_id`, `feature_name`, `value`, `unit`, `numerator`, `denominator`, `source_version`, `observation_period`, `coverage_fraction`, `n_entities`, `n_missing`, `method_version`, `quality_status`, and `missing_reason`. Use explicit status values such as `validated`, `provisional`, `blocked` and `not_applicable`. The wide matrix is generated from this table, not maintained separately by hand.

Deliver a source manifest, feature dictionary, join reports, wide/long feature tables, district GeoPackage, QA report, configuration and model-run manifest. Support both a frozen run and a rebuild from changed inputs. Tests must verify scientific invariants and join behavior, not merely repeat implementation code.

## 3. Shared spatial and identifier preparation

### 3.1 Districts and denominators

Verify exactly 96 unique district IDs and one Brás polygon. Inspect and repair the previously identified invalid LAJEADO boundary, recording area change and inspecting any components. Test district overlaps, gaps and coverage against the municipal union. Recalculate metric area; compare it with stored area fields without assuming the stored rounded values are exact.

Use the supplied `massa_d_agua.gpkg` (3,973 valid polygons, EPSG:31983). Review category coverage, union overlaps, intersect with districts and subtract the water union once. Set `district_land_area_m2 = gross_area_m2 - water_area_m2` only after conservation and visual QA. Avoid deleting parks or undeveloped land from the denominator; they are part of the urban form. Publish gross and land-area versions together where reservoir coverage materially changes results.

Apply different boundary rules to different measures:

- **Extensive area/length totals:** intersect geometries with districts so amounts are allocated, and check conservation against the citywide intersection.
- **Entity counts and distributions:** assign each whole entity once using largest overlap; use ascending district ID as the deterministic equal-area tie-break. Preserve the full object for size/shape calculations.
- **Points on boundaries:** apply a deterministic tie-break and flag the case; do not duplicate points into both districts.
- **Routing:** retain an external buffer around the city/district so shortest paths may leave and re-enter the reporting unit. Report attributes for the unit, not a graph artificially cut at its border.

### 3.2 Parcels, tax accounts and condominiums

Preserve `lo_setor`, `lo_quadra`, `lo_lote`, `lo_condomi`, `lo_tp_quad` and `lo_tp_lote` as strings. Construct a candidate ten-character SQL from sector (3), block (3) and lot (4). Keep source filename/district and feature ID separately. A repeated SQL is an investigation target, not permission to drop an arbitrary record.

Classify duplicate groups into identical geometry, cross-file duplication, legitimate multipart representation, condominium representation or conflicting geometry. Dissolve components only after confirming they represent one physical parcel. Spatial assignment, not the filename alone, determines the final reporting district. Validate parcel-type codes before defining the eligible parcel universe.

Read IPTU with semicolon delimiters and explicit types. Preserve the full contributor number and its check digit. Create a separate candidate SQL from its ten base digits; validate its structure. Preserve `ANO DO EXERCICIO`, `NUMERO DA NL`, registration date and taxpayer phase. Audit multiple launches/records per contributor before selecting the applicable observation. Do not equate tax accounts with physical lots or buildings.

Build the crosswalk in explicit stages:

1. Exact SQL match to a unique canonical physical parcel.
2. For unmatched condominium units, evaluate a **sector–block–condominium** key using `NUMERO DO CONDOMINIO` and `lo_condomi`. The executed v3 accepts unique noncompeting entity matches as a declared cadastral proxy. All 39,521 nonzero-condominium geometry rows use lot 0000, so SQL alone conflates separate condominiums within a block. Use sector–block–condominium as their entity key and SQL for noncondominiums. Quarantine multiple-geometry entity keys and the 630 competing exact/condominium matches.
3. Inspect ambiguous one-to-many matches against cadastral documentation and sample maps. Use address/spatial evidence only as a recorded secondary method, never an unrestricted nearest join.
4. Store match method, candidate count, confidence/ambiguity, matched tax records and unmatched records. Produce match rates by district, tax-account count and constructed-area mass.

For condominium area aggregation, first establish whether each field is unit-specific, shared parcel total, or already fraction-adjusted. `AREA DO TERRENO`, `AREA OCUPADA`, `AREA CONSTRUIDA` and `FRACAO IDEAL` must not all be summed or multiplied by fractions under a single generic rule. Reconcile representative condominium groups and the municipal totals. Use the physical polygon area once as the parcel-area denominator. Do not sum floor counts across apartments.

### 3.3 Streets, classification and grade separation

Replace the old CET export with `classvias.gpkg`, layer `classvias`; ignore its `layer_styles` table. Reproject its EPSG:4326 MultiLineStrings to EPSG:31983. It contains 210,740 records and no `lg_seg_id`-equivalent field. Normalize `Lg_codlog`, constrain candidates by even/odd address ranges, and assess geometric overlap/direction/distance against logradouro. A CODLOG alone is not a segment key: there are 49,114 distinct codes. Persist one-to-many, conflicting and unmatched candidates. Audit mapped length by district, not just matched record count. Determine whether the classified layer itself is an appropriate canonical network only through an explicit comparison, not a silent source swap.

The user's latest decision assigns **all remaining unclassified roads to Local**, including prior conflict-quarantined residuals, while preserving observed classes and conflict flags. This supersedes the v3 minor-road-only rule. Apply the accepted one-to-one `m6_classification_overlay.parquet` from `analysis/outputs/sp_simplification_review_2026_09_10/` as used in the completed N10 construction. It supplies 100% model classification under the assumption; 76.1491% of length is observed and 23.8509% imputed. Keep observed/model vectors separate and a no-imputation sensitivity. M6 acquisition is no longer a blocker under this declared rule.

The old export had exactly 75,000 records, but the new file alone does not prove why the old export was incomplete. Treat it as superseded input and retain historical evidence; do not publish truncation as independently verified without export metadata.

Use `obra_arte.gpkg` as grade-separation evidence. It contains 6,548 lines, including bridges, viaducts, pedestrian bridges, tunnels and pedestrian malls; 5,973 records have reference year 2004. It is not a current, complete set of crossing-level labels. Classify structure types before using them. Build a crossing review table with incident edges, associated structure, assumed level and decision. Suppress false cross-level connections while retaining same-level junctions and bridge approaches. The incoming blanket rule to exclude every node intersecting a structure can remove real intersections and will be a sensitivity diagnostic only. Unresolved crossings remain flagged and ineligible for accepted M2, rather than being silently treated as either connected or disconnected.

Keep source edges, quarantine reasons, source IDs and exact-geometry duplicate groups. Calibrate snapping and carriageway consolidation in the three pilot districts. No pedestrian-permeability feature is reinstated.

## 4. Attribute construction specifications

### M1 — Street-network density

**Inputs:** canonical logradouro edges and district polygons. Define an inclusion dictionary for `lg_tipo`; distinguish the motor-street morphology network from the pedestrian graph. Investigate passages, stairs, alleys and unnamed features rather than deciding from name alone. Avoid counting duplicated geometries or transit routes as additional streets.

**Formula:** `street_density_km_km2 = sum(length(edge ∩ district))/1000 / district_area_km2`.

**Outputs:** density, total street length, edge count and included/excluded-type shares. Use a consistent policy for divided carriageways: retain the selected convention in both cities and provide a sensitivity version if their geometry conventions differ. **Checks:** positive length, no exact geometry duplicates in the canonical measure, conservation across districts and map inspection of unusual density values.

### M2 — Structure-buffer-excluded intersection-density proxy

**Approved definition:** use the user's selected 5 m exclusion of PONTE/VIADUTO/TUNEL lines. `analysis/config/sp_current_methods.json` binds the current overlay. `selected_m2_proxy` selects municipal candidates with at least three source arms and no relevant structure within distance ≤5 m. There are 106,625 selected candidates (244 in Brás), excluding 1,060 of 107,685 candidates: 0.98435% citywide.

**Implemented N10 formula:** `intersection_density_proxy_5m_km2 = count(selected_m2_proxy)/district_area_km2`. The numerator is a selected planar-source proxy, not certified physical connectivity. Do not consume the historical `accepted_m2_junction` flag as this selection; that field remains false in frozen v3.

**Checks and sensitivities:** unique node IDs and municipal ownership, exact reconciliation to selected/excluded counts, and comparison with 0/10/20 m scenarios. Preserve source-arm and proximity flags. Divided carriageways, approach junctions, incomplete structure coverage and geometry offsets remain limitations. Do not reuse this selection as a validated routing graph. Physical-junction certification is a separate refinement rather than a prerequisite imposed on this approved descriptive proxy. The selected M2 proxy density is now included in the N10 release.

### M3 — Block-size distribution

**Inputs:** `quadra_viaria_editada`, initially the `Quadra` category. Review `CET`, `Borda`, `Ilha` and `Praca_Canteiro` separately. Repair invalid geometry and retain a reference-year field. Assign whole blocks once; do not calculate size from district-clipped fragments.

**Calculations:** area in m²; median, P25, P75 and IQR; `median(ln(area_m2/1 m²))` and `IQR(ln(area_m2/1 m²))`. Retain block count and distributions by source year. **Checks:** positive areas, outlier maps and sensitivity to eligible block definitions. The matrix initially uses median log area plus log-area IQR, with family weighting applied later.

### M4 — Block-shape distribution

Use the same block universe and assignments as M3. Calculate compactness `4πA/P²` and elongation as long side divided by short side of the minimum rotated bounding rectangle. Define perimeter consistently, including how holes are treated; flag degenerate rectangles and unusual multipart cases.

**Outputs:** median and IQR of compactness and elongation, plus valid-count coverage. **Checks:** compactness in (0,1] within numerical tolerance, elongation ≥1, expected values on synthetic square/rectangle polygons, and no shape changes introduced by district clipping.

### M6 — Street hierarchy

Preserve raw CET categories, then create a documented crosswalk to local/collector/arterial/expressway or the categories actually supported by the data. Do not force unlike categories into a familiar label without a rule.

For each class k, `observed_share_k = observed_class_length_k / total_included_street_length`. Publish `unknown_observed_share` on the same denominator; observed shares plus unknown must sum to 1. Build separate `model_share_k` values after the user-approved all-unclassified-as-Local fallback, retaining `imputed_local_share` and unresolved model-class share. Imputation must not overwrite the observed vector. Also publish conditional shares among classified length as diagnostics, not replacements for missing coverage. A large observed unknown share limits comparability even when an assumed Local assignment fills the model vector; report that uncertainty and compare the no-imputation variant. Drop one redundant compositional column or use an appropriate compositional treatment when fitting covariance-based models.

### M7 — Parcel density

Use canonical physical parcels from Section 3.2, not raw file rows, tax accounts, building footprints or vegetation-selected lots. Count whole parcels under the deterministic district-assignment rule.

**Formula:** `parcel_density_km2 = unique_physical_parcels / district_area_km2`. **Companions:** median/IQR of log parcel area and the share of parcels without matched cadastral records. **Checks:** duplicates resolved, counts reconciled to accepted entity groups, cross-district cases inspected, and an explicit statement of fiscal coverage. Absence from the cadastre does not imply vacant or unoccupied land.

### B1 — Building coverage

Read only buildings intersecting municipal districts from the indexed Overture GeoPackage. For extensive coverage, intersect full footprints with districts and compute the **union area** of overlapping footprints, using buffered tiles and a reconciliation step if needed for memory. Preserve both union area and summed individual footprint area as an overlap diagnostic.

**Formula:** `building_coverage_land = area(union(footprints) ∩ district_land)/district_land_area_m2`. Until the water mask is accepted, `building_coverage_gross` uses total district area and remains explicitly named as such. **Checks:** ratio in [0,1], district/city area conservation, imagery spot-checks and coverage by source. Unique Overture IDs do not guarantee zero geometric duplication.

### B2 — Cadastral floor-count proxy

The new primary B2 is `QUANTIDADE DE PAVIMENTOS` from IPTU, with units **floors**, not metres. Retain observed Overture heights as diagnostics only. Floor counts cannot be copied to every footprint or summed across apartments.

After physical-parcel/condominium identity is accepted, collapse repeated identical floor reports within the same accepted structure/parcel. For conflicting floor counts, preserve the range and unresolved status; decide a documented representative rule through case review before accepting a value. Do not let the number of condominium tax accounts weight the district distribution. Publish median, P75/P90 and valid-entity coverage for the explicitly defined parcel/structure entity. Zero floors remain source values until a zero/unknown/vacant rule is verified; do not silently interpret zero as an observed zero-storey building.

Name all model columns as cadastral floor-count proxies. Do not claim building-level height distribution or convert floors to metres without separate calibration. Test sensitivity to parcel identity and exclude unresolved floor conflicts from accepted quantiles with their missing share reported.

### B3 — Cadastral built intensity and volume alternatives

The selected B3 is district-level **cadastral constructed-area density**, using unique fiscal units once after linkage and aggregation checks. The supplied handoff proposes summing unit constructed areas without multiplying again by ideal fraction. The executed v3 adopts that as a declared fiscal proxy; the newly read dictionary defines the fields but does not explicitly certify that shared floor area is already prorated for every record. Aggregate accepted `AREA CONSTRUIDA` once per legitimate unit/group, geolocate it through the parcel crosswalk, and assign or area-allocate boundary parcels with the assumption recorded.

`cadastral_floor_area_density = accepted_constructed_area_m2 / district_land_area_m2` is dimensionless. For individual lots, `parcel_far = accepted_constructed_area_m2 / physical_parcel_area_m2`; describe it as a cadastral FAR proxy rather than a surveyed legal development coefficient. Never substitute permitted zoning FAR for existing construction.

Where suitable building heights exist, a separate volume density is `sum(footprint_area_m2 × height_m)/district_land_area_m2`, in metres. Do not compare unadjusted partial-height totals across districts. The existing `gross_floor_area_m2` field in the Overture file remains a reproducible **fallback scenario**, not the primary B3: most of its values assume one floor. Report tax/geometry/Overture discrepancies; do not repair one source silently to match another.

### U1 — Observed cadastral land-use mix

Map every IPTU `TIPO DE USO DO IMOVEL` label through a versioned dictionary to a fixed common vocabulary, initially residential, commerce/services, industry/warehouse, institutional, transport/utilities, vacant, and mixed/other where supported. Review all raw categories; preserve unknown rather than forcing it into the dominant class. Zoning stays contextual.

Construct two planned versions: (1) parcel-count-weighted mix and (2) parcel-land-area-weighted mix. Each physical parcel contributes once; a condominium's many accounts must not make it count as hundreds of parcels. If several uses occur in a parcel, classify it as mixed unless validated floor-area shares justify fractional allocation. A floor-area-weighted mix is a separately named sensitivity measure.

For a fixed K accepted categories, calculate `H = -sum(p_k ln p_k)/ln(K)`; never change K per district. Report each share, classified parcel count/area, unknown share and mixed-use share. Compute entropy on known classified mass with coverage recorded; suppress modeling eligibility if too much mass is unknown. Do not interpret zero entropy from no usable data as single-use land.

### U2 — RAIS formal employment density

**Current experiment results:** ten mass-conserving allocations have been executed as documented in `SP_METHOD_DECISIONS.md`. Area-first/address-first locate 4,878,630 jobs (90.5551%); separate citywide-prior variants allocate the remaining 508,844 by assumption. All 45 integration checks and three synthetic allocation tests pass. Area-first has been selected and constructed as primary, with address-first sensitivity and residual-imputation contributions reported separately. The newly identified `99999999` code contains 351,576 jobs with no geographic support; boundary splitting alone cannot resolve it. Preserve directly located, CEP-weighted, citywide-imputed and unlocated job mass separately.

Use `rais_empregos_sp_2022.csv`: 29,594 unique eight-digit CEPs and 5,387,474 reported active formal employment links. This replaces CNEFE establishment-address intensity in the primary model. It measures formal employment links reported at establishment postal locations, not unique workers, informal work or all economic activity.

Keep CEP as an eight-character string. Build a versioned CEP-to-district crosswalk from verified postal geography or geocoded establishment/address evidence. IPTU/CNEFE addresses can be candidates, but residential address frequency is not automatically an appropriate allocation weight for employment. Detect generic/central-office CEPs, multiple district matches and outliers; preserve unresolved job mass. For accepted split CEPs, publish weights summing to one and justify their basis. Never copy the full job count to every matched address/district.

`formal_job_density_km2 = allocated_formal_jobs_2022 / district_area_km2`.

Check allocated jobs plus unresolved jobs equals 5,387,474. Report coverage by job mass and CEP count. The extraction code filters positive active links and then groups by CEP; pandas grouping can exclude null CEPs before export. The saved CSV does not quantify those omitted records. Preserve that extraction limitation and reconcile against an upstream aggregate before claiming full source coverage. Do not rerun a billed BigQuery extraction merely to regenerate documentation.

CNEFE remains available for postal/geographic validation and population-allocation sensitivity. Its multi-species IDs are a modeling issue, not evidence that the dataset is inherently flawed.

### U3 — Population density

Use `densidade_demografica`: unique census-sector identifiers, `qt_populacao` and the 2022 geometry. Do not append the vulnerability file as additional population observations; the earlier audit found the same IDs, population and geometry in both.

Where an authoritative sector-to-district assignment exists, validate and use it. For true boundary crossings, use documented area allocation or an improved within-sector residential allocation and report affected population. `population_density_km2 = allocated_population / district_area_km2`. Sum counts before dividing; do not average sector density. Retain a reconciliation to the source city total and explain any excluded/outside pieces.

CNEFE dwelling locations may support a within-sector allocation refinement, but addresses are not people. An equal-per-dwelling allocation is an assumption, must conserve each sector's population, and should be compared with area weighting. Use neither the number of addresses nor IPTU tax-account counts as population.

### U4 — Service-weighted bus access

The selected primary variant uses the supplied SPTrans GTFS feed and population locations, replacing basic Euclidean proximity as the primary result. First normalize and validate routes, trips, stops, stop_times, calendar and frequencies. The feed contains 1,362 routes, 2,272 trip templates, 22,261 stops, 99,315 stop-time records and 40,402 frequency intervals. Do not mistake template counts for operated departures. Rail-station data remain separate; an SPTrans bus result is not all-mode transit accessibility.

The executed service scenarios are weekday 2026-09-09 07:00–09:00, Saturday 2026-09-12 09:00–11:00 and Sunday 2026-09-13 09:00–11:00, in America/Sao_Paulo. `N08/service_method.json` supplements the frozen run config with a 400 m binary Euclidean catchment, 800 m sensitivity, and maximum reachable stop service per route/direction before summing distinct route/directions. These are declared scenarios, not measured historical service or pedestrian-network distances. The calendar range is 2023-10-01 to 2027-04-01 and does not establish an observation date. `calendar_dates.txt`, `feed_info.txt` and `exact_times` are absent from the supplied inventory. Absence of calendar exceptions is not proof that every holiday follows the regular timetable.

For frequency-based templates, use headways and stop-time offsets to estimate stop-level departures within the selected window; distinguish exact schedules from expected service, support times beyond 24:00, and avoid counting template stop_times again as additional scheduled departures. Validate trip/route/stop/service foreign keys, positive headways, chronological offsets and overlapping frequency intervals. These parsing rules follow the [GTFS schedule reference](https://gtfs.org/documentation/schedule/reference/).

Implemented feature: for population location j, take the maximum expected stop departures among reachable stops for each route/direction, sum those route/direction maxima to obtain `S_j`, then calculate `U4 = sum_j(P_j × S_j)/sum_j(P_j)`. The 400 m binary Euclidean primary and 800 m sensitivity are recorded in `N08/service_method.json`; N10 uses representative points of intersections between 250 m grid cells, census sectors and districts, with area-proportional source-sector population. Grid origin is (0,0) in EPSG:31983. A 125 m pilot refinement is retained as sensitivity evidence. Keep frequency supply and spatial access diagnostics separate, avoid counting multiple nearby stops of the same route/direction as independent service when they represent the same boarding opportunity, and retain stops beyond district borders.

GTFS route shapes are vehicle paths, not pedestrian routing. Until a validated walking network exists, use an explicitly labeled Euclidean catchment for the service-weighted variant and report its limitation; walking-network access remains a separate future variant. No U5 is required. N10 includes population-within-reach diagnostics alongside the expected-service attributes.

## 5. Quality gates and acceptance criteria

These are **proposed project gates**, to be frozen after pilot inspection rather than presented as universal scientific standards:

| Gate | Acceptance rule |
|---|---|
| District identity | 96 unique IDs; exactly one Brás row; no unreported overlaps/gaps or unrepaired geometry |
| Entity identity | Explicit canonical IDs; unresolved duplicate/cross-file cases quarantined, not silently discarded |
| Joins | Validated cardinality and no row multiplication in extensive measures; publish matched/unmatched mass and counts by district |
| Classification coverage | Report observed coverage separately from Local-imputed coverage. The all-unclassified-as-Local overlay resolves model-class missingness by assumption; the former 95% observed-length target is diagnostic, not a blocker under the latest user decision |
| Tax coverage | Initial target ≥95% of in-scope cadastral constructed-area mass assigned without ambiguity for B3; separately assess unmatched parcels and noncadastral coverage. A high row-match rate alone does not suffice. |
| B2 proxy eligibility | One accepted floor report per declared physical entity; floors remain floors, with conflict/zero/missing coverage and entity-weighting sensitivity. |
| RAIS allocation | Unique CEP rows; accepted allocation weights sum to one; allocated plus unresolved jobs conserve the CSV total; upstream null-CEP omission documented. |
| GTFS | Referential integrity, headway/time validation, dated service assumptions and no template/frequency double counting; bus-only scope explicit. |
| Mathematical invariants | Finite ratios, nonnegative extensive quantities, shares sum to one, entropy in [0,1], compactness ≤1 within numerical tolerances |
| Conservation | District allocations reconcile to city intersections; tax area is not replicated across parcels/buildings; census allocations conserve population |
| Temporal interpretation | Every feature has an observation period; mixed-date outputs and exceptions are identified in the published report |

Test fixtures should include: a square/rectangle block, a T-junction, a planar overpass that must not connect, divided carriageways, a parcel crossing a district boundary, duplicate parcel geometry, a condominium with multiple units, one parcel with multiple buildings, zero/unknown land use, an address with shared coordinates. Validate at least Brás plus contrasting districts before the full run.

## 6. Next implementation sequence and deliverables

The detailed N11 specification is now in [URBAN_MODEL_IMPLEMENTATION_PLAN.md](URBAN_MODEL_IMPLEMENTATION_PLAN.md). Its proposed preprocessing, family distance, robustness protocol and implementation stages govern future model work; N11 remains unexecuted.

N01–N08 implement preparation; N09 audits it. Execution details and acceptance status are in the current handoff and `sp_prep_2026_09_10_v3/progress.json`. N05 produced unresolved crossing candidates, not accepted physical junctions. N07 conserved all exported job mass but located only 59.29%; it did not pass the 95% job-mass gate. The table below remains the work specification, not a claim that every acceptance criterion passed.

Current execution status: N01–N04 and N06–N08 have completed preparation; N05 has completed candidate generation but failed physical-junction acceptance; N09 integrity checks pass with family-specific exclusions. N07 employment allocation fails its 95% mass gate. N10 has since been completed; N11 remains unstarted. The resulting 13-family attribute matrix is available under explicitly declared proxy assumptions; this does not establish physical-junction truth or complete observed job geolocation. M6 has since been resolved under the user-selected Local assumption; M2 has since been approved as the 5 m exclusion proxy, and ten U2 allocations have been executed. Current results and decisions are in `SP_METHOD_DECISIONS.md`; the older v3 gate results are historical.

| Order / task | Work | Required products and acceptance |
|---|---|---|
| N01 — Isolate v3 run | Add a run/configuration argument to the preparation entry point; freeze new file hashes, source bindings and methodology flags. Keep v2 untouched. | New run manifest, environment lock and config; tests show changed inputs cannot overwrite baseline products. |
| N02 — District land geometry | Reuse validated source districts, review 22.07 m² overlap excess/14.27 m² internal slivers; integrate and union water polygons in EPSG:31983. | District gross/water/land polygons and areas; land+water=gross, no duplicated water area, positive land denominators, Brás/Grajaú maps. No model ratios yet. |
| N03 — Fiscal identity and semantics | Import dictionary, enumerate all 38 observed uses, resolve parcel types and multi-geometry SQLs; investigate 630 competing exact/condo candidates. Test unique-unit area aggregation and physical-entity floor rules. | Canonical parcel candidates with acceptance status, fiscal crosswalk, reviewed use mapping, floor-report table and account-level area eligibility; row/mass conservation and case evidence. |
| N04 — Classified street integration | Reproject classvias, build CODLOG/range/spatial matcher, resolve duplicate lines and road-type inclusion. Apply the latest user-approved all-unclassified-as-Local overlay, retaining flags and the observed vector. | Canonical edge/class lineage, observed/imputed/unknown coverage by district, unmatched/conflict queues, no-imputation comparison. |
| N05 — Junction topology | Associate structure types and crossing levels, calibrate snap/consolidation and carriageway rules on pilots. | Accepted/rejected/unresolved crossing table and junction geometry; overpass/approach synthetic tests and map review. The frozen N05 stage has no M2 density; N10 constructs the approved proxy. |
| N06 — Blocks and buildings | Normalize eligible blocks, repair audit, whole-entity assignment, indexed municipal Overture subset, footprint/parcel overlap relationships. | Normalized blocks/buildings, overlap diagnostics and mappings; area conservation and no duplicated cadastral totals. Do not redownload Overture. |
| N07 — Population and formal jobs | Execute relevant module 05 paths: unique census population, validated boundary allocation, postal/district crosswalk and RAIS allocation. Use CNEFE only where a documented allocation rationale exists. | Population counts, accepted/unresolved job mass, CEP ambiguity diagnostics, conservation checks and mixed-date metadata. |
| N08 — Transit service | Validate feed keys/calendar, derive dated expected stop service and declare spatial catchment assumptions. | Service tables by date/window/route/direction/stop, exclusion records and bus-mode scope. The frozen N08 stage has no final district access index; N10 supplies it. |
| N09 — Integrated preparation acceptance | Run Brás, Itaim Bibi and Grajaú review, then all 96 districts; audit lineage, missingness, imputation and joins. | New QA report, 96-district input-coverage table, reproducible checkpoints and current handoff update. Every unresolved gate gets a reason and affected family. |
| N10 — Attribute construction (completed) | Apply Section 4 definitions for the 13 active families after preparation acceptance. | Long-form attributes and derived wide matrix, dictionary, numerators/denominators, source dates, units and quality flags. Completed in `sp_attributes_2026_09_11_v1`; see its construction report and validation files. |
| N11 — Similarity and robustness (later) | Fit transformations/scaling, family weighting, correlation/PCA checks and distances to Brás. | Saved transforms, regularized covariance where appropriate, distance explanations and sensitivity to proxies/imputation/scales. No rankings until eligible features exist. |

N01 precedes every implementation stage. N02/N03 feed building and fiscal work; N04/N05 govern street topology; N07/N08 govern service-weighted population access. Independent preparation stages may run separately with explicit lineage, but no attribute stage may consume an unresolved candidate as accepted truth.

Pilot acceptance must include a divided road, grade-separated crossing with an actual approach junction, multipart SQL, condominium with competing keys, a CEP spanning districts, a large-employer CEP, a frequency template, and a midnight service. Use conservation, topology and cardinality invariants rather than tests that merely mirror the code.

## 7. Remaining evidence and decisions

New acquisition has supplied the named dictionaries, water, structure, class, formal-job and service files. Remaining evidence and model-design work includes: review of high-impact CEP disagreements and model sensitivity to the selected area-first U2/unlocated policy, cadastral parcel-type and unit/shared-area interpretation, and source-date/export completeness. GTFS service scenarios/catchments and the water denominator have been implemented and documented. The N10 release retains these proxy limitations; carry them into N11. Parcel-type definitions, an independent boundary reference and source licenses still need documentation. Improved measured building heights are no longer a primary B2 dependency. Employment data acquisition is no longer the U2 blocker; geolocation and coverage are.

For the later Chicago comparison, harmonize physical entities, floor-count proxy definitions, formal employment coverage, transit modes/windows, district/grid supports and time periods. Do not compare SP cadastral floors directly to Chicago measured metres. Accessibility outcomes remain a separate later study; morphological similarity does not demonstrate causation.

## 8. Evidence and versioning

Current source-review evidence: `analysis/outputs/sp_resolution_review_2026_09_10/evidence.json`; reproduce with `.venv/bin/python analysis/scripts/audit_sp_resolution.py`. This audit reads the new inputs and writes only source-review evidence.

Earlier executed preparation evidence remains under `analysis/processed/SP/sp_prep_2026_09_09_v2/`, and building validation remains alongside the existing GeoPackage. These are frozen historical results, not validation of new integrations. Do not modify their manifests to make them appear current. Source attribution and extraction details are in `BUILDING_PIPELINE.md` and the building metadata sidecars.

Change run/method version when source binding, physical-entity rules, observed/imputed treatment, allocation, denominators or service assumptions change. Consolidation history and remaining tasks live in `SP_DATA_RESOLUTION_HANDOFF.md`.
