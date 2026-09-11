# Supporting evidence

These folders explain why data and methods were accepted. They are not final attribute tables.

| Folder | What it contains |
|---|---|
| source_inventory/ | Initial inventory and GIS/RAIS source checks |
| historical_readiness/ | Earlier parcel/identity readiness assessment; historical |
| data_resolution/ | Review of newly supplied data and documentation consolidation |
| road_classification_and_crossings/ | M6 Local-class overlay, M2 distance scenarios, unmatched-job priorities and supporting checks |
| job_allocation_experiments/ | Ten U2 geographic allocation scenarios, conservation checks, disagreements and approved M2 selection overlay |

Use [SP_METHOD_DECISIONS.md](../../notes/SP_METHOD_DECISIONS.md) for a human explanation. JSON is evidence/provenance, CSV holds summaries, and Parquet holds reusable allocation/overlay records. Preserve the contents and versioned manifests: the attribute pipeline consumes selected files from these experiments. New experiments should use new folders rather than overwrite accepted evidence.
