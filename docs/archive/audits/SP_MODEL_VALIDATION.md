# São Paulo urban model — independent validation

> **Revalidation update:** the issues below were corrected in `sp_urban_model_v2`. All 26 independent audit checks and 30 automated tests now pass; 577 sensitivity scenarios completed. See [corrections and results](../../sp/SP_MODEL_FIXES.md) and the [Chicago harmonization plan](../../chicago/CHICAGO_HARMONIZATION_PLAN.md). The original findings below remain as the historical audit record.

Reviewed **15 September 2026** against `URBAN_MODEL_IMPLEMENTATION_PLAN.md` and the released attributes. Reviewed both `model_analysis.ipynb` and the currently edited `model_analysis.py`, the CLI and `sp_model` modules, configuration, fitted parameters and saved rankings.

## Original review decision (superseded by v2)

**The primary equal-family SP distances and saved rankings are numerically correct for the current inputs and all-one family weights. The pipeline is not yet ready for full methodological acceptance or transfer to Chicago.** PCA loading interpretations have a real labeling error; the CLI currently fails to import; defensive checks and the planned reproducibility/robustness stages are incomplete.

These findings do not invalidate the reproduced baseline ranking. They distinguish a correct primary calculation from a validated, reusable research pipeline. No user implementation, notebook, published model table or attribute input was changed by this review. Corrected loading labels are supplied as separate review evidence, not silently applied to the notebook.

## 1. What was independently checked

The audit independently uses NumPy quantiles, broadcast pair differences and an explicit 23-coordinate Euclidean embedding to reconstruct every family calibration and all 9,216 ordered pair distances. It does not derive the reference answer from the production distance function.

- Primary scalar/log transforms and median/IQR scaling match. B2 P90 correctly falls back to population SD: log-scale median 0.6931471806, IQR zero, scale 0.5517240608.
- Primary CSV values match the full and long attribute tables; saved scalar fitted parameters match the independent fit.
- M6 squared Hellinger distance, positive-pair median calibration and equal-family aggregation match the declared baseline.
- Saved pairwise distances and all 95 Brás ranks reproduce. Maximum absolute distance discrepancy is approximately **1.78×10⁻¹⁵**.
- Matrices are finite, nonnegative and symmetric with zero diagonals; all 96³ triangle-inequality comparisons pass. Contributions reconcile to squared total distances.
- Consistently permuting district rows preserves the result.
- Both the notebook's code cells and its Python export execute from clean namespaces in a headless environment; numerical results agree. Matplotlib display magic and rich display were replaced with no-op display adapters, with figures closed rather than shown. This verifies computation and plotting-code execution, not interactive browser rendering or remote basemap availability.
- Full unwhitened PCA preserves the primary distances. Five PCs reach the specified 90% variance threshold; PC1+PC2 explain **83.34435%**. The Ward code runs and selects k=3 among the tested k=3…8.
- Existing 19 synthetic tests pass, but those tests cover source preparation/attribute construction and allocations; they do not establish model robustness.

### Reproduced primary top 10

| Rank | District | ID | Distance |
|---|---|---|---|
| 1 | BELEM | 08 | 0.537614 |
| 2 | BOM RETIRO | 09 | 0.627889 |
| 3 | CAMBUCI | 14 | 0.681758 |
| 4 | PINHEIROS | 62 | 0.764482 |
| 5 | MOOCA | 53 | 0.832456 |
| 6 | TATUAPE | 80 | 0.846557 |
| 7 | LIBERDADE | 49 | 0.868025 |
| 8 | LAPA | 48 | 0.891913 |
| 9 | VILA MARIANA | 90 | 0.925813 |
| 10 | SANTA CECILIA | 69 | 0.953658 |

This verifies arithmetic for the chosen assumptions, not that these are objectively interchangeable neighborhoods or that their order is stable under all plausible source choices.

## 2. Findings that need correction

### F1 — High: 15 of 23 PCA loading labels are assigned to the wrong variables

**Location:** `model_analysis.py:363–367`, corresponding notebook cell 13.

`E_df` is assembled in configuration family order, placing M6 before M7. `t_df` is built from all scalar columns first and M6 last. SVD is fitted to `E_df.values`, but the loading table is indexed by `t_df.columns`. Therefore 15 loadings are attached to the wrong attribute names.

**Impact:** PC1/PC2 driver tables and axis interpretations can be wrong. The fitted embedding, eigenvalues, PCA scores, distance calculations and Ward clusters remain numerically unaffected by this labeling mistake.

**Correction:** label loading rows with `E_df.columns`, and assert their exact order matches the matrix supplied to SVD. Do this in the notebook and export, or replace duplicated calculations with one shared implementation. Rerun the downstream loading descriptions.

Correct PC1 largest absolute coefficients include street density −0.427589, cadastral parcel density −0.402294, population density −0.390905, intersection density −0.385484 and floor-area density −0.363223. Correct PC2 largest absolute coefficients include land-use entropy −0.547550, floor P90 −0.362690 and formal-job density −0.322692. PCA signs may flip under an equivalent decomposition; feature labels must not.

Evidence: [label-by-position audit](../../../analysis/work/reviews/sp_model_validation_2026_09_15/pca_loading_label_audit.csv) and [correctly labeled loadings](../../../analysis/work/reviews/sp_model_validation_2026_09_15/corrected_pca_loadings.csv).

### F2 — High: the CLI fails in the current project environment

**Location:** `scripts/sp_model/inputs.py:6,66`; imported by the CLI at `scripts/model_sp_urban_similarity.py:5`.

Importing the entry point with `.venv/bin/python` raises `ModuleNotFoundError: No module named 'pkg_resources'`. The notebook bypasses that loader and therefore succeeds independently; its execution does not validate the command-line path.

**Correction:** use standard-library `importlib.metadata.version` for package metadata instead of `pkg_resources`. Capture required package versions, and add the notebook/model dependencies to the analysis environment specification. The requirements currently omit scipy, scikit-learn, seaborn and mapping/notebook extras used by this workflow. Then run the CLI into an isolated validation run directory, not over the currently published result.

The Python export also assumes an IPython context and an `analysis/` working directory. Keep it explicitly a notebook export, or add a real script entry point; do not describe it as a standalone root-directory CLI.

### F3 — Medium: invalid scalar inputs and malformed compositions are not reliably rejected

**Locations:** `scripts/sp_model/inputs.py:56–58`; `scripts/sp_model/transforms.py:18–26,67–72`; duplicated notebook transforms.

The loader checks nulls rather than all finite numbers. Direct probes show zero passed to `log`, and infinite scalar input, can produce invalid coordinates without an exception. In the composition check, `np.allclose(..., atol=1e-8)` retains its default relative tolerance; a row summing to 1.000001 is accepted despite exceeding the declared absolute 1e-8 tolerance. The notebook normalizes without this sum check at all.

**Correction:** explicitly validate finite inputs and transform domains; use finite-output checks after each transformation and scaling step. Require finite, nonnegative shares and `rtol=0, atol=1e-8` before permitted numerical renormalization. Record adjustments. Add tests for zero/negative log inputs, infinity, nulls, nonunit and all-zero compositions.

These probes expose reuse hazards; they do not imply that the current valid released inputs contain these defects.

### F4 — Medium: positional joins and weight handling are unsafe for alternate runs

**Location:** `scripts/sp_model/distances.py:8–24,44–47`, and notebook weight expressions.

The function treats scalar and composition rows positionally without checking their district indexes. Reversing only the composition table is silently accepted and combines measurements from different districts. Validate identical unique indexes or explicitly align by ID before conversion to arrays.

Weights are divided by the hard-coded value 13 rather than their sum. All-one baseline weights are correct, but multiplying every weight by two increases every distance by √2 even though relative weights are unchanged. Negative weights are also accepted. Require finite nonnegative weights, positive total mass, and divide by their actual sum. Distinguish deliberate zero-weight exclusions from accidental empty families.

A common positive multiplier alone does not change a within-run ranking, but it invalidates normalization and cross-scenario distance comparisons. Removing a family or using arbitrary perturbations needs the same general normalization rule. Fix and test this before the planned sensitivities or cross-city feature subsets.

### F5 — High for release acceptance: provenance and fitted state are incomplete

**Location:** `scripts/model_sp_urban_similarity.py:14,22–29,54–58`; `scripts/sp_model/inputs.py`.

`freeze_inputs` computes a manifest, but the runner never saves it. Family calibrations, contributions, exact embedding, complete environment, code hashes and selected ID/column order are not persisted. Repeated runs write the same v1 paths without a signature or overwrite guard. The loader checks file existence and counts but not exact cross-file district identity, distinct selected columns, dictionary-family consistency or approved feature membership.

**Correction:** persist a model-specific manifest and fitted state; validate exact IDs/column mappings; implement a separate transform-with-saved-parameters API; add a run/config argument and refuse to overwrite an existing run with changed inputs/config/code. Persist contributions, embedding and validation results alongside the rankings. Preserve the existing result as the baseline snapshot.

The independent audit records hashes for this review, but that does not retroactively create a manifest for the original model execution.

### F6 — High for scientific acceptance: robustness stages are configured or planned but not executed

**Location:** CLI has no scenario/alternative-metric loop; config lines 15,41–45; notebook ends with PCA and Ward.

No executable/saved evidence was found for the 500 weight perturbations, leave-one-family-out, equal-domain weights, built-form-only/no-U4 comparisons, U2 alternatives, M6 observed-only, or M2 threshold scenarios. Regularized Mahalanobis appears in the configuration but is not implemented. The notebook's PCA and Ward comparisons do not replace source or weighting sensitivity.

The three configured M2 alternatives also set `refit_scales: true`, contrary to the plan's first fixed-state substitution experiment. They are currently unused, so this has not changed the published baseline. Implement a frozen-transform/calibration comparison first; label full refits as a separate experiment.

**Correction:** complete and save the prespecified core source and weighting experiments, including top-k overlap and rank shifts, with fixed/refitted state distinguished. Compare covariance/PCA variants or explicitly revise the scope and explain any deferrals. Report instability rather than selecting favorable settings.

## 3. Interpretation and presentation corrections

- The model uses 13 **families** represented by a 23-coordinate embedding, not a 13-dimensional feature space.
- “PCA-weighted instead of equal-family weights” is misleading: PCA here starts from the already equal-family-weighted embedding. Truncation removes directions; it does not remove the original weighting assumptions. Full-rank unwhitened PCA recovers the original distances.
- PCA loadings describe directions of variation, not predictive feature importance or causal drivers. Correct the labeling error before interpreting those axes.
- Ward clustering on the same embedding is descriptive consistency evidence, not independent validation of urban typologies. k=3 maximizes the tested silhouette values; it is not proven to be the city's true number of urban classes.
- The radar uses mean/SD standardization of raw variables, while distances use log/robust transformations and family calibration. It also omits M6 and several distribution summaries. Relabel it as a selected raw-variable profile or plot the actual fitted coordinates. Its current Brás/Belém values do fit inside the selected display limits; no clipping defect was observed for this pair.
- The notebook sorts tied distances without the plan's explicit district-ID secondary key, while the CLI implements that key. Add consistent tie ordering and cutoff annotations before claiming deterministic scenario top-k membership.

## 4. Required completion order before Chicago harmonization

1. Fix PCA labels and descriptions; remove the broken CLI dependency; add explicit scalar/composition/ID/weight validation.
2. Centralize notebook calculations on the tested modules and add model-specific regression tests, including independent embedding reconstruction and all probes above.
3. Save immutable input/config/code lineage, calibrations, embedding, contributions and fitted transform state. Re-execute notebook and CLI against the same frozen inputs in an isolated new run and compare every output.
4. Execute core source/weight/family sensitivities; separate PCA/covariance metric comparisons and document any deferred spatial tests. Do not assert rank stability from clustering alone.
5. Publish a completed SP model report and sign-off that distinguishes arithmetic validation, robustness and source uncertainty.

**Chicago decision:** do not yet mark the SP model as validated for harmonization. A Chicago implementation plan should follow these corrections and sensitivity results, which may change the feature subset or metric we need to harmonize. Existing exploratory Chicago files were not executed or changed by this audit.

## 5. Reproduction and evidence

Run from the repository root:

```bash
.venv/bin/python analysis/scripts/validate_sp_urban_model.py
.venv/bin/python -m unittest discover -s analysis/tests -p 'test_sp*.py' -v
```

The audit writes only `analysis/work/reviews/sp_model_validation_2026_09_15/`. It runs the user analysis code in clean headless namespaces, verifies input/output preservation and records failures without changing the user implementation. Its successful process exit means **audit execution completed**, not that all model checks passed. Read the `failed` count and findings.

The targeted audit records **17 passing checks and 8 failing checks**. The separate 19 existing tests pass.

| Check | Outcome |
|---|---|
| Independent primary metric matches pipeline | PASS |
| Primary values match wide and long source tables | PASS |
| Saved scalar fitted parameters match independent fit | PASS |
| All family calibrations independently reproduced | PASS |
| Contributions sum to squared distances | PASS |
| Finite symmetric nonnegative zero-diagonal distances | PASS |
| All 884736 triangle inequalities | PASS |
| Saved pairwise matrix matches recomputation | PASS |
| Saved 95-row ranking matches independently | PASS |
| CLI imports in current environment | FAIL |
| Reject log zero before producing invalid coordinates | FAIL |
| Reject infinite scalar input | FAIL |
| Reject composition sum error 1e-6 above declared tolerance | FAIL |
| Equivalent relative weights preserve distance | FAIL |
| Reject negative family weight | FAIL |
| Reject mismatched scalar/composition ID order | FAIL |
| Consistent row permutation preserves result | PASS |
| model_analysis_py clean headless execution | PASS |
| model_analysis_notebook clean headless execution | PASS |
| Notebook and exported script numeric results match | PASS |
| PCA loadings assigned to fitted feature order | FAIL |
| Notebook primary distance matches independent metric | PASS |
| Full unwhitened PCA preserves primary distances | PASS |
| Displayed radar range contains plotted values | PASS |
| Reviewed code and published inputs/outputs unchanged | PASS |

[Machine-readable audit and reviewed hashes](../../../analysis/work/reviews/sp_model_validation_2026_09_15/audit.json), [CLI import traceback](../../../analysis/work/reviews/sp_model_validation_2026_09_15/cli_import.log), and [independent ranking](../../../analysis/work/reviews/sp_model_validation_2026_09_15/independent_bras_ranking.csv). The working evidence is intentionally local/ignored; this report and audit code preserve the findings for continuation.
