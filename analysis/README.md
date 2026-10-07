# Analysis workspace

What each folder is for and the rules for adding to it. Project entry point and documentation map: [root README](../README.md). The deployable explorer lives in the repository-root [viz/](../viz/README.md); `scripts/export_viz_data.py` regenerates its browser data, and `tests/check_viz_model.js` compares it with the published results.

## Folders

| Folder | What it holds | Tracked | Rule |
|---|---|---|---|
| [results/](results/) | Published outputs, one folder per release: `SP/`, `Chicago/`, `SP_CHI/` (paired cross-city work). Each release has its own README, tables and validation receipts | yes | Never overwrite a release; publish a new dated/versioned folder. Start with [SP](results/SP/README.md) or [Chicago](results/Chicago/README.md) |
| [scripts/](scripts/INDEX.md) | Pipeline, pilot and validation scripts (flat), library packages `harmonization/`, `sp_attributes/`, `sp_model/`, `sp_v3/`, and finished scripts in `_archive/*.zip` | yes | Keep flat: scripts find the repo root with `parents[2]` and import each other. Regenerate [INDEX.md](scripts/INDEX.md) with `make_index.py` |
| config/ | Frozen, versioned method contracts (JSON) and one lookup CSV read by scripts; see [config bindings in INDEX.md](scripts/INDEX.md#config-bindings-analysisconfig) | yes | Never edit in place: a change is a new file with the next version. Keep superseded versions; published results cite them |
| tests/ | Unit tests (`unittest`) | yes | Run from the repo root: `.venv/bin/python -m unittest discover -s analysis/tests` |
| [curio_nodes/](curio_nodes/README.md) | Chicago feature and model nodes installed in the Curio dataflow, and install/sync scripts | yes | Curio spec backups (`backup_spec_rev_*.json`) stay local |
| data/ | Original downloads (SP, Chicago, shared), ~16 GB | no | Never edit |
| cache/ | Regenerable download caches (Overture SP extraction), ~0.8 GB | no | Safe to rebuild |
| [work/](work/README.md) | Local intermediates, ~8 GB: `prepared/`, `evidence/`, `runs/`, plus dated pilot folders | no | Not published. New pilots write to `work/runs/<name>_<date>/` |
| `outputs` → `.compat/outputs/`, `processed` → `work/prepared` | Legacy symlinks from the 11 September 2026 reorganization; `.compat/` holds only links (below) | — | Keep; do not use for new work |

Notebooks: [chicago_curio_model_analysis.ipynb](chicago_curio_model_analysis.ipynb) reproduces the Chicago Curio feature construction, eight-family candidate model and three linked views; [model_analysis.ipynb](model_analysis.ipynb) and `model_analysis.py` analyze the São Paulo model v2.

### Legacy links: `outputs`, `processed` and `.compat/`

The 11 September reorganization moved SP outputs into `work/` and kept the old names working through links. `.compat/` contains no data:

```text
outputs -> .compat/outputs/
  sp_attributes/sp_attributes_2026_09_11_v1   -> work/runs/sp_attributes_2026_09_11_v1
  sp_allocation_experiments_2026_09_10        -> work/evidence/job_allocation_experiments
  sp_audit                                    -> work/evidence/source_inventory
  sp_readiness_2026_09_09                     -> work/evidence/historical_readiness
  sp_resolution_review_2026_09_10             -> work/evidence/data_resolution
  sp_simplification_review_2026_09_10         -> work/evidence/road_classification_and_crossings
processed -> work/prepared
```

The frozen SP pipeline (`sp_v3/common.py`, `sp_attributes/`, several SP scripts) and the frozen configs `sp_current_methods.json` and `sp_attributes_2026_09_11.json` still address these paths, so the links must stay until that pipeline is retired. Preserve symlinks when copying the repository. The migration is recorded in `work/organization_manifest.json` (local), with old/new locations and SHA-256 checks.

## File formats

**CSV** for inspection and interchange (read district IDs as strings); **Parquet** for typed Python/GIS tables; **GPKG/GeoJSON** for spatial data; **Markdown** for human reports; **JSON** for parameters, checks and provenance; **logs/TXT** for execution traces. Human reports and machine checks are kept separate.

## Git checkout versus local data

Git tracks code, configs, documentation, tests and the published `results/`. Original downloads, prepared records, evidence, caches and intermediates are excluded by `.gitignore` and remain on the original workstation. A fresh checkout can read the published results but cannot rebuild them; full reconstruction requires the documented raw/prepared inputs, which this repository does not bundle. Result reports sometimes link to local-only evidence on purpose.

The RAIS fetcher (`scripts/fetch_RAIS.py`) requires a local `GOOGLE_CLOUD_PROJECT` environment variable and separately configured credentials.
