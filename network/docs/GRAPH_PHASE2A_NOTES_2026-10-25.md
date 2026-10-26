# Phase 2a notes: the ladder on Morgan

25 October 2026; results against the reference added 26 October (section 4). Phase 2a of the [graph and GPS plan](GRAPH_GPS_PLAN_2026-10-24.md), section 8, phase 2: steps, the ladder fit on D1 (Morgan, both sessions) and its baselines.

The geometry stayed sealed until the reference was fixed. This note records:
- what was built;
- the results that needed no reference;
- what the first fits taught about the model;
- the results against the reference, and the gate.

## 1. What was built

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

## 2. What can be shown now (no geometry)

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

## 3. What the first fits taught

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

## 4. Against the reference (26 October)

**The reference** (agreed 26 October; tracing by hand was dropped as unscalable):
- **Curbs:** the city's 2010 curb lines, checked by Renzo on the 2025 orthophoto. 86 of 109 pieces matched; 23 had changed and he redrew them.
- **Back of the sidewalk:** the property line, from Cook County's current parcels merged into blocks. Renzo spot-checked six places ("roughly right").
- **Read across the street every metre:** both edges are readable over 1,075 of Morgan's 1,799 m; intersections, the bridge and gaps are left out.
- **Widths (medians):** road 15.2 m, east sidewalk 2.0 m, west 2.9 m. Together that is 20.1 m, Chicago's standard 66 ft right of way.
- **Datum:** the city and county data are NAD83 and phone GPS is WGS84. At Morgan in October 2026 the same point is 1.0 m west and 0.9 m north in GPS coordinates. pyproj's default conversion ignores this, so `evaluate.py` moves the reference by it before scoring. Without the move, every walking line looked about a metre too far west.

`python -m graph.evaluate --reference ../data/west_loop_reference --fit ../data/west_loop_graph/phase2a --out ../data/west_loop_graph/phase2a/eval` writes the scores, the profile and a plot (`walking_lines.png`).

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

## 5. Crossings tied to the far line (26 October)

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

## 6. Next

1. ~~Tie each crossing's far end to the far walking line.~~ Done (section 5).
2. **Phase 2b, the video's curb offsets.** The camera sees the curb. Projecting the curb and sidewalk masks gives each run's distance from the curb with no map, which is the plan's "edges" term (section 6). It also gives the cells.
   - **The road's width by steps:** the steps taken while the crosswalk is underfoot (already detected) measure it.
   - **The separation then follows:** road width plus the two curb offsets, so this should fix the separation that remains.
   - **It needs desktop-01:** the gravity stream gives the camera's tilt, and the second session's frames are there. The laptop has only D1's masks.
3. **A GPS pull that varies along the street**, if 1 and 2 leave a bias.
4. Every change is scored with `evaluate.py` on D1 only. The setting is frozen before D3.
