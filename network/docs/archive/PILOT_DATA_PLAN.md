# Pilot data: next steps toward a sidewalk passage graph

Prepared 14 October 2026. This is an analysis and implementation plan, not a claim that the pilot routes or graph have been validated. Tasks and checkpoints are in [PILOT_DATA_TODO.md](PILOT_DATA_TODO.md).

## What we have

Three MultiSensor capture folders under [`data/pilot/`](../../data/pilots/pilot1_2026-10-14/raw/) contain video, GPS, inertial, battery, Wi-Fi, cellular, and metadata exports. Together they hold about **37 minutes of video**, **3,869 GPS fixes**, and **5.4 GiB of raw data**. GPS fixes have a median interval near **0.55 s** in each session; the largest observed interval is **1.44 s**. The phone-reported median GPS accuracy is **3.2–4.1 m**, with isolated values as high as **39.3 m**. These are device estimates, not measured sidewalk-position errors. Summed raw GPS step lengths are about **3.2 km**, not unique sidewalk coverage.

The existing [GPS notebook](../../notebooks/pilot_gps_overview.ipynb) plots time-ordered tracks over a cached Cook County 2025 orthophoto without snapping or smoothing. The researcher confirmed its route assignment on 14 October 2026; **there is no field log**:

| Capture folder | Confirmed route |
|---|---|
| `2026-10-14-11-05-58-312` | R01 (red) |
| `2026-10-14-11-22-51-789` | G01 (green) |
| `2026-10-14-11-34-58-512` | P01 (pink) |

The [dashboard script](../../scripts/build_pilot_dashboard.py) exposes a sensor overview; it does not reconstruct pedestrian topology. The [route drawing](../img/pilot-routes-hand-drawn.png) defines intended capture, but actual coverage must be checked from recordings. The 2025 aerial image and October 2026 ground recordings can disagree because of change as well as positioning error.

## Research question for this pilot

Can these captures support a **traceable passage graph** in which the two physical sidewalk sides, legal crossings, observed mid-block park paths, and unknown connections are represented without inventing connectivity? This pilot should expose where GPS, inertial signals, video, and aerial imagery agree or disagree. It is too small to establish general performance across Chicago.

Keep the construction automatic. Reviewing video to audit a proposed result is allowed; using manually traced sidewalks or crossings as hidden construction inputs is not. A separately human-verified reference can be made for evaluation.

## Ordered work

### 1. Establish a session manifest and data contract

Carry the researcher's confirmed folder-to-route mapping into a manifest and mark its provenance as researcher recollection, since there is no field log. Recover actual start/end landmarks, direction, overlaps, and deviations from the recordings, leaving uncertain details unresolved. For each session record recording settings, device identity, available streams, timestamp conventions, coordinate reference, units, and file integrity. Measure video duration/frame rate and offsets against GPS and inertial time using a few visible turns/stops. Distinguish synchronized evidence from timestamps merely sharing a format. Keep original folders unchanged and derived outputs outside raw folders.

**Output:** a manifest plus a short quality table listing missing data, timing offsets/gaps, video usability, and uncertainty for each session. **Gate:** do not align frame detections or IMU events to a GPS position until the clocks have been checked.

### 2. Audit actual coverage against the drawn routes

Use the raw GPS overlay to find candidate transitions, then inspect the corresponding video to decide what was actually traversed. Record each intended sidewalk side, crossing, overlap, and drawn park path as `observed`, `partial`, `not observed`, `inaccessible`, or `uncertain`, with a session/time interval and reason. Distinguish travel to/from a route and repositioning from intended coverage. The pilot park paths are a separate passage class. Keep UIC campus and private paths out of the target inventory. Record actual O-PG and O-GR shared *physical* passages if present; geographical proximity alone does not prove an overlap.

**Output:** an observed-versus-planned map and issue register, including ambiguities between parallel sides and any missing crossing arm. **Gate:** the capture set is sufficient for a graph experiment only after its observed passages and gaps are explicit; planned arrows are not graph ground truth.

### 3. Freeze a minimal graph and evidence contract

Represent a node only at a junction/branch, crossing attachment, physical endpoint, or coverage boundary. Represent each sidewalk side, traversed crossing, and pilot park path as its own polyline passage edge; bends remain shape points. A capture's travel direction is an observation attribute; walking eligibility is a separate graph attribute. An edge must retain its source session/time intervals, modality-specific support, geometry estimate, quality/ambiguity state, and whether it is street-adjacent or a park exception. Preserve raw GPS separately. Do not connect lines merely because they cross in 2D or fall within one GPS accuracy radius. Allow unresolved endpoints and parallel hypotheses rather than forcing a connected graph.

**Output:** a one-page schema with two or three illustrated cases from this pilot: opposite sidewalk sides, a crossing, and a park or route-join case. **Gate:** agree on what counts as a traversable connection before building edges or route queries.

### 4. Build and compare bounded street-level baselines

First produce a GPS-only passage hypothesis from time-ordered trajectories, preserving gaps, turns, and raw/estimated geometry separately. Then test whether inertial turn/stop cues and synchronized video improve segmentation and crossing identification. Do not snap to road centerlines or silently force a track onto the route drawing. For each candidate edge or node, retain the actual observation interval and a reason for inclusion; leave side assignment unresolved when evidence cannot distinguish nearby paths.

**Output:** two inspectable graph variants—GPS-only and GPS plus synchronized street-level evidence—with an error log. **Gate:** compare their node/edge inventories and connectivity against the same observed-coverage audit before adding aerial information.

### 5. Add aerial evidence without hiding source disagreements

Document the orthophoto's acquisition year, resolution, retrieval, and coordinate reference. Derive or propose aerial passage hypotheses only where visible; absence under trees or shadows is not evidence of no sidewalk. Match aerial and street-level hypotheses explicitly, retain aerial-only and street-only elements, and mark unresolved matches or contradictory geometries. The union is a set of traceable hypotheses, not an averaged line or an automatically routable network.

**Output:** a provenance-colored comparison of the street-level graph, aerial hypotheses, and their union, with case notes for opposite sides, crossings, and mid-block paths. **Gate:** no candidate becomes routable solely because two lines meet in a map image.

### 6. Evaluate the pilot and decide the next collection

Create a small, separately verified reference for selected cases **after freezing the comparison criteria**, keeping it out of construction and tuning. Report missing and false connections, wrong-side assignments, crossing recognition, duplicate edges, uncertain elements, and provenance completeness separately. Test a few short route queries only on explicitly eligible edges. Measure actual coverage, usable-video rate, storage per recording hour, and the effort of review and processing. Because all three captures belong to one small pilot, report these as feasibility findings, not citywide accuracy estimates.

**Output:** a concise pilot findings report and a go/revise decision: which graph definitions worked, what failed, which methods merit a second pilot, and which passages need reacquisition. Any second collection should target a specific unresolved failure (for example two sidewalk sides too close for GPS, a crossing connection, or a path hidden in aerial imagery).

## Cross-cutting rules

- Keep raw video and sensor exports local. Treat Wi-Fi/cellular observations and incidental people in video as sensitive; publish only reviewed, minimal derived evidence.
- Keep route-plan information separate from reconstruction input unless a later experiment declares it as a prior. The same drawing cannot both supply the graph and independently verify it.
- Do not convert reported GPS accuracy into a universal lateral-error threshold. Inspect disagreements on this phone and these streets first.
- Record unknowns explicitly. A disconnected component or missing edge can be an honest coverage limit; forced connectivity would undermine routing reliability.

The broader design remains in [PLAN.md](PLAN.md); the [field protocol](PILOT_PROTOCOL.md) and [route plan](PILOT_NEAR_WEST_SIDE.md) explain the intended capture.
