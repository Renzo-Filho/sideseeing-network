# Method: how the graph is built

Merged on 4 November 2026 from the [graph pipeline](archive/GRAPH_PIPELINE_2026-11-03.md) (3 November), sections 3 to 6 of the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md) (24 October) and the [plain-English explanation](archive/GRAPH_WORK_EXPLAINED_2026-10-30.md) (30 October). What goes in, how it is stored, joined, aggregated and transformed, and what comes out. It names the code that exists (`network/walk2net/`, laid out in [ARCHITECTURE.md](ARCHITECTURE.md)) and the steps still to build. Why the graph is built this way, and how it is scored, is in [RESEARCH_PLAN.md](RESEARCH_PLAN.md); results are in [RESULTS.md](RESULTS.md).

Rates and sizes below were measured on one session, D2 S1 (`2026-10-20-16-38-56-189`, 45 min, moto g 5G 2023), on 3 November, unless another source is cited.

## 1. In plain words

A person walks the streets wearing a phone on a vest. The phone records video, GPS and motion sensors. From that alone, with no map, we want a map of where people can walk: the sidewalks with their width and obstacles, the crossings, the corners that join them, and which moves each corner allows.

The hard part is that phone GPS is off by several metres: enough to put the walker on the wrong side of the street, or in the road. So the work has two halves:
1. **Correct the walk:** work out where on the street the walker really was (section 5). Done on Morgan ([RESULTS](RESULTS.md)).
2. **Build the graph on top of it:** nodes, edges, sidewalk polygons and the moves between them (sections 6 and 8). Not started.

**Every source contributes something different; none is enough alone:**

| Source | What it tells us | Where it goes in the graph |
|---|---|---|
| GPS | Roughly where the walk happened (± several metres) | Anchors the street's position; corrected by everything else |
| Accelerometer (steps) | Distance walked, step by step | Edge lengths, crossing lengths, the distance between walking lines |
| Gyroscope (turns) | Direction and every turn | Which sidewalk each stretch is on; corners; which moves were made |
| Gravity sensor | The camera's tilt at every moment | Distances on the ground from the video; later, slope |
| Video + SAM3 masks | Curb, sidewalk, crosswalk, ramps, tactile paving, poles, trees, obstacles | Polygon boundaries, width, ports, features placed in the right cell |
| Audio transcripts | What the collector said | Evaluation only for the network and ramps (decision 14); exploratory for Level 3 |
| Aerial photo (regime C) | The view from above | Fixes the shift both walking lines share; a second source for outlines |

**The merging rule.** Everything is joined through **time and the corrected track**. Each frame, detection, step and spoken word has a timestamp; the corrected track says where the walker was at that time, on which walking line, how far along the street. That places the observation in the right polygon, at the right distance along its edge. Each graph element keeps the list of observations that support or contradict it.

## 2. The pipeline at a glance

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

## 3. Inputs

### 3.1 One capture (a MultiSensor folder), never modified

| File | Content | Rate (D2 S1) | Used for |
|---|---|---|---|
| `video.mp4` | 1920×1080, 30 fps; stereo audio, 44.1 kHz | — | Frames, masks, transcript (via sideseeing-tools); ground motion |
| `gps.csv` | UTC time, fix accuracy, latitude, longitude. No altitude, speed or bearing | 1.5 fixes/s | Absolute position |
| `sensors.three.csv` | Accelerometer (about 100 Hz), gyroscope, gravity, linear acceleration, magnetometer (about 50 Hz each); boot-clock nanoseconds and UTC | — | Steps, turns, camera pitch and roll; magnetometer unused so far |
| `sensors.three.uncalibrated.csv` | Uncalibrated gyroscope and magnetometer | — | Unused |
| `sensors.one.csv` | Barometer (about 25 Hz), ambient light (about 1.6 Hz, on change), proximity | — | Exploratory (section 11) |
| `wifi.csv` | Each scan's access points: BSSID, SSID, signal level, frequency, scan time | A real scan every 7.5 s (median), logged every second; 4,027 access points | Exploratory (section 11) |
| `cell.csv` | Cell towers and signal | About 2 rows/s | Unused |
| `consumption.csv` | Battery current | 1/s | Unused |
| `metadata.json` | Phone, sensor list, settings, start and stop times | — | Clock alignment; phone identity |

### 3.2 Field context

- **The route plan:** `data/west_loop/plan/` (`routes.gpkg` modules, `sessions.csv`).
- **The field log** ([FIELD_PROTOCOL §4](FIELD_PROTOCOL.md#4-before-and-after-each-field-day)), `data/<area>/field_log.csv`: per session its label (`D1 S1`…), **its protocol**, leg, collector, phone, camera height and deviations, among them crosswalks not crossed. The protocol tells the code which side of the road to expect.
- **The area config** (`areas/<area>.toml`) and **the protocol definitions** (`protocols/`): the area's streets, projection and reference sources; each protocol's road side ([ARCHITECTURE §3](ARCHITECTURE.md#3-the-protocol-is-data)).
- **The collector's camera height** on the vest. Renzo's is 1.30 m; each collector is to be measured.
- **Voice:** spoken words and remarks, reviewed in step S0. For the network and the ramps they stay **evaluation only** (decision 14).

### 3.3 Processed on desktop-01 (sideseeing-tools), copied to `data/<area>/workspace/`

| Product | Content |
|---|---|
| Frames | About 1 per second (17,499 frames over the 4.9 h of D1–D3); redacted copies |
| SAM3 masks | The 35 prompts in the local workspace copy's `prompt_groups.json` (37 counted on desktop-01), on every frame, plus 5 zone prompts on D1–D2 |
| Transcript | Whisper `turbo-silence`, word times |
| Motion events | Stops, turns, crossing candidates |

All of them carry `t`, seconds from the start of the video.

### 3.4 Outside sources

| Source | Role | Regime |
|---|---|---|
| Cook County 2025 orthophoto | Tile2Net's input; background for review | A, C |
| Tile2Net polygons and network | The baseline; aerial evidence for fusion | A (output), C (input) |
| City curb lines, Cook County parcels | Reference only | Never an input |
| Cook County 2022 LiDAR terrain | Reference for running slope | Never an input |
| OpenStreetMap snapshot | Route planning; a comparison map | Never a graph input (decision 15) |

### 3.5 What each regime may read

| | Capture and workspace | Tile2Net / orthophoto | Reference, OSM, voice |
|---|---|---|---|
| A. Tile2Net | — | ✓ | — |
| B. Walk only | ✓ | — | — |
| C. Walk + Tile2Net | ✓ | ✓ | — |

## 4. How the data are managed

**Identity:**
- A **session** is its capture folder name (`2026-10-20-16-38-56-189`), with a label (`D2 S1`), a collector and a phone.
- A **pass** is one walk of one sidewalk side in one session, for example the east side of Aberdeen from Van Buren to Madison in D2 S1.
- Graph elements get IDs that survive revisions.

**Time:** every table carries `t`, seconds from the video start. Sensor files are moved onto it through the boot clock, using the offset measured between their `timestamp_nano` and UTC. Phase 0 measured the alignment bounds ([RESULTS](RESULTS.md#phase-0-results-sessions-clocks-runs-side-cue-and-zones) 0 §2).

**Space, in one place only:**
- Internal work is in metres, UTM 16N (EPSG:32616).
- Each street's ladder works in a street frame: `u` along the street, `v` across it.
- The City's and the County's data are NAD83; phone GPS is WGS 84. At Morgan they differ by about 1 m ([RESULTS](RESULTS.md#phase-2a-notes-the-ladder-on-morgan) 2a §4). The shift is applied by one function (`walk2net.evaluate.score.datum_shift`) and nowhere else.
- Outputs for Tile2Net comparison are in WGS 84 (EPSG:4326), like Tile2Net's.

**Storage:**

| Tier | Where | Rule |
|---|---|---|
| Raw | Google Drive, RustFS; local copies in `data/<area>/raw/` only while needed | Never edited |
| Workspace | desktop-01; copy in `data/<area>/workspace/` | Regenerated by sideseeing-tools, not by hand |
| Derived per session | `data/<area>/derived/<session>/` | Rebuilt from raw and workspace |
| Graph runs | `data/<area>/graph/<run>/` | One folder per run, never overwritten |

**Run manifest.** Every graph run writes `manifest.json` with: the sessions and their input files, with hashes; the code commit; every setting; the regime (A, B or C); the split it may touch (development only, until the frozen test). The current folders (`phase2a`, `phase2b_h130`…) predate this rule; new runs follow it.

**Splits that survive new data.** Collection continues until early or mid December. To keep the test set clean as days arrive:
- every module of the route plan (in practice, a street) is assigned to **development** or **test** in `splits.csv`, fixed before it is walked or processed;
- a new day's passes inherit their module's split;
- test passes are processed through S1–S4 (checks only) and not looked at further until the frozen run.

**Adding a day:**
1. Transfer and manifest (`docs/datasets/`).
2. desktop-01 processing.
3. S1 checks.
4. Assign passes to modules, and so to splits.
5. If development, run the pipeline.
6. Add a line to STATUS.

## 5. The walk-only inference: the ladder

GPS cannot tell the two sidewalks of a street apart, but **the walk itself measures the street**:
- the gyroscope gives exact times and relative headings for every turn, so the walk splits into straight **runs** separated by **transitions**;
- a crossing of the walked street is a short run roughly perpendicular to the runs around it. Its steps give the distance between the two sidewalks' walking lines, and its ends are the two **curb ports**;
- under the protocol each crosswalk over the walked street is crossed there and back ([FIELD_PROTOCOL §1](FIELD_PROTOCOL.md#1-the-protocol)), so every crossing is a repeated, timed observation of the same **rung**;
- the video says which side the road is on, and confirms crossing ends (tactile paving, crosswalk);
- GPS supplies absolute position, with a bias towards the street's middle.

A two-sided street is then a **ladder**: two rails (the walking lines) joined by rungs (the crosswalks), whose number, order, timing and length come from motion, and whose absolute placement comes from GPS. Intersections are where ladders meet. Fitting the ladder and the trajectory together corrects the GPS (each run is placed on its rail) and produces the graph's skeleton with no external map.

```
            rung (crosswalk)        rung
   west  ───●──────────────────────●───────────●───  rail = walking line, west sidewalk
            │  ↕ W (from crossing   │
            │    steps)             │
   east  ───●──────────────────────●───────────●───  rail = walking line, east sidewalk
            port                    port
   runs:  ══ northbound on east ══►       ◄══ southbound on west ══
```

**How the current model works** (phase 2a and 2b, `walk2net/stages/ladder.py`):
- **Splitting the walk:** the gyroscope cuts it into straight runs between turns; a run across the street is a crossing.
- **Heading:** each run's direction comes from adding up the turns, rounded to quarter turns (the grid).
- **Side:** each run's sidewalk comes from the crossings. After crossing eastward, you are on the east sidewalk. No GPS is needed for this.
- **Unknowns:** a street centre line that may bend gently, two parallel walking lines either side of it, each recording's step length, how far GPS is pulled towards the street's middle, and where each run starts.
- **Fit:** a robust least-squares problem (a factor graph):

| Term | Ties | Evidence | Built |
|---|---|---|---|
| GPS | Each state to its fix, robust loss, a lateral bias towards the centre | GPS | Yes |
| Odometry | Consecutive states: steps × step length, heading change | Accelerometer, gyroscope | Yes |
| On-line | The states of a run lie on its walking line | Assignment | Yes |
| Rung | A crossing ends on the far walking line; repeats share their ports | Crossing candidates | Yes (phase 2a, 26 October) |
| Side | The road is left or right of the camera | SAM3 masks | Side cue tested in phase 0 |
| Edges | The two lines are road width + both curb distances apart, measured from the video | Projected masks, steps on the road | Yes (phase 2b) |
| Smoothness | Lines bend only where a turn was observed | Turns | Yes |
| Aerial (regime C only) | The video's curb distance meets Tile2Net's curb | Tile2Net polygons | To build (P5) |

GPS fixes that are far off count much less than nearby ones, so one wild fix cannot drag a line across the street. `scipy.optimize.least_squares` is enough for one street; GTSAM if it grows.

**Baselines, on the same sessions:** raw GPS; the 5-fix median the viewer shows; a GPS + steps (Kalman/RTS) smoother; multi-trace clustering (Kasemsuppakorn and Karimi 2013); the **protocol rule** (the walking direction alone gives the side); and the notebook's OSM-assisted track, as a map-assisted reference only (decision 15). The smoother uses the same steps and turns as the ladder. What it lacks is the knowledge that the walk runs on two parallel sidewalks joined by crossings.

## 6. Transformations, step by step

| Step | Input → output | Code | State |
|---|---|---|---|
| **S0. Data review** (Renzo) | Captures, transcripts, frames → reviewed inputs: corrected transcripts, excluded or flagged frames and stretches (blur, dark, redaction misses, wrong clock), each change recorded | — | Planned |
| **S1. Sync and contract** | Capture + workspace → clock offsets, alignment bounds, focal length, rotation windows (`alignment.csv`, `rotation_windows.csv`) | `stages/sync.py`; `experiments.phase0 align` | Built |
| **S2. Motion** | Accelerometer, gyroscope, GPS → steps; runs and transitions (turns, spins, crossings, stops) | `stages/walk.py` | Built |
| **S3. Camera pose** | Gravity, focal length, the collector's height → pitch and roll per frame; a projection from pixels to the ground | `stages/ground.py` | Built; lens distortion waits for the checkerboard |
| **S4. Per-frame measurements** | Masks + pose → curb distance on each side, paved edges, sidewalk just ahead; each detection's footprint on the ground | `experiments.phase2b measure` (curb, edges); detections on the ground: to build | Partly built |
| **S5. Trajectory and walking lines** | Runs, crossings, GPS, side cue, S4 distances → each pass on a walking line, the corrected track (section 5) | `stages/ladder.py`, `baselines.py`, `stages/side_cue.py`; `experiments.phase2a fit`, `experiments.phase2b fit` | Built for one straight street |
| **S6. Corners and ports** | Where two streets' ladders meet: the turns and crossing ends there → a corner cell and its node; ports where crossings start and end, sized by ramp detections; the transitions walked | — | To build (D2's jog and corners) |
| **S7. Cells** | Walking lines + aggregated offsets (S10's stations) → sidewalk strips; crossing paths + crosswalk masks → crosswalk cells; corner cells from S6; boundaries typed (curb, building line, cut, coverage end) | — | To build |
| **S8. Network** | Cells → centrelines → edges and nodes, transitions; export in Tile2Net's format | — | To build. **One centreline rule** for our cells, Tile2Net's polygons and the reference |
| **S9. Fusion (regime C)** | Tile2Net layers + S5–S8 → matching, the edits of [RESEARCH_PLAN §2.4](RESEARCH_PLAN.md#24-methods-compared), provenance and state on every element | — | To build |
| **S10. Enrichment** | S4 values and detections + the corrected track → stations, features, port and crossing attributes, condition tags (section 9) | — | To build |
| **S11. Scoring** | Any regime's layers + the reference → the plan's metrics | `evaluate/score.py` (walking lines today) | To extend |

**One rule for S0: inputs and the reference stay apart.** S0 may **fix and exclude** (a wrong clock, an unusable frame, a transcript error). A human **label of content** ("there is a ramp here") goes to the reference, not into the input; otherwise construction is no longer automatic (decision 2) and the evaluation becomes circular. Still to agree ([RESEARCH_PLAN §6](RESEARCH_PLAN.md#6-open-questions), question 3).

**From walking lines to cells.** The rails are where the collector walked, not the graph's edges. In every frame, the sidewalk mask projected onto the ground gives the distance from the walking line to the sidewalk's two edges, curb side and building side; the obstacle and vegetation masks give the lines between zones. Placed along the rail, those distances become the strip's boundaries, and the strip's centreline becomes the edge. Once a strip exists, its edge moves from "where the walker went" to "the middle of the sidewalk". The crosswalk mask does the same across the road, and the turns at each corner sweep it from several directions.

## 7. Width, length, slope and zones

| Quantity | How | What limits it |
|---|---|---|
| **Length** | Along each edge between its nodes, from the corrected track and step counts; the video marks where a segment starts and ends | Mostly solved by the graph itself |
| **Zones** | Across each strip from the building line: frontage (up to clear pavement), furniture or parkway (from the curb to the line of poles, trees, tree pits, grass), through (between them), following NACTO's sidewalk zones | Bare-concrete furniture zones are marked only by sparse poles; frontage is often empty. If the masks cannot separate zones, the strip stays at level 1 |
| **Width** | Total width spans all zones; clear width is the through zone minus obstacles. Mask edges 2–5 m ahead projected onto the ground; a robust median per stretch | Camera pitch: about 4–6% width error per degree at these distances. Sidewalks wider than the view are censored ("at least"). Mask edges at grass, driveway aprons and shadows |
| **Running slope** (limit about 5%, ramps 8.33%) | The angle between ground lines along the walk and the horizontal given by gravity (camera and sensor are rigid together, so the mount drops out), averaged over a stretch | The gravity sensor while walking; a constant camera-to-sensor angle, calibrated once on level ground. The barometer drifts and GPS altitude is too noisy for slope |
| **Cross slope** (limit 2%, about 1.1°) | The same with the slab joints across the walk | Needs about 0.5° overall. Exploratory |

**What the projection needs:**
- **The lens.** Recordings are 1920×1080 at 30 fps. The turns give a horizontal focal length of about 1460 px ([RESULTS](RESULTS.md#phase-0-results-sessions-clocks-runs-side-cue-and-zones) 0); a checkerboard video per phone would add the distortion and show whether stabilisation crops.
- **The camera height.** It sets the scale of every width and offset (a 5 cm error is about 4% of a width). Measured on the vest: 1.30 m for Renzo (decision 17). The ground's apparent motion and the tactile paving (at least 610 mm deep by rule) are independent checks.
- **Pitch and roll** per frame from the gravity stream.

## 8. Data structure and outputs

**Two linked views of the same space** (decision 3). The **cells** split the walkable space: one strip per sidewalk side per block, one cell per corner, one per crosswalk, with zones and features inside. The **graph** is nodes and edges:

```
 ┌─────────┬────────────────────────────────┬─────────┐  building line
 │         │ frontage zone                  │         │
 │    ●════╪═══════ edge = centreline ══════╪════●    │  ● node, in its corner cell
 │    ║    │ through zone   · · walking line│    ║    │
 │    ║    │ furniture zone   ▪ pole ▪ tree │    ║    │
 └──▒▒║▒▒──┴────────────────────────────────┴──▒▒║▒▒──┘  curb; ▒ ramp = passable part
    │ ║ │  crosswalk cells: edge = centreline  │ ║ │           of the shared boundary
```

**How the two views stay linked:**
- Every edge belongs to exactly one strip or crosswalk cell, and its geometry is that cell's centreline, computed from the cell, never edited on its own.
- Every node belongs to one corner cell. A mid-block node sits on the boundary where a mid-block crossing joins or where coverage ends.
- **Connectivity lives on the boundaries.** Two cells that touch connect only through a port: a fence, a planter wall, a level change or a curb without a ramp separates them. Only transitions, each naming the two ports it uses, say which moves a corner allows.
- The walking line's offset from the centreline is kept: it says where people actually walk.
- A detection is placed in the cell and zone it is *in*, not on the walking line the camera was on.

**Levels of detail.** Each element records how far the evidence took it. A stretch seen only at dusk, or a sidewalk wider than the view, stays at a lower level, visibly.

| Level | What exists | From |
|---|---|---|
| 0 | Nodes, edges, transitions, lengths; the edge is the walking line, flagged as such | GPS, accelerometer, gyroscope |
| 1 | Cell outlines and boundaries; the edge becomes the centreline | Projected sidewalk, crosswalk and curb masks; the orthophoto in regime C |
| 2 | Zones, features, measured ports, width and slope stations | Obstacle, vegetation and feature masks; gravity |

**Output tables.** All GeoParquet, one folder per run, with `manifest.json`.

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
| `observations`, `runs`, `walking_lines` | The evidence (immutable, keyed by session and `t`), the walk's segmentation, and each pass's walking line | inference |
| `associations` | observation or pass → element, supports or contradicts, method version, dependency group (one pass) | all |
| `tile2net/` | `polygons` and `network` in Tile2Net's layers, fields and CRS | export |

## 9. How observations are aggregated

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
- Positions from consecutive frames within a few metres of each other are one object; the same object on different passes is merged by position.
- A feature records how many frames and passes support it, and the cell and zone it falls in.

**Promotion rules** (thresholds set on development data and frozen):
- **A sidewalk edge:** a pass on a walking line, with sidewalk in the video for most of its frames.
- **A crossing edge:** a walked rung (confirmed), or a crosswalk mask over the road with no walk (unverified).
- **A port:** the end of a walked crossing; its ramp, tactile paving and width come from the detections there.
- **A feature:** seen in at least k frames of one pass at a consistent ground position.

**Across sources (regime C):** geometry weighted by visibility (under canopy the street wins; in the open the aerial edge wins); topology from the walk wherever it was walked; two values that differ by more than their uncertainties are both kept and the element is marked `conflicting`.

## 10. Comparing sources: the ablation matrix

Each quantity can come from several sources. Every cell below is a run scored against the same reference, quantity by quantity.

| Quantity | GPS | + steps, gyroscope | + crossings (ladder) | + video | + Wi-Fi | + aerial (Tile2Net) | Reference |
|---|---|---|---|---|---|---|---|
| Position across the street | ✓ (raw, 5-fix median) | ✓ (smoother) | ✓ | ✓ (curb distance) | exploratory (side) | ✓ | Curbs, back of sidewalk |
| Position along the street | ✓ | ✓ (steps) | — | ✓ (ground motion) | — | ✓ | Corners on the orthophoto |
| Which side a pass is on | ✓ | — | ✓ | ✓ (side cue) | exploratory | ✓ | Protocol rule, labels |
| Sidewalk width | — | — | — | ✓ | — | ✓ (polygon) | Tape, orthophoto |
| Road width | — | ✓ (steps across) | ✓ | ✓ (whole span) | — | ✓ | Curbs |
| Running slope | — | — | — | ✓ (gravity + ground lines) | barometer (exploratory) | — | Inclinometer, LiDAR |
| Ramps, tactile paving, signals | — | — | ✓ (crossing ends) | ✓ (SAM3, Project Sidewalk models) | — | weak | Video labels |

Some rows already exist: phases 2a and 2b compared raw GPS, the smoother, the ladder and the ladder with video (cross-street position, road width).

## 11. Exploratory sources (time-boxed)

First checks on 3 November, on D2's two sessions:

| Source | Finding | What it could give | Status |
|---|---|---|---|
| **Wi-Fi** | A real scan every 7.5 s, about one every 10 m of walking. D2 S1 walked mostly the east sidewalks and S2 the west. In the same 25 m stretch, after removing each stretch's common offset between sessions, an access point's signal differs between the sides by a median 4.0 dB; with the side labels shuffled, 3.1 dB (all 200 shuffles ≤ 3.8 dB). 13% of pairs differ by 10 dB or more | A side cue that needs neither the protocol nor the camera; matching passes across days and collectors | **A real but modest signal on one day.** Worth a proper test. `network/experiments/wifi_side_check.py` |
| **Barometer** | Second-to-second noise about 7 cm; short-term wobble about ±0.3 m; slow drift over minutes | Level changes (stairs, ramps, bridge approaches); long grades, checked against LiDAR | Untested on a known level change |
| **Ambient light** | About every 0.6 s, 17–5,689 lux. The sensor is on the screen side, so it probably faces the collector's chest | Dusk and night flags | Low priority: the video's exposure says the same |
| **Magnetometer** | About 50 Hz | Steel above or below (the 'L', bridges) | Untested |

## 12. Reading the result map

`network/data/west_loop/graph/map.html` shows the Morgan work. Open it by running `python3 -m http.server 8767 --bind 127.0.0.1` in that folder, then visit http://127.0.0.1:8767/map.html. **It stays on this laptop:** it contains Cook County parcel lines (AGENTS.md rule 7). The background is the 2025 orthophoto, and every layer can be switched on and off. Phone data are shifted by the NAD83–WGS 84 difference (about a metre at Morgan) before drawing.

| Layer | What it is | Role for the graph |
|---|---|---|
| **Reference curbs** (green) | The City's 2010 curb lines near Morgan, checked against the 2025 photo; 23 pieces redrawn | Scoring only, never an input |
| **Reference back of sidewalk** (pink) | Cook County parcels merged into blocks; the outlines facing Morgan | Scoring only. With the curbs it outlines the reference sidewalk polygon |
| **GPS fixes** (white dots) | Raw `gps.csv` of both recordings | The starting point to improve on |
| **Walking lines: phase2a** (purple) | First version: steps, turns, crossings and GPS | Superseded; for comparison |
| **Walking lines: phase2a_far** (orange) | Plus: each crossing ends on the far line | Superseded; for comparison |
| **Walking lines: phase2b** (green) | Plus: the lines are road width + both curb distances apart, with the estimated camera height | Superseded; for comparison |
| **Walking lines: phase2b_h130** (blue) | With the measured camera height (1.30 m) and the road width over the whole time on the road | **Current best: the backbone of the graph** |
| **Corrected track** (light blue, off at start) | The model's position at each GPS time | Places every frame, detection and spoken word on the map |
| **Crossings by steps** (cyan) | Each trip across Morgan, from where the walker left their line to where they turned around | The future crossing edges and, at their ends, the ports |
| **Curb where the video puts it** (red dots) | The measured distance from the curb, drawn from the blue line towards the road | The first piece of a sidewalk polygon: its road-side boundary |

Not on the map: the baselines of the score tables ([RESULTS](RESULTS.md)).

## Sources

The method's prior work (GPS traces, side-of-street positioning, indoor landmark mapping, width and slope from images and sensors, linked polygons and lines) is listed with links in the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md), "Sources consulted". NACTO's [sidewalk zones](https://nacto.org/publication/urban-street-design-guide/street-design-elements/sidewalks/sidewalk-zones/) define the zones.
