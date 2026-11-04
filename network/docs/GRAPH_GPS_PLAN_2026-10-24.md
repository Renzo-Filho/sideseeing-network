# The walk measures the street: an initial plan for the passage graph, its cells and GPS correction

Draft, 24 October 2026. A proposal for discussion, built on [PLAN.md](PLAN.md), the [research critique](archive/RESEARCH_CRITIQUE_2026-10-23.md) and the [hypothesis experiments](archive/HYPOTHESIS_EXPERIMENTS_2026-10-23.md). It keeps their decisions: construction is automatic, voice is an evaluation reference only (decision 14), the three input regimes (street-only, street + aerial, map-assisted) stay separate, and **OSM is not used for map matching** (24 October). It makes one revision, agreed with Renzo on 24 October: the graph gets a second, linked view made of polygons (section 4). [PLAN.md](PLAN.md) decision 3 is revised to match. Numbers below are measurements from the West Loop notebooks or the sideseeing-tools viewer, cited where they first appear. Nothing here is a result of the proposed method.

## 1. The goal

Build, from vest-mounted phone recordings alone, a pedestrian **passage graph**: sidewalk sides as passages, crossings and corner turns as transitions between specific ports, each element linked to the observations that support or contradict it, with alternatives kept where the evidence cannot decide. Correct the GPS trajectory **as part of the same inference**, not as a separate map-matching step: deciding which sidewalk a stretch of walking belongs to *is* the GPS correction problem.

Give the graph **two linked views of the same space**. The **cells** are polygons that split the walkable space: one strip per sidewalk side per block, one cell per corner, one per crosswalk, with zones and features inside. The **graph** is the usual nodes and edges: each edge is the centreline of a strip or crosswalk cell and each node sits in a corner cell, so it compares directly with OpenStreetMap and Tile2Net. The aim is to keep everything the recordings can say about the street (where it goes, how wide and steep it is, its ramps and obstacles), at whatever level of detail the evidence supports (section 4).

The paper question stays the critique's: *when can sparse phone recordings establish which pedestrian passages connect, and does evidence-aware inference reduce false route claims compared with committing early to one map?* This plan adds a specific way to answer it without a map.

## 2. What we can build on

| | What exists (24 October) | Source |
|---|---|---|
| Recordings | 8 West Loop sessions, about 5 h. **D1** (19 Oct): Morgan, both sides. **D2** (20 Oct): half of Aberdeen, Madison's jog, Carpenter, both sides. **D3** (22 Oct): two neighbouring streets walked at the same time, so by two collectors, both sides each. GPS extents suggest SANGAMON_A and PEORIA_A (Van Buren to Wayman/Hubbard); **to confirm** which collector and phone walked which. | `west_loop.ipynb` §0; GPS files on desktop-01 |
| The GPS problem, measured | Reported accuracy about 3 m, yet the track sits 3.2–3.9 m from the walked sidewalk, towards the middle of the street. 25% of along-street fixes fall on the street's other half. 9 (D1) and 12 (D2) wrong-side stretches of 24–77 m, up to 25 m away, while reporting 3–6 m accuracy. | `west_loop.ipynb` findings 9 |
| Motion events, no model, no map | Stops, turns (gyroscope about gravity) and crossing candidates. On D1 S1 they reproduce the notebook exactly (24 stops, 83 turns) and the 50 motion-only crossing candidates are exactly the notebook's 50 OSM-matched *across* crossings. | sideseeing-tools `analysis.pauses`, `analysis.turns`; `workspace.motion()` |
| Repeated rungs | Each crosswalk over the walked street was crossed there and back in each session: exactly 4 times for 22 of Morgan's 25 crosswalks. Morgan's crosswalks are about 13 m long. | `west_loop.ipynb` findings 5, §7 |
| Video evidence | SAM3 masks for 35 prompts on every second of video, redacted frames. Tactile paving is detected in 49 of D1 S1's 50 crossings, 4.3× more often during crossings than elsewhere; crosswalk in all 50. | sideseeing-tools Questions panel; West Loop run |
| Narration | Whisper `turbo-silence`, chosen after Renzo's review (84% of its rated windows correct). Evaluation only. | `tasks/west-loop-run.md` |
| One time base | Every stream joins on `t`, seconds from the video start: `SideSeeingWorkspace.timeline / detections / transcript / gps / motion`. The viewer shows them together and can serve as the labelling tool. | sideseeing-tools `feature/visual-analytics` |

## 3. The idea

GPS cannot tell the two sidewalks of a street apart (section 2), but **the walk itself measures the street**:

- the gyroscope gives exact times and relative headings for every turn, so the walk splits into straight **runs** separated by **transitions**;
- a crossing of the walked street is a short run roughly perpendicular to the runs before and after it. Its duration and step count give the distance between the two sidewalks' walking lines, and its start and end are the two **curb ports**;
- under the protocol each crosswalk is crossed several times (above), so every crossing is a repeated, timed observation of the same **rung** between the same two ports;
- the video says which side the road is on (curb, car and crosswalk masks to the left or right of the frame) and confirms crossing ends (tactile paving, crosswalk);
- GPS supplies absolute position, but with a bias towards the street's middle that looks systematic (both sides measured 3.2–3.9 m inwards).

A two-sided street is then a **ladder**: two rails (the sidewalks' walking lines) joined by rungs (the crosswalks), whose number, order, timing and length come from motion, and whose absolute placement comes from GPS. Intersections are where ladders meet, with ports at each corner. Estimating the ladder and the trajectory together corrects the GPS (each run is placed on its rail) and produces the graph in one step, with no external map.

```
            rung (crosswalk)        rung
   west  ───●──────────────────────●───────────●───  rail = walking line, west sidewalk
            │  ↕ W (from crossing   │
            │    duration × speed)  │
   east  ───●──────────────────────●───────────●───  rail = walking line, east sidewalk
            port                    port
   runs:  ══ S1 northbound on east ══►       ◄══ S2 southbound on west ══
```

Where the constraints do not pin a choice down (a run that could be on either rail, a crossing that could attach to either corner of a jogged intersection), the method keeps **alternatives** instead of guessing, which is H2's subject.

**From walking lines to cells.** The rails are where the collector walked, not the graph's edges. In every frame, the sidewalk mask projected onto the ground gives the distance from the walking line to the sidewalk's two edges, the curb side and the building side, and the obstacle and vegetation masks give the lines between its zones. Placed along the rail, those distances become the strip's boundaries, and the strip's centreline becomes the edge. The crosswalk mask does the same across the road, and the spins at every intersection sweep the corner from several directions. The edges also help the GPS correction: the rung becomes a curb-to-curb measurement, and the distance between the two rails is the road width plus each walking line's offset from its curb.

```
 ┌─────────┬────────────────────────────────┬─────────┐  building line
 │         │ frontage zone                  │         │
 │    ●════╪═══════ edge = centreline ══════╪════●    │  ● node, in its corner cell
 │    ║    │ through zone   · · walking line│    ║    │
 │    ║    │ furniture zone   ▪ pole ▪ tree │    ║    │
 └──▒▒║▒▒──┴────────────────────────────────┴──▒▒║▒▒──┘  curb; ▒ ramp = passable part
    │ ║ │  crosswalk cells: edge = centreline  │ ║ │           of the shared boundary
```

## 4. The data structure

One partition of the walkable space into **cells**, and a **graph** linked to it element by element. The evidence and inference records are the critique's. All are plain tables (GeoParquet/GeoJSON plus JSON for the groups), keyed by IDs that never change when the graph is revised.

| | Record | Key fields | Built from |
|---|---|---|---|
| Evidence | **Observation** (immutable) | `obs_id`, session, modality (GPS fix, stop, turn, crossing candidate, detection interval, speech segment, aerial tile), `t0`, `t1`, values, quality, source version | Workspace tables; already on one time base |
| | **Run / transition** (the walk segmentation) | `run_id`, session, `t0`, `t1`, median heading, moving seconds; transitions typed turn, U-turn, spin, crossing, stop | Motion events (built) |
| Cells | **Cell** | `cell_id`, version, kind (sidewalk strip, corner, crosswalk; or a zone with its parent strip: frontage, through, furniture), polygon, an inner and an outer boundary for its uncertainty, censored sides (outside the frame, so the cell is *at least* this wide), level of detail | Projected masks along the walking lines |
| | **Boundary** | `boundary_id`, the cell on each side (or one cell and what lies beyond: building, road, unwalked), line, kind (cut between a strip and its corner, curb, building line, coverage boundary), state (passable, blocked, unknown), and its passable segments, the **ports**, each with a width; at a curb, the ramp, its tactile paving and whether it lines up with the crosswalk | Masks, crossing ends, coverage |
| | **Feature** | `feature_id`, cell and zone, kind (curb ramp, tactile paving, pole, tree, hydrant, bench, driveway, obstacle), point or polygon, position as distance along the centreline and offset from it | Detections, projected |
| | **Station** | cell, distance along the centreline, total width, clear width (the through zone minus obstacles), the width of each zone, running slope, cross slope, each with an uncertainty and the frames it comes from | Section 5 |
| Graph | **Node** | `node_id`, its corner cell (or, for a mid-block crossing or a coverage end, the boundary it sits on), position | Derived from the cells |
| | **Edge** (passage) | `edge_id`, version, its cell, two nodes, kind (sidewalk side, crossing, other), geometry (the cell's centreline), length, lateral uncertainty | Derived from the cells |
| | **Transition** (corner move) | `transition_id`, node, from port, to port (so from edge, to edge), observed direction(s), traversal state kept separate | Turns and crossing ends linked to ports |
| Inference | **Walking line** (rail) | `walk_id`, the cell it runs in, polyline, spread across passes, offset from the centreline | The inference (section 6) |
| | **Association** | `obs_id` or `run_id` → walking line, cell, boundary, feature or interval along an edge; supports or contradicts; method version; **dependency group** (one pass, one GPS drift) | The inference |
| | **Alternative group** | `group_id`, the mutually exclusive options (e.g. run 17 on the west *or* east walking line; crossing 9 to port NE *or* SE), scores | The inference |

**How the two views stay linked.**

- Every edge belongs to exactly one strip or crosswalk cell, and its geometry is that cell's centreline: the medial axis of the strip, extended through the cut to the node. It is computed from the cell, never edited on its own, so the two views cannot drift apart.
- Every node belongs to one corner cell and sits where the centrelines of its edges meet. A mid-block node sits on the boundary where a mid-block crossing joins or where coverage ends.
- **Connectivity lives on the boundaries.** Two cells that touch connect only through a port: a fence, a planter wall, a level change or a curb without a ramp can separate them. All of a corner's edges reach its node, but only transitions, each naming the two ports it uses, say which moves between them are possible.
- Alternatives apply to both views: if a run's walking line is uncertain, so are the cell it outlines and the edge that is its centreline.
- The walking line's offset from the centreline is kept: it says where people actually walk on the sidewalk.

**Levels of detail.** Each element records how far the evidence took it. A stretch seen only at dusk (D2 S2) or a sidewalk wider than the view stays at a lower level, visibly, instead of being filled in.

| Level | What exists | From |
|---|---|---|
| 0 | Nodes, edges, transitions, lengths; the edge is the walking line, flagged as such | GPS, accelerometer, gyroscope |
| 1 | Cell outlines and boundaries; the edge becomes the centreline | Projected sidewalk, crosswalk and curb masks; gravity for pitch and roll; the orthophoto in the street + aerial regime |
| 2 | Zones, features, measured ports, width and slope stations | Obstacle, vegetation and feature masks; gravity |

A **consistent graph** is one choice per alternative group that satisfies the constraints: consecutive runs joined only by a small turn stay on one walking line; crossing the walked street changes strip; a run's heading runs along its walking line; walking lines joined by a crossing are about W apart. A route query runs inside each consistent graph, never over their union, and reports its support across them, a conditional route naming the unresolved choice, or "insufficient evidence". Only the parts that are the same in every kept graph are exported: nodes and edges to OpenSidewalks and as OSM-style sidewalk and crossing ways, cells as `area:highway=footway` outlines next to their ways. Zones, stations and alternatives stay in our own tables.

The camera's position and a detected object's position stay separate: once the cells exist, a detection is associated with the cell and zone it is *in*, not the walking line the camera was on. This is also what the sidewalk assessment tab needs.

## 5. Width, length, slope and zones

| Quantity | How | What limits it |
|---|---|---|
| **Length** | Along each edge between its nodes, from the corrected trajectory and step counts (0.78 m per step on the West Loop days); the video marks where a segment starts and ends (curb, corner, driveway) and the length of features on the ground | Mostly solved by the graph itself |
| **Zones** | Across each strip, from the building line: the frontage zone up to the start of clear pavement; the furniture zone (or parkway) from the curb to the line of poles, trees, tree pits and grass; the through zone between them, following NACTO's sidewalk zones. The projected masks give the lines between zones, smoothed over a stretch | Where the furniture zone is bare concrete, only a line of poles with gaps marks it. The frontage zone is often empty (building flush with the sidewalk). If the masks cannot separate the zones, the strip stays at level 1 |
| **Width** | Total width spans all zones; clear width is the through zone minus the obstacles inside it (pole, planter, trash bin, scaffolding). Project the edges of the masks 2–5 m ahead onto the ground; a robust median over each stretch | Camera pitch: about 4–6% width error per degree at these distances, so pitch from the gravity sensor must be steady (average steady frames, or refine from the image). Sidewalks wider than the view are censored ("at least"). Mask edges at grass, driveway aprons and shadows |
| **Running slope** (limit about 5%, ramps 8.33%) | The camera and the gravity sensor are rigid together, so the mount drops out: slope is the angle between ground lines along the walk (curb, sidewalk edges) and the horizontal given by gravity, averaged over a stretch of the centreline | The gravity sensor while walking; a constant camera-to-sensor misalignment, calibrated once on level ground. The barometer drifts 1–1.5 m per session (notebook) and GPS altitude is too noisy, so neither measures slope here |
| **Cross slope** (limit 2%, about 1.1°) | The same with lines across the walk: the transverse joints of the concrete slabs | Needs about 0.5° overall. Exploratory |

**What the projection needs.**

- **The lens.** The recordings are 1920×1080 at 30 fps; the setting name `0_1_4000x2250@15` does not describe the stream. The camera's rotation during turns already gives a horizontal focal length of about 1460 px ([phase 0](GRAPH_PHASE0_RESULTS_2026-10-25.md)). A checkerboard video with the same phone in the same video mode would add the lens distortion and show whether stabilisation crops the image.
- **The camera height.** It sets the scale of every width and offset: a 5 cm error is about 4% of a width. Angles, slope and topology do not need it. It is inferred, not measured, in two independent ways:
  - The ground's apparent motion between frames gives speed ÷ height, and GPS over long straight runs gives the speed, so every run yields a height.
  - The tactile paving at curb ramps is a ruler on the ground at almost every crossing. By rule it extends at least 610 mm (2 ft) in the direction of travel; whether most panels are exactly that deep is to confirm on Morgan.

  The two estimates are each other's check, and a tape measurement of the vest, if taken, validates both.
- **Pitch and roll** per frame come from the gravity stream at 50 Hz (`west_loop.ipynb` §8).

**Reference.** At 20–30 marked spots on Morgan: total width, the width of each zone and clear width with a tape, running and cross slope with a digital inclinometer, a photo of each spot. For the geometry, the City of Chicago's curb lines, checked against the 2025 orthophoto, and the back of the sidewalk traced on it (section 8, phase 1).

**Prior work.** Width from single street-view images reaches about 0.25 m mean absolute error when scale is calibrated (UrbanVGGT, 2026); a monocular segmentation-and-depth pipeline matched its reference 64% of the time (TU Wien); HeiGIT estimates phone camera parameters for the same purpose. Slope has been measured with phone LiDAR, inclinometers on wheelchairs, and slope-meter apps; this search found no quantified slope from walking video plus gravity. What would be new here is continuous, uncertainty-tagged measurement along a walk, attached to the right cell and zone of the graph.

## 6. GPS correction without a map

**Formulation.** A robust least-squares problem (a factor graph) over the trajectory states at GPS times `x_t`, the walking lines `g_p`, a per-street separation `W_s` and a GPS bias, with discrete run-to-walking-line assignments `a_i`:

| Term | Ties | Evidence |
|---|---|---|
| GPS | `x_t` to the fix, with a robust loss and a lateral bias towards the street centre | GPS |
| Odometry | `x_t` to `x_{t+1}`: step count × step length, heading change | Accelerometer, gyroscope |
| On-line | the states of run `i` lie on walking line `g_{a_i}`, within the walking-line spread (F6) | Assignment |
| Rung | a crossing's ends lie on the two walking lines, perpendicular to them, `W_s` apart; repeats of one crosswalk share their ports | Crossing candidates |
| Side | the road is to the left or right of the camera, so `a_i` given the walking direction | SAM3 masks |
| Edges | the curb and building edges seen from a run lie at the measured offsets from its walking line; the two curbs of a street are the crosswalk's length apart | Projected sidewalk and crosswalk masks |
| Smoothness | walking lines are smooth polylines that bend only where a turn was observed | Turns |
| Aerial (street + aerial regime only) | cell boundaries near visible sidewalk edges | Orthophoto, later |

The cells follow from the solution: their boundaries are the walking lines plus the measured offsets, and the edges are their centrelines (section 4).

For a few alternatives (two walking lines, two attachments), enumerate the discrete choices, solve the continuous part for each, and keep the k best consistent ones. Robust-SLAM tools such as switchable constraints and max-mixtures handle the same discrete–continuous structure. They are tools here, not the contribution. `scipy.optimize.least_squares` is enough for one street; GTSAM if it grows.

**Baselines, all on the same sessions.** Raw GPS; the 5-fix median now used for display; a Kalman/RTS smoother of GPS + pedestrian dead reckoning; multi-trace clustering in the style of Kasemsuppakorn and Karimi (2013); and the notebook's OSM-assisted corrected track as a separate **map-assisted** reference, never as ground truth; and the **protocol rule**: under the West Loop protocol the walking direction alone gives the sidewalk side (northbound on the east side, southbound on the west), so the joint inference must beat it ([phase 0](GRAPH_PHASE0_RESULTS_2026-10-25.md), section 4). Ablations: without the video side term, without the rung term, without repeats (one crossing per crosswalk).

**What success looks like.** Side identity of runs, with abstention; the longest wrong-side stretch (now up to 77 m); where the walking lines and edges fall against the reference sidewalk (inside it, and their distance to its centreline), and boundary error of the cells; crossing attachment to the correct ports; port-to-port reachability, the critique's metric that a boundary-level score can miss.

## 7. What is established, and what would be new

| Established (cite, compare, do not claim) | What this plan would add (a hypothesis to test) |
|---|---|
| Pedestrian networks from multiple GPS traces (Kasemsuppakorn & Karimi 2013); pedestrian maps from crowd traces (Blanke et al. 2014) | Sidewalk-**side** identity and **port-specific** transitions from sparse traces, where GPS error exceeds the distance between the sides |
| Side-of-street positioning with a phone and a pedestrian map (Weng et al. 2025, PolyU sidewalk matching) | The same decision **without a map**, from the walk's own geometry |
| Sensor landmarks resetting dead reckoning (UnLoc 2012) and merging walking traces into pathway maps (Walkie-Markie 2013), both indoors; IMU-only road-crossing detection (2024) | Outdoors, with **crossings as timed, repeated, measurable rungs** that fix both the side and the street width |
| Probabilistic topological mapping (Ranganathan & Dellaert 2011); robust SLAM with discrete choices | Applying alternatives to **route claims**, with consistency enforced per hypothesis, evaluated by port-level reachability and risk–coverage (H2) |
| Aerial pedestrian graphs (Tile2Net, TraversRL); routability benchmarks (PathwayBench) | A ground-level benchmark with observation-linked passages, side identity and verified negative connections |
| Linked polygons and lines: OSM maps a footway's outline (`area:highway=footway`) beside its line; Tile2Net derives a centreline network from its aerial polygons; IndoorGML (OGC) pairs cells with a dual graph whose edges come from shared boundaries | Both views built **from walking recordings**, with ports as measured boundary segments (ramp width, tactile paving, alignment with the crosswalk) and uncertainty and alternatives carried on both views. Unlike IndoorGML, where every cell is a node, a strip is an edge, so routing tools and comparisons with OSM and Tile2Net work unchanged |
| Aerial sidewalk polygons (Tile2Net); width from street-view images (UrbanVGGT 2026, TU Wien, HeiGIT); slope from phone LiDAR or inclinometers | Cells with **zones, features, width and slope measured continuously from walking video**, registered without a map, linked to the graph, with censored and uncertain edges kept explicit; and street-level cells where aerial imagery is occluded |

This search was targeted, not systematic. Before any claim, trace the citations of Kasemsuppakorn & Karimi, the PolyU work and Walkie-Markie, and look for outdoor landmark-PDR sidewalk mapping specifically.

**Possible papers.** Since 25 October the goals, pipeline and phases of the two papers in progress (the dataset paper, and the graph paper, which is the first below) are in [PAPERS.md](PAPERS.md).
1. **First (recommended):** the map-free joint trajectory and ladder-graph inference, with alternatives where it cannot decide, plus the West Loop benchmark and port-level evaluation. This covers H1's side-identity question and a bounded part of H2. SIGSPATIAL fits, as the critique argues.
2. **Second:** H2 at full scale, retained alternatives against early commitment on route risk–coverage, once more intersections exist.
3. **Later:** H3 (revisits chosen by route impact) and the aerial union.

## 8. Work plan with gates

| Phase | Work | Gate before moving on |
|---|---|---|
| **0. Data contract** (about a week) | Run the motion step on all 8 sessions (desktop-01, CPU only); check clock alignment between video, IMU and GPS at a few visible events per session (and whether D3 includes the sync tap); confirm D3's streets, collectors and phones; test the video side cue on D1: do curb, car and crosswalk masks say which side the road is on? Check on a few Morgan blocks whether the masks separate the zones. Record the lens calibration video | Every stream used has a measured alignment bound; the side cue works on at least a stated share of D1 runs, or is dropped; zones are kept where the masks separate them, otherwise strips stop at level 1. **Done 25 October** ([results](GRAPH_PHASE0_RESULTS_2026-10-25.md)): clocks and side cue met, zones in part; the calibration video is still to record |
| **1. Reference for development sites** | On D1 (Morgan) and D2 (Aberdeen–Madison–Carpenter, including both jogged corners): the geometry reference is the City of Chicago's curb lines ([5gv8-ktcg](https://catalog.data.gov/dataset/boundaries-curb-lines), December 2010), checked block by block against the 2025 Cook County orthophoto and redrawn where they changed, plus the back of the sidewalk from Cook County's parcels (changed 26 October from tracing by hand, which does not scale; spot-checked on the orthophoto). Done on Morgan: [phase 2a notes](GRAPH_PHASE2A_NOTES_2026-10-25.md), section 4. The city's sidewalk polygons ([77cn-6x4c](https://catalog.data.gov/dataset/sidewalks-097b1), 2011) do not cover the sidewalk on the imagery and are not used. Tile2Net stays a competitor (phase 5), scored against the same reference. Then label each run's walking line and each crossing's ports from the video, in the viewer, blind to model output. Double-label the corners; `unknown` where the recordings cannot decide. Take the field measurements of section 5 at 20–30 spots on Morgan | Reference instructions frozen; disagreement and effort recorded |
| **2. Ladder on one street** | In progress: [phase 2a notes](GRAPH_PHASE2A_NOTES_2026-10-25.md). Morgan, both sessions: segmentation into runs and rungs, `W` from crossings, walking lines and assignments from the factor graph, against all baselines. Then the cells: boundaries, zones, centrelines as edges, width and running slope along both sides, against the field measurements and the reference sidewalk | **Geometry** (changed 25 October; under the protocol the walking direction alone gives the side, so side identity cannot fail here): the walking lines lie inside the reference sidewalk and nearer its centreline than the GPS + PDR smoother's track, and `W` agrees with the curb-to-curb width plus the two walking-line offsets; or the plan changes (section 10). Side identity is tested on the natural-walk block |
| **3. Corners and alternatives** | D2: Madison's jog, two streets meeting, corner cells and their ports, alternative groups where attachment is ambiguous; route queries per consistent graph | Alternatives appear where the reference says the decision is hard, not everywhere |
| **4. Held-out test** | Freeze every threshold; run once on D3 (new streets, a second collector). Report per site, with site-level intervals | Results reported whatever they are |
| **5. Aerial** | Add the orthophoto term as the street + aerial regime; compare with aerial-only (Tile2Net) on the same blocks: centrelines (lateral offset, topology) and polygons (overlap, boundary error), stratified by tree cover. Compare the edges with OSM's sidewalk and crossing ways, as a reference, not as truth | — |

The viewer supports each phase: the timeline already shows runs, turns, crossings and detections on one time base, so the reference labelling of phase 1 (plan step V3 in sideseeing-tools) and the graph view (V5) can be built there.

## 9. Decisions

**Settled (24 October).** Two linked views: cells and graph. The edge is its cell's centreline, for direct comparison with OSM and Tile2Net. Each corner is its own cell, linked to a node. Zones are included, to be rethought if the masks cannot separate them. Which width the cells mean is no longer a choice: total, clear and per-zone widths are all stored. PLAN.md decision 3 is revised to match.

**Settled (25 October).** After [phase 0](GRAPH_PHASE0_RESULTS_2026-10-25.md):

- The `road` prompt is approved, together with `grass`, `tree pit`, `building` and `fence` for the zones. They make a second SAM3 pass on D1 and D2, queued on desktop-01 after the West Loop run.
- Motion events are put on the video clock.
- Runs are split at straight crossings.
- The protocol rule joins the baselines.
- The camera height is inferred (section 5), not measured.

Later the same day:

- **Paper 1** is the map-free joint inference with alternatives.
- **D3 stays strictly held out.**
- **Phase 2's gate is geometry** (section 8).
- **The reference** is the city's curb lines, checked by Renzo against the 2025 orthophoto, with the back of the sidewalk traced by him, blind to model output.
- **At the next fieldwork** Renzo records the natural-walk block and a checkerboard calibration video for each phone.

**Open, for Renzo.**

1. **Second labeller:** whether someone else can double-label the corners and the video labels (phase 1).
2. **How far to take slope:** running slope only, or cross slope too as an exploratory result.
3. **Field reference:** who takes the tape and inclinometer measurements on Morgan, and when.
4. **Protocol dependence:** the method leans on the protocol (out and back, crossing every crosswalk, spins). Declare it as an *assisted survey* regime; the natural-walk block (agreed) measures how much it depends on the ritual.

## 10. Risks, and what would change the plan

- **The rung is not a clean measurement.** Walking speed changes during a crossing, and crossings include the curb approach. Seen 25 October ([phase 2a notes](GRAPH_PHASE2A_NOTES_2026-10-25.md)): crossed there and back, a crosswalk never joins the two walking lines within one session; the steps measure the near walking line to the far turnaround, and the far line comes from another session. If `W` from crossings varies more than the side separation it is meant to fix, keep the rung only as a topological tie (which walking line connects to which), not a distance.
- **The GPS bias is not systematic.** If the inward pull changes with buildings or side, the bias term cannot be shared and side identity will rest on video; then the result is about when video is needed.
- **The video side cue fails** with camera pitch changes (D2 was flatter by about 5°) and at dusk (D2 S2 fell below 35 lux). Then side identity comes only from rungs, and alternatives stay open longer: an honest result for H2.
- **Everything depends on the protocol.** If the natural-walk sample loses most of the benefit, the contribution is an assisted surveying method, which is still publishable but narrower.
- **Cells are only as good as the projection.** Pitch errors scale the width, wide sidewalks leave the frame, and mask edges blur at grass, driveways and shadows. If width errors exceed about 0.3 m against the tape, keep the cells as outlines with wide uncertainty bands rather than measurements; the edges then lean on the walking lines.
- **The zones do not separate.** Where the furniture zone is bare concrete with sparse poles, its line is a guess. Then report total and clear width only, keep the strips at level 1, and rethink zones (agreed 24 October).
- **Corner cells have no clean centreline.** A corner is not a strip, so the node is placed where its edges' centrelines meet, a convention to state, and corners are compared as polygons, not lines.
- **Cross slope is below what the phone can resolve.** Then report running slope only, and say so.
- **A tuned GPS + PDR smoother already resolves the sides.** Then the joint graph inference is not needed for geometry, and the paper should centre on transitions, alternatives and route decisions instead.

## Sources consulted for this plan

- West Loop notebooks: [`west_loop.ipynb`](../notebooks/west_loop.ipynb), [`west_loop_sam3_whisper.ipynb`](../notebooks/west_loop_sam3_whisper.ipynb); sideseeing-tools `tasks/visual-analytics-plan.md` and `tasks/west-loop-run.md`.
- Kasemsuppakorn & Karimi, [A pedestrian network construction algorithm based on multiple GPS traces](https://mail.iaorifors.com/paper/79378), Transportation Research Part C, 2013.
- [Sidewalk matching: a smartphone-based GNSS positioning technique for pedestrians](https://research.polyu.edu.hk/en/publications/sidewalk-matching-a-smartphone-based-gnss-positioning-technique-f/) (PolyU; uses a pedestrian map; probably the critique's Weng et al. 2025, to confirm).
- [UnLoc](https://synapsesocial.com/papers/W2054602086) (MobiSys 2012) and [Walkie-Markie](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/shen) (NSDI 2013): landmark-anchored indoor dead reckoning and pathway mapping.
- [Reliable heading tracking for pedestrian road crossing prediction](https://arxiv.org/html/2410.06400v1) (2024): IMU-only crossing detection.
- [Shoe-sensor curb and ramp transitions](https://www3.cs.stonybrook.edu/~jain/papers/shubham_hotPlanet14.pdf) (HotPlanet 2014).
- Width and slope: [UrbanVGGT](https://papers.cool/arxiv/2603.22531) (2026); [TU Wien thesis](https://repositum.tuwien.at/handle/20.500.12708/229239); [HeiGIT](https://heigit.org/measuring-what-you-never-notice-a-computer-vision-approach-to-accessible-paths/); [phone LiDAR for ADA compliance](https://rosap.ntl.bts.gov/view/dot/87091) (2024); [smartphone sensors on a wheelchair](https://udspace.udel.edu/items/89d8c375-4c08-4256-a35f-150d1237aa6f) (Delaware); [smartphone slope meter](https://resna.org/sites/default/files/legacy/conference/proceedings/2012/ComputersandCommunication/ASSESSINGDISABILITYCOMPLIANCEUSINGSMARTPHONE.html) (RESNA 2012).
- Linked polygons and lines: Hosseini et al., [Mapping the walk](https://www.evl.uic.edu/pubs/2703) (Tile2Net), Computers, Environment and Urban Systems 101, 2023, and its [README](https://github.com/VIDA-NYU/tile2net/blob/main/README.md) (polygons, then a centreline network); [IndoorGML](https://docs.ogc.org/is/22-045r5/22-045r5.pdf) (OGC; cells, cell boundaries and the dual graph); OSM [`area:highway=footway`](https://wiki.openstreetmap.org/wiki/Tag:area:highway%3Dfootway) (de facto, not formally approved); NACTO [sidewalk zones](https://nacto.org/publication/urban-street-design-guide/street-design-elements/sidewalks/sidewalk-zones/).
- The critique's sources: OpenSidewalks, Tile2Net, PathwayBench, TraversRL, Ranganathan & Dellaert 2011, Blanke et al. 2014, Weng et al. 2025.
