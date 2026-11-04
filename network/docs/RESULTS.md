# Graph results: phases 0, 2a and 2b on Morgan
The dated results of the graph work, one section per phase, as written on the day each was run (25 to 30 October 2026). Every result number of the network track comes from here or from the files under `network/data/west_loop/graph/`. The text is that of the three phase notes, unchanged except that headings moved down one level and links point to the merged pages; the original notes are in [archive/](archive/). Add a new phase as a new section; do not rewrite an old one.
| Section | Written | What it records |
|---|---|---|
| [Phase 0](#phase-0-results-sessions-clocks-runs-side-cue-and-zones) | 25 October | The data contract: sessions, clocks, runs, the video side cue, zones |
| [Phase 2a](#phase-2a-notes-the-ladder-on-morgan) | 25 October, extended 26 October | The walking lines on Morgan (the ladder), scored against the reference; crossings tied to the far line |
| [Phase 2b](#phase-2b-notes-the-curb-from-the-video-on-morgan) | 27 October, extended 30 October | Curb distance and road width from the video; the measured camera height (1.30 m) |

**Commands in the sections below are those of their date.** On 4 November the code became the `walk2net` package ([ARCHITECTURE §6](ARCHITECTURE.md#6-where-each-piece-went)); run from `network/` with the sideseeing-tools venv:

| Written below | Now |
|---|---|
| `python -m graph.phase0 …` | `python -m experiments.phase0 …`; `report` adds `--area west_loop` |
| `python -m graph.phase2 …` | `python -m experiments.phase2a …`; `fit` adds `--area west_loop --street morgan` |
| `python -m graph.phase2b …` | `python -m experiments.phase2b …`; `fit` adds `--area west_loop --street morgan` |
| `python -m graph.reference`, `graph.evaluate`, `graph.resultmap` | `python -m walk2net.evaluate.reference`, `walk2net.evaluate.score`, `walk2net.resultmap`, each with `--area west_loop --street morgan`; `--reference` defaults to the area's reference folder |
| `graph/contract.py`, `runs.py`, `steps.py`, `ground.py`, `ladder.py` | `walk2net/stages/sync.py`, `walk.py` (runs and steps), `ground.py`, `ladder.py` |

The settings these sections name as constants (Morgan's axis, the UTM zone, the datum shift, the protocol's road sides) now live in `network/areas/west_loop.toml` and `network/protocols/`. Re-run with them, the phase 2b fit at 1.30 m gives this page's numbers value for value (`tests/test_regression.py`).

## Phase 0 results: sessions, clocks, runs, side cue and zones

25 October 2026. Phase 0 of the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md), section 8: the data contract before any graph is built. The code is `network/graph` (`python -m graph.phase0`). The clock checks ran on desktop-01, where the raw recordings are; the rest ran on the workspace. Outputs are in `data/west_loop_graph/phase0/`, which git ignores. D3 (22 October) got the contract checks only, so it stays unopened for method development. Section 7 records the decisions taken on these results.

### 1. The sessions

| Day | Session | Planned modules near its fixes | Phone (Android) | Minutes | GPS accuracy, median (share over 10 m) | Stops / turns / crossing candidates |
|---|---|---|---|---|---|---|
| D1 | 2026-10-19-15-43-14-478 | MORGAN 99% | 34 | 44.2 | 3.1 m (0.2%) | 24 / 104 / 50 |
| D1 | 2026-10-19-16-37-31-946 | MORGAN 98% | 34 | 42.5 | 3.1 m (0.1%) | 23 / 119 / 47 |
| D2 | 2026-10-20-16-38-56-189 | CARPENTER 65%, ABERDEEN 33%, MADISON_WEST 12% | 34 | 44.9 | 3.2 m (0.2%) | 26 / 98 / 49 |
| D2 | 2026-10-20-17-32-46-710 | CARPENTER 58%, ABERDEEN 34%, MADISON_WEST 17% | 34 | 43.9 | 3.2 m (0.0%) | 19 / 95 / 51 |
| D3 | 2026-10-22-15-05-58-722 | SANGAMON_A 99% | 34 | 26.4 | 3.8 m (0.7%) | 4 / 93 / 34 |
| D3 | 2026-10-22-15-09-20-275 | PEORIA_A 100% | 33 | 30.1 | 5.7 m (13%) | 7 / 76 / 39 |
| D3 | 2026-10-22-15-37-28-260 | SANGAMON_A 100% | 34 | 28.3 | 4.4 m (0.2%) | 4 / 115 / 38 |
| D3 | 2026-10-22-15-44-19-995 | PEORIA_A 99% | 33 | 31.2 | 5.1 m (11%) | 13 / 89 / 40 |

- **D3 is confirmed:** two phones walked SANGAMON_A and PEORIA_A at the same time. Both are moto g 5G (2023), as Renzo confirmed, and they run different Android versions. The Android 34 phone, which also recorded D1 and D2, walked Sangamon. The Android 33 phone walked Peoria, and its GPS is clearly worse.
- **Modules are an inventory only.** They come from the planned route pieces (built from OSM), which the graph never uses as input.
- **GPS fixes arrive every 0.55 s**, not every second.
- **D3 has far fewer stops.** This is probably because Peoria has no signalised crosswalks and Sangamon two, against nine on Morgan (`data/west_loop/sessions.csv`).
- **The video is H.264 at 1920×1080 and 30 fps**, not the 4000×2250@15 that the camera setting names.

### 2. Clocks

| Session | Video against sensors (s) | Drift (s per hour) | Clear rotation windows | Focal length (px, rough) | GPS against sensors (s) | GPS correlation |
|---|---|---|---|---|---|---|
| D1 15-43 | −0.28 | −0.18 | 6 | 1459 | +1.2 | 0.58 |
| D1 16-37 | −0.30 | −0.26 | 6 | 1457 | +0.9 | 0.53 |
| D2 16-38 | −0.33 | −0.22 | 6 | 1529 | +0.6 | 0.40 |
| D2 17-32 | −0.39 | −0.24 | 5 | 1457 | +1.2 | 0.46 |
| D3 15-05 | −0.29 | −0.17 | 5 | 1452 | +2.0 | 0.39 |
| D3 15-09 | −0.29 | −0.21 | 6 | 1467 | +0.6 | 0.14 |
| D3 15-37 | −0.32 | −0.19 | 6 | 1387 | +1.5 | 0.61 |
| D3 15-44 | −0.34 | −0.21 | 6 | 1464 | +1.1 | 0.26 |

- **The video against the sensors.** During the six largest turns of each session, the image's sideways slide matches the gyroscope's rate about gravity closely (correlation 0.97–0.996).
  - The camera shows each turn about 0.3 s before the sensor clock records it, and the gap grows by about 0.2 s per hour. Both values are the same on both phones and all three days.
  - Within a session, the windows agree within 0.15 s. Two of the 48 windows had no clear correlation and are left out.
  - Whether the cause is the app's sample time stamps or the video's start time in the metadata is not settled.
  - For the graph it is a correction: `report --rotation` fits a line through each session's windows (the offset at the start and the drift) and moves the motion events onto the video clock.
- **Frame times hold.** Every frame's time stamp is within 0.03 s of its index ÷ 30, so the workspace's frame times are right.
- **GPS lags the sensors by 0.6–2.0 s**, but with weak correlation (0.14–0.61, weakest on the Android 33 phone), because the course from fixes is noisy at walking speed. Take about 1–2 s as the bound.
- **No sync tap.** No session shows three knocks that match in the accelerometer and the audio, and the West Loop documents do not call for them. The rotation check replaces the tap, and it is better: one measurement per turn over the whole session, not one at the start.
- **The lens.** The slide per degree of turn gives a horizontal focal length of about 1460 px at 1920 px width, a field of view of about 67°. This is rough: the pitch, stabilisation and walking all add to the slide. It is a prior until the checkerboard calibration.

### 3. Runs

After the split below, each D1 and D2 session has:
- 38–48 runs;
- 47–51 crossings found from turns;
- 16–24 straight crossings.

A run along the street is typically a block long (median 108–115 m).

- **GPS overstates crossing length.** Its displacement over a crossing is about 20 m, against about 13 m for Morgan's crosswalks. The end positions include standing at the curb, plus the fix error. So, as planned, a rung's length must come from timing and steps.
- **Straight crossings are now cut out of runs.** A crossing made straight on, over a cross street, has no turn, so the turn cut cannot see it. `runs.split_at_crosswalks` now cuts out every stretch where the crosswalk mask covers the ground just ahead of the walker: at least 30% of the patch in the bottom 15% of the frame, middle 30%, in two or more frames less than 2 s apart.
  - The cut stretches are partial: a median 4–5.5 s and about 11 m. The crosswalk is underfoot only part of the way, because of the approach and the gaps between stripes.
  - They mark where a crossing happened; their ends will need the curb and the tactile paving (phase 2).

### 4. Side cue

Each run's cue is the side holding at least 70% of the car and curb boxes, from 5 boxes up; otherwise it abstains. The table counts runs of at least 20 m along the street axis, after the clock correction and the crosswalk split:

| Session | NS runs: agree / disagree / abstain | Madison (EW): left / right / abstain |
|---|---|---|
| D1 15-43 | 14 / 0 / 1 | — |
| D1 16-37 | 14 / 0 / 0 | — |
| D2 16-38 | 11 / 1 / 1 | 2 / 0 / 0 |
| D2 17-32 | 12 / 0 / 1 | 2 / 0 / 1 |

- **D1 passes the gate.** All 28 runs where the cue decided agree with the protocol, and one abstains. Before the split it was 34 of 34 with 8 abstaining: the runs that abstained mostly contained a straight crossing.
- **D2's one disagreement is the Madison jog corner** (814–822 s, 68 cars on the right and none on the left). In the first pass, three crossings of Madison sat inside runs here; their frames show the collector at the curb and on the crosswalk.
- **On Madison's jog, the cue caught a departure from the plan.** It says the road was on the left in all 4 decided runs, with lopsided counts such as 399 cars on the left against 19 in the first pass. The module plan walks east–west streets with the road on the right, but on the jog the collector kept the road on the left, as on the north–south streets. The run that abstains has cars on the left (146 against 13) but curbs on the right (72 against 22).
- **Under the protocol, the walking direction alone gives the side.** North–south streets are walked northbound on the east side and southbound on the west side, so heading decides which sidewalk. That makes it a baseline the joint inference must beat (added to the plan's section 6). The cue's value lies elsewhere: catching departures, as on Madison, and handling natural walks.

### 5. Zones

The contact sheets, `zones_<session>.jpg`, show 24 frames each, with the masks drawn over them:
- blue: `sidewalk`
- orange: `curb`
- green: furniture

| | Morgan (D1 15-43, 3 blocks, 230 frames) | Carpenter and Aberdeen (D2 16-38, 3 blocks, 249 frames) |
|---|---|---|
| The street | Paved to the curb, no parkway | Grass parkways, tree pits, planters; stoops and fences on the building side |
| Road-side curb found | 56% of frames | 10% |
| Unpaved strip between curb and paving | 21% (tree pits) | 4% measured; grass is visible but not segmented |
| Furniture on the road side | 34% (poles 68, trees 15, parking meters 9, bicycle racks 6); bases at a median 22% of the way from curb to building side | 28% (trees 44, poles 22, planters 8, a few bins, meters and hydrants); trees mostly stand beyond the paving, in the parkway |


- **The furniture zone can be measured on commercial streets** like Morgan. There it is a strip along the curb, and the offsets of its objects' bases give its width over a block.
- **Parkways cannot be measured with the current prompts.** There is no `grass`, `road` or `building` prompt. Worse, `curb` also fires on the edge where the sidewalk meets a building ledge, on both days.
- **No prompt separates the frontage zone.**
- **So the zone gate is met only in part,** until the zone prompts of section 7 have run.

### 6. Gates

| Gate (plan, phase 0) | Result |
|---|---|
| Every stream used has a measured alignment bound | **Met.** Video against sensors: −0.28 to −0.39 s, drift about −0.2 s per hour, windows agreeing within 0.15 s; now corrected. GPS: 0.6–2.0 s late. Frame times within 0.03 s |
| The side cue works on a stated share of D1 runs | **Met.** 28 of 28 decided runs agree; 1 of 29 abstains |
| Zones kept where the masks separate them | **In part.** The furniture zone along the curb on Morgan; parkways and frontage wait for the zone prompts |
| D3's streets, collectors and phones | **Met.** Streets and phones confirmed. Which collector carried which phone is not needed, since the camera height is inferred per session |
| Lens calibration video and camera height | **Lens:** a rough focal length of 1460 px from the rotation check; the checkerboard video is still to record. **Camera height:** inferred, not measured (section 7) |

### 7. Decisions taken (25 October)

1. **Sensor times are corrected** in the graph code (`report --rotation`), not yet in sideseeing-tools' `sensor_signal`.
2. **The zone prompts are approved and queued.** `road`, `grass`, `tree pit`, `building` and `fence` make a second SAM3 pass on D1 and D2 (`~/sideseeing/zones_step.py`). It starts on desktop-01 once the West Loop run and its `after_run.sh` have finished, so the GPU is never shared. It logs to `logs/westloop/zones.log`, with its start and end in the run's status file.
3. **The protocol rule joins the plan's baselines.**
4. **Runs are split at straight crossings** (section 3).
5. **The camera height is inferred, not measured.**
   - **Why it matters.** It sets the scale of the ground projection. A point on the ground seen at angle θ below the horizon lies at distance h ÷ tan θ, so every width and offset scales with h: a 5 cm error is about 4% of a width, 8 cm on a 2 m sidewalk. Angles, slope and topology do not depend on it.
   - **The two estimates.** Both come from the recordings:
     - **The walk's own scale.** With the focal length (section 2) and the pitch (gravity), the ground's apparent motion between frames gives speed ÷ height. GPS over a long straight run gives the speed to a few percent. Each block-long run gives one height, and a session has about 15 of them.
     - **A ruler on the ground.** Tactile paving must extend at least 610 mm (2 ft) in the direction of travel. It is detected at almost every crossing (49 of 50 on D1 S1), so each crossing gives another estimate. Whether most panels are exactly that deep is to confirm on Morgan.
   - **Body height alone is too loose.** A chest camera sits around 1.2–1.45 m for adults, which is ±10% and only good as a sanity bound.
   - **Why not a tape.** The two estimates check each other. Inferring per session also covers the past sessions, which no tape can reach, and makes the collector's identity unnecessary. A tape measurement of the vest, if ever taken, would turn the agreement into a stated error.

**Still to do.** Record the checkerboard video, for the lens distortion and the stabilisation crop; it does not block phase 2. Phase 1, the reference, needs people. Phase 2, the ladder on Morgan, can start alongside it, checked against D1's protocol sides until the reference exists.

### 8. How to rerun

On desktop-01, from `~/sideseeing/graph-dev`, a copy of `network/graph`. The `conda activate sideseeing` environment is used, with `PYTHONPATH=~/sideseeing/tools-va/src:.`; `tools-va` is a worktree of sideseeing-tools' `feature/visual-analytics`, kept apart from the checkout the West Loop run uses.

```
W=~/sideseeing/workspaces/west-loop; P=$W/graph/phase0
python -m graph.phase0 align --raw ~/sideseeing/raw/chicago/west-loop --workspace $W --out $P
python -m graph.phase0 report --workspace $W --out $P/report --rotation $P/rotation_windows.csv \
    --sessions 2026-10-19-15-43-14-478 2026-10-19-16-37-31-946 2026-10-20-16-38-56-189 2026-10-20-17-32-46-710 \
    --zone-sessions 2026-10-19-15-43-14-478 2026-10-20-16-38-56-189
```

- **The motion events** in `$W/motion/` came from `~/sideseeing/motion_all.py` (`SideSeeingWorkspace.generate_motion_events`, CPU only). D1 S1's file is identical to the one made earlier on the laptop.
- **The session table with planned modules** needs geopandas and `--pieces data/west_loop/plan/routes.gpkg`; it ran on the laptop.
- **The checks:** `python -m pytest graph/tests` from `network/`.

## Phase 2a notes: the ladder on Morgan

25 October 2026; results against the reference added 26 October (section 4). Phase 2a of the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md), section 8, phase 2: steps, the ladder fit on D1 (Morgan, both sessions) and its baselines.

The geometry stayed sealed until the reference was fixed. This note records:
- what was built;
- the results that needed no reference;
- what the first fits taught about the model;
- the results against the reference, and the gate.

### 1. What was built

All of it is in `network/graph`, with checks in `graph/tests` (13 pass):
- **`steps.py`**: steps from the accelerometer, by the West Loop notebook's method.
- **`ladder.py`**: the street frame, each run's heading, each run's sidewalk from the crossings, and the fit.
- **`baselines.py`**: GPS plus steps (Kalman and RTS smoother), and walking lines from any track (raw GPS, the 5-fix median the viewer shows, the smoother).
- **`phase2.py`**: two steps.
  - `prepare` runs on desktop-01 and writes step times and crosswalk-underfoot times, on the video clock.
  - `fit` runs on the laptop and fits the sessions together and each alone.
- **`reference.py` and `trace.html`**: the phase 1 reference page.

```
python -m graph.phase2 prepare --raw RAW --workspace W --rotation rotation_windows.csv --out PREP --sessions ...
python -m graph.phase2 fit --workspace W --rotation rotation_windows.csv --prepared PREP --out OUT --sessions ...
```

### 2. What can be shown now (no geometry)

| | D1 15-43 | D1 16-37 |
|---|---|---|
| Steps | 3759 | 3763 |
| Step length (fitted) | 0.766 m | 0.777 m |
| Runs / along Morgan / crossings of Morgan | 106 / 54 / 50 | 105 / 52 / 47 |
| Heading corrections needed | 1 | 1 |
| Long runs' GPS bearing against their heading (median) | 4.5° | 4.7° |
| Runs along Morgan on the protocol's side, from the crossings alone | 93% | 94% |
| The same, runs of 40 m or more | 15 of 15 | 13 of 13 |

- **The sidewalk side comes from the motion alone.** You cross towards the street, so the gyroscope's turns and the crossings say which sidewalk every run is on, with no GPS position, no video and no protocol rule. GPS only says which way the long runs point.
- **The protocol rule gives the same answer here, but the method doesn't need it.** The natural-walk block will test it where the rule does not hold.
- **The disagreements are all short pieces** (14 m at most). They come from two zones where neighbouring crossings disagree (about 2273 s into the first session, 2158 s into the second), plus a 2 m shuffle at the end of a session. Those zones are where the plan keeps alternatives (phase 3).

### 3. What the first fits taught

Each lesson below changed the model:

1. **The turn angles drift.** Added up as measured, they disagreed with the long runs' GPS bearings by a median 23–36°, and many runs came out with the wrong heading.
   - *Change:* on a street grid every turn is a whole number of quarters. The turns between two runs are summed and rounded to quarters, and each long run's GPS bearing fixes its own heading.
   - *Result:* one correction per session; the gap to GPS dropped to about 5°.
2. **Crossings are there and back.** Under the protocol, the walker turns at the far curb and never walks the far sidewalk. So within one session, a crossing doesn't join the two walking lines.
   - *Change:* a crossing is a leg measured by steps, from the walking line it leaves to its own far end (the port at the far curb), and each walking line comes only from the runs walked on it. D1's two sessions, one on each side, are fitted together.
   - *Consequence:* the plan's rung ("the distance between the two walking lines, by steps") is not observed within a session under this protocol. What the steps measure is the near walking line to the far turnaround.
3. **The two walking lines belong to one street.** Fitted freely, a stretch of GPS on the wrong side of the street (the notebook found stretches of 24–77 m) dragged one line across the other.
   - *Change:* the lines are a centreline that may bend, plus and minus a half-separation that barely changes.
4. **Only the data are treated robustly.** The robust cost was being applied to the shape terms too, which let the lines kink cheaply.
   - *Change:* now only the GPS fixes and the joins between runs are robust.

### 4. Against the reference (26 October)

**The reference** (agreed 26 October; tracing by hand was dropped as unscalable):
- **Curbs:** the city's 2010 curb lines, checked by Renzo on the 2025 orthophoto. 86 of 109 pieces matched; 23 had changed and he redrew them.
- **Back of the sidewalk:** the property line, from Cook County's current parcels merged into blocks. Renzo spot-checked six places ("roughly right").
- **Read across the street every metre:** both edges are readable over 1,075 of Morgan's 1,799 m; intersections, the bridge and gaps are left out.
- **Widths (medians):** road 15.2 m, east sidewalk 2.0 m, west 2.9 m. Together that is 20.1 m, Chicago's standard 66 ft right of way.
- **Datum:** the city and county data are NAD83 and phone GPS is WGS84. At Morgan in October 2026 the same point is 1.0 m west and 0.9 m north in GPS coordinates. pyproj's default conversion ignores this, so `evaluate.py` moves the reference by it before scoring. Without the move, every walking line looked about a metre too far west.

`python -m graph.evaluate --reference data/west_loop/reference --fit data/west_loop/graph/phase2a --out data/west_loop/graph/phase2a/eval` writes the scores, the profile and a plot (`walking_lines.png`).

**Walking lines,** read every metre where their side was walked:

| | Inside the sidewalk | Median distance to its middle | Median distance onto it from the curb (negative: in the road) | On the street's other half |
|---|---|---|---|---|
| Ladder, east | 35% | 1.6 m | −0.5 m | 0% |
| GPS + steps smoother, east | 42% | 2.0 m | −0.8 m | 11% |
| Raw GPS and 5-fix median, east | 36% | 2.4 m | −1.1 m | 14% |
| Ladder, west | 54% | 1.8 m | +1.4 m | 0% |
| GPS + steps smoother, west | 24% | 4.2 m | −2.2 m | 22% |
| Raw GPS and 5-fix median, west | 18% | 4.7 m | −2.3 m | 23% |

Fix by fix, the tracks give the same picture. The ladder is never on the street's other half, against 15–29% for raw GPS. The ladder's fit of each session alone is no better than the joint fit.

**Crossings** (53 of 97 where the reference reads the road):
- The steps measure a median 19.9 m.
- From the crossing's start on the walking line to the far curb is 17.3 m.
- So the far end lies a median 1.9 m past the far curb (quartiles −0.2 to 4.2 m). The walker turns around on the far sidewalk, not at the curb. This explains why crossings by steps came out longer than the road.

**The gate is half met.**
- **Met:** the ladder's walking lines are nearer the sidewalk's middle than the smoother's on both sides (1.6 against 2.0 m east, 1.8 against 4.2 m west), and the ladder never puts a line on the street's other half.
- **Not met:** the lines lie inside the sidewalk only 35% (east) and 54% (west) of the way. The west line's median sits near the middle of its sidewalk. The east line's median sits 0.5 m into the road, about 1.5 m off its middle, and from about 520 to 1,150 m along the street it is 2–6 m into the road.
- **A medium-sized error fails "inside" here:** these sidewalks are only 2–3 m wide, so an error of 1–2 m is enough.

**What it says about the model:**
- **Crossings and steps fix the side, not the absolute position.** Without a map, the absolute sideways position comes only from GPS and its bias.
- **The bias differs between the two sessions.** The fitted pull was 0.6 m for the east session and 3.7 m for the west one, and it also varies along the street. That is the plan's risk "the GPS bias is not systematic".

### 5. Crossings tied to the far line (26 October)

Until now nothing tied a crossing's far end to anything. The return leg only had to match the outward one, so the distance between the two walking lines came from GPS alone. Now each crossing's end lies on the walking line it heads to (`FAR_M`, 1.5 m, robust). That is the modelling assumption the reference supports: the walker turns on the far sidewalk. The measured 1.9 m was not used. Output: `data/west_loop_graph/phase2a_far/`.

`evaluate.py` now also splits the two lines' error into:
- **the shift they share:** the street's centre, which without a map only GPS can place;
- **their separation:** which the crossings and steps measure.

| | Shift, median \| p90 | Separation, median | Inside, east \| west | Onto the sidewalk from the curb, east \| west (median) | In the road, east \| west |
|---|---|---|---|---|---|
| Raw GPS | 2.1 \| 8.9 m | 8.5 m too close | 36% \| 18% | −1.1 \| −2.3 m | 57% \| 73% |
| GPS + steps smoother | 2.0 \| 7.4 m | 7.5 m too close | 42% \| 24% | −0.8 \| −2.2 m | 56% \| 70% |
| Ladder, first fit | 1.0 \| 3.5 m | 3.9 m too close | 35% \| 54% | −0.5 \| +1.4 m | 60% \| 38% |
| **Ladder, far ends tied** | **1.1 \| 3.1 m** | **1.8 m too close** | 36% \| 48% | **+0.9 \| +2.1 m** | **37% \| 30%** |

The reference's sidewalk middles sit 1.0 m (east) and 1.45 m (west) from the curb, 17.65 m apart.

**What changed:**
- **The bias is gone.** The east line's median now sits in the middle of its sidewalk, and the west one 0.6 m past its middle, still inside a 2.9 m sidewalk.
- **The separation error halved.**
- **The share inside did not move.** What is left is the shared shift, which follows the GPS along the street: half a metre to 3 m, in stretches hundreds of metres long. Both sessions' GPS is off the same way there.

Crossings and steps cannot see that shift, and neither will the video's curb offsets, which measure distances from the walking line, not positions. Without a map, the shared shift is the floor of the street-only method; the orthophoto (the street + aerial regime) is what can remove it.

**Tried and dropped:** ignoring the GPS's across-street position while crossing. GPS chips smooth their output, which may cut a short out-and-back crossing short. The separation improved to 1.3 m too close. But the distance to the sidewalk's middle got slightly worse (east 1.75 → 1.86 m) and the share inside fell on the west (48% → 45%). It was not kept; its outputs are in `phase2a_far_noxgps_experiment/`.

### 6. Next

1. ~~Tie each crossing's far end to the far walking line.~~ Done (section 5).
2. **Phase 2b, the video's curb offsets.** First pass done on 27 October: [phase 2b notes](#phase-2b-notes-the-curb-from-the-video-on-morgan). The camera sees the curb. Projecting the curb and sidewalk masks gives each run's distance from the curb with no map, which is the plan's "edges" term (section 6). It also gives the cells.
   - **The road's width by steps:** the steps taken while the crosswalk is underfoot (already detected) measure it.
   - **The separation then follows:** road width plus the two curb offsets, so this should fix the separation that remains.
   - **It needs desktop-01:** the gravity stream gives the camera's tilt, and the second session's frames are there. The laptop has only D1's masks.
3. **A GPS pull that varies along the street**, if 1 and 2 leave a bias.
4. Every change is scored with `evaluate.py` on D1 only. The setting is frozen before D3.

## Phase 2b notes: the curb from the video, on Morgan

27 October 2026. Phase 2b of the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md), section 8, phase 2, following the [phase 2a notes](#phase-2a-notes-the-ladder-on-morgan), section 6, item 2. D1 only (Morgan, both sessions). Nothing was run on D3 or on the GPU.

### 1. What was built

- **`ground.py`**: the camera.
  - **Pinhole model:** focal length 1460 px from phase 0, centre at the image's middle.
  - **Pitch and roll from the gravity sensor:** gravity lies along the phone's x axis, and the camera looks along its −z.
  - **Pixels onto the ground,** and ground points back into the image.
  - **Edge lines:** a robust line through a mask's edge 1.5–8 m ahead, giving its perpendicular distance from the camera.
  - **Ground motion:** frames 0.1 s apart, seen from above and aligned (ECC), give the motion in units of the camera's height.
- **`phase2b.py measure`** (desktop-01): per session, the camera's height, and per frame the pitch, the roll, the share of sidewalk just ahead, and the curb and sidewalk edge lines on both sides.
- **`phase2b.py fit`** (laptop):
  - each leg's road width by steps, and each walking line's distance from its curb along the street;
  - their sum at every leg: the separation of the two walking lines;
  - the ladder refitted with that separation as a new robust term (`ladder.EDGE_M`, 0.6 m).
- **Checks:** `graph/tests/test_phase2b.py`.
  - Gravity gives the pitch.
  - A drawn curb is read at its distance, and the distance scales with the height.
  - A measured separation holds the walking lines apart.
  - All 19 tests pass.

```
python -m graph.phase2b measure --raw RAW --workspace W --rotation rotation_windows.csv --prepared PREP --fit FIT --out OUT --sessions ...
python -m graph.phase2b fit --workspace W --rotation rotation_windows.csv --prepared PREP --fit FIT --measured OUT --out FIT2 --sessions ...
```

Outputs:
- the measurements are in `graph/phase2b` on desktop-01 and `network/data/west_loop/graph/phase2b_measured/`;
- the fit is in `network/data/west_loop/graph/phase2b/`, scored in `phase2b/eval/`.

### 2. What the video measures

| | D1 15-43 (east side) | D1 16-37 (west side) |
|---|---|---|
| Camera height (ground motion against steps, 10 runs) | 1.485 m (runs 1.31–1.64) | 1.425 m (runs 1.27–1.60) |
| Pitch, roll (median) | 21.0°, 3.9° | 21.1°, 4.4° |
| Road-side curb seen | 29% of frames | 26% |
| Distance from the curb, median | 1.46 m | 1.65 m |
| Paved run under the walker, median | 2.48 m | 2.52 m |
| Road width by steps, median of each session's legs | 13.5 m (49 legs) | 14.3 m (47 legs) |

**Three things that went wrong on the way, kept for the record:**
1. **Matching frames 1 s apart failed:** the ground looks too different after 1.3 m of walking. Matching on the video at 10 frames a second works.
2. **Feature tracking locked onto gravel,** whose repeating texture reads as no motion. Aligning whole images (ECC) on the sidewalk straight ahead, with the warp's border masked, fixed it.
3. **The crosswalk mask covers only the painted bars,** so "crosswalk underfoot" flickered mid-crossing, and the first road widths came out at 6.85 m. The road is now timed by the absence of sidewalk in the same patch just ahead. The threshold is half the patch, so it trips at the same look-ahead at both curbs.

### 3. Against the reference

| | Step 1 (far ends tied) | Phase 2b |
|---|---|---|
| Separation, median error | 1.77 m too close | **0.92 m too close** |
| Shared shift, \|median\| \| p90 | 1.10 \| 3.09 m | 0.94 \| 3.13 m |
| Inside the sidewalk, east \| west | 36% \| 48% | **41% \| 62%** |
| Median distance to its middle, east \| west | 1.75 \| 1.84 m | 1.65 \| 1.51 m |
| In the road, east \| west | 37% \| 30% | 32% \| 21% |
| On the street's other half | 0% | 0% |

Every measure moved the right way. The gate is still half met: the lines are nearer the middle than the smoother's on both sides, but are not inside the sidewalk most of the way on the east.

### 4. Calibration: two errors that partly cancel

Two errors pull in opposite directions:
- **Road width by steps, about 8% short.** The steps give 14.0 m. The road visible on the orthophoto measures 15.2 m at u = 650 and 15.35 m at u = 900. Cadence on the road equals cadence along the street (ratio 1.005), so a longer stride while crossing is not the cause. The likely cause is the sidewalk mask spilling over the curb ramps at both ends.
- **Camera scale, about 15% too large.** The video reads paved sidewalks of 2.5–2.7 m on both sides. The orthophoto shows about 2.2–2.3 m of concrete. A height near 1.27 m, rather than 1.45 m, would fit, and is also more typical for a vest. Ground-motion alignment can be pulled towards no motion by anything that moves with the camera, such as the walker's shadow, and that makes the height too large.

Because they partly cancel, the separation came out close: 17.5 m measured, against 17.65 m between the reference's sidewalk middles. Neither should be trusted alone.
- **Height:** the plan's second ruler, the tactile paving at curb ramps (at least 610 mm deep), is independent of the steps. A tape measure of the vest pocket's height at the next fieldwork would settle it outright.
- **Road width:** the far curb's projected distance ahead, added to the distance walked, gives a width that is independent of the threshold.

### 5. The reference at the half-metre level

Patches of the 2025 orthophoto across the street (u = 650 and 900) show two things, at the same size as the errors left:
- **Curbs:** at u = 650, both reference curbs lie 0.6 m west of the visible curb edges, a pure shift. At u = 900, the west curb is 0.7 m off and the east 0.2 m. Renzo redrew 23 pieces on the orthophoto and kept 86 of the city's 2010 lines. So the reference may mix two frames, about half a metre apart. Shifts that both curbs share leave widths unchanged; mixed lines do not.
- **East property line:** the concrete runs about 2.2 m from the visible curb to the building, but the parcel line sits 1.4 m out, inside the paving. So the reference's east sidewalk (1.95 m, curb to property line) is probably too narrow. That penalises "inside" on the east. Cook County's parcels are known to be shifted by a metre in places; roof lean in the orthophoto cannot move the paving.

Before the gate is read as final, the reference needs one consistent pass:
- curbs from a single source, in the orthophoto's frame;
- the back of the sidewalk where the paving meets buildings and fences.

### 6. Next

1. **Height from the tactile paving** (map-free, on desktop-01, no GPU); the road width from the far curb ahead.
2. **The reference:** one consistent pass for curbs and the back (section 5). Which source to use is Renzo's decision.
3. **The cells:** strips from the curb line and the paved edge along each walking line.
4. **Then** phase 3 on D2, and freeze the settings before D3.

### 7. Measured height and the road's full span (30 October)

**The height.** Renzo measured the vest's camera height on himself: **1.30 m**. Other collectors may differ; this is the proxy until their measurements come in. `phase2b fit --height-m 1.30` rescales every ground distance by it, since all of them scale with the height.
- The ground-motion estimate (1.43–1.49 m) was about 12% high.
- At 1.30 m, the paved sidewalk under the walker reads 2.17 m (east) and 2.30 m (west). The orthophoto shows about 2.2 and 2.3 m. The camera scale is now right.
- The walker's distance from the curb becomes 1.28 m (east) and 1.51 m (west).

**The road's width.** With the height right, the short road width no longer hid behind it: the separation error went from 0.92 to 1.19 m. On about one crossing in five, the sidewalk mask flickers on mid-road. Keeping only the longest unbroken stretch made those crossings short. Taking the whole span, from the first frame on the road to the last, fixed the bias:

| Road width by steps against the reference (53 crossings) | Median | Error, median | Error, quartiles |
|---|---|---|---|
| Longest stretch (before) | 14.32 m | −0.73 m | −2.33 / +0.79 m |
| Whole span (now) | 14.52 m | +0.24 m | −1.14 / +1.72 m |

Each crossing is only good to about 1.5 m, because there is one frame a second at each end. The fit relies on their number.

**Tried and dropped:** reading the road's width straight ahead in the video, as the far curb's distance plus the distance walked. Only 42 crossings saw both curbs, and the errors spread from −3.6 to +0.6 m.

**Results** (`network/data/west_loop/graph/phase2b_h130/`):

| | Step 1 | Phase 2b (27 Oct) | **Phase 2b, 1.30 m and whole span** |
|---|---|---|---|
| Separation, median error | 1.77 m too close | 0.92 m too close | **0.61 m too close** |
| Shared shift, \|median\| \| p90 | 1.10 \| 3.09 m | 0.94 \| 3.13 m | 0.94 \| 3.12 m |
| Inside the sidewalk, east \| west | 36% \| 48% | 41% \| 62% | **42% \| 67%** |
| Median distance to its middle, east \| west | 1.75 \| 1.84 m | 1.65 \| 1.51 m | 1.72 \| **1.40 m** |
| In the road, east \| west | 37% \| 30% | 32% \| 21% | 31% \| **14%** |
| On the street's other half | 0% | 0% | 0% |

What limits the walking lines now:
- **The shared shift**, which only the aerial photo can remove.
- **The reference's own half-metre problems** (section 5). They matter most on the east side.

Section 4's calibration problem is resolved for the height. The road width is now unbiased on average but loose for each crossing; the checkerboard video will refine the lens.
