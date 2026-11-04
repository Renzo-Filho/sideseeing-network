# sideseeing-network

Two connected research tracks on walkable urban space in São Paulo and Chicago.

1. **Urban similarity model** ([analysis/](analysis/README.md)). Describes São Paulo's 96 districts (reference: Brás, district `10`) and Chicago's 77 Community Areas with street-morphology (M), built-form (B) and urban-function (U) feature families, and compares places descriptively. The Chicago-only and São Paulo–Chicago models were fitted on 6 October 2026.
2. **Sidewalk network** ([network/](network/README.md)). Field collection with a phone on a vest (video, GPS, motion sensors, voice), and the passage graph built from those recordings without a map. It aims at two papers: a West Loop + Brás dataset, and the passage graph.

Agents: read [AGENTS.md](AGENTS.md) first.

## Start here

| I want to… | Open |
|---|---|
| Know where the similarity model stands | [analysis/docs/STATUS.md](analysis/docs/STATUS.md) |
| Know where the sidewalk network stands | [network/docs/STATUS.md](network/docs/STATUS.md) |
| Read the cross-city model and its conclusions | [model report](analysis/docs/harmonization/MODEL_REPORT.md) |
| Explore the cross-city methods interactively | [Cross-City Urban Explorer](analysis/viz/README.md): `python3 -m http.server 8765 --directory analysis/viz` |
| Read the passage-graph work in plain English | [GRAPH_WORK_EXPLAINED](network/docs/GRAPH_WORK_EXPLAINED_2026-10-30.md) |
| Find every document of a track | [analysis/README.md](analysis/README.md) · [network/docs/README.md](network/docs/README.md) |
| Find a dataset | Model inputs: [analysis/data/README.md](analysis/data/README.md) · field captures: [network/data/README.md](network/data/README.md) and [Drive/RustFS inventory](network/docs/datasets/README.md) |
| Run or find a script | [analysis/scripts/INDEX.md](analysis/scripts/INDEX.md) · [network/README.md](network/README.md#code) |

## Layout

```text
README.md  AGENTS.md      this page; the guide for agents (CLAUDE.md points to it)
analysis/                 track 1: urban similarity model
  docs/                   status, protocol, decisions, per-city and cross-city reports, archive/
  viz/                    Cross-City Urban Explorer, a static site (deploy root)
  scripts/ config/ tests/ code, frozen method contracts, unit tests
  results/                published releases: SP/, Chicago/, SP_CHI/ (tracked)
  curio_nodes/            nodes and dataflows installed in Curio
  data/ cache/ work/      model inputs and intermediates (local, git-ignored)
network/                  track 2: sidewalk network
  docs/                   status, plans, protocols, phase notes, datasets/, archive/
  graph/                  the passage-graph package (python -m graph.<phase>)
  scripts/                route planning, transcription, Drive mount, transfers
  notebooks/              field-day analysis notebooks (local, not committed yet)
  data/                   captures and everything derived from them (local, git-ignored)
```

## Development

Python 3.12. Two environments:
- `.venv` (this repo) for `analysis/` and the route-planning scripts. `pyproject.toml` declares its dependencies; `analysis/requirements.txt` pins the tested ones.
- `../sideseeing-tools/venv` (a sibling repo) for `network/graph`, the notebooks and anything needing torch, Whisper or SAM3. Heavy runs happen on desktop-01.

```bash
.venv/bin/python -m unittest discover -s analysis/tests        # analysis tests
node analysis/tests/check_viz_model.js                         # explorer vs published results
cd network && ../../sideseeing-tools/venv/bin/python -m pytest -q graph/tests   # graph tests
```
