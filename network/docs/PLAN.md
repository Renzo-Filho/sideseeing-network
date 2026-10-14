# Sideseeing sidewalk network: initial research plan

Draft initiated 12 October 2026, updated 13 October through Q19. This records the design interview; it is not an implementation authorization or a completed specification. No data-processing experiment has been run for this plan.

## Research objective

Automatically reconstruct a geographically embedded sidewalk passage graph from Sideseeing recordings and public aerial imagery, while associating multimodal evidence with its nodes and edges. The first prototype concerns general walking. Interactive applications and specialized accessibility profdefinir protocolo simplificadoiles are future work.

The research includes both topology reconstruction and evidence association. Evaluate these separately: a correctly detected object attached to the wrong sidewalk is an association error; an invented connection between sidewalks is a topology error.

## Decisions agreed with the researcher

1. GPS and sensor recordings provide the initial prototype. Sideseeing video and public aerial/satellite imagery help refine, constrain, or extend reconstruction.
2. Construction is automatic. No crowdsourcing or human labeling phase is planned for construction. A separate human-verified reference is permitted for evaluation.
3. Start with a passage graph: geographically embedded lines connecting nodes. Edges may be polylines. The first representation does not reconstruct sidewalk surfaces or require 3D geometry.
4. Insert nodes at changes in connectivity: junctions/branches, crossing attachments, physical endpoints, and boundaries of reconstructed coverage. Distinguish coverage boundaries from physical dead ends.
5. A bend, GPS sample, frame, or detected object does not by itself require a node. Local observations may refer to positions or intervals along an edge.
6. Combine street-level and aerial inferences by retaining their union and marking the supporting source(s) on nodes and edges. The earlier suggestion to filter uncertain elements out of the prototype was not adopted. Routing eligibility remains an open design decision.
7. Begin with an exploratory study overlaying multiple GPS recordings on aerial imagery.
8. The collection protocol will exclude diagonal road traversals unless the sidewalk/crosswalk itself follows that diagonal. Broader crossing eligibility is deferred until collection details are established.
9. Document failure cases and use them to revise definitions. An initial rule is a testable design choice, not an immutable ontology.
10. Target collection of all sidewalks in a Chicago community area within one to two weeks; choose the area with its workload and team capacity in mind. Each collector uses MultiSensor on their own phone. Register devices after volunteer confirmation. Detailed coverage boundaries, schedules, and acquisition settings remain open; see [COLLECTION_PROTOCOL.md](COLLECTION_PROTOCOL.md).
11. Initial systematic collection concerns street-adjacent sidewalks on both physical sides of streets, using the existing data-collection vest setup. Represented passages are expected to be bidirectional in most cases. Preserve observed recording direction separately from permitted graph traversal. Collect each sidewalk once; route overlaps are permitted for practical, efficient coverage and must be documented and highlighted.
12. Plan the first field pilot on a small sample of Near West Side near UIC, excluding UIC campus sidewalks. Renzo will collect alone with a moto g 5G (2023), MultiSensor and the vest. The scope is the three researcher-drawn routes between Aberdeen and Morgan, Polk to Taylor, in [PILOT_NEAR_WEST_SIDE.md](PILOT_NEAR_WEST_SIDE.md); the practical steps are in [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md). Drawn public mid-block paths are an exploratory pilot exception and are reported separately. This is a pilot-location decision, not the selection of the final full-study area.

## Proposed conceptual structure — pending confirmation

Maintain three related entities:

- **Observation:** source recording/image, time or time interval, original geometry or frame reference, coordinate/time metadata, and known quality information.
- **Graph element:** stable identifier, node role or edge passage type, geographic geometry, and explicit endpoint references for edges.
- **Evidence association:** link from an observation or derived inference to a node, edge, or interval along an edge; include its method and its support, contradiction, or unresolved status.

Preserve the original GPS trajectory separately from an estimated passage geometry. Repeated walks can support one passage even if the trajectories do not coincide.

Proposed provenance categories are street-level only, aerial only, and supported by both. Preserve modality-specific provenance within the street-level category so GPS, inertial, and video contributions remain distinguishable. Conflicting evidence is an additional property, not a fourth exclusive source category. Agreement is not equivalent to independently verified correctness.

### Meaning of union

First retain the inferences from both source families with their original identities and evidence. Then establish explicit correspondences where two inferred elements are judged to describe the same physical passage. Record unresolved correspondences and competing geometries.

Union must not silently mean averaging coordinates, merging every nearby line, accepting one source as authoritative, or connecting every geometric intersection. These operations require separate matching and connectivity rules. The first overlay study should precede their selection.

All proposed elements can remain visible in the prototype. Whether a routing query can traverse every proposed element or must select an evidence-based subset is unresolved.

## Node and edge definitions with cases to investigate

| Case | Initial treatment | Failure or definition to investigate |
|---|---|---|
| Curved sidewalk without a branch | One edge with intermediate shape coordinates | Sharp turns may be confused with junctions; distinguish geometry from connectivity. |
| Mid-block crossing | Split the sidewalk at its crossing attachment | Determine the attachment location and whether repeated observations describe the same connection. |
| Corner with two crossing attachments | Distinct nodes when the attachments occupy distinct locations | Determine when simplifying these into one corner would invent movements or lose meaningful passage geometry. |
| Recording stops mid-sidewalk | Coverage-boundary node | A capture endpoint must not be asserted to be a physical dead end. Determine how the boundary changes when new coverage arrives. |
| Two recordings overlap | Candidate observations of the same passage | Prevent both duplicate edges and incorrect merging of opposite sidewalks. Matching tolerances remain open. |
| GPS track shifts toward the opposite sidewalk | Retain raw observations and an unresolved association | Specify when other modalities can support a correction and when ambiguity must remain. |
| Geometries cross at different levels | Do not create a connection from geometric intersection alone | A 2D graph may need a level or separation attribute without becoming a full 3D reconstruction. |
| Two nearby but separated paths | Separate passages unless connection evidence exists | Spatial proximity alone must not invent a link through a fence, wall, or other separation. |
| Pole or other localized obstacle | Evidence at a position/interval along an edge | If it fully interrupts passage, determine whether this becomes a state restriction, an edge split, or a topology revision. |
| Broad plaza or open pedestrian area | Explicitly unresolved simplification case | A unique passage line may be inadequate; consider multiple representative paths or a later surface abstraction. |
| Sidewalk hidden in aerial imagery | Keep street-level inference and its provenance | Non-visibility must not automatically be interpreted as non-existence. |
| Aerial and street-level observations from different dates | Preserve source dates and conflicting claims | Decide whether disagreement reflects localization, inference error, or environmental change. |
| Legitimate diagonal sidewalk/crosswalk | Represent its actual passage geometry | Do not confuse a genuine diagonal facility with a prohibited collection shortcut. |
| Apparent diagonal caused by a gap between GPS samples | Preserve the sampling gap as evidence | A line between samples is not sufficient proof that the collector walked that straight segment. |
| Sidewalk or crossing observed but never traversed | Retain an inferred element and its source | Define inference acceptance and eventual routing behavior without requiring every passage to have been walked. |

## Proposed sequence of studies

The following checklist is a research sequence, not work already performed. Algorithm families, numerical thresholds, software choices, and data availability are not settled.

### Study 0 — Establish the data contract

Collection protocol design is tracked in [COLLECTION_PROTOCOL.md](COLLECTION_PROTOCOL.md), adapting the Brás audit to a Chicago study conducted by Renzo and at most two volunteers. Full-area sidewalk collection within one to two weeks and each collector's use of their own phone are agreed targets; detailed schedules, device registration, coverage boundaries, and operational procedures remain to be defined.

- [ ] Inspect representative captures: actual columns, units, sensor identities, timestamp origins, sampling gaps, GPS quality fields, and video alignment.
- [ ] Establish the public imagery source, spatial reference, resolution, acquisition date where available, coverage, and usage conditions.
- [ ] Describe the collection protocol, including crossing behavior and capture start/stop conventions.

**Dependencies:** access to representative captures and candidate imagery.

**Acceptance:** an explicit input inventory separates verified properties from unknown ones; filenames alone do not establish sensor meaning or synchronization.

**Verification:** inspect actual metadata and sample records; check a small number of synchronized events before assuming clocks align. No particular sensor-fusion algorithm is selected at this step.

### Study 1 — Plot recordings against aerial imagery

- [ ] Plot raw GPS points and time-ordered trajectories over the same imagery, keeping recordings distinguishable and preserving gaps.
- [ ] Examine selected cases from the table: both sides of a street, repeated traversals, corners, a crossing, and difficult visibility where the available data permit.
- [ ] Record alignment patterns, ambiguities, sampling discontinuities, and apparent source disagreement.

**Dependencies:** Study 0 spatial reference and recording inventory.

**Acceptance:** reproducible diagnostic maps with source identities, scale, timestamps/dates where known, and an issue register. Record missing case coverage rather than assuming it exists.

**Verification:** check coordinate alignment and sample ordering. The overlay is exploratory evidence, not independent validation of sidewalk topology. It must not silently snap tracks to imagery or create inferred edges.

### Checkpoint A — Review observations before selecting reconstruction methods

- [ ] Use the issue register to decide which localization, passage matching, and image interpretation methods merit testing.
- [ ] Select the first bounded study area and freeze an evaluation protocol before tuning reconstruction on it.

### Study 2 — Reconstruct the initial street-level passage graph

- [ ] Specify how ordered captures and available sensors support passage geometry and crossing/junction hypotheses.
- [ ] Apply the node rules, identifying physical endpoints separately from coverage endpoints and unresolved cases.
- [ ] Attach evidence references to every inferred element and preserve raw trajectories.

**Dependencies:** Studies 0–1 and Checkpoint A method decisions.

**Acceptance:** an inspectable graph for the selected area, with explicit endpoint connectivity, source references, and documented unresolved cases.

**Verification:** inspect endpoint consistency, duplicate passage hypotheses, disconnected components, and case-table behavior. Do not require global connectedness as a correctness condition.

### Study 3 — Add aerial hypotheses and reconcile the union

- [ ] Infer candidate aerial passages and associations with street-level elements.
- [ ] Preserve source-only elements, shared support, conflicting claims, and unresolved correspondences.
- [ ] Highlight provenance in diagnostic plots; record every geometry/topology revision and its evidence.

**Dependencies:** Study 2 representation plus selected aerial inference and correspondence methods.

**Acceptance:** the union is inspectable and traceable; no source-only element disappears silently during reconciliation.

**Verification:** review duplicate hypotheses, source agreement, source conflicts, and geometric crossings that must not become graph connections.

### Checkpoint B — Fix graph and query semantics

- [ ] Resolve the routing treatment of proposed or conflicting connections.
- [ ] Confirm which initial node/edge rules survive the failure cases and document additions.

### Study 4 — Evaluate topology and evidence association

- [ ] Compare reconstruction against a separately human-verified reference, keeping evaluation labels out of graph correction and tuning on held-out cases.
- [ ] Evaluate missing/false connections, passage matching, geometry where measurable, and provenance coverage. Report source-specific and union results separately.
- [ ] Run basic route queries under the declared eligibility rules to expose the consequences of topology errors.

**Dependencies:** Studies 2–3, Checkpoint B, and an independent evaluation reference.

**Acceptance:** an error report distinguishing topology, geometry, association, and observation gaps, with no claim that additional coverage alone proves greater reliability.

**Verification:** compare source variants on the same reference area and document any limitations in the reference itself. Choose numerical metrics and success thresholds before final evaluation.

## Intended initial capabilities — proposed

- Query neighbors and passage connectivity.
- Retrieve the observations supporting a node, edge, or edge interval.
- Inspect provenance, ambiguity, and source disagreement in diagnostic plots.
- Combine repeated captures without losing their separate identities.
- Run basic path queries once routing eligibility is defined.
- Export graph geometry and evidence links for inspection and later interaction.

Interactive applications, specialized accessibility routing, and full walkable-surface reconstruction are not established first-prototype requirements. Field collection targets the selected community area's sidewalks; that coverage target does not assert that the initial reconstruction will automatically recover every passage correctly.

## Open design frontier

1. Confirm the exact Near West Side pilot routes and logistics, using a small sample near UIC and explicit overlap labels; the full community area is outside the pilot scope.
2. Is the proposed provenance model sufficient, especially its separation of source identity, source agreement, and evaluation status?
3. Which candidate edges should basic route queries traverse? This does not change the decision to retain the full inference union.
4. What is the operational rule for reconciling two source hypotheses into one physical passage? Study 1 should inform this rather than choosing a distance threshold now.
5. What representation and evaluation are feasible given actual sampling, synchronization, imagery resolution, and capture protocol? These are facts to investigate before asking the researcher to choose algorithms.

## Context and provenance of this plan

The attached proposal, `projeto_bepe-renzo.pdf`, supplies research context; decisions in this interview govern the present scope. The screenshot establishes a recording's file organization but not its complete data contract. The initial literature check identified OpenSidewalks and AccessMap as relevant prior art; no novelty claim has been established by this plan.

- OpenSidewalks schema: https://github.com/OpenSidewalks/OpenSidewalks-Schema
- AccessMap project: https://tcat.cs.washington.edu/accessmap/

This draft does not alter existing repository research plans or implementation files.
