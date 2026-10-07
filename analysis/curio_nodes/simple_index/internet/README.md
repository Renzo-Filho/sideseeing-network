# Internet-fetched composite urban index

Curio project `62ab18dc-dbff-4bc6-9050-99536dea8854` is a separate copy of the original composite index `4e6b8d2a-af2e-44f2-9ce9-32b1646553f3`. It keeps the original factor, merge, index, table, and map specification. Eleven source-selector nodes and the two map-data nodes now receive or fetch internet sources; seven new acquisition nodes fetch and prepare those sources. The saved project has **zero Curio dataset references**.

The standalone file [internet_dataflow.trill.json](internet_dataflow.trill.json) embeds every node's code. Running it does not import a Python function or read a file from this repository. It needs outbound internet access and temporary scratch space during execution; its large intermediates are removed after preparation where possible.

The flow uses pinned Overture release `2026-08-19.0`, GHSL `R2023A`, IBGE CNEFE 2022, and Census TIGER/Line 2022 blocks. The Chicago/GeoSampa portals and CTA/SPTrans GTFS endpoints serve their current contents. In particular, the current SPTrans feed differs from the one downloaded for the original flow in September 2026. The **method logic** is the same; some index values may differ because the published inputs changed.

Curio's 64 MiB Discovery Catalog limit does not apply to the acquisition nodes because they fetch and extract the public sources in node code. The local Curio browser reports `not isolated`; the saved flow has not been executed end-to-end inside Curio. An isolated Curio runtime blocks node network egress and cannot run this flow until Curio supports this use case.

## Verification

- Each acquisition program was run against its public source into a fresh temporary folder. The reporting units, Overture places and road segments, CNEFE, Census blocks, both GTFS feeds, Overture buildings, and GHSL rasters were fetched or reconstructed. All six GHSL raster arrays matched the current local arrays cell-for-cell.
- The copied A and B calculation pipelines were executed from those fetched outputs: each produced 173 index rows, both result tables, and both map datasets.
- Curio's `validate_trill.py --resolve` accepted the generated JSON and the saved project. The saved spec has 47 nodes, 55 edges, no dataset references, no `curio_dataset_path` calls, and no local repository paths in node code.

The [build script](build_dataflow.py) embeds the acquisition files into the JSON; those files are authoring sources only. The [verification script](verify_pipeline.py) runs the generated graph against already fetched scratch inputs. Neither is needed by an advisor who imports the JSON.
