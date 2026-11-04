# Sidewalk network (network/)

Track 2 of the project. A collector walks every sidewalk of an area with a phone on a vest (MultiSensor: video, GPS, accelerometer, gyroscope, gravity, audio with spoken notes). From those recordings alone, without a map, we build the **passage graph**: sidewalks, crossings and corners as linked polygons (cells) and lines (edges and nodes), with every observation attached as evidence. The work aims at two papers, a West Loop + Brás **dataset** and the **graph** method ([PAPERS.md](docs/PAPERS.md)).

The collection area is **West Loop, Chicago**. River North was planned first and then dropped. Brás (São Paulo) comes from the 2025 sidewalk audit and is used only by the dataset paper.

Where things stand: [docs/STATUS.md](docs/STATUS.md). Every document: [docs/README.md](docs/README.md). Rules for agents: [AGENTS.md](../AGENTS.md).

## Layout

```text
network/
  docs/        status, plans, protocols, phase notes; datasets/ (Drive and RustFS inventories); img/; archive/
  graph/       the passage-graph package, one module per step, tests/ (pytest)
  scripts/     stand-alone tools (below)
  notebooks/   field-day analysis notebooks (local; not committed yet: their outputs show street video frames)
  data/        captures and everything derived from them (local, git-ignored; map in data/README.md)
```

## Code

**`graph/`**, run from `network/` with the sideseeing-tools venv: `../../sideseeing-tools/venv/bin/python -m graph.<module> …`. Each module's docstring gives its command line.

| Module | What it does | Plan phase |
|---|---|---|
| `contract`, `runs`, `side_cue`, `zones`, `steps`, `phase0` | The data contract: sessions and clocks, the walk cut into runs, which side the road is on, whether the masks separate a sidewalk's zones | 0 |
| `reference` (+ `trace.html`) | The scoring reference: the City's curbs checked on the 2025 orthophoto, the back of the sidewalk from Cook County parcels | 1 |
| `ladder`, `baselines`, `phase2`, `evaluate` | The two walking lines of a street fitted with its crossings, the baselines, and the score against the reference | 2a |
| `ground`, `phase2b` | The curb and the sidewalk's edges from the video; the camera's height | 2b |
| `resultmap` (+ `resultmap.html`) | One local page showing every layer over the orthophoto | — |

**`scripts/`**:

| Script | What it does | Environment |
|---|---|---|
| `routes.py <area>` | Route plan from OSM sidewalks and crossings: one out-and-back module per street, field cards | `.venv`, from the repo root |
| `route_methods.py <area>` | Compares the module plan with CPP, RPP and CARP routes | `.venv` |
| `routing_example.py` | The worked-example figure of [ROUTING_WORKFLOW.md](docs/ROUTING_WORKFLOW.md) | `.venv` |
| `transcribe.py <raw session>` | Whisper transcript with word times, written to the area's `derived/` | sideseeing-tools |
| `build_pilot_dashboard.py` | sideseeing-tools dashboard for pilot 1 | sideseeing-tools |
| `drive.sh mount\|unmount\|status` | Mounts Google Drive read-only at `~/gdrive`, where the West Loop captures live | — |
| `transfer_bras.py` (+ test) | Resumable Brás copy from Drive to RustFS; its run record is in `data/_transfers/bras/` | `python3` |

## Where the data lives

- **Originals:** Google Drive (`IC/Sideseeing/UIC/data/west_loop`, mounted by `scripts/drive.sh`) and the RustFS `sideseeing` bucket (`chicago/west-loop/`, `sao-paulo/bras/`). The inventories are in [docs/datasets/](docs/datasets/README.md).
- **Local working copies:** `data/`, described in [data/README.md](data/README.md).
- **Heavy processing** (frames, SAM3, redaction, Whisper, motion): sideseeing-tools on desktop-01; its workspace is copied into `data/<area>/workspace/`.
