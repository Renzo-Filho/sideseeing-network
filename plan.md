# São Paulo–Chicago urban-form comparison: research protocol

## Current scope decision — September 25, 2026

**Current sequence:** develop and validate a **Chicago-only model** over 77 Community Areas first. The São Paulo–Chicago common model is a future stage and must not block Chicago-local feature decisions. The [Chicago-only reassessment](docs/chicago/CHICAGO_ONLY_MODEL_REASSESSMENT.md) distinguishes existing local measurements from unresolved local source and method gates. A Chicago-only fit requires a new Chicago contract and local scaling; the old SP-anchored cross-city contracts do not authorize it.

For M3/M4, follow the [Chicago physical block protocol](docs/chicago/CHICAGO_PHYSICAL_BLOCK_PROTOCOL_V1.md), its [small-pilot assessment](analysis/results/Chicago/chicago_block_protocol_pilot_v1_2026_09_26/README.md), the [established-method comparison](analysis/results/Chicago/chicago_block_method_comparison_v1_2026_09_26/README.md), and the [new complete-zone iteration](analysis/results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/README.md). The established comparison found identical momepy/Shapely faces on the same municipal linework in 14 halos, and the published shape/area artifact rule flagged only 2/5 enclosed non-block point controls. The newer iteration selected 3 m mapped-alley reopening on development cores before an eight-sketch CHI:49 ordinary-grid holdout, where both municipal enclosures and Cook ROW plus Road Edge matched 8/8 rough blocks. This does not establish citywide accuracy or M4 shape. A fresh motorway-centered core exposed 13 tiny freeway slivers and a true residential wedge that the proposed 30% motorway-exposure deletion rule would wrongly remove. Three rough motorway-core outlines and two industrial-core outlines required post-freeze exclusion, exposing limits of imagery-only reference tracing. A named-street gap screen found 11 segment alerts across five cached Community Areas, including West Veterans Place, which remains a known merged block until its landward edges are established. OSM public-edge screening, parcel-group identity, and DuPage Parcel Blocks have not solved the physical-block contract. **M3/M4 remain unaccepted.** Next establish independent complete references with road-status review, repair missing named-street boundaries, validate context-aware non-block adjudication on unseen zones, and only then build and audit all 77 Community Areas. Census-block size/shape remains a separately named fallback, not an automatic physical-block replacement.

The [2022 Cook LiDAR raster pilot](analysis/results/Chicago/chicago_m3_lidar_motorway_pilot_2026_09_26/README.md) supports adding 3D physical context to this workflow. Height difference protected the visibly built frontage wedge from a simple motorway filter, but two false freeway slivers had similarly strong height signals. LiDAR therefore enters as review and grade-separation evidence; a classified point-cloud trial and independent validation are required before 3D can drive automatic corrections.

The [classified-point follow-up](analysis/results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26/README.md) has now tested two targeted 2022 Cook LAS tiles. Building-class returns support the narrow real frontage wedge while vegetation-class returns explain the high raster signal in two slivers. Road-surface-class returns trace the West Veterans Place ROW/Road Edge gap, and a bridge-deck cluster is about 6.38 m above local ground. These observations support a **2D candidate + 3D corroboration/repair queue**, with road status and exact landward edges still established from municipal/cadastral/imagery evidence. No 3D threshold is an approved automatic deletion or citywide M3/M4 rule; independent complete-zone validation remains the gate.

M2 (junction/intersection density) is **deferred and excluded from the planned Chicago model and any future São Paulo–Chicago common distance**. This is a feature-scope decision, not a finding that junctions are unimportant or that the candidate measures are invalid everywhere. The existing São Paulo v2 model and historical M2 pilots remain intact as evidence; neither their values nor their weight carry into a new model. Reopening M2 requires a separately recorded decision and paired validation of physical junctions before fitting. The [current model status](docs/MODEL_STATUS.md) records the active work plan. The original 13-family design below is historical; excluding M2 leaves at most 12 of those original families, subject to the remaining measurement gates. The six-family proposal already excludes M2.

B1 footprint coverage and the supplemental BV vertical-form family are **retained in the planned Chicago and common model scope**. The [paired harmonization decision](docs/chicago/B1_BV_HARMONIZATION_DECISION.md) finds that both can be measured with common definitions and complete paired candidates; bounded independent source-accuracy and land-support checks remain before model-input acceptance. B1 uses unioned Overture footprint coverage on hydrographic land; BV uses land-weighted GHSL ANBH net grid height under one family budget, with volume as a sensitivity. BV is not a replacement for B2 reported floors or B3 constructed area. This decision does not settle the remaining families or authorize fitting.

## Chicago construction status — September 16, 2026

The [functional extension](docs/chicago/CHICAGO_FUNCTIONAL_EXTENSION.md) now constructs U2/U3/U4 from the new supplied data and reviews hydrography. Matched Overture sources have been acquired for paired morphology work; common-feature acceptance remains pending.

Local Chicago construction and remaining measurement gates are tracked in [docs/chicago/CHICAGO_EXECUTION_REPORT.md](docs/chicago/CHICAGO_EXECUTION_REPORT.md) and [data requirements](docs/chicago/CHICAGO_DATA_REQUIREMENTS.md). Local arithmetic checks alone do not make the attributes ready for cross-city ranking.


Originally updated 11 September 2026; M2 scope updated 25 September 2026. This is the current research protocol. [Implementation methods](docs/archive/plans/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md) and the [current model status](docs/MODEL_STATUS.md) govern detailed definitions, evidence and continuation.

## Objective and research sequence

First characterize São Paulo's urban form and functional structure independently of pedestrian-condition outcomes. Compare Brás with the other 95 municipal districts, then extend to Chicago once comparable sources and definitions are validated. Finally examine accessibility outcomes among morphologically similar areas. Similarity is descriptive; it does not establish causal effects on pedestrian conditions.

The principal questions are: what characterizes Brás; which São Paulo districts are similar under consistent measurements; which Chicago areas remain comparable after harmonization; and how do accessibility conditions differ among comparable places?

## Units, time and active families

The primary São Paulo unit is the municipal district, with two-character municipal ID and Brás=10. Chicago Community Areas are a later comparison unit, not automatically equivalent geographical supports. Assess scale sensitivity using aligned 250 m and 500 m projected grids before interpreting cross-city differences. Use EPSG:31983 for São Paulo measurements. Keep whole-object shape/count rules distinct from clipped extensive-area/length allocation.

The baseline is mixed-date: 2022 census/formal employment, 2026 fiscal register and building release, and separately documented road/structure/transit source periods. A GTFS calendar range or local file timestamp does not establish a synchronized measurement year.

| Family | Current definition |
|---|---|
| M1 | Street-network density |
| M2 | **Deferred from new Chicago and cross-city models.** Historical SP v2: intersection-density proxy excluding candidates within 5 m of bridge/viaduct/tunnel lines. |
| M3 | Block-size distribution |
| M4 | Block-shape distribution |
| M6 | Street hierarchy, separating observed and Local-imputed classes |
| M7 | Accepted physical-parcel density |
| B1 | Building-footprint coverage using reviewed land-area denominators |
| B2 | Cadastral floor-count proxy; units floors, not metres |
| B3 | Cadastral constructed-area intensity with validated unique-unit aggregation |
| U1 | Observed cadastral land-use mix |
| U2 | RAIS formal employment density through an accepted CEP geography |
| U3 | Census population density |
| U4 | Dated service-weighted bus access with explicit spatial catchment assumptions |

M5 and U5 were removed by the user. The table records **13 originally planned families**; M2 is now deferred, so the maximum original-family scope under discussion is 12. These counts are not numeric-column counts: quantiles, distributions and class shares can expand the matrix. Record column selection and family weights explicitly for any new model.

## Modeling and interpretation, after feature acceptance

Keep source dates, entity definitions, numerator/denominator, coverage, imputation and quality status with each feature. Missing data remain null with reasons; confirmed absence can be zero. Avoid fitting biased quantiles, incomplete class vectors or unresolved job allocations as fully observed values.

Transform skewed positive variables deliberately; save transformations and scaling fitted on the declared comparison universe. Examine correlation and composition constraints, avoid singular covariance and prevent families with more summaries from dominating. Compare standardized Euclidean, suitably regularized Mahalanobis and selected PCA-space distances; use clustering as a sensitivity analysis. Inspect the sources of similarity, proxy/imputation sensitivity and ranking stability rather than declaring the first-ranked district an equivalent neighborhood.

Before joint-city modeling, align entity units, floor-count proxies, formal-job coverage, modes/service windows, temporal interpretation and spatial support. Revisit normalization for the joint population. Do not compare São Paulo cadastral floors with Chicago metre heights or differently defined transit indices as though they were the same attribute.

## Later accessibility study

Keep pedestrian accessibility outcomes separate from the morphology selection stage to avoid selecting analogues on the outcome being compared. Later work should validate sidewalk geometry/CRS, width and slope meanings, crossings, barriers, curb-ramp continuity, surface/obstruction observations, route coverage and annotation reliability. Treat any composite accessibility index, its components and weights as a separate prespecified protocol before collection/modeling. Model outcomes only with explicit exposure/coverage denominators and appropriate spatial validation; exploratory association is not causal identification.

## Current execution boundary

The v2/v3 baselines are preserved. Historical N10 attribute construction is complete for all 96 districts: 77 numeric attributes/diagnostics/sensitivities and 23 primary candidate columns across the original 13 families. Historical SP M2 uses the 5 m structure-exclusion proxy; it is not in the planned Chicago or common score. M6 assigns unclassified roads Local with imputation flags; U2 uses area-first with an unlocated bucket and alternative scenarios retained. The [construction report](analysis/results/SP/reports/ATTRIBUTE_REPORT.md) documents implementation and validation. The SP similarity model is implemented and corrected in [v2](docs/sp/SP_MODEL_FIXES.md), with source/weight robustness evaluated. [Chicago harmonization](docs/chicago/CHICAGO_HARMONIZATION_PLAN.md) has entered local-source attribute construction; grid-morphology attributes, cross-city fitting and the separate accessibility study remain later work.

Current documentation is indexed in `docs/README.md`; SP preparation history is under `docs/sp/`, while superseded plans and audits are explicitly archived under `docs/archive/`. Evidence, scripts and prepared datasets remain in the analysis workspace. Use the current handoff rather than historical manifests to identify the next action.
