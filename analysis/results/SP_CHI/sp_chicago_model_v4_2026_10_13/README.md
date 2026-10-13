# São Paulo–Chicago model v4: proposed Brás-focused settings (13 October 2026)

Produced by [`analysis/scripts/sp_chicago_model_settings.py v4`](../../../scripts/sp_chicago_model_settings.py) under the contract [`sp_chicago_model_v4.json`](../../../config/sp_chicago_model_v4.json).
- **Status:** proposed for exploration, not final. It is the explorer's starting settings.
- **Data:** v2's inputs (173 units, 21 columns); reference Brás (SP:10).
- **Settings:** all-relative scaling, full distance.
- **Family weights:** U1 and U6 0.25 each, B1 0.20, U4 0.10, M4 and M6 0.05 each, U2 0.04, BV 0.03, M1 0.02, U3 0.01. M3 and M7 are off.
- **Weights inside families:** U1 commerce 3, residential 2, industrial 1, institutional 0; M4 compactness 2, elongation 1.
- **Methodology and reading:** [docs/harmonization/MODEL_REPORT.md §13](../../../../docs/harmonization/MODEL_REPORT.md#13-version-4-proposed-brás-focused-settings-13-october-2026).

**Result.** Brás's closest Chicago group is Near West Side, Near North Side, Lower West Side, West Town and Avondale (shares of 500 weight draws in the top five: 94.2%, 82.2%, 77.8%, 94.6%, 81.2%). First place is not firm. None is a close match: Brás's best Chicago distance is farther than the best cross-city match of 98.3% of units (`run.json`, `match_strength`).

## `tables/`

| File | Content |
|---|---|
| `distance_v4.csv` | 173 × 173 dissimilarity matrix. The explorer is checked against it |
| `ranking_bras_v4.csv` | Every unit ranked by distance to Brás, overall and within its city |
| `neighbours_v4.csv` | Five nearest neighbours of every unit |
| `family_contribution_shares_v4.csv` | Each family's weight and its share of D² over all pairs |
| `worked_example_bras_vs_top_chicago_v4.csv` | Brás vs its ten closest Chicago areas: each family's share of D² |
| `stability_bras_top5_chicago_v4.csv`, `stability_v4_weight_draws.csv` | 500 draws of the family weights (×U(0.5, 1.5), seed 20261006; inner weights fixed) |
| `comparison_v4.csv` | Named alternatives (v2, v3, equal inner weights, hybrid scaling, PCA distance, single weight changes) compared with v4 |
| `active_correlations_v4.csv` | Cross-family column pairs among the active columns with \|Spearman\| ≥ 0.6, under all-relative scaling |
| `bras_profile_sao_paulo_v4.csv` | Brás's value, rank within São Paulo and within-city z on every column: the evidence the weights cite |

`run.json` holds the settings, the normalized budgets, Brás's Chicago top five, the match strength and the stability summary.
