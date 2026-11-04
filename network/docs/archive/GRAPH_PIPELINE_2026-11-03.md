# The graph pipeline: inputs, data, transformations, outputs

Draft, 3 November 2026. The method side of the [graph paper plan](GRAPH_PAPER_PLAN_2026-11-03.md): what goes in, how it is stored, joined, aggregated and transformed, and what comes out. It names the code that exists (`network/graph/`) and the steps still to build. The walk-only inference itself (the ladder, its factor graph) is detailed in the [October plan](GRAPH_GPS_PLAN_2026-10-24.md), sections 3 to 6, and is summarised here, not repeated.

Rates and sizes below were measured on one session, D2 S1 (`2026-10-20-16-38-56-189`, 45 min, moto g 5G 2023), on 3 November, unless another source is cited.

## 1. The pipeline at a glance

```
 INPUTS                         PER SESSION                           PER STREET / AREA                    OUTPUTS
 ─────────────────────────      ──────────────────────────────        ─────────────────────────────        ──────────────────
 capture folder (raw)  ──► S0 review ─► S1 sync ─► S2 motion ─► S3 camera pose ─► S5 trajectory + walking lines ─► S6 corners, ports
                               │                    │                     ▲   (factor graph)            │
 desktop-01 workspace ─────────┼──► S4 per-frame measurements ────────────┤                            ▼
  (frames, SAM3, Whisper,      │       (curb distance, edges,             │                       S7 cells ─► S8 network ──► Tile2Net-format layers
   motion events)              │        detections on the ground)        │                            │          │
                               │                                         │ aerial term (regime C)     ▼          ▼
 Tile2Net polygons ────────────┴─────────────────────────────────────────┘ ───────────────────► S9 fusion ──► graph tables
 (regime C only)                                                                                       │
                                                                     S10 enrichment (stations, features, ports, crossings) ──► attributes
                                                                     S11 scoring against the reference (never an input) ──► tables
```

## 2. Inputs

### 2.1 One capture (a MultiSensor folder), never modified

| File | Content | Rate (D2 S1) | Used for |
|---|---|---|---|
| `video.mp4` | 1920×1080, 30 fps; stereo audio, 44.1 kHz | — | Frames, masks, transcript (via sideseeing-tools); ground motion (phase 2b) |
| `gps.csv` | UTC time, fix accuracy, latitude, longitude. No altitude, speed or bearing | 1.5 fixes/s | Absolute position |
| `sensors.three.csv` | Accelerometer (about 100 Hz), gyroscope, gravity, linear acceleration, magnetometer (about 50 Hz each); boot-clock nanoseconds and UTC | — | Steps, turns, camera pitch and roll; magnetometer unused so far |
| `sensors.three.uncalibrated.csv` | Uncalibrated gyroscope and magnetometer | — | Unused |
| `sensors.one.csv` | Barometer (about 25 Hz), ambient light (about 1.6 Hz, on change), proximity (a few readings) | — | Unused so far (exploratory, section 8) |
| `wifi.csv` | Each scan's access points: BSSID, SSID, signal level, frequency, scan time | A real scan every 7.5 s (median), logged every second; 4,027 access points in the session | Unused so far (exploratory, section 8) |
| `cell.csv` | Cell towers and signal | About 2 rows/s | Unused |
| `consumption.csv` | Battery current | 1/s | Unused |
| `metadata.json` | Phone, sensor list, settings, start and stop times of the button and the media | — | Clock alignment; phone identity |

### 2.2 Field context

- **The route plan:** `data/west_loop/plan/` (`routes.gpkg` modules, `sessions.csv`).
- **The field log:** day, session label (`D1 S1`…), collector, phone, deviations, crosswalks logged *not crossable*.
- **The collector's camera height** on the vest. Renzo's is 1.30 m; each collector is to be measured.
- **Voice:** code words and remarks, reviewed in step S0. For the network and the ramps it stays **evaluation only** (PLAN decision 14). Whether reviewed remarks may feed Level 3 is under review (plan, section 12).

### 2.3 Processed on desktop-01 (sideseeing-tools), copied to `data/<area>/workspace/`

| Product | Content |
|---|---|
| Frames | About 1 per second (17,499 frames over the 4.9 h of D1–D3); redacted copies |
| SAM3 masks | The 35 prompts in the local workspace copy's `prompt_groups.json` (PAPERS.md counts 37 on desktop-01), on every frame, plus 5 zone prompts on D1–D2 |
| Transcript | Whisper `turbo-silence`, word times |
| Motion events | Stops, turns, crossing candidates |

All of them carry `t`, seconds from the start of the video.

### 2.4 Outside sources

| Source | Role | Regime |
|---|---|---|
| Cook County 2025 orthophoto | Tile2Net's input; background for review | A, C |
| Tile2Net polygons and network | The baseline; aerial evidence for fusion | A (output), C (input) |
| City curb lines, Cook County parcels | Reference only | Never an input |
| Cook County 2022 LiDAR terrain | Reference for running slope | Never an input |
| OpenStreetMap snapshot | Route planning; a comparison map | Never a graph input |

### 2.5 What each regime may read

| | Capture and workspace | Tile2Net / orthophoto | Reference, OSM, voice |
|---|---|---|---|
| A. Tile2Net | — | ✓ | — |
| B. Walk only | ✓ | — | — |
| C. Walk + Tile2Net | ✓ | ✓ | — |

## 3. How the data are managed

**Identity:**
- A **session** is its capture folder name (`2026-10-20-16-38-56-189`), with a label (`D2 S1`), a collector and a phone.
- A **pass** is one walk of one sidewalk side in one session, for example the east side of Aberdeen from Van Buren to Madison in D2 S1.
- Graph elements get IDs that survive revisions (October plan, section 4).

**Time:** every table carries `t`, seconds from the video start. Sensor files are moved onto it through the boot clock, using the offset measured between their `timestamp_nano` and UTC. Phase 0 measured the alignment bounds.

**Space, in one place only:**
- Internal work is in metres, UTM 16N (EPSG:32616).
- Each street's ladder works in a street frame: `u` along the street, `v` across it.
- The City's and the County's data are NAD83; phone GPS is WGS 84. At Morgan they differ by about 1 m (phase 2a notes, section 4). The shift is applied by one function (`evaluate.datum_shift`) and nowhere else.
- Outputs for Tile2Net comparison are in WGS 84 (EPSG:4326), like Tile2Net's.

**Storage:**

| Tier | Where | Rule |
|---|---|---|
| Raw | Google Drive, RustFS; local copies in `data/<area>/raw/` only while needed | Never edited |
| Workspace | desktop-01; copy in `data/<area>/workspace/` | Regenerated by sideseeing-tools, not by hand |
| Derived per session | `data/<area>/derived/<session>/` | Rebuilt from raw and workspace |
| Graph runs | `data/<area>/graph/<run>/` | One folder per run, never overwritten |

**Run manifest.** Every graph run writes `manifest.json` with:
- the sessions and their input files, with hashes;
- the code commit;
- every setting;
- the regime (A, B or C);
- the split it may touch (development only, until the frozen test).

The current folders (`phase2a`, `phase2b_h130`…) predate this rule; new runs follow it.

**Splits that survive new data.** Collection continues until early or mid December. To keep the test set clean as days arrive:
- every module of the route plan is assigned to **development** or **test** in a table `splits.csv`, fixed before the module is walked or processed;
- a new day's passes inherit their module's split;
- test passes are processed through S1–S4 (checks only) and not looked at further until the frozen run.

**Adding a day:**
1. Transfer and manifest (`docs/datasets/`).
2. desktop-01 processing.
3. S1 checks.
4. Assign passes to modules, and so to splits.
5. If development, run the pipeline.
6. Add a row to STATUS.

## 4. Transformations, step by step

| Step | Input → output | Code | State |
|---|---|---|---|
| **S0. Data review** (Renzo) | Captures, transcripts, frames → reviewed inputs: corrected transcripts, excluded or flagged frames and stretches (blur, dark, redaction misses, wrong clock), each change recorded | — | Planned |
| **S1. Sync and contract** | Capture + workspace → clock offsets, alignment bounds, focal length, rotation windows (`alignment.csv`, `rotation_windows.csv`) | `contract.py`, `phase0 align` | Built |
| **S2. Motion** | Accelerometer, gyroscope, GPS → steps; runs (straight stretches) and transitions (turns, spins, crossings, stops) | `steps.py`, `runs.py` | Built |
| **S3. Camera pose** | Gravity, focal length, the collector's height → pitch and roll per frame; a projection from pixels to the ground | `ground.py` | Built; lens distortion waits for the checkerboard |
| **S4. Per-frame measurements** | Frames' masks + pose → curb distance on each side, paved edges, sidewalk just ahead; each detection's footprint placed on the ground relative to the camera | `phase2b measure` (curb, edges); detections on the ground: to build | Partly built |
| **S5. Trajectory and walking lines** | Runs, crossings, GPS, side cue, S4 distances → each pass placed on a walking line, the corrected track, the walking lines of each street (factor graph: GPS, odometry, on-line, rung, side, edges, smoothness; plus the aerial term in regime C) | `ladder.py`, `phase2 fit`, `phase2b fit`, `baselines.py`, `side_cue.py` | Built for one straight street |
| **S6. Corners and ports** | Where two streets' ladders meet: the turns and crossing ends there → a corner cell and its node; ports where crossings start and end, sized by ramp detections; the transitions the walker made | — | To build (D2's jog and corners) |
| **S7. Cells** | Walking lines + aggregated offsets (S10's stations) → sidewalk strips; crossing paths + crosswalk masks → crosswalk cells; corner cells from S6; boundaries typed (curb, building line, cut, coverage end) | — | To build |
| **S8. Network** | Cells → centrelines → edges and nodes, transitions; export in Tile2Net's format | — | To build. **One centreline rule** for our cells, Tile2Net's polygons and the reference |
| **S9. Fusion (regime C)** | Tile2Net layers + S5–S8 → matching (pass ↔ Tile2Net segment, crossing ↔ crosswalk polygon); the edits of the plan's section 4; provenance and state on every element | — | To build |
| **S10. Enrichment** | S4 per-frame values and detections + the corrected track → stations, features, port and crossing attributes, condition tags (section 5) | — | To build |
| **S11. Scoring** | Any regime's layers + the reference → the plan's metrics | `evaluate.py` (walking lines today) | To extend |

**One rule for S0: inputs and the reference stay apart.** A source that feeds the pipeline cannot also be the reference for the same quantity.
- S0 may **fix and exclude**: a wrong clock, an unusable frame, a transcript error.
- A human **label of content** (there is a ramp here) goes to the reference, not into the input. Otherwise the construction is no longer automatic (PLAN decision 2), and the evaluation becomes circular.

## 5. How observations are aggregated

**From frames to a pass.**
- Each frame's measurement (a curb distance, a width, a detection) is placed on its pass by the frame's `t` and the corrected track.
- Along the pass, values are pooled into **stations**, by default every 5 m along the walking line: robust median, spread (MAD), number of frames.
- A side that leaves the image is marked **censored** ("at least this wide"), not averaged.
- At about one frame per second and 1.3 m per second, a 5 m station gets about four frames per pass. The spacing is tuned on development data.

**From passes to an element.**
- Frames of one pass share one GPS drift and one lighting, so they are **not independent**. Each pass is one dependency group.
- An edge's value is the median over passes; its uncertainty is the spread between passes when there are two or more, and the within-pass spread, widened, when there is one.
- Repeated days add passes. They never add frames to an old pass.

**Detections to features.**
- A detection's ground position comes from its mask's footprint (the bottom of the object) projected with the frame's pose.
- Positions from consecutive frames within a few metres of each other are one object.
- The same object seen on different passes is merged by position.
- A feature records how many frames and how many passes support it, and the cell and zone it falls in. The camera's walking line is never used as the object's position.

**Promotion rules** (from observations to graph elements), with thresholds set on development data and frozen:
- **A sidewalk edge:** a pass on a walking line, with sidewalk in the video for most of its frames.
- **A crossing edge:** a walked rung (state confirmed), or a crosswalk mask over the road with no walk (state unverified).
- **A port:** the end of a walked crossing. Its ramp, tactile paving and width come from the detections there.
- **A feature:** seen in at least k frames of one pass at a consistent ground position.

**Across sources (regime C):**
- Geometry is weighted by visibility: where the video sees canopy over the sidewalk or the orthophoto cannot, the street wins; in the open, the aerial edge wins.
- Topology comes from the walk wherever it was walked.
- Two values that differ by more than their uncertainties are both kept, and the element is marked `conflicting`.

## 6. Outputs

All GeoParquet, one folder per run, with `manifest.json`.

| Table | Key columns | Level |
|---|---|---|
| `nodes` | `node_id`, geometry, kind (corner, mid-block, coverage end), cell, source, state | 0 |
| `edges` | `edge_id`, two nodes, kind (sidewalk, crossing), geometry, length, lateral uncertainty, cell, source, state | 0 |
| `cells` | `cell_id`, kind (strip, corner, crosswalk; zones as children), polygon, inner and outer bound, censored sides, level of detail | 1 |
| `boundaries` | `boundary_id`, the cells on each side, kind, state, ports (position, width, ramp, tactile paving, alignment) | 1 |
| `transitions` | `transition_id`, node, from port, to port, observed directions, state | 1 |
| `stations` | cell, distance along the centreline, total, clear and zone widths, running slope, each with spread, frames, passes, censoring | 2 |
| `features` | `feature_id`, cell, zone, kind, position along and across, frames, passes, condition tags | 2 |
| `crossings` | edge, marking, signal, duration and wait per traversal, steps | 2 |
| `associations` | observation or pass → element, supports or contradicts, method version | all |
| `tile2net/` | `polygons` and `network` in Tile2Net's layers, fields and CRS | export |

## 7. Comparing sources: the ablation matrix

Each quantity can come from several sources. Every cell below is a run scored against the same reference. This is how "GPS alone against sensors + GPS against video" is answered, quantity by quantity.

| Quantity | GPS | + steps, gyroscope | + crossings (ladder) | + video | + Wi-Fi | + aerial (Tile2Net) | Reference |
|---|---|---|---|---|---|---|---|
| Position across the street | ✓ (raw, 5-fix median) | ✓ (smoother) | ✓ | ✓ (curb distance) | exploratory (side) | ✓ | Curbs, back of sidewalk |
| Position along the street | ✓ | ✓ (steps) | — | ✓ (ground motion) | — | ✓ | Corners on the orthophoto |
| Which side a pass is on | ✓ | — | ✓ | ✓ (side cue) | exploratory | ✓ | Protocol rule, labels |
| Sidewalk width | — | — | — | ✓ | — | ✓ (polygon) | Tape, orthophoto |
| Road width | — | ✓ (steps across) | ✓ | ✓ (whole span) | — | ✓ | Curbs |
| Running slope | — | — | — | ✓ (gravity + ground lines) | barometer (exploratory) | — | Inclinometer, LiDAR |
| Ramps, tactile paving, signals | — | — | ✓ (crossing ends) | ✓ (SAM3, Project Sidewalk models) | — | weak | Video labels |

Some of these rows already exist: phase 2a and 2b compared raw GPS, the smoother, the ladder and the ladder with video (cross-street position, road width).

## 8. Exploratory sources (time-boxed)

First checks on 3 November, on D2's two sessions:

| Source | Finding | What it could give | Status |
|---|---|---|---|
| **Wi-Fi** | A real scan every 7.5 s, about one every 10 m of walking. On the north–south streets, D2 S1 walked mostly the east sidewalks and S2 the west. In the same 25 m stretch, after removing each stretch's common offset between the sessions, an access point's signal differs between the sides by a median 4.0 dB; with the side labels shuffled, 3.1 dB (all 200 shuffles ≤ 3.8 dB). 13% of pairs differ by 10 dB or more | A side cue that does not depend on the protocol or the camera; matching passes across days and collectors | **A real but modest signal on one day.** Worth a proper test. `network/scripts/wifi_side_check.py` |
| **Barometer** | Second-to-second noise about 7 cm; short-term wobble about ±0.3 m; slow drift over minutes | Level changes (stairs, ramps, bridge approaches, underpasses); long grades, checked against LiDAR | Untested on a known level change |
| **Ambient light** | About every 0.6 s, 17–5,689 lux. The camera looks out of the phone's back, so this screen-side sensor probably faces the collector's chest (to confirm on the vest) | Dusk and night flags | Low priority: the video's exposure says the same |
| **Magnetometer** | About 50 Hz | Steel above or below (under the elevated train, over bridges) | Untested |
