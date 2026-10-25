# Phase 2a notes: the ladder on Morgan (in progress)

25 October 2026. Phase 2a of the [graph and GPS plan](GRAPH_GPS_PLAN_2026-10-24.md), section 8, phase 2: steps, the ladder fit on D1 (Morgan, both sessions) and its baselines.

The geometry is sealed: its numbers stay in `data/west_loop_graph/phase2a/` until Renzo has traced the reference on Morgan (phase 1), so that the trace is made blind. This note records:
- what was built;
- what can be shown now;
- what the first fits taught about the model;
- what waits for the reference.

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

## 4. What waits for the reference

- **The GPS pull.** It is one value per session, and the two sessions get clearly different values. It probably varies along the street with the buildings, which is the plan's risk "the GPS bias is not systematic". A pull that varies along the street is the likely next change.
- **The walking lines' separation** varies along the street more than Morgan's layout suggests. The reference will say where the lines are right.
- **The crossings' length by steps** is longer than a walk from the walking line to the far curb would be. Either the turnaround lies past the curb, or strides are longer while crossing. Curb-to-curb widths from the reference will tell.
- **One session alone** places its walking line sideways only through the few fixes taken while crossing, so pull and line trade off. The simulated checks show it too.
- **The two conflict zones** become alternative groups (phase 3).

## 5. Next

1. Renzo checks the curbs and traces the back of the sidewalk on Morgan (`network/graph/trace.html`), then exports `data/west_loop_reference/morgan_trace.geojson`.
2. Unseal and evaluate against that reference, for the ladder and each baseline:
   - whether each walking line falls inside the sidewalk, and how far it sits from its centreline;
   - where the crossings end against the curbs;
   - the phase 2 gate.
3. Then decide on the changes above, with a frozen setting before D3.
