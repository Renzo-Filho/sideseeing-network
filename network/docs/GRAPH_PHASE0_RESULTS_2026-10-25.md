# Phase 0 results: sessions, clocks, runs, side cue and zones

25 October 2026. Phase 0 of the [graph and GPS plan](GRAPH_GPS_PLAN_2026-10-24.md), section 8: the data contract before any graph is built. The code is `network/graph` (`python -m graph.phase0`). The clock checks ran on desktop-01, where the raw recordings are; the rest ran on the workspace. Outputs are in `data/west_loop_graph/phase0/`, which git ignores. D3 (22 October) got the contract checks only, so it stays unopened for method development.

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

- **D3 is confirmed:** two phones walked SANGAMON_A and PEORIA_A at the same time. Both phones are moto g 5G (2023), but they run different Android versions. The Android 34 phone, which also recorded D1 and D2, walked Sangamon. A second phone on Android 33 walked Peoria, and its GPS is clearly worse. Which collector carried which phone is not in the data.
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

- **The video against the sensors.** During the six largest turns of each session, the image's sideways slide matches the gyroscope's rate about gravity closely (correlation 0.97–0.996). The camera shows each turn about 0.3 s before the sensor clock records it. The gap grows by about 0.2 s per hour, and both values are the same on both phones and all three days. Within a session, the windows agree within 0.15 s. Two of the 48 windows had no clear correlation and are left out. Whether the cause is the app's sample time stamps or the video's start time in the metadata is not settled. For the graph it is a correction: video time = sensor time + the offset at that moment.
- **Frame times hold.** Every frame's time stamp is within 0.03 s of its index ÷ 30, so the workspace's frame times are right.
- **GPS lags the sensors by 0.6–2.0 s**, but with weak correlation (0.14–0.61, weakest on the Android 33 phone), because the course from fixes is noisy at walking speed. Take about 1–2 s as the bound.
- **No sync tap.** No session shows three knocks that match in the accelerometer and the audio, and the West Loop documents do not call for them. The rotation check replaces the tap, and it is better: one measurement per turn over the whole session, not one at the start.
- **The lens.** The slide per degree of turn gives a horizontal focal length of about 1460 px at 1920 px width, a field of view of about 67°. This is rough: the pitch, stabilisation and walking all add to the slide. It is a prior until the checkerboard calibration.

## 3. Runs

On D1 and D2, the walk splits into 27–32 runs and 47–51 crossing candidates per session. A run along the street is typically a block long (median 79–103 m).

- **GPS overstates crossing length.** Its displacement over a crossing is about 20 m, against about 13 m for Morgan's crosswalks. The end positions include standing at the curb, plus the fix error. So, as planned, a rung's length must come from timing and steps.
- **A known gap: straight crossings stay inside runs.** A crossing made straight on, over a cross street, has no turn, so it stays inside a run. Three were found on D2 at Madison (section 4). The fix is to split runs where the crosswalk mask is under the walker.

## 4. Side cue

Each run's cue is the side holding at least 70% of the car and curb boxes, from 5 boxes up; otherwise it abstains. The table counts runs of at least 20 m along the street axis:

| Session | NS runs: agree / disagree / abstain | Madison (EW): left / right / abstain |
|---|---|---|
| D1 15-43 | 16 / 0 / 5 | — |
| D1 16-37 | 18 / 0 / 3 | — |
| D2 16-38 | 14 / 2 / 3 | 3 / 0 / 0 |
| D2 17-32 | 16 / 1 / 2 | 2 / 1 / 1 |

- **D1 passes the gate.** All 34 runs where the cue decided agree with the protocol, and 8 runs (19%) abstain.
- **D2's three disagreements are not sidewalk runs.** Their frames show the collector at a curb or on a crosswalk, crossing Madison while heading north (section 3).
- **On Madison's jog, the cue caught a departure from the plan.** It says the road was on the left in 5 of 6 decided runs, with lopsided counts such as 399 cars on the left against 19. The module plan walks east–west streets with the road on the right, but on the jog the collector kept the road on the left, as on the north–south streets.
- **Under the protocol, the walking direction alone gives the side.** North–south streets are walked northbound on the east side and southbound on the west side, so heading decides which sidewalk. That makes it a baseline the joint inference must beat. The cue's value lies elsewhere: catching departures, as on Madison, and handling natural walks.

## 5. Zones

The contact sheets, `zones_<session>.jpg`, show 24 frames each, with the masks drawn over them:
- blue: `sidewalk`
- orange: `curb`
- green: furniture

| | Morgan (D1 15-43, 3 blocks, 232 frames) | Carpenter and Aberdeen (D2 16-38, 3 blocks, 248 frames) |
|---|---|---|
| The street | Paved to the curb, no parkway | Grass parkways, tree pits, planters; stoops and fences on the building side |
| Road-side curb found | 56% of frames | 10% |
| Unpaved strip between curb and paving | 21% (tree pits) | 4% measured; grass is visible but not segmented |
| Furniture on the road side | 34% (poles, parking meters, trees, bicycle racks); bases at a median 22% of the way from curb to building side | 28%; trees mostly stand beyond the paving, in the parkway |

- **The furniture zone can be measured on commercial streets** like Morgan. There it is a strip along the curb, and the offsets of its objects' bases give its width over a block.
- **Parkways cannot be measured with the current prompts.** There is no `grass`, `road` or `building` prompt. Worse, `curb` also fires on the edge where the sidewalk meets a building ledge, on both days.
- **No prompt separates the frontage zone.**
- **So the zone gate is met only in part.**

## 6. Gates

| Gate (plan, phase 0) | Result |
|---|---|
| Every stream used has a measured alignment bound | **Met.** Video against sensors: −0.28 to −0.39 s, drift about −0.2 s per hour, windows agreeing within 0.15 s. GPS: 0.6–2.0 s late. Frame times within 0.03 s |
| The side cue works on a stated share of D1 runs | **Met.** 34 of 34 decided runs agree; 19% abstain |
| Zones kept where the masks separate them | **In part.** The furniture zone along the curb on Morgan; parkways and frontage need new prompts |
| D3's streets, collectors and phones | Streets and phones confirmed; collectors still to confirm |
| Lens calibration video and camera height | **Not done** (fieldwork). A rough focal length of 1460 px comes from the rotation check |

## 7. What this changes, and decisions for Renzo

1. **Correct the sensor times.** Apply each session's offset and drift (section 2) when sensor events join the video: in the graph code first, and in sideseeing-tools' `sensor_signal` if it holds.
2. **A second SAM3 run with zone prompts.** `road` (already plan decision 4), plus `grass`, `tree pit`, `building` and `fence`, on D1 and D2. This is GPU time on desktop-01 after the current run, so it needs your approval.
3. **Add the protocol rule (side from walking direction) to the baselines** in plan section 6.
4. **Split runs at straight crossings** where the crosswalk mask is under the walker, before phase 2.
5. **From the field:** the checkerboard video, each collector's camera height, and who carried which phone on D3.

Phase 1, the reference, needs people. Phase 2, the ladder on Morgan, can start alongside it, checked against D1's protocol sides until the reference exists.
