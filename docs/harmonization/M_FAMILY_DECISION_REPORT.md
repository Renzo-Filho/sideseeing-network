# M-family decision report

Opened 30 September 2026, in the same form as the [B-family decision report](B_FAMILY_DECISION_REPORT.md). This page records the state of the street-morphology and parcel families (M1, M6, M2, M3, M4, M7), one section per family. It was assembled from the user's draft "Summary of Curio's Model" (kept outside the repository, in Downloads) and the repository documents cited below. **Only the M2 parameters in the [M2 convention](M2_JUNCTION_CONVENTION.md) were chosen by the user; every other item marked "proposed" or "open" is not a decision.** Figures marked *(summary)* come from the user's draft and were not recomputed here; figures marked *(repo)* were found in the cited document. Current status stays in [STATUS.md](../STATUS.md).

## Framework used

Same three gates as the B report: (1) **arithmetic**, (2) **source coverage and measurement**, (3) **semantic meaning and spatial support**. A complete numeric table passes only gate 1.

| Family | Gate 1 | Gate 2 | Gate 3 | Disposition |
|---|---|---|---|---|
| M1 street density | passed | open (O'Hare, Marsilac) | open (denominator proposal) | provisional |
| M6 street hierarchy | passed | open (class 4 residual, unknown/unclassified) | open | provisional |
| M2 junction density | SP proxy only | open | open | **deferred** (25 Sep); estimand convention drafted 30 Sep |
| M3 block size | candidate only | failed (artifacts, merges) | open | unaccepted; goal reframing proposed |
| M4 block shape | candidate only | failed | open | unaccepted; follows M3 |
| M7 parcel density | SP only | failed in Chicago (PIN ≠ ground lot) | failed | unaccepted; reframing proposed |

## Cross-cutting open decision: developed-land denominator (D-DEN)

The user's draft asks, for M1, B1 and M2: *divide by developed (urbanized) land instead of gross district area.* For M2 the user chose developed land on 30 September 2026. M1 and B1 are not yet decided.

- **Why it helps.** Gross area mixes street fabric with airfields, reservoirs, large parks and rural land. O'Hare (airfield) and Marsilac (rural) are already the two largest M1 source outliers *(repo: [M1/M6 review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md))*.
- **Conditions.** (1) One support, one rule, both cities, from a product outside the municipal maps (candidate: a GHSL built-up layer; resolution, epoch and threshold **not checked**). (2) Street space beside development must count as developed, or dense grids lose part of their own denominator. (3) The numerator uses the same support. (4) Decide once for all families that adopt it; mixing gross-area M1 with developed-land M2 muddles comparison.
- **Existing guidance.** The [methods guide](../survey/METHODS_FIELD_GUIDE.md) says a built-up-area denominator "introduces a new classification source and can hide parks, airports or water differently across cities" and should be compared as a labelled sensitivity.
- **B1 note.** B1 currently divides by hydrographic **land** (not gross); developed land is a third denominator. The B1 tests T1–T5 in the B report assume land support.
- **Open.** Pick the support (source, epoch, threshold, street inclusion), then decide per family: primary or sensitivity.

---

## M1 — street density, and M6 — street hierarchy

### Status

Both are plausible citywide candidates but unaccepted. `strict_cross_city_accepted=false`.

### Definition

M1 = clipped mapped eligible Overture street length per gross district km² (km/km²), ten classes (`motorway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `living_street`, `pedestrian`, `unclassified`, `unknown`), links and carriageways retained, service/alleys/driveways/paths excluded. M6 = the ten length shares of the same network, no imputation. Locked for review in [method_decisions.json](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/method_decisions.json).

### Evidence

- **Why Overture is primary.** One source and one set of rules in both cities. The municipal maps are validation references; they use different agencies, class codes and scopes.
- **Overture vs local density.** Median ratio 1.048 in Chicago and 0.936 in São Paulo (about +5% and −6%, a ratio of about 1.12 between them); rank agreement Spearman 0.961 (Chicago) and 0.976 (SP) *(repo, M1/M6 review)*. Six Chicago and seven SP units fall outside the 0.85–1.15 ratio band.
- **Source scope differs sharply.** Overture's `footway` plus `service` is 64% of Chicago segments but 18% of São Paulo's (km, all segments); the M1 class rule removes 75% of Chicago's raw Overture length and 25% of SP's *(repo: [street class inventory](../../analysis/results/SP_CHI/street_class_inventory_2026_09_30/README.md))*. After the rule, Chicago eligible Overture length is 7,164 km against the city file's 7,171 km (which includes extent, river and other non-street lines).
- **Chicago class 4 ("other streets").** The City's PDF, ArcGIS metadata and web search give no definition beyond the label *(summary)*. Empirical check *(repo: [centerline class review](../../analysis/results/Chicago/chicago_centerline_class_review_2026_09_30/README.md))*: midpoints matched to the nearest raw Overture road within 15 m, length-weighted, give residential 79.8%, service 10.4%, tertiary 5.7%, secondary 1.7%, unclassified 1.3%, no road within 15 m 0.3%. Working description: a residual class, about 80% residential-type; do not relabel it Local wholesale.
- **SP classes.** The SP imputation of Local was not forced by missing source data: `classvias` carries a class on its own geometry, and 95% of `logradouro` length lies within 5 m of a `classvias` line *(repo, street class inventory)*.
- **O'Hare** class 99 (141 km) is airfield circulation, only about 20.7% within 15 m of eligible Overture; **Marsilac** has 45.4 km of local lines with no raw Overture road within 15 m *(repo, M1/M6 review)*.

### What M1/M6 will and will not claim

M1 is mapped street length regardless of legal access; M6 is the class mix of that network, with `unknown` and `unclassified` kept separate. Neither is pedestrian accessibility.

### Open questions

1. D-DEN: developed-land versus gross area for M1 (see above).
2. Treat O'Hare and Marsilac as source-coverage exceptions, or let the developed-land support absorb them? (The O'Hare lines inside the airfield may stay inside "developed" land.)
3. Chicago class 4: keep as a separate M6 residual class, or split by an independent rule? Not decided.
4. Which street universe is frozen for Chicago-only work (Overture ten-class, or the municipal centerlines)? The [STATUS](../STATUS.md) lists this as a gate.

### Next steps

- Decide D-DEN; if developed land is chosen, pick the support and recompute M1 as a labelled variant beside the gross-area value.
- Run the O'Hare and Marsilac source-completeness sensitivity listed in the M1/M6 decision file.

---

## M2 — junction density

### Status

**Deferred** from the Chicago-only and cross-city models (25 September 2026, [DECISIONS.md](../DECISIONS.md)). Not a finding that junctions are unimportant. On 30 September 2026 the user adopted the estimand direction in a **draft [pedestrian-junction convention](M2_JUNCTION_CONVENTION.md)** (not accepted; no construction, no rebuild, no fit). Reopening still needs the four conditions in DECISIONS.md: scope decision, same-meaning estimand and street universe, paired fixtures, new versioned contract.

### Definition (draft convention)

Pedestrian junctions with at least three arms, at grade, counted once, per developed-land km². Streets: locked M1 classes minus motorway and links; no service, alleys, paths or covered/tunnel levels in the primary measure. Divided-road carriageways on one side are one arm; nodes separated only by a median or island of width ≤ W are one junction.

User selections, 30 September 2026: **W = 15 m** (sensitivities 9.1 m and 30 m); alleys excluded (sensitivity: included); mapped private streets included (sensitivity: excluded); roundabout central-island test by imagery judgement; **denominator = developed land** (source open).

### Evidence

- **Why two problems.** Overpasses are a *factual* ambiguity (is there a connection?). Divided roads are a *definitional* ambiguity (one junction or four?). Imagery and LiDAR can check a declared rule; they cannot choose it.
- **National definitions disagree.** US [MUTCD §1A.13](https://mutcd.fhwa.dot.gov/htm/2009/part1/part1a.htm): roadways 30 ft (9.1 m) or more apart give separate intersections. Brazil's [CTB Anexo I](https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm): *interseção* includes "as áreas formadas" by the crossing; I found no median-width rule. Both exclude grade-separated crossings.
- **Overture is a graph, not a flat map.** Two segments without a shared connector are not connected "even if their geometries overlap" ([Overture guide](https://docs.overturemaps.org/guides/transportation/segments-and-connectors/)). `level` is "an approximation for rendering." SP v2's planar proxy is the flat-map case; the Chicago diagnostic uses `fnode`/`tnode` plus level.
- **Grade information in the buffered Overture road files** *(computed 30 Sep 2026, whole segment files, all road classes; not clipped to the cities)*: non-zero `level_rules` on 3.73% of Chicago road length and 4.21% of SP; `is_bridge` on 2.99% and 3.91%. Bridge-flagged segments without a non-zero level: 334 (Chicago), 83 (SP); non-zero level without bridge/tunnel/covered flag: 942 and 310. Presence is similar; completeness is unverified.
- **SP v2 proxy** (5 m structure exclusion): 107,685 candidates become 106,625 (−0.98%); Brás 256→244; effect uneven by district (Santa Cecília −17%, Sé −11.6%, Grajaú −0.3%) *(repo, DECISIONS.md)*. Omitting M2 from SP v2: Spearman 0.9915, 9/10 top-ten retained, max rank shift 14 (about the old proxy only).
- **Chicago diagnostic:** 24,846 endpoint candidates (24,652 inside the city); not accepted *(repo, [Chicago attributes](../chicago/ATTRIBUTES.md))*.
- **Pilots.** Loop has 71 close pairs (≤10 m) of which only 34 have a short source link; 40 of 114 Loop short links have possible ramp/grade context; Brás has 13 of 13 linked. A 2.49 m Loop pair is two stacked junctions (levels `+1` vs `−1/−2`) *(repo, [junction review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md))*. Held-out: `arms(A)+arms(B)−2` matched 3 of 3 linked pairs, a case-level diagnostic *(repo, [held-out review](../../analysis/results/Chicago/chicago_m_holdout_2026_09_25/README.md))*.
- **State of the art** (searched 30 Sep 2026): OSMnx consolidation buffers each node by a tolerance radius and merges overlapping buffers (so `tolerance=5` merges nodes within 10 m), then rebuilds topology so stacked junctions stay apart; overcounts above 14% without it and 22% in Sydney, validated by hand against imagery ([Boeing 2025, *Transactions in GIS* 29(3) e70037](https://doi.org/10.1111/tgis.70037); [preprint](https://arxiv.org/html/2407.00258v2); radius semantics from the installed OSMnx 2.1.0 docstring); neatnet collapses dual carriageways but is planar, and its authors report topology changes at non-planar interchanges ([Fleischmann et al.](https://arxiv.org/html/2504.16198v2)); a global sprawl study merges within 20 m ([Barrington-Leigh and Millard-Ball](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0223078)); image-based road-graph extraction (RoadTracer, Sat2Graph) is benchmarked on map reconstruction, not on intersection counts.

### What M2 will and will not claim

Physical opportunity to change direction or cross at grade, from street geometry only. Not crossings, signals, ramps, safety or accessibility outcomes (kept separate by the [protocol](../PROTOCOL.md)).

### Open questions

1. **Developed-land support** (source, epoch, threshold, street inclusion) for the denominator.
2. **Does M2 add information beyond M1 and M3?** Tested on the existing proxies, 30 September 2026 ([M2 redundancy review](../../analysis/results/SP_CHI/m2_redundancy_2026_09_30/README.md)): M1 ranks explain 75% of SP and 90% of Chicago M2 rank variance (SP with M3: 82%), not an artifact of the shared gross-area denominator. M2 is the fourth-largest contributor to SP v2 distances to Brás (mean 7.5%), yet omitting it gives Spearman 0.9915, recomputed exactly. What M1 lacks is junction spacing along streets, which in SP tracks block size (ρ = −0.58). Whether the pedestrian-junction count behaves the same is unknown until it is built. Open: is this residual worth the reopening cost?
3. Whether a pedestrian-prohibition (foot access) signal exists in Overture or the Chicago centerlines: not inspected, so rule D6 may have no data behind it.
4. Chicago `f_zlev`/`t_zlev`/`tiered` semantics: dictionary saved, not yet read for this purpose.
5. Is Overture grade information complete? Only independent labels can show this.
6. Median-width data: no source identified; the operational method can only approximate W by a network merge distance.
7. Precommitted invariance threshold (draft proposal: |ln b_CHI − ln b_SP| ≤ 0.05) needs user approval before any result is seen.
8. SP LiDAR (GeoSampa 2017/2020): metadata seen only; licence, classification and size not checked.

### Next steps

1. Select the developed-land support (open item 1).
2. Run the redundancy check of M2 against M1/M3 using existing data (open item 2) and bring it back before any construction.
3. Only if (2) justifies reopening: draw the stratified two-reviewer label sample in both cities, run the §5 synthetic fixtures against OSMnx-style topological consolidation, and apply the §6 criteria of the convention.

---

## M3 — block size, and M4 — block shape

### Status

Both unaccepted. Candidate faces exist for all 77 Chicago areas; none is an accepted physical block set. M4 depends on M3's accepted blocks.

### Definition

M3 = median and IQR of log whole-block area. M4 = median and IQR of compactness `4πA/P²` and rectangle elongation, over the same blocks. A **face** (closed shape from joining street lines or subtracting street polygons from land) is geometry; a **block** is a meaning. Three failures: face artifacts (a face that is not a block), merged blocks (a street is missing), special land (real land the definition treats separately).

### Evidence: what has been tried

| Approach | Result |
|---|---|
| Street centerlines (momepy enclosures) | Faces identical to Shapely in 14 halos; edges at street middles make faces too large *(summary: 28–34% area error; figure not found in the repo)*; ramps, divided roads and rail create artifacts |
| Centerline filters (links, grade, rail, shoreline) | Removing lines deletes real blocks, adding lines creates slivers; rail centerlines took CHI:28 from 765 to 1,404 faces *(repo)* |
| Cook ROW + Road Edge, alleys reopened 3 m | 1.0–7.6% area error on selected outlines *(repo, DATA_SOURCES)*; citywide 23,204 faces, 3,756 flagged for first review, none reviewed *(repo, provisional-faces README)* |
| Single-rule filters | A 2,462 m² industrial fragment kept; a real frontage wedge would be deleted by a motorway-exposure rule *(repo, held-out review)*; freeway-island parcel coverage *(summary: 95–99%)* |
| Gap repair | Works at West Veterans Place; parcels build and then validate the corridor (circular); not a general rule |
| LiDAR | Separates a real wedge from tree-covered slivers; absent road returns do not prove absent streets |
| Aerial imagery | Human reference tracing, not extraction; at least ten traced outlines needed corrections after the freeze |

State of the art accepts error and uses heuristics: a shape/area artifact index (Fleischmann and Vybornova 2024, validated visually, false negatives unquantified), network simplification before polygonizing (neatnet 2025, seven hand-simplified cities), road-class buffers (Xu et al. 2025, *summary*, not verified here). The user's search found no block method with independent block-level precision and recall. Probability-sample map accuracy (Olofsson et al. 2014; Stehman) is a different field's standard that the block literature does not apply *(summary; abstracts only, not verified here)*.

### Proposed goal change (not decided)

From "perfect blocks" to **M3/M4 with measured error and district-level intervals**: a feature is usable if the district ranking is stable within those intervals.

### Open questions

1. Accept the reframing? It requires a probability sample of reference blocks per district stratum, with independent labellers.
2. Required sample size and the stability criterion (to be fixed before results are seen).
3. How to treat special land (airport, motorway islands, rail) under the block meaning: separate category, or excluded?
4. Is a developed-land denominator relevant here? M3/M4 are distributions, not densities (open).

### Next steps

Design the probability sample and the error-interval procedure; resolve the named-street gap and the non-block rules on unseen zones; only then build all 77 areas. Census-block size/shape remains a separately named fallback.

---

## M7 — parcel density

### Status

Chicago equivalent unaccepted. SP has an accepted count (1,667,297 entities).

### Definition

Original: accepted physical cadastral entities per gross km². Core problem *(summary)*: a tax parcel is not a lot. Chicago's PIN, a mapped polygon and a piece of ground can differ (an owner of two 25 ft lots may keep two PINs; a developer may consolidate eight into one). M7 therefore measures **the grain of the ground tax map**, which mixes original subdivision with later assembly and tax administration. SP fiscal lots share this property.

### Evidence

- Cook ground-piece work *(repo)*: `evaluate_chicago_m7_ground_pieces_2026_09_30.py` and tables in [chicago_m7_ground_pieces_2026_09_30](../../analysis/results/Chicago/chicago_m7_ground_pieces_2026_09_30/tables/). 613,802 parcel features collapse to 605,803 ground pieces under the primary rule (drop elevated layers, merge overlaps of at least 90% of the smaller feature); counts 605,847 at 0.99 and 605,774 at 0.50. Median size by type: BaseParcel 348 m², CondominiumParcel 523 m². The folder has no README; a results README is a gap.
- Correlations across 77 Community Areas *(summary; the result tables are not in the folder)*: ground pieces/km² vs M1 0.67, B1 0.50, U3 0.33, jobs −0.02; PINs/km² vs M1 0.63, B1 0.69, U3 **0.83**, jobs 0.54. M1, B1 and U3 ranks explain 56% of variance in Chicago ground-piece density and 68% in SP's count *(summary)*.
- Implication: PIN density is a hidden population proxy, so it must not stand in for M7. Ground-piece density is partly redundant with compactness.
- Earlier Chicago sample: condominium PIN counts can exceed mapped parcel features by orders of magnitude; `tieback_key_pin` is a tax-proration key, not a verified parent *(repo, [M sample](../../analysis/results/Chicago/chicago_m_sample_2026_09_25/README.md))*.

### Proposed reframing (not decided)

From "how many accepted parcels per km²?" to "how large is a typical mapped ground parcel, and how varied are parcel sizes?" (median and IQR of log parcel area, like M3).

### Open questions

1. Adopt the size-distribution reframing? It removes the PIN/population proxy problem and the density overlap, but changes the estimand in both cities and needs an SP rebuild.
2. Which collapse threshold defines a "ground piece" (0.90 is the current primary; 0.50 and 0.99 give almost the same count)?
3. SP equivalent: lots versus condominium entities; is the SP count the same object?
4. Redundancy with M3 (block size) and B1 once parcel size is the statistic.

### Next steps

Write a results README for the ground-piece folder (tables, SHA-256, the correlation table with its script); then evaluate the size-distribution variant against M3/B1 redundancy in both cities before any decision.

---

## Consolidated open questions and next steps

| # | Question | Needed from | Blocks |
|---|---|---|---|
| 1 | D-DEN: developed-land support (source, epoch, threshold, street inclusion) and which families use it as primary | user, after support selection | M1, B1, M2 |
| 2 | M2 redundancy beyond M1/M3 with existing data | analysis | M2 reopening |
| 3 | M2 invariance threshold approval | user | M2 validation |
| 4 | M3/M4 reframing to measured error with district intervals; sample design | user, then analysis | M3, M4 |
| 5 | M7 reframing to parcel-size distribution | user | M7 |
| 6 | M1 street universe for Chicago-only work, class 4 treatment, O'Hare/Marsilac sensitivity | user | M1, M6 |
| 7 | Results README for the M7 ground-piece folder | analysis | M7 evidence |

Unchecked: Chicago z-level fields, SP LiDAR files, whether Overture foot-access data exist, the summary's Xu et al. 2025 and Olofsson/Stehman citations, the 28–34% centerline area error and the 95–99% freeway-island parcel coverage.
