# SP method decisions: M6 classification, U2 allocation and M2 simplification

Updated 11 September 2026 after the user's response to v3 preparation. This document supplements the [current handoff](SP_DATA_RESOLUTION_HANDOFF.md) and [attribute implementation plan](SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md). M6's broader Local rule and M2's **5 m bridge/viaduct/tunnel exclusion** are accepted and applied as separate preparation overlays. **Ten U2 allocation experiments have been executed**; area-first was subsequently selected for the completed N10 construction. No model was fitted.

## Subsequent N10 construction — completed

The user approved starting attribute construction with the recommended area-first U2 policy and an explicit unlocated bucket. N10 now provides all 13 families for 96 districts, including the approved M2/M6 rules. The [construction report](../outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) records the complete methods, pilot values, full-data checks and additional issues caught during implementation. This supersedes the earlier primary-selection/no-attributes status below, which describes the experiment stage.

Newly tested construction issues include clipped versus original street length, mixed-dimensional boundary contacts, tiled footprint unions and U4 population-grid approximation. Both street issues were corrected before release, and source totals reconcile. The U4 125 m pilot refinement differs from the 250 m primary by at most 1.28% for weekday/400 m service across the three pilots. No similarity model has been fitted.

## Issue, cause, action and validation register

| Issue | Why it occurs | What we did | What the result establishes |
|---|---|---|---|
| M6 unclassified roads | Street geometry/identifiers and classification coverage do not match completely; some candidate classes conflict | Applied the user's decision to assign every remaining unclassified edge Local; retained original matches, conflict flags and imputation flags | Complete classification under the assumption, with 23.85% imputed length. One-to-one IDs and observed+imputed coverage were checked; this does not verify actual road hierarchy. |
| M2 ambiguous physical crossings | Planar lines do not encode bridge/tunnel levels; independent structure geometry is offset and can include multiple components | Compared 0/5/10/20 m exclusion scenarios; applied the user's selected 5 m rule to PONTE/VIADUTO/TUNEL | Exactly 1,060 municipal candidates excluded, leaving 106,625. Brás retains 244. This validates implementation of a proxy, not a surveyed connected graph. |
| U2 CEP spanning districts | Postal identifiers do not align with municipal district borders; an exact CEP join cannot uniquely locate all jobs | Constructed CEP-specific support and ran area, address, hybrid, equal-share, residential and mixed-use variants | Every CEP and city total is conserved. The distribution is sensitive: area versus address weighting shifts 275,226.71 job links between districts, and 11 districts differ by more than 10%. |
| U2 asymmetric geographic evidence | Cadastral and address coverage differ; the fiscal data can identify business space on only one side of a CEP | Saved support-asymmetry diagnostics and compared A/B/hybrid allocations | 889 CEPs, containing 495,877 jobs, have positive business area in one district but establishment addresses in multiple districts. Area-only concentration is not automatically ground truth. |
| U2 nongeographic/unmatched codes | Some exported CEP strings lack usable location, especially 99999999; other fiscal supports are mixed-use or have no positive eligible area | Retained explicit UNLOCATED rows in base experiments; separately distributed residual jobs with two municipality-wide priors | Base area/address variants locate 90.5551%; four fully allocated variants conserve 100% by explicit imputation. The experiment does not turn imputed locations into observations. |

## 1. M6: all remaining unclassified streets become Local

The user explicitly authorized treating unclassified roads as Local. The new rule retains every observed match and prior Local imputation, then assigns LOCAL to all 23,764 remaining unclassified records, including records previously quarantined for conflicting classes. Original evidence and conflict flags remain available. There are now 171,232 observed and 47,958 imputed source-edge records; the canonical-edge flag still excludes the nine exact geometry duplicates when measuring length.

This provides 100% classification under the selected assumption. Citywide street length remains 76.1491% observed; 23.8509% is now imputed Local. It does not become 100% observed coverage. No further road-class acquisition is required to construct the chosen primary M6 variant. The observed-only version remains useful as a sensitivity check, not a blocker.

The validated v3 run is unchanged. Apply `analysis/outputs/sp_simplification_review_2026_09_10/m6_classification_overlay.parquet` one-to-one on `edge_id` as implemented in N10 feature construction. Use its `class_model` and `class_imputed`, retaining v3 geometry, `class_observed`, conflicts and `canonical_edge`. `m6_method.json` records the decision; `m6_coverage_overlay.csv` updates preparation coverage. The old v3 readiness JSON remains historical and therefore still describes the earlier incomplete-class rule. The current rule in this document supersedes that M6 limitation.

## 2. U2: allocate jobs using geographic evidence, preserving the CEP total

### Distinguish three problems

1. **A CEP has evidence in multiple districts.** This is an allocation problem: split its job count across the candidate districts using documented weights.
2. **A CEP has only fiscal evidence, or fiscal and address sources disagree.** This is partly a source-validation problem. Such cases can receive provisional weights, but they are not equivalent to corroborated locations.
3. **A CEP has no usable geographic support.** A within-CEP border rule cannot locate it; this requires new geolocation or an explicitly separate municipality-wide imputation model.

The current pipeline retained, rather than discarded, all 5,387,474 exported job links: 3,194,165 located and 2,193,309 unresolved. The newly inspected unmatched queue contains **351,576 jobs under `99999999`**. This string has no location in the current supports; its official coding semantics require upstream verification. It represents **6.5258% of all exported jobs**. Even if every other CEP were geolocated, retaining this code as unlocated caps directly supported geographic coverage at **93.4742%**. Filling it with an assumption must not be described as passing a 95% observed-geolocation gate.

The top ten unmatched codes contain 425,561 of 507,963 unmatched jobs. Targeted upstream/establishment review is therefore more productive than manually reviewing thousands of low-mass CEPs. The priority table is saved with the analysis evidence.

### Common allocation formula

For CEP c with job total J_c, let S_cd be its nonnegative allocation support in district d. Allocate:

`w_cd = S_cd / sum_d(S_cd)`

`allocated_jobs_cd = J_c * w_cd`

Weights must sum to one within every allocated CEP. Fractional allocated jobs are expected; retain floating-point values until presentation. If integer counts are required, use largest-remainder rounding within each CEP to preserve its total. Zero support triggers an explicit fallback; it never produces division by zero or silent zero jobs.

The supplied data contain observed CEP addresses, not authoritative CEP polygons. Build candidate districts from those addresses and accepted cadastral evidence. Do not invent a CEP polygon from a convex hull or spread jobs across a whole district merely because one address occurs there. The support below must be associated with the **same CEP**, not total business/residential area of the entire district. For a parcel crossing a district border, a documented intersection-area split can distribute its support; do not duplicate the unit's entire area on both sides.

### Options to compare

| Option | Support S_cd | Strength | Limitation / role |
|---|---|---|---|
| A. Nonresidential constructed area | Sum positive IPTU constructed area once per accepted fiscal unit for that CEP and district, initially commerce/services, industry/warehouse, institutional and transport/utilities | Uses vertical capacity as well as footprint; available in existing data and directly related to workplace space | Employment per m² varies by activity; tax year differs from RAIS; cadastral coverage varies. Recommended primary proxy to test, not observed establishment employment. |
| B. Establishment-address counts | Number of unique eligible CNEFE establishment addresses for that CEP/district | Simple, less dependent on cadastral floor-area completeness | Assumes equal employment per address; a small shop and large hospital count equally. Recommended first fallback and main alternative. |
| C. Business footprint area | Union of building/parcel footprint area attributable to business use and the CEP, intersected with each district | Purely geometric and understandable | Requires resolving building–parcel–CEP many-to-many links and mixed use; misses vertical differences. Useful sensitivity, with more preparation than A/B. |
| D. Residential area | Residential constructed/parcel area attributable to the CEP in each district | Supplies geographic support where the CEP occurs mainly in housing | Assumes jobs follow residential space and can pull employment away from business concentrations. Consider a low-confidence fallback or sensitivity, not the primary employment model. |
| E. Equal shares / hybrid | Equal shares across supported districts, or a declared mix of normalized A and B weights | Simple benchmark; a hybrid can reduce dominance of one evidence type | Equal shares ignore district-side size; hybrid coefficients are assumptions, not calibrated estimates. Test rather than silently choose coefficients. |

A's initial categories exclude mixed/other and vacant/residential uses. Compare inclusion of mixed-use business support as a sensitivity; do not assign the whole area of an apartment-heavy mixed parcel to employment. Preserve different fiscal units once rather than counting every building–parcel overlap as independent floor area. Do not invent sector-specific jobs-per-m² coefficients without calibration data.

This is an application of ancillary-data redistribution (dasymetric allocation). [EPA's method overview](https://www.epa.gov/enviroatlas/dasymetric-toolbox) explains redistribution using spatial ancillary evidence; it does not validate our employment weights. Employment-to-building disaggregation has been studied explicitly by [Ludick and van Heerden](https://repository.up.ac.za/items/081b2876-15ed-4ea9-a340-d8e01ce00353). The simple A/B rules proposed here are project assumptions to test, not a reproduction or validation of their optimization model.

### What the existing inputs can support

| Current unresolved group | Job mass | Job mass in CEPs with positive nonresidential constructed-area evidence (A) |
|---|---:|---:|
| Multi-district review | 1,100,410 | 1,077,631 |
| Fiscal-only location candidate | 569,787 | 551,983 |
| Cross-source conflict | 15,149 | 15,083 |
| Unmatched | 507,963 | 0 |

For multi-district cases, 1,803 of 2,025 CEPs have positive A support. **Availability is not yet validation:** some of these CEPs have area evidence on only one side, so a weight of 100% on that side may reflect missing cadastre rather than the true job distribution. Use the union of candidate districts and flag disagreement between A and B before choosing the primary allocation.

Residential support does not solve most unmatched job mass: 1,690 unmatched CEPs have residential fiscal evidence but represent only 15,042 jobs; 1,225 have eligible dwelling-address evidence but represent only 10,981 jobs. These sets overlap, so their job totals cannot be added. The remaining mass is concentrated in large codes including `99999999`.

### Experiment protocol and execution boundary

1. Preserve the currently corroborated/unique placements as a baseline, but review generic/large-employer codes and existing source conflicts separately.
2. Create `cep_district_support` with business unit area, establishment addresses, residential support, district provenance, nonzero-support coverage and conflict flags. No district density is needed to compare weights.
3. Calculate A and B allocations for the same multi-district CEPs. Use B when A is absent. Where A is positive on only one of several independently supported sides, compare B and a declared hybrid; do not automatically label the A result high confidence.
4. Give fiscal-only placements a provisional status. Treat cross-source conflicts as weighted scenarios plus priority review, not proof that both sources are correct. Inspect the largest job contributors first.
5. Handle `99999999` and other genuinely unlocated mass separately. Compare a municipality-wide business-area prior against a prior based on the already located job distribution. Both conserve the city total but impute geographic structure. Alternatively retain an explicit unlocated-city bucket in the primary result while publishing the fully allocated scenarios. None of these jobs is discarded.
6. Publish at least A-led and B-led district allocation scenarios, and a separately marked residual-imputation scenario. Record `observed/corroborated_job_mass`, `CEP_weighted_job_mass`, `citywide_imputed_job_mass` and `unlocated_job_mass` separately.
7. Check per-CEP and city mass conservation, unique fiscal units/addresses, support completeness, boundary cases, weights in [0,1], and no multiplication through geometry joins. Compare district allocation differences and the fraction attributable to assumptions, especially Brás and high-employment districts. Later N10/N11 should test similarity stability with and without heavily imputed U2.

Independent establishment-level job counts or verified large-employer addresses would improve validation. Existing unique-district CEPs can test geographic assignment, but they do not validate the internal employment split of a truly multi-district CEP. Sharing IPTU area between U2 weights and B3 also introduces methodological dependence; correlation cannot automatically be interpreted as independent agreement between employment and built form.

### Executed U2 experiments and results

The executable implementation is `analysis/scripts/experiment_sp_allocations.py`. It preserves all 3,194,165 previously located job links at their v3 district assignment. Only previously unresolved CEPs vary. Unique accepted fiscal units contribute constructed area once; CNEFE support comes from the existing deduplicated establishment-address table. No Overture building-to-parcel overlap is multiplied into fiscal area.

Geography remains the v3 whole-parcel, largest-district-overlap assignment for fiscal supports and the v3 point assignment for CNEFE. This experiment **did not redo cadastral parcel/district intersections**. Thus CEP totals are conserved exactly, but fine-scale placement within a border-crossing parcel remains a stated approximation. The support table includes business, residential and mixed area and establishment-address counts, keyed uniquely by CEP/district.

Six base experiments were run:

| Saved scenario | Executed rule | Located jobs | Unlocated jobs |
|---|---|---:|---:|
| `area_first` | Business area; establishment addresses if no business area; residential area if neither workplace support exists | 4,878,630 | 508,844 |
| `address_first` | Establishment addresses; business area if no addresses; residential fallback | 4,878,630 | 508,844 |
| `hybrid` | 50/50 mix of independently normalized area/address weights when both exist; otherwise available support and residential fallback | 4,878,630 | 508,844 |
| `equal_workplace` | Equal weights among districts with positive workplace support; residential fallback where none exists | 4,878,630 | 508,844 |
| `residential_first` | Residential-area weights first, then workplace support if unavailable; stress test rather than preferred workplace model | 4,878,630 | 508,844 |
| `area_mixed` | Include positive mixed/other fiscal area with business area, then address/residential fallbacks | 4,894,553 | 492,921 |

The hybrid's 50/50 coefficient is a declared experimental value, not fitted or independently calibrated. The pure footprint option remains unexecuted because business–footprint–CEP attribution has not been resolved; treating every parcel overlap as accepted would introduce an additional unsupported allocation. It is retained as a later option, not reported as a completed experiment.

Four additional scenarios take `area_first` and `address_first`, then allocate their 508,844 residual jobs across all 96 districts using either (i) the municipality-wide distribution of accepted business constructed area or (ii) the fixed v3 located-job distribution. These are named `*_business_prior` and `*_located_jobs_prior`. Each conserves all 5,387,474 jobs and labels the residual contribution `citywide_imputed_proxy`.

The principal area/address base mass decomposition is: 3,194,165 fixed located-proxy jobs; 1,667,542 workplace-weighted jobs; 16,923 residential-fallback jobs; and 508,844 unlocated jobs. The residual is now 717 originally unmatched CEPs containing 492,921 jobs plus 25 fiscal-only CEPs containing 15,923 jobs. Including mixed area resolves those 25 fiscal-only cases, explaining the gain to 90.8506% geographic allocation. This is a coverage gain under a broader assumption, not evidence that the mixed-use variant is more accurate.

### District sensitivity: what we discovered

The following are **experimental allocated job totals**, not density attributes or observed district employment counts. Values are rounded for readability; files retain fractional precision.

| District | Business area first | Addresses first | 50/50 hybrid | Area/address difference relative to address result |
|---|---:|---:|---:|---:|
| Brás | 45,959.91 | 43,809.35 | 44,884.63 | +4.91% |
| Itaim Bibi | 452,709.40 | 451,802.72 | 452,256.06 | +0.20% |
| Grajaú | 18,283.05 | 20,218.98 | 19,251.01 | −9.57% |
| Santo Amaro | 242,285.24 | 228,085.61 | 235,185.43 | +6.23% |
| Alto de Pinheiros | 23,302.45 | 31,643.25 | 27,472.85 | −26.36% |
| Jardim Ângela | 15,121.05 | 21,246.78 | 18,183.91 | −28.83% |

Across 1,770 CEPs with differing allocations, half the sum of absolute CEP/district differences is **275,226.71 jobs**: the amount redistributed between districts by changing area-first to address-first weights. This is neither job loss nor a measured error. Eleven districts have an absolute change exceeding 10% relative to the address-first result. Detailed per-CEP disagreement and district tables identify the drivers for review.

Residential-first gives Brás 39,569.07 jobs. The area-first result with a business-area citywide residual prior gives Brás **56,654.03**, whereas the located-job prior gives **50,135.43**. Thus residual placement changes Brás more than the base area-versus-address choice. This is a material modeling decision, not an inconsequential final fill operation.

**Recommendation after the experiment:** retain area-first as the leading provisional workplace-capacity candidate and address-first as the mandatory sensitivity comparison; neither is proven more accurate by conservation tests. Keep the citywide residual tier separate and publish its contribution. Do not silently select a fully allocated variant because it reaches 100%. Prioritize the job-heavy disagreement queue and upstream correction of `99999999` before claiming directly observed geographic completeness. A primary U2 scenario remains a methodological choice; the experiments are complete and available for that decision.

### How the experiment was validated

All **45 integration checks passed**: three M2 identity/count checks, four checks for each of ten U2 scenarios, and an input-hash preservation check. Each allocation has unique CEP/district rows, finite weights in [0,1], per-CEP weights summing to one, and the complete original job count conserved per CEP. Fixed v3 located job mass remains unchanged in every scenario. Files used as inputs were hashed before and after processing and are unchanged.

Three synthetic tests also passed: contrasting 70/30 area versus 25/75 address weights (and their 47.5/52.5 hybrid); residential fallback with no invented allocation where all supports are zero; and invariance to area-unit scaling with exact mass conservation. These test arithmetic and fallback behavior. **No establishment-level ground-truth job counts were available**, so they do not establish geographic accuracy. No district densities, model feature matrix or similarity ranking was built.

## 3. M2: quantify the include/exclude simplification

### Comparable geographic scope and units

The source structure table has 4,416 PONTE, 1,129 VIADUTO and 114 TUNEL line records (5,659 combined), plus 821 PASSARELA and 68 CALCADAO records. Restricting to records that intersect the municipal union gives **4,246 PONTE, 927 VIADUTO and 112 TUNEL (5,285 combined)**, plus 789 pedestrian-bridge and 68 pedestrian-mall records. These are line features, not a certified inventory of unique physical bridges/tunnels; original identifiers and components can repeat.

There are **107,685 three-or-more-source-arm intersection candidates inside municipal districts**. The earlier 107,906 figure included 221 outside/unassigned candidates. Do not compare structure records directly to intersection points as though they were the same unit. A structure may have multiple nearby intersections, or none.

The primary review below uses PONTE/VIADUTO/TUNEL. Pedestrian bridges and pedestrian malls are separate sensitivity categories, not assumed road-network grade separation. Each candidate is counted once even if several structure records are nearby. Distances are to the original line geometry, using all source structures as the proximity context, including any just outside the municipal boundary.

| Proximity threshold | Municipal candidates near bridge/viaduct/tunnel | Candidates farther away | Reduction if all nearby candidates are excluded | Brás near / all 256 candidates | Brás reduction |
|---|---:|---:|---:|---:|---:|
| Exact intersection (0 m) | 0 | 107,685 | 0% | 0 | 0% |
| 5 m | 1,060 | 106,625 | 0.984% | 12 | 4.688% |
| 10 m | 2,792 | 104,893 | 2.593% | 28 | 10.938% |
| 20 m | 4,141 | 103,544 | 3.845% | 45 | 17.578% |

At 5 m, adding all structure types increases the municipal exclusion to 1,265 points (1.175%). The zero exact intersections show that an exact point-on-structure test is ineffective on these two geometry representations; it does **not** prove absence of grade separation. The 5 m result is a tolerance-dependent scenario, not a measured error rate.

At 5 m, exclusion changes Brás from **256 to 244**, Itaim Bibi from **1,378 to 1,316 (−4.50%)**, and Grajaú from **3,625 to 3,615 (−0.28%)**. Effects are concentrated: Santa Cecília **330→274 (−16.97%)**, Bela Vista **179→149 (−16.76%)**, Sé **344→304 (−11.63%)**, República **443→395 (−10.84%)**, and Consolação **300→268 (−10.67%)**. A small citywide percentage is therefore insufficient to conclude that district comparisons are unaffected.

### What each simplification means

**Include every planar candidate:** use a clearly named planar-intersection proxy, with at least three source arms and unique municipal assignment. Counting a grade-separated crossing as connected can inflate local intersection density. It can create false connections if reused as a routing graph. For a fixed district area, the percentage change in the count equals the percentage change in the corresponding density; no density or ranking was constructed in this review.

**Exclude every nearby candidate:** use a clearly named structure-buffer-excluded proxy. This can remove real approach/interchange junctions and other same-level crossings near the structure. It still leaves undetected grade-separated crossings farther from the supplied geometry. It is not automatically the physical truth.

The two counts are sensitivity scenarios, not statistical confidence bounds on the actual number of physical junctions. Missing crossings, positional differences, divided carriageways and duplicated nodes can affect both. The original coordinates have not been snapped/consolidated into a certified graph. All frozen v3 `accepted_m2_junction` flags remain false.

**User-selected decision, now implemented:** use the **5 m structure-buffer-excluded planar proxy** as the primary M2 definition. Retain source candidates with at least three source arms, a municipal district assignment, and no PONTE/VIADUTO/TUNEL geometry within distance ≤5 m. Exclude PASSARELA/CALCADAO from the primary structure test. This selects 106,625 candidates and excludes 1,060, a 0.98435% citywide reduction. Brás selects 244 and excludes 12. The 0/10/20 m variants remain recorded sensitivity evidence.

The new `m2_selection_overlay.parquet` preserves all original nodes and geometry, with `near_bridge_tunnel_5m`, `selected_m2_proxy` and `m2_method`. N10 uses `selected_m2_proxy`; the frozen v3 `accepted_m2_junction` field remains false because it means certified physical connectivity. Do not use the selected proxy as a validated routing graph. Implementation matches the requested threshold exactly; it does not resolve missing grade information or positional uncertainty. Final similarity effects remain N11 work.

## 4. Executed work and reproduction

Executed in this review: municipality-scoped M2 counts and 0/5/10/20 m proximity scenarios; district and pilot effects; M6's authorized classification overlay and coverage reconciliation; U2 business/residential evidence-availability checks; unmatched-job prioritization and inspection of `99999999`. The initial review did not reassign jobs. The subsequent authorized experiment now supplies ten U2 allocations and the accepted M2 5 m selection, as described above; no candidate is certified as a physical intersection.

Reproduce from the repository root:

```bash
.venv/bin/python analysis/scripts/review_sp_simplifications.py
```

Outputs are in `analysis/outputs/sp_simplification_review_2026_09_10/`: `evidence.json`, `m2_district_scenarios.csv`, `m6_classification_overlay.parquet`, `m6_coverage_overlay.csv`, `m6_method.json`, `u2_weight_evidence_availability.csv`, `u2_residential_evidence_availability.csv`, `u2_unmatched_priority.csv`, `u2_residual_summary.json`, and `reproduction.json`. The last file fingerprints this script and the frozen source checkpoints. Future construction must bind both v3 and the accepted M6 overlay in its manifest.

### Current execution artifacts and continuation

The current experiment directory is `analysis/outputs/sp_allocation_experiments_2026_09_10/`. Key products are `m2_selection_overlay.parquet`, `m2_method.json`, `m2_district_selection.csv`, `cep_district_support.parquet`, `support_asymmetry.parquet`, ten `*_allocations.parquet` and `*_district_totals.csv` pairs, `scenario_mass_summary.csv`, `district_scenario_comparison.csv`, `district_sensitivity.csv`, `cep_allocation_disagreement.csv`, `unlocated_by_original_status.csv`, `experiment_findings.json`, `checks.json` and `manifest.json`.

```bash
.venv/bin/python analysis/scripts/experiment_sp_allocations.py
.venv/bin/python analysis/scripts/summarize_sp_experiments.py
.venv/bin/python -m unittest discover -s analysis/tests -p 'test_sp_allocations.py' -v
```

The experiment runner writes only its dedicated output directory and may deterministically regenerate those experiment files; it does not modify frozen v3. Its manifest records input hashes and the executed code hash. `analysis/config/sp_current_methods.json` binds the current base run, approved M6/M2 overlays and U2 experiment directory; U2 primary selection is now `area_first`. The N10 run manifest freezes those bindings and its selected scenario.

## 5. Other preparation issues retained in the project record

These earlier issues were addressed during v3 and remain relevant to interpretation. Their detailed source evidence and validation are in `SP_DATA_RESOLUTION_HANDOFF.md`; they were not independently rerun as part of the U2 experiment.

| Issue and cause | Action and validation | Remaining interpretation |
|---|---|---|
| Condominium parcel identity: lot 0000 is shared across separate condominiums within a block, making SQL alone ambiguous | Used sector–block–condominium keys for condominium entities; retained SQL for noncondominiums; quarantined competing/multiple-geometry links. Unique fiscal-unit count and source area were conserved. | 97.3% of source fiscal area is located, but that does not establish cadastral coverage of all physical buildings. |
| Building height/floors: Overture floor observations are extremely sparse and the one-floor GFA fallback is not measured built area | B2 uses a declared cadastral floor-count proxy; repeated reports collapse by entity, conflicts/ancillary reports are excluded. B3 uses unique fiscal-unit area without fraction reapplication. | Common-area semantics and cadastral coverage remain proxy limitations; floors are not metres. |
| District/water denominators: district overlaps and overlapping water masks can double-count area | Applied deterministic district overlap ownership; unioned water before subtraction; checked positive land and land+water=gross. | Boundary convention and supplied water coverage are documented, not independently adjudicated physical truth. |
| Building/parcel cardinality: many footprints intersect several parcels, and parcel coverage differs by district | Retained positive overlap candidates without copying tax area to each footprint; checked 3,145,436 unique municipal building IDs against an independent source scan. | Brás has 99.52% parcel-overlap candidates versus 57.75% in Grajaú; overlap is not an accepted tax match. |
| Population boundary crossings and duplicated thematic layers | Allocated unique census sectors by area, retained explicit outside residual, and did not append the duplicate vulnerability population. | Allocations are fractional proxies; allocated plus residual population conserves 11,451,999. |
| GTFS frequency templates, after-midnight times and missing exceptions | Validated keys, time ordering and headways; calculated expected stop service for fixed scenarios rather than counting templates as operated departures. | Bus-only expected service, mixed dates, Euclidean access and absent holiday exceptions remain explicit assumptions. |

The resolution standard throughout is to distinguish implemented arithmetic, user-selected assumptions and independently established facts. Passing integrity checks establishes reproducibility and conservation, not external accuracy of every proxy.
