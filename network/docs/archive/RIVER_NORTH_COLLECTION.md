# River North collection: field rules and route plan

Draft, 16 October 2026. River North is the selected area for the full collection. This document turns the pilot measurements into field rules and plans the routes. Team size, hours per day, and the day-by-day schedule are still open. They will be settled next, using the route plan below.

## 1. Decisions taken on 16 October 2026

| Decision | Choice |
|---|---|
| Boundary | Land between the **Chicago River** (south and west), the **Chicago Ave centreline** (north) and the **Michigan Ave centreline** (east): 1.45 km². |
| Boundary streets | **Both sides** of Chicago Ave and Michigan Ave are collected, along with the crosswalks over them. With these outer sidewalks, the collection area is 1.53 km². |
| Crossings | **Every legal crosswalk** is traversed once. A crossing that is only visible from the sidewalk does not count. |
| Team and daily hours | Open. To be settled after this route plan. |

**This boundary is not the cross-city model's River North.** The model scored the City of Chicago neighborhood polygon (`Boundaries_-_Neighborhoods_20261013.geojson`, 3.60 km²). That polygon also includes Goose Island and the area north of Chicago Ave up to Division St and North Ave. Any comparison with the model must state this difference.

**Proposed, not yet confirmed:** do not collect lower-level streets (Lower Michigan, Lower Wabash, Lower North Water, Lower Illinois), bridges, the Riverwalk, or private plazas. Lower levels have no usable GPS and are not ordinary street sidewalks. Bridges lead out of the area. The Riverwalk and plazas are not street-adjacent, which keeps the scope consistent with the [collection protocol](../COLLECTION_PROTOCOL.md).

## 2. What the pilot measured

These figures are from the three Near West Side sessions of 14 October 2026 (moto g 5G 2023). The GPS figures are in [`pilot_gps_overview.ipynb`](../../notebooks/pilot_gps_overview.ipynb). The other figures come from the raw `metadata.json`, `gps.csv`, `sensors.*.csv` and `consumption.csv` files.

| Measurement | Pilot value | Consequence for River North |
|---|---|---|
| Time until GPS accuracy stays ≤ 6 m for 10 s | 9–14 s after the video starts | Stand still for 30 s at the start (rule F1). |
| Standing time at the start of each session | 4–5 s (from the accelerometer) | The pilot started walking before GPS had settled. Its first 20 s had reported accuracy as poor as 39 m. |
| Stops of ≥ 3 s between start and end | **None** in any session | The pilot gives no measurement of signal waits. River North has 342 signalised crosswalks, so the first field day must measure waits (section 6). |
| Walking speed (4-s rolling median) | 1.38–1.45 m/s | Plan with 1.4 m/s. |
| Reported GPS accuracy (median) | 3.2–4.1 m | Residential streets only. Tall buildings and the elevated 'L' are untested (section 6). |
| Gap between tracks on opposite sides of Carpenter and Miller | about 9 m (3 m bins, so roughly 6–12 m) | Opposite sides were separable on narrow streets. This measures track-to-track distance, not error against the real sidewalks. |
| Video recorded | 1920×1080 at 30 fps, as set | MultiSensor records at `camera_resolution` (3 = FHD; 4 = UHD). The `camera: 4000x2250@15` field in `metadata.json` is not used for recording, and the frame rate is the camera library's default. Rule S1. |
| Storage | 9.1 GB per recording hour (video) | A 3-hour day is about 27 GB. |
| Battery current while recording | 946–990 mA | About 1 Ah per recording hour. Carry a power bank. |
| Sensor rates with `sensors_delay: 3` (Normal, per the app source) | Raw accelerometer and uncalibrated gyroscope 99 Hz. Magnetometer 52 Hz. Pressure 10 Hz. **Calibrated gyroscope, gravity and linear acceleration 5 Hz.** | Test a faster sensor setting before day 1 (rule S2). |
| Standing still vs walking, 99 Hz accelerometer | Per-second std of acceleration magnitude: below 0.3 m/s² only while standing; walking median 3.0 m/s² | Short deliberate stops are detectable without manual labels, which is why rule F3 exists. |
| `deviceStartAngle` in metadata | +78.6° (R01), −79.9° (G01), −78.1° (P01) | The sign flip may mean the phone was mounted the other way up in R01. This is unverified. Check the R01 video before fixing the mounting rule (rule S3). |

## 3. Field rules

These rules standardise the pauses so that every recording has the same structure. The structure is: still start, walking, a still curb pause before each crossing, the crossing, walking, and a still end. The stops then mark crossings in the sensor data automatically, and every crossing approach gets the same camera view.

**F1. Start.** Stand at the leg's start corner, facing the walking direction, with the phone already in the vest. Press record and stand still for **30 s**.

**F2. End.** At the end of the leg, stand still for **10 s**, then stop recording. Check that the recording saved before moving on.

**F3. Curb pause.** Stop at the curb before **every** crosswalk for at least **3 s**, even if the signal already shows WALK. This creates a stillness marker in the accelerometer. It also gives a steady view of the curb ramp, the markings and the signal head.

**F4. When to cross.**
- Cross only at a crosswalk, and continue **straight ahead** along the sidewalk line. The route plan relies on this (section 4).
- At a signal, start crossing **only on a fresh WALK phase**. If you arrive during the countdown or a flashing DON'T WALK, wait for the next cycle. This keeps waits comparable and crossings safe.
- At an uncontrolled or stop-controlled crosswalk, cross when it is safe, after the curb pause.
- Never cross diagonally, and never mid-block, unless the route card lists a marked mid-block crosswalk.
- If a crosswalk is closed, missing or prohibited, do not cross. Continue to the next legal crosswalk, and log the target as *not crossable* with the time.

**F5. No other stops.** Walk at an ordinary pace. If a crowd, obstruction or anything else forces you to stop, stand, keep recording, continue, and log it at the end of the leg. Do not stop to look at things.

**F6. Walking line.** Walk in the middle of the clear walking zone and keep the same line throughout. Do not drift toward the building or the curb, and do not touch the phone while walking or crossing.

**F7. Sessions.** One session is one leg (one side of one street), named by its plan ID, e.g. `ERIE-N`. A restart gets a new suffix (`ERIE-N.2`), and the failed folder is kept. A leg ends after the U-turn crosswalk at the far end (section 4), and the next leg starts there with F1.

**F8. Log.** For each leg, record the ID, capture folder, start and end time, and any deviations, closures, crowding or stops. Copy the original folders each day and check that video, GPS and sensor files open before deleting anything from the phone ([collection protocol §7](../COLLECTION_PROTOCOL.md)).

**Settings to freeze before day 1** (verify each one on a short test export, not just in the app):

- **S1.** Video resolution: FHD (`camera_resolution` 3) or UHD (4). Test UHD in Pilot 2 for storage and detail. Keep the zoom at 1.0 and do not touch the preview: MultiSensor supports pinch-to-zoom while recording.
- **S2.** Sensor rate. Record 2 minutes with a faster `sensors_delay` and compare stream rates and file sizes with the pilot. Keep the faster setting only if the 5 Hz calibrated streams improve.
- **S3.** Mounting orientation. Choose one orientation, record which side the lens is on, and use it in every session.
- **S4.** GPS interval 1 s, Battery Saver off, about 10 GB free per recording hour, and a power bank.

## 4. Route plan

**Rule: walk each street out on one side and back on the other, crossing straight ahead at every intersection.** In a grid, each corner has two sidewalks and two crosswalks. If you walk along street S, crossing straight ahead takes you over the crosswalks that cross the perpendicular streets. So every sidewalk side and every crosswalk is walked exactly once by the street it continues. The only repeats are at the far end of each street, where you cross back over the street you are walking (the U-turn). That U-turn crosswalk also belongs to the perpendicular street's module, so it is recorded twice. That repeat is the planned overlap (route join) between the two modules.

- East–west streets: the out leg is the **north side, eastbound**; the back leg is the **south side, westbound**.
- North–south streets: the out leg is the **east side, northbound**; the back leg is the **west side, southbound**.
- Each module starts and ends at the same end of its street, on opposite sides. Moving to the next module is about one block.

`network/routes.py river_north` builds the plan from OpenStreetMap (snapshot of 16 October 2026). It assigns every mapped sidewalk and crosswalk piece to the nearest parallel street within 30 m, and to a side of that street. OSM is a planning inventory: field observations override it. The outputs are in `data/river_north/` (not versioned):

- `sessions.csv`: one row per leg, with endpoints and counts.
- `cards/<MODULE>.png`: one route card per module, with ▲ marking the start of each leg.
- `overview.png`: all modules on one map.
- `unassigned.csv`: the review list.
- `routes.gpkg`: every assigned piece, for GIS.

**Coverage of the OSM inventory:** 42.4 of 43.2 km of sidewalk (98%) and 6.7 of 7.2 km of crosswalk (94%) are assigned. The plan has 26 modules and 52 legs, with 447 crosswalks, 342 of them signalised.

| Module | Out leg | Back leg | Sidewalk (m, both sides) | Crosswalks (with signals) | Walking min |
|---|---|---|---:|---:|---:|
| MICHIGAN | `MICHIGAN-E` Illinois → Chicago | `MICHIGAN-W` Chicago → Wabash | 1,409 | 13 (13) | 19 |
| RUSH | `RUSH-E` Grand → Chicago | `RUSH-W` Chicago → Grand | 1,072 | 14 (8) | 15 |
| WABASH | `WABASH-E` State → Chicago | `WABASH-W` Chicago → State | 1,467 | 15 (8) | 20 |
| STATE | `STATE-E` Wabash → Chicago | `STATE-W` Chicago → Wabash | 1,709 | 21 (20) | 24 |
| DEARBORN | `DEARBORN-E` State → Chicago | `DEARBORN-W` Chicago → Clark | 1,696 | 20 (20) | 24 |
| CLARK | `CLARK-E` Dearborn → Chicago | `CLARK-W` Chicago → LaSalle | 1,653 | 20 (20) | 23 |
| LASALLE | `LASALLE-E` Clark → Chicago | `LASALLE-W` Chicago → Wells | 1,504 | 20 (20) | 22 |
| WELLS | `WELLS-E` Merchandise Mart → Chicago | `WELLS-W` Chicago → Merchandise Mart | 1,645 | 21 (21) | 23 |
| FRANKLIN | `FRANKLIN-E` Kinzie → Chicago | `FRANKLIN-W` Chicago → Hubbard | 1,384 | 18 (10) | 20 |
| ORLEANS | `ORLEANS-E` Merchandise Mart → Chicago | `ORLEANS-W` Chicago → Merchandise Mart | 1,603 | 19 (18) | 23 |
| SEDGWICK | `SEDGWICK-E` Erie → Chicago | `SEDGWICK-W` Chicago → Erie | 470 | 5 (0) | 7 |
| KINGSBURY | `KINGSBURY-E` Kinzie → Chicago | `KINGSBURY-W` Chicago → Kinzie | 1,564 | 17 (7) | 22 |
| HUDSON | `HUDSON-E` Erie → Chicago | `HUDSON-W` Chicago → Erie | 446 | 11 (0) | 7 |
| LARRABEE | `LARRABEE-E` Huron → Chicago | `LARRABEE-W` Chicago → Erie | 424 | 4 (2) | 6 |
| WOLF_POINT | `WOLF_POINT-N` Kinzie → Orleans | `WOLF_POINT-S` Orleans → Kinzie | 381 | 3 (1) | 5 |
| MERCHANDISE_MART | `MERCHANDISE_MART-N` Orleans → Wells | `MERCHANDISE_MART-S` Wells → Orleans | 191 | 2 (2) | 3 |
| KINZIE | `KINZIE-N` Kingsbury → North Water | `KINZIE-S` Wabash → Kingsbury | 1,790 | 14 (12) | 24 |
| HUBBARD | `HUBBARD-N` Kingsbury → Wabash | `HUBBARD-S` Wabash → Kingsbury | 1,879 | 18 (13) | 25 |
| ILLINOIS | `ILLINOIS-N` Kingsbury → Michigan | `ILLINOIS-S` Michigan → Kingsbury | 2,069 | 19 (17) | 29 |
| GRAND | `GRAND-N` Kingsbury → Michigan | `GRAND-S` Rush → Kingsbury | 2,322 | 23 (23) | 32 |
| OHIO | `OHIO-N` Kingsbury → Michigan | `OHIO-S` Michigan → Kingsbury | 2,206 | 19 (19) | 30 |
| ONTARIO | `ONTARIO-N` Kingsbury → Michigan | `ONTARIO-S` Michigan → Kingsbury | 2,453 | 20 (20) | 33 |
| ERIE | `ERIE-N` Larrabee → Michigan | `ERIE-S` Michigan → Larrabee | 2,729 | 25 (14) | 37 |
| HURON | `HURON-N` Larrabee → Michigan | `HURON-S` Michigan → Larrabee | 2,716 | 29 (15) | 37 |
| SUPERIOR | `SUPERIOR-N` Larrabee → Michigan | `SUPERIOR-S` Michigan → Larrabee | 2,784 | 27 (14) | 38 |
| CHICAGO | `CHICAGO-N` Larrabee → Michigan | `CHICAGO-S` Michigan → Larrabee | 2,867 | 30 (25) | 39 |
| **Total** | 52 legs | | **42,433** | **447 (342)** | **585** |

"From" and "to" name the nearest cross street to each end of the leg, as OSM gives it. Walking minutes assume 1.4 m/s and **exclude signal waits, rituals and repositioning**.

### Places that need a site check before their module is walked

- **Multi-level block east of Wabash and south of Grand** (Rush, Illinois, Hubbard, Michigan, Kinzie, North Water). OSM marks these street segments as lower level, but not their sidewalks, so which sidewalks are at street level cannot be read from OSM. This is why Kinzie and Hubbard stop at Wabash, Grand's south side stops at Rush, and Michigan's east side starts at Illinois. Most of the review list is here.
- **Riverfront pieces**: Wolf Point Plaza, the Merchandise Mart frontage, and the Clark and Kinzie approaches near the river. These may be private or plaza space. MERCHANDISE_MART has a sidewalk on one side only (6 m on its south side).
- **Larrabee and Michigan are lopsided.** Larrabee has 109 m on its east side against 315 m on its west side. Michigan has 641 m on its east side against 768 m on its west side. Check whether one side lacks a sidewalk or OSM is incomplete.
- **Under the elevated 'L'**: the North Side Main Line runs over **Franklin St for its full length** and over Wells near the Merchandise Mart. Expect the worst GPS and dark video there.
- **Unassigned crosswalks** (32 pieces, 415 m): mostly mid-block crossings and crossings over ramps. A marked mid-block crosswalk is added to its module's route card as a cross-and-return, with the return logged as a repeat.

## 5. Workload, before measuring signal waits

| Component | Estimate | Basis |
|---|---|---|
| Walking | 9.7 h | 42.4 km of sidewalk plus crosswalk length, at the pilot's 1.4 m/s |
| Start and end rituals (F1, F2) | about 35 min | 52 legs × 40 s |
| Signal waits | **unknown** | 342 signalised crosswalks × mean wait. For scale only: a 30 s mean would add 2.9 h and a 60 s mean 5.7 h. |
| Repositioning | small | About one block between modules |
| Revisits and review places | to be set | Collection protocol §3 requires a reserve |
| Storage | 9.1 GB × recording hours | Pilot rate |

## 6. Pilot 2 and the first River North day

**Pilot 2** ([PILOT2_PROTOCOL.md](PILOT2_PROTOCOL.md)) runs near UIC on 16 October 2026. It settles:
- the sensor speed and the video resolution;
- the voice protocol and its vocabulary;
- the barometer and magnetometer checks;
- GPS under elevated track, on Paulina St below the Pink Line.

**The first River North day** walks the two things the UIC area cannot test, and re-measures signal waits:
- **FRANKLIN**, entirely under the 'L';
- **ONTARIO**, past tall buildings.

Its measured waits complete the workload estimate in section 5.

## 7. Open items for the next discussion

1. Team: who records, on which phones, and how many vest setups exist.
2. Hours per day, and the module order per day. Modules are independent, so they can be assigned to different collectors.
3. Time of day and day of week. Pedestrian crowds, parked cars and building shadows all affect what the camera sees.
4. Confirm the exclusions proposed in section 1, and the site checks in section 4.
5. Results of settings tests S1–S3, from Pilot 2.

Related documents: [collection protocol](../COLLECTION_PROTOCOL.md), [research plan](../PLAN.md), [pilot data plan](PILOT_DATA_PLAN.md).
