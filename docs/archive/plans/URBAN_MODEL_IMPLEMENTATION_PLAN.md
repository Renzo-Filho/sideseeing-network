# Urban similarity model — detailed implementation plan

**Status update: the primary SP model and core robustness experiments are implemented and corrected in v2.** See [SP_MODEL_FIXES.md](../../sp/SP_MODEL_FIXES.md) for completed work, validation and remaining scientific limits. The following specification is retained as the implementation protocol. This plan starts from the completed São Paulo attribute release, compares Brás (`10`) with the other 95 municipal districts, and preserves the existing source/proxy decisions. It specifies a descriptive similarity model, not a predictor of pedestrian conditions or a causal model.

Read alongside [attribute documentation](../../sp/ATTRIBUTE_DOCUMENTATION.md), [results](../../../analysis/results/SP/README.md), [research protocol](../../../plan.md) and [method decisions](../../sp/SP_METHOD_DECISIONS.md). These are proposed modeling defaults, not previously validated findings. Freeze them before inspecting the resulting rankings; document any later changes rather than choosing settings to obtain preferred neighbors.

## 1. Questions and final products

The model must answer:

1. What distinguishes Brás across morphology, buildings and urban functions?
2. Which districts have the smallest overall attribute distance to Brás?
3. Which families make each candidate similar or different?
4. Which findings survive alternative data assumptions, scales and weights?
5. Where is similarity driven by uncertain data or an incomplete representation of urban form?

Produce a complete 95-district ranking, a top-10 review set, family-level explanations, district profile comparisons, maps and a stability report. “Top 10” is an inspection size, not an empirically established equivalence threshold. Smaller distance means more similar under the declared model; do not report distance as a probability, quality score, causal effect or percentage of urban equivalence.

No new source acquisition is required to implement the initial model under the approved proxies. Better geolocation, source coverage and harmonization remain refinement tasks. Chicago, 250/500 m morphological grids and pedestrian outcomes are outside this SP district implementation.

## 2. Data contract and frozen inputs

Use these canonical paths, not reconstructed joins against raw data:

| Input | Use |
|---|---|
| `results/SP/tables/attributes_primary.csv` | Explicit 23-column primary candidate selection |
| `results/SP/tables/attributes_wide.parquet` | All 77 columns for controlled substitutions |
| `results/SP/tables/attributes_long.parquet` | Numerators, denominators, periods, coverage, quality and method metadata |
| `results/SP/tables/attribute_dictionary.csv` | Family membership, units and primary flags |
| `results/SP/spatial/sao_paulo_district_attributes.gpkg` | District geometry for mapping and spatial stress tests |
| `results/SP/validation/` | Existing numerical checks and outlier flags |
| `work/evidence/job_allocation_experiments/` | U2 allocation tiers and scenario diagnostics |
| `work/runs/sp_attributes_2026_09_11_v1/` | Frozen attribute provenance and optional population-support diagnostics |

At run initialization, save hashes of every consumed file, exact selected column order, source release ID, all 96 district IDs, Brás ID, configuration, package versions and code hash. Require exactly one row per district, 96 rows, 23 primary columns across 13 families, matching IDs across all inputs and finite primary values. Read IDs as strings.

Use **all 96 districts, including Brás**, to fit unsupervised transformations/scales. Every district has equal fitting weight; do not weight fitting by population or land area. This is a description of a declared finite comparison universe, not an estimate of prediction accuracy on unseen districts. Save the fitted state and reuse it for scoring; never refit separately for each candidate.

If a later release has missing primary values, stop the primary build and report affected families/districts. Do not silently median-impute or compute each pair using a different feature set. An explicitly reduced-family model may be published separately with its own configuration and renormalized weights.

## 3. Initial attribute review before fitting

Create an input-review report containing ranges, quantiles, zero frequencies, unique-value counts, coverage definitions, quality flags and the existing 38 outlier flags. Show Brás alongside the district distribution in raw units. Review flagged source records where a clear numerical problem is suspected; retain legitimate extremes. Corrections belong in a new attribute release, not an undocumented modeling patch.

Known facts from the released primary table that affect implementation:

- No primary column is constant and no primary value is missing.
- Cadastral P90 floors range from 1 to 15 but have **zero IQR**. A zero robust scale must not cause division by zero or accidental elimination of this variable.
- Highway share also has zero IQR, while VTR share has a very small IQR. Do not standardize each street share independently.
- Job density ranges approximately from 1.09 to 120,722.36 links/km²; positive densities need deliberate skew treatment.
- U2's unlocated 508,844 jobs are outside primary district totals. Its citywide allocated fraction is not district reliability.
- Six M6 shares sum to one, and family column counts vary from one to six. Treating 23 columns as 23 equally independent concepts would over-weight expanded families.
- U1 entropy describes diversity but cannot distinguish different compositions with equal diversity. Include a composition sensitivity and retain category profiles in explanations.

The review must not select transformations based on which district becomes closest to Brás. Record decisions before generating the first ranking.

## 4. Feature transformations and scaling

### 4.1 Proposed primary transformations

Natural logarithms below apply to numerical values in the fixed released units. Units are part of the configuration; changing units requires a new fitted transformation. No log is applied twice to an already logged block-area measure.

| Family | Primary column(s) | Transformation before scaling |
|---|---|---|
| M1 | `street_density_km_km2` | `ln(x)`; strictly positive in this release |
| M2 | `intersection_density_proxy_5m_km2` | `ln(x)` |
| M3 | `block_log_area_median`, `block_log_area_iqr` | Identity; these already summarize log area |
| M4 | Compactness median/IQR; elongation median/IQR | Identity for all four; preserve interpretation of shape summaries |
| M6 | Six `street_class_model_share_*` columns | Joint square-root composition; special treatment below |
| M7 | `cadastral_parcel_density_km2` | `ln(x)` |
| B1 | `building_coverage_land` | Identity on the fraction |
| B2 | `cadastral_floor_count_median`, `cadastral_floor_count_p90` | `ln(x)`; floors are positive |
| B3 | `cadastral_floor_area_density` | `ln(x)`; positive values, no arbitrary added floor-space constant |
| U1 | `land_use_entropy_count` | Identity on [0,1] |
| U2 | `formal_job_density_area_first_km2` | `ln(x)` |
| U3 | `population_density_km2` | `ln(x)` |
| U4 | `bus_service_access_weekday_am_400m` | `ln(1+x)`; defined for genuine zero service |

The log choices express relative differences for positive intensities and reduce domination by extreme magnitudes. They are modeling assumptions, not corrections to raw measurements. If an alternative scenario introduces a zero where `ln(x)` was specified, fail that scenario's transformation gate and record an explicit alternative such as `ln(1+x)` applied consistently to its whole comparison, rather than adding an undocumented epsilon to isolated records.

### 4.2 Robust scaling for noncomposition variables

For each transformed scalar feature j, fit median `m_j` and `s_j = Q75 − Q25`, then `z_dj = (t(x_dj) − m_j) / s_j`. Median/IQR scaling follows the documented [RobustScaler convention](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html); the following fallback is an explicit project addition.

If IQR is effectively zero, use the **population standard deviation (`ddof=0`)** of the transformed feature. Declare an effective-zero tolerance of `1e-12 × max(1, max absolute transformed value)`. If the fallback is also below tolerance, exclude the constant coordinate with a recorded reason and recompute the family's coordinate count. If an entire family becomes constant, stop and require a separately versioned reduced-family specification. Log every fallback, especially B2 P90. Do not winsorize by default.

Save raw units, transform, center, IQR, fallback standard deviation, selected scale, tolerance and retained status for every coordinate. A sensitivity run replaces robust scaling with mean/population-standard-deviation scaling; neither is chosen by preferred ranking.

### 4.3 M6 composition

For each district, let `p_d` be the six model-class shares. Require nonnegative finite components and sum within `1e-8` of one. Only numerical residuals within that tolerance may be renormalized, with the adjustment logged. Larger errors fail validation.

Use squared Hellinger distance:

`r_M6(d,e) = 0.5 × sum_c (sqrt(p_dc) − sqrt(p_ec))²`.

It is zero for equal compositions, bounded by one, supports genuine zero shares and does not require choosing a reference class or adding pseudo-counts. Keep all six classes in this joint calculation. Do not apply scalar z-scores to their square roots. This is the proposed project treatment of road composition; it does not validate the Local assumptions.

The observed shares sum to observed coverage, not one. In the observed-only sensitivity, first divide those shares by their positive sum and report the excluded/imputed fraction separately. Never pass the unnormalized observed vector into the primary composition function.

## 5. Primary distance: equal family weight, explicit decomposition

### 5.1 Within-family dissimilarity

For each non-M6 family f with `k_f` retained coordinates:

`r_f(d,e) = (1/k_f) × sum_{j in f} (z_dj − z_ej)²`.

M6 uses the squared Hellinger expression above. A family with four summaries therefore does not receive four times the nominal weight of a one-summary family.

Because Hellinger and standardized scalar distances have different numerical ranges, also fit a **family calibration**: `b_f` is the median of strictly positive `r_f(d,e)` among the 4,560 unordered district pairs. A positive-pair median handles ties in discrete families. Save the zero-pair fraction and b_f. Fail if no positive pair or a numerically negligible calibration exists; do not divide by an arbitrary tiny number. This calibration makes a typical nonidentical district pair comparable across families; it is a deliberate assumption to test, not a universal normalization law.

### 5.2 Overall distance

Primary family weights are `w_f = 1/13`:

`D(d,e) = sqrt(sum_f w_f × r_f(d,e) / b_f)`.

Save `contribution_f(d,e) = w_f × r_f(d,e) / b_f`. Contributions are nonnegative and sum exactly to `D²`. For a candidate, show each family's contribution and, when D>0, its share of total squared distance. Also show signed transformed differences and raw values; a distance alone does not show whether a candidate has more or less density or service than Brás.

This metric has an exact Euclidean embedding: scalar coordinates are `sqrt(w_f/(k_f b_f)) × z_dj`; M6 coordinates are `sqrt(w_M6/(2 b_M6)) × sqrt(p_dc)`. Save that embedding so Euclidean distance can independently reproduce every primary distance. Do not add family weight a second time in the distance routine.

### 5.3 Ranking and presentation

Calculate a symmetric 96×96 distance matrix. Exclude Brás only when producing its 95-candidate ranking; its own distance remains zero in the matrix. Rank ascending. Preserve exact ties using a shared competition rank (minimum rank in the tied group) and district ID as a deterministic display order. Do not fabricate distinct ranks through hidden rounding; export full precision and round only in human reports.

Publish raw distance, rank, family contributions and source-quality annotations. Do not convert distances into a “percentage similarity.” Compare top-5, top-10 and top-20 membership, and inspect distances/gaps rather than assuming an abrupt cutoff at rank 10. Geographical proximity and district area appear as context, not additional hidden similarity features.

## 6. Weighting and substantive scope alternatives

Equal family weight is the primary default. It gives 6/13 weight to M families, 3/13 to B families and 4/13 to U families. It does **not** mean equal weight to the three broad domains.

Prespecify these alternatives, recalibrating weights to sum to one:

1. **Equal domain weight:** morphology M, buildings B and urban functions U each receive 1/3, shared equally within that domain.
2. **Built-form-only:** the nine M/B families. This describes physical form without U1–U4 functions.
3. **Without U4:** 12 families, isolating the effect of bus supply; especially important before a later accessibility-outcome study.
4. **Leave-one-family-out:** all 13 omissions, with remaining weights renormalized.
5. **Family-weight perturbations:** 500 seeded scenarios; independently multiply each primary family weight by a Uniform(0.5,1.5) draw and renormalize. These are assumption perturbations, not statistical confidence intervals.

Do not make unreliable sources look reliable by silently multiplying features by coverage. Coverage definitions are heterogeneous and often citywide. Use annotations, targeted source sensitivities and explicit family exclusions instead.

## 7. Correlation, covariance and PCA comparisons

### 7.1 Redundancy review

Inspect Spearman correlations in the transformed noncomposition variables and Pearson correlations in the primary embedding. Flag absolute correlations above 0.85 as review prompts, not automatic exclusion rules. Review M1/M2, M7 with block measures, B1/B3, B2/B3, and U2/B3 in particular. Distinguish shared urban structure from shared input-data construction. Entropy and its component shares should not all enter as independent primary families.

### 7.2 Regularized Mahalanobis sensitivity

Fit a global Ledoit–Wolf covariance on the centered primary embedding. Use its stored precision matrix to calculate `D_M² = deltaᵀ precision delta`. Ledoit–Wolf shrinks covariance toward a scaled identity; the estimator and saved shrinkage/precision are described in the [official documentation](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html). Check positive definiteness, eigenvalues and condition number; fail on nonfinite or unstable results rather than silently using an unregularized inverse.

This is an **alternative metric**, not the primary equal-family metric. Covariance adjustment changes effective weighting; ordinary Mahalanobis distance can cancel invertible coordinate rescalings, while shrinkage only partly preserves their influence. Do not claim exact equal-family influence or reuse primary nonnegative contribution percentages for this metric. If explaining it, use explicitly labeled signed contributions `delta_j × (precision delta)_j`, whose sum is D_M² but whose terms can be negative.

### 7.3 PCA sensitivity and visualization

Fit centered PCA to the primary embedding with deterministic full SVD and **no whitening**. Select the smallest number of components reaching 90% explained variance; compare 80% and 95%. Save loadings, explained variance, scores and retained component count. PCA centers inputs but does not itself equalize feature scales, so use the prepared embedding. Implementation reference: [PCA documentation](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html).

Calculate distances in the retained component space and compare rankings with the primary metric. Full-rank unwhitened PCA must reproduce primary Euclidean distances within tolerance; this is a useful test. A two-component plot is visualization only; do not rank on it merely because it looks clear. Components are statistical axes, not automatically validated urban typologies.

Optional later clustering: Ward clustering on the primary Euclidean embedding for k=3…8, with dendrogram, silhouette and sensitivity review. It is secondary descriptive context, not evidence of true classes, and is not required to accept the primary ranking.

## 8. Attribute and spatial sensitivity experiments

Change one source/method assumption at a time before considering combinations. **For numerical substitutions, keep primary fitted transforms, scalar scales and family calibrations fixed** so the first comparison isolates the substitution. Where the representation changes, fit and label a separate representation. Optionally refit an entire alternative model as a second experiment, explicitly distinguishing substitution effects from scale-refitting effects.

| Experiment | Change | What it tests |
|---|---|---|
| M2 thresholds | Replace 5 m by released 0/10/20 m candidates | Dependence on the structure-exclusion proxy |
| M6 observed-only | Renormalize observed class shares where observed coverage is positive | Dependence on Local imputation; disclose selection bias of observed streets |
| B1 denominator | Replace land coverage with gross coverage | Influence of water/denominator choice |
| U1 area entropy | Replace count entropy with land-area entropy | Influence of entity vs land-area weighting |
| U1 composition | Replace entropy family by seven count shares with Hellinger treatment; separately test land-area shares | Similar diversity with different actual use composition |
| U2 alternatives | All nine nonprimary released scenarios | Geographic weighting, mixed use and residual imputation assumptions |
| U2/B3 removal | Leave out U2, B3 and both together | Shared fiscal-support dependence |
| U4 service/catchment | Other five window/radius columns | Bus-service timing and Euclidean radius assumptions |
| Scaling | Mean/SD instead of median/IQR with explicit fallback | Robustness to normalization |
| Family calibration | Remove b_f normalization as a separately labeled metric | Dependence on equal typical family-distance calibration |
| Brás fit influence | Fit scales/calibrations/covariance on the other 95, then transform Brás | Reference district's influence on normalization |
| Spatial fit influence | Omit each of 32 official subprefeitura groups from fitting, retain all 96 for scoring | Spatially clustered influence on fitted normalization |

For the spatial test, use a validated supplied district–subprefeitura crosswalk if available; otherwise mark it deferred pending that crosswalk, rather than inventing group membership. These omission experiments measure influence in the comparison universe, not out-of-sample prediction accuracy. No independent target exists for a conventional accuracy-based train/test split.

The existing 125 m U4 experiment covers only three pilots. Report it as local numerical evidence, not a citywide ranking-stability result. Extending it to all 96 requires a separate attribute-support run. Similarly, the U4 population grid is not a constructed 250/500 m morphology grid. MAUP/grid robustness remains later attribute work.

For each comparison, export rank shifts, Spearman rank correlation, top-k overlap/Jaccard for k=5/10/20, absolute distance changes only for commensurable metrics, and the exact scenario specification. Tied distances at a top-k cutoff must be flagged; report the tie-expanded set as well as deterministic fixed-k display membership.

Do not merge all experiments into one apparent probability. Report separately: source-scenario ranges, distance-method disagreement, family-weight perturbation frequencies and fit-cohort influence. The scenario set is designed, not randomly sampled from a known uncertainty distribution. A proposed “weight-stable top-10” label requires membership in at least 80% of the 500 weight perturbations; label this a project threshold, and show the frequency itself. Source disagreement must remain visible even for weight-stable candidates.

## 9. Implementation stages and acceptance

All stages below are **planned, not executed**. Use explicit checkpoints and record problems, fixes and decisions as work proceeds.

| Task | Implementation | Deliverable / acceptance |
|---|---|---|
| N11.01 — Freeze inputs | Loader, hash manifest, feature registry and model configuration | 96 unique IDs; 23 primary columns; Brás found; all 13 families; source versions recorded |
| N11.02 — Review attributes | Distribution, quality, zero-IQR and correlation review; raw Brás profiles | Review report; outlier decisions recorded; no unexplained deletions |
| N11.03 — Transform | Explicit transform registry, finite/domain checks, robust scaling and fallback | Fitted JSON state plus transformed table; B2 P90 fallback tested |
| N11.04 — Build families | M6 composition function, within-family distances, calibration and weights | 13 family distance matrices, calibration table and embedding |
| N11.05 — Score | Full pairwise distances, Brás ranking and contribution decomposition | 96×96 matrix; 95 candidates; contributions reconcile with squared distances |
| N11.06 — Explain | Raw/transformed profiles, family bars and district maps | Brás profile, candidate comparison table, top-10 review report; no causal claims |
| N11.07 — Compare metrics | Regularized covariance, PCA and correlation review | Stored estimators, diagnostics and separate alternative rankings |
| N11.08 — Test robustness | Source substitutions, weighting, family omissions and fit-cohort influence | Scenario registry, ranks, top-k overlap, weight frequencies and explicit deferred tests |
| N11.09 — Review candidates | Inspect top-10 plus candidates appearing in any core sensitivity top-10 | Candidate notes on similarities, disagreements and source limitations; no weight tuning to preference |
| N11.10 — Release | Independent validation, export and handoff updates | Versioned result package, report, README, input/code/output hashes and completed task ledger |

Dependency order: 01 → 02 → 03 → 04 → 05; 06/07 follow 05; 08 requires the primary fitted state and specified alternatives; 09 uses explanations and robustness results; 10 follows successful checks. Failed stages record their error and do not mark the model complete.

## 10. Proposed code and folder architecture

Keep attribute outputs untouched. New paths below are proposed and must be created during implementation, not treated as existing artifacts:

```text
analysis/
  config/sp_urban_model_v1.json
  scripts/model_sp_urban_similarity.py
  scripts/sp_model/
    inputs.py          # schema, feature selection, quality metadata
    transforms.py      # fitted scalar transforms and composition checks
    distances.py       # family distances, calibration, embedding, scoring
    sensitivity.py     # named scenarios and fitted-state policy
    reporting.py       # comparisons, figures and readable report
  tests/test_sp_model.py
  work/runs/sp_urban_model_v1/
    metadata/          # input/config/code hashes, environment, fitted state
    intermediates/     # transformed values, embedding, family matrices
    scenarios/         # per-scenario configs, matrices and rankings
    logs/              # execution log and progress/checkpoints
  results/SP/models/sp_urban_model_v1/
    tables/            # Brás rankings, explanations, stability, pairwise distances
    spatial/           # district geometry plus rank/distance/quality annotations
    figures/           # maps, profiles, family contributions, sensitivity plots
    reports/           # final report and executed-task ledger
    validation/        # tests and independent checks
    README.md
```

Configuration must explicitly contain source release and paths; selected feature names and family membership; transformations/fallback tolerance; fitting cohort; family calibration rule; weights; composition rule; Brás ID; metric variants; scenario substitutions and whether scales are frozen/refit; random seed `20260911`; 500 weight draws; tie policy; and publication thresholds. Store actual selected versions of NumPy/pandas/scikit-learn/GeoPandas rather than depending on whichever latest package happens to be installed. Plain JSON plus arrays/tables should expose fitted parameters without requiring opaque pickle files.

Suggested CLI stages: `review`, `fit`, `score`, `sensitivity`, `report`, `validate`, `all`. Every checkpoint signature includes inputs, configuration, code and relevant fitted-state hashes. A changed method requires a new run ID. An interrupted run may reuse only hash-matching checkpoints. Exports must link from the new model README; do not reuse the compatibility output tree for new work.

## 11. Required tests and validation

Use mathematical fixtures and independent reconstruction, not tests that repeat the implementation line for line:

- Identical feature vectors give distance zero; changing one scalar increases only that family's primary contribution.
- M6 equal compositions give zero, disjoint one-class compositions give squared Hellinger distance one, and genuine zeros remain finite.
- All primary distance matrices are symmetric, finite, nonnegative and have zero diagonals. Check triangle inequalities within numerical tolerance on deterministic sampled triples.
- Embedding Euclidean distances equal the directly assembled family distances; family contributions sum to D².
- Duplicating the whole coordinate set within one numeric family does not change its mean squared dissimilarity. Duplicate input feature names are rejected.
- Zero-IQR but nonconstant data trigger SD fallback; a constant coordinate is reported; invalid log inputs fail clearly.
- Row permutation and serialization/reload do not change results after reindexing. Brás is excluded from its candidate list but retained in fit-universe metadata.
- Fixed-state substitution cannot overwrite primary fitted parameters. Scenario metadata identifies every changed column and source.
- Full-rank unwhitened PCA reproduces primary distances; regularized covariance yields finite, nonnegative quadratic forms within tolerance.
- Tie handling and top-k cutoff annotations are deterministic. Seeded weight scenarios reproduce exactly within declared floating-point tolerance.
- Reopened CSV/Parquet/GPKG outputs agree on district IDs and values; exported geometry is valid EPSG:31983.
- Input attribute hashes are unchanged after model execution. No pedestrian outcome, district name encoding, ID or geographic coordinate enters the similarity feature vector.

No “95% accuracy” target is appropriate without independently labeled analogues. Acceptance means correct implementation, transparent assumptions, readable explanations and honest stability reporting. If rankings are unstable, publish that finding rather than forcing a stable shortlist.

## 12. Final report and continuation

The report must describe the question, comparison universe, source periods, exact 23-column selection, transformation/fallback decisions, family weights/calibration, primary ranking, contribution explanations, alternative metrics, source/weight sensitivity and deferred work. Include Brás's raw profile and side-by-side candidate profiles so readers can verify what “similar” means. Maps should show both distances and data limitations; proximity on a map is not validation of morphological similarity.

Maintain a task ledger with status, code version, inputs, outputs, checks, issues, causes and resolutions. The next agent should be able to resume from one run README and `progress.json`. Update the project handoff only after the corresponding stage actually runs; this plan does not authorize claiming completed modeling or rankings.

**Next executable step: N11.01–N11.02, freeze model inputs and complete the attribute-review report.** Then implement the prespecified primary metric before running alternatives. Future Chicago harmonization requires common entity definitions, time/coverage comparisons and a new declared fitting universe; later pedestrian-outcome analysis needs its own design and spatial validation.
