# Chicago model v1: fit outputs (6 October 2026)

Produced by executing [`analysis/chicago_model_analysis.ipynb`](../../../chicago_model_analysis.ipynb) with [`analysis/scripts/chicago_model.py`](../../../scripts/chicago_model.py), under the frozen contract [`chicago_model_v1.json`](../../../config/chicago_model_v1.json). Methodology and reading: [MODEL_REPORT.md](../../../../docs/chicago/MODEL_REPORT.md).

## `tables/`

| File | Content |
|---|---|
| `distance_R1.csv`, `distance_R2.csv`, `distance_R3.csv` | 77 × 77 dissimilarity matrices: equal weights, PCA weights (4 components, 91.0%), without correlated features |
| `neighbours_R1.csv`, `neighbours_R2.csv`, `neighbours_R3.csv` | Each area's five nearest areas, with distance |
| `j3_u1_admission.csv` | J-3 U1 land-share admission (Chicago and São Paulo) |
| `spearman_scalar_columns.csv` | Spearman matrix of the scalar columns (J-4, R3) |
| `scaling.csv` | Transform, mean, SD, median, IQR and capped areas per column |
| `family_contribution_shares_R1.csv` | Each family's share of D² over all pairs |
| `worked_example_reference_vs_top_match.csv` | Loop vs Near North Side, family by family |
| `pca_variance.csv`, `pca_loadings.csv` | Explained variance; correlations of components with model columns |
| `r3_pruning_log.csv` | Columns dropped in R3 and why |
| `run_comparison.csv` | Agreement between R1, R2 and R3 |
| `stability_R1_weight_draws.csv` | Share of 500 weight draws in which each top-five neighbour persists |
| `sensitivities.csv` | J-9 scenarios (and one labelled post hoc) vs R1 |
| `ward_clusters.csv` | Ward clusters (k = 4) |

## `figures/`

`spearman_heatmap`, `family_contribution_shares`, `contributions_top10_R1`, `map_distance_R1`, `radar_R1`, `pca_cumulative_variance`, `pca_scatter`, `stability_histogram`, `ward_dendrogram`, `pca_clusters`, `map_clusters`.
