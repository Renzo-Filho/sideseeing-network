# SP model corrections and revalidation — 15 September 2026

**The reported implementation defects have been fixed.** The corrected release is [sp_urban_model_v2](results/SP/models/sp_urban_model_v2/README.md). It preserves the original v1 primary ranking while adding input contracts, reusable fitted state, provenance and the missing sensitivity experiments. The original v1 outputs remain unchanged.

## Corrections completed

| Review issue | Implemented correction | Verification |
|---|---|---|
| Incorrect PCA loading labels | Labels now follow `E_df.columns`; notebook and export share model functions | All 23 labels agree with the fitted matrix; previously 15 were mislabeled |
| CLI import failure | Replaced `pkg_resources` with standard-library package metadata; pinned model/notebook dependencies | CLI runs successfully and verifies an existing completed run |
| Invalid scalar/composition input | Finite/domain checks; strict absolute 1e-8 share-sum tolerance; logged numerical normalization; explicit zero-IQR fallback | Invalid log values, infinities, negative/nonunit shares rejected; B2 fallback preserved |
| Row and weight handling | Exact unique scalar/composition index agreement; distinct features; nonnegative finite weights normalized by their sum | Misaligned rows/invalid weights rejected; permutation and common-weight rescaling invariance pass |
| Incomplete source contract | Exact 01–96 IDs and 23-column/13-family dictionary match; primary/wide/long/GPKG values agree | Valid input contract passes; duplicate selection, wrong IDs and infinite inputs fail |
| Unsaved fit state/provenance | Manifest, environment/code/input hashes, scalar fit/apply state, calibrations, embedding, family distances/contributions and output inventory | Serialization reproduces coordinates; completed run verifies hashes; changed configuration is refused under the same run ID |
| Missing source/weight sensitivities | Executed named source substitutions with frozen primary scales, representation changes, exclusions, alternate weights, PCA/covariance, and fit-cohort experiments | All 577 scenarios completed without failed scenarios |
| Misleading interpretation | Corrected PCA/cluster descriptions and labeled the radar as a selected raw-variable z-score profile | Notebook no longer labels variance loadings as predictive importance or Ward clusters as independent validation |

The notebook's stale rendered outputs were cleared after the code edits. Both its code cells and Python export have been executed from clean headless namespaces by the audit; user code and resulting numerical objects agree. Interactive browser rendering is separate from that computational check. Open the notebook and Run All for refreshed interactive output; static plots are already published in the v2 release.

## Results

- **30 automated tests pass**: 19 existing preparation/attribute tests and 11 model regression/contract tests.
- **26 independent audit checks pass; zero fail.** This includes all 884,736 triangle-inequality comparisons, independent embedding reconstruction and comparison against both saved releases.
- All 95 Brás ranks and original primary distances remain unchanged within floating-point tolerance (approximately 1.8×10⁻¹⁵ maximum discrepancy).
- Primary top three remain **Belém, Bom Retiro and Cambuci**.
- Full unwhitened PCA preserves primary distances. Loadings are now correctly labeled; five components reach 90% explained variance.
- The reopened district GeoPackage contains 96 valid geometries in EPSG:31983, with distances matching the tabular results.
- Original source hashes are unchanged. Changed-signature overwrite rejection was exercised against the completed v2 run, and a repeated identical invocation verified existing artifacts rather than recomputing them.

## Executed robustness work

| Scenario group | Runs |
|---|---:|
| Source/catchment substitutions | 20 |
| U1 composition representations | 2 |
| Family exclusions, including built-form-only and joint U2/B3 removal | 15 |
| Equal-domain weights | 1 |
| Standard scaling | 1 |
| No family calibration | 1 |
| Fit excluding Brás | 1 |
| Fit excluding each supplied subprefeitura group | 32 |
| Seeded family-weight perturbations | 500 |
| PCA 80/90/95% and Ledoit–Wolf Mahalanobis | 4 |
| **Total** | **577** |

M2 0/10/20 m variants and every U2 allocation alternative retain the primary top 10, although individual ranks/distances can shift. Observed-only M6 and gross-area B1 also retain those ten. Land-area U1 entropy retains eight, and two U4 variants retain nine. These are sensitivity findings, not validation of the underlying employment allocations or road classes.

Nine districts are in the top 10 in at least 80% of the 500 weight perturbations: Belém, Bom Retiro, Cambuci, Pinheiros, Mooca, Tatuapé, Liberdade, Lapa and Vila Mariana. The threshold is prespecified and the frequency is conditional on this designed weight range; it is not a statistical probability of true urban equivalence. See [all scenario comparisons](results/SP/models/sp_urban_model_v2/tables/scenario_summary.csv) and [weight frequencies](results/SP/models/sp_urban_model_v2/tables/weight_stability.csv).

## Remaining scientific limits

The corrected SP model is ready to serve as the **reference implementation for harmonization planning**. It does not establish that a Chicago feature with the same name is comparable. Source dates, cadastral entities, class definitions, population/job coverage and geographic support still require harmonization. The 508,844 unlocated SP jobs remain outside primary totals. Full-city 125 m U4 support and 250/500 m morphology grids are explicitly deferred source work; the completed subprefeitura influence tests do not substitute for MAUP analysis.

## Files and reproduction

- [Model report](results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md), [ranking](results/SP/models/sp_urban_model_v2/tables/bras_ranking.csv), [correct PCA loadings](results/SP/models/sp_urban_model_v2/tables/pca_loadings.csv).
- [Configuration](config/sp_urban_model_v2.json), [CLI](scripts/model_sp_urban_similarity.py), [model tests](tests/test_sp_model.py), [independent audit](scripts/validate_sp_urban_model.py).
- Local audit: `work/reviews/sp_model_validation_2026_09_15_v2/audit.json`; original failed audit remains under the original dated directory.
- Full fitted states, source/code/output hashes and scenario configurations: `work/runs/sp_urban_model_v2/` (local working data).

```bash
.venv/bin/python -m unittest discover -s analysis/tests -p 'test_sp*.py' -v
.venv/bin/python analysis/scripts/model_sp_urban_similarity.py
.venv/bin/python analysis/scripts/validate_sp_urban_model.py
```

A completed identical model run is verified and reused. To change inputs, configuration, environment or executable model code, create a new run ID/configuration. `--output-root` isolates a verification build without overwriting the published paths. Failed matching-signature runs can be recomputed; they are never presented as completed releases.
