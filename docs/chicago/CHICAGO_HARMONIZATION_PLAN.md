# São Paulo–Chicago attribute harmonization plan

**Current scope review — 25 September 2026:** the user reopened the earlier [six-family proposal](SIX_FAMILY_PLAN_REASSESSMENT.md) and has now **deferred M2 from both the Chicago and future cross-city models**. The [B1/BV decision](B1_BV_HARMONIZATION_DECISION.md) confirms feasible paired methods and retains both families in the planned model scope, subject to independent source-accuracy checks. The [model status](../MODEL_STATUS.md) tracks the remaining scope; the [original ledger](CHICAGO_13_FAMILY_COMPLETION_LEDGER.md) and [v2 contract](../../analysis/config/sp_chicago_harmonization_v2_full_scope.json) preserve the historical 13-family proposal. The next contract must omit M2; the existing one remains fit-blocked. Six supplied Microsoft tiles were organized and tested in [paired B1 pilots](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md); Overture remains the primary B1 source. The six-family matrix is technically ready but not scientifically accepted, and no model has been fitted. Earlier M2 inclusion statements below are historical.


**Approved for execution — 22 September 2026.** The user authorized proceeding and requested documentation for every step. See the [cumulative execution document](SP_CHICAGO_HARMONIZATION_EXECUTION.md) for current status, decisions, evidence and outputs. Approval permits construction and targeted checks; feature acceptance still precedes model fitting.

## 1. Proposed outcome and current evidence

Build a Chicago model and a separately versioned **updated SP harmonized model** using the same accepted definitions and fitted reference state. Preserve the original 96-district SP attributes and `sp_urban_model_v2`, and the existing Chicago local/functional releases. The new SP model is a companion release, not an overwrite or a continuation of the old 13-family calibration.

Deliver district profiles for 96 SP districts and 77 Chicago Community Areas, an updated SP-to-Brás ranking, and Chicago-to-Brás comparisons with family contributions and uncertainty. A single common measurement space supports these outputs; do not fit a separate Chicago normalization for the main comparison.

### What is already available

| Inputs | Current evidence / remaining work |
|---|---|
| Reporting boundaries, hydrography, local roads, footprints and observed use | Available; common denominator, topology and use definitions still need acceptance |
| Overture buildings and road segments/connectors for both cities | Matched `2026-08-19.0` acquisition complete; paired road and footprint candidates audited September 17; shared-source completeness and measurement equivalence remain open |
| Chicago Census 2020 blocks/counts, LODES WAC 2022 and CTA GTFS | Processed in `chi_functional_2026_09_16_v2`; 163 historical checks passed. Reuse artifacts, then construct matched SP companions and review temporal/coverage differences |
| Cook/DuPage parcels and Cook assessor tables, benchmarking | Nine Chicago-scoped acquisitions complete; restricted supplemental records are no longer a prerequisite |
| Commercial workbook evidence | Eight text extracts and seven user-supplied original XLSX files. T76 original is optional. These do not establish complete stories/GFA |
| GHSL ANBH/AGBH height (2018) and total built volume (2020) | Nine source ZIPs and six city extracts acquired; R2023A/V1-0, native 100 m ESRI:54009. Acquisition receipts exist; scientific interpretation/aggregation remains to be checked after approval |
| Original SP model v2 | Corrected and previously validated reference implementation; retain its data, state and outputs unchanged |

Evidence: [harmonization audit](../../analysis/results/Chicago/harmonization_checkpoint_2026_09_17/README.md), [functional extension](CHICAGO_FUNCTIONAL_EXTENSION.md), [cadastral acquisition](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md), [public-data proposal](../../analysis/results/Chicago/public_data_alternative_2026_09_21/README.md), [GHSL acquisition](../../analysis/results/SP_CHI/ghsl_public_2026_09_21/README.md), [SP corrections](../sp/SP_MODEL_FIXES.md). Historical check counts are evidence of completed work, not acceptance of the new model.

### Decisions proposed for approval

- Exclude **M7 physical cadastral entity density, B2 reported floors and B3 fiscal constructed area** from both cities' common model. Keep them only as existing city-specific diagnostics; do not pursue restricted records to unblock the build.
- Construct a core from accepted common morphology, footprint coverage and resident density; add bus supply only after its paired support/calendar gate passes. No family is accepted merely because its source exists.
- Evaluate GHSL under a new **BV — vertical form** family, with separate height and volume variants. Never relabel these as B2/B3. Keep a core-only comparison so the older estimated products' influence is visible.
- Treat U1 land use and U2 employment as gated functional extensions. Their current city-specific definitions do not yet justify entry into the primary core.
- Fit new transformations, scales and family calibration on harmonized SP, then apply that saved state to Chicago. Publish new SP results alongside the unchanged v2 reference.

No additional bulk dataset is currently a known prerequisite for this route. If source review reveals a specific indispensable gap, document the affected attribute and a bounded acquisition or symmetric omission; do not restart broad data hunting.

## 2. Geographic and temporal contract

### Reporting units and projections

- Use 96 SP districts and 77 Chicago Community Areas. Keys must be globally unique, e.g. `SP:10` and `CHI:10`, alongside city, local ID and name. Never join cities by a bare two-digit ID or name alone.
- Retain SP EPSG:31983. Use **NAD83 / UTM zone 16N, EPSG:26916**, in metres for Chicago calculations. Validate source CRSs rather than assuming a shapefile is WGS84; never calculate areas in longitude/latitude or Web Mercator. Store coordinate operations and units.
- Recompute geometry-based area. Do not assume `shape_area` or assessor area fields are m². For attribute fields explicitly documented as square feet, use `m² = ft² × 0.09290304`; geometric area comes from metric projected geometry.
- Use municipal support for reporting and a buffered extraction area for boundary-crossing features. At least 800 m beyond the city is required for the largest bus catchment; use a larger recorded geometry margin when constructing whole blocks or road topology.
- Union the water mask, clip it to each unit, and save gross, water and land area. Check Lake Michigan, river corridors, airport boundaries and islands explicitly. Parks remain land. Use the **same denominator convention in both cities**: preserve gross-area density formulas and land-area B1 and the separately defined GHSL volume intensity in the first compatibility comparison; publish land-denominator density sensitivities for both cities if water fractions materially affect ranks.
- Community Areas and SP districts differ in size and history. District-level rankings are the first descriptive support, not proof that scales are equivalent. Later 250/500 m matched grids must be constructed from source objects in both cities; the U4 population grid is not a morphology grid.

### Time contract

GHSL height is 2018 and volume is 2020; Overture is a 2026 release. Use the same edition of each product in both cities, but do not describe the combined model as a single-year city snapshot. Record source-age limitations and compare core-only, height and volume variants.

Maintain a source register with observation period, release date, extraction date, geography vintage, units, license/attribution, original URL and hash. Do not use a downloaded filename as the measurement year.

Prefer the same Overture snapshot for shared physical geometry. Freeze RAIS/LODES employment at 2022 where both definitions and availability are verified. For Chicago population, use 2020 Census blocks as the initial fine-scale count/support and disclose the gap from SP's 2022 census. Test a documented ACS-based update separately; an ACS period estimate is not a point-in-time 2023 census. Census guidance distinguishes the periods covered by [one- and five-year ACS estimates](https://www.census.gov/programs-surveys/acs/guidance/estimates.html).

For transit, select valid nonholiday local weekday/weekend scenarios in both feeds. If the matching September 2026 feeds are not archived/available, choose documented comparable local windows and mark the temporal mismatch. Do not invent historical service from a current feed. Keep 07:00–09:00 weekday and 09:00–11:00 weekend windows initially, using each city's local service calendar and timezone.

## 3. Source reuse and evidence closure

Start from the acquired manifests and frozen releases in section 1. Do not repeat completed downloads or unchanged historical validation suites. Target checks at changed definitions, new paired calculations and unresolved source semantics.

Use existing municipal and assessor inputs as diagnostics for common Overture geometry. Use CMAP observed use and SP observed-use inputs only under an explicit shared ontology and weighting. Census blocks support population/jobs allocation, not physical street blocks. CTA versus SP bus-only supply is the initial operator scope; rail/Pace expansion is deferred.

Review the locally saved GHSL Data Package 2023 PDF, source copyright files and per-raster metadata before selecting a height denominator or interpreting zeros. Retain exact URLs, source years, resolution, units, hashes and transformations. Source ZIPs contain surrounding regions; city extracts retain intersecting cells, not fractionally allocated city totals.

Any necessary incremental acquisition must be geographically scoped, resumable and documented. Agency contact, subscriptions, restricted supplemental records and the optional T76 binary are outside this build's prerequisites.

## 4. Family-by-family harmonization decisions

### M1 — Street density

**Keep:** clipped geometric line length / gross reporting area, single ownership of boundary-coincident length.

**Change for the harmonized release:** choose one common road universe and representation, then recompute both cities. Proposed pilot contract: retain major through local street classes and designated pedestrian streets, preserve explicitly represented carriageways, exclude parking aisles, driveways, sidewalks, steps and nonstreet paths. Evaluate alleys/service streets separately because Chicago's alley network could dominate a mismatch in mapping conventions. Explicitly resolve unknown classes and private access; never assume missing access means public.

Use the same duplicate/self-retrace handling, line clipping, boundary ownership and inclusion rules. Compare the new SP M1 with the municipal-line baseline before accepting the shared source. Street names and identical API column names are insufficient evidence of equivalence.

### M2 — Intersection density

**Current decision:** exclude M2 from new Chicago and SP–Chicago scores. The method and gate below are retained as historical design notes for an explicitly approved future reopening; no M2 construction or acceptance task is scheduled.

**Keep:** at least three incident eligible road arms per accepted counting point / gross area.

**Gate:** the current SP planar-plus-5 m exclusion proxy is not the same measurement as a Chicago routable intersection count. Preferred common-source pilot: derive the same connector/segment topology rule for both cities, count undirected physical arms once, exclude simple segmentation points, and inspect bridges, tunnels, divided roads, slip lanes and closely spaced junctions. Freeze any consolidation distance after reviewing the same fixture types in both cities.

Keep the original SP 5 m proxy as a legacy sensitivity. If topology cannot be validated comparably, either use a fully documented common planar/structure proxy in both cities or exclude M2 from the strict common model. Do not “improve” only Chicago and compare it to the old SP count.

### M3 and M4 — Physical block size and shape

**Keep:** whole-object area/log-area statistics, compactness `4πA/P²`, rectangle elongation, unweighted median/IQR.

**Gate:** Chicago census blocks, zoning polygons and SP cadastral `Quadra` are not equivalent block definitions. Preferred shared version: polygonize a common, planarized block-boundary network using identical road/ramp/alley rules, suppress duplicate carriageway artifacts and apply the same treatment of rail/water barriers. Derive physical blocks in **both** cities. The block-enclosure network is a 2D morphological construct; do not silently reuse it as a routable graph.

Audit boundary-truncated blocks, very large peripheral polygons, traffic islands, parks and industrial campuses. Keep complete objects with positive municipal intersection and deterministic largest-overlap ownership; identify extraction-edge truncation. Test the shared definition against SP Quadra and Chicago sample maps. If comparable blocks cannot be established, withhold M3/M4 from the strict model rather than using Census blocks as a convenient substitute.

### M6 — Road hierarchy composition

**Keep:** length-weighted composition and Hellinger distance, with missing/imputed mass separate.

**Change:** GeoSampa's six labels, including VTR, have no automatically proven Chicago equivalents. Propose common-source categories from the chosen transportation taxonomy, with an explicit mapping table reviewed in both cities. A candidate grouping is limited-access, major arterial, intermediate/collector, local/living street, pedestrian street, and unresolved; finalize it only after auditing source meanings. Treatment of included service roads must match M1.

Do not copy SP's “all unknown Local” assumption to Chicago without a new declared decision. A shared version can retain unknown as an explicit category and test complete-case or imputation alternatives in both cities. Unknown mass may encode mapping coverage rather than physical hierarchy: review asymmetric coverage and exclude M6 from the strict set if it dominates the comparison. This changes the SP representation and requires a new fit/calibration; do not mix new Chicago classes with the old six-vector.

### M7 — Physical cadastral parcel density (excluded from proposed common model)

**Current decision:** no acquisition or reconstruction is scheduled for this family. The criteria below explain its exclusion and apply only if a future separately approved extension revisits it.

**Keep:** one accepted physical entity per location, whole-object assignment, count / gross area.

**Need:** Cook parcel polygons and a defensible parcel/condominium parent crosswalk. PINs can represent legal/tax units rather than the physical entities used by SP's corrected SQL/condominium keys. Counting every apartment PIN as a parcel would inflate density.

Build `physical_entity_id`, unit links, geometry lineage and ambiguity exclusions. Test condominium buildings, parcels with multiple structures, multi-PIN properties and public/transport parcels. Accept M7 only if both cities' entity universes are sufficiently aligned and coverage is reported. Otherwise retain it in city-specific analyses, not the strict cross-city model.

### B1 — Footprint coverage

**Keep:** exact union of clipped footprint polygons on land / land area; gross-area and overlap-excess diagnostics.

**Available:** matched Chicago/SP Overture polygons. **Remaining gate:** a reviewed common land-mask method and source-completeness comparison. Use the same metric tiled-union algorithm and positive-area intersection rule. Compare both sources on dense high-rise, industrial, residential and peripheral samples. Avoid adding building parts and parent footprints twice. This is a strong candidate for the strict common model once mapped coverage and water handling pass; source uniformity alone is not proof of equal completeness.

### B2 — Reported floors (excluded from proposed common model)

**Current decision:** no acquisition or reconstruction is scheduled for this family. The criteria below explain its exclusion and apply only if a future separately approved extension revisits it.

**Keep only if matched:** unweighted median/P90 of one eligible positive floor report per accepted comparable entity.

**Need:** actual stories/floor-count semantics across Cook residential, condominium and commercial records, including how basements, half-stories, split levels and ancillary units are encoded. A single-family subset cannot stand in for Chicago's whole built stock. Do not compare Chicago measured height with SP cadastral floors, convert height using an arbitrary metres-per-floor factor, or default missing floors to one.

If coverage/units cannot be aligned, exclude B2 from the strict common model. A shared building-level height/floors alternative requires new attributes in **both** cities and must not be labeled equivalent to the existing cadastral B2.

### B3 — Constructed floor-area intensity (excluded from proposed common model)

**Current decision:** no acquisition or reconstruction is scheduled for this family. The criteria below explain its exclusion and apply only if a future separately approved extension revisits it.

**Keep only if matched:** accepted unique constructed-area mass / land area.

**Need:** determine whether Cook fields represent building gross area, living area, rentable area, unit area or repeated parent area. Resolve physical-building/parcel/unit joins and common-area handling before summing. Convert documented square feet to m² once. Do not sum residential living area and commercial rentable area as though both were gross floor area, nor multiply repeated condo building area by unit count.

The SP measure is a declared tax proxy, not certified surveyed GFA. A Chicago footprint-times-estimated-floors proxy is a different method; it must be separately constructed for both cities or omitted. Report coverage and unresolved mass rather than forcing B3 into the model.

### U1 — Land-use diversity

**Keep:** fixed-ontology normalized entropy, with classified mass and unknown coverage explicit.

**Preferred semantic match:** comparable observed cadastral use per physical entity and the same weighting/ontology in both cities. Construct and review a source-code crosswalk into the common categories; inspect vacant, mixed-use, parking, institutional and public land separately. Do not equate zoning permission with actual use.

CMAP area-based observed use can support an alternative only if SP gets a comparable observed-area representation. Do not compare CMAP land-area entropy to SP parcel-count entropy. If a valid shared weighting/domain cannot be built, omit U1 from the strict common model and use its profiles descriptively. This gate matters: the SP U1 area sensitivity retained only eight primary top-10 members.

### U2 — Workplace jobs

**Keep:** allocated workplace job links / gross area, with unresolved mass and uncertainty tiers.

**Available:** Chicago LODES WAC 2022 and matching block support. **Remaining gate:** verify the paired employment definition and allocation sensitivity using these existing artifacts. Deduplicate by geography/job-type/segment and use the published total field once. Include workplace blocks intersecting the city; preserve outside mass. For border blocks, choose a documented positive-area/ancillary workplace allocation and test it—do not apply population residential weights automatically to employment.

Compare coverage/reference definitions with RAIS active links, including public/federal work, multiple jobs, disclosure treatments and noncovered employment. LODES is not a direct individual-employer census with exact within-block locations. SP CEP weights and Chicago block allocation have different uncertainty structures; report those differences. Do not apply a CEP rule to Chicago block data merely to make algorithms look alike.

U2 should start in the extended functional comparison. The SP U2 variants kept the same top ten, but that does not prove RAIS–LODES measurement equivalence or eliminate the 508,844 unlocated SP jobs.

### U3 — Resident density

**Keep:** unique population mass allocated to reporting units / gross area, with outside residual preserved.

**Available:** Chicago Census 2020 block geometries and counts; compare their Community Area totals with the provided aggregate ACS data as a vintage-aware diagnostic. Area-intersection allocation must conserve source counts; do not join on imperfect Community Area names without an ID crosswalk.

A separate ACS update can use documented estimates and uncertainties, but the 2023 label must first be traced to its one-/five-year period and source. Do not discard margins of error or fabricate exact block-level current populations from Community Area totals. Record the 2020-versus-2022 census gap and test the effect of the chosen population support on U4.

### U4 — Population-weighted bus supply

**Keep:** sector/block ∩ district ∩ origin-zero 250 m grid support; proportional population; within-piece representative points; 400 m weekday primary and 800 m/weekend sensitivities; maximum reachable stop supply per route/direction followed by sum, then population-weighted mean.

**Available:** CTA static GTFS and fine-scale population. **Remaining gate:** matched SP support, service scenarios and operator scope. Filter bus service explicitly; validate service calendar/exceptions, after-midnight times, routes/directions, stop identities, scheduled departures and any frequency templates. Include stops outside Community Areas and city borders within the catchment. Preserve agency in keys when testing multiple feeds.

Compare city-operated bus scopes first (CTA versus the supplied SP bus operator scope), then label broader metropolitan bus/rail coverage as a separate two-city alternative. Frequency coverage, Euclidean barriers and timing differences remain limitations. Never add rail only in Chicago or interpret supply as observed ridership/access to jobs.

### BV — Public vertical form (new GHSL family)

This is a new grid-based measure for both cities, not a building-level floor distribution or legal GFA. Use the acquired ANBH/AGBH 2018 and total volume 2020 products. Do not convert metres to stories or volume to constructed floor area. Detailed product interpretation is a first implementation checkpoint, not a claim already validated in this plan.

**Proposed candidates:**

| Candidate | Definition to implement after source-definition review | Role |
|---|---|---|
| `BV_height_net_mean_m` | ANBH mean weighted by valid cell–district land intersection area, on the explicitly documented height-support domain | Preferred height candidate; a spatial grid summary, not building-weighted mean height |
| `BV_height_gross_mean_m` | AGBH mean under its documented denominator and corresponding area weights | Alternative diagnostic; not an additional full-weight coordinate beside ANBH |
| `BV_volume_density_m3_m2` | Sum of cell volume multiplied by its district-land intersection fraction of full source-cell area, divided by district land area | Volume alternative; assumes uniform within-cell volume allocation |

For height, freeze valid-support and zero handling from product documentation before calculation. Preserve genuine zero; exclude source NoData and report its area separately. If the proposed area-weighted ANBH statistic is not supported by the documented product semantics, revise its definition before freezing the contract. Do not invent built-area weights from contemporary Overture footprints or infer them by combining 2018 height with 2020 volume. Any genuinely necessary companion raster requires an explicit, targeted acquisition decision.

Intersect reporting units and the reviewed land mask with the **native Mollweide source cells**; compute overlap fractions in that source equal-area CRS. Keep input rasters unchanged, with no bilinear interpolation. Check that allocated volume plus outside/water residuals reconciles to source mass within a declared numerical tolerance. A cell touching multiple districts must not contribute its full volume to each. Record that area fractions are an allocation assumption, not observed subcell building locations. Report gross-area allocation/denominator as a sensitivity.

Publish per-unit valid coverage, NoData area, boundary-cell share and denominators. Insufficient support produces a documented missing result, not an imputed zero. Acceptance requires a common support policy and finite valid inputs for the declared comparison cohort. If a family cannot support the complete 96/77 cohort without unjustified imputation, withhold it from the primary model in both cities.

**Weight policy:** primary extension candidate is one height coordinate in one BV family. Run volume-only as an alternative; a combined height/volume sensitivity may split the single BV budget equally after coordinate scaling. ANBH, AGBH and volume must not become three independent full-weight families. Compare omission of BV and B1 to disclose overlapping built-form information. Freeze the primary choice before looking at cross-city rankings.

## 5. Comparison sets and modeling policy

Freeze the following comparison sets before inspecting neighbor rankings:

| Set | Candidate families | Acceptance and purpose |
|---|---|---|
| Common core | M1/M3/M4/M6, B1, U3; U4 if its gate passes | M2 is excluded by decision; each retained family must pass its paired definition/coverage gate |
| Core + vertical form | Accepted core + BV | Proposed main public-data extension; report core-only and height/volume variants alongside it |
| Functional sensitivity | Accepted core, optionally BV, plus U1 and/or U2 | Add only after observed-use weighting and RAIS/LODES coverage/allocation gates pass; otherwise retain descriptive profiles |
| Legacy city diagnostics | M7/B2/B3 and existing local alternatives | Outside common distances; original SP v2 remains available separately |

Use equal weights across accepted families as the proposed default, with one budget for BV. Recompute normalization after a family exclusion. Also evaluate equal-domain weighting and bounded family-weight perturbations with fixed seeds and documented ranges. Final family acceptance and any changed primary definition must be recorded before rankings, with unresolved material changes brought back for review.

Every excluded family is excluded in both cities and its weight is redistributed explicitly. Never zero-fill an unavailable Chicago attribute or silently use pair-specific available features. Publish the shared family list and reason for every exclusion. A reduced set is a new model, not a result from the original 13-family SP metric.

### Proposed primary fit: SP-anchored harmonized measurements

Recompute harmonized measurements for all 96 SP districts first. Fit transforms, scalar scales and positive-pair family calibrations to those SP harmonized values, then apply the **same saved state** to 77 Chicago rows. This asks which Chicago places resemble Brás in a common physical measurement space while retaining an interpretable SP reference. Do not refit scales for Chicago or z-score each city separately; that would change the question to within-city relative position.

Flag Chicago values outside the SP fitting range/quantiles; do not clip them to manufacture similarity. If the shared feature set changes, refit the harmonized SP reference rather than reuse the old 23-coordinate calibration unchanged.

As a sensitivity, compare a jointly fitted 173-unit model with an explicit city-balanced weighting scheme for scalar quantiles and family calibration. Save how row and pair weights are defined; do not claim equal city influence from pooling unequal sample sizes. Keep SP-anchored and pooled distances/ranks separate. PCA should be fitted on the declared reference universe; no city-specific rotations in a shared distance comparison.

Evaluate source variants, family omissions, weighting perturbations, water denominators, population vintage and district/grid support. Inspect domain shift and city separation, not just nearest-neighbor rank. No supervised accuracy or causal interpretation is available without independent labels/outcomes.

## 6. Approval gate, checkpoints and deliverables

**Approval received.** Proceed through the bounded checkpoints below and record each in the cumulative execution document.

After approval, work in bounded checkpoints and update the handoff at each stop. Reuse completed acquisitions and historical checks. Run new checks only where the new work requires them.

| Checkpoint | Work after approval | Concrete deliverable / exit gate |
|---|---|---|
| H0 — Freeze measurement decisions | Read GHSL technical definitions; fix road/access/topology rules, land support, height support, family tiers, dates and weights; inventory existing artifacts without reacquisition | Versioned machine-readable contract and acceptance ledger. No ranking; resolve or explicitly defer every primary-definition ambiguity |
| H1 — Paired physical pilots | Same road topology, block construction, hierarchy and footprint methods in both cities; pilot GHSL partial-cell allocation and height support | Paired fixture maps/tables, coverage and conservation evidence. Symmetric exclusions for failed families; no city-specific shortcut |
| H2 — Paired physical attributes | Compute accepted morphology/B1/BV for all 96 SP districts and 77 Chicago Community Areas | City-qualified long/wide tables with numerators, denominators, coverage, source years and source hashes |
| H3 — Paired functional attributes | Reuse population/GTFS results; build SP companions; finish the paused employment sensitivity only if U2 is retained; attempt U1 only with a common observed-area/entity definition | Population and jobs residual accounting, matched bus scenarios, U1/U2 acceptance or explicit exclusion. No claim that all functional families pass |
| H4 — Freeze common matrix | Review full paired outputs and acceptance ledger; lock included features, family budgets and source qualifications | Complete finite 96/77 matrices for included families, frozen dictionary/config and independent checks of changed computations, before fitting/ranking |
| H5 — Fit new SP reference and apply to Chicago | New SP-anchored transforms/calibration; save/apply identical state; derive SP and Chicago distances to Brás | Updated SP harmonized model, Chicago profiles/ranks, family contributions, domain-shift flags and reproducible saved state |
| H6 — Robustness and release | Core vs BV, height vs volume, functional exclusions, water/partial-cell assumptions, source uncertainty and weights; city-balanced pooled fit as sensitivity | Model report, rank stability, source/feature manifest, limitations and updated handoff; original models intact |

A failed gate triggers correction or explicit symmetric omission before downstream fitting. Do not compensate with pairwise available-feature distances or zero-filled inputs. If failure materially changes the proposed main model, stop at the checkpoint and present the revised contract for review.

Matched 250/500 m morphology grids and pedestrian outcomes are deferred follow-up work. District-level release does not require those acquisitions or computations, but cannot claim spatial-scale invariance or predictive validity.

Pilot geography: use supplied Chicago IDs for Loop, Near West Side, West Town, South Lawndale and O'Hare after validating name-to-ID mapping. Together they provide dense, industrial/mixed, residential and edge/airport cases. They are processing fixtures, **not prespecified Brás analogues**. Retain Brás, Itaim Bibi and Grajaú as SP contrast cases; do not select pilots based on resulting similarity.

## 7. File organization and reproducibility

Use `analysis/data/Chicago` as the canonical Chicago source root; do not introduce parallel `CHI`, `Chicago data` or working-directory-dependent trees. Proposed new paths:

```text
analysis/config/sp_chicago_harmonization_v1.json
analysis/scripts/harmonization/          # shared entity, geometry and measurement functions
analysis/scripts/prepare_chicago.py
analysis/tests/test_harmonization.py
analysis/work/prepared/Chicago/<run>/
analysis/work/runs/sp_chicago_harmonization_v1/
analysis/results/Chicago/<release>/     # tables, spatial, reports, validation
analysis/results/SP/<harmonized_release>/ # new SP attributes/model, distinct from v2
analysis/results/SP_CHI/<model>/        # shared fit, comparisons and sensitivity
```

Keep acquisition/preparation intermediates local under existing ignore rules. Publish compact aggregate results, source metadata and code. Do not modify the frozen SP v2 model or overwrite Chicago source data. Store country/city-qualified IDs, effective periods, source field mappings, entity counts, area/job/population numerators, denominators, source/allocated coverage and uncertainty flags in the long table.

The current model loader correctly enforces the SP-only 96-ID contract. A cross-city loader must be a separate implementation with declared city-specific ID universes and common-feature schemas, not a weakened SP validator. Reuse the now-tested transform/apply, composition, weighting and distance mathematics once the cross-city data contract passes.

## 8. Acceptance and limits

Require exact identities and no row multiplication; valid metric geometry; mapped source completeness checks; conserved population/jobs/areas with explicit outside or unresolved buckets; common semantics for included families; GHSL valid-support and partial-cell accounting; deterministic joins; transformed finite values; identical model state for both cities; and independently reconstructed distances/contributions. Targeted tests must include false planar overpasses, border blocks/cells, NoData versus genuine zero, volume conservation, zero support, multiple nearby same-route stops and mutually exclusive city IDs. Add independent raster-aggregation fixtures, transform/state replay, and distance/contribution reconstruction. Cadastral conversion and condominium tests are unnecessary unless those excluded families are explicitly reopened.

Coverage percentages describe their specific source universe. Do not replace unknown physical completeness with a generic 95% threshold or hide unmatched mass in zero-valued features. Publish exclusions and differences before the cross-city ranking.

**Current next step:** H4 review of H1–H3 candidate outputs under a newly versioned M2-excluded scope. M2 remains a historical diagnostic; M3/M4 remain unaccepted candidates after their semantic gates. U1 is withheld and U2 extended-only. SP bus supply was recomputed after discovering nonbus routes in the legacy input. No model fitting or acceptance has occurred. Consult the model status and execution ledger before resuming.
