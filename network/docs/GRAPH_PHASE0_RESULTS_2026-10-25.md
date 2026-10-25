# Phase 0 results: sessions, clocks, runs, side cue and zones

25 October 2026. Phase 0 of the [graph and GPS plan](GRAPH_GPS_PLAN_2026-10-24.md), section 8: the data contract before any graph is built. The code is `network/graph` (`python -m graph.phase0`). The clock checks ran on desktop-01, where the raw recordings are; the rest ran on the workspace. Outputs are in `data/west_loop_graph/phase0/`, which git ignores. D3 (22 October) got the contract checks only, so it stays unopened for method development. Section 7 records the decisions taken on these results.

## 1. The sessions

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

## 2. Clocks

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

## 3. Runs

After the split below, each D1 and D2 session has:
- 38–48 runs;
- 47–51 crossings found from turns;
- 16–24 straight crossings.

A run along the street is typically a block long (median 108–115 m).

- **GPS overstates crossing length.** Its displacement over a crossing is about 20 m, against about 13 m for Morgan's crosswalks. The end positions include standing at the curb, plus the fix error. So, as planned, a rung's length must come from timing and steps.
- **Straight crossings are now cut out of runs.** A crossing made straight on, over a cross street, has no turn, so the turn cut cannot see it. `runs.split_at_crosswalks` now cuts out every stretch where the crosswalk mask covers the ground just ahead of the walker: at least 30% of the patch in the bottom 15% of the frame, middle 30%, in two or more frames less than 2 s apart.
  - The cut stretches are partial: a median 4–5.5 s and about 11 m. The crosswalk is underfoot only part of the way, because of the approach and the gaps between stripes.
  - They mark where a crossing happened; their ends will need the curb and the tactile paving (phase 2).

## 4. Side cue

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

## 5. Zones

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

## 6. Gates

| Gate (plan, phase 0) | Result |
|---|---|
| Every stream used has a measured alignment bound | **Met.** Video against sensors: −0.28 to −0.39 s, drift about −0.2 s per hour, windows agreeing within 0.15 s; now corrected. GPS: 0.6–2.0 s late. Frame times within 0.03 s |
| The side cue works on a stated share of D1 runs | **Met.** 28 of 28 decided runs agree; 1 of 29 abstains |
| Zones kept where the masks separate them | **In part.** The furniture zone along the curb on Morgan; parkways and frontage wait for the zone prompts |
| D3's streets, collectors and phones | **Met.** Streets and phones confirmed. Which collector carried which phone is not needed, since the camera height is inferred per session |
| Lens calibration video and camera height | **Lens:** a rough focal length of 1460 px from the rotation check; the checkerboard video is still to record. **Camera height:** inferred, not measured (section 7) |

## 7. Decisions taken (25 October)

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

## 8. How to rerun

On desktop-01, from `~/sideseeing/graph-dev`, a copy of `network/graph`. The `conda activate sideseeing` environment is used, with `PYTHONPATH=~/sideseeing/tools-va/src:.`; `tools-va` is a worktree of sideseeing-tools' `feature/visual-analytics`, kept apart from the checkout the West Loop run uses.

```
W=~/sideseeing/workspaces/west-loop; P=$W/graph/phase0
python -m graph.phase0 align --raw ~/sideseeing/raw/chicago/west-loop --workspace $W --out $P
python -m graph.phase0 report --workspace $W --out $P/report --rotation $P/rotation_windows.csv \
    --sessions 2026-10-19-15-43-14-478 2026-10-19-16-37-31-946 2026-10-20-16-38-56-189 2026-10-20-17-32-46-710 \
    --zone-sessions 2026-10-19-15-43-14-478 2026-10-20-16-38-56-189
```

- **The motion events** in `$W/motion/` came from `~/sideseeing/motion_all.py` (`SideSeeingWorkspace.generate_motion_events`, CPU only). D1 S1's file is identical to the one made earlier on the laptop.
- **The session table with planned modules** needs geopandas and `--pieces data/west_loop/routes.gpkg`; it ran on the laptop.
- **The checks:** `python -m pytest graph/tests` from `network/`.
