# São Paulo–Chicago model v3: final settings (13 October 2026)

Produced by [`analysis/scripts/sp_chicago_model_settings.py v3`](../../../scripts/sp_chicago_model_settings.py) under the contract [`sp_chicago_model_v3.json`](../../../config/sp_chicago_model_v3.json).
- Data: 173 units and 21 columns, the same inputs as [v2](../sp_chicago_model_v2_2026_10_08/README.md); reference Brás (SP:10).
- Settings: all-relative scaling and the full distance.
- Family weights: U1 0.25, U6 0.20, BV, M1 and B1 0.10 each, U2, U3, U4, M6 and M4 0.05 each. M3 and M7 are off.
- Methodology and reading: [docs/harmonization/MODEL_REPORT.md §12](../../../../docs/harmonization/MODEL_REPORT.md#12-version-3-final-settings-13-october-2026).

Brás's Chicago top five are Lower West Side, Avondale, West Town and McKinley Park, each in 100% of 500 weight draws, then Logan Square (50.2%, not firm).

## `tables/`

| File | Content |
|---|---|
| `distance_v3.csv` | 173 × 173 dissimilarity matrix. The explorer and the Curio dataflow are checked against it |
| `ranking_bras_v3.csv` | Every unit ranked by distance to Brás, overall and within its city |
| `neighbours_v3.csv` | Five nearest neighbours of every unit |
| `family_contribution_shares_v3.csv` | Each family's weight and its share of D² over all pairs |
| `worked_example_bras_vs_top_chicago_v3.csv` | Brás vs its ten closest Chicago areas: each family's share of D² |
| `stability_bras_top5_chicago_v3.csv`, `stability_v3_weight_draws.csv` | 500 weight draws around the v3 weights (×U(0.5, 1.5), seed 20261006) |
| `comparison_v3.csv` | Named alternatives (v2 published, other scalings, PCA distance, small weight changes) compared with v3 |
| `active_correlations_v3.csv` | Cross-family column pairs among the active families with \|Spearman\| ≥ 0.6, under all-relative scaling |

`run.json` holds the settings, the normalized budgets, Brás's Chicago top five and the stability summary.
