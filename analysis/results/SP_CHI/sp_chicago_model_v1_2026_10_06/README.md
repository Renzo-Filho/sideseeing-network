# São Paulo–Chicago model v1: fit outputs (6 October 2026)

Produced by executing [`analysis/sp_chicago_model_analysis.ipynb`](../../../sp_chicago_model_analysis.ipynb) with [`sp_chicago_model.py`](../../../scripts/sp_chicago_model.py), under the contract [`sp_chicago_model_v1.json`](../../../config/sp_chicago_model_v1.json). 173 units; reference Brás (SP:10). Methodology and reading: [docs/harmonization/MODEL_REPORT.md](../../../../docs/harmonization/MODEL_REPORT.md).

## `tables/`

| File | Content |
|---|---|
| `distance_{hybrid,all_absolute,all_relative}_{R1,R2,R3}.csv` | 173 × 173 dissimilarity matrices for every scaling × run |
| `ranking_bras_{scaling}_{run}.csv` | Every unit ranked by distance to Brás, overall and within its city |
| `bras_top5_chicago_all_runs.csv` | Brás's five closest Chicago areas in all nine runs |
| `scale_comparison.csv` | Agreement of each scaling × run with hybrid R1, and how much each mixes the two cities |
| `neighbours_hybrid_R1.csv` | Five nearest neighbours of every unit |
| `city_levels.csv`, `scaling_hybrid.csv` | City medians, C6 level per column, capped units |
| `family_contribution_shares_hybrid_R1.csv` | Each family's share of D² over all pairs |
| `worked_example_bras_vs_top_chicago.csv` | Brás vs West Town, family by family |
| `pca_variance.csv`, `pca_loadings.csv` | Explained variance; correlations of components with model columns |
| `r3_pruning_log_{scaling}.csv` | Columns dropped in R3 |
| `stability_hybrid_R1_weight_draws.csv`, `stability_bras_top5_chicago.csv` | 500 weight draws |
| `sensitivities_hybrid.csv` | Pre-registered alternatives (and one post hoc) vs hybrid R1 |
| `ward_clusters.csv` | Ward clusters (k = 4) |

## `figures/`

`city_levels_boxplots`, `family_contribution_shares`, `contributions_top10_all`, `contributions_top10_chicago`, `maps_distance_to_bras`, `radar_bras_vs_top_chicago`, `pca_cumulative_variance`, `pca_scatter`, `scale_city_mixing`, `stability_histogram`, `ward_dendrogram`, `pca_clusters`, `maps_clusters`.
