# Software architecture

Agreed on 4 November 2026 (drafted the same day as the architecture plan). How the method becomes software that **anyone who collects data with our protocol can run, reproducibly, on their own area**: one installable package in this repository, `walk2net`. Its decisions are 33 and 34 in [RESEARCH_PLAN §5](RESEARCH_PLAN.md#5-decisions); what has been built so far is dated in [STATUS.md](STATUS.md).

The scientific method is in [METHOD.md](METHOD.md); this page is about the code that implements it.

## 1. Decisions

| Question | Answer |
|---|---|
| Who runs it | Anyone who collects with our protocol, on any area. It must be reproducible and scale with more sessions, streets, collectors and areas |
| Where it lives | This repository, as a package under `network/` |
| Name | `walk2net` for now (the paper's working title); may change later |
| The graph object | **`PedestrianGraph`** ("pedestrian graph" in prose; it was "passage graph" before 4 November) |
| The heavy processing (frames, SAM3, redaction, Whisper) | Stays in sideseeing-tools, on a GPU machine. `walk2net` **only reads its workspace**; it does not launch it |

## 2. What "anyone, any area, reproducibly" requires

| # | Requirement | What it means in code | Before the package (4 November) |
|---|---|---|---|
| R1 | One installation | `pip install -e network/` in one environment, with sideseeing-tools as a dependency | Two environments: `.venv` for scripts, sideseeing-tools' venv for `graph/` |
| R2 | Documented inputs | A capture folder, the sideseeing-tools workspace, a **field log** (CSV with a fixed set of columns), an **area config**, and the **protocol version** of each session | Inputs are implicit: paths on the command line, knowledge in the docs |
| R3 | No place written into the code | The street axis, the projection, the datum shift and the reference sources come from the area config or are derived (UTM zone from the area's location) | `reference.MORGAN`, `UTM = 32616`, the NAD83 shift for Chicago, `data/west_loop/...` paths |
| R4 | Reproducible runs | A frozen config and a `manifest.json` per run: inputs with hashes, code commit, every setting, regime, split | Output folders without manifest (`phase2a`, `phase2b_h130`…) |
| R5 | Scales | Per-session steps run independently, in parallel, and are cached by a hash of their code, inputs and settings, so a new day computes only its new sessions. Outputs are GeoParquet, split by session and street | Each phase recomputes what it needs |
| R6 | A stable surface | A command line and a small Python API; everything else internal. A schema version in every output | `python -m graph.<phase>` commands, one per phase |
| R7 | Documentation | A user guide (collect → process → build → score), this developer guide, a schema reference | The method is documented; the software is not |
| R8 | Research integrity by construction | Construction never imports the evaluation code; the test split cannot be touched without a frozen config; voice is never a construction input | Kept by discipline and AGENTS.md rules |

## 3. The protocol is data

The pipeline relies on the protocol: the corner ritual makes the ladder's rungs; the walking direction gives the expected side of the road. Today that knowledge is spread through the code as constants. For example `side_cue.PROTOCOL_ROAD_SIDE` says the road is on the walker's **right** on east–west streets: true under the October rules, wrong under the briefing, where it is always on the left.

So each protocol is a small definition file in `network/protocols/`, and each session names its protocol in the field log (`data/<area>/field_log.csv`, read by `walk2net.fieldlog`). A protocol file holds one setting today: the side of the walker the road is on, per street axis (`road_side`). Every protocol walks the out leg north or east, so the side of each leg follows from it. Fields are added when code reads them.

| Protocol | Sessions | Main differences |
|---|---|---|
| `oct-2026` | Up to the briefing (at least D1–D3) | Modules; east–west streets north side first; Pilot 2 vocabulary |
| `briefing-2026-11` | From the briefing on | One street per day; road always on the left; the 270°/180° corner ritual; the briefing's vocabulary |
| `free-route` | The free test routes (decision 26) | No protocol expectation applies |

## 4. The shape: tables in the middle, a few classes at the edges

The graph will hold thousands of nodes, edges, cells and stations per area. They are stored as **tables with a schema** (GeoDataFrames, saved as GeoParquet), the tables of [METHOD §8](METHOD.md#8-data-structure-and-outputs), not as one Python object per node. Each step is a **function**: tables in, tables out, no file paths, no command line. Classes are used only where state and behaviour belong together:

| Class | Holds | Does |
|---|---|---|
| `Session` | One capture on one time base: the sideseeing-tools workspace, the raw paths, its field-log row (collector, phone, camera height, protocol) | Gives GPS, motion, frames, masks and clock offsets on the video clock |
| `PedestrianGraph` | The tables: nodes, edges, cells, boundaries, transitions, stations, features, crossings, associations | `validate()` (every edge has its cell, ports lie on boundaries, IDs are unique and stable), `save()` and `load()`, `to_tile2net()`, `to_osm()` |
| `Area`, `Street`, `Protocol` (`config.py`); `RunConfig` (M3) | Frozen settings, read from TOML files with Python's own `tomllib` (no extra dependency) | Hashed into the manifest (M3) |
| `Camera`, `Ladder`, `Frame` | Already exist (`stages/ground.py`, `stages/ladder.py`) | Unchanged |

No class hierarchy for steps, no plugin registry, no database.

## 5. Layout

A layer becomes a folder when it holds more than one module.

```
network/
  pyproject.toml            the walk2net package, installed into the sideseeing-tools venv: pip install -e network/
  walk2net/
    __init__.py             the package map; later the public API (Session, PedestrianGraph, build, score, export)
    stages/                 sync (S1), walk (S2: steps and runs), side_cue and zones (checks), ground (S3-S4),
                            ladder (S5); then corners, cells, network, fusion, enrich as they are built
    baselines.py            raw GPS and the steps smoother (a folder once the protocol rule and Tile2Net runner join)
    evaluate/               reference.py (+ trace.html), score.py; never imported by stages/
    plan.py                 field planning: streets and legs from OpenStreetMap, route cards
    resultmap.py (+ .html)  the local result map
    config.py               Area, Street, Protocol, read from areas/ and protocols/; RunConfig in M3
    fieldlog.py             the field log: one row per recording, each session's protocol
    io/                     M3: captures and workspace (Session), reference sources, Tile2Net layers; fieldlog moves here
    model/                  M3: schema.py (one contract per table), graph.py (PedestrianGraph), ids.py
    run.py, cli.py          M3: the runner (config -> steps -> cache -> outputs + manifest) and the walk2net command
  areas/, protocols/        area configs and protocol definitions (TOML)
  experiments/              phase0, phase2a, phase2b, wifi_side_check: the drivers behind RESULTS.md
  tests/                    unit tests on synthetic data, configs, the layout rule, the Morgan regression (-m slow)
  scripts/                  operations only: drive.sh, transfer_bras.py (+ test), transcribe.py
```

Run from `network/` with the sideseeing-tools venv: `python -m walk2net.<module>` or `python -m experiments.<name>`; each module's docstring gives its command line. Tests: `python -m pytest -q`.

**Command line, from M3** (the stable surface):

| Command | Does |
|---|---|
| `walk2net plan AREA` | Streets and legs for an area, under the current protocol |
| `walk2net check SESSION…` | The data contract: clocks, streams, field log, protocol (S1) |
| `walk2net build CONFIG` | Runs the steps for the sessions and regime in the config; writes the graph and the manifest |
| `walk2net score RUN REFERENCE` | Scores any run, ours or Tile2Net's, against a reference |
| `walk2net export RUN --format tile2net\|osm` | Writes the graph in another format |

## 6. Where each piece went

| Before | Now | Step |
|---|---|---|
| `graph/contract.py` | `stages/sync.py` | M1, moved |
| `graph/runs.py`, `steps.py` | `stages/walk.py` | M1, merged. Named `walk`, not `motion`: `motion` is a variable name in the callers |
| `graph/side_cue.py`, `zones.py` | `stages/` | M1, moved. M2: the protocol constant gave way to the session's protocol |
| `graph/ground.py` | `stages/ground.py` | M1, moved whole: the camera and its measures are one small unit. Split into pose and measure if it grows |
| `graph/ladder.py` | `stages/ladder.py` | M1, moved |
| `graph/baselines.py` | `baselines.py` | M1, moved |
| `graph/reference.py`, `evaluate.py`, `trace.html` | `evaluate/reference.py`, `evaluate/score.py`, `evaluate/trace.html` | M1, moved. M2: the Morgan axis, the UTM zone, the datum shift and the Chicago sources moved to the area config; reference files are named after the street. `trace.html` still loads Morgan's files only |
| `graph/phase0.py`, `phase2.py`, `phase2b.py` | `experiments/phase0.py`, `phase2a.py`, `phase2b.py` | M1, moved whole. Their method logic (for example the session ladder of `phase2a`, which `phase2b` reuses) moves into `stages/` when the runner replaces them (M3) |
| `graph/resultmap.py` (+ html) | `resultmap.py` | M1, moved |
| `graph/tests/` | `tests/` | M1, moved; `test_layout.py` added |
| `scripts/routes.py` | `plan.py` | M1, moved. M2: the `AREAS` dict became `areas/west_loop.toml`; the legs' directions follow the protocol named on the command line |
| Settings written in the code: `AREAS`, `MORGAN`, `UTM`, `EPOCH`, the NAD83 datum, `PROTOCOL_ROAD_SIDE`, phase 0's `AXES` | `areas/west_loop.toml`, `protocols/*.toml` | M2. The projection is derived from the area's location (`config.utm_epsg`) |
| `scripts/route_methods.py`, `routing_example.py` | Dropped | M1. The tour plans (CPP, RPP, CARP) are a kind of walk the protocol does not use. Git history and the archived [routing workflow](archive/ROUTING_WORKFLOW.md) keep them |
| `scripts/wifi_side_check.py` | `experiments/` | M1, moved (exploratory, time-boxed) |
| `scripts/transcribe.py`, `transfer_bras.py`, `drive.sh` | `scripts/` | Unchanged: operations, outside the package |

## 7. Tests that keep it honest

| Test | Checks |
|---|---|
| Unit tests on synthetic data | Each step's logic |
| Configs and field log (`tests/test_config.py`) | The projection from the location; protocols' road and leg sides; a wrong field log (misspelt column, missing protocol, unknown protocol, a session twice) is refused |
| Layout rule (`tests/test_layout.py`) | `stages/` never imports `evaluate/` (decision 2, AGENTS.md rule 12). Later also `model/` and `run.py` |
| Schema contracts (M3) | Every table a step writes matches its contract; `PedestrianGraph.validate()` on built graphs |
| Split guard (M3) | The runner refuses test sessions unless the config is frozen and its hash recorded (decision 18) |
| Regression on Morgan (`tests/test_regression.py`; `python -m pytest -m slow`, about a minute, local data) | The phase 2b fit at 1.30 m, re-run from its stored inputs and scored, equals the published `phase2b_h130` value for value (fit summary, evaluation, walking lines): the numbers of [RESULTS](RESULTS.md) 2b §7. A 1 cm change of the camera height makes it fail. It is how each later step proves nothing changed |

## 8. Migration, step by step

Each step leaves the tests green and the RESULTS numbers reproducible. No step changes what the method computes.

| Step | Work | Done when |
|---|---|---|
| **M1. Package** | `network/pyproject.toml`; `graph/` becomes `walk2net/` (section 5); phase drivers to `experiments/`; tests moved; one environment; `route_methods.py` dropped | `pip install -e network/` works; all tests pass; the docs' commands updated |
| **M2. Configs and protocols** | `AreaConfig`, `Protocol`, the field-log columns; Morgan's axis, the UTM zone, the datum shift and the data paths leave the code; `side_cue` reads the session's protocol; the Morgan regression test | No place or path in `stages/`; the regression reproduces RESULTS 2b §7 |
| **M3. Contract and runner** | `model/schema.py` from METHOD §8 (adds `pyarrow` for GeoParquet, not yet in the venv); `PedestrianGraph`; `Session` (with the field log's camera height; the lens's focal length, `ground.F_PX`, measured on one phone, becomes per session); the runner with cache and manifest; the split guard; the experiment drivers' method logic into `stages/`; `walk2net check` and `build` for S1–S5 | Schema and guard tests pass; a run writes its manifest; a second run of the same config reuses the cache |
| **M4. Scorer (research plan P3)** | `evaluate/` reads Tile2Net-format layers and computes Gate 1's metrics | Tile2Net's first scores on the development blocks |
| **M5 on. New steps** | S6 corners, S7 cells, S8 network, S9 fusion, S10 enrichment (P4, P5, P7), each written into `stages/` against the schema | Each step's own tests and the plan's gates |
| **Docs** | The user guide, once M3 gives a working `build` | Someone else runs `plan`, `check` and `build` on one session from the guide alone |

M1 to M3 can run alongside the research plan's P1 (Tile2Net) and P2 (reference). M4 is P3 itself.

## 9. Open questions

1. **sideseeing-tools as a dependency:** installed from the sibling folder (as now), or pinned to a git commit for reproducibility?
2. **The field log:** a CSV filled by hand after each day, or generated from the capture folders plus a short form? It now carries the protocol version, so it becomes an input, not just a record.
3. **The day's briefing:** the route section of the 4 November briefing (street, start and end, length, map strips) could be generated by `walk2net plan`. Were those strips made by hand?
