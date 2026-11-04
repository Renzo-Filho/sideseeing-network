# The graph paper with Tile2Net as the baseline: plan, contribution and paper

Draft, 3 November 2026, for discussion with Renzo and the advisors. It follows the advisors' direction: **Tile2Net is the baseline**, so the first result is a network of the same kind, nodes and edges, at least as accurate as Tile2Net's; the enriched graph (detections, measurements from the video) comes second. It keeps the cells (polygons) of the [October plan](GRAPH_GPS_PLAN_2026-10-24.md), because they are what joins the two steps. The October plan stays the method reference for the walk-only inference (its sections 3 to 6). Its framing, phases and paper sections (1, 7 to 9) are replaced by this page once it is agreed.

**How the graph is produced** (inputs, data management, aggregation, transformations, outputs) is in [GRAPH_PIPELINE_2026-11-03.md](GRAPH_PIPELINE_2026-11-03.md). Collection continues until early or mid December: until then the work runs on the data that exist and grows with them (section 9).

Numbers about this project come from the phase notes, cited. Numbers about other work are not quoted: only their methods are described.

## 1. What changes

| | October plan (24 Oct) | This plan |
|---|---|---|
| The question | Can phone walks build the passage graph without a map, keeping alternatives where they cannot decide? | **What does the pedestrian's own walk add to an aerial pedestrian network?** First to the network, then to what the network knows |
| The baseline | One of many (phase 5, at the end) | **Tile2Net, from the start.** Every output is scored next to it, with the same reference and the same code |
| First success | The walking lines inside the sidewalk (geometry gate) | **A network (nodes and edges) at least as accurate as Tile2Net's, and better at corners and crossings** |
| Aerial imagery | A later regime | **Part of the main method**: Tile2Net supplies the absolute position the walk cannot (the shared GPS shift, [phase 2b notes](GRAPH_PHASE2B_NOTES_2026-10-27.md) §7) |
| Alternatives and route risk | The centre of paper 1 | Kept inside the graph as `unknown` and `conflicting` states. Selective routing becomes future work (section 11) |
| Cells, width, slope, features | Levels 1 and 2 of the graph | Unchanged in substance. They are now the bridge to Tile2Net (it is polygons first, too) and the second result |

Nothing done so far is lost. The ladder (phase 2a) and the video measurements (phase 2b) are the walk-only method, and they register the walk to the aerial network in the fused method.

## 2. What Tile2Net does, and where the walk can do better

Tile2Net ([Hosseini et al. 2023](https://www.evl.uic.edu/pubs/2703), [code](https://github.com/VIDA-NYU/tile2net)), read from the paper on 3 November:
1. **Segmentation** of orthorectified aerial tiles into sidewalk (with footpaths), crosswalk, road and background.
2. **Polygons** from connected pixels, georeferenced.
3. **Centrelines** from each polygon: simplified outline, dense Voronoi skeleton, short branches trimmed. A crosswalk's centreline joins the middles of its rectangle's short sides and is then **connected to the nearest sidewalk line**.
4. **Topology clean-up:** false nodes and isolated lines removed, small gaps closed by extending both ends to meet.
5. **Output:** polygon and network layers, GeoParquet by default, WGS 84.

**How it was evaluated.** Polygons: the share of official polygons that overlap a detected one, and the overlapping area. Network: the share of official segments with a detected segment **within 4 m of the official segment's centroid**. This measures coverage only. It does not penalise extra segments, wrong connections or a line on the wrong side of a curb within 4 m. [PathwayBench](https://arxiv.org/html/2407.16875v1) later scored Tile2Net on routability between the edges of polygons around each intersection. It reports good edge retrieval but poor routability, with more connected components than the reference. Those figures are theirs and are not verified here.

**Where Tile2Net says it falls short, and what the walk sees there:**

| Tile2Net's own limitation (paper §5) | What the walk records |
|---|---|
| Centrelines are fitted to each polygon on its own, so they break between polygons | The walker passed through: a continuous run is evidence the passage is continuous |
| Many segments meet near a corner, giving redundant nodes | The turns and crossing ends at that corner: where the walker turned, which ramp they used, which crossing they took |
| A crosswalk is joined to the **nearest** sidewalk line | The crossing's two ends are measured (phase 2a: the rung), so the crossing is attached to the walking line and port it actually reached |
| Crosswalk paint fades or is missing | A crossing that was walked exists and is passable, painted or not. SAM3 sees the paint up close |
| Trees and shadows hide footpaths and sidewalks | The camera is under the canopy |
| The official data used to check it are years older than the imagery | The recording is dated to the day |
| (Not discussed) Which moves a corner allows | The protocol crosses every legal crosswalk and logs the ones that are closed or missing as *not crossable* ([RIVER_NORTH_COLLECTION.md](RIVER_NORTH_COLLECTION.md), field rules). That is a verified **negative** connection, which no image gives |

And beyond the network, aerial imagery cannot see clear width, slope, ramps, tactile paving, signals, obstacles, surface condition, or how long a crossing and its wait take. The walk records all of these (section 7).

The other side, said plainly: **the walk alone cannot fix its absolute position.** Phase 2b ends with the walking lines off by a shift that both sides of the street share (median 0.94 m, p90 3.12 m), which crossings, steps and the video cannot see. The orthophoto can, and Tile2Net is built on it. **The two are complementary:** aerial for absolute position and coverage, the walk for connectivity, passages the aerial view cannot see, and attributes.

## 3. One representation, three levels

Every method writes the same layers, so **one scorer scores them all**, Tile2Net included.

| Level | What it holds | Tile2Net has it? | Scored in |
|---|---|---|---|
| **0. Network** | Nodes and edges, typed sidewalk or crossing; the same layers, fields and CRS as Tile2Net's network output | Yes | Gate 1 |
| **1. Cells** | Sidewalk, corner and crosswalk polygons (the same layers as Tile2Net's polygons). Each edge is its cell's centreline, which is Tile2Net's own rule. **Ports** (passable openings on a cell's boundary, such as ramps) and **transitions** (the moves a corner allows) | Polygons yes; ports and transitions no | Gate 1 (polygons, ports) |
| **2. Enrichment** | Stations along each edge (total, clear and zone widths, running slope), features placed in their cell and zone, port attributes (ramp, tactile paving, alignment with the crosswalk), crossing attributes (marking, signal, duration, wait), optional visual embeddings | No | Gate 2 |
| **3. Condition and experience** (candidate, added 3 November) | Condition tags on detected elements (Project Sidewalk models, section 7); comfort proxies with a measurement behind them: shade and canopy, noise level from the audio (levels only, computed locally), pedestrian density, the buffer from traffic, lighting. How pedestrians *feel* needs a rating study (section 9) | No | Not in Gate 2 unless agreed |

**Evidence and provenance on every element, at every level:**
- **Source:** aerial only, street only, both, or conflicting (PLAN decision 6: keep the union, mark the source).
- **State:** confirmed, unknown, or contradicted.
- **The observations** that support or contradict it.

The record types are the October plan's (its section 4). The export to Tile2Net's format carries level 0 and the polygons; everything else stays in our own tables.

**Why the cells conciliate the two goals.** Tile2Net builds the network as polygons → centrelines. We do the same, with polygons that come from the walk (curb and paved edge projected from the video along the walking line), or from Tile2Net's polygons corrected by the walk. So the network result and the enrichment are one structure. The polygon that defines an edge's geometry is also the place where widths, slopes and features are stored.

## 4. Methods compared

```
            aerial tiles ──► Tile2Net ──► polygons ──► network ─────────────────────┐  A. aerial only (baseline)
                                │                                                   │
 walk: GPS, IMU, video ──► ladder + video edges ──► cells ──► network ──────────────┤  B. walk only (first, on its own)
                                │                                                   │
                                └──► register walk to Tile2Net ──► edit with street ─┤  C. walk + Tile2Net (second step)
                                     (removes shared shift)       evidence          │
                                                                                     ▼
                                                     same layers ──► one scorer, one reference
```

**Order (decided 3 November).** The walk's network is not a replacement for Tile2Net, and it first stands on its own: **B is built and scored against A before C exists.** C comes second.

**What fusion means, and what it does not.** C does not put our method inside Tile2Net, and it does not change Tile2Net. C *reads Tile2Net's output files* (its polygons and network) as one more input, the way it reads the orthophoto. Tile2Net's code stays as released, and our pipeline stays a separate tool that can run with or without that input. Contributing anything back to the Tile2Net project would be a separate, later choice.

**A. Tile2Net (aerial only):** run **as released** (decided 3 November) on the Cook County 2025 orthophoto over the whole collection area. Chicago is not a pre-configured region, so tiles are prepared as the repository's data guide asks. A Chicago fine-tune is recorded for later (section 13).

**B. Walk only, the first result:** the existing ladder (phase 2a), with the video's curb distance and road width (phase 2b), turned into cells and their centrelines, with corners from turns and crossing ends. No aerial input, no map.

**C. Walk + Tile2Net (the second step).**
1. **Register.** Add the aerial term the October plan reserved (its section 6): the video gives each walking line's distance to its curb, and Tile2Net gives where that curb is (the road-side edge of its sidewalk polygon). Fitting both removes the shared shift. The walk is not snapped to any map. It is placed by its own measured distance to an aerially seen edge.
2. **Match.** Which run covers which Tile2Net sidewalk segment, and which walked crossing covers which crosswalk polygon.
3. **Edit, keeping provenance:**

| Case | Walk | Tile2Net | Result |
|---|---|---|---|
| Sidewalk seen from above and walked | Run on a walking line; sidewalk in the video | Polygon | **Confirmed**; geometry from both |
| Under trees or shadow | Walked; sidewalk in the video | Gap or broken polygon | **Added**, street only |
| Corner | Turns, crossing ends, ramp detections | Several nodes; crosswalk joined to the nearest line | **Rebuilt:** one corner cell and node, ports at the ramps, transitions from the moves observed |
| Crossing walked, no paint visible from above | Rung | No crosswalk polygon | **Crossing added**, marking `none` or `faded` |
| Painted crosswalk logged *not crossable* | Not crossed; log or video shows why | Crosswalk polygon | Edge kept; its transitions **blocked** |
| Tile2Net sidewalk where the walk shows none (plaza, parking, driveway apron) | Passed by; video shows no sidewalk | Polygon | **Contradicted**; kept and flagged |
| Not walked | None | Polygon | **Aerial only**, unchanged |

4. **Geometry.** Each cell boundary combines the aerial edge and the edge measured from the street, weighted by visibility: where canopy covers the sidewalk, the street wins; in the open, the aerial edge does. The centreline follows from the fused cell.

So C always covers at least what Tile2Net covers, and improves it where walked.

**Other comparisons** (reported, not the focus):
- Raw GPS and a GPS + steps smoother turned into lines (the phase 2a baselines).
- A multi-trace aggregation baseline (Kasemsuppakorn and Karimi 2013).
- OpenStreetMap's sidewalk and crossing ways, as another map, not as truth.

## 5. The reference

The reference must be independent of all three methods and fixed before any of them is scored on it.

**Area and splits** (revised 3 November):
- **Development:** the protocol walks, street by street in straight lines, north–south and east–west: D1 (Morgan), D2 (Aberdeen, Madison's jog, Carpenter) and the later protocol days.
- **Test, proposed by Renzo:** routes walked **not in straight lines**, chosen "at random": a walker going somewhere, turning where they please, crossing where they need to.
- **Test, recommended in addition:** D3 (Sangamon and Peoria), already held out since 25 October: new streets, walked with the protocol.

Why both. The free routes test the **walking style** (does the method still work without the out-and-back ritual?). D3 tests **new streets** (does it work where nothing was tuned?). With free routes alone, a bad result could not be traced to either cause. Two conditions make the free routes a fair test:
- They are **drawn before the walk.** For example, random origin–destination pairs on the route plan, with each route sketched beforehand and kept unchanged, so nobody picks easy streets on the spot.
- Some **cross development streets and some do not.** This separates the walking style from the street novelty.

The free routes also are the natural-walk block the October plan asked for. They cover each sidewalk once, one side at a time, so their network is sparser per street; Gate 1 compares methods on the same walked blocks only.

**Layers:**

| Layer | Source | Check |
|---|---|---|
| Sidewalk polygons | Curb: **the City's lines, kept for now** (3 November), checked on the 2025 orthophoto. Back: parcels or the building line | **To review with the advisors:** the half-metre problems on Morgan ([phase 2b](GRAPH_PHASE2B_NOTES_2026-10-27.md) §5) |
| Sidewalk centrelines | Derived from the reference polygons with **one centreline rule, used for every method's polygons too** | So that a convention difference is not scored as error |
| Crosswalk polygons and centrelines | Drawn on the orthophoto; faded or unpainted ones confirmed in the video | Source recorded per element |
| Corner nodes | One per corner cell | — |
| Ports | Curb ramps and their width, from the video and the orthophoto | Double-labelled on the corners |
| Transitions | For each corner, which moves are possible: crosswalk present, ramp at both ends, no barrier. Labelled from the video and the orthophoto, blind to model output; `unknown` allowed | Reviewers double-label a sample (decided 3 November); the agreement rate is reported |

**A bias to avoid.** A reference drawn on the orthophoto favours the aerial method under trees. Each reference element therefore records its source and whether it is visible on the orthophoto, and canopy stretches are checked in the video. Results are reported separately for visible and covered stretches.

## 6. Gate 1: the network

**Metrics, on the walked blocks, against the reference:**

| Family | Metric | Why |
|---|---|---|
| Tile2Net's own | Share of reference segments with a predicted segment within 4 m of the reference segment's centroid, and the reverse (predicted segments with a reference within 4 m) | Compares on Tile2Net's own terms, the reading the advisors know |
| Coverage and correctness | Length-based completeness, correctness and F1 within 1, 2 and 4 m | Here sidewalks are 2–3 m wide (Morgan reference medians 2.0 and 2.9 m, [phase 2a](GRAPH_PHASE2A_NOTES_2026-10-25.md) §4), so 4 m cannot tell a sidewalk from the curb lane |
| Position | Lateral offset from the reference centreline (median, p90); share inside the reference polygon | The measure used since phase 2a |
| Topology | Nodes per real corner (redundant nodes); connected components; **crossing attachment** (each crossing joined to the right corner and side); **port-pair reachability** ([critique](RESEARCH_CRITIQUE_2026-10-23.md)); PathwayBench's traversability similarity, for comparability; APLS (path-length similarity) over the walked blocks | Where aerial networks are known to fail, and what routing needs |
| Polygons | IoU with the reference sidewalk and crosswalk polygons; curb and back boundary error; width error | Both methods make polygons. This is Tile2Net's polygon evaluation, made stricter |

**Strata:** canopy over the sidewalk (visible or covered on the orthophoto); corner type (plain, jogged, with alley or driveway); crossing (painted, faded, unpainted, logged not crossable).

**Two gates, in order, each run once on the test blocks with every setting frozen:**

**Gate 1a: the walk's network on its own (B against A).** This is the first success criterion: a network, nodes and edges, similar to or better than Tile2Net's.
- **Not worse than Tile2Net on finding the network:** Tile2Net's own 4 m metric and length F1, within a margin.
- **Better on topology:** crossing attachment and port-pair reachability, with intervals from a bootstrap over corners, paired by corner.
- **Position is reported whatever it shows.** B is expected to be worse in absolute position, because of the shared GPS shift that only the aerial view removes ([phase 2b](GRAPH_PHASE2B_NOTES_2026-10-27.md) §7). That gap is what C is for.

**Gate 1b: the fusion (C against A).**
- Not worse than Tile2Net on geometry (F1 and lateral offset), within a margin.
- Better on topology.

**The margins are not set yet** (3 November). They should come from established practice rather than be invented here, and be fixed before any test result is seen. Candidates to review with the advisors:
- the ASPRS and NSSDA way of reporting horizontal accuracy (RMSE and a 95% figure);
- buffer-based completeness and correctness, as in road-network extraction;
- Tile2Net's own 4 m tolerance;
- an equivalence test (two one-sided tests) for "not worse by more than the margin".

If neither B nor C is better on topology, the walk's network contribution is not shown, and the paper leans on Gate 2 and the routing result (section 8). That is still publishable, but narrower.

## 7. Gate 2: the enriched graph

| Attribute | From the walk | Reference | Aerial can see it? |
|---|---|---|---|
| Total width | Projected sidewalk mask, curb to paved edge (phase 2b) | Tape at 20–30 spots on Morgan; orthophoto where clear | In the open |
| Clear width | Through zone minus obstacles inside it | Tape | No |
| Zone widths (frontage, through, furniture) | Masks for sidewalk, tree pit, grass, poles | Tape, photos | Partly |
| Running slope | Gravity plus ground lines along the walk | Inclinometer; **Cook County 2022 LiDAR terrain**, already used in the analysis track, as an independent baseline | From LiDAR only |
| Cross slope | Slab joints across the walk | Inclinometer | No; exploratory |
| Curb ramp at a port, and its alignment with the crosswalk | SAM3 ramp prompts at crossing ends | Video labels; a City ramp inventory, if one exists (to check) | Weakly |
| Tactile paving | SAM3 | Video labels; spoken code words | No |
| Pedestrian signal | SAM3; the stop before the crossing | Video labels | No |
| Crossing duration, wait at the curb, walking speed | Steps, stops and turns on the video clock | Behaviour itself, measured | No |
| Obstacles and furniture, placed in cell and zone | SAM3 (poles, hydrants, bins, benches, bollards, trees, planters, meters, racks, bus stops) | Video labels; spoken code words | Trees, partly |
| Temporary obstructions | SAM3 (scaffolding, construction barriers, cones) | Video labels | No, and imagery is out of date |
| Surface condition | SAM3 (cracks, potholes, puddles, manholes) | Video labels | No |
| Visual embedding per edge (optional) | An image encoder over the edge's frames | Retrieval against the labels above | No |

All the SAM3 prompts named above were already run on the West Loop sessions (the prompt groups in the West Loop workspace).

**A second detector, not only SAM3** (added 3 November). Project Sidewalk's open models are trained on sidewalk accessibility labels, not on general prompts:
- a label validator for curb ramps, missing curb ramps, obstacles and surface problems ([sidewalk-cv-2021](https://github.com/ProjectSidewalk/sidewalk-cv-2021));
- a condition tagger with 33 tags on image crops ([Liu et al., ASSETS 2024](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf));
- RampNet, curb ramps in Street View panoramas ([arXiv 2508.09415](https://arxiv.org/abs/2508.09415)).

All three were trained on Street View, seen from a car's roof; our frames are from a vest, pitched down, on the sidewalk. Use:
1. Check which checkpoints are public.
2. Score them on a labelled sample of our frames before using any output.
3. If they hold up, use SAM3 for *where* (boxes) and Project Sidewalk's tagger for *what condition*, on the same crops.

The Brás audit's frame classifier is a third model to register (PAPERS.md).

**The gate:**
- Width within about 0.3 m of the tape, kept from the October plan; otherwise cells stay outlines.
- Running slope within a tolerance agreed beforehand, against the inclinometer and LiDAR.
- Detection precision and recall reported per attribute.
- Each attribute's coverage: the share of edges or ports that have it at a stated confidence.

## 8. What it changes: routes

One result to show why the second step matters. Choose origin–destination pairs on the test blocks **before** looking at any output. For each pair:
- the route on Tile2Net's network;
- the route on C's network;
- the route under a wheelchair profile on the enriched graph: a ramp at both ends of every crossing, clear width and running slope within the US accessibility guidelines (thresholds taken from PROWAG and confirmed before use).

**Report:**
- How often a route Tile2Net calls valid uses a move the reference says is impossible (no crosswalk, blocked, no ramp).
- How often it fails the wheelchair profile.
- How often the enriched graph finds the valid alternative.

These are the critique's false route claims, made concrete with attributes aerial imagery cannot see.

## 9. Work plan

| Phase | Work | Gate, or output | Status |
|---|---|---|---|
| **Pre-step. Data review** (Renzo) | Review the voice transcripts and the video frames, and process them into the inputs the pipeline reads ([pipeline](GRAPH_PIPELINE_2026-11-03.md), step S0) | Reviewed inputs, with what was changed recorded | Planned |
| **P0. Data contract** | Clocks, side cue, zones | — | Done ([results](GRAPH_PHASE0_RESULTS_2026-10-25.md)) |
| **P1. Tile2Net on West Loop** | Tiles from the Cook County 2025 orthophoto at Tile2Net's expected resolution; run **as released** on desktop-01's GPU over the whole collection area; first look at its corners and crossings on Morgan | Baseline layers on disk | **New; first** |
| **P2. Reference v2** | One consistent pass for Morgan's curbs and back; extend to D2 and the test blocks; crosswalks, corners, ports and transitions labelled in the viewer, blind; inventory the later days and freeze the splits | Instructions frozen; disagreement recorded | Morgan curbs and back done, needs the pass |
| **P3. One scorer** | Extend `graph/evaluate.py` to read Tile2Net-format layers and compute section 6's metrics; score Tile2Net first | Baseline table on development blocks | New |
| **P4. Walk only (B)** | From the phase 2b walking lines: cells (curb and paved edge), centrelines, corner cells from turns and crossing ends, ports, transitions; written in Tile2Net's format. Morgan, then D2's corners and jogs. **B stands on its own first** | Development scores next to Tile2Net (Gate 1a's measures) | Walking lines done (2a, 2b) |
| **P5. Walk + Tile2Net (C)** | After P4. Registration term; matching; the edits of section 4; provenance | Development scores; settings frozen | New |
| **P6. Gates 1a and 1b** | Run A, B, C once on the test blocks | Section 6's tables, whatever they show | — |
| **P7. Enrichment** | Stations, features in cells and zones, port and crossing attributes, behaviour; tape, inclinometer and LiDAR references; checkerboard calibration | Section 7's table | Width and camera height started (2b) |
| **P8. Routes** | Section 8 on the test blocks | Route validity table | — |
| **P9. Paper** | Section 10 | Draft | — |

P1 and P2 come first and can run at the same time. P1 can tell us early whether Tile2Net has a problem on Chicago imagery.

### While collection continues (until early or mid December)

- **Splits now, before more data arrive.** Assign every module of the route plan to development or test in `splits.csv` (pipeline, section 3). A new day's passes inherit their module's split. Test passes get only the automatic checks until the frozen run.
- **Development runs** grow as days arrive: P3–P5 on D1, D2 and later development modules.
- **Gate 1 (P6) runs once, after the last collection day,** on all test modules.

**Workstreams added 3 November** (from Renzo's ideas; each idea and its assessment is in section 14):

| Workstream | What | Size | Gate |
|---|---|---|---|
| **Calibration in the field** | A short routine on every collection day, and a calibration day on Morgan with modules that can be repeated on other blocks. Plan: [CALIBRATION_DAY_PLAN_2026-11-03.md](../CALIBRATION_DAY_PLAN_2026-11-03.md) | Routine 10 min a day; calibration day about 3 h | Per collector and phone: height, step length, lens; error models for width, curb distance, slope; their day-to-day spread |
| **Source ablations** | The pipeline's section 7 matrix: each quantity from GPS alone, + motion, + crossings, + video, + Wi-Fi, + aerial, against the same reference | Runs as P3–P5 progress | Part of Gate 1 and Gate 2 tables |
| **Exploratory sensors** | Wi-Fi as a side cue and for matching passes across days (a first signal exists, pipeline section 8); barometer on a known level change; magnetometer under the elevated train | Two weeks, then stop or adopt | Wi-Fi side cue beats shuffled labels on a second day and adds to the video side cue on the natural-walk block |
| **Second detector** | Project Sidewalk's models (section 7) | One week | Precision and recall on a labelled sample of our frames |
| **Level 3, condition and experience** | Measured proxies (section 3). Collectors already talk about what they experience while they walk (Renzo and the volunteers); that talk is kept as an exploratory measurement, after the data review, **not as the core** (3 November) | Proxies after P7 | Exploratory; a perception study is a separate paper (section 13) |

The next fieldwork still has the open items: the checkerboard video, the free-route walks (section 5), and the tape and inclinometer spots. The calibration day covers the first and the last.

## 10. The contribution and the paper

**What is established, cited and not claimed:**
- Aerial pedestrian networks: Tile2Net; TraversRL (graphs grown from aerial images, 2026).
- Routability benchmarks: PathwayBench.
- Sidewalks from aerial plus car-level street-view images (Ning et al.).
- Phone-based multimodal sidewalk mapping: iOSPointMapper.
- Curb ramps from street-level images: RampNet; Project Sidewalk.
- Pedestrian networks from GPS traces (Kasemsuppakorn and Karimi 2013).
- Linked polygons and lines: Tile2Net itself, IndoorGML, OSM `area:highway=footway`.

**What would be new** (each a hypothesis that Gates 1 and 2 test):
1. **The walk as evidence of connectivity.** A crossing walked is a passage that exists and connects specific ports; a crossing logged as not crossable is a verified absence. Car-level street view cannot give this, and neither can aerial images.
2. **A network from phone walks without a map, in Tile2Net's format.** Crossings are measured rungs that fix which side each stretch is on. Cells come from video masks projected with the phone's gravity sensor.
3. **A fusion that lets each source do what it is good at.** Aerial supplies absolute position and coverage. The walk supplies corner topology, crossing attachment, and passages hidden or unpainted from above. Every element keeps its provenance, and contradictions are kept rather than resolved silently.
4. **A pedestrian-level enrichment with measured error.** Width, clear width, slope, ramps, tactile paving, signals, obstacles, crossing and waiting times, each attached through time to the right cell, zone or port.
5. **An evaluation that shows the difference:** a West Loop reference down to ports and transitions; Tile2Net's own metric beside stricter ones; how often an aerial-only route is invalid or inaccessible.

**Working titles** (to choose with the advisors):
- *Walk2Net: what the pedestrian's walk adds to aerial sidewalk networks.* The name pairs with Tile2Net on purpose; check that the advisors are comfortable with it.
- *From tiles to steps: correcting and enriching aerial pedestrian networks with phone walking recordings.*

**Shape of the paper:**
1. Introduction: aerial networks scale, but miss corners, crossings and everything a pedestrian experiences.
2. Related work.
3. Data: the West Loop collection, its protocol and the reference.
4. Method: walk only; walk + Tile2Net; enrichment.
5. Results: Gate 1, Gate 2, routes.
6. Discussion: the cost of walking (hours per kilometre against aerial), when walking is worth it, and the limits.

**Key figures:**
- One corner as Tile2Net draws it, against C, with ports and transitions.
- The metric table split by canopy.
- An attribute map.
- A route Tile2Net calls valid that is not.

**Venues:**
- **CEUS** (Tile2Net's journal; a natural follow-up for its authors).
- **ACM SIGSPATIAL** (the critique's choice; spatial graphs and multimodal acquisition).
- **ASSETS** or **CHI**, if the accessibility routing result leads.
- A computer-vision venue only if the vision part becomes the main contribution.

Decide with the advisors, together with authorship.

**Relation to the dataset paper** ([PAPERS.md](PAPERS.md)):
- The reference and the West Loop labels are made once and serve both papers.
- D3 is the test split for both.
- The enrichment's labels are the dataset's West Loop labels.
- Section 4 of PAPERS.md is to be rewritten from this page once it is agreed.

## 11. Risks, and what would change the plan

- **Tile2Net is weak on Chicago imagery** (it was not trained on Chicago). The comparison would then flatter us. It runs as released for this paper and is reported as such; a Chicago fine-tune is recorded in section 13.
- **West Loop is an open grid.** Tile2Net may already do well on its plain corners. Stratify by corner type and canopy, and put the claim where the difference is: jogs, alleys, driveways, faded and unpainted crossings, ramps.
- **The reference favours the aerial view.** Mitigation in section 5; report by stratum.
- **Coverage is unequal.** We cover only walked streets. Score on walked blocks only, and report coverage and field effort openly. The framing is "aerial for coverage, the walk for correctness and attributes", not "the walk replaces aerial".
- **Port- and transition-level reference is costly.** Limit it to the corners of the test blocks, with a second labeller on a sample.
- **Few test corners give wide intervals.** Count the corners before freezing the splits. Add a later day to the test set if needed.
- **The method leans on the protocol** (out and back, every crosswalk, spins). Declare it an assisted survey; the free-route test walks (section 5) measure how much it depends on that.
- **Alternatives and selective routing** (H2 of the critique) are no longer the centre. Ambiguous elements stay `unknown` or `conflicting`. The parked ideas are listed in section 13 for review.

## 12. Decisions

**Decided on 3 November:**

| # | Decision |
|---|---|
| 1 | Not a replacement. **The walk's network (B) stands on its own first**; the fusion (C) comes second and reads Tile2Net's output files without changing Tile2Net (section 4) |
| 2 | **Tile2Net runs as released.** A Chicago fine-tune is recorded for later (section 13) |
| 4 | Venue and title: later |
| 5 | **Test:** routes walked not in straight lines, drawn at random before the walk (Renzo's proposal), with D3's held-out streets recommended in addition (section 5). To confirm the D3 part |
| 6 | **The City's curb lines are kept** for the reference for now; to review with the advisors |
| 7 | **Reviewers** double-label a sample of the reference |
| 8 | **Embeddings:** future work (section 13) |
| 9 | **A data-review pre-step** (Renzo): the voice transcripts and the video frames are reviewed and processed before they feed the pipeline ([pipeline](GRAPH_PIPELINE_2026-11-03.md), step S0) |
| 10 | **Collectors' talk** is recorded as they walk and kept as an exploratory measurement, not as the core idea |

**To review:**
- **3. The margins** for Gates 1a and 1b: from an established standard (section 6), with the advisors, before any test result.
- **6. The curb source:** with the advisors.
- **9. Inputs and the reference must stay apart.** A source that feeds the pipeline cannot also be the reference for the same thing. If reviewed voice feeds Level 3 (comfort), it can still score ramps and crossings; if it also feeds ramps, those need another reference. The data review may fix and exclude (wrong clock, unusable frames, redaction misses). Human labels of content (a ramp here) belong to the reference, not to the input, or construction is no longer automatic (PLAN decision 2). To agree before S0 is built.
- **5. The sampling of the free routes:** how many, how drawn.

## 13. Parked for later review

Ideas from the October plan and the critique that are not in this paper. Review them when the paper's first draft exists, or earlier if a result calls for one.

| Idea | What it would add | Why parked | Revisit when | Needs |
|---|---|---|---|---|
| **Alternative groups** | Keep competing versions of an uncertain element (pass on the east *or* west walking line; crossing to port NE *or* SE) instead of one answer | Gate 1 needs one network to compare with Tile2Net; `unknown` and `conflicting` states keep the honesty for now | Phase P4 shows many corners where the walk cannot decide | The October plan's alternative groups, section 4 |
| **Route queries per consistent graph** | Answer a route in each consistent version of the graph, never over their union | Depends on alternative groups | With alternative groups | Enumeration of consistent graphs |
| **Risk–coverage routing** (critique H2) | Fewer false route claims at the same share of answered queries, against committing early to one map | A full study of its own; needs many ambiguous intersections | After the full West Loop collection | Preregistered origin–destination queries, a decision loss |
| **Revisits chosen by route impact** (critique H3) | Which block to walk again to resolve the most route uncertainty | Needs H2 first | After H2 | Replay of later captures |
| **Aerial union at full scale** | Our graph over the whole area, beyond walked blocks, with each source's elements kept | This paper scores walked blocks only | After Gate 1 | Matching rules at scale |
| **Brás as a second test city** | The method in another city and protocol | The Brás protocol crosses once, without the ladder's repeats | After P6 (decided in PAPERS.md) | Tile2Net on São Paulo imagery; Brás corrected GPS |
| **Change over time** (critique) | Tell real change in the street from alignment error; update the graph | Needs repeated visits months apart | A second collection season | Repeat walks |
| **Perception study** | How pedestrians feel on each sidewalk, from many raters | Subjective data need many raters and their own design | After Level 3 proxies exist | Rating protocol, ethics approval, raters |
| **Cross slope** | Slope across the sidewalk (accessibility) | Probably below what the phone resolves | After running slope works | Inclinometer spots |
| **Visual embeddings per edge** | Search and compare sidewalks by appearance | A good idea; other work comes first (3 November) | After Gate 2 | An encoder, a retrieval test |
| **Tile2Net fine-tuned on Chicago** | A fairer aerial baseline: tiles from the Cook County orthophoto labelled from City data, used to fine-tune Tile2Net's released model | Tile2Net runs as released for this paper (3 November) | If Tile2Net as released clearly fails on Chicago imagery, or a reviewer asks | Labelled Chicago tiles, GPU time, the co-authors' advice |

## 14. Renzo's ideas (3 November), with an assessment

Each idea is recorded as Renzo put it, followed by Claude's assessment, checked against the data where possible.

### Idea 1. Calibration pilots, and comparing sources

> Plan 3 to 5 pilots to calibrate measurements, and use them to improve and generalise the inference from the videos (measuring sidewalks, measuring steps, etc.). Use these rules to improve the estimates from GPS, the sensors and especially the images: distances of things in the images build or add information to the graph and the polygons. Then combine different sources while comparing them: for example, the distance estimate alone, against sensors + GPS, against other sources.

**Assessment: the goal fits; the form should change.**
- **What needs calibrating is per collector and per phone,** and can drift from day to day: the camera's height, the step length, the lens, the mount's angle.
  - The camera's height alone was 12% off until it was measured (1.30 m against 1.43–1.49 m from ground motion; [phase 2b](GRAPH_PHASE2B_NOTES_2026-10-27.md) §7).
  - A short routine on every collection day catches this. A one-off pilot does not.
- **3 to 5 separate pilots cost field days** that the collection needs before December.
- **Rules tuned on a few pilot blocks can fit those blocks.** Whether they generalise has to be checked on development streets anyway.
- **So:** a daily routine, and one calibration day built from modules. A module can be repeated on other kinds of block (narrow, wide, with trees, on a slope). That is what more pilots would really add, and it can be done if the first day shows the need. Plan: [CALIBRATION_DAY_PLAN_2026-11-03.md](../CALIBRATION_DAY_PLAN_2026-11-03.md).
- **Comparing sources fits fully.** It is now the ablation matrix ([pipeline](GRAPH_PIPELINE_2026-11-03.md), section 7), and part of it exists: phase 2a and 2b compared raw GPS, the smoother, the ladder and the ladder with video. One correction: the comparison is made quantity by quantity, because not every source measures everything (GPS gives no width).

### Idea 2. Unconventional data: Wi-Fi, light, pressure

> Set aside time for exploratory analysis of unconventional data, such as the Wi-Fi signal and other sensors (light, pressure). It may lead to a new finding or idea for the project.

**Assessment: it fits, if it is time-boxed and tests named questions.** Open-ended searching across five sensors is how weeks disappear. Checked on D2 on 3 November ([pipeline](GRAPH_PIPELINE_2026-11-03.md), section 8):
- **Wi-Fi is the promising one.**
  - A real scan every 7.5 s, about one per 10 m of walking.
  - At the same 25 m stretch of a street, an access point's signal differs between the east and west sidewalks by a median 4.0 dB, against 3.1 dB with the side labels shuffled. None of 200 shuffles exceeded 3.8 dB.
  - A real but modest signal, on one day only, with sides from the protocol rule (`network/scripts/wifi_side_check.py`).
  - Why it matters: a side cue that needs neither the out-and-back walk nor daylight would address the method's dependence on the protocol.
- **The barometer is finer than expected:** about 7 cm of noise from second to second. It could see stairs, ramps and bridge approaches. West Loop is flat, so it is unlikely to beat LiDAR for slope.
- **The light sensor** is on the screen side, and the camera looks out of the phone's back, so it probably faces the collector's chest. The video's exposure says the same thing. Low value.
- **The magnetometer** may mark stretches under the elevated train. Untested.

Plan: two weeks, Wi-Fi first, then stop or adopt.

### Idea 3. Project Sidewalk's models

> In the data processing and AI part, run and test Jon Froehlich's models (Project Sidewalk), so that SAM3 is not the only model used. A minor part, but to be registered.

**Assessment: it fits, and it matters more than "minor".** These are the only models we have that rate an element's *condition*, not just its presence: a label validator (curb ramps, missing ramps, obstacles, surface problems), a 33-tag condition tagger (ASSETS 2024), and RampNet (curb ramps). Caveats and use:
- They were trained on Street View, from a car's roof. Our frames are from a vest at 1.30 m, tilted about 21° down. Expect a drop in accuracy, and measure it on a labelled sample of our frames before using any output.
- The pairing to test: SAM3 says *where* an element is, and the tagger says *what condition* it is in, on the same crops.
- Ask Jon Froehlich which checkpoint suits forward-facing walking video.

Registered in section 7.

### Idea 4. Qualitative features: conditions and how pedestrians feel

> Explore qualitative features to add to the graph, perhaps as a Level 3: infer sidewalk conditions and pedestrians' "feelings" about them.

**Assessment: conditions fit now; feelings do not, as stated.**
- **Conditions and comfort proxies fit**, as Level 3 (section 3): condition tags (idea 3), shade, noise level from the audio, pedestrian density, the buffer from traffic, lighting. Each has a measurement behind it.
- **Feelings do not fit this paper:**
  - One or two collectors' videos cannot measure how pedestrians feel.
  - Perception studies need many raters and their own design.
  - Image-based "feeling" scores from vision–language models are not calibrated ([critique](RESEARCH_CRITIQUE_2026-10-23.md), its sources).
- **The collectors' talk** is kept as an exploratory measurement (decision 10). The perception study is parked as its own paper (section 13).
