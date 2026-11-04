# Sideseeing: from recordings to defensible pedestrian connectivity

Research critique and proposed experiments, 23 October 2026. This is a proposal, not an amendment to the agreed collection protocol or a claim that reconstruction has been validated.

For test cases, baselines, labels, metrics, and falsification criteria for the three main hypotheses, see [Sideseeing: testable graph hypotheses](HYPOTHESIS_EXPERIMENTS_2026-10-23.md).

**Recommendation.** Develop a benchmark and method for recovering pedestrian connectivity from sparse, imperfect observations, with explicit uncertainty about passage identity and transitions. Make the principal empirical question whether retaining those uncertainties improves route reliability at useful coverage and acquisition cost. A labeled Chicago dataset is a valuable foundation. A graph schema, multimodal pipeline, or attractive map alone is unlikely to distinguish the work sufficiently from existing research.

The proposed paper question is:

> When can sparse phone recordings establish which pedestrian passages connect, and can evidence-aware inference reduce false route claims compared with committing early to one map?

The strongest eventual result would be a measured tradeoff: fewer invalid routes at matched query coverage, or more valid route answers at a fixed empirical error budget, with an explanation of which observations resolve each ambiguity. This is a hypothesis to test, not a result already obtained.

**What was reviewed and what remains unverified.** I read the ten Markdown documents in `network/docs/`, the West Loop notebook's source and saved textual results, and the primary sources linked below. I examined the notebook's route fitting, side assignment, turn detection, crossing matching, corrected-track construction, and timestamp conversion. I did not rerun the raw-data analysis, decode the videos, establish synchronization independently, or verify the physical network in the field. Numbers below are notebook reports or derived diagnostics, not new measurements. The literature review is targeted rather than systematic; it does not establish a “first-ever” claim.

Your current message establishes West Loop as the ongoing collection area. Some documents still call River North selected and West Loop a candidate. Those are historical planning statements, not the current status.

**What the current work establishes—and what it does not.**

The plan already makes sound distinctions: physical passages versus capture trajectories; direction of observation versus traversal permission; coverage endpoints versus physical endpoints; topology versus evidence association; and OSM planning versus reconstruction. Preserve these distinctions.

The four sessions summarized in `network/west_loop.ipynb` cover 19–20 October, with approximately 175 minutes of recording on Morgan and the Aberdeen–Madison–Carpenter corridor. They establish a useful development corpus, not a representative sample of Chicago or four independent experimental units for every claim.

| Notebook finding or implementation | Research interpretation |
|---|---|
| Approximately 25% of eligible along-street fixes fall on the other half of the fitted street; reported offsets from mapped sidewalks are several metres | Strong motivation to investigate side ambiguity. These figures depend on fitted OSM geometry and a session side estimated from the median GPS offset; they are not independently surveyed lateral errors. |
| Crossing identification uses gravity-projected gyroscope turns and blockwise heading references | A useful candidate baseline. Absolute reference directions and crossing associations also use the known route and OSM. This is not yet map-free crossing reconstruction. |
| Crossings are matched to OSM candidates, including a 40 m matching limit; corrected paths use mapped sidewalk offsets | Counts and corrected distances are conditional on a map and rules. A missing OSM crossing can be omitted even when a physical crossing occurred. |
| Corrected-track construction joins consecutive pieces and follows the nominal route through deviations | Suitable as a diagnostic under its stated assumptions. Those joins must not become unverified graph edges, and that path cannot serve as independent geometry ground truth. |
| The reported 360-degree routine usually produces approximately 270-degree turns; crossings have multiple traversals | Collection behavior supplies strong event cues. Quantify the benefit and effort as an assisted acquisition protocol. Repeated passages remain correlated observations of one physical connection. |
| Video headers indicate FHD; sensor streams are dense; camera pitch and lighting differ between sessions | Encouraging data availability, but headers and sample rates do not establish visual usability, camera calibration, or synchronization. |
| Sensor timestamps are mapped to UTC through a median clock offset and metadata video start | A reasonable provisional clock model. Check residuals, offsets and drift using visible events near the beginning, middle and end; inspect video presentation timestamps. |
| The notebook identifies its two route corners as particularly uncertain | Use these as development cases. Select fresh intersections for held-out evaluation after methods and thresholds are frozen. |

Several document claims need more careful wording in a paper. “GPS settled within 6 m” is a reported-accuracy criterion, not independently measured position error. “All crosswalks crossed” refers to a mapped candidate inventory and heuristic assignments. “The gyroscope can tell the curb” overstates what relative orientation alone identifies. Similarly, a scope boundary at a bridge is not necessarily a physical sidewalk end. Distinguish these cases in annotations and manifests.

**The literature substantially narrows the novelty claim.**

| Prior work | What it already contributes | Consequence for Sideseeing |
|---|---|---|
| [OpenSidewalks schema](https://github.com/OpenSidewalks/OpenSidewalks-Schema) | Explicit pedestrian nodes, edges, zones and topology conventions | Use compatible semantics and export. Separate sidewalk sides and connectivity nodes are not new. |
| Ning et al., [Sidewalk extraction using aerial and street view images](https://journals.sagepub.com/doi/10.1177/2399808321995817), online 2021 / volume 2022 | Combines aerial extraction with street-view evidence to restore missing or occluded sidewalks | “Fuse overhead and street imagery” is already established. |
| Hosseini et al., [Mapping the walk / Tile2Net](https://fmiranda.me/publications/pdfs/tile2net.pdf), CEUS 2023 | Converts aerial segmentation into pedestrian polygons and networks | Include a credible aerial-only baseline, not just raw GPS. |
| Zhang et al., [APE](https://arxiv.org/abs/2303.02323), 2023 | Pedestrian imagery annotations and inference using a street-network prior | Compare input assumptions explicitly; map-conditioned and map-free methods answer different questions. |
| Zhang et al., [PathwayBench](https://arxiv.org/html/2407.16875v1), 2024 manuscript | Pedestrian graph benchmark with intersection-scale routability evaluation | Routability-first benchmarking is established. Extend it with evidence, side identity and uncertainty. The [repository](https://github.com/TaskarCenterAtUW/pathways-bench) currently links three city releases and lists others as forthcoming; do not equate all claimed coverage with immediately downloadable data. |
| Han et al., [TraversRL](https://arxiv.org/html/2607.17479v1), accepted ECCV 2026 | Grows pedestrian graphs from aerial images using sequential prediction and reinforcement learning | A direct contemporary comparator. Its described experiments seed from a ground-truth node and filter disconnected graphs in the WashingtonInter construction. Reproduce those conditions separately from autonomous seeding and genuine disconnection tests. |
| Blanke et al., [Crowdsourced Pedestrian Map Construction](https://www.ulfblanke.de/research/urbaniot14/urbaniot14.pdf), Urb-IoT 2014 | Infers pedestrian maps from GPS trajectories at large events | Trajectory-to-pedestrian-network construction is established; sparse sidewalk-side recovery is a sharper target. |
| Naidu et al., [iOSPointMapper](https://arxiv.org/abs/2512.22392), 2025 manuscript revised 2026; presented at TRB 2026 | Ground-level feature mapping with RGB, LiDAR, GPS/IMU and human validation | Phone-based multimodal sidewalk mapping is not sufficient novelty. Sideseeing's lower-cost sensor regime and topology task need explicit evaluation. |
| Ranganathan and Dellaert, [Online Probabilistic Topological Mapping](https://dellaert.github.io/files/Ranganathan10ijrr.pdf), IJRR 2011 | Maintains distributions over alternative topologies from sequential observations | Multiple topology hypotheses and Bayesian graph inference are established ideas, not inventions of this project. |
| [RoNIN](https://arxiv.org/abs/1905.12853), ICRA 2020; [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3), T-RO 2021; [Hydra](https://www.roboticsproceedings.org/rss18/p050.pdf), RSS 2022 | Inertial localization, visual-inertial mapping, and structured scene representations | Reuse appropriate localization tools. A pose graph is not automatically a pedestrian passage graph. |
| [Sidewalk Environment for Visual Navigation](https://zenodo.org/records/3526490), 2019; [SidewalkBench](https://arxiv.org/abs/2606.16953), 2026 preprint | Image/connectivity environments and simulated sidewalk navigation evaluation | Distinguish physical network reconstruction from learning an agent to navigate an existing environment. |

Also relevant: [Project Sidewalk](https://makeabilitylab.cs.washington.edu/media/publications/Saha_ProjectSidewalkAWebBasedCrowdsourcingToolForCollectingSidewalkAccessibilityDataAtScale_CHI2019.pdf) for annotation design; [Lieu et al.'s September 2026 preprint](https://arxiv.org/abs/2609.17882) for the limits of uncalibrated VLM confidence on sidewalk attributes. The latter is an attribute study, not evidence about Sideseeing topology performance.

My inference from this literature is that the promising gap lies at the intersection of sparse pedestrian capture, uncertain passage correspondence, independently checked transitions, and the consequences for routing. Absence of an exact match in this search is not proof of novelty. Before submission, expand citation tracing around these papers and compare their full input/output and evaluation contracts.

**The graph should express claims about the world, not just store lines.**

Keep the physical representation simple: a geographically embedded multigraph, potentially with level separation, whose edges are passages and whose nodes mark meaningful connectivity events. Avoid inventing a new graph database or adopting a GNN merely because the output is a graph.

Separate four logical records; these can initially be ordinary tables and GeoJSON files:

| Record | Minimum content |
|---|---|
| Observation | Immutable capture/image ID, modality, original timestamp or interval, clock transform/version, sensor or camera frame, quality and visibility metadata |
| Passage hypothesis | ID/version, endpoint references, polyline, passage type, level/separation, existence state, geometry uncertainty, temporal validity and coverage-boundary status |
| Transition hypothesis | Specific departure and arrival endpoints, physical transition type, support/contradiction, observed direction, separately modeled traversal/access state |
| Evidence association | Observation-to-claim relation, relevant time and passage interval, derivation/model version, support versus contradiction, association uncertainty, shared dependency group |

A transition can be implemented as a short connector edge. No exotic mathematical structure is required. Explicit transition records prevent all movements at an intersection from becoming implicitly allowed when its geometry is collapsed into one node. Once a small open corner is verified as mutually connected, ordinary node adjacency can be sufficient; do not model restrictions that the environment does not have.

Use several confidence dimensions: passage existence, geometry, identity/side association, endpoint connectivity, and time-specific traversability. A certain sidewalk with an uncertain crossing attachment is not equivalent to an uncertain sidewalk. “Not observed,” “occluded,” “contradicted,” “temporarily blocked,” and “outside coverage” have different meanings.

In particular, observed traversal supports a physical passage for that collector at that time. It does not by itself establish legal permission, reverse-direction permission, current availability, or suitability for every pedestrian. General walking still needs a declared physical/access policy; richer accessibility attributes can remain out of scope.

Adopt OpenSidewalks-compatible export where possible. Its current conventions distinguish the road-surface crossing, curb interfaces, and connecting footways to sidewalk centerlines. Keep uncertain alternatives and detailed evidence in an accompanying representation rather than flattening them into a deceptively definitive export. Pin the schema version used.

Treat camera location and observed-object location separately. A frame captured on one sidewalk may show the opposite sidewalk or a distant crossing. Attaching every detection to the nearest GPS fix reproduces the very side-association error the project should study. When localization is insufficient, preserve the visual relation without forcing a global point.

Version passage splits and merges. If a newly observed crossing splits an edge, retain lineage and remap evidence intervals; an observation ID should not change because the graph changes. This directly supports day-by-day reconstruction.

**The most important change: the retained union must not be the routable graph.**

Suppose two recordings might depict the same sidewalk or opposite sidewalks. Those are alternative explanations. If their edges and endpoint assignments are all inserted into one traversable union, a router can combine mutually incompatible explanations and produce a route supported by neither.

Maintain a small set of consistent local hypotheses initially. A research formulation could be:

`P(G, X, A | D, M)`

where `G` is passage topology and geometry, `X` is the capture trajectory/pose state, `A` associates observations with passages, `D` contains sensor and imagery evidence, and `M` is an explicitly declared map prior, if present. This is a formulation, not a claim that a posterior has been implemented or calibrated.

Start with bounded ambiguous sites and a few alternatives: same/different passage, one of two crossing attachments, connection/no connection, or unresolved continuation. Compare an early-commitment baseline with retaining alternatives. Extend to a larger inference model only if this experiment demonstrates a useful gain.

A route must be consistent within a hypothesis. For a fixed proposed route `r`, a calibrated weighted ensemble could estimate support by summing the weights of graphs in which that whole route exists and satisfies the declared traversal policy. If the weights are merely heuristic scores, report ensemble support rather than a probability guarantee.

Two distinctions matter:

- “Every hypothesis contains some route” does not mean “one fixed route works in every hypothesis.” The alternatives may require different crossings.
- Multiplying independent edge probabilities is generally unjustified: shared GPS drift, one ambiguous intersection, or the same image-derived alignment can affect many edges together.

Return a supported route, a conditional candidate with its unresolved transitions, or insufficient evidence. Reserve “no physical route exists” for cases supported by an adequately complete reference or observation model. Evaluate abstention so the system cannot appear reliable simply by answering nothing.

Visibility belongs in the observation model. Failure to see a sidewalk behind trees is missing information. An unobstructed image of a barrier is different evidence. Street and aerial predictions may also share map priors or alignment; two source labels do not imply two independent votes.

**A concrete opportunity in evaluation: preserve sidewalk-side identity.**

PathwayBench's boundary-pair traversability checks whether any entry on one polygon boundary can reach any exit on another. That is useful, but it can discard which physical sidewalk each entry belongs to. The following is my constructed counterexample to that aggregation, not a reported failure rate or a run of the authors' implementation.

Take a rectangular region with four ports: northwest (`NW`) and northeast (`NE`) on its north boundary, southwest (`SW`) and southeast (`SE`) on its south boundary. Let:

| Reference | Wrong prediction |
|---|---|
| `NW — SW` and `NE — SE` | `NW — SE` and `NE — SW` |

The predicted lines crossing geometrically do not share a graph node. Both graphs have four nodes, two edges, two components, and degree one at every node. Both allow north-boundary to south-boundary traversal. But the prediction connects each entry to the wrong sidewalk exit.

A small standard-library calculation confirmed boundary-pair Jaccard = **1.0**, exact port-pair Jaccard = **0.0**, with two false and two missing reachable port pairs. This is a logical limitation of that aggregation, not proof that PathwayBench's entire metric suite fails; geometry or other checks may expose the problem.

Evaluate reachability between matched physical ports in addition to the original benchmark metrics. Match ports with location, side, level and passage context, retaining unmatched ports as errors rather than snapping them across the street. Test sensitivity to matching tolerance. Include crossing attachment identity and transition type because reachability alone can still hide a wrong local shortcut when a longer legitimate route already exists.

Initially this is a useful metric extension. It becomes a research contribution only if it changes conclusions on real systems or reveals material errors that existing measures overlook.

**Experiments that can begin during collection.**

Do not wait for full-area completion. Use Morgan and the two Madison corners as development data, with explicit prior-conditioned labels. Reserve fresh spatial clusters for evaluation. First reconstruct short passage chains and small intersections; long-range localization and full-area fusion can follow.

| Experiment | Comparison | What would support the hypothesis | Failure that changes the plan |
|---|---|---|---|
| Relative motion versus GPS ambiguity | GPS; GPS+IMU; GPS+video; GPS+IMU+video | Better side association and transition detection on the same held-out cases | IMU identifies turns but leaves absolute passage identity unresolved; video is too poorly aligned or occluded |
| Preserve alternatives | Early merge/assignment versus bounded joint hypotheses, using the same candidate observations | Lower false-route rate at matched answered-query coverage | The benefit disappears against a tuned conservative deterministic baseline |
| Aerial contribution | Aerial-only; street-only; simple union/snapping; explicit correspondence with uncertainty | Improvement on occluded or untraversed connections without increased false joins | Aerial evidence mostly introduces wrong attachments, stale paths, or map-prior dependence |
| Collection assistance | Current spin routine versus newly recorded ordinary walking at matched sites | Quantified improvement per additional minute of capture and review | Almost all accuracy depends on ritual markers; then frame the result as an assisted surveying protocol |
| Observation budget | One pass, repeated passes, and later-day revisits | A coverage–error–effort curve showing when extra evidence matters | More correlated frames add little information or false certainty |
| Targeted revisits, later extension | Random; nearest missing target; uncertainty-only; route-impact priority | More corrected route decisions per total collector-minute | Travel costs dominate, or the policy exploits reference labels unavailable at selection time |

Separate map input regimes throughout: (1) sensor-only reconstruction, (2) sensors plus aerial imagery, (3) explicitly map-assisted reconstruction. The current notebook is a useful example of the third regime. OSM-only and a simple OSM-refinement method are serious practical baselines in a well-mapped area. The question “does ground evidence correct or update a good existing map?” may be more useful than rebuilding every visible sidewalk, but it is a distinct task.

Avoid weak comparisons. Use a tuned GPS-only trajectory aggregation baseline, not only raw points joined into a line. Include a basic geometric fusion baseline and a conservative confidence-threshold baseline. Adapt Tile2Net and, if reproducible artifacts are available, TraversRL for the aerial component. Report any unavailable implementation rather than presenting a substitute as the original method. Do not compare published scores across different cities as though they were common-test results.

Keep candidate generation fair. Run both an end-to-end comparison and a diagnostic comparison with fixed candidates. Otherwise a supposed fusion improvement may only reflect access to extra candidate passages. Oracle trajectories, oracle associations or ground-truth seed nodes can diagnose the bottleneck, but must remain clearly labeled upper bounds.

VIO is optional, not a prerequisite for the first graph experiment. Test camera intrinsics, IMU-camera orientation, timing, blur, stabilization and tracking viability before budgeting a large SLAM integration. An IMU-event and visual-transition baseline can already test the central graph hypothesis.

**Collection design should maximize information about failures, alongside coverage.**

The notebook's spin and crossing routine differs from the written straight-ahead, pause-based plan. Preserve both as dated protocol versions. Do not silently describe all recordings as equivalent natural walking. Likewise, opposite sidewalks recorded in opposite directions confound physical side with direction and appearance. Obtain same-side reverse-direction repeats on a small diagnostic subset.

Keep the ongoing coverage program, but reserve a provisional 10–15% of available collection time for controlled diagnostic revisits; this is a proposed budget to revise after measuring effort. Prioritize:

- Same physical sidewalk in both directions and on separate days.
- True nearby non-connections: fences, divided approaches, grade separation where present, or disconnected passages. Verify them rather than assuming absence from a map.
- Passage continuations beyond recording boundaries, plus genuine dead ends.
- Irregular and offset intersections, alley/driveway ambiguity, and observable detours.
- Aerial occlusion and places whose current state differs from the imagery date.
- A small paired ordinary-walk versus assisted-walk sample, with order balanced where practical.
- Another collector/device on shared passages if feasible. If both change together, call it a joint transfer test; a crossed design is needed to isolate device effects.

One traversal of every sidewalk side is an acquisition target, not proof that every junction transition has been observed. Record continuous transitions between collection modules where feasible. Deliberate route overlaps are valuable because they test passage correspondence, not just repeatability of coordinates.

For an untraversed-passage experiment, remove entire traversal intervals across all input streams, including reverse passes and administrative clues. Disclose whether the passage remains visible from another sidewalk or aerial image. Masking spin frames alone does not create ordinary walking; it creates missing data. Natural-walking generalization requires actual natural-walking capture.

**Build a reference for a graph task, not just a large collection of labels.**

The essential annotations are physical passage identities, endpoint/transition identities, verified positive and negative connections, crossing types and attachments, coverage/visibility masks, and time-aligned evidence associations. Dense frame segmentation everywhere is optional and may consume the budget without resolving the main question.

Start with roughly 20–30 diverse intersection or passage motifs across available and upcoming recordings, if coverage permits. This is an ontology and annotation-effort pilot, not a statistically adequate final benchmark by itself. Freeze reference instructions, measure disagreement and effort, and then determine the needed final sample from practical effect sizes and uncertainty intervals.

Reference annotators should be blinded to algorithm output. Double-annotate the pilot and difficult cases, retain unresolved disagreements, and use field revisits for ambiguities that the recordings cannot resolve. A reference made by separately annotating the input video is label-independent but not independent sensing: its invisibility limitations remain. Voice can suggest events for review, but is neither exhaustive nor automatically correct. Missing speech is not a negative label.

Use a three-valued reference where appropriate: verified present/connected, verified absent/disconnected, unknown. Score only adjudicable claims and report how much of the benchmark remains unknown. If geometry is not independently measured, give reference uncertainty and avoid centimetre-scale claims based on an aerial trace.

Split by physical intersection/corridor with spatial buffers. Every repeat of one passage, nearby context, and corresponding aerial crops belongs to the same split. Random frame splits leak nearly identical scenes. Temporal revisit evaluation is a separate task that deliberately reuses place identity. Use clustered uncertainty estimates by site/corridor; thousands of frames or OD pairs sharing one junction are not thousands of independent samples.

If labels are used for training, put them in an explicit supervised track with separate held-out evaluation. This is compatible with automatic inference at test time, but changes the earlier construction assumption and should be declared. The initial reference can remain evaluation-only.

An effective release would contain a broad acquisition tier with manifests and quality flags, and a smaller deeply verified topology tier with raw-to-reference links. Release enough synchronized, reviewed sensor/video evidence to reproduce the claimed baselines, not only cropped keyframes if the methods require motion continuity. Follow the project's existing restrictions on raw audio and incidental identifying data. Document excluded streams, review/redaction effects, source rights, fixed splits, evaluator versions, and a small executable example.

**What to measure.**

| Dimension | Proposed measurements and safeguards |
|---|---|
| Geometry | Error distributions conditional on correctly matched passages, with missed/extra passages reported separately; reference positional uncertainty |
| Topology | False/missing direct transitions, duplicate passages, wrong crossing attachments, local port reachability; PathwayBench-compatible results for comparability |
| Side identity | Accuracy and abstention on known physical passage identities, including extended wrong-side stretches |
| Route behavior | False reachable OD pairs, missed reachable pairs, invalid returned paths, valid answer coverage, detour/stretch for valid routes, and abstentions |
| Uncertainty | Empirical risk–coverage curves; Brier score/reliability analysis if probabilities are produced; separate confidence for side and connectivity |
| Evidence association | Whether the cited interval actually supports the claimed passage/transition and side; interval localization quality; provenance completeness |
| Cost | Acquisition, travel, annotation and review minutes; compute and storage; all per verified unit or valid route improvement |
| Transfer | Spatial holdout, natural-walking protocol, day/lighting, joint collector/device, and external city where appropriate data exist |

Choose OD queries before examining method outputs. Include short crossing-sensitive pairs, same-side pairs, longer routes, verified disconnected pairs, and boundary cases. Separate intrinsic local reachability from routes allowed to leave the benchmark crop. Freeze the boundary convention so a valid detour outside the crop is not mislabeled as impossible.

Evidence provenance needs a behavioral test. Remove or corrupt an input source and rerun its descendants; inspect whether confidence and claims change sensibly. Redundant evidence can legitimately preserve an edge, so deletion of one source need not delete the edge. Measure support correctness separately from the existence of a file link.

Do not treat confidence as a deployment guarantee. With rare topology failures, a small pilot cannot establish a very low route-error probability. Select thresholds on development/validation data, freeze them before test evaluation, and show interval estimates and stratified failures rather than one pooled percentage.

**Measurable gates and publication strategy.**

| Gate | Deliverable | Decision criterion |
|---|---|---|
| 1. Evidence readiness | All sessions registered; clock model and residual checks; visual quality review; versioned protocols and prior-use ledger | Every included stream has a verified alignment bound or an explicit exclusion/unknown status |
| 2. Representation pilot | Approximately 20–30 motifs, annotation guide, adjudication log, small graph fixtures including the port counterexample | The schema distinguishes the target failure cases; reference disagreements and annotation effort are measured |
| 3. Street-level feasibility | GPS, GPS+IMU, GPS+video, combined street evidence on frozen local splits | Identify whether the dominant error is sensing, localization, correspondence or graph construction; no claim based on cleaned map overlays |
| 4. Core method test | Early commitment versus retained alternatives; common input/candidate controls; route risk–coverage curves | A useful improvement survives a tuned deterministic baseline and site-level uncertainty analysis; otherwise simplify the method claim |
| 5. Fusion and transfer | Aerial-only and map-assisted comparators; held-out corridors; natural-walk and repeat tests | State precisely where each modality helps or fails and how much acquisition it requires |
| 6. Release readiness | Reproducible benchmark, reviewed evidence, fixed splits, evaluator, documentation and representative sample | Another researcher can reproduce a baseline without your route recollection or manual repairs |

Freeze a practically meaningful improvement target after the development pilot and before the held-out test. Do not pick the target after seeing final performance. Increase sample diversity and size based on the observed uncertainty, not on a desired headline kilometre count.

My recommended first paper combines the dataset with one focused method: uncertain passage association and transition inference, evaluated through side-specific connectivity and route decisions. The three contributions would be a benchmark exposing the ambiguity, an inference procedure that handles it, and an empirical account of its benefit and limits. If the procedure adds little, a strong evaluation/dataset paper remains possible; do not manufacture algorithmic novelty.

ACM SIGSPATIAL is my first venue choice for this framing: its [2026 research scope](https://sigspatial2026.sigspatial.org/research-submission.html) explicitly covers spatial graphs, uncertainty, acquisition, and multimodal integration. A computer-vision venue becomes more plausible if the method advances beyond this sensing setup and performs convincingly against contemporary graph-extraction approaches. The [NeurIPS 2026 Evaluations & Datasets call](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets) emphasizes meaningful evaluation rather than dataset size alone and does not require a new model; its current requirements are useful design guidance, not a promise about future calls. The 2026 submission cycle is not a prospective deadline for this work.

Three broader directions are worth retaining, in order of priority:

1. **Topology identifiability and selective routing:** determine which ambiguities each modality can resolve and when the method must abstain. This is the recommended core.
2. **Acquisition based on route consequences:** choose the next observation by expected reduction in consequential route errors per collector-minute, compared with simpler revisit policies. Active information gathering is established in robotics—see the [active SLAM literature](https://arxiv.org/abs/2207.00254)—so the contribution must be pedestrian-specific evidence and cost, not the general idea of information gain.
3. **Temporal updating and uncertain urban analysis:** distinguish real change from alignment error, or propagate alternative topologies into transit access and catchment estimates. These can demonstrate urban-science impact after the underlying reconstruction is reliable.

Do not make a new ontology, a new neural architecture, aerial extraction, SLAM, active collection, accessibility semantics, and an interactive application all prerequisites for the first paper. The immediate research investment should be a small, carefully verified connectivity benchmark and a fair test of whether preserving ambiguity changes route outcomes.
