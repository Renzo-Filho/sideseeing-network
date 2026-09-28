# Chicago data discovery — 18 September 2026

See the [full source-by-source report](../../../../docs/chicago/CHICAGO_DATA_DISCOVERY_2026_09_18.md).

- `dataset_register.csv`: ten selected datasets/documentation sources and attribute mapping.
- `request-validation.json`, `followup-validation.json`: exact public API request URLs, retrieval outcomes and counts. Two whole-history aggregations timed out; successful samples are not full-data completeness checks.
- `geometry_sample_checks.json`: sampled Esri rings only, not full polygon topology or city coverage.
- `evidence_manifest.json`: sizes and SHA-256 hashes of local raw evidence in the Git-ignored `.firecrawl/chicago-data-2026-09-18/` directory. Transfer raw evidence separately when handing work to another machine; respect DuPage redistribution restrictions.

The initial DuPage contains-Chicago query includes West Chicago and is rejected. Use the separately recorded exact-label query only as a diagnostic; spatial city selection is still required. No model attributes were built. No complete county downloads are represented by these artifacts.
