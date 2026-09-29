# Harmonization build checkpoint — September 22, 2026

User approved implementation and requested documentation of every plan step. H0 is partially complete; the GHSL part of H1 is complete. No model was fitted and no new cross-city family accepted.

- 48 candidate rows: eight pilot areas × three GHSL products × gross/land support.
- 56 pilot coverage/partition checks passed, zero failed.
- Eight focused aggregation unit tests passed.
- All pilots have complete valid raster coverage to numerical tolerance; no missing candidate values. Maximum extent residual is 1.49e-7 m².
- Existing SP v2 and Chicago numeric releases remain unchanged. No downloads or background jobs remain running.

See [cumulative execution documentation](../../../../docs/harmonization/EXECUTION_LOG.md) for formulas, source definitions, limitations, reproduction and the H0–H6 ledger. `ghsl_pilot_attributes.csv` contains provisional measurements, not accepted model inputs. `checks.json`, `source_receipts.json`, `implementation_receipts.json`, `ghsl_definition_evidence.json` and `contract_snapshot.json` bind this checkpoint.

The GHSL PDF lists 255 for AGBH NoData; actual acquired headers use −1. Per-file masks are preserved. Height and volume are correlated products, not three independent families. Area-weighted ANBH includes observed zeros and is a spatial-grid statistic, not mean individual-building height.

Next: complete H0 road access/class/topology and land-mask policy, then H1 paired geometry fixtures. Full-city attributes, functional acceptance, fitting and robustness remain pending. Source completeness and scientific comparability have not been inferred from arithmetic checks.
