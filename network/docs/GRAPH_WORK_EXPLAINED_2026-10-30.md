# The passage graph work so far, in plain English

30 October 2026. A plain explanation of what was done for the graph paper up to now, what the Morgan map shows, and how all of it is meant to become the graph. For the technical details, see the [plan](GRAPH_GPS_PLAN_2026-10-24.md) and the notes for [phase 0](GRAPH_PHASE0_RESULTS_2026-10-25.md), [phase 2a](GRAPH_PHASE2A_NOTES_2026-10-25.md) and [phase 2b](GRAPH_PHASE2B_NOTES_2026-10-27.md).

## 1. The goal in one paragraph

A person walks the streets wearing a phone on a vest. The phone records video, GPS and motion sensors. From that alone, with no map, we want a map of where people can walk:
- **Sidewalks:** each with its width and obstacles.
- **Crossings,** and **the corners** that join them.
- **Which moves are possible** at each corner.

The hard part is that phone GPS is off by several metres. That's enough to put the walker on the wrong side of the street, or in the middle of the road. So the work has two halves:
1. **Correct the walk:** work out where on the street the walker really was. This is what has been done so far.
2. **Build the graph on top of it:** nodes, edges, sidewalk polygons and the moves between them. This has not started yet.

## 2. What was done, step by step

All of this is on one street so far, **Morgan Street**: set D1, two recordings on 19 October 2026. In one, the walker went north on the east sidewalk. In the other, they went south on the west sidewalk. Both times they crossed Morgan and came straight back at every crosswalk.

1. **Checking the data (phase 0).**
   - The video, motion sensors and GPS run on slightly different clocks; we lined them up.
   - GPS turned out to lag the walker by about one second.
   - The camera's zoom (its focal length) was measured from how the image slides during turns.
2. **A reference to score against (phase 1).** To know whether our answer is right, we need the true sidewalk:
   - **Curbs:** the City of Chicago's curb lines, which Renzo checked against the 2025 aerial photo, redrawing the 23 pieces that had changed.
   - **Back of the sidewalk:** the property line, from Cook County's land parcels.
3. **The walking lines (phase 2a).** For each sidewalk, the line the walker followed, worked out from steps, turns, crossings and GPS together (section 3 explains how).
4. **Crossings tied to the far side (26 October).** Every crossing ends on the other sidewalk, so its last step marks where the far walking line is. This fixed most of the error in how far apart the two lines were.
5. **Measurements from the video (phase 2b, 27 October).** The camera sees the curb. From each frame we measure:
   - **How far the walker is from the curb,** by projecting SAM3's curb outline onto the ground. This needs the camera's tilt (from the phone's gravity sensor) and its height. The height was first estimated from how fast the ground slides past the camera (about 1.45 m). Renzo then measured it on the vest: **1.30 m**, which is now used, and the video's sidewalk widths match the aerial photo.
   - **How wide the road is:** the steps taken from the first moment there is no sidewalk just ahead to the last, i.e. while the walker is on the road.

   Together these give how far apart the two walking lines should be: road width + each line's distance from its curb. Adding this halved the remaining error.
6. **A map of the results** (`data/west_loop_graph/map.html`, section 3).

**How good is it now?**
- The corrected lines are never on the wrong half of the street. Raw GPS is there 15–29% of the time.
- The lines are inside the sidewalk 42% of the way on the east side and 67% on the west. Raw GPS manages 18–36%.
- The two lines are 0.6 m closer together than the reference's sidewalk middles; at first they were 3.9 m closer.
- What's left is mostly a shift that both lines share over stretches of a few hundred metres, where GPS was off the same way in both recordings. Nothing in the recordings themselves can see that kind of error. The aerial photo, a later phase, can fix it.

**Still to fix:**
- **The camera's lens:** the checkerboard video will measure it exactly. Each road width is also only good to about 1.5 m, because there is one frame a second at each end.
- **The reference itself is off by about half a metre in places.**
  - Some city curb lines sit 0.6 m from the curbs visible on the photo.
  - On the east side, the parcel line falls in the middle of the paving.
  - It needs one consistent pass before the scores are final.

## 3. The map, layer by layer

Open the map by running `python3 -m http.server 8767 --bind 127.0.0.1` in `data/west_loop_graph/`, then visit http://127.0.0.1:8767/map.html. It stays on this laptop, because it contains parcel lines that may not be shared. The background is Cook County's 2025 aerial photo. Each layer can be switched on and off.

A note on alignment: the city and county data use one coordinate system (NAD83), and phone GPS uses another (WGS84). At Morgan they differ by about a metre, so everything from the phones is shifted by that amount before drawing.

### Reference layers (the "answer key", not from our recordings)

| Layer | What it is | How it was made | Role for the graph |
|---|---|---|---|
| **Reference curbs** (green) | The edge between sidewalk and road | The city's 2010 curb lines near Morgan, checked against the 2025 photo; 23 redrawn by Renzo | Used only to **score** our results, never as an input |
| **Reference back of sidewalk** (pink) | The property line, where the public sidewalk ends | Cook County parcels merged into whole blocks; the block outlines facing Morgan | Same: scoring only. Together with the curbs it outlines the "true" sidewalk polygon |

### What the phones recorded

| Layer | What it is | How it was made | Role for the graph |
|---|---|---|---|
| **GPS fixes** (white dots) | Where the phone *thought* it was, about 1.5 times a second | Raw `gps.csv` of both recordings, unchanged | The starting point we must improve on. It drifts across the road, which is why correction is needed |

### What our model computed

| Layer | What it is | How it was made | Role for the graph |
|---|---|---|---|
| **Walking lines: phase2a** (purple) | The line walked along each sidewalk, first version | The model in the box below, with steps, turns, crossings and GPS | Superseded by the blue lines; kept on the map for comparison |
| **Walking lines: phase2a_far** (orange) | Second version | Same, plus: each crossing's last step must land on the far sidewalk's line | Superseded; for comparison |
| **Walking lines: phase2b** (green) | Third version | Same, plus: the two lines must be "road width + both curb distances" apart, measured from the video and steps, with the estimated camera height | Superseded; for comparison |
| **Walking lines: phase2b_h130** (blue) | Current best version | As phase2b, with the measured camera height (1.30 m) and the road width over the whole time on the road | **The backbone of the graph.** Each sidewalk's walking line is the first, rough version of that sidewalk's edge, and the line the sidewalk polygon is built around |
| **Corrected track** (light blue, off at start) | Where the model says the walker was at each GPS moment | The model's position at each GPS time: moving along a blue line by steps, or straight across at crossings | The corrected GPS. Every video frame, detection and spoken comment is placed on the map through it |
| **Crossings by steps** (cyan) | Each trip across Morgan: 97 in all | From where the walker left their line, across by steps × step length, to where they turned around | The future **crossing edges**, and where they meet the sidewalk, the **ports** (passable openings, e.g. a curb ramp) of the corner polygons |
| **Curb where the video puts it** (red dots) | The curb, as seen by the camera | For each frame along the street: the walker's measured distance from the curb, drawn that far from the blue line towards the road | The first piece of a **sidewalk polygon**: its road-side boundary. Placed relative to the blue line, so it moves with it |

**How the walking-line model works.**
- **Splitting the walk:** the gyroscope cuts it into straight "runs" between turns. A run across Morgan is a crossing.
- **Heading:** each run's direction comes from adding up the turns, rounded to quarter turns (the street grid).
- **Side:** each run's sidewalk comes from the crossings. After crossing eastward, you're on the east sidewalk. No GPS is needed for this.
- **Unknowns:** the model describes the street as a centre line that may bend gently, plus two parallel walking lines either side of it. It also solves for each recording's step length (about 0.77 m), how far GPS is pulled towards the street's middle, and where each run starts.
- **Fitting:** it finds the values that best agree with all of the following at once:
  - the GPS fixes;
  - runs joining up at turns;
  - smooth, nearly parallel lines;
  - (orange and blue) crossings ending on the far line;
  - (blue) the measured distance between the lines.

  GPS fixes that are far off count much less than nearby ones, so one wild fix can't drag a line across the street.

**Not on the map:** the baselines in the score tables. These are raw GPS, a 5-fix median (what the viewer shows) and a "GPS + steps" smoother; all three are turned into lines the same way. The smoother uses the same steps and turns as our model. What it lacks is the knowledge that the walk happens on two parallel sidewalks joined by crossings. That knowledge is what our model adds.

## 4. From walking lines to the graph: lines and polygons together

The graph will have **two linked views of the same space**.

**The polygons (cells).** These split the walkable space into pieces:
- **Sidewalk strips:** one per side of the street per block, bounded by the curb on one side and the building or property line on the other.
- **Corner cells:** one per corner, where the sidewalks and crossings meet.
- **Crossing cells:** one per crosswalk.

**The lines (nodes and edges).** These form the usual network:
- **Edges:** each edge is the **centreline of a strip or crossing cell**. It is computed from the polygon, never drawn on its own, so the two views always agree.
- **Nodes:** each node sits in a corner cell, where the edges' centrelines meet.

```
 building ─────────────────────────────────────────────
 │  corner │      sidewalk strip (polygon)      │ corner │
 │   cell  │●════════ edge = centreline ═══════●│  cell  │   ● node
 │         │                                    │        │
 └─ curb ──┴────────────────────────────────────┴─ curb ─┘
     ║ crossing cell: edge = centreline ║
```

**Why both:**
- **The lines** are what routing tools, OpenStreetMap and Tile2Net use, so we can compare directly.
- **The polygons** keep what a line throws away: how wide the sidewalk is, where the obstacles stand, which part is clear to walk.

**How they connect:**
- **Ports:** two neighbouring polygons connect only through a port, a measured opening on their shared boundary, such as a curb ramp. A fence or a curb without a ramp separates them, even when they touch.
- **Transitions:** at a corner, which turns are possible (from this sidewalk, through this ramp, onto that crosswalk) is stored as a transition naming the two ports.

**How we get there from what exists now:**
1. **First graph, rough:** each blue walking line is a sidewalk's edge, each cyan crossing a crossing edge, and nodes go at the corners. This is the "level 0" graph, the next step.
2. **Sidewalk polygons:** take the curb line (red dots, smoothed along the street) and the sidewalk's paved edge on the building side (also measured in phase 2b) along each walking line. Together they outline the strip.
3. **Edges become centrelines:** once a strip exists, its edge moves from "where the walker went" to "the middle of the sidewalk". This is the "level 1" graph.
4. **Corners and crossings:** corner cells come from the turns and the crossing ends; crossing cells from the crosswalk outline seen while crossing.

## 5. How all the data is merged into the graph

Every kind of recording contributes something different. None of them is enough alone.

| Source | What it tells us | Where it goes in the graph |
|---|---|---|
| **GPS** | Roughly where on Earth the walk happened (± several metres) | Anchors the whole street's position; corrected by everything else |
| **Accelerometer** (steps) | Distance walked, step by step (about 0.77 m each) | Edge lengths; crossing lengths; how far apart the walking lines are |
| **Gyroscope** (turns) | Direction and every turn | Which sidewalk each stretch is on; where corners are; which moves were made (transitions) |
| **Gravity sensor** | The camera's tilt at every moment | Needed to measure distances on the ground from the video; later, the sidewalk's slope |
| **Video + SAM3 masks** | Curb, sidewalk, crosswalk, ramps, tactile paving, poles, trees, obstacles… | Polygon boundaries (curb, building side); width; ports (ramps, tactile paving); **features** placed in the right cell (a pole on this sidewalk, 40 m from the corner) |
| **Audio transcripts** | What the collector said ("ramp blocked", "no tactile paving here") | Notes attached to the cell, port or feature at that moment. For the dataset paper, they're released as annotated transcripts |
| **Aerial photo** (later) | The view from above, where trees don't hide it | Fixes the shift both walking lines share; a second source for polygon outlines |

**The merging rule.** Everything is merged through **time and the corrected track**:
1. Each frame, detection, step and spoken word has a timestamp.
2. The corrected track says where the walker was at that time, on which walking line, at which point along the street.
3. That places the observation in the right polygon, and at the right distance along its edge.

Each element of the graph keeps a list of **the observations that support or contradict it**. For example: "this ramp is supported by tactile paving seen in three frames and by the collector saying 'ramp' at 12:04".

**When the evidence disagrees,** for example when two crossings suggest different sidewalks, the graph keeps **both alternatives**, rather than guessing. Questions about routes are then answered for each alternative, or reported as "not enough evidence".

## 6. Where this leaves us

| Done | Next |
|---|---|
| Data checked, clocks lined up | **First (rough) graph on Morgan:** nodes, walking lines as edges, crossings |
| Reference for Morgan (needs a clean-up) | **Sidewalk polygons** from the curb and building-side edges, and edges as their centrelines |
| Walking lines on Morgan, four versions, scored; camera height measured | Lens calibration (checkerboard); the reference clean-up |
| Curb distance and road width from video | Corners and alternatives on the second street set (D2), then the one-time test on D3 |
| Map of all of it | Compare with Tile2Net and OpenStreetMap; write the paper |
