# Calibration day: plan for discussion

Draft, 3 November 2026. A field day to calibrate what the pipeline measures, collector by collector and phone by phone, and to build error models against tape and level. It answers Renzo's calibration idea in the [graph paper plan](GRAPH_PAPER_PLAN_2026-11-03.md) (section 14, idea 1). The day is built from **modules**: one full day on Morgan first; any module can then be repeated on another kind of block, if the first day shows that the errors depend on the block. A 10-minute **daily routine** for every collection day follows at the end.

## 1. Why: what each module fixes

Every module answers a problem already measured on our data.

| Module | Problem it addresses | Measured so far |
|---|---|---|
| CAL-0 Setup | The camera's height sets every distance from the video. The mount's angle changes between sessions | Height 1.30 m measured, against 1.43–1.49 m from ground motion ([phase 2b](GRAPH_PHASE2B_NOTES_2026-10-27.md) §7). Walking pitch 18.7–22.8° between sessions; the phone sat the other way round in some ([pilot 2](../notebooks/pilot2_test.ipynb), findings §4) |
| CAL-1, CAL-11 Still and sync | Sensor bias; barometer drift; clock alignment | Sync taps are the protocol's ([PILOT2_PROTOCOL.md](archive/PILOT2_PROTOCOL.md)) |
| CAL-2 Checkerboard | The lens: focal length and distortion; whether stabilisation crops | Focal length about 1460 px, from turns only ([phase 0](GRAPH_PHASE0_RESULTS_2026-10-25.md)); no distortion model |
| CAL-3 Step course | Step length per collector and pace; GPS error along the street | 0.78 m per step on the West Loop days (October plan §5), one collector |
| CAL-4 Width spots | Video widths against tape | Video 2.17 and 2.30 m against about 2.2 and 2.3 m on the orthophoto, on Morgan only ([phase 2b](GRAPH_PHASE2B_NOTES_2026-10-27.md) §7) |
| CAL-5 Lateral lines | The video's distance from the curb; GPS's sideways error at a known offset | Curb distance 1.28 and 1.51 m from the video, never checked against a known line |
| CAL-6 Crossings | The rung: where the walker turns around on the far side | The far end lies a median 1.9 m past the far curb ([phase 2a](GRAPH_PHASE2A_NOTES_2026-10-25.md) §4); each crossing good to about 1.5 m |
| CAL-7 Slope, ramps, tactile paving | Running and cross slope from gravity and the video; the tactile paving as a ruler | No reference measurement yet |
| CAL-8 Stair and curb | Whether the barometer sees a storey and a curb | Planned in pilot 2 (`P2-BARO`), not reported in its findings. Noise about 7 cm ([pipeline](GRAPH_PIPELINE_2026-11-03.md) §8) |
| CAL-9 Wi-Fi repeats | The Wi-Fi side cue needs the same side walked twice | A modest signal on D2, between opposite sides only ([pipeline](GRAPH_PIPELINE_2026-11-03.md) §8) |
| CAL-10 Under the 'L' (optional) | GPS, light and magnetometer under elevated steel | Lake St runs under the Green and Pink Lines ([WEST_LOOP_COLLECTION.md](WEST_LOOP_COLLECTION.md)) |

## 2. Where, who, what to bring

**Where: Morgan St.** The reference already exists there (the City's curbs checked on the orthophoto, the back of the sidewalk). Everything measured on the day joins it and checks it. Choose on the orthophoto and the D1 video, before the day:
- **Block A:** a block with a parkway (trees, tree pits or grass between the curb and the paving).
- **Block B:** a block without one.
- Two **corners with curb ramps and tactile paving**, for CAL-6 and CAL-7.
- **A grade**, if there is one: Morgan's bridge (left out of the reference read in phase 2a) is the first candidate. Check its slope on site.
- **A public stair** of at least one storey, for CAL-8. To find before the day, with its access checked.
- **Morgan and Lake,** for CAL-10.

Morgan is a development street, so nothing here touches the test set.

**Who:**
- **The collector** (Renzo) wears the vest and walks.
- **A helper** measures, fills in the field sheet, takes photos and watches traffic.
- **Volunteers,** if they come: each does CAL-0 to CAL-3 with their own phone.

**Equipment:**

| Item | For |
|---|---|
| 30 m tape and 5 m tape | Step course, widths, offsets |
| Digital inclinometer or level, 0.1° resolution | Slopes; checking level ground for CAL-2 |
| Checkerboard: a standard calibration pattern printed on rigid board (for example, 9 × 6 inner corners, 40 mm squares, A3 foam board). Measure the printed square size | CAL-2 |
| Painter's tape and a few small cones (removable markers only) | Spots, lines, start and end marks |
| Clipboard, field sheets (section 4), pen | Records |
| A second phone for photos | One photo per spot |
| Each collector's phone, the vest, a power bank | Recording |

## 3. The modules, in order

Times are estimates for one collector and one phone. Record each module as **its own MultiSensor session**, with the usual still start, sync taps and spoken ID (`CAL-3 start`…), unless it says otherwise.

| # | Module | What to do | Time |
|---|---|---|---|
| **CAL-0** | Setup | For each collector: (1) Measure the camera's height on the vest, standing upright in walking shoes, from the ground to the centre of the lens. (2) Photograph the phone in the vest from the side, with a ruler, showing its tilt. (3) Check that the lens is on the same side as on collection days, and the app's angle against a target. (4) Confirm the settings used for collection (video mode, Game sensor delay) | 10 min |
| **CAL-1** | Still and sync | 60 s standing still with the vest on, then the three taps and the session ID | 2 min |
| **CAL-2** | Checkerboard | For each phone, in the collection video mode: (1) Hold the board 1–4 m away and move it slowly through every part of the frame, tilted in several directions, for about 90 s. (2) Lay the board on ground checked as level, and record it from the vest standing still, for 30 s: this gives the angle between the camera and the gravity sensor | 15 min per phone |
| **CAL-3** | Step course | Tape a straight 20 m stretch on Block A and mark both ends. Walk it at normal pace 3 times each way, slow 2 times each way, and fast once each way. Stand 3 s at each mark | 20 min |
| **CAL-4** | Width spots | Before the collector walks: the helper marks 10–15 spots along Blocks A and B (narrow and wide, with and without obstacles, one under a tree, one at a driveway) and measures, at each, the total width (curb face to the back of the sidewalk), the paved width, the clear width (narrowest free passage) and each zone. Then the collector walks the blocks at normal pace, stops 3 s at each spot facing along the walk, and says the spot's number | 45 min |
| **CAL-5** | Lateral lines | On a wide stretch of Block A, mark short pieces of painter's tape at 0.5 m, 1.0 m and 1.5 m from the curb face (if the paving allows), every 10 m. Walk the block along each line, each way | 20 min |
| **CAL-6** | Crossings | At one corner, cross the street on WALK only, 4 times: twice stopping with the toes at the far curb (marked), twice turning around as on collection days. Repeat at a second corner. The crossing's length comes from the reference, not from a tape across the road | 15 min |
| **CAL-7** | Slope, ramps, tactile paving | With the inclinometer: running and cross slope at 5 of the CAL-4 spots and on the grade if there is one; the running slope of 2–3 curb ramps; the depth of 5–10 tactile panels in the direction of travel (tape). At each, the collector stands still for 5 s on the spot | 20 min |
| **CAL-8** | Stair and curb | 30 s still at the bottom of the stair, climb, 30 s still at the top, come down, 30 s still. Count the steps and tape one riser. Then step down one ordinary curb and stand 10 s | 10 min |
| **CAL-9** | Wi-Fi repeats | One block of Morgan: east side north, cross, west side south, cross, and repeat, so that each side is walked twice in one session | 15 min |
| **CAL-10** | Under the 'L' (optional) | Walk one block of Lake St beside the elevated structure's columns, each side, at normal pace | 15 min |
| **CAL-11** | Still and sync, end | 60 s still, three taps, `CAL end` | 2 min |

**Total:** about 3.5 hours for one collector, plus about 30 minutes per extra volunteer (CAL-0 to CAL-3). Finish well before dusk: the light falls quickly in November (D2 S2 dropped below 35 lux, [October plan](GRAPH_GPS_PLAN_2026-10-24.md) §10). Choose a dry day; wet paving changes the masks.

**Safety and courtesy:**
- Measure only on the sidewalk, never across traffic.
- Cross only on WALK.
- The helper watches traffic during CAL-6.
- Do not block passers-by.
- Use removable markers and take them away afterwards.
- Ask before using a stair on private property.

## 4. Field sheet

One row per measured thing. Times are local, read from the collector's phone clock when possible.

```
module, spot_id, time, block, kind, total_width_m, paved_width_m, clear_width_m, zone_widths_m, offset_from_curb_m,
running_slope_deg, cross_slope_deg, depth_m, photo, notes
```

**Examples:**

```
CAL-4, S07, 14:12, A, width, 3.10, 2.25, 1.60, "parkway 0.85; through 1.60; frontage 0", , , , , IMG_0412, tree pit narrows the clear width
CAL-7, S07, 14:51, A, slope, , , , , , 1.2, 1.8, , IMG_0430,
CAL-7, R02, 15:03, NE corner Morgan/Monroe, ramp, , , , , , 4.6, , , IMG_0433, aligned with crosswalk
CAL-7, T03, 15:05, NE corner Morgan/Monroe, tactile, , , , , , , , 0.61, IMG_0434,
```

The values in the examples are invented to show the format.

## 5. Where the data go

- **Captures:** Drive and RustFS as usual, in a `calibration` folder. A local copy goes in `network/data/calibration_<date>/raw/`.
- **The field sheet** (CSV) and the photos: `network/data/calibration_<date>/`.
- **The tape, level and tactile measurements** also join the Morgan reference, with their source marked as *field*.
- **Every calibration session is development data.**

## 6. What comes out, and where it is used

| Result | From | Used by |
|---|---|---|
| Camera height and mount angle per collector; their spread between days | CAL-0, the CAL-3 ground motion | S3 camera pose |
| Focal length and distortion per phone; the camera–gravity angle | CAL-2 | S3 camera pose |
| Step length per collector and pace | CAL-3 | S2 motion; S5 odometry |
| Error of video widths against tape, by width and zone (an error model, not one number) | CAL-4 | S4 measurements; S10 station uncertainty; Gate 2 |
| Error of the video's curb distance at known offsets; GPS sideways error at a known offset | CAL-5 | S5 "edges" term; the ablation matrix |
| The far-end overshoot of a crossing, per collector | CAL-6 | S5 rung term |
| Slope error against the level; tactile paving depth as a ruler | CAL-7 | S10 stations; Gate 2 |
| Whether the barometer sees a storey and a curb | CAL-8 | Exploratory sensors |
| The Wi-Fi side cue on same-side repeats | CAL-9 | Exploratory sensors |
| GPS, light and magnetometer under steel | CAL-10 | Exploratory sensors |

**When to repeat modules elsewhere.** If CAL-4 or CAL-5 show errors that depend on the block (a parkway, trees, a wide sidewalk), repeat those two modules on one or two blocks of another kind. This is where more than one pilot pays off. A short repeat of CAL-0 to CAL-3 on another day measures how stable the parameters are.

## 7. The daily routine (every collection day, about 10 minutes)

1. Check the phone's orientation in the vest and the app's angle against the target (pilot 2: the mount changes between sessions).
2. If the vest or the collector changed, measure the camera's height.
3. 60 s still, three taps, session ID: already the protocol's start.
4. Walk a 10 m stretch between two tape marks, once each way, at normal pace.
5. At the end of the day: 60 s still, three taps.

## 8. To discuss before the day

- **The blocks:** which two Morgan blocks, which corners, the grade and the stair.
- **People:** who helps, and whether any volunteers join for CAL-0 to CAL-3.
- **Equipment:** whether a digital inclinometer is available, and the checkerboard print.
- **The date:** dry, with enough daylight; and whether CAL-10 fits.
- **The repeat:** whether to plan a second, shorter day now (CAL-0 to CAL-3 and CAL-9), or wait for the first day's results.
