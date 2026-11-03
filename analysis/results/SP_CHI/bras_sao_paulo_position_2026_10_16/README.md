# Brás's position within São Paulo (16 October 2026)

Script: `analysis/scripts/bras_sao_paulo_position.py` (a few seconds). Inputs: the cross-city model's 21 columns (`sp_chicago_model.load_inputs`, the same data in v2–v4) and the U6 shares in `u6_activity_2026_10_06/u6_by_unit.csv`. Reading: [`docs/harmonization/MODEL_REPORT.md` §3.1](../../../../docs/harmonization/MODEL_REPORT.md#31-brás-within-são-paulo).

| File | Content |
|---|---|
| `bras_columns.csv` | Per column: Brás's value, São Paulo minimum, median and maximum, rank (1 = highest), within-city z (the all-relative reading) and rank by \|z\| (1 = farthest from the São Paulo mean). U6 mix columns are shares; their z is the city-centred log-ratio standardized within São Paulo, for comparing extremeness only |
| `bras_families.csv` | Per family (and U6's two halves), under all-relative and hybrid scaling: Brás's mean calibrated gap to the other São Paulo districts and its rank among them (1 = most unusual) |

The family ranks are the same under both scalings except M4 (36th vs 40th) and U3 (84th vs 83rd), where pooled standardization and the ±3 cap move a few districts.
