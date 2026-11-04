# Urban similarity model (analysis/)

Track 1 of the project: São Paulo's districts and Chicago's Community Areas described with M, B and U feature families and compared descriptively, with Brás as the reference. Everything for this track lives under this folder: code, configs, results, documentation and the explorer. The other track is [network/](../network/README.md); the rules for agents are in [AGENTS.md](../AGENTS.md).

## Start here

| I want to… | Open |
|---|---|
| Know where the model stands and what is next | [docs/STATUS.md](docs/STATUS.md), the only page with dated status for this track |
| Understand the research design | [docs/PROTOCOL.md](docs/PROTOCOL.md) |
| See why a feature was kept, deferred or changed | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Explore the three cross-city methods interactively (any reference unit) | [Cross-City Urban Explorer](viz/README.md): `python3 -m http.server 8765 --directory analysis/viz` from the repo root |
| Read the São Paulo–Chicago model (Brás reference; proposed settings v4 and candidate v3, on v2's data with the U1 commerce share) | [model report](docs/harmonization/MODEL_REPORT.md) (conclusions §1; v1 §5, v2 §6, v3 §7, v4 §8; across versions §9; Chicago neighborhoods §10) · [contract v4](config/sp_chicago_model_v4.json) · [contract v3](config/sp_chicago_model_v3.json) · [notebook](sp_chicago_model_analysis.ipynb) · [contract v2](config/sp_chicago_model_v2.json) · [v1](config/sp_chicago_model_v1.json) |
| Read the Chicago model (methodology, features, results) | [model report](docs/chicago/MODEL_REPORT.md) · [notebook](chicago_model_analysis.ipynb) · [contract](config/chicago_model_v1.json) |
| Read Chicago feature definitions and sources | [model plan](docs/chicago/MODEL_PLAN.md) · [attributes](docs/chicago/ATTRIBUTES.md) · [data sources](docs/chicago/DATA_SOURCES.md) · [M3/M4 block protocol](docs/chicago/BLOCKS_M3_M4.md) · [execution log](docs/chicago/EXECUTION_LOG.md) |
| Read São Paulo definitions and the SP model | [attributes](docs/sp/ATTRIBUTES.md) · [preparation](docs/sp/PREPARATION.md) · [model v2](docs/sp/MODEL.md) |
| Read the SP–Chicago harmonization history | [plan](docs/harmonization/PLAN.md) · [execution log](docs/harmonization/EXECUTION_LOG.md) |
| Read the advisor's simple index (methods A/B) | [docs/SIMPLE_INDEX.md](docs/SIMPLE_INDEX.md) · [notebook](simple_index_ab.ipynb) |
| Find paper-oriented evidence | [survey](docs/survey/README.md) · [advisor brief](docs/survey/ADVISOR_BRIEF.md) · [experiment ledger](docs/survey/EXPERIMENT_LEDGER.md) |
| Find every dataset: content, source, version, use in the models | [data register](data/README.md) |
| Browse published results | [SP](results/SP/README.md) · [Chicago](results/Chicago/README.md) · `results/SP_CHI/` |
| Run or find a script | [scripts/INDEX.md](scripts/INDEX.md) |
| Work in Curio | [curio_nodes/README.md](curio_nodes/README.md) |

Superseded plans, audits and the September handoff are kept unchanged in [docs/archive/](docs/archive/).

## Folders

| Folder | What it holds | Tracked | Rule |
|---|---|---|---|
| [docs/](docs/) | Status, protocol, decisions, per-city (`chicago/`, `sp/`) and cross-city (`harmonization/`) reports, the paper survey (`survey/`) and `archive/` | yes | Dated status goes only in `docs/STATUS.md`. Superseded pages move to `archive/` unchanged |
| [viz/](viz/README.md) | The Cross-City Urban Explorer: a static site, complete on its own (the deploy root). `scripts/export_viz_data.py` regenerates `viz/data.js`; `tests/check_viz_model.js` compares it with the published results | yes | Never type numbers into the page; regenerate `data.js` |
| [results/](results/) | Published outputs, one folder per release: `SP/`, `Chicago/`, `SP_CHI/` (paired cross-city work). Each release has its own README, tables and validation receipts | yes | Never overwrite a release; publish a new dated/versioned folder. Start with [SP](results/SP/README.md) or [Chicago](results/Chicago/README.md) |
| [scripts/](scripts/INDEX.md) | Pipeline, pilot and validation scripts (flat), library packages `harmonization/`, `sp_attributes/`, `sp_model/`, `sp_v3/`, and finished scripts in `_archive/*.zip` | yes | Keep flat: scripts find the repo root with `parents[2]` and import each other. Regenerate [INDEX.md](scripts/INDEX.md) with `make_index.py` |
| config/ | Frozen, versioned method contracts (JSON) and one lookup CSV read by scripts; see [config bindings in INDEX.md](scripts/INDEX.md#config-bindings-analysisconfig) | yes | Never edit in place: a change is a new file with the next version. Keep superseded versions; published results cite them |
| tests/ | Unit tests (`unittest`) | yes | Run from the repo root: `.venv/bin/python -m unittest discover -s analysis/tests` |
| [curio_nodes/](curio_nodes/README.md) | Chicago feature and model nodes installed in the Curio dataflow, and install/sync scripts | yes | Curio spec backups (`backup_spec_rev_*.json`) stay local |
| [data/](data/README.md) | Original downloads (SP, Chicago, shared), ~14.2 GB. [README.md](data/README.md) registers every dataset (content, source, use, terms, what was removed on 20 Oct 2026); `SHA256SUMS` hashes every file | register only | Never edit; new downloads go in a dated folder with a manifest and a register row |
| cache/ | Provenance of the Overture SP building extraction (SQL, manifest, STAC items, IBGE inputs), ~7 MB. Its regenerable Parquet checkpoint and DuckDB extensions were removed on 20 Oct 2026 | no | Keep the provenance files |
| [work/](work/README.md) | Local intermediates, ~6 GB: `prepared/`, `evidence/`, `runs/`, plus dated pilot folders | no | Not published. New pilots write to `work/runs/<name>_<date>/` |
| `outputs` → `.compat/outputs/`, `processed` → `work/prepared` | Legacy symlinks from the 11 September 2026 reorganization; `.compat/` holds only links (below) | — | Keep; do not use for new work |

Notebooks, at this folder's top level, each reproduce one model from its scripts: [sp_chicago_model_analysis.ipynb](sp_chicago_model_analysis.ipynb) (cross-city model), [chicago_model_analysis.ipynb](chicago_model_analysis.ipynb) (Chicago model v1), [simple_index_ab.ipynb](simple_index_ab.ipynb) (simple index A/B), [chicago_curio_model_analysis.ipynb](chicago_curio_model_analysis.ipynb) (the Chicago Curio feature construction, eight-family candidate model and three linked views), and [model_analysis.ipynb](model_analysis.ipynb) with `model_analysis.py` (São Paulo model v2).

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

Git tracks code, configs, documentation, tests and the published `results/`. Original downloads, prepared records, evidence, caches and intermediates are excluded by `.gitignore` and remain on the original workstation. The [data register](data/README.md) and its `SHA256SUMS` are tracked, so the sources and their exact versions stay documented without the files. A fresh checkout can read the published results but cannot rebuild them; full reconstruction requires the documented raw/prepared inputs, which this repository does not bundle. Result reports sometimes link to local-only evidence on purpose.

The RAIS fetcher (`scripts/fetch_RAIS.py`) requires a local `GOOGLE_CLOUD_PROJECT` environment variable and separately configured credentials.
