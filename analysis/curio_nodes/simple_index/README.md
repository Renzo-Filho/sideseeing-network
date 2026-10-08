# Curio dataflow: composite urban index (methods A and B) and the harmonized model (H)

Saved Curio project **"Composite urban index: method A and method B"** (`4e6b8d2a-af2e-44f2-9ce9-32b1646553f3`, user 3). One canvas, three complete lanes:

| Lane | Sources → factor nodes | Merge → index | Result tables (Simple View) |
|---|---|---|---|
| **A** (top) | C commercial · R dwellings · H hubs · V Overture height · N, L streets | counts per unit, pooled min–max, equal-weight sum | top 10 units; five Chicago areas closest to Brás; map of Chicago areas by closeness to Brás |
| **B** (middle) | C · R · H · V GHSL volume ÷ surface · N, L · land area | counts ÷ land km², pooled min–max, equal-weight sum | top 10 units; five Chicago areas closest to Brás; map of Chicago areas by closeness to Brás |
| **H** (bottom) | the 12 accepted families of `sp_chicago_model_v2`, one loader and one node each (M1, M3, M4, M6, M7 · B1, BV · U2, U3, U4, U6, U1) | one merge and join per domain → standardized profile (J-5 transforms, C6 hybrid scaling, ±3 cap) → distance between every pair of units (blocks calibrated by their median pair, equal family budgets: run R1) | ten units closest to Brás; five Chicago areas closest to Brás with the two families driving each distance; map of Chicago areas by distance to Brás |

### Lane H: harmonized cross-city similarity model (added 7 October 2026; v2 since 8 October 2026)

- **Version 2 (8 October 2026):** U1 compares four land-use shares, with the commerce share added by user decision ([report §11](../../../docs/harmonization/MODEL_REPORT.md#11-version-2-u1-commerce-share-8-october-2026)). Same datasets: the commerce share is in the accepted U1 table.
- **Weights you can change:** the first lines of *H · distance between every pair of units* hold `FAMILY_WEIGHTS` (a family's budget, e.g. `{'U1': 2}`) and `COLUMN_WEIGHTS` (a column inside its family, e.g. `{'p_commerce': 2}`; 0 drops it). Both are empty in the published fit. A column weight recomputes its block's calibration, so it changes only the mix inside the family. `COLUMN_WEIGHTS = {'p_commerce': 0}` reproduces v1 exactly (checked by `run_local.py`).

- **Inputs are the accepted family tables**, not raw sources: each family was built and validated step by step ([MODEL_PLAN](../../../docs/chicago/MODEL_PLAN.md)), and rebuilding them would repeat that work. `register_datasets.py` hard-links the ten tables into the dataset store (`data.sideseeing.feature-*`); each family node refuses a table whose SHA-256 differs from the one in `analysis/config/chicago_model_v1.json` (U3 São Paulo: `sp_chicago_model_v1.json`). `dataflow.py` reads hashes and columns from those contracts.
- **Nodes:** `nodes/h_family.py` (one per family, constants inserted by `dataflow.py`), `join_factors.py` (per domain), `h_profile.py`, `h_distance.py`, `h_top10.py`, `h_closest.py`, `h_chicago_map.py`. The distance node returns every ordered pair (29,756 rows) with the distance, the other unit's rank overall and in its city, and each family's part of D², so any other reference is one filter away.
- **The top-10 view** lists the ten units closest to Brás (both cities), because the model has no index to rank by; its first ten are all São Paulo districts. The other two views match lanes A and B.
- **Validation** (`run_local.py … --lanes H`, Curio's Python): every pair distance equals the published v2 hybrid R1 matrix to 2.2e-15, and with commerce at weight 0 the v1 matrix to 2.2e-15; Brás's ranking of all 172 units is identical; the Chicago five are West Town, Avondale, Logan Square, Lincoln Park, North Center; West Town's family shares match the published worked example (B1 38%, U6 22%, U1 18%). The lane runs in about 1.5 s and 0.2 GB. `validate_trill.py --resolve` accepts the patched spec (revision 19).
- **Not in the lane:** R2, R3, the all-absolute and all-relative scalings, weight draws and sensitivities. The interactive explorer (`viz/`) recomputes those.

Each map (Vega-Lite) shades the 77 Community Areas by index gap to Brás, |I(u) − I(Brás)|, darker meaning closer, and outlines and numbers the five closest (`nodes/chicago_map.py`, spec in `dataflow.py`). Definitions follow protocol P-AB-1 ([docs/SIMPLE_INDEX.md](../../../docs/SIMPLE_INDEX.md)). The bias tests are not part of this dataflow.

## Files

- `nodes/*.py` (including `join_factors.py`): the code of every computation node (each file is the body of the node; `arg` is its input).
- `dataflow.py`: loaders, placement and edges for both lanes.
- `register_datasets.py`: adds the inputs Curio did not have to the user's dataset store (hard links; GTFS as text Parquet), including lane H's ten accepted family tables.
- `run_local.py`: runs the lanes as the Curio sandbox does (`--lanes ABH`, default all) and compares them with the published results; `run_local_report.json` holds the last comparison of each lane.
- `install_project.py`: creates the project through Curio's `save_project` (`--dry-run` writes nothing).
- `patch_project.py`: updates an installed project's node code and dataset references in place (under Curio's spec lock, with a backup).

Curio's catalog does not accept GeoPackage datasets (`gpkg` is not a supported manifest format), so the São Paulo district layer is registered as GeoParquet and the São Paulo buildings as a table of height and bounding-box centre for buildings with a height (2,090,405 rows, read from the GeoPackage R-tree by the same query the validated build used). Fixed 2 October 2026 after the first in-Curio run failed on these two inputs.

Two Curio rules shape method B's wiring: the canvas keeps at most five inputs per Merge Flow (`in_0` … `in_4`) and silently drops extra wires when a project loads, and the sandbox resolves only one merge level, so a merge's output cannot usefully feed another merge (it arrives as a tuple of unresolved references). Method B therefore merges its five factors, joins them in "B · join factors per unit", and merges that table with land area in "B · factors and land area" before the index. `run_local.py` asserts both rules and runs nodes in dependency order, as Curio does.

## Data loading through the Discovery Catalog (2 October 2026)

The loaders now read 17 of the 21 datasets, and the GHSL rasters, from Curio's Discovery Catalog: the City of Chicago portal (Community Areas, Hydro), GeoSampa (districts), and a folder source `.curio/discovery/source.sideseeing.local-data@1` over `analysis/data` (Overture places, segments and Chicago buildings, CNEFE, both GTFS feeds as `.txt` tables, GHSL raster collections read with `curio_collection`). The dataset ids are listed, with what each is, in `dataflow.py` (`D`, `LABELS`). Still registered by `register_datasets.py`: the prepared reporting units, the Census blocks and the São Paulo building heights (project-derived; the source GeoPackage exceeds the catalog's 512 MiB limit).

With these inputs method A is unchanged and method B's index moves by at most 2.8e-7 (GeoSampa's district outlines arrive in EPSG:4326), with identical ranks, closest areas and maps. Issues found while testing the catalog: [DISCOVERY_CATALOG_ISSUES.md](DISCOVERY_CATALOG_ISSUES.md).

## Validation (2 October 2026)

Run under Curio's Python environment, both lanes reproduce [the published tables](../../results/SP_CHI/simple_index_ab_2026_10_01/README.md): largest index difference 4.4e-16 (A) and 8.9e-16 (B), identical ranks, identical five closest Chicago areas and profile ranks. Local run: 2 min 53 s, peak 3.7 GB. Curio's `validate_trill.py --resolve` accepts the saved spec.

The A top-10 table shows gross unit area, because method A uses no land denominator; the B table shows land area.

## Rebuild

```bash
CURIO=/home/renzo/Documents/GitHub/curio
$CURIO/venv/bin/python register_datasets.py $CURIO/.curio/users/3/datasets
$CURIO/venv/bin/python run_local.py $CURIO/.curio/users/3/datasets
cd $CURIO && PYTHONPATH=$CURIO DATABASE_URL=sqlite:///$CURIO/instance/urban_workflow.db CURIO_LAUNCH_CWD=$CURIO \
  venv/bin/python /path/to/install_project.py --user 3
```

In Curio, run one lane at a time: the residential and height nodes each use 1–3 GB of memory.
