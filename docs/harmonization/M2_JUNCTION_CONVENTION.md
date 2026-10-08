# M2 pedestrian junction convention — draft for decision

**Status: draft proposal, 30 September 2026. Not accepted.** M2 remains deferred from the Chicago-only model and any future SP–Chicago distance ([decision](../DECISIONS.md#decision-defer-m2-in-both-new-models)). This page supplies the first reopening condition, a declared junction estimand and street universe, so that any later algorithm, fixture or acceptance test has a fixed target. It authorizes no construction, rebuild or fit. On 30 September 2026 the user selected the proposed W, A, P and R primaries in §3 and a developed-land denominator (G), whose common source is still undefined.

## 1. Purpose

M2 describes **how often a pedestrian walking the street network reaches a place where streets meet at grade, offering a choice of direction and a street crossing**. A district with 150 such junctions per km² gives pedestrians far more route choices and crossing points than one with 30.

M2 measures **physical street geometry only**. It does not record marked crosswalks, signals, curb ramps, sidewalk presence, crossing legality or safety. Those are pedestrian-accessibility *outcomes*, which the [protocol](../PROTOCOL.md) keeps separate from the morphology selection stage. Crossing facilities are also mapped very unequally: in the matched Overture files (whole buffered extract, segment counts), Chicago has 42,725 `footway/sidewalk` and 23,140 `footway/crosswalk` segments, versus 4,848 and 13,919 in São Paulo.

National definitions are not adopted directly. The US [MUTCD §1A.13](https://mutcd.fhwa.dot.gov/htm/2009/part1/part1a.htm) makes each roadway crossing a separate intersection when a divided highway's roadways are 30 ft (9.1 m) or more apart; Brazil's [CTB Anexo I](https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm) defines *interseção* as "todo cruzamento em nível, entroncamento ou bifurcação, incluindo as áreas formadas por tais cruzamentos". Both exclude grade-separated crossings; they count divided-road crossings differently. This convention is the project's own and applies identically in both cities.

## 2. Physical definition (what a reference labeller decides)

**D1. Eligible street.** A public or private roadway that a pedestrian can walk along or cross: Overture classes `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `living_street`, `pedestrian`, `unclassified` and `unknown`, excluding the `link` subclass. These are the locked [M1 ten classes](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/method_decisions.json) minus `motorway`. Excluded: `motorway` and all `link` segments (ramps and slip lanes), `service` and its subclasses (alleys, driveways, parking aisles), and `footway`, `sidewalk`, `crosswalk`, `path`, `steps`, `cycleway`, `track`. Designated pedestrian streets (São Paulo *calçadões*) are eligible.

**D2. At grade.** Streets meet only if a pedestrian can pass from one to the other on the same surface. Bridges over, and tunnels under, another street create no junction. A junction located entirely on a bridge deck counts if its streets meet at that level.

**D3. Junction.** A **pedestrian junction** is one contiguous at-grade *junction area* where at least three **arms** of eligible streets meet. The junction area is the paved area bounded by the prolongation of the curb lines of the meeting streets, including any traffic islands, refuges and slip-lane islands within it.

**D4. Arm.** An arm is a distinct street direction leaving the junction area along which a pedestrian can continue. Arm-counting rules:

1. The two carriageways of one divided street on the same side of the junction form **one** arm.
2. Slip lanes, turning roadways and ramps are not arms.
3. A street that dead-ends after leaving the junction is still an arm.
4. A pedestrian street is an arm.

**D5. One junction or several.** Two meeting points are the **same** junction when their junction areas touch or overlap, with only roadway, traffic islands or medians of width ≤ **W** between them. They are **separate** junctions when a block, park, plaza, building frontage or median wider than **W** lies between them.

| Configuration | Count |
|---|---|
| Ordinary T or cross | 1 junction (3 or 4 arms) |
| Divided × local; divided × divided, medians ≤ W | 1 junction |
| Divided street with median > W crossed by a local street | 2 junctions, one per carriageway crossing |
| Offset ("jog") T junctions whose areas overlap | 1 junction |
| Offset T junctions separated by frontage | 2 junctions |
| Roundabout or traffic circle whose central island is traffic-only (not a usable plaza or park) | 1 junction; arms are the external approaches |
| Ring street around a usable plaza, park or block | Each meeting point on the ring is a junction |
| Overpass / underpass with no at-grade connection | 0 |
| Stacked junctions on different levels (e.g. Loop upper/lower Randolph) | Each at-grade level is assessed separately, subject to D7 |
| Dead end (1 arm), bend or segmentation point (2 arms) | 0 |

**D6. Explicit pedestrian prohibition.** An arm with an explicit source restriction denying pedestrian access is not an arm. Absence of a restriction is **not** evidence of permission; this residual uncertainty is reported, not resolved.

**D7. Covered and tunnel levels.** Arms lying wholly on segments flagged `is_tunnel` or `is_covered` are excluded in the primary measure (Lower Wacker-type roads). Report them separately.

**D8. Count, assignment and density.** Count each junction once. Assign it to the district containing its representative point (centroid of the junction area or of its member nodes); a point on a shared boundary goes to the lowest unit ID, as in the existing Chicago diagnostic. Arms outside the district still count toward the three-arm threshold, so the network must be read beyond district edges.

`pedestrian_junction_density_developed_km2 = junctions with ≥3 arms whose representative point lies in developed land / developed land km² in the district`

Numerator and denominator use the **same** developed-land support; junctions outside it are reported as a residual, not counted. The gross-area density is a mandatory sensitivity.

Report the arm distribution (3, 4, 5+) beside the density as a diagnostic, not as a weighted variant.

## 3. Parameters

W, A, P and R: proposed primaries selected by the user on 30 September 2026. G: developed land selected; its definition and source remain open.

| ID | Parameter | Primary | Mandatory sensitivities | Why it is a choice |
|---|---|---|---|---|
| **W** | Median or island width that still forms one junction (D5) | 15 m | 9.1 m (MUTCD 30 ft), 30 m | No evidence-derived pedestrian threshold was found. 15 m is a proposal: it keeps ordinary refuges and narrow medians inside one junction, while parkway medians separate. |
| **A** | Alleys (`service/alley`) as arms | Excluded | Included | Chicago alleys are walkable and dense, but they are not the street crossings M2 targets, and M1 excludes them. In the buffered files Chicago has 17,173 alley segments versus 6,976 in SP. |
| **P** | Private access (Overture `recognized: as_private`; Chicago `status=P`) | Included (access-agnostic, as M1) | Explicit-private arms excluded | Access tagging completeness is unverified and may differ between the cities. |
| **R** | Roundabout central-island test (D5) | Imagery judgement in labels | — | The operational proxy (e.g. ring length) must be validated, not assumed. |
| **G** | Denominator | **Developed land km²**, one common source and rule in both cities (source **open**) | Gross km²; hydrographic land km² | Matches the pedestrian purpose: junction frequency within the urban fabric, not diluted by airports, reservoirs, large parks or rural land (O'Hare, Marsilac). Requires a paired developed-land definition that keeps street space inside the support (§7). |

## 4. Operational candidate (to be validated, not accepted)

This is an implementation hypothesis on the matched Overture release. It must reproduce the physical definition on labelled fixtures before any district values are computed.

1. Select eligible segments (D1) and remove the scoped portions excluded by D6 and D7.
2. Form at-grade nodes from shared `connector_id`s, keyed by connector and the scoped level at that position. Two segments without a shared connector never connect, whatever their geometry ([Overture guide](https://docs.overturemaps.org/guides/transportation/segments-and-connectors/)). Where `level_rules` and bridge/tunnel flags disagree, record the case; do not silently choose one.
3. Compute node degree on the eligible at-grade graph and drop degree-2 points.
4. Consolidate nodes into junction complexes along at-grade network spans no longer than a merge distance derived from **W**. Never merge across a level change or by straight-line distance alone (the 2.49 m Loop pair).
5. Count arms per complex as distinct external street directions. Merge parallel carriageways of the same named street on the same side into one arm; drop `link` spans. The earlier `arms(A)+arms(B)−2` rule is a special case to re-test, not a definition.

The literature's network-distance consolidation ([Boeing](https://arxiv.org/html/2407.00258v2)) matches step 4. Planar morphological simplifiers such as [neatnet](https://arxiv.org/html/2504.16198v2) can alter topology at non-planar interchanges and are not suitable without grade handling.

## 5. Synthetic fixtures (part of the definition)

Each fixture has a known answer under this convention. Any operational method must pass them in both cities' source representations before real cases are reviewed.

| Fixture | Expected junctions | Expected arms |
|---|---:|---|
| Four-way crossing of two single-carriageway streets | 1 | 4 |
| T junction | 1 | 3 |
| Divided (median 6 m) × local street | 1 | 4 |
| Divided × divided, both medians 6 m (four map nodes) | 1 | 4 |
| Divided (median 40 m) × local street | 2 | 3 each |
| Cross with four channelized slip lanes | 1 | 4 |
| Offset T, centres 8 m apart, overlapping areas | 1 | 4 |
| Offset T, 40 m apart with frontage between | 2 | 3 each |
| Overpass of a local street, no ramps | 0 | — |
| Interchange of a motorway with an arterial (ramps only) | 0 from the motorway; arterial at-grade ramp-terminal junctions follow D4 (ramps are not arms) | — |
| Traffic-only roundabout with four approaches | 1 | 4 |
| Two at-grade junctions stacked on levels +1 and −1 | Each level judged separately; primary excludes covered/tunnel arms (D7) | — |
| Pedestrian street meeting two residential streets | 1 | 3 |
| Cul-de-sac end; bend with 2 arms | 0 | — |

## 6. Validation and harmonization criteria (to precommit before any result is seen)

1. **Labels.** Draw a stratified random sample in both cities (ordinary grid, divided arterial, ramp/interchange vicinity, stacked/covered, roundabout, irregular periphery). Two reviewers independently label junction identity and arm counts under §2, using orthophotos and LiDAR (Cook 2022; São Paulo GeoSampa 2017/2020, to be verified), before seeing algorithm output. "Uncertain" is a permitted label.
2. **Definition clarity.** Inter-reviewer agreement on junction identity must reach a declared level (proposal: ≥ 90%). Persistent disagreement means §2 is ambiguous and must be revised, not averaged.
3. **Accuracy per city and stratum.** Junction precision and recall, arm-count accuracy, and the count bias ratio *b* = algorithm count / reference count.
4. **Invariance between cities.** The differential bias must be small relative to between-district variation. Proposal: |ln *b*<sub>CHI</sub> − ln *b*<sub>SP</sub>| ≤ 0.05. For scale, the SD of log district density is 0.594 for the SP v2 proxy and 0.424 for the Chicago endpoint diagnostic; those are different instruments, used here only for scale.
5. **Stability.** Report district rank changes across W ∈ {9.1, 15, 30} m and the A/P/G sensitivities.

Passing these tests would satisfy only the estimand and fixture conditions for reopening. A new versioned scope and weight contract would still be required before any M2 value enters a model.

## 7. Known limits

- The developed-land support is not yet defined. It must come from one source and rule applied identically in both cities (for example a GHSL built-up product, to be verified), must include street space adjacent to development so that dense grids are not penalized or inflated by excluding their own roads, and must be shared with any other family that adopts it. City cadastral or CMAP use layers are not interchangeable supports (see U1 findings).
- Physical opportunity is not safe or comfortable crossing; wide arterials count the same as quiet streets.
- Midblock crossings and off-street pedestrian paths are out of scope.
- Missing or incorrectly connected source streets bias counts in ways only independent labels can reveal. Overture grade information covers about 4% of road length in both buffered extracts, with hundreds of flag/level disagreements in each city. Its completeness is unverified.
