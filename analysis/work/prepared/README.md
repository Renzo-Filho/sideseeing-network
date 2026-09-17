# Prepared source data

These are standardized inputs to attribute construction, **not final model attributes**. Original downloads remain in `analysis/data`; review-ready results are in [results/SP](../../results/SP/README.md).

| Folder | Status and purpose |
|---|---|
| SP/sp_prep_2026_09_10_v3/ | Current frozen preparation: expanded SP sources and N01–N09 integration, about 1.6 GB |
| SP/sp_prep_2026_09_09_v2/ | Historical baseline, about 1.2 GB; retained for reproducibility and reused parcel geometry |

Both versions are needed by the completed attribute run. Do not delete v2 merely because v3 exists. Later approved M2/M6 rules and U2 allocations live in `work/evidence` and supplement v3; its historical readiness flags were intentionally not rewritten.

## What the v3 stage folders mean

| Stage | Prepared content |
|---|---|
| N01 | Source inventory, hashes and baseline-preservation manifest |
| N02 | District boundaries, water and land denominators |
| N03 | Parcel identities, fiscal-unit records, floor proxies and land-use profiles |
| N04 | Canonical street geometry and classification evidence |
| N05 | Planar crossing candidates and structure diagnostics; not certified routing topology |
| N06 | Eligible blocks, municipal building records and building–parcel overlap candidates |
| N07 | Census population allocation and initial formal-employment geography |
| N08 | Transit stops and dated expected bus-service scenarios |
| N09 | Integrated integrity and family-readiness checks |
| review/, logs/ | Human-review material and execution traces |

The v2 folders use older descriptive names: `01_districts`, `02_parcels_tax`, `03_streets`, plus review, logs and run metadata. They remain frozen rather than being reorganized internally, because hashes, partition paths and later pipelines depend on them.

Parquet contains prepared records; JSON contains provenance, assumptions and checks. For a human account of acceptance and limitations, read the [handoff](../../../docs/sp/SP_DATA_RESOLUTION_HANDOFF.md). Existing `analysis/processed/...` references resolve here through a compatibility link.
