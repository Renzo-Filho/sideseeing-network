# Guide for agents

Read this before working in the repository. It says what the project is, where each kind of information lives, and the rules that keep the research reproducible. `CLAUDE.md` points here, so Claude Code and other agents read the same file.

## 1. The project in two tracks

| Track | Folder | Question | Status page |
|---|---|---|---|
| Urban similarity model | [analysis/](analysis/README.md) | How similar are São Paulo districts (reference: Brás) and Chicago Community Areas, by street, building and function features? | [analysis/docs/STATUS.md](analysis/docs/STATUS.md) |
| Sidewalk network | [network/](network/README.md) | Can phone recordings of a walk (video, GPS, motion, voice) build a map of where people can walk, without a map? | [network/docs/STATUS.md](network/docs/STATUS.md) |

The similarity model was fitted on 6 October 2026 and is in its write-up phase. Day-to-day work is now on the network track: the West Loop (Chicago) collection, the passage graph, and the West Loop + Brás dataset.

## 2. Where to find things

| Looking for | Go to |
|---|---|
| What is done and what is next | The track's `STATUS.md` (the only pages with dated status) |
| Every document of a track | [analysis/README.md](analysis/README.md) (start-here table) · [network/docs/README.md](network/docs/README.md) |
| Why a choice was made | [analysis/docs/DECISIONS.md](analysis/docs/DECISIONS.md) · the numbered decisions in [network/docs/PLAN.md](network/docs/PLAN.md) and [PAPERS.md](network/docs/PAPERS.md) §6 |
| A script, what it does, who imports it | [analysis/scripts/INDEX.md](analysis/scripts/INDEX.md) · [network/README.md](network/README.md#code) |
| A model input dataset | [analysis/data/README.md](analysis/data/README.md) (register + `SHA256SUMS`) |
| A field capture or its derivatives | [network/data/README.md](network/data/README.md) (local) · [network/docs/datasets/](network/docs/datasets/README.md) (Drive and RustFS inventories) |
| A published number | The release folder under `analysis/results/` that produced it, or the network phase notes and `network/data/west_loop/graph/` |
| Old plans and handoffs | `analysis/docs/archive/` · `network/docs/archive/` (kept unchanged; do not treat as current) |

## 3. Environments and machines

- Run everything from the **repository root**, except `network/graph`, which runs from `network/` as `python -m graph.<module>`.
- `.venv` (Python 3.12): `analysis/`, `network/scripts/routes.py`, `route_methods.py`, `routing_example.py`.
- `../sideseeing-tools/venv` (sibling repo): `network/graph`, its tests, the network notebooks, `transcribe.py`, anything with torch, Whisper or SAM3.
- desktop-01 runs the heavy processing (frames, SAM3, redaction, Whisper, motion). Its sideseeing-tools workspace is copied to `network/data/<area>/workspace/`.
- Raw captures live on Google Drive (mount read-only with `network/scripts/drive.sh mount`) and in the RustFS `sideseeing` bucket. **The laptop disk is nearly full:** read captures in place; never make large local copies; delete scratch output you create.

Tests, all must pass before a commit that touches code:

```bash
.venv/bin/python -m unittest discover -s analysis/tests
node analysis/tests/check_viz_model.js
cd network && ../../sideseeing-tools/venv/bin/python -m pytest -q graph/tests
```

## 4. Rules

**Data and results**
1. Never modify a raw capture folder (MultiSensor `video.mp4`, `gps.csv`, sensor CSVs, `metadata.json`) or anything in `analysis/data/`. Derived output goes to the area's `derived/`, `workspace/` or `graph/`, or to `analysis/work/`.
2. Never overwrite a published release in `analysis/results/`. Publish a new dated folder (`<name>_<yyyy_mm_dd>`) with its own README.
3. Configs in `analysis/config/` are frozen contracts. A change is a new file with the next version; keep the old one.
4. A new model input gets a dated folder, a row in `analysis/data/README.md` and its hash in `SHA256SUMS`.
5. Keep the legacy links `analysis/outputs`, `analysis/processed` and `analysis/.compat/`: the frozen São Paulo pipeline reads through them.
6. Some scripts record their own SHA-256 in their outputs (`build_simple_index_ab`, `evaluate_places_against_cnefe`, `audit_simple_index_sources`, `acquire_harmonized_overture`, `acquire_osm_places`, `experiment_sp_allocations`, `prepare_sp_inputs`, `validate_chicago_employment_sensitivity_v2`). Do not edit them, not even a docstring, unless you are making a new release.

**Privacy and licences**

7. Cook County parcel data, and pages built on it (`network/data/west_loop/graph/map.html`, the reference), stay on this machine.
8. Raw audio never leaves the machine. Audio is released only as annotated transcripts.
9. Video frames show people. Do not commit notebook outputs or frames; the network notebooks stay uncommitted until outputs are stripped.
10. Never put credentials, tokens or rclone configuration in the repository.

**Research integrity**

11. Every number you state comes from the project's own data or a result file you have read. Never quote a figure from memory, a paper or the web as if it were measured here.
12. Graph construction is automatic (PLAN decision 2). The Morgan reference (curbs, back of sidewalk) and the spoken code words are for **scoring only**, never inputs (decision 14).
13. Do not snap GPS to OSM or map-match it inside graph construction. An OSM-assisted track is only a map-assisted baseline.
14. D3 (Sangamon and Peoria) is the held-out test: run it once, with every setting frozen, and report the result whatever it is.
15. A result is "done" only when its gate in the plan is checked. Report a half-met gate as half met.

**Documents**

16. Dated status goes only in the track's `STATUS.md`. Other pages carry the date they describe and are not re-dated with status banners.
17. A new document goes in its track's `docs/` and gets a row in the index (`analysis/README.md` or `network/docs/README.md`). A superseded one moves unchanged to `docs/archive/`, and its index row says why.
18. Write in plain English: short sentences, concrete terms, tables for comparisons. Relative links only, checked to resolve.
19. After adding, archiving or documenting an analysis script, regenerate the index: `.venv/bin/python analysis/scripts/make_index.py`.

## 5. Where new things go

| New thing | Place |
|---|---|
| Analysis script | `analysis/scripts/<verb>_<subject>[_<yyyy_mm_dd>].py`, flat, with a one-line docstring; then `make_index.py` |
| Analysis result | `analysis/results/{SP,Chicago,SP_CHI}/<name>_<yyyy_mm_dd>/` with README, tables and checks |
| Graph step | a module in `network/graph/` with its command line in the docstring and a test in `graph/tests/` |
| Network tool | `network/scripts/`, with its usage in the docstring and a row in `network/README.md` |
| Field-day analysis | extend the existing notebook in `network/notebooks/` (West Loop days go in `west_loop.ipynb`) |
| Field captures | Drive and RustFS first; local copies in `network/data/<area>/raw/` only while needed |
| Phase notes or a plan | `network/docs/<TOPIC>_<yyyy-mm-dd>.md`, linked from the docs index and STATUS |
| Transfer manifest or inventory | `network/docs/datasets/`; run logs in `network/data/_transfers/` |

## 6. Git

- Work on a branch; `main` holds merged work. Commit only when asked.
- Commit messages: `type(scope): what changed`, e.g. `feat(network): …`, `docs(analysis): …`, `fix(curio): …`. Scopes: `analysis`, `model`, `viz`, `curio`, `network`, `data`, `docs`.
- Git tracks code, configs, docs, tests and `analysis/results/`. Model inputs, captures, intermediates, caches and tool state are ignored (see `.gitignore`).
