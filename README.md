# sideseeing-network

Urban-form similarity research: characterize São Paulo's municipal districts (reference: Brás, district `10`) and Chicago's 77 Community Areas with street-morphology (M), built-form (B) and urban-function (U) feature families, then compare places descriptively. The Chicago-only and São Paulo–Chicago models were fitted on 6 October 2026; both are descriptive comparisons with documented limits.

## Start here

| I want to… | Open |
|---|---|
| Know where the project stands and what is next | [docs/STATUS.md](docs/STATUS.md) — the only page with dated status |
| Continue work in a new agent session | [current status](docs/STATUS.md) · [historical handoff](docs/HANDOFF.md) |
| Understand the research design | [docs/PROTOCOL.md](docs/PROTOCOL.md) |
| See why a feature was kept, deferred or changed | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Explore the three cross-city methods interactively (any reference unit) | [Cross-City Urban Explorer](viz/README.md): `python3 -m http.server 8765 --directory viz` |
| Read the São Paulo–Chicago model (Brás reference) | [model report](docs/harmonization/MODEL_REPORT.md) · [notebook](analysis/sp_chicago_model_analysis.ipynb) · [contract](analysis/config/sp_chicago_model_v1.json) |
| Read the Chicago model (methodology, features, results) | [model report](docs/chicago/MODEL_REPORT.md) · [notebook](analysis/chicago_model_analysis.ipynb) · [contract](analysis/config/chicago_model_v1.json) |
| Read Chicago feature definitions and sources | [model plan](docs/chicago/MODEL_PLAN.md) · [attributes](docs/chicago/ATTRIBUTES.md) · [data sources](docs/chicago/DATA_SOURCES.md) · [M3/M4 block protocol](docs/chicago/BLOCKS_M3_M4.md) · [execution log](docs/chicago/EXECUTION_LOG.md) |
| Read São Paulo definitions and the SP model | [attributes](docs/sp/ATTRIBUTES.md) · [preparation](docs/sp/PREPARATION.md) · [model v2](docs/sp/MODEL.md) |
| Read the SP–Chicago harmonization history | [plan](docs/harmonization/PLAN.md) · [execution log](docs/harmonization/EXECUTION_LOG.md) |
| Find paper-oriented evidence | [survey](docs/survey/README.md) · [advisor brief](docs/survey/ADVISOR_BRIEF.md) · [experiment ledger](docs/survey/EXPERIMENT_LEDGER.md) |
| Browse published results | [SP](analysis/results/SP/README.md) · [Chicago](analysis/results/Chicago/README.md) · `analysis/results/SP_CHI/` |
| Run or find a script | [analysis/scripts/INDEX.md](analysis/scripts/INDEX.md) |
| Work in Curio | [analysis/curio_nodes/README.md](analysis/curio_nodes/README.md) |

Superseded plans and audits are kept unchanged in [docs/archive/](docs/archive/).

## Layout

```text
README.md            this page
docs/                methods, decisions and status (see table above)
viz/                 isolated static Cross-City Urban Explorer (Vercel project root)
analysis/            code, configs, results and local data — see analysis/README.md
  scripts/           pipeline and pilot scripts (flat; INDEX.md), library packages, _archive/*.zip
  curio_nodes/       Chicago feature/model nodes installed in the Curio dataflow
  config/            frozen, versioned method contracts read by scripts
  tests/             unit tests
  results/           published outputs: SP/, Chicago/, SP_CHI/ (tracked)
  data/ cache/ work/ local inputs and intermediates (git-ignored)
```

## Development

Use Python 3.12. `pyproject.toml` declares the project dependencies; `analysis/requirements.txt` records the exact tested environment used by the published releases. Run scripts from the repository root and the tests with:

```bash
.venv/bin/python -m unittest discover -s analysis/tests -v
```

After adding, archiving or documenting a script, regenerate the index with `.venv/bin/python analysis/scripts/make_index.py`.
