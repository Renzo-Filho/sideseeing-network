# Analysis workspace — start here

## Chicago attribute construction (September 2026)

New: [functional extension and matched-source work](CHICAGO_FUNCTIONAL_EXTENSION.md) · [functional release](results/Chicago/chi_functional_2026_09_16_v2/README.md).

**Continue in a new chat:** copy the complete [NEXT_AGENT_PROMPT.md](NEXT_AGENT_PROMPT.md).

[Data requirements](CHICAGO_DATA_REQUIREMENTS.md) · [Attribute documentation](CHICAGO_ATTRIBUTE_DOCUMENTATION.md) · [Execution report and handoff](CHICAGO_EXECUTION_REPORT.md) · [Chicago outputs](results/Chicago/README.md)


**To analyze the completed São Paulo attributes, open [results/SP](results/SP/README.md).** There are 96 districts, 13 feature families, 23 primary candidate columns and 77 total attribute/diagnostic columns. The primary SP model is implemented; the corrected v2 release and robustness results are available below.

| Folder | Purpose | Should I open it? |
|---|---|---|
| [results/SP](results/SP/README.md) | Final tables, district map, report, figures and validation | **Yes — start here** |
| [notes](notes/README.md) | Research definitions, implementation plan, decisions and handoff | For methodology and next steps |
| data/ | Original downloaded/input datasets; SP and Chicago sources | Only for source investigation; preserve originals |
| [work](work/README.md) | Prepared datasets, supporting experiments and execution checkpoints | For reproduction or debugging |
| config/ | Versioned method choices and input bindings | For pipeline development |
| scripts/, tests/ | Processing code and validation tests | For pipeline development |
| references/ | Source dictionaries and reference material | As needed |
| cache/ | Auxiliary working cache | Not a published result |

`outputs` and `processed` are **compatibility links**, not additional datasets. Existing scripts, frozen manifests and older documentation use those names. `outputs` points to a hidden legacy-path index; `processed` points to `work/prepared`. Use `results/` and `work/` for browsing. No large datasets were copied, and no source or numerical output was changed.

## Layout

```text
analysis/
  results/SP/
    tables/                 primary, full and metadata-rich attribute tables
    spatial/                district GeoPackage
    reports/                readable construction report
    figures/                pilot figure
    validation/
      tables/               outliers, distributions and coverage summaries
      checks/               machine-readable validation results
  notes/                    project methodology and handoff
  data/                     original inputs
  work/
    prepared/SP/            current v3 preparation and historical v2 baseline
    evidence/               source reviews and M2/M6/U2 experiments
    runs/                   checkpoints, intermediate calculations and logs
    organization_manifest.json
  config/  scripts/  tests/  references/  cache/
```

File roles: **CSV** for inspection and interchange (read district IDs as strings); **Parquet** for efficient typed Python/GIS tables; **GPKG** for spatial analysis; **Markdown** for documentation; **JSON** for machine-readable parameters, checks and provenance; **logs/TXT** for execution traces. Files are grouped by purpose first, with human reports and machine checks separated.

## Working conventions

- Read final results from `results/SP`; use the long table for coverage and quality metadata.
- Keep raw inputs and frozen v2/v3 preparations unchanged. Never treat temporary or prepared records as final model attributes.
- New model work belongs in a new versioned run under `work/runs`; publish its accepted outputs separately. Do not overwrite this completed attribute release while exploring results.
- Original executable paths remain supported through relative symbolic links. Preserve symlinks when copying the repository; on systems without symlink support, use a copy tool that dereferences links and check disk requirements.
- The folder migration is recorded in [work/organization_manifest.json](work/organization_manifest.json), including old/new locations and SHA-256 checks of all pre-existing output/prepared files. Reproduction entry points in the existing documentation remain valid. The migration script is `scripts/organize_analysis_workspace.py` and safely exits if already applied.

[Attribute documentation](ATTRIBUTE_DOCUMENTATION.md) — definitions, input processing, formulas, all 77 columns, and limitations.

[Urban model implementation plan](URBAN_MODEL_IMPLEMENTATION_PLAN.md) — proposed N11 preprocessing, family distances, Brás comparisons, robustness tests and deliverables; the primary implementation now exists; see the v2 corrections report for completed modeling and robustness work.

## GitHub checkout and local data

Git tracks analysis code, versioned configurations, documentation, tests and the compact **district-level release** in `results/SP` (about 5.5 MB). Original downloads, record-level prepared data, allocation evidence, caches and execution intermediates are intentionally excluded by `.gitignore`; they remain on the original workstation. A fresh checkout can inspect the published attributes without those large datasets.

For development, use Python 3.12 and install `analysis/requirements.txt` into a virtual environment. Run `python -m unittest discover -s analysis/tests -p 'test_sp*.py' -v` for synthetic tests. Full source reconstruction additionally requires the documented raw/prepared inputs; this repository does not bundle them or claim they can be recovered from the district tables.

Legacy scripts still address `analysis/outputs` and `analysis/processed`. To reproduce a historical run, restore the original directory layout from your data backup, or restore the organized `work/` datasets and compatibility links using the original workstation's organization manifest. The one-time `organize_analysis_workspace.py` is a migration tool for a complete pre-organization workspace, not a fresh-checkout bootstrap command. Reports link to some excluded local evidence intentionally; their absence on GitHub is not missing published district results. `fetch.py` is a historical acquisition prototype with older feature labels and bounded requests, not the accepted current preparation entry point. The RAIS fetcher requires a local `GOOGLE_CLOUD_PROJECT` environment variable and separately configured credentials.

[SP model validation](SP_MODEL_VALIDATION.md) — reproduced baseline ranking, identified defects and remaining acceptance work.

[Corrected SP model](SP_MODEL_FIXES.md) · [Chicago harmonization plan](CHICAGO_HARMONIZATION_PLAN.md).
