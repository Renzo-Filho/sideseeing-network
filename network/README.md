# Sidewalk network (network/)

Track 2 of the project. A collector walks every sidewalk of an area with a phone on a vest (MultiSensor: video, GPS, accelerometer, gyroscope, gravity, audio with spoken notes). From those recordings alone, without a map, we build the **pedestrian graph**: sidewalks, crossings and corners as linked polygons (cells) and lines (edges and nodes), with every observation attached as evidence. The work aims at two papers, a West Loop + Brás **dataset** and the **graph** method ([research plan](docs/RESEARCH_PLAN.md)).

The collection area is **West Loop, Chicago**. River North was planned first and then dropped. Brás (São Paulo) comes from the 2025 sidewalk audit and is used only by the dataset paper.

Where things stand: [docs/STATUS.md](docs/STATUS.md). Every document: [docs/README.md](docs/README.md). Rules for agents: [AGENTS.md](../AGENTS.md).

## Layout

```text
network/
  pyproject.toml  the walk2net package (working name)
  walk2net/       the pedestrian-graph package: stages/ (the pipeline's steps), evaluate/, baselines, plan, resultmap
  areas/          area configs (TOML): streets, projection, planner settings, reference sources
  protocols/      protocol definitions (TOML): which side of the walker the road is on
  experiments/    the drivers that produced docs/RESULTS.md
  tests/          the package's tests (pytest; the Morgan regression with -m slow)
  scripts/        operations: Drive mount, transfers, transcription
  docs/           status, research plan, method, field protocol, results, architecture; datasets/; img/; archive/
  notebooks/      field-day analysis notebooks (local; not committed yet: their outputs show street video frames)
  data/           captures and everything derived from them (local, git-ignored; map in data/README.md)
```

## Code

The software design is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Everything below runs from `network/` with the sideseeing-tools venv, where the package is installed once with `pip install -e network/` (from the repository root). Each module's docstring gives its command line; tests: `python -m pytest -q`.

**`walk2net/`** (`python -m walk2net.<module> …`):

| Module | What it does | Phase in RESULTS.md |
|---|---|---|
| `stages/sync`, `stages/walk`, `stages/side_cue`, `stages/zones` | The data contract (sessions and clocks), steps and the walk cut into runs, which side the road is on, whether the masks separate a sidewalk's zones | 0 |
| `stages/ladder`, `baselines` | The two walking lines of a street fitted with its crossings; the baselines | 2a |
| `stages/ground` | The camera and the ground: the curb and the sidewalk's edges from the video; the camera's height | 2b |
| `evaluate/reference` (+ `trace.html`) | The scoring reference: the City's curbs checked on the 2025 orthophoto, the back of the sidewalk from Cook County parcels | 2a §4 (reference) |
| `evaluate/score` | The walking lines scored against the reference | 2a, 2b |
| `config`, `fieldlog` | The area and protocol configs; the field log, which names each session's protocol | — |
| `plan` | Route plan from OSM sidewalks and crossings under a protocol (`python -m walk2net.plan west_loop briefing-2026-11`): one out-and-back leg per sidewalk side, route cards | — |
| `resultmap` (+ `resultmap.html`) | One local page showing every layer over the orthophoto | — |

**`experiments/`** (`python -m experiments.<name> …`): `phase0`, `phase2a`, `phase2b`, the runs behind RESULTS.md; `wifi_side_check`, the exploratory Wi-Fi side test ([METHOD.md](docs/METHOD.md) §11).

**`scripts/`**:

| Script | What it does | Environment |
|---|---|---|
| `transcribe.py <raw session>` | Whisper transcript with word times, written to the area's `derived/` | sideseeing-tools |
| `drive.sh mount\|unmount\|status` | Mounts Google Drive read-only at `~/gdrive`, where the West Loop captures live | — |
| `transfer_bras.py` (+ test) | Resumable Brás copy from Drive to RustFS; its run record is in `data/_transfers/bras/` | `python3` |

## Where the data lives

- **Originals:** Google Drive (`IC/Sideseeing/UIC/data/west_loop`, mounted by `scripts/drive.sh`) and the RustFS `sideseeing` bucket (`chicago/west-loop/`, `sao-paulo/bras/`). The inventories are in [docs/datasets/](docs/datasets/README.md).
- **Local working copies:** `data/`, described in [data/README.md](data/README.md).
- **Heavy processing** (frames, SAM3, redaction, Whisper, motion): sideseeing-tools on desktop-01; its workspace is copied into `data/<area>/workspace/`.
