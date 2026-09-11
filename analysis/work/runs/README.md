# Execution records

`sp_attributes_2026_09_11_v1/` is the completed attribute-construction run. Final tables/maps/checks now resolve through links to [results/SP](../../results/SP/README.md).

| Item inside the run | Purpose |
|---|---|
| intermediates/ | Parcel areas, canonical fiscal summaries, per-district footprint QA, population points and per-point bus service |
| parts/ | Hash-checked B1/U4 feature checkpoints by district; avoid repeating expensive calculations |
| population_support_sensitivity/ | 125 m pilot experiment and comparison with primary 250 m support |
| logs/ | Execution traces, including failures fixed before release |
| manifest.json | Frozen input/config bindings |
| progress.json | Completion state; no model fitted |
| release_inventory.json | Original release code/output/documentation hash snapshot |
| pilot_attributes_long.parquet | Intermediate pilot subset |
| REPORT.md | Frozen report; reader copy with relocated links is in results/SP/reports |
| runner.lock | Pipeline concurrency lock, not data |

Do not interpret checkpoint files as separate datasets to analyze. The release was complete before folder organization; old filenames remain as links for reproducibility. Frozen inventories describe their original release snapshot; the organization manifest documents the later location change.
