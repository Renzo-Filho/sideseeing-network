# Phase 2b notes: the curb from the video, on Morgan

27 October 2026. Phase 2b of the [graph and GPS plan](GRAPH_GPS_PLAN_2026-10-24.md), section 8, phase 2, following the [phase 2a notes](GRAPH_PHASE2A_NOTES_2026-10-25.md), section 6, item 2. D1 only (Morgan, both sessions). Nothing was run on D3 or on the GPU.

## 1. What was built

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

## 2. What the video measures

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

## 3. Against the reference

| | Step 1 (far ends tied) | Phase 2b |
|---|---|---|
| Separation, median error | 1.77 m too close | **0.92 m too close** |
| Shared shift, \|median\| \| p90 | 1.10 \| 3.09 m | 0.94 \| 3.13 m |
| Inside the sidewalk, east \| west | 36% \| 48% | **41% \| 62%** |
| Median distance to its middle, east \| west | 1.75 \| 1.84 m | 1.65 \| 1.51 m |
| In the road, east \| west | 37% \| 30% | 32% \| 21% |
| On the street's other half | 0% | 0% |

Every measure moved the right way. The gate is still half met: the lines are nearer the middle than the smoother's on both sides, but are not inside the sidewalk most of the way on the east.

## 4. Calibration: two errors that partly cancel

Two errors pull in opposite directions:
- **Road width by steps, about 8% short.** The steps give 14.0 m. The road visible on the orthophoto measures 15.2 m at u = 650 and 15.35 m at u = 900. Cadence on the road equals cadence along the street (ratio 1.005), so a longer stride while crossing is not the cause. The likely cause is the sidewalk mask spilling over the curb ramps at both ends.
- **Camera scale, about 15% too large.** The video reads paved sidewalks of 2.5–2.7 m on both sides. The orthophoto shows about 2.2–2.3 m of concrete. A height near 1.27 m, rather than 1.45 m, would fit, and is also more typical for a vest. Ground-motion alignment can be pulled towards no motion by anything that moves with the camera, such as the walker's shadow, and that makes the height too large.

Because they partly cancel, the separation came out close: 17.5 m measured, against 17.65 m between the reference's sidewalk middles. Neither should be trusted alone.
- **Height:** the plan's second ruler, the tactile paving at curb ramps (at least 610 mm deep), is independent of the steps. A tape measure of the vest pocket's height at the next fieldwork would settle it outright.
- **Road width:** the far curb's projected distance ahead, added to the distance walked, gives a width that is independent of the threshold.

## 5. The reference at the half-metre level

Patches of the 2025 orthophoto across the street (u = 650 and 900) show two things, at the same size as the errors left:
- **Curbs:** at u = 650, both reference curbs lie 0.6 m west of the visible curb edges, a pure shift. At u = 900, the west curb is 0.7 m off and the east 0.2 m. Renzo redrew 23 pieces on the orthophoto and kept 86 of the city's 2010 lines. So the reference may mix two frames, about half a metre apart. Shifts that both curbs share leave widths unchanged; mixed lines do not.
- **East property line:** the concrete runs about 2.2 m from the visible curb to the building, but the parcel line sits 1.4 m out, inside the paving. So the reference's east sidewalk (1.95 m, curb to property line) is probably too narrow. That penalises "inside" on the east. Cook County's parcels are known to be shifted by a metre in places; roof lean in the orthophoto cannot move the paving.

Before the gate is read as final, the reference needs one consistent pass:
- curbs from a single source, in the orthophoto's frame;
- the back of the sidewalk where the paving meets buildings and fences.

## 6. Next

1. **Height from the tactile paving** (map-free, on desktop-01, no GPU); the road width from the far curb ahead.
2. **The reference:** one consistent pass for curbs and the back (section 5). Which source to use is Renzo's decision.
3. **The cells:** strips from the curb line and the paved edge along each walking line.
4. **Then** phase 3 on D2, and freeze the settings before D3.

## 7. Measured height and the road's full span (30 October)

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
