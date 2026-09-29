# São Paulo data preparation

## São Paulo preparation: current status and resumption handoff

**Chicago continuation (2026-09-16):** local attribute work is tracked in [CHICAGO_EXECUTION_REPORT.md](../chicago/EXECUTION_LOG.md), with current [data requirements](../chicago/DATA_SOURCES.md). This SP handoff remains historical/reference material; do not overwrite the frozen SP attributes.

### SP reference stage — corrected model; Chicago local baseline complete

The user implemented the SP model and authorized correction after independent review. The corrected `sp_urban_model_v2` now passes 26 audit checks and 30 automated tests, preserves the original 95-district Brás ranking, and includes 577 source/weight/metric/influence scenarios. Read [SP_MODEL_FIXES.md](MODEL.md) for issue/cause/fix evidence and the [v2 model report](../../analysis/results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md) for results. Original v1 model outputs and frozen source attributes remain unchanged.

Chicago source inventory, geographic support and validated local attribute construction are tracked in [CHICAGO_EXECUTION_REPORT.md](../chicago/EXECUTION_LOG.md). No cross-city model has been fitted; shared-feature acceptance and paired SP reconstruction remain pending. Full-city finer U4 support and morphological grids remain explicitly deferred. The preparation and N10 evidence below are historical stages, not a claim that N11 is still unstarted.

Updated 11 September 2026. This is the single current execution record. Pair it with [SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md](../archive/plans/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md) for attribute formulas and the ordered specification. Older status documents were removed in the prior consolidation; historical data and validation evidence remain preserved.

### N10 attribute construction — complete

The user authorized construction on 11 September 2026 and accepted `area_first` U2 as primary, address-first sensitivity, and an explicit unlocated bucket. **All 13 families are constructed for all 96 districts: 77 attribute/diagnostic/sensitivity columns, 23 primary candidate columns, and 7,392 long-form rows.** The release is `analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/`; its [construction report](../../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) documents methods, issues, tests, limitations and continuation.

Deliverables: long/wide CSV and Parquet tables, primary CSV, attribute dictionary, district GeoPackage (EPSG:31983), pilot plot, population-grid sensitivity, validation/release-review JSON, outlier review, source/code/output hashes and execution logs. Configuration: `analysis/config/sp_attributes_2026_09_11.json`; runner: `analysis/scripts/construct_sp_attributes.py`; current source/overlay binding: `analysis/config/sp_current_methods.json`. The historical v2/v3 runs and raw inputs remain unchanged.

Pilots Brás/Itaim Bibi/Grajaú passed before full construction. Five new synthetic tests passed. Release validation checks all feature keys, bounds, shares, source-total conservation, projected geometry, all 96 population supports and input preservation. A 125 m U4 support refinement changes the primary weekday/400 m result by +0.57% in Brás, −0.67% in Itaim Bibi and +1.28% in Grajaú. The 250 m primary approximation is retained with this sensitivity documented.

Two street-processing bugs were caught before release: GeoPandas `.length` referenced source geometry instead of the clipped-length column, and GEOS rejected mixed point/line shared-boundary differences. Explicit column indexing and zero-dimensional-contact filtering corrected them. The final audit also identified 40.00088 m of retraced geometry in two source edges: normalizing each edge independently aligned the audit with polygon clipping without changing district attributes. District street totals now reconcile independently to the clipped municipal network. U2 source counts and census-sector counts are retained in entity metadata.

**Historical N10 next-stage recommendation (now executed in SP model v2):** The primary CSV is unscaled and includes dependent M6 shares; transformations, family weights, compositional handling, outlier review and U2 sensitivity remain necessary before similarity rankings. The N10 stage itself did not perform model fitting or rankings; these now exist in the separate v2 model. Chicago fitting and grid-morphology attributes remain unperformed. U4's grid is population-integration support, not a completed grid-morphology analysis.

### Approved methods and experiment evidence update (after v3 acceptance)

The user has now authorized treating **all unclassified M6 roads as Local**. This was applied in a separate preparation overlay, with 23,764 new Local assignments and all observed/conflict evidence retained. Use `analysis/outputs/sp_simplification_review_2026_09_10/m6_classification_overlay.parquet` joined by edge ID; the frozen v3 files are unchanged. M6 is ready under this declared assumption, despite the historical v3 status below.

[SP_METHOD_DECISIONS.md](../DECISIONS.md) is the current issue/decision/experiment report. **M2's 5 m bridge/viaduct/tunnel exclusion is approved and implemented**, selecting 106,625 candidates including 244 in Brás. **Ten U2 allocation experiments are complete**, with all 45 integration checks and three synthetic tests passing. Area-first/address-first allocate 90.5551% geographically; separate municipality-wide priors distribute the remaining 508,844 by explicit imputation. The subsequent N10 authorization selected area-first as primary; see the completed release above.

Resume using `analysis/config/sp_current_methods.json`, which binds the frozen base, approved M6/M2 overlays and U2 experiments. New code: `analysis/scripts/experiment_sp_allocations.py` and `summarize_sp_experiments.py`. Current evidence: `analysis/outputs/sp_allocation_experiments_2026_09_10/`. That directory name is retained as the experiment ID even though this handoff was finalized on 11 September. The report describes causes, methods, outcomes, validation limits and reproducible commands, including the 351,576 jobs at unlocated code `99999999`.

### Scope and authorization

The user first authorized preparation N01–N09 and subsequently authorized N10 attribute construction. Both are now complete. The earlier construction stop has been superseded; SP model fitting/ranking has since been completed and corrected in v2; see the current-stage note. M5 and U5 remain removed; the active families are M1–M4, M6–M7, B1–B3 and U1–U4.

The analysis unit is the 96 municipal districts, with Brás=`10`, Itaim Bibi=`35` and Grajaú=`30`. The metropolitan building bounding box is only a source extraction extent. Municipal membership is determined geometrically. All geometric processing uses EPSG:31983.

### Frozen preparation execution status

The isolated run is `analysis/processed/SP/sp_prep_2026_09_10_v3/`. **N01–N09 preparation and integrated integrity validation have finished.** All 27 N09 integrity checks pass, including an independent municipal source scan, output hashes, raw-file hashes and preservation of every historical v2 baseline file. Eleven unit tests pass. The runner's `progress.json` is the machine-readable execution record; `N09/readiness.json` records family-specific acceptance. Those frozen v3 results recorded M2/U2 as blocked and M6 incomplete. They are historical: approved M2/M6 overlays and executed U2 experiments now supersede that status as described above.

N06 contains **3,145,436 unique municipal Overture buildings** across all 96 districts and **7,035,747 positive building–parcel overlap candidates**. The independent source scan reproduces the municipal building count. These are source-building records, not a guarantee of complete mapping of physical structures. Brás contains **8,354** prepared buildings. No tax area was transferred to the footprint candidates.

Successful execution is separate from scientific acceptance. N05 has generated an investigation table, not accepted physical junctions. N07 has conserved formal jobs but has not achieved sufficient geographic coverage. Their N10 variants use the explicitly approved M2 proxy and selected U2 area-first policy with source limitations retained.

### What was implemented and why

| Task | Executed work and purpose | Products inside the v3 run |
|---|---|---|
| N01 | Freeze every raw-file hash, configuration and package version; freeze all v2 output hashes; prevent baseline overwrite or reuse of a run ID with changed inputs. Stage checkpoints include code and upstream checkpoint hashes. A runner lock prevents concurrent writes. | `N01/manifest.json`, `progress.json`, stage `checkpoint.json` files |
| N02 | Reuse repaired districts, remove overlaps deterministically, union supplied water and calculate gross/water/land area. This supplies consistent spatial support and future B1/B3 denominators. Preserve internal holes; do not delete parks. | `N02/districts.parquet`, `district_land.parquet`, `district_water.parquet`, `districts.gpkg`, `qa.json` |
| N03 | Resolve cadastral entity keys, retain every unique fiscal account once, map all 38 use labels, retain location exceptions and create one floor-report profile per accepted entity. This prepares cadastral proxies without copying account area to buildings. | `N03/parcel_identity.parquet`, `fiscal_records.parquet`, `parcel_fiscal_profiles.parquet`, `use_mapping.csv`, `competing_keys.parquet`, `location_exceptions.parquet`, `bras_condominium_review.parquet`, coverage tables and QA |
| N04 | Join classvias to source streets using identifiers, address ranges and geometry; add a strict geometry fallback; distinguish measured class, Local imputation and unknowns. Canonicalize exact duplicate geometry while retaining lineage. | `N04/edges.parquet`, `classification_source.parquet`, `edge_lineage.parquet`, `class_candidates.parquet`, `geometry_identity_fallback.parquet`, `coverage.json`, `qa.json` |
| N05 | Enumerate geometric street crossings and incident source edges; flag nearby structures and report snap sensitivity. This creates a finite review queue for physical topology. It does not infer edge levels from a structure line. | `N05/crossing_candidates.parquet`, `crossing_incidence.parquet`, `crossing_edge_pairs.parquet`, `structure_crossing_candidates.parquet`, `collinear_overlap_review.parquet`, `structures.parquet`, `qa.json` |
| N06 | Normalize blocks and select eligible `Quadra` records; read buildings from the existing indexed GeoPackage in bounded batches, assign each whole building once to its largest-intersection district, and preserve every positive parcel-overlap candidate. | `N06/blocks.parquet`, `blocks_qa.json`, `buildings/<district>/buildings_*.parquet`, `parcel_links_*.parquet`, per-district `completed.json`; final `qa.json` covering all 96 districts |
| N07 | Allocate unique census sectors by intersection area, preserving outside residual; normalize CNEFE establishment postal evidence; allocate RAIS only where observed postal geography is unambiguous under the declared rules. | `N07/census_sectors.parquet`, `census_district_allocation.parquet`, `address_reference.parquet`, `establishment_address_evidence.parquet`, `cep_cnefe_candidates.parquet`, `cep_tax_candidates.parquet`, `formal_job_allocation.parquet`, `unresolved_job_ceps.parquet`, `large_employer_cep_review.parquet`, `qa.json` |
| N08 | Validate GTFS keys, times, headways and intervals; derive expected stop service for dated scenarios. This prepares service supply for the later population-access overlay. | `N08/normalized_stop_times.parquet`, `normalized_frequencies.parquet`, `trips.parquet`, `calendar.parquet`, `stops.parquet`, `trip_exclusions.parquet`, `stop_service_events.parquet`, `stop_route_service.parquet`, `service_method.json`, `qa.json` |
| N09 | Validate conservation, identities, hashes, municipal building extraction and family readiness. Pilot maps show input coverage, not model values. | `N09/checks.json`, `readiness.json`, `district_input_coverage.csv/.parquet`, `qa.json`; maps in `review/` |

The source manifest is a local snapshot and environment inventory, not a complete licensing catalogue or dependency lockfile. Source observation periods and licenses still require a complete provenance register. The raw-source review remains at `analysis/outputs/sp_resolution_review_2026_09_10/evidence.json`; it is historical source QA, not a substitute for v3 integration QA.

### Discoveries and accepted methods

#### Districts and water

Ascending district ID owns the 22.067 m² of inter-district overlap. This is a documented deterministic convention, not independent boundary adjudication. Land plus water equals gross district area, and land denominators are positive. Existing internal holes are retained. The supplied water mask is unioned before subtraction to avoid double counting. Pilot maps were inspected for Brás, Itaim Bibi and Grajaú; these establish visible alignment/coverage of the supplied mask, not independent hydrological completeness.

#### Fiscal identity: the important correction

All **39,521 nonzero-condominium parcel geometry rows use lot code `0000`**. SQL (sector–block–lot) therefore conflates different condominiums in the same block. The v3 entity key is sector–block–condominium for those records and SQL for noncondominiums. There are 39,519 condominium entity keys; two have multiple geometries and remain unresolved. After also excluding coincident distinct-SQL review cases, 39,515 condominium geometry candidates are eligible. Noncondominiums have 1,627,782 eligible single-geometry candidates.

This correction raised located constructed-area mass from an intermediate, incorrectly restrictive 61.6% to **97.3032%**. Do not reuse the intermediate figure as the final result. All 3,920,972 unique fiscal accounts and their 597,424,198 m² source area are retained; 3,842,434 accounts and 581,313,100 m² satisfy the declared location/aggregation rule. The remaining 78,538 accounts contain 16,111,098 m². All **630 competing exact/condominium links** remain excluded from accepted aggregation.

B3 sums constructed area once per unique fiscal unit without applying ideal fraction again. This is the user-selected **cadastral constructed-area proxy**. The dictionary does not independently certify common-area proration, and the result must not be labeled surveyed actual floor area. N03 inherits the v2 largest-overlap parcel district assignment; it has not reallocated all 1.7 million source parcel records for N02's 22 m² boundary correction.

B2 accepts a single distinct positive floor report per accepted entity, excluding autonomous garage/storage reports from floor selection. It does not sum apartment floors, weight by account count, assign floors to every building or convert floors to metres. There are 1,548,308 one-report profiles, 89,012 profiles without an eligible positive report and 1,049 conflicting profiles. Use mapping includes residential ancillary garages/storage as residential, office ancillary garages as commerce/services and standalone garages as transport/utilities. All 38 observed strings have explicit mappings. Parcel legal-type interpretation and common-area evidence remain limitations of the declared proxies.

#### Street classes and physical junctions

N04 starts with 219,190 valid source edges. Nine duplicate geometries are excluded through a canonical flag, retaining lineage. Class matching requires normalized CODLOG, compatible parity address ranges (zero/unknown limits are permissive), and at least 80% line coverage by the same class's 2 m buffer. Alternative-class coverage of 20% or more flags conflict. A second pass requires whole-geometry Hausdorff distance at most 1 m and exactly one supported class; this is not an unrestricted nearest-road join.

Final edge counts: **171,232 observed**, including 19,095 strict geometry-fallback matches; **24,194 Local-imputed**; **23,764 unresolved**, including 319 conflicts. Local imputation is restricted to residual nonconflicting R/TV/AL types. It is not observed evidence. District coverage is length-weighted and canonical geometry is clipped to each district. Citywide observed length is 76.1491%, imputed length 10.7018% and unresolved length 13.1491%; no district reaches 95% observed classification. In Brás, 83.61% of length is observed, 4.91% imputed and 11.48% unresolved. Maps show unresolved major-junction/ramp corridors in Itaim Bibi and more extensive imputation in Grajaú. M6 requires sensitivity and residual review before complete comparison.

N05 found **136,005 crossing points**, 107,906 with at least three incident source arms, 1,894 within 5 m of a supplied structure and nine collinear overlaps. **Zero junctions are marked accepted for M2.** Coordinate-bin diagnostics yield 132,928 bins at 0.2 m and 132,669 at 1 m; these are not accepted snapping rules or intersection counts. Structure lines lack reliable edge-level attributes and mostly reference 2004. A bridge approach can be a real same-level junction, so blanket deletion near structures is not a valid primary method. Case-level connectivity and carriageway consolidation remain outstanding.

#### Blocks and municipal buildings

The block layer contains 65,720 source records; one geometry was repaired and none remain invalid. Only 46,801 are typed `Quadra`, and three of those have no positive municipal intersection, leaving **46,798 municipal block candidates** used in completed M3/M4 construction. The other classes (Praca_Canteiro, Borda, CET and Ilha) remain in the normalized source table but are not eligible blocks. Of all classes, 1,669 records are outside/touching-only, mostly Borda. N10 filters both `eligible_type` and non-null district assignment.

Buildings retain complete source polygons and IDs; membership requires positive municipal intersection, with largest district overlap determining whole-entity ownership. Completed B1 intersects and unions footprints across district land; whole-object ownership is not used as an area allocation. Building–parcel relationships remain many-to-many overlap candidates; `accepted_tax_transfer` is false for every row. Source summed footprint areas are QA diagnostics, not B1 union coverage.

Of the 3,145,436 municipal building records, 2,892,365 (91.95%) have at least one positive parcel-overlap candidate. Coverage varies sharply: Brás has 8,314 of 8,354 (99.52%), Itaim Bibi 16,725 of 16,797 (99.57%), and Grajaú 67,719 of 117,265 (57.75%). These are geometry-overlap rates, not accepted tax matches. The variation is evidence that the 97.3% match of IPTU's own constructed-area total **does not establish completeness of cadastral coverage of all buildings**. B2/B3/U1/M7 must retain that limitation and a district sensitivity analysis.

#### Population and employment

The population input has 27,301 unique sectors; three geometries were repaired. Source population is **11,451,999**. Area allocation gives 11,446,054.473 inside districts and 5,944.527 outside residual, exactly conserving the source total within numerical tolerance. Fractional population is an allocation proxy. The vulnerability file was not appended as duplicate population.

RAIS retains all **29,594 CEP rows and 5,387,474 formal job links**. Postal evidence uses 596,960 precise establishment-address records after species/geocoding/ambiguity filtering. It does not weight jobs by residential address frequency. A unique CNEFE district is accepted when fiscal evidence is absent or agrees; ambiguous CNEFE addresses, cross-source conflicts and tax-only candidates are withheld. Observed unique postal placement is a proxy, not an authoritative CEP polygon.

| Job allocation status | CEPs | Job links |
|---|---:|---:|
| Single district, CNEFE and fiscal corroboration | 20,066 | 3,124,339 |
| Single district, CNEFE only | 3,127 | 69,826 |
| Multiple districts | 2,025 | 1,100,410 |
| Fiscal evidence only | 1,933 | 569,787 |
| Unmatched | 2,407 | 507,963 |
| Cross-source conflict | 36 | 15,149 |

Located total is **3,194,165 (59.2887%)**; unresolved total is **2,193,309 (40.7113%)**. This fails the 95% job-mass gate. Jobs were neither replicated across districts nor distributed using unsupported equal weights. The saved CSV may omit null-CEP establishments upstream because the extraction groups CEP in pandas. No billed BigQuery extraction was rerun. Reconcile an upstream aggregate before claiming complete RAIS coverage.

#### Bus service

All **2,272 trip templates** passed implemented validation, with zero excluded trips and zero invalid stop coordinates among 22,261 stops. Validation includes route/service/trip/stop/shape keys, unique IDs/sequences, chronological times, positive headways and nonoverlapping frequency intervals. The 40,402 frequency rows generate expected service rather than treating each template as one departure. Times beyond 24:00 and preceding service days are supported. Missing `exact_times` defaults to zero; interval/headway exposure is therefore expected, potentially fractional service.

Scenarios, in America/Sao_Paulo: Wednesday 2026-09-09 07:00–09:00; Saturday 2026-09-12 and Sunday 2026-09-13 09:00–11:00. The output has 234,225 trip-stop service event rows and 233,460 aggregated route/direction/stop rows across windows. Summed expected stop calls are 887,974.575 weekday, 686,235.100 Saturday and 637,312.040 Sunday. These are calls across stops, **not distinct vehicle departures or passengers**.

`N08/service_method.json` supplements the earlier frozen configuration: future access uses a 400 m binary Euclidean catchment, an 800 m sensitivity and the maximum reachable stop service per route/direction, preventing repeated nearby boarding opportunities from being added together. N10 documents the 250 m grid/sector/district support and area-proportional population weights in the construction report. The frozen N08 stage did not compute an access index; the N10 release now contains it. The feed is bus-only; shapes are not a walking graph. Missing calendar exceptions prevent holiday-specific claims. The 2023–2027 calendar range is not proof of feed observation date.

### Readiness and remaining work

**N10 and the corrected SP model are complete; cross-city harmonization remains next.** The following source/proxy limitations remain relevant to interpreting the released attributes.

| Families | Status / condition for continuation |
|---|---|
| M1, M3, M4 | Constructed and validated; retain source-network universe and whole-block conventions. |
| B1 | Constructed using clipped footprint unions and the land mask; independent imagery/source completeness remains unverified. |
| U3, U4 | Constructed; retain area-allocation, mixed dates and Euclidean bus-access assumptions. All 96 population supports reconcile. |
| M7, B2, B3, U1 | Provisional cadastral proxies. Identity and account conservation are audited, but source/legal scope and shared-area interpretation remain limitations. Publish missing/conflicting coverage and sensitivities. |
| M6 | Constructed under the latest user-approved all-unclassified-as-Local overlay. Preserve the 23.85% imputed length share and observed-only sensitivity. |
| M2 | Constructed as the approved 5 m structure-buffer-excluded planar proxy. Use `selected_m2_proxy` in the new overlay; physical routing connectivity is not certified. |
| U2 | Area-first primary is constructed; address-first and citywide-prior sensitivities are retained. The 508,844 unlocated jobs stay outside primary district totals. High-disagreement CEPs and `99999999` remain refinement targets. |

Completed work and remaining tasks:

1. Completed: all 96 municipal building partitions and N09 acceptance. Preserve the frozen preparation and completed N10 release.
2. Completed: the user-approved M2 5 m exclusion overlay. Its method and source hashes are bound in N10; other distance scenarios are retained as sensitivities.
3. Completed: selected area-first and retained the unlocated bucket; review its sensitivity during modeling. Use `cep_allocation_disagreement.csv` and the unmatched priority table for targeted verification. Keep business-area/address comparisons and citywide-imputed mass separate; do not claim empirical accuracy from conservation alone.
4. Completed by explicit user assumption: assign all unclassified M6 segments Local in the separate overlay. N10 retains observed-only diagnostics and the imputed share.
5. Document cadastral type codes, representative common-area/floor cases, source licenses and observation periods; quantify proxy coverage in each district. Current unit-area arithmetic is accepted only as a declared proxy.
6. Completed: N10 long/wide attributes, dictionary, QA and district GeoPackage. Use the long-form coverage/quality metadata alongside numeric tables; do not interpret provisional source proxies as fully observed truth.
7. Only after feature acceptance, perform N11 transformations, weighting, covariance/PCA checks and Brás similarity comparisons. Chicago harmonization, grids and the separate accessibility study remain later work.

### Reproduction, checkpoints and recovery

Run from the repository root with the existing environment:

```bash
.venv/bin/python analysis/scripts/prepare_sp_v3.py --stages N06
.venv/bin/python analysis/scripts/prepare_sp_v3.py --stages N09
.venv/bin/python -m unittest discover -s analysis/tests -p 'test_sp*.py' -v
MPLCONFIGDIR=/tmp/sp-matplotlib .venv/bin/python analysis/scripts/review_sp_v3.py
```

The complete preparation runner (no `--stages`) was rerun successfully after acceptance: all N02–N09 checkpoints were reused, with no recomputation. Evidence: `logs/sp-v3-resume-check.log`. Each checkpoint hashes outputs and depends on its module, common helpers, frozen source/config fingerprint and relevant upstream stage checkpoints. It refuses changed input/config under the same run ID. No attribute stage exists in this runner. The N03 entity-key rule and `N08/service_method.json` are explicit supplements to the generic parcel/spatial-method placeholders in the frozen config; source/code hashes preserve the executed implementation. Freeze those resolved rules directly into the next run configuration before changing methods. Core modules are in `analysis/scripts/sp_v3/`: `common.py`, `geography.py`, `fiscal.py`, `network.py`, `demography.py`, `transit.py`, `acceptance.py`.

N06 also checkpoints each district under `buildings/<ID>/completed.json`. A district is reusable only when its signature and output hashes match. An interrupted district is regenerated; completed districts need not repeat. **Changing `geography.py` or `common.py` invalidates these district signatures.** Avoid such edits merely to change logging or documentation during a partial run. Keep a single runner active to avoid resource pressure and conflicting progress writes.

The initial 512 MB fiscal join failed due to DuckDB memory allocation. N03 now explicitly uses 768 MB and one thread; other stages use the frozen default 512 MB/two threads. This was a resource correction, not a change to scientific thresholds. The first N09 independent source scan also required an Arrow conversion fix (`to_numpy(zero_copy_only=False)` for binary geometry); the validation was rerun after that compatibility correction, without changing source or N06 outputs. N06 was deliberately interrupted/resumed while correcting the condominium identity rule; its completed geometry checkpoints were reused. Logs record these steps; failures do not imply that earlier successful output is a completed final run.

Four new focused tests pass (11 tests including the seven baseline tests; recorded in `review/unit_tests.log`): extended GTFS times, frequency-window conservation/offsets, district ownership with touching-only exclusion/equal-area tie handling, and refusal to overwrite/escape the baseline directory. N09 passed full-data identity, mass, hash and building completeness checks. Its environment inventory is `N09/environment.json`; pilot inspection findings are `review/inspection.json`. Pilot PNGs were visually inspected; this review is not aerial-imagery validation or physical-junction certification.

### Historical artifacts retained

The existing metropolitan `analysis/data/SP/Edificacoes/sao_paulo_building_morphology.gpkg` contains 7,278,768 source building polygons and remains unchanged. [The building pipeline](#são-paulo-building-morphology-pipeline) describes its extraction and earlier validation; v3 adds a municipal preparation subset in GeoParquet rather than replacing the GeoPackage. The v2 run and its historical reports remain evidence of the earlier methods, not current acceptance of the new inputs. Documentation consolidation history is `analysis/outputs/sp_resolution_review_2026_09_10/documentation_consolidation.json`.

## São Paulo building morphology pipeline

Current technical reference, reviewed 10 September 2026. The completed extraction is unchanged. Current project status is in `SP_DATA_RESOLUTION_HANDOFF.md`; no new cloud extraction was required for v3 integration.

This pipeline extracts Overture building polygons intersecting the bounding box of metropolitan São Paulo. It queries remote GeoParquet on the public Overture S3 bucket through DuckDB, then computes metrics in bounded GeoPandas batches. It does not download fragmented GeoSampa building archives.

### Run

From the repository root, with a Python virtual environment:

```bash
python -m pip install -r analysis/requirements-buildings.txt
python analysis/scripts/prepare_overture_sp.py
python analysis/scripts/extract_sao_paulo_buildings.py --self-test
python analysis/scripts/extract_sao_paulo_buildings.py
```

Network access is needed for official IBGE geography, Overture STAC metadata, signed DuckDB extensions and selected S3 byte ranges. No AWS credentials are required. Preparation pins the release from the catalog into `analysis/cache/overture_sp`; reruns reuse that release and the completed extraction. For a different release or extent, use a fresh cache. Old Overture releases may eventually be unavailable remotely.

The extraction uses a 2 GB DuckDB memory limit, four query threads and 25,000-record GeoPandas batches. `--batch-size` controls the latter. The memory limit applies to DuckDB, not the entire Python process. The script refuses to overwrite an existing final or partial GeoPackage. After an interrupted conversion, move the partial file aside before rerunning; a completed filtered Parquet stage is reusable without another cloud query.

### Selection and geometry

- Release: **2026-08-19.0**, pinned from the official catalog during this run.
- Scope: the 39 municipalities listed by the IBGE metropolitan-region API, ID `04901`.
- IBGE municipal extent in WGS84: approximately `[-47.2084, -24.0643, -45.6948, -23.1834]`.
- Outward-rounded extraction bounding box: **west -47.21, south -24.07, east -45.69, north -23.18**.
- STAC file-extent pruning is followed by Parquet bbox predicate pushdown and exact geometry/box intersection.
- Complete source footprints are retained at the box edge; they are not clipped into partial buildings.
- Source geometry is EPSG:4326. All delivered spatial layers use **SIRGAS 2000 / UTM zone 23S, EPSG:31983**.
- Areas are calculated only after projection. Invalid geometries are repaired where possible and flagged; an unrecoverable polygon fails the run instead of silently losing a building.

The bounding box includes neighboring territory outside the metropolitan municipality union. Use `in_rmsp = 1` to select buildings whose interior representative point falls within that union. This is based on generalized IBGE API cartography, not a cadastral boundary adjudication. The two boundary layers make this distinction inspectable.

### Delivered GeoPackage

`analysis/data/SP/Edificacoes/sao_paulo_building_morphology.gpkg`

| Layer/table | Contents |
|---|---|
| `buildings` | One record per Overture building ID, with full MultiPolygon geometry and morphology attributes |
| `rmsp_boundary` | Union of the 39 metropolitan municipal polygons |
| `extraction_bbox` | Actual extraction box |
| `morphology_metadata` | Nonspatial provenance, definitions, query scope and aggregate quality checks |

Core fields in `buildings`:

| Field | Meaning |
|---|---|
| `building_id` | Overture ID, enforced unique by a database index |
| `footprint_area_m2` | Projected footprint area in square metres |
| `height_m` | Source building height in metres when available; null otherwise |
| `floor_count` | Source number of above-ground floors when available; null otherwise |
| `gross_floor_area_m2` | `footprint_area_m2 * COALESCE(floor_count, 1)` |
| `floors_used_for_gfa` | Floor multiplier actually used in the calculation |
| `floor_count_imputed` | True where the missing floor count was replaced with 1 for GFA only |
| `underground_floor_count` | Separately reported basement-floor count where available |
| `has_parts` | Source flag for associated building parts; parts are not double-counted as additional buildings |
| `is_underground` | Source flag for wholly underground buildings |
| `geometry_repaired` | Whether geometry repair was necessary |
| `in_rmsp` | Representative point lies in the metropolitan municipality union |
| `sources_json` | Source-specific attribution, source record IDs and available provenance |
| `overture_release` | Release identifier |

**GFA is an estimate, not measured actual floor area.** The requested formula assumes every floor occupies the entire footprint. A one-floor fallback does not establish that a building has one floor. Overture defines `num_floors` as above-ground floors, so the calculation does not include basement floor area; basement counts are retained separately. Heights are not inferred from floor counts, and missing floor counts are not inferred from heights. Buildings with varying-height parts may need a later part-level volume model.

Coverage means all matching building records in the selected Overture release. It is not a guarantee that every physical building is mapped, or that source footprints represent cadastral wall outlines rather than imagery-derived roofprints. Missing height/floor coverage must be considered before using B2/B3 for neighborhood similarity.

The completed cloud query selected **7,278,768 records** from **four of 512** Parquet assets. Of these source records, **2,090,405 (28.7192%)** have height and **21,250 (0.2919%)** have above-ground floor counts. Therefore **7,257,518 (99.7081%)** require the requested one-floor GFA fallback. These are bounding-box-wide source coverage rates, not rates for Brás or the metropolitan-only subset.

For the current model, B2 uses a separately validated cadastral floor-count proxy and B3 targets cadastral constructed area. Do not substitute the mostly one-floor Overture GFA scenario for either. The existing file remains useful for footprints and source-height diagnostics. Municipal district analysis requires an actual municipal restriction; metropolitan membership alone is insufficient.

### Validation

The pipeline verifies projected area and null-floor fallback against synthetic 10 m squares, reconciles source and output record counts, validates all output geometries before writing, enforces unique/nonmissing IDs, checks the stored GFA formula over the full table, checks SQLite integrity, verifies CRS and layer counts, and recalculates area from a sample of the exported geometries. A `.partial.gpkg` is renamed to the final filename only after these checks pass.

A JSON metadata sidecar duplicates the embedded metadata for convenient inspection. The filtered WKB Parquet checkpoint, STAC catalog/items, IBGE inputs and executed SQL remain in the cache to support reproduction; they are not substitutes for the delivered GeoPackage.

### Municipal preparation in v3

`analysis/scripts/prepare_sp_v3.py --stages N06` reads the existing indexed GeoPackage in 25,000-record batches. It retains buildings with positive intersection area in the 96-district municipal union, assigns each whole footprint to the district with the largest intersection (ascending ID breaks ties), and saves district GeoParquet partitions with source IDs and parcel-overlap candidate tables. No fiscal area is transferred to footprints. N09 independently rescans the source municipal extent to reconcile the prepared count; current results are in `SP_DATA_RESOLUTION_HANDOFF.md`. The original GeoPackage and its metropolitan scope remain unchanged.

### Sources

- [Overture catalog](https://stac.overturemaps.org/catalog.json)
- [Official DuckDB extraction guidance](https://docs.overturemaps.org/getting-data/duckdb/)
- [Overture building schema](https://docs.overturemaps.org/schema/reference/buildings/building/)
- [Overture attribution guidance](https://docs.overturemaps.org/attribution/)
- [IBGE metropolitan membership](https://servicodados.ibge.gov.br/api/v1/localidades/regioes-metropolitanas/04901)
- [IBGE municipal geography](https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&qualidade=maxima&intrarregiao=municipio)

Source-level attribution is retained in every building's `sources_json`; consult those fields and the release attribution terms when redistributing the resulting data.
