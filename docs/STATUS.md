# Model status and current scope

This is the **only page that carries dated project status**. Other documents describe methods, decisions and evidence; update this page after each substantive checkpoint instead of adding status banners elsewhere.

## Current sequence

**Current sequencing decision — 25 September 2026:** prioritize a **Chicago-only model**; defer the SP–Chicago common model to a later stage. Use the [Chicago-only family reassessment](#chicago-only-model-current-stage) for current inclusion and data gates. Cross-city acceptance requirements elsewhere on this page describe future work and do not prevent use of an independently valid Chicago-local measurement. No Chicago-only fit has been authorized or produced.

**As of 25 September 2026. M2 is deferred from both the planned Chicago model and future cross-city model; bulk processing and fitting remain paused.** This is the current entry point for the shared urban model. The [open discussion](DECISIONS.md) leads the search for stronger street-morphology, workplace and land-use measures; the [bounded U1 screens](../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md) and [Chicago M follow-up](../analysis/results/Chicago/chicago_m_holdout_2026_09_25/README.md) remain diagnostic. The [six-family review](harmonization/PLAN.md) remains a baseline scope option; the [original 13-family ledger](harmonization/PLAN.md) preserves historical definitions and gates for still-active families. The [v2 contract](../analysis/config/sp_chicago_harmonization_v2_full_scope.json) is a frozen 13-family proposal, **not the current inclusion list**; its `fit_authorized=false` remains in force. A new versioned contract must omit M2 before any future fit. The [execution record](harmonization/EXECUTION_LOG.md) preserves methods and decisions. No common fit is authorized.

**Current sequence:** develop and validate a **Chicago-only model** over 77 Community Areas first. The São Paulo–Chicago common model is a future stage and must not block Chicago-local feature decisions. The [Chicago-only reassessment](#chicago-only-model-current-stage) distinguishes existing local measurements from unresolved local source and method gates. A Chicago-only fit requires a new Chicago contract and local scaling; the old SP-anchored cross-city contracts do not authorize it.

For M3/M4, follow the [Chicago physical block protocol](chicago/BLOCKS_M3_M4.md), its [small-pilot assessment](../analysis/results/Chicago/chicago_block_protocol_pilot_v1_2026_09_26/README.md), the [established-method comparison](../analysis/results/Chicago/chicago_block_method_comparison_v1_2026_09_26/README.md), and the [new complete-zone iteration](../analysis/results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/README.md). The established comparison found identical momepy/Shapely faces on the same municipal linework in 14 halos, and the published shape/area artifact rule flagged only 2/5 enclosed non-block point controls. The newer iteration selected 3 m mapped-alley reopening on development cores before an eight-sketch CHI:49 ordinary-grid holdout, where both municipal enclosures and Cook ROW plus Road Edge matched 8/8 rough blocks. This does not establish citywide accuracy or M4 shape. A fresh motorway-centered core exposed 13 tiny freeway slivers and a true residential wedge that the proposed 30% motorway-exposure deletion rule would wrongly remove. Three rough motorway-core outlines and two industrial-core outlines required post-freeze exclusion, exposing limits of imagery-only reference tracing. A named-street gap screen found 11 segment alerts across five cached Community Areas, including West Veterans Place, which remains a known merged block until its landward edges are established. OSM public-edge screening, parcel-group identity, and DuPage Parcel Blocks have not solved the physical-block contract. **M3/M4 remain unaccepted.** Next establish independent complete references with road-status review, repair missing named-street boundaries, validate context-aware non-block adjudication on unseen zones, and only then build and audit all 77 Community Areas. Census-block size/shape remains a separately named fallback, not an automatic physical-block replacement.

The [2022 Cook LiDAR raster pilot](../analysis/results/Chicago/chicago_m3_lidar_motorway_pilot_2026_09_26/README.md) supports adding 3D physical context to this workflow. Height difference protected the visibly built frontage wedge from a simple motorway filter, but two false freeway slivers had similarly strong height signals. LiDAR therefore enters as review and grade-separation evidence; a classified point-cloud trial and independent validation are required before 3D can drive automatic corrections.

The [classified-point follow-up](../analysis/results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26/README.md) has now tested two targeted 2022 Cook LAS tiles. Building-class returns support the narrow real frontage wedge while vegetation-class returns explain the high raster signal in two slivers. Road-surface-class returns trace the West Veterans Place ROW/Road Edge gap, and a bridge-deck cluster is about 6.38 m above local ground. These observations support a **2D candidate + 3D corroboration/repair queue**, with road status and exact landward edges still established from municipal/cadastral/imagery evidence. No 3D threshold is an approved automatic deletion or citywide M3/M4 rule; independent complete-zone validation remains the gate.

M2 (junction/intersection density) is **deferred and excluded from the planned Chicago model and any future São Paulo–Chicago common distance**. This is a feature-scope decision, not a finding that junctions are unimportant or that the candidate measures are invalid everywhere. The existing São Paulo v2 model and historical M2 pilots remain intact as evidence; neither their values nor their weight carry into a new model. Reopening M2 requires a separately recorded decision and paired validation of physical junctions before fitting. The [current model status](#current-sequence) records the active work plan. The original 13-family design below is historical; excluding M2 leaves at most 12 of those original families, subject to the remaining measurement gates. The six-family proposal already excludes M2.

B1 footprint coverage and the supplemental BV vertical-form family are **retained in the planned Chicago and common model scope**. The [paired harmonization decision](DECISIONS.md) finds that both can be measured with common definitions and complete paired candidates; bounded independent source-accuracy and land-support checks remain before model-input acceptance. B1 uses unioned Overture footprint coverage on hydrographic land; BV uses land-weighted GHSL ANBH net grid height under one family budget, with volume as a sensitivity. BV is not a replacement for B2 reported floors or B3 constructed area. This decision does not settle the remaining families or authorize fitting.

### Chicago construction status — 16 September 2026

The [functional extension](chicago/ATTRIBUTES.md) now constructs U2/U3/U4 from the new supplied data and reviews hydrography. Matched Overture sources have been acquired for paired morphology work; common-feature acceptance remains pending.

Local Chicago construction and remaining measurement gates are tracked in [Chicago execution log](chicago/EXECUTION_LOG.md) and [data requirements](chicago/DATA_SOURCES.md). Local arithmetic checks alone do not make the attributes ready for cross-city ranking.

## Chicago-only model (current stage)

Reassessment of 25 September 2026.

### Scope

The next model is **Chicago-only**, using the 77 Community Areas. A São Paulo–Chicago similarity model is a future stage with its own feature definitions, source checks, fitted state and release. Do not make present Chicago feature inclusion depend on matching a São Paulo source. The user has excluded M2 from the planned Chicago model and retained B1 footprint coverage and BV estimated vertical form. Neither the existing SP-fitted H4 proposal nor its six-family weighting is a Chicago-only model contract; no new fit has been authorized.

The question for each Chicago family is whether it measures a defined Chicago characteristic over credible citywide support, not whether it matches a São Paulo fiscal or administrative field. Existing Chicago local and functional releases are evidence and starting inputs; experimental and partial fields do not become accepted merely because cross-city comparability is deferred.

| Family | Chicago-only disposition | Remaining Chicago gate |
|---|---|---|
| M1 street density; M6 class mix | Constructed citywide from municipal and Overture sources. Plausible local candidates. | Choose and freeze one street universe/class scheme; review airport/edge and source-completeness cases. |
| M2 junction density | Excluded by user decision. | None for this model. |
| M3 block size; M4 block shape | Experimental enclosures, not accepted physical blocks. The [Chicago physical-block protocol](chicago/BLOCKS_M3_M4.md) and [small-pilot assessment](../analysis/results/Chicago/chicago_block_protocol_pilot_v1_2026_09_26/README.md) formalize the staged method and gate status. The [ROW/parcel pilot](../analysis/results/Chicago/chicago_m3_row_land_2026_09_26/README.md) removes many false road fragments. A [fresh-tile test](../analysis/results/Chicago/chicago_m3_fresh_tiles_2026_09_26/README.md) favors alley-open ROW on 11 rough new block sketches, but confirms a named-street ROW gap and inadequate DuPage airport ROW. The [candidate inventory](../analysis/results/Chicago/chicago_m3_candidate_v1_2026_09_26/README.md) finds nine obvious freeway islands among 26 tile-contained candidates; parcel groups support the false islands and also merge two distinct Loop blocks. A [new CHI:49 motorway stress check](../analysis/results/Chicago/chicago_m3_motorway_holdout_2026_09_26/README.md) supports a motorway flag but has two ambiguous sketches and an incomplete true-block census. Cook Lake polygons resolve the two fresh water controls. | Resolve and independently test the named-street ROW gap; validate freeway/rail/private-access/airport rules on a complete reference inventory across neighborhoods; measure precision, recall, boundary/area error and M4 shape tails. Verify DuPage physical-road support before any 77-area release. M4 uses accepted M3 blocks. |
| M7 physical cadastral entities | Not ready under the original physical-entity definition. | Obtain or resolve Cook parent/condo/elevation relationships and DuPage coverage; do not equate PINs or polygon rows with physical entities. A separately named mapped-parcel statistic would need its own decision. |
| B1 footprint coverage | Retained. Complete Overture and historical municipal coverage candidates exist. | Review mapped omissions/commissions and hydrographic land support in contrasting Chicago areas; retain source vintage/lineage. |
| BV estimated vertical form | Retained. Complete Chicago GHSL ANBH and volume candidates exist. | Check 100 m grid-height plausibility and valid/zero/edge support; give height and volume one family budget and inspect no-BV sensitivity. |
| B2 reported stories | A valid **reported-subset diagnostic**, not yet an all-building floor distribution. Positive municipal reports cover 427,924 of 820,395 assigned ACTIVE buildings (52.16%); district coverage ranges 20.90–76.78%. | Resolve categorical/split-floor meaning and coverage bias by property type and area. Do not impute missing stories or interpret subset quantiles as whole-stock quantiles without evidence. |
| B3 constructed floor area | **Current data gap for the original feature.** No verified unique all-stock Chicago GFA source exists. | Find an improvement/fiscal-unit source with clear area meaning, parent/unit links and residential, condo, commercial, exempt and DuPage coverage; prevent parent-area duplication. |
| U1 land-use mix | Chicago-local CMAP 2023 eight-group area entropy and shares exist; SP ontology is irrelevant to this stage. | Freeze the local use ontology and classified-support policy; audit mixed/secondary, `6000` nonparcel, unknown and vacant area. Report coverage beside entropy. |
| U2 workplace intensity | Chicago-local LODES WAC 2022 job density exists; RAIS comparison is irrelevant to this stage. | State the covered-job universe and whole-block area allocation; inspect downtown/boundary and business-support sensitivities, plus source-file provenance. |
| U3 resident density | Chicago Census 2020 block allocation exists. | Use documented Census support and boundary residuals; keep the uncertain supplied ACS aggregate as a separate period diagnostic. |
| U4 reachable bus supply | CTA GTFS weekday/weekend, 400/800 m scenarios exist. | Freeze a dated Chicago-only service window and method; report that CTA-only scheduled bus service excludes Pace and does not measure actual reliability. |

### Practical model path

1. Start a **new Chicago-only feature contract** with fixed observation years, eligible support, family budgets, missingness rules and precommitted sensitivities. Do not repurpose the SP-anchored cross-city H4 contract. B1 and BV are retained; M2 is excluded. Select other families only after their Chicago gates pass.
2. Review a bounded set of Chicago maps/records for M1/M6, B1/BV, U1/U2 and U4. Existing local and functional candidate tables cover all 77 areas, so this step needs no broad reconstruction. Keep B2's reported subset and coverage diagnostic visible.
3. Pursue M3/M4 and M7 as separate method/source work. Seek a specific B3 area source; if none is available, omit original B3 from the Chicago score and state the loss. No proxy can silently take its family name or weight.
4. After the selected Chicago features pass, create a versioned Chicago candidate matrix and fit Chicago-only transformations/scales on the declared Chicago cohort. Test feature contributions, omission/source sensitivities and rank stability within Chicago. Cross-city calibration and Brás comparisons belong to the later project stage.

Evidence: [Chicago local release](../analysis/results/Chicago/chi_local_2026_09_16_v1/README.md), [functional extension](../analysis/results/Chicago/chi_functional_2026_09_16_v2/README.md), [held-out M review](../analysis/results/Chicago/chicago_m_holdout_2026_09_25/README.md), [B1/BV decision](DECISIONS.md), and [current model status](#current-sequence).

### Plain-language feature notes

#### Why Chicago can be easier, and why it is not automatic

For a Chicago-only model, we can ask whether each number describes Chicago well without first matching a São Paulo tax field or map class. That is a real simplification. We still have to decide what the feature counts and whether its Chicago data cover the whole city fairly. The existing local tables are starting evidence, not a finished Chicago score. A new contract would choose the features, years, missing-data rules, weights, and Chicago-based scales before ranking the 77 Community Areas. M2 is excluded; B1 and BV are retained for review. The descriptions below keep the same interpretation as above and focus on what Chicago alone still needs.

#### M1: Street-network density

**What it would say:** Which Community Areas have more mapped street length for their size. A tight grid and a knot of highway ramps can both produce a high number.

**Why it is still unfinished:** The city and Overture maps include different roads. At O’Hare, some city class-99 lines are airport circulation, not ordinary neighborhood streets. We need one rule for streets, ramps, divided roads, and map edges, followed by local checks. Status: plausible citywide candidate, not yet accepted.

#### M2: Intersection density

**What it would say:** How frequently streets meet and offer a possible change of direction.

**Why it is still unfinished:** Nearby map points can be parts of one divided-road crossing or different upper and lower roads. Chicago endpoint and connector counts are useful experiments, but they are not confirmed real junctions. Status: deliberately excluded; no M2 value or weight belongs in the new Chicago score.

#### M3: Block size

**What it would say:** Whether Chicago’s street-bounded land is divided into small, fine-grained blocks or large, coarse-grained ones.

**Why it is still unfinished:** The 23,204 newly generated land faces include true blocks, but also motorway islands, airport land, uncertain railway edges, and faces merged across a missing street. The West Veterans Place split is proposed, not independently verified. A full set of independently traced blocks—including ones the computer misses—must test the repair method across very different neighborhoods. Status: not accepted.

#### M4: Block shape

**What it would say:** Whether those blocks are compact or long and narrow, a clue to possible detours.

**Why it is still unfinished:** A false sliver or a merged block can dominate the shape statistics. We must first settle M3, then measure the whole outline without letting a Community Area border create a fake edge. Status: not accepted.

#### M6: Street-class composition

**What it would say:** How much of each area’s mapped street length is local street, major road, motorway, and other classes.

**Why it is still unfinished:** Chicago can choose a local classification without matching São Paulo, but it must choose one consistent street map, check O’Hare and peripheral coverage, and leave truly unknown roads visible. Status: calculated candidate, not yet accepted.

#### M7: Physical parcel density

**What it would say:** Whether land is split into many small property units or a few large ones.

**Why it is still unfinished:** A Cook PIN might identify a condo unit rather than a ground parcel, and DuPage has its own records. A simple row count could make one apartment tower look like dozens of separate land pieces. The parent relationships still need verification. Status: not accepted.

#### B1: Building-footprint coverage

**What it would say:** How much ground in a Community Area is covered by mapped buildings, regardless of their height.

**Why it is still unfinished:** Full citywide Overture and older municipal candidates exist, but we need to check where each map misses or adds buildings and whether the land denominator follows a reasonable water boundary. Status: retained, not yet accepted as a score input.

#### B2: Reported floor counts

**What it would say:** The middle and taller end of Chicago buildings that actually report stories.

**Why it is still unfinished:** Only 52.16% of assigned active municipal buildings have a positive story report, and coverage varies greatly by area. Zero often means no report. Broad labels, split levels, condos, commercial properties, and DuPage gaps may bias the reported subset. Status: a useful subset diagnostic, not an accepted whole-stock feature.

#### B3: Constructed floor-area intensity

**What it would say:** How much indoor built area is recorded relative to the land underneath it.

**Why it is still unfinished:** Chicago has several partial area fields, not one verified all-building total. They define space differently and can repeat a parent building’s area for many condo records. If a complete, nonduplicated source cannot be established, original B3 should be omitted explicitly rather than replaced by footprint or estimated volume. Status: not accepted.

#### Supplemental BV: Estimated vertical form

**What it would say:** Whether a Community Area appears taller on average in a broad GHSL grid, even if B1’s ground coverage is similar.

**Why it is still unfinished:** Compare selected cells with local building evidence and inspect zeros, missing cells, water, and district edges. Keep height and volume under one family weight and test what changes if BV is left out. Status: retained, not yet accepted; it is not a replacement for B2 or B3.

#### U1: Land-use diversity

**What it would say:** Whether mapped Chicago land is mostly one use or spread among homes, commerce, industry, institutions, and other uses.

**Why it is still unfinished:** The CMAP eight-group calculation exists, but roads and other nonparcel land marked 6000 cover meaningful area. Mixed, vacant, secondary, and unknown uses need a declared rule; otherwise a diversity score can change just because one area’s map classifies more land. Status: candidate, not yet accepted.

#### U2: Workplace-job density

**What it would say:** Where LODES reports concentrations of jobs within Chicago.

**Why it is still unfinished:** Jobs are reported by Census block, while Community Area boundaries sometimes cut blocks. Moving jobs according to block area or likely business land changes estimates, especially around boundaries and downtown. We must state which jobs the source includes and preserve source-file lineage. Status: candidate, not yet accepted; matching Brazil’s RAIS is not required for the local model.

#### U3: Resident-population density

**What it would say:** Where Chicago Census residents live per square kilometre, distinct from daytime crowds.

**Why it is still unfinished:** The 2020 block counts and area allocation are already well documented, making this one of the clearer local candidates. Yet the contract must state how boundary-crossing blocks and small uncovered gaps were handled. An older supplied ACS Community Area total has uncertain period and should remain separate. Status: close to a defined local measure, but not formally accepted for the new score.

#### U4: Reachable bus supply

**What it would say:** How much scheduled CTA bus service is near residents during a chosen morning or weekend window.

**Why it is still unfinished:** Several radii and days have been calculated, but one main window and rule must be chosen before fitting. The CTA feed excludes Pace, schedules are not observed reliability, and a straight-line distance can cross barriers. Status: candidate, not yet accepted.

#### How the Chicago-only work can help the cross-city comparison

Validating Chicago first can give us trusted examples of real versus false blocks, missing roads, mapping gaps, and incomplete building records. Those examples reveal what a future common definition must survive. But a locally useful Chicago number does not automatically become a comparable São Paulo–Chicago number. The later model must define the same idea in both cities, rebuild changed measurements in both, learn its numerical scales from São Paulo, and apply those saved scales to Chicago without silently changing the meaning of a feature.

#### Status basis

This account follows the current project status and the Chicago-only reassessment, 13-family completion ledger, B1/BV decision, six-family reassessment, physical-block protocol, and dated result reports in the repository. Passing arithmetic checks means the calculations are reproducible; it does not by itself prove that the maps represent the real world or authorize a model fit.

## SP–Chicago common model (future stage)

### Where the model stands

**M2 excluded; B1 and BV paired methods feasible; remaining scope open.** Paired candidates cover **96 São Paulo districts and 77 Chicago Community Areas**. The [B1/BV harmonization decision](DECISIONS.md) retains both in the planned Chicago and common model scope: shared definitions and complete paired candidate values exist, while independent source-accuracy and land-support gates remain open. This is not acceptance of their values for fitting or a decision about B2/B3. The restored six-family proposal uses **M1, M6, B1, BV, U3 and U4**. The original comprehensive design had 13 families. Its current maximum scope is **12 original families**, excluding M2: M1, M3, M4, M6, M7, B1, B2, B3, U1, U2, U3 and U4; BV is a separate supplemental family, not one of those original families. Neither route has accepted measurements for a common fit. There is no harmonized SP fitted state, Chicago application, common distance matrix, cross-city ranking or PCA.

The existing [SP model v2](../analysis/results/SP/models/sp_urban_model_v2/), [Chicago local baseline](../analysis/results/Chicago/chi_local_2026_09_16_v1/) and [Chicago functional extension](../analysis/results/Chicago/chi_functional_2026_09_16_v2/) remain separate releases. A six-family release, if selected, must be named and interpreted as a limited structural, population and bus-service comparison. A broader route may retain up to the 12 original families other than M2, depending on acceptance. Either new SP companion must fit transformations, scales and family calibration on SP only and apply the saved state unchanged to Chicago.

| Work completed | Evidence and present use |
|---|---|
| H1–H3 paired construction | [Sealed 173-unit candidate release](../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md): 6,209 long-form rows, 37 candidate/diagnostic columns, separate [SP](../analysis/results/SP/harmonized_candidates_2026_09_22/) and [Chicago](../analysis/results/Chicago/harmonized_candidates_2026_09_22/) companions. None of those column counts implies accepted model coordinates. |
| Physical-method review | [M1/M6 all-unit audit](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md) locks a ten-class method for review; source-coverage exceptions remain. [M2 source topology](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md), [M3/M4 local-reference fixtures](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures/README.md), [rail/water tests](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md) and [local rail envelopes](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v4_local_rail/README.md) are diagnostic; they do not establish a common physical-block method. |
| Footprints and vertical form | [Microsoft six-tile inventory and eight-unit B1 pilot](../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md) are complete. Overture remains the primary B1 candidate; Microsoft remains diagnostic. All 2,035,929 SP Microsoft records in the selected tiles have height `-1`. [GHSL public height/volume candidates](../analysis/results/SP_CHI/ghsl_public_2026_09_21/README.md) are supplemental BV evidence, not floors or constructed area. |
| Functional candidates | Paired U3 population and corrected bus-only U4 tables exist in H1–H3. Chicago [U2 business-support sensitivity](../analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/README.md) exists. Vintage, service, job-universe and land-use semantics remain to be accepted. |
| Reopened H4 proposal | The [six-family readiness review](../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md) passed 13 input checks. Previously rejected on scope, it is now [reopened for scientific review](harmonization/PLAN.md). Its sealed matrix is unchanged; no fit followed. |

### Broader-scope family gates

This table tracks the original families, with M2 marked deferred; the [six-family review](harmonization/PLAN.md) has narrower acceptance conditions. These are work states, **not acceptance statuses**. See the [ledger](harmonization/PLAN.md) for definitions and evidence.

| Family | Current state | Required closure |
|---|---|---|
| M1 street density | Paired candidate; ten-class method locked for review | Resolve O'Hare airfield and Marsilac rural/source-coverage outliers; audit eligible linework and boundary length in both cities. |
| M2 physical junctions | **Deferred; excluded from Chicago and future cross-city scoring** | No current closure task or rebuild. Historical SP v2 and bounded topology pilots remain diagnostic. Reopening requires an explicit scope decision and paired physical-arm/grade validation. |
| M3 physical-block size | Enclosure pilots, no accepted block population | Establish a defensible shared boundary network and whole-block ownership; eliminate false slivers without deleting real blocks; inspect matched maps and distribution shifts. |
| M4 physical-block shape | Pilot shapes only | Use the **same accepted whole blocks as M3** and freeze perimeter, holes, compactness and elongation rules. |
| M6 road hierarchy | Ten-class shares audited in 173 units | Resolve edge-unit source coverage, retain distinct `unclassified` and `unknown` mass, and verify class shares and extrapolation. |
| M7 physical cadastral entities | Parcel/PIN inputs available, entity population unresolved | Resolve Cook parcel/condo parent relationships, DuPage scope and cross-city physical-entity meaning; verify no tax-account multiplication. |
| B1 footprint coverage | **Retained; paired method feasible.** Exact Overture unions in both cities; Microsoft diagnostic pilot | Check mapped completeness and land/water support against independent local references; document source lineage and vintage sensitivity. |
| BV vertical form — supplemental | **Retained; paired method feasible.** Complete GHSL grid-height and volume candidates | Verify grid and land support, zero/NoData handling, independent local plausibility and temporal qualifications. Give height and volume one family budget; compare no-BV and volume-only sensitivities. BV does not resolve B2 or B3. |
| B2 reported floors | Partial stories and `num_floors` coverage | Link reported positive floors to the accepted entity population; resolve split/half-floor and missing commercial/condo/DuPage coverage without height conversion. |
| B3 constructed floor area | SP fiscal source, no proven Chicago all-stock equivalent | Obtain or establish comparable **unique constructed-area** support across Chicago residential, commercial and condo stock; reconcile units, duplicates and totals. Footprint area or volume cannot stand in. |
| U1 primary-use diversity | Exact six-unit area accounting and two-anchor POI provider audit completed; none accepted | Choose occupied-four versus six-class parcel-use estimand before scaling; inspect sampled labels independently. SP no-lot land includes 7–8.5% of selected district land inside mapped ordinary blocks, warranting targeted source review; Chicago `6000` is a nonparcel class. Some SP mixed labels can be explicitly recoded. POI diversity remains unweighted pending source-quality and added-information checks. |
| U2 workplace jobs | Paired candidates and Chicago allocation sensitivity | Reconcile RAIS/LODES workforce universes, unlocated/outside mass and allocation uncertainty before common interpretation. |
| U3 resident population | Paired complete candidates | Document 2022 SP versus 2020 Chicago vintages/support and a bounded sensitivity; preserve mass reconciliation. |
| U4 reachable bus supply | Corrected paired bus-only scenarios | Verify expected-frequency SP versus scheduled CTA meaning, service calendars/holiday exceptions, one-week date gap and scenario stability. |

See the [source and entity decision brief](DECISIONS.md) for the manual review protocol, exact M7/B2/B3 decisions and available routes.

**Critical dependency for the broader route:** M7, B2 and B3 are source and entity problems, not simply missing code. The available Microsoft and GHSL products cannot close them. M4 depends on M3 block identity; B2/B3 depend on a defensible entity/stock concept. The broader model cannot honestly be declared complete until its retained definitions and data pass. If an original measurement proves unsupported, prepare a concrete replacement definition and its effect for a user decision. M2 is the explicit exception: its exclusion has been decided and must be reflected in the next contract and weights.

### Next work packages, in order

0. **Six-family scope review; no fitting.** Agree whether the limited comparison is a separate interim release or a replacement research question, then review its six semantic gates and precommit sensitivities using the [reassessment](harmonization/PLAN.md).
1. **Manual source/entity decision checkpoint for the comprehensive route; no bulk rebuild.** Compare the available Cook, DuPage, commercial, condo and SP fiscal definitions against M7/B2/B3 requirements. Inspect a small Loop/Brás plus peripheral crosswalk and record duplicate/coverage issues, supported stock and exact missing evidence. Decide the measurement rules and acceptance tests before requesting a bounded source or restarting construction.
2. **Finish retained common physical methods.** Inspect paired M3/M4 block edges, including divided/stacked roads, ramps, rail and water boundaries. Reject rules that create narrow rail slivers or lose local reference blocks. Carry the declared pedestrian-street universe into any new boundary version, or justify a distinct boundary universe. Rebuild M3/M4 over 96/77 only after pilot rules pass. Close M1/M6 source-coverage audits and B1 local-reference checks alongside this work. Do not schedule an M2 rebuild.
3. **Close functional semantics.** Resolve U1 using the [six-unit exact-area follow-up](../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md), independent labels and a predeclared four/six-class ontology before any scale-up; reconcile U2 workforce universes and allocation; document U3 vintage sensitivity; compare U4 calendar/frequency/service support. Run paired fixture and conservation checks for each changed method.
4. **Publish a new scope contract and candidate version.** Exclude M2 from both Chicago and cross-city inclusion lists, assign its weight to no feature by default, and declare the remaining family budgets before fitting. Recompute changed retained families in **both** cities, save source/transform manifests, unit coverage and independent checks, and record pass/fail evidence for every included family. Keep sealed H1–H3, historical H4 and the old v2 contract untouched. The old contract remains `fit_authorized=false`; a new model remains unauthorized pending its own scope and semantic review.
5. **Fit and validate only after the chosen route passes its scientific acceptance review.** Fit the new harmonized SP transformations, scales and family calibration on 96 SP districts; save fitted state and 96×96 distances. Apply that unchanged state to 77 Chicago areas; publish cross-city/Brás rankings, family contributions, out-of-SP-range flags, robustness and sensitivity scenarios. Reconcile reported contributions to distances and document which analogues remain stable.
6. **Release the model and record.** Publish versioned SP and Chicago outputs, reproducible commands/manifests, validation receipts, limitations and a final H0–H6 account. Preserve the original SP v2 and Chicago releases.

## Documentation map

- **This page:** current scope, status, priority order and definition of done.
- [Handoff](HANDOFF.md): operational prompt for the next execution session.
- [Decisions](DECISIONS.md): dated decisions (M2 deferral, B1/BV, entities, SP methods) and open questions.
- [Research protocol](PROTOCOL.md): objectives, units, families and modeling rules.
- Chicago: [attributes](chicago/ATTRIBUTES.md), [data sources](chicago/DATA_SOURCES.md), [M3/M4 block protocol](chicago/BLOCKS_M3_M4.md), [execution log](chicago/EXECUTION_LOG.md).
- São Paulo: [attributes](sp/ATTRIBUTES.md), [preparation](sp/PREPARATION.md), [model v2](sp/MODEL.md).
- SP–Chicago (future): [plan, 13-family ledger and six-family option](harmonization/PLAN.md), [execution log](harmonization/EXECUTION_LOG.md), [frozen v2 contract](../analysis/config/sp_chicago_harmonization_v2_full_scope.json) (`fit_authorized=false`; supersede with a new version before fitting).
- [Survey](survey/README.md): paper-oriented evidence, experiment ledger and reproducibility protocol.
