# Research plan: the sidewalk network

Merged on 4 November 2026 from the plans of 12 October to 3 November: [PLAN](archive/PLAN.md), the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md), [PAPERS](archive/PAPERS.md) and the [graph paper plan](archive/GRAPH_PAPER_PLAN_2026-11-03.md). It holds the goals of both papers, the design of the graph paper, the work plan and every decision taken so far. The graph paper's design (section 2) is a **draft for the advisors**, as of 3 November.

| For | See |
|---|---|
| How the graph is computed: inputs, steps, data, outputs | [METHOD.md](METHOD.md) |
| How a field day is done | [FIELD_PROTOCOL.md](FIELD_PROTOCOL.md) |
| What has been measured so far | [RESULTS.md](RESULTS.md) |
| Where things stand, dated | [STATUS.md](STATUS.md) |

Numbers about this project come from [RESULTS.md](RESULTS.md), cited. Numbers about other work are not quoted: only their methods are described.

## 1. Two papers

- **Dataset paper:** West Loop (Chicago) and Brás (São Paulo) as one labelled dataset (section 3).
- **Graph paper:** what the pedestrian's own walk adds to an aerial pedestrian network. First to the network (nodes and edges), then to what the network knows (widths, slopes, ramps, obstacles) (section 2).

**What the two papers share:**
- **One West Loop reference, made once.** Curbs, the back of the sidewalk and the video labels are the graph paper's evaluation and the dataset's verified West Loop labels. They are made blind to model output, under written instructions.
- **One test split.** D3 (Sangamon and Peoria) is held out for both.
- **One pipeline.** sideseeing-tools does the processing, and its viewer is the labelling tool.
- **Both papers proceed at the same time** (decision 21). Shared steps are done once.

## 2. The graph paper

### 2.1 The question

**What does the pedestrian's own walk add to an aerial pedestrian network?** Tile2Net is the baseline from the start (decision 24). The first result is a network of the same kind, at least as accurate as Tile2Net's and better at corners and crossings. The enriched graph comes second.

What changed on 3 November, against the October plan:

| | October plan | Now |
|---|---|---|
| The baseline | One of many, at the end | **Tile2Net, from the start.** Every output is scored next to it, with the same reference and the same code |
| First success | The walking lines inside the sidewalk | **A network at least as accurate as Tile2Net's, and better at corners and crossings** |
| Aerial imagery | A later regime | **Part of the main method:** it supplies the absolute position the walk cannot (the shared GPS shift, [RESULTS](RESULTS.md#phase-2b-notes-the-curb-from-the-video-on-morgan) 2b §7) |
| Alternatives and route risk | The centre of the paper | Kept inside the graph as `unknown` and `conflicting` states; selective routing is parked (section 8) |
| Cells, width, slope, features | Levels 1 and 2 | Unchanged in substance; now the bridge to Tile2Net and the second result |

Nothing done so far is lost. The ladder (phase 2a) and the video measurements (phase 2b) are the walk-only method, and they register the walk to the aerial network in the fused method.

### 2.2 What Tile2Net does, and where the walk can do better

Tile2Net ([Hosseini et al. 2023](https://www.evl.uic.edu/pubs/2703), [code](https://github.com/VIDA-NYU/tile2net)), read from the paper on 3 November:
1. **Segmentation** of orthorectified aerial tiles into sidewalk, crosswalk, road and background.
2. **Polygons** from connected pixels, georeferenced.
3. **Centrelines** from each polygon (a trimmed Voronoi skeleton). A crosswalk's centreline is **connected to the nearest sidewalk line**.
4. **Topology clean-up:** false nodes and isolated lines removed, small gaps closed.
5. **Output:** polygon and network layers, GeoParquet, WGS 84.

**How it was evaluated:** the share of official segments with a detected segment within 4 m of the official segment's centroid. This measures coverage only: it does not penalise extra segments, wrong connections, or a line on the wrong side of a curb within 4 m. [PathwayBench](https://arxiv.org/html/2407.16875v1) later scored it on routability; its figures are theirs and not verified here.

| Tile2Net's own limitation (its paper, §5) | What the walk records |
|---|---|
| Centrelines are fitted per polygon, so they break between polygons | The walker passed through: a continuous run is evidence the passage is continuous |
| Many segments meet near a corner, giving redundant nodes | The turns and crossing ends at that corner: which ramp, which crossing |
| A crosswalk is joined to the **nearest** sidewalk line | The crossing's two ends are measured, so it is attached to the walking line it actually reached |
| Crosswalk paint fades or is missing | A walked crossing exists, painted or not |
| Trees and shadows hide sidewalks | The camera is under the canopy |
| The official data used to check it are older than the imagery | The recording is dated to the day |
| (Not discussed) which moves a corner allows | A crosswalk the collector could not cross is a verified **negative** connection, which no image gives |

Beyond the network, aerial imagery cannot see clear width, slope, ramps, tactile paving, signals, obstacles, surface condition, or how long a crossing and its wait take.

**The other side, said plainly:** the walk alone cannot fix its absolute position. Phase 2b ends with a shift that both sides of the street share (median 0.94 m, p90 3.12 m, [RESULTS](RESULTS.md#phase-2b-notes-the-curb-from-the-video-on-morgan) 2b §7). The orthophoto can fix it. **The two are complementary:** aerial for absolute position and coverage, the walk for connectivity, hidden passages and attributes.

### 2.3 One representation, three levels

Every method writes the same layers, so **one scorer scores them all**, Tile2Net included. The tables are in [METHOD §8](METHOD.md#8-data-structure-and-outputs).

| Level | What it holds | Tile2Net has it? | Scored in |
|---|---|---|---|
| **0. Network** | Nodes and edges, typed sidewalk or crossing, in Tile2Net's layers, fields and CRS | Yes | Gate 1 |
| **1. Cells** | Sidewalk, corner and crosswalk polygons; each edge is its cell's centreline. **Ports** (passable openings on a cell's boundary, such as ramps) and **transitions** (the moves a corner allows) | Polygons yes; ports and transitions no | Gate 1 |
| **2. Enrichment** | Stations along each edge (total, clear and zone widths, running slope), features in their cell and zone, port and crossing attributes | No | Gate 2 |
| **3. Condition and experience** (candidate) | Condition tags; comfort proxies with a measurement behind them (shade, noise level, density, buffer from traffic, lighting). How pedestrians *feel* needs a rating study | No | Not in Gate 2 unless agreed |

**Every element carries:**
- its **source**: aerial only, street only, both, or conflicting (decision 6: keep the union, mark the source);
- its **state**: confirmed, unknown or contradicted;
- **the observations** that support or contradict it.

**Node rules** (decisions 4, 5 and 9; the full case table is in [PLAN](archive/PLAN.md), "Node and edge definitions"):
- A node marks a change in connectivity: a junction, a crossing attachment, a physical end, or the end of coverage. A coverage end is never a dead end.
- A bend, a GPS sample, a frame or an object does not need a node; it is a position along an edge.
- Lines that cross do not connect unless there is evidence of a connection (levels, fences, walls).
- Not visible from above does not mean not there.

**Why cells.** Tile2Net builds polygons, then centrelines. We do the same, with polygons from the walk (curb and paved edge projected from the video), or Tile2Net's polygons corrected by the walk. The polygon that defines an edge's geometry is also where its widths, slopes and features are stored, so the network result and the enrichment are one structure.

### 2.4 Methods compared

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

**B is built and scored against A before C exists** (decision 24). C reads Tile2Net's output files as one more input; it does not change Tile2Net, and our pipeline runs with or without that input.

- **A. Tile2Net:** run **as released** (decision 25) on the Cook County 2025 orthophoto over the whole collection area, with tiles prepared as its data guide asks.
- **B. Walk only:** the ladder (phase 2a) with the video's curb distance and road width (phase 2b), turned into cells and centrelines, with corners from turns and crossing ends. No aerial input, no map.
- **C. Walk + Tile2Net:**
  1. **Register:** the video gives each walking line's distance to its curb; Tile2Net gives where that curb is. Fitting both removes the shared shift. The walk is not snapped to a map: it is placed by its own measured distance to an aerially seen edge.
  2. **Match** runs to Tile2Net sidewalk segments and walked crossings to crosswalk polygons.
  3. **Edit, keeping provenance:**

| Case | Walk | Tile2Net | Result |
|---|---|---|---|
| Seen from above and walked | Run on a walking line | Polygon | **Confirmed**; geometry from both |
| Under trees or shadow | Walked | Gap or broken polygon | **Added**, street only |
| Corner | Turns, crossing ends, ramps | Several nodes; crosswalk joined to the nearest line | **Rebuilt:** one corner cell and node, ports at the ramps, transitions from the moves observed |
| Crossing walked, no paint from above | Rung | No crosswalk polygon | **Crossing added**, marking `none` or `faded` |
| Painted crosswalk logged not crossable | Not crossed | Crosswalk polygon | Edge kept, transitions **blocked** |
| Tile2Net sidewalk where the walk shows none | Passed by | Polygon | **Contradicted**; kept and flagged |
| Not walked | None | Polygon | **Aerial only**, unchanged |

  4. **Geometry:** each cell boundary combines the aerial edge and the street edge, weighted by visibility. Under canopy the street wins; in the open, the aerial edge does.

So C covers at least what Tile2Net covers and improves it where walked.

**Other comparisons** (reported, not the focus): raw GPS and a GPS + steps smoother turned into lines; multi-trace aggregation (Kasemsuppakorn and Karimi 2013); OpenStreetMap's sidewalk and crossing ways, as another map, not as truth.

### 2.5 The reference and the splits

The reference is independent of all three methods and fixed before any of them is scored on it.

**Splits:**
- **Development:** the protocol walks, street by street (D1 Morgan, D2 Aberdeen, Madison's jog and Carpenter, and the later protocol days).
- **Test:** routes walked **not in straight lines**, drawn at random **before** the walk and kept unchanged (decision 26). Some cross development streets and some do not, which separates the walking style from street novelty.
- **Test, recommended in addition:** D3 (Sangamon and Peoria), held out since 25 October (decision 18): new streets, walked with the protocol.

Why both: the free routes test the **walking style**; D3 tests **new streets**. With free routes alone, a bad result could not be traced to either cause.

| Layer | Source | Check |
|---|---|---|
| Sidewalk polygons | Curb: **the City's lines** (decision 20), checked on the 2025 orthophoto. Back: parcels or the building line | The half-metre problems on Morgan ([RESULTS](RESULTS.md#phase-2b-notes-the-curb-from-the-video-on-morgan) 2b §5); to review with the advisors |
| Sidewalk centrelines | Derived from the reference polygons with **one centreline rule, used for every method too** | A convention difference is not scored as error |
| Crosswalk polygons and centrelines | Drawn on the orthophoto; faded ones confirmed in the video | Source recorded per element |
| Corner nodes | One per corner cell | — |
| Ports | Curb ramps and their width, from the video and the orthophoto | Double-labelled on the corners |
| Transitions | Per corner, which moves are possible; labelled blind to model output; `unknown` allowed | A sample double-labelled (decision 27); agreement reported |

**A bias to avoid:** a reference drawn on the orthophoto favours the aerial method under trees. Each element records its source and whether it is visible on the orthophoto, and results are reported separately for visible and covered stretches.

### 2.6 Gate 1: the network

| Family | Metric | Why |
|---|---|---|
| Tile2Net's own | Share of reference segments with a predicted segment within 4 m of their centroid, and the reverse | Tile2Net's own terms, the reading the advisors know |
| Coverage and correctness | Length-based completeness, correctness and F1 within 1, 2 and 4 m | Morgan's sidewalks are 2–3 m wide ([RESULTS](RESULTS.md#phase-2a-notes-the-ladder-on-morgan) 2a §4), so 4 m cannot tell a sidewalk from the curb lane |
| Position | Lateral offset from the reference centreline (median, p90); share inside the reference polygon | The measure used since phase 2a |
| Topology | Redundant nodes per corner; connected components; **crossing attachment**; **port-pair reachability**; PathwayBench's traversability similarity; APLS over the walked blocks | Where aerial networks fail, and what routing needs |
| Polygons | IoU with the reference polygons; curb and back boundary error; width error | Tile2Net's polygon evaluation, made stricter |

**Strata:** canopy (visible or covered); corner type (plain, jogged, with alley or driveway); crossing (painted, faded, unpainted, not crossable).

**Two gates, in order, each run once on the test blocks with every setting frozen:**
- **Gate 1a, B against A** (the first success criterion): not worse than Tile2Net on finding the network (its 4 m metric and length F1, within a margin); better on topology (crossing attachment and port-pair reachability, with bootstrap intervals paired by corner). Position is reported whatever it shows: B is expected to be worse there, which is what C is for.
- **Gate 1b, C against A:** not worse on geometry (F1, lateral offset) within a margin; better on topology.

**The margins are not set yet** (open question 1). They should come from established practice and be fixed before any test result: the ASPRS and NSSDA horizontal accuracy reporting, buffer-based completeness and correctness, Tile2Net's 4 m tolerance, and an equivalence test for "not worse by more than the margin".

If neither B nor C is better on topology, the walk's network contribution is not shown, and the paper leans on Gate 2 and routes. That is still publishable, but narrower.

### 2.7 Gate 2: the enriched graph

| Attribute | From the walk | Reference | Aerial sees it? |
|---|---|---|---|
| Total width | Projected sidewalk mask, curb to paved edge (phase 2b) | Tape at 20–30 spots on Morgan; orthophoto where clear | In the open |
| Clear width | Through zone minus obstacles | Tape | No |
| Zone widths | Masks for sidewalk, tree pit, grass, poles | Tape, photos | Partly |
| Running slope | Gravity plus ground lines along the walk | Inclinometer; Cook County 2022 LiDAR terrain | LiDAR only |
| Cross slope | Slab joints across the walk | Inclinometer | No; exploratory |
| Curb ramp at a port, and its alignment | SAM3 ramp prompts at crossing ends | Video labels; a City ramp inventory, if one exists | Weakly |
| Tactile paving, pedestrian signal | SAM3; the stop before the crossing | Video labels; spoken words | No |
| Crossing duration, wait, walking speed | Steps, stops and turns on the video clock | Measured behaviour | No |
| Obstacles and furniture, in cell and zone | SAM3 (poles, hydrants, bins, benches, bollards, trees, planters, meters, racks, bus stops) | Video labels; spoken words | Trees, partly |
| Temporary obstructions, surface condition | SAM3 (scaffolding, barriers, cones; cracks, potholes, puddles, manholes) | Video labels | No |
| Visual embedding per edge | Future work (decision 28) | — | — |

**A second detector:** Project Sidewalk's open models (a label validator, [sidewalk-cv-2021](https://github.com/ProjectSidewalk/sidewalk-cv-2021); a 33-tag condition tagger, [Liu et al., ASSETS 2024](https://makeabilitylab.cs.washington.edu/media/publications/Liu_TowardsFineGrainedSidewalkAccessibilityAssessmentWithDeepLearningInitialBenchmarksAndAnOpenDataset_ASSETS2024.pdf); [RampNet](https://arxiv.org/abs/2508.09415)). They were trained on Street View from a car's roof; our frames are from a vest, pitched down. Check which checkpoints are public, score them on a labelled sample of our frames, then use SAM3 for *where* and the tagger for *what condition*. The Brás audit's frame classifier is a third model to register.

**The gate:** width within about 0.3 m of the tape (otherwise cells stay outlines); running slope within a tolerance agreed beforehand; detection precision and recall per attribute; each attribute's coverage at a stated confidence.

### 2.8 What it changes: routes

Choose origin–destination pairs on the test blocks **before** looking at any output. For each, route on Tile2Net's network, on C's network, and under a wheelchair profile on the enriched graph (ramps at both ends of every crossing, clear width and running slope within the US guidelines, thresholds from PROWAG confirmed before use). Report how often a route Tile2Net calls valid uses a move the reference says is impossible, how often it fails the wheelchair profile, and how often the enriched graph finds the valid alternative.

### 2.9 The contribution and the paper

**Established, cited and not claimed:** Tile2Net and TraversRL (aerial networks); PathwayBench (routability); Ning et al. (aerial plus car-level street view); iOSPointMapper (phone-based mapping); RampNet and Project Sidewalk (ramps from street-level images); Kasemsuppakorn and Karimi 2013 (networks from GPS traces); Tile2Net, IndoorGML and OSM `area:highway=footway` (linked polygons and lines). The October literature search, with side-of-street positioning and indoor landmark mapping, is in the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md) §7.

**What would be new** (each a hypothesis that Gates 1 and 2 test):
1. **The walk as evidence of connectivity:** a walked crossing connects specific ports; a crossing logged not crossable is a verified absence.
2. **A network from phone walks without a map, in Tile2Net's format.**
3. **A fusion that lets each source do what it is good at,** keeping provenance and contradictions.
4. **A pedestrian-level enrichment with measured error,** attached through time to the right cell, zone or port.
5. **An evaluation that shows the difference:** a reference down to ports and transitions, and how often an aerial-only route is invalid or inaccessible.

**Working titles** (to choose with the advisors): *Walk2Net: what the pedestrian's walk adds to aerial sidewalk networks*; *From tiles to steps: correcting and enriching aerial pedestrian networks with phone walking recordings.*

**Shape:** introduction; related work; data (the collection, its protocol, the reference); method (walk only, walk + Tile2Net, enrichment); results (Gate 1, Gate 2, routes); discussion (the cost of walking against aerial, when it is worth it, limits). **Key figures:** one corner as Tile2Net draws it against C; the metric table split by canopy; an attribute map; a route Tile2Net calls valid that is not.

**Venues:** CEUS (Tile2Net's journal), ACM SIGSPATIAL, ASSETS or CHI if the accessibility result leads. Decide with the advisors, with authorship (decision 31).

## 3. The dataset paper

**Goal:** West Loop and Brás as one dataset: whole walks recorded with a phone on a vest, every stream on one clock, processed by the same pipeline, labelled with one schema, with fixed splits, benchmark tasks and baselines.

**What would make it worth a paper** (to check against related datasets before writing):
- **Areas, not routes:** both areas walked street by street, on both sides, with their crossings. The earlier SideSeeing dataset ([Damaceno et al. 2024](https://arxiv.org/abs/2407.06464)) followed routes to hospitals.
- **Two cities, two protocols:** Chicago's grid against Brás's busy commercial streets.
- **Labels at two scales:** the audit's (surface per lot, each crossing's ramp, paint and adequacy, in Brás) and the network's (where each sidewalk is, which side each stretch is on, where crossings end, in West Loop).
- **Whole synchronised walks**, not cropped keyframes.

| | West Loop, Chicago | Brás, São Paulo |
|---|---|---|
| Recordings | From 19 October 2026, still being collected (STATUS) | 216 captures in 16 route groups, 9–16 November 2025 |
| Streams | Video 1920×1080 at 30 fps, GPS, motion sensors, audio with narration (released only as annotated transcripts) | The same app (MultiSensor) |
| Human labels that exist | Spoken words for sidewalk elements, an evaluation reference only (decision 14) | The audit's GeoPackage: corrected GPS for 64,645 frames matched to 5,035 lots; surface problems on 1,138 lots; 578 crossings rated adequate, partial or inadequate |
| Human labels to make | The reference geometry; in the viewer, walking lines, crossing ports and features; tape and inclinometer spots | A sample relabelled blind, to measure agreement with the audit |
| Machine output (released, marked as such) | SAM3 masks, Whisper transcripts, motion events | The audit's frame classifier; the same SAM3 and motion outputs once run |

**Benchmark tasks (proposed):**
1. **Crossing elements:** crosswalk, curb ramp and tactile paving at each crossing (Brás audit, West Loop labels).
2. **Surface condition** per lot frontage (Brás).
3. **Sidewalk side and GPS correction:** West Loop's geometry and Brás's hand-corrected GPS as references; baselines from the graph paper.
4. **Transfer between cities:** tune on one, test on the other.

**Not claimed:** neither area represents its city; SAM3 masks are machine output, not ground truth; the Brás GPS was corrected by hand to match frames to lots, so it is a reference with its own error.

**Venue:** NeurIPS's datasets track or Scientific Data; decide once the schema and the rights are settled.

## 4. Work plan

Status of each phase is in [STATUS.md](STATUS.md).

**Graph paper:**

| Phase | Work | Gate or output |
|---|---|---|
| **Pre-step S0. Data review** (Renzo) | Review the voice transcripts and the video frames, fix and exclude, record every change ([METHOD §6](METHOD.md#6-transformations-step-by-step)) | Reviewed inputs. The input-versus-reference rule is agreed first (open question 3) |
| **P0. Data contract** | Clocks, side cue, zones | Done ([RESULTS](RESULTS.md#phase-0-results-sessions-clocks-runs-side-cue-and-zones)) |
| **P1. Tile2Net on West Loop** | Tiles from the 2025 orthophoto; run as released on desktop-01; first look at its corners on Morgan | Baseline layers. **First:** the earliest risk check |
| **P2. Reference v2** | One consistent pass for Morgan's curbs and back; extend to D2 and the test blocks; crosswalks, corners, ports and transitions labelled blind; freeze the splits | Instructions frozen; disagreement recorded |
| **P3. One scorer** | Extend `walk2net/evaluate/score.py` to read Tile2Net-format layers and compute section 2.6's metrics; score Tile2Net first | Baseline table on development blocks |
| **P4. Walk only (B)** | From the phase 2b walking lines: cells, centrelines, corner cells, ports, transitions, in Tile2Net's format. Morgan, then D2's corners and jogs | Development scores next to Tile2Net |
| **P5. Walk + Tile2Net (C)** | Registration, matching, the edits of section 2.4, provenance | Development scores; settings frozen |
| **P6. Gates 1a and 1b** | A, B and C once on the test blocks, **after the last collection day** | Section 2.6's tables, whatever they show |
| **P7. Enrichment** | Stations, features, port and crossing attributes; tape, inclinometer and LiDAR references; lens calibration | Section 2.7's table |
| **P8. Routes** | Section 2.8 on the test blocks | Route validity table |
| **P9. Paper** | Section 2.9 | Draft |

P1 and P2 come first and run at the same time.

**While collection continues** (until early or mid December): assign every route-plan module to development or test in `splits.csv` before it is walked ([METHOD §4](METHOD.md#4-how-the-data-are-managed)); development runs grow as days arrive; test passes get only the automatic checks until the frozen run.

**Workstreams added on 3 November:**

| Workstream | What | Size | Gate |
|---|---|---|---|
| Calibration in the field | A calibration day on Morgan and a short daily routine: [CALIBRATION_DAY_PLAN](CALIBRATION_DAY_PLAN_2026-11-03.md), **under discussion** | About 3.5 h, plus about 10 min a day | Height, step length and lens per collector and phone; error models for width, curb distance and slope |
| Source ablations | Each quantity from GPS alone, + motion, + crossings, + video, + Wi-Fi, + aerial ([METHOD §10](METHOD.md#10-comparing-sources-the-ablation-matrix)) | Runs as P3–P5 progress | Part of the Gate 1 and Gate 2 tables |
| Exploratory sensors | Wi-Fi as a side cue; barometer on a known level change; magnetometer under the 'L' ([METHOD §11](METHOD.md#11-exploratory-sources-time-boxed)) | Two weeks, then stop or adopt | The Wi-Fi side cue beats shuffled labels on a second day |
| Second detector | Project Sidewalk's models (section 2.7) | One week | Precision and recall on a labelled sample |
| Level 3 | Measured proxies; the collectors' talk kept as an exploratory measurement, not the core (decision 30) | After P7 | Exploratory |

**Dataset paper** (renamed DS0–DS6 on 4 November, so they no longer collide with the field days D1–D3):

| Phase | Work | Gate before moving on |
|---|---|---|
| **DS0. Inventory and transfer** | Every capture in RustFS with a manifest; Brás from the `2025_Auditoria_Calcadas` Drive folder ([datasets/](datasets/README.md)) | Checksums verified at the destination, or an exclusion reason |
| **DS1. The same processing for both** | Frames, SAM3, redaction, Whisper (West Loop only), motion; Brás later with the same prompts (decision 22) | Every capture has masks, redacted frames and motion events on one time base, or an exclusion reason |
| **DS2. One label schema** | Four levels: frame, lot frontage or sidewalk stretch, crossing, walking run. Each label present, absent or unknown, with provenance. Start from the 2024 taxonomy | Schema and labelling guide frozen |
| **DS3. Labels** | West Loop: the shared reference (P2) plus crossing elements; the chosen transcript corrected, tagged and anonymised. Brás: import the audit, relabel a stratified sample blind | Agreement and effort reported per label type |
| **DS4. Privacy, ethics, rights** | Redaction miss rate on a sample; audio only as annotated transcripts (decision 23); consent and ethics approval for both cities; written agreement and a licence from the Brás audit's partners (its team, Alobrás, IME-USP) | Written approvals; miss rate reported |
| **DS5. Splits, tasks, baselines** | Splits by corridor with spatial buffers (West Loop test: D3; Brás by route group); the four tasks; baselines (SAM3 zero-shot, the audit's classifier, the graph paper's GPS baselines) | Splits frozen before any baseline is tuned |
| **DS6. Release and paper** | Data laid out like the workspace, a loader in sideseeing-tools, a datasheet, a fixed evaluator | Someone else reproduces one baseline from the release alone |

**Older phase names**, used in STATUS before 4 November and in the archived plans:

| Old name | Now |
|---|---|
| G0 data contract (PAPERS), phase 0 (GRAPH_GPS_PLAN) | P0 |
| G1 reference, phase 1 | P2 |
| G2a ladder, G2b cells, phase 2 | The walking lines that P4 starts from ([RESULTS](RESULTS.md) 2a, 2b) |
| G2c fieldwork | The calibration day and the free test routes |
| G3 corners and alternatives, phase 3 | P4 (corners); alternatives parked (section 8) |
| G4 held-out test, phase 4 | P6 |
| G5 comparisons, phase 5 | P1, P3 and P5 |
| G6 paper | P9 |
| D0–D6 (dataset paper) | DS0–DS6 |

## 5. Decisions

One numbered list. Numbers 1–14 are those of the October [PLAN](archive/PLAN.md), which other pages cite (AGENTS.md cites 2 and 14); later decisions continue from 15. A revised decision is edited in place, with the revision dated.

| # | Date | Decision |
|---|---|---|
| 1 | 12 Oct | GPS and sensor recordings give the first prototype; video and public aerial imagery refine, constrain or extend it. *Revised 3 Nov: aerial imagery is part of the main method (decision 24).* |
| 2 | 12 Oct | **Construction is automatic.** No crowdsourcing or human labelling for construction. A separate human-verified reference is allowed for evaluation. |
| 3 | 12 Oct, revised 24 Oct | A pedestrian graph of geographically embedded lines, with a second, linked view made of polygons: the **cells** (one strip per sidewalk side per block, one per corner, one per crosswalk, with zones). Each edge is its cell's centreline; each node sits in a corner cell; cells connect only through ports. Total, clear and per-zone widths are all stored. No 3D geometry. |
| 4 | 12 Oct | Nodes at changes in connectivity: junctions, crossing attachments, physical ends, coverage boundaries. A coverage boundary is not a dead end. |
| 5 | 12 Oct | A bend, a GPS sample, a frame or an object does not by itself need a node. |
| 6 | 12 Oct | Street-level and aerial inferences are combined by **keeping their union** and marking the source on every element. Routing eligibility stays open. |
| 7 | 12 Oct | Begin with overlays of GPS recordings on aerial imagery. *Done in the pilot and West Loop notebooks.* |
| 8 | 12 Oct | No diagonal road crossings, unless the crosswalk itself is diagonal. |
| 9 | 12 Oct | Document failure cases and revise definitions; a rule is a testable choice, not a fixed ontology. |
| 10 | 12 Oct | Collect all sidewalks of one Chicago area. Each collector uses MultiSensor on their own phone. *Revised: the area is West Loop (decision 13); collection runs until early or mid December.* |
| 11 | 12 Oct | Street-adjacent sidewalks on both sides of every street, with the vest. Keep the recorded direction separate from the direction a passage allows. *Revised 4 Nov: each street is walked out on one side and back on the other, crossing the walked street and back at every corner ([FIELD_PROTOCOL](FIELD_PROTOCOL.md)).* |
| 12 | 12 Oct | First pilot near UIC (Near West Side), Renzo alone with a moto g 5G (2023). *Done 14 October ([archive](archive/PILOT_NEAR_WEST_SIDE.md)).* |
| 13 | 16 Oct | River North selected for the full collection. *Revised: River North dropped; **West Loop** is the collection area ([FIELD_PROTOCOL §5](FIELD_PROTOCOL.md#5-the-area)).* |
| 14 | 16 Oct | **Voice:** collectors speak code words and remarks while walking. The words are an **evaluation reference only**: construction and any vision-language model run without them. A later, declared experiment may compare "automatic" with "automatic + voice". MultiSensor is the only app. |
| 15 | 24 Oct | **OSM is never used for map matching.** The three input regimes (street only, street + aerial, map-assisted) stay separate; an OSM-assisted track is only a map-assisted baseline. |
| 16 | 25 Oct | After phase 0: zone prompts approved (`road`, `grass`, `tree pit`, `building`, `fence`); motion events on the video clock; runs split at straight crossings; the protocol rule joins the baselines. |
| 17 | 25 Oct, revised 30 Oct | Camera height: first inferred from the video; then **measured on the vest, 1.30 m**, and used since ([RESULTS](RESULTS.md#phase-2b-notes-the-curb-from-the-video-on-morgan) 2b §7). Each collector is to be measured. |
| 18 | 25 Oct | **D3 (Sangamon and Peoria) is strictly held out:** run once, every setting frozen, reported whatever it shows. |
| 19 | 25 Oct | The walking-line gate is geometry (inside the sidewalk, nearer its centreline than the smoother). *Superseded 3 Nov by Gate 1 (section 2.6).* |
| 20 | 25–26 Oct, kept 3 Nov | **The reference:** the City's curb lines, checked against the 2025 orthophoto; the back of the sidewalk from Cook County parcels (26 Oct, replacing hand tracing). To review with the advisors (open question 2). |
| 21 | 25 Oct | Both papers proceed at the same time. |
| 22 | 25 Oct | Brás: rights deferred; its GPU run uses the West Loop prompts, later. |
| 23 | 25 Oct | Audio is released only as annotated transcripts. |
| 24 | 3 Nov | **Tile2Net is the baseline.** The walk's network (B) stands on its own first; the fusion (C) comes second and reads Tile2Net's output without changing it. Not a replacement for Tile2Net. |
| 25 | 3 Nov | **Tile2Net runs as released.** A Chicago fine-tune is parked. |
| 26 | 3 Nov | **Test:** routes walked not in straight lines, drawn at random before the walk, with D3 recommended in addition. *The D3 part is to confirm.* |
| 27 | 3 Nov | Reviewers double-label a sample of the reference. |
| 28 | 3 Nov | Visual embeddings are future work. |
| 29 | 3 Nov | A data-review pre-step (S0, Renzo) before the pipeline. |
| 30 | 3 Nov | The collectors' talk is kept as an exploratory measurement, not as the core idea. |
| 31 | 3 Nov | Venue and title: later, with the advisors. |
| 32 | 4 Nov | **Field days follow the volunteer briefing** ([FIELD_PROTOCOL](FIELD_PROTOCOL.md)), which replaces the October field rules. North–south streets: east side south to north, then west side north to south. East–west streets: south side west to east, then north side east to west. The calibration day is a separate plan, under discussion. |
| 33 | 4 Nov | The graph is called the **pedestrian graph** (`PedestrianGraph` in code); it was the "passage graph" before. |
| 34 | 4 Nov | **The method becomes software anyone can run:** an installable package in this repository (`walk2net`, a working name), reproducible and usable on any area by anyone who collects with the protocol. Architecture agreed the same day: [ARCHITECTURE.md](ARCHITECTURE.md). |

## 6. Open questions

1. **The margins** for Gates 1a and 1b, from an established standard, with the advisors, before any test result.
2. **The curb source** for the reference, with the advisors.
3. **Inputs and the reference stay apart.** A source that feeds the pipeline cannot also be the reference for the same quantity. The data review (S0) may fix and exclude (a wrong clock, an unusable frame, a transcript error); a human label of content ("a ramp here") belongs to the reference, or construction is no longer automatic (decision 2). To agree before S0 is built.
4. **The free test routes:** how many, and how they are drawn.
5. **Brás agreement sample:** its size, and who relabels it.
6. **Brás as a test for the graph paper:** its hand-corrected GPS says which side each frame is on, but its protocol crosses each crosswalk once, without the ladder's repeats. Decide after P6.
7. **Slope:** running slope only, or cross slope too as an exploratory result.
8. **The calibration day:** its date, blocks, people and equipment ([CALIBRATION_DAY_PLAN](CALIBRATION_DAY_PLAN_2026-11-03.md) §8).

## 7. Risks, and what would change the plan

- **Tile2Net is weak on Chicago imagery.** The comparison would flatter us. It runs as released and is reported as such.
- **West Loop is an open grid.** Tile2Net may already do well on plain corners. Stratify by corner type and canopy, and put the claim where the difference is: jogs, alleys, driveways, faded crossings, ramps.
- **The reference favours the aerial view.** Report by stratum (section 2.5).
- **Coverage is unequal.** Score walked blocks only, and report coverage and field effort openly: "aerial for coverage, the walk for correctness and attributes".
- **The port- and transition-level reference is costly.** Limit it to the test blocks' corners, with a second labeller on a sample.
- **Few test corners give wide intervals.** Count them before freezing the splits; add a later day to the test set if needed.
- **The method leans on the protocol** (out and back, every crosswalk crossed there and back). Declare it an assisted survey; the free test routes measure how much it depends on that.
- **The rung is not a clean measurement.** Speed changes during a crossing, and the far end lies past the far curb. If crossings vary more than the side separation they fix, keep the rung only as a topological tie.
- **The video side cue fails** with pitch changes or at dusk; side identity then rests on the rungs.
- **Cells are only as good as the projection.** If width errors exceed about 0.3 m against the tape, cells stay outlines with wide bands; if zones do not separate, report total and clear width only.
- **Cross slope is below what the phone resolves.** Then report running slope only.

## 8. Parked for later review

| Idea | What it would add | Why parked | Revisit when |
|---|---|---|---|
| Alternative groups | Competing versions of an uncertain element instead of one answer | Gate 1 needs one network; `unknown` and `conflicting` keep the honesty for now | P4 shows many corners the walk cannot decide |
| Route queries per consistent graph | Routes answered in each consistent version, never their union | Depends on alternative groups | With them |
| Risk–coverage routing (critique H2) | Fewer false route claims at the same coverage | A study of its own; needs many ambiguous intersections | After the full collection |
| Revisits chosen by route impact (H3) | Which block to walk again | Needs H2 | After H2 |
| Aerial union at full scale | Our graph beyond walked blocks | This paper scores walked blocks only | After Gate 1 |
| Brás as a second test city | The method in another city and protocol | No ladder repeats in Brás | After P6 (open question 6) |
| Change over time | Real change against alignment error | Needs visits months apart | A second season |
| Perception study | How pedestrians feel, from many raters | Needs its own design, ethics and raters | After the Level 3 proxies |
| Cross slope | Accessibility | Probably below the phone's resolution | After running slope works |
| Visual embeddings per edge | Search sidewalks by appearance | Other work first (decision 28) | After Gate 2 |
| Tile2Net fine-tuned on Chicago | A fairer aerial baseline | Runs as released (decision 25) | If it clearly fails on Chicago, or a reviewer asks |

## 9. Renzo's ideas of 3 November, and where they went

The ideas and the full assessments are in the [graph paper plan](archive/GRAPH_PAPER_PLAN_2026-11-03.md) §14.

| Idea | Verdict | Where it went |
|---|---|---|
| 1. Calibration pilots, and comparing sources | The goal fits; one modular calibration day and a daily routine instead of 3–5 pilots | The calibration plan; the ablation matrix ([METHOD §10](METHOD.md#10-comparing-sources-the-ablation-matrix)) |
| 2. Unconventional data: Wi-Fi, light, pressure | Fits if time-boxed; Wi-Fi is the promising one | Exploratory sensors, two weeks ([METHOD §11](METHOD.md#11-exploratory-sources-time-boxed)) |
| 3. Project Sidewalk's models | Fits, and matters more than "minor": the only models that rate condition | Gate 2's second detector (section 2.7) |
| 4. Conditions and pedestrians' feelings | Conditions fit now as Level 3; feelings need a perception study | Level 3 (section 2.3); perception study parked (section 8) |

## Sources

- Hosseini et al., [Mapping the walk](https://www.evl.uic.edu/pubs/2703) (Tile2Net), Computers, Environment and Urban Systems 101, 2023; [code](https://github.com/VIDA-NYU/tile2net).
- [PathwayBench](https://arxiv.org/html/2407.16875v1).
- Project Sidewalk: [sidewalk-cv-2021](https://github.com/ProjectSidewalk/sidewalk-cv-2021); Liu et al., ASSETS 2024; [RampNet](https://arxiv.org/abs/2508.09415).
- Damaceno et al., [SideSeeing](https://arxiv.org/abs/2407.06464), arXiv 2407.06464, 2024.
- The Brás audit: its report (`RELATÓRIO DA AUDITORIA DE CALÇADAS - BRÁS`, supplied by Renzo) and its GeoPackage, `sao-paulo/bras/processed/auditoria_calcada_bras.gpkg` in RustFS (counts read on 25 October).
- The October sources (GPS positioning, indoor landmark mapping, width and slope from images, linked polygons and lines) are listed in the [graph and GPS plan](archive/GRAPH_GPS_PLAN_2026-10-24.md).
