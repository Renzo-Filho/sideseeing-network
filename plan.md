# São Paulo–Chicago urban-form comparison: research protocol

## Chicago construction status — September 16, 2026

Local Chicago construction and remaining measurement gates are tracked in [analysis/CHICAGO_EXECUTION_REPORT.md](analysis/CHICAGO_EXECUTION_REPORT.md) and [data requirements](analysis/CHICAGO_DATA_REQUIREMENTS.md). Local arithmetic checks alone do not make the attributes ready for cross-city ranking.


Updated 11 September 2026. This is the current research scope. [Implementation methods](analysis/notes/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md) and the [current resolution handoff](analysis/notes/SP_DATA_RESOLUTION_HANDOFF.md) govern detailed definitions, evidence and continuation.

## Objective and research sequence

First characterize São Paulo's urban form and functional structure independently of pedestrian-condition outcomes. Compare Brás with the other 95 municipal districts, then extend to Chicago once comparable sources and definitions are validated. Finally examine accessibility outcomes among morphologically similar areas. Similarity is descriptive; it does not establish causal effects on pedestrian conditions.

The principal questions are: what characterizes Brás; which São Paulo districts are similar under consistent measurements; which Chicago areas remain comparable after harmonization; and how do accessibility conditions differ among comparable places?

## Units, time and active families

The primary São Paulo unit is the municipal district, with two-character municipal ID and Brás=10. Chicago Community Areas are a later comparison unit, not automatically equivalent geographical supports. Assess scale sensitivity using aligned 250 m and 500 m projected grids before interpreting cross-city differences. Use EPSG:31983 for São Paulo measurements. Keep whole-object shape/count rules distinct from clipped extensive-area/length allocation.

The baseline is mixed-date: 2022 census/formal employment, 2026 fiscal register and building release, and separately documented road/structure/transit source periods. A GTFS calendar range or local file timestamp does not establish a synchronized measurement year.

| Family | Current definition |
|---|---|
| M1 | Street-network density |
| M2 | Intersection-density proxy excluding candidates within 5 m of bridge/viaduct/tunnel lines |
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

M5 and U5 were removed by the user. These are **13 families**, not necessarily 13 numeric columns: quantiles, distributions and class shares can expand the matrix. Record column selection and family weights explicitly.

## Modeling and interpretation, after feature acceptance

Keep source dates, entity definitions, numerator/denominator, coverage, imputation and quality status with each feature. Missing data remain null with reasons; confirmed absence can be zero. Avoid fitting biased quantiles, incomplete class vectors or unresolved job allocations as fully observed values.

Transform skewed positive variables deliberately; save transformations and scaling fitted on the declared comparison universe. Examine correlation and composition constraints, avoid singular covariance and prevent families with more summaries from dominating. Compare standardized Euclidean, suitably regularized Mahalanobis and selected PCA-space distances; use clustering as a sensitivity analysis. Inspect the sources of similarity, proxy/imputation sensitivity and ranking stability rather than declaring the first-ranked district an equivalent neighborhood.

Before joint-city modeling, align entity units, floor-count proxies, formal-job coverage, modes/service windows, temporal interpretation and spatial support. Revisit normalization for the joint population. Do not compare São Paulo cadastral floors with Chicago metre heights or differently defined transit indices as though they were the same attribute.

## Later accessibility study

Keep pedestrian accessibility outcomes separate from the morphology selection stage to avoid selecting analogues on the outcome being compared. Later work should validate sidewalk geometry/CRS, width and slope meanings, crossings, barriers, curb-ramp continuity, surface/obstruction observations, route coverage and annotation reliability. Treat any composite accessibility index, its components and weights as a separate prespecified protocol before collection/modeling. Model outcomes only with explicit exposure/coverage denominators and appropriate spatial validation; exploratory association is not causal identification.

## Current execution boundary

The v2/v3 baselines are preserved. N10 attribute construction is complete for all 96 districts: 77 numeric attributes/diagnostics/sensitivities and 23 primary candidate columns across 13 families. M2 uses the approved 5 m structure-exclusion proxy; M6 assigns unclassified roads Local with imputation flags; U2 uses area-first with an unlocated bucket and alternative scenarios retained. The [construction report](analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) documents implementation and validation. The SP similarity model is implemented and corrected in [v2](analysis/SP_MODEL_FIXES.md), with source/weight robustness evaluated. [Chicago harmonization](analysis/CHICAGO_HARMONIZATION_PLAN.md) has entered local-source attribute construction; grid-morphology attributes, cross-city fitting and the separate accessibility study remain later work.

Current Chicago documentation is linked from `analysis/README.md`; SP preparation history is consolidated under `analysis/notes/`. Superseded status reports have been removed; evidence, scripts and prepared datasets remain. Use the current handoff rather than historical manifests to identify the next action.
