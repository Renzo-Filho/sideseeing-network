# Research methods field guide: learning from the São Paulo–Chicago project

**Audience:** an undergraduate researcher learning urban data science. **Evidence cutoff:** 22 September 2026. This guide explains the *techniques*, the decisions behind them, and the questions to ask before using them elsewhere. It describes work already done; it does not accept a new cross-city feature or fit a new model. For exact runs and results, follow the [experiment ledger](EXPERIMENT_LEDGER.md); for the source problems those experiments uncovered, see the [resource survey](DATA_RESOURCE_SURVEY.md).

## How to use this guide

Read the sections in order once, then return to a method when you inspect its script. In each section, distinguish four questions:

1. **What is the research question?** What property of a city do we hope to describe?
2. **What is actually observed?** A polygon, tax account, road line, satellite cell, schedule entry, or survey count?
3. **What operation turns observations into a number?** A join, union, allocation, classification, summary or model transform?
4. **What does the resulting number justify?** A reproducible calculation can still be a weak measure of the intended urban property.

In this project, **SP** means São Paulo and **CHI** means Chicago. A *reporting unit* is an SP district or CHI Community Area; the paired cohort has 96 and 77 units. A *family* is a conceptual group of related features: for example M6 contains several street-class shares but counts as one family in the SP similarity model. The **SP model v2** is a completed *within-city* descriptive model. The proposed common SP–CHI model has **not** been fitted: its source meanings and acceptance gates remain open. [Current status](../STATUS.md).

A useful mental model of the workflow:

```mermaid
flowchart LR
    A[Research question] --> B[Define estimand]
    B --> C[Audit source universe and labels]
    C --> D[Choose spatial support and sample]
    D --> E[Construct indicator]
    E --> F[Validate arithmetic and cases]
    F --> G[Run sensitivities]
    G --> H[Make a bounded claim]
    F -- failed or uncertain --> B
```

The arrow back to the definition is deliberate. When a pilot shows that the source does not measure the proposed quantity, revising the question or source is often more honest than polishing the algorithm.

## 1. Start with a measurement definition, not a convenient column

### Technique: define the estimand and observation unit

An **estimand** is the quantity you intend a statistic to represent. “Land-use diversity” is too vague to compute. You must choose what receives a vote: each tax entity, each square metre of classified land, each business destination, or each resident's experienced surroundings. You must also specify the categories, geographic area, date, missing-data rule and denominator.

**Project context.** SP's original U1 gives one vote to each classified cadastral entity across seven use groups. Chicago's local U1 gives area weight to CMAP primary-use polygons across eight groups. Both outputs are called land-use entropy, but they answer different questions. In a six-unit pilot, choosing six mapped classes versus four occupied classes even reversed the conditional Brás–Loop entropy order. We therefore stopped at a *measurement decision*, not a citywide calculation. [SP definitions](../sp/ATTRIBUTES.md), [Chicago definitions](../chicago/ATTRIBUTES.md), [U1 diagnosis](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md).

**Why this technique matters.** It prevents a familiar but serious error: treating similarly named columns as comparable measurements. A formal definition also tells you which missing data can be recovered. A null value inside an existing parcel is a different problem from land for which no parcel exists in the source.

**Other options.** You could define U1 as a *within-district classified-use mix*, an *all-land mix*, or *destination diversity*. Each is a legitimate research question if named accurately; none is an automatic substitute for the others. A shared grid can standardize spatial support, but it cannot make unlike source categories mean the same thing. Record the chosen estimand before looking at which version makes a favored neighborhood rank well.

**Student habit:** write one sentence before coding: “For each [unit], I measure [quantity] among [observed universe], using [numerator/categories] over [denominator], at [date], while reporting [missing mass].” If you cannot fill every bracket, the feature is still a proposal.

## 2. Discover a data source, then audit what is really in it

### Technique: source register, schema inspection and provenance manifest

We assembled registers of publisher, URL, product version, observation period, release and download dates, geography, units, field definitions, license, row counts and hashes. We then inspected actual values rather than trusting the schema. A **SHA-256 hash** identifies the exact file used in a run; it does not certify the publisher's data as accurate. A dated release is not necessarily an observation from that date.

**Project context.** The Chicago commercial API includes fields named `stories` and `gross_building_area`, but both had **zero populated records in the tested 2024 Chicago slice**. Eight publisher-linked workbook text extracts also lacked a verified stories or explicit GFA column. Seven XLSX files were later supplied locally but have not been reconciled with the extracts; T76 remains absent. The DuPage catalog's prose names `PROPCLASS`, while the inspected service uses other class fields. The Chicago local population CSV carried a 2023 label without verified estimate period or margins of error. These discoveries came from checking actual content, not merely finding a download link. [Chicago discovery](../chicago/DATA_SOURCES.md), [acquisition](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md), [workbook checkpoint](../../analysis/results/Chicago/chicago_workbooks_2026_09_19/README.md).

**How we used it.** Scripts such as [Chicago cadastral acquisition](../../analysis/scripts/acquire_chicago_cadastral.py), [assessor bulk acquisition](../../analysis/scripts/acquire_chicago_assessor_bulk.py) and [independent acquisition validation](../../analysis/scripts/validate_chicago_cadastral_acquisition.py) retained source IDs, schemas, Chicago filters, counts and manifests. [Microsoft link auditing](../../analysis/scripts/audit_microsoft_building_links.py) showed that `dataset-links.csv` was a tile index, not building features. [Microsoft download verification](../../analysis/scripts/_archive/one_time_migrations.zip) read each selected gzip stream and compared it with the decompressed copy before redundant plain files were removed.

**Other options.** If an API supports stable versioned snapshots, retrieve one instead of reconstructing a date from changing pages. If no stable snapshot exists, archive the exact response and retrieval time, then describe it as a snapshot *of your download*, not a guaranteed atomic publisher state. For a scientific replication package, preserve source hashes and enough metadata to reacquire permitted sources, while respecting reuse terms.

**Common mistake:** “The column exists” does not mean “the information exists for the population I need.” Check positive-value coverage by year, property class and location.


**A useful missing-data taxonomy.** Before filling a blank, ask which mechanism produced it:

| Example | Mechanism | Honest first response |
|---|---|---|
| SP land outside raw fiscal lot polygons | Outside the source universe in the bounded files | Investigate parcel/public-space context; do not invent a tax use. |
| SP lot with no accepted use | Existing geometry, failed or absent accepted label/join | Inspect raw records and join rules. |
| Chicago CMAP code 6000 | A mapped nonparcel/unclassifiable code | Keep its area explicit; do not treat it as a missing polygon or automatic street. |
| Microsoft building height of −1 in selected SP tiles | Source sentinel for unavailable height | Mark height missing, not a negative height or zero-floor building. |
| Overture place without taxonomy | Destination record lacking the category needed for diversity | Report category coverage by city/provider; verify a sample independently. |

This distinction is sometimes called a *missingness mechanism*. It guides the next data search: another fiscal-derived map is unlikely to independently fill land outside the fiscal universe, whereas a broken join may be repairable without new data. [Resource survey](DATA_RESOURCE_SURVEY.md).

## 3. Choose a sample that can answer the first question cheaply

### Technique: stratified, fixed-seed pilot sampling

We did not begin U1 validation by overlaying all 173 reporting units. [The summary screen](../../analysis/scripts/pilot_u1_summary_ontology.py) read only published district summaries and used fixed seed `20260922` to select Brás/Loop plus units from predeclared residential, industrial, excluded-mass, low-coverage and middle-entropy strata. The next source study narrowed to three contrasting units per city. [The source sampler](../../analysis/scripts/pilot_u1_source_samples.py) drew **20 uniform land points and 20 uniformly selected source polygons per unit**. Those are two different samples: a large polygon occupies more land points, while a tiny polygon has the same chance as a large one in the polygon draw.

**Why we used it.** A small, varied pilot exposes category and geometry problems before an expensive full-city run. The fixed seed and saved selection strata make the sample reproducible. Anchors such as Brás and Loop are chosen for the research question; the other draws prevent us from inspecting only one downtown type.

**What it can establish.** The 20 land points show *where to investigate*, not a precise district area fraction or a citywide error rate. The six units were chosen partly by their existing attributes, so they are not a probability sample of both cities. The point locations were initially matched to source codes, **not independently labeled true land use**. The later exact six-unit overlay provides area fractions for the selected source polygons and units; it still does not provide a citywide estimate. [Sample report](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/README.md).

**Other options and when to use them.**

| Design | Good for | Tradeoff |
|---|---|---|
| Simple random points over all city land | Estimating a citywide *area* prevalence if the frame and independent labels are sound | Rare but important errors may be missed; can require many reviews. |
| Stratified random points, with known selection probabilities | Comparing downtown/periphery or missingness classes and estimating weighted prevalence later | Requires a defined frame and weighting; more bookkeeping. |
| Uniform source-polygon sample | Discovering unusual code labels and small-object problems | Does not estimate land-area prevalence without area weights. |
| Purposive “hard case” fixtures | Debugging ambiguous topology, joins or mixed use quickly | Cannot yield a population error rate. |
| Full source overlay | Exact area accounting *for the supplied source* | Expensive and still not independent truth. |

For the next study, the most useful strata are SP no-lot land inside/outside mapped blocks, raw-lot/no-use, mixed parcels, Chicago `6000` and mixed use, plus POIs by provider/taxonomy status. Record how cases were chosen so a reader knows whether an accuracy estimate is warranted. [Validation protocol](README.md).

## 4. Make spatial measurements in an appropriate coordinate system

### Technique: project geometry, repair it, and define spatial support

Longitude and latitude are angles. We used metre-based projected coordinates for geometry: **EPSG:31983 for SP** and **EPSG:26916 for CHI**. GHSL was handled on its native 100 m Mollweide grid. Before calculating area or length, scripts checked CRS, repaired invalid polygons where needed, retained polygonal parts for area calculations and recorded area changes. A **spatial support** is the region over which a number is measured: gross district, land after a water mask, accepted parcel area, or valid raster-cell area.

**Project context.** SP land area is gross district area minus unioned supplied water. Chicago's early water denominator used CMAP `LANDUSE=5000`, a land-use proxy rather than a certified shoreline; later hydrography has a different vintage. The paired B1 pilot reports both land and gross denominators because the choice matters. Inter-district overlaps and touching boundaries required deterministic ownership to avoid counting a boundary object twice. [SP geographic rules](../sp/ATTRIBUTES.md), [Chicago geographic rules](../chicago/ATTRIBUTES.md), [paired execution](../harmonization/EXECUTION_LOG.md).

**A useful distinction:**

- **Clip an extensive object** when measuring how much of it lies in a district. A road crossing a boundary contributes its in-district length to each side; a footprint contributes its clipped area.
- **Assign a whole object once** when summarizing an object's identity or shape. A border block is owned by the district with greatest overlap so its shape is not turned into two artificial “blocks.”

These are different estimands. Applying the whole-object rule to footprint coverage would misallocate area; clipping blocks before shape quantiles would create false small border blocks.

**Other options.** A locally suitable equal-area projection can be preferable for regional area comparisons. Geodesic calculations on the ellipsoid are possible without one planar CRS but complicate polygon workflows. For large multi-region studies, tile-specific projections or an equal-area global grid may be necessary. Document the chosen CRS, units, boundary version and geometry repairs; do not silently change them between cities or releases.

## 5. Query and combine polygons without exhausting memory

### Technique: spatial index, bounding-box filter, exact predicate and tiled union

Spatial operations have two stages. A **bounding box** cheaply finds *possible* matches; an exact intersection or point-in-polygon predicate removes false positives. The [Chicago U1 sampler](../../analysis/scripts/pilot_u1_source_samples.py) read CMAP polygons using a district bounding box in the source CRS, reprojected them, then tested actual intersection. The [POI pilot](../../analysis/scripts/pilot_u1_poi_samples.py) used geographic Parquet pruning and bounded DuckDB memory before exact district point membership. These steps reduce data read, but the exact predicate still defines the result.

For B1, individual building polygons can overlap. If two 100 m² footprints overlap by 20 m², summing their areas gives 200 m², while their **union** occupies 180 m². We therefore intersected footprints with disjoint 2 km tiles and unioned within each tile. Because the tiles do not overlap in area, their unioned areas can be summed without counting shared roofs twice. The result is divided by district land for the primary B1 coverage. [SP B1 method](../sp/ATTRIBUTES.md), [Chicago B1 method](../chicago/ATTRIBUTES.md), [paired footprint script](../../analysis/scripts/prepare_harmonized_footprints.py).

**Why we used it.** Exact union gives the correct mapped-area numerator while tiling prevents a single enormous union operation. We separately retain “sum before union minus union area” as a duplicate/overlap diagnostic. It is *not* a probability that a building is wrong.

**Other options.** A single untiled union is conceptually simple and useful as an independent check in small pilots. Rasterization is faster at fixed resolution but introduces cell-size and boundary error. Approximate sampling can estimate area with uncertainty, but should not replace exact union when the acceptance question depends on small differences. A spatial index accelerates queries; it does not repair invalid geometry or source misclassification.

## 6. Resolve entities before joining administrative data

### Technique: entity resolution and join-cardinality checks

An **entity** is the thing being counted. A tax account, legal parcel, condominium parent, apartment, building footprint and improvement card are not necessarily one-to-one. Before a join, write its expected cardinality: one-to-one, one-to-many, many-to-one or genuinely many-to-many. Test those expectations, keep competing links visible and aggregate each quantity at its own natural unit.

**Project context.** In SP, 39,521 condominium parcel geometry rows with nonzero condominium code used lot code `0000`. Sector–block–lot would merge distinct condominiums, so the accepted key uses sector–block–condominium for those records. The correction raised located *source fiscal area* from an intermediate erroneous 61.6% to 97.3032% under the declared location rule. Even this does not prove coverage of all physical buildings. The preparation retains building–parcel intersections as *candidate links* without transferring fiscal area to every overlapping building. [SP handoff](../sp/PREPARATION.md), [fiscal preparation](../../analysis/scripts/sp_v3/fiscal.py), [entity decision brief](../DECISIONS.md).

Chicago needs another crosswalk: parcel ↔ PIN ↔ condo parent ↔ improvement/building ↔ floor/area record. A condo parent building area can repeat on unit records; summing rows would inflate area. A PIN count can multiply a physical entity. A building footprint cannot define legal parcel identity by itself. B2 also needs an eligible *reported-floor* population: a missing or top-coded story cannot be silently turned into an exact floor count.

**Other options.** Deterministic linkage uses documented IDs and rules; probabilistic record linkage can help when IDs are incomplete, but it needs hand-labeled matches and explicit false-match uncertainty. Geometry overlap can narrow candidates, not establish tax identity. If a common entity cannot be defined, redefine the research question openly rather than force a join that produces a full numeric table.

## 7. Build street networks and blocks with physical meaning

### Technique: distinguish cartographic crossings from real junctions

Two lines intersect on a flat map even when one passes over the other. A road dataset may also represent one physical junction with several short connectors, carriageways and ramps. SP's local M2 used a declared **planar crossing proxy** with a 5 m bridge/viaduct/tunnel exclusion. It is a useful local diagnostic, not proof of a routable or physically consolidated junction. The matched-source M2 pilots examined connector IDs, incident arms, level flags and close pairs in both cities. A 2.49 m Loop pair was a false distance merge because its roads were on different source levels. [SP M2](../sp/ATTRIBUTES.md), [paired junction review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md), [junction script](../../analysis/scripts/_archive/m2_junctions.zip).

**Alternative methods.** Planar intersection counting is simple but overcounts bridges. Source graph connectors reduce some false crossings but can split physical junctions. Distance clustering can consolidate nearby connectors yet merge stacked roads. A physically meaningful method needs labeled junction fixtures, grade information, arm deduplication and threshold sensitivity; no single distance radius can be chosen just because it gives a plausible total.

### Technique: polygonization, barrier tests and bidirectional reference comparison

**Polygonization** turns a closed network of lines into polygons. Those polygons may be traffic islands, divided carriageway slivers, or water enclosures instead of urban blocks. We tested all-street, no-link and grade-aware road rules, then rail centerlines, buffered rail corridors, shorelines and city-local rail envelopes on small paired pilot areas. In one Chicago case, rail centerlines increased polygons under 6 m width from **5 to 359** and worsened candidate-to-reference matching; they were rejected as direct block edges. [Block reference fixtures](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures/README.md), [barrier experiment](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md).

We compared each candidate polygon with a local reference using **intersection over union**, `IoU = area(candidate ∩ reference) / area(candidate ∪ reference)`. We counted matches in *both* directions. Candidate→reference asks “how many proposed blocks resemble some reference block?” Reference→candidate asks “how many reference blocks did we manage to represent?” A filter can improve the first number merely by deleting difficult candidates while making the second worse. The references themselves differ: Chicago Census blocks and SP municipal Quadra are not a shared definition of physical block.

**Other options.** Independently mapped rights-of-way and land-only barriers could improve boundary construction; a manually labeled sample can evaluate it. Network faces from a routable graph may work where levels and sidewalks are reliable. Morphological distance-to-street statistics avoid claiming block identity but answer a different question. Do not delete all tiny polygons before checking whether any are real urban fabric.

## 8. Combine raster cells with districts while respecting the data type

### Technique: native-grid overlay for intensive and extensive variables

The GHSL inputs are 100 m cells, not individual buildings. For each reporting geometry, we calculate the overlap area of each **native** cell. Two types of quantity require different formulas:

- **Intensive** value, such as a cell height in metres: area-weighted mean `sum(valid height_i × overlap_i) / sum(valid overlap_i)`.
- **Extensive** mass, such as cell built volume in m³: allocate `volume_i × overlap_i / full_cell_area`, then sum allocated volumes. Divide by district area only if the named result is *volume intensity*.

If a 10,000 m² cell overlaps a district by 2,500 m², a uniform-within-cell volume allocation assigns **25%** of that cell's volume. This is an assumption, not a claim to know where the volume sits within the cell. A valid zero cell is an observation; **NoData** is absence of an observation. The code records valid, missing and partial-cell area separately and withholds a volume density when positive missing support exceeds its tolerance. [Native-grid helper](../../analysis/scripts/harmonization/rasters.py), [GHSL acquisition](../../analysis/results/SP_CHI/ghsl_public_2026_09_21/README.md), [paired raster construction](../../analysis/scripts/prepare_harmonized_ghsl.py).

**Why we used it.** Reprojection/interpolation of a raster can alter values and support; native overlap keeps the publisher's cells and makes boundary allocation explicit. In the paired run, an extract mask hid a tiny North Park boundary intersection, which was recovered from the original source ZIP rather than filled with zero. The actual AGBH file header also used a NoData code different from the saved PDF description, so the per-file mask mattered. [Execution record](../harmonization/EXECUTION_LOG.md).

**Other options.** Nearest-cell extraction is faster but ignores boundary fractions. Reprojecting to a common grid can be appropriate for visual maps or aligned cell-level models, but requires a documented resampling rule; intensive and extensive quantities should not be resampled identically. A finer source raster could reduce within-cell allocation uncertainty. GHSL height and volume remain *vertical form* estimates, not reported floors or constructed floor area.

## 9. Turn source observations into interpretable district indicators

### Technique: density and denominator audits

Density is a numerator divided by an explicitly named support. SP M1 uses clipped street kilometres per **gross km²**; B1 uses unioned footprint area per **land area**; B3 uses accepted fiscal constructed m² per **land m²**. A district can have B3 greater than 1 because floor area stacks vertically. Every released ratio keeps its numerator and denominator so it can be reconstructed. [SP attribute definitions](../sp/ATTRIBUTES.md).

**Other options.** A built-up-area denominator may better describe urbanized fabric, but it introduces a new classification source and can hide parks, airports or water differently across cities. Counts per resident answer a service/exposure question, not spatial intensity. Compare alternatives as sensitivities and label them clearly.

### Technique: quantiles instead of only averages

For SP block size, we used the median and interquartile range (IQR) of **log whole-block area**; for shape, compactness and minimum-rotated-rectangle elongation; for eligible reported floors, median and P90. A median resists a few huge blocks better than a mean. IQR describes middle-range spread. P90 captures an upper tail that the median would miss. Whole objects receive equal weight, rather than letting a large block count as many blocks. [SP M3/M4/B2](../sp/ATTRIBUTES.md).

**Other options.** Means are useful when total area per object is the research target but are more sensitive to extremes. Area-weighted quantiles answer “what does a random square metre experience?” rather than “what is a typical block?” Kernel distributions or empirical CDFs retain more detail but are harder to fit in a small model. Log IQR is **not** the logarithm of raw-area IQR.

### Technique: category crosswalk and Shannon entropy

For category shares `p_c` across `K` prespecified groups, normalized Shannon entropy is

`H = −sum(p_c × ln(p_c)) / ln(K)`, using zero contribution for `p_c = 0`.

Entropy is zero when all *classified* mass belongs to one category; it reaches one for equal shares across all K groups. It does **not** say whether the categories are desirable or whether the source classified most district land. Suppose 100 hectares of land include 30 classified residential, 20 commercial and 10 industrial hectares, while 40 hectares have no accepted label. For a three-class *conditional* entropy, the shares are 30/60, 20/60 and 10/60. You must also report **classified support = 60/100 = 0.60**. Renormalizing away the other 40 hectares without showing support makes the result look more complete than it is.

**Project context.** SP count-weighted seven-class entropy and Chicago area-weighted eight-class entropy are not comparable. The [six-class pilot](../../analysis/scripts/pilot_u1_summary_ontology.py) mapped broad groups while retaining excluded mass; the [exact-area pilot](../../analysis/scripts/pilot_u1_clipped_area.py) used district land, explicitly separated overlaps, unmapped area, SP mixed use and Chicago `6000`. Brás/Loop conditional entropy changed order between six and four classes. POI `destination_diversity_12` uses **counts of mapped destinations**, so it is a differently named candidate, not repaired parcel use. [U1 source diagnosis](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md).

**Other options.** Simpson diversity emphasizes dominant categories differently; a vector of category shares avoids compressing all information to one score; Hill numbers convert entropy to an “effective number of categories.” All still require comparable classes, weighting and missingness rules. A grid can reveal within-district mixtures, but it cannot fix invalid labels. Before comparing entropy values, inspect category shares and source coverage.

### Technique: audit POI taxonomy, provider mix and duplicates

The [Overture Places sample](../../analysis/scripts/pilot_u1_poi_samples.py) used one release and exact district point membership, then grouped records into a fixed 12-category *destination* ontology. That makes the computation repeatable; it does not make each listing true. The [quality follow-up](../../analysis/scripts/pilot_u1_poi_quality.py) counted missing taxonomy, compared confidence distributions and base providers, and looked for close same-name duplicate candidates. Brás had 254/5,443 records without taxonomy hierarchy (4.7%); the Loop had 3,773/16,569 (22.8%). Meta supplied 96.6% of Brás records but 54.1% of Loop records. A same-provider restriction still left unequal fixed-category coverage. These are **diagnostics of source construction**, not measured false-positive or duplicate rates. [POI results](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md).

**Why we used it.** Entropy can change when one city has many unclassified or differently sourced records, even if the real destination mix is identical. A confidence cutoff is a sensitivity scenario, not a validated accuracy threshold across providers. Checking 20 saved listings per unit against an independent reference is the next step; the current sample has not established a POI accuracy rate.

**Other options.** A city business-license register may give stronger administrative provenance but miss unlicensed, noncommercial or closed places and may define establishments differently. Field verification or carefully reviewed imagery can validate a small stratified sample. Combining feeds may improve apparent coverage while increasing duplicate and selection problems. Whichever source you use, publish the *record universe*, category coverage, provider mix and uncertainty next to destination diversity.

## 10. Allocate population and jobs without losing mass

### Technique: fractional geographic allocation with a residual bucket

When a Census sector overlaps two districts, a simple **area-weighted allocation** gives district `d` the fraction `area(sector ∩ d) / area(sector)` of the sector's population. If a 100-person sector overlaps districts by 30% and 70%, the approximation assigns 30 and 70 people. Fractions do not mean we observed fractional residents; they keep the accounting consistent. Population outside the project boundary remains outside instead of being forced into the city. [SP U3 method](../sp/ATTRIBUTES.md), [Chicago functional construction](../../analysis/scripts/prepare_chicago_functional.py).

SP RAIS job records are grouped by CEP, but a CEP is not a workplace point or, in these inputs, an authoritative polygon. We used evidence from located jobs, fiscal business area and establishment addresses to construct **weights for candidate districts**, then allocated each unresolved CEP total proportionally where support exists. Jobs with no support remain **UNLOCATED**. The SP primary scenario leaves 508,844 of 5,387,474 source formal job links unlocated. Chicago LODES block jobs were separately allocated using business-land support and an explicit gross-area fallback; whole-block outside-city job mass remains visible. [SP allocation experiments](../../analysis/scripts/experiment_sp_allocations.py), [Chicago employment v2](../../analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/README.md).

**Why we used it.** The total source mass can be checked: allocated inside + outside + unlocated should equal the original count, within numerical tolerance. Copying every CEP's full jobs into each candidate district would multiply employment. Discarding unlocated jobs would falsely suggest complete geography.

**Other options.** Dasymetric population allocation weights only plausible inhabited land or buildings rather than uniform sector area; it needs an independently justified settlement layer. Verified workplace addresses or a consistent establishment census would improve job location. A probabilistic allocation can propagate uncertainty through many plausible maps instead of giving one point estimate. None of these automatically aligns **RAIS formal job links** with the different **LODES covered-job universe**; that is a separate source-definition question.

## 11. Convert a transit schedule into a resident-weighted service indicator

### Technique: GTFS calendar/frequency interpretation and spatial integration

GTFS supplies routes, trips, stop times, service calendars, exceptions and sometimes headway frequencies. We selected specific local date/time windows, checked service validity and derived expected stop departures. SP uses expected frequency exposure for some trips; CTA uses scheduled service. To approximate where residents experience supply, each populated sector/district intersection was split by a 250 m grid, assigned a representative point and population weight. Stops within a Euclidean **400 m** primary catchment were considered, including across district borders. At a point, the method takes the **maximum** departure count among reachable stops for each route/direction, then sums route/direction supply, avoiding repeated counting of nearby stops for the same service. Finally it computes the population-weighted mean. [SP U4 definition](../sp/ATTRIBUTES.md), [bus-only correction](../../analysis/scripts/rebuild_sp_bus_companion.py), [paired functional script](../../analysis/scripts/prepare_harmonized_functional.py).

**Project lesson.** The original SP model v2 transit calculation included metro and rail routes because it did not filter route type. The later paired companion filtered `route_type=3` and recomputed all SP scenarios; Brás weekday/400 m supply fell about **16.6%**. Arithmetic validation of the earlier value had not caught the *scope-label* error. SP/CTA schedule meanings, holiday exceptions and scenario dates still require interpretation before calling U4 fully comparable. [Paired release](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md).

**Other options.** A walking-network catchment can account for rivers, crossings and street access, but needs a validated routable pedestrian graph. Observed vehicle locations or headway reliability measure *delivered* rather than scheduled service. A destination-accessibility model adds travel time and opportunities. Each is a richer but different estimand; none should be called “the same U4” without a new definition.

## 12. Build a similarity model without letting units or column counts dominate

### Technique: transform, scale and combine feature families

SP model v2 first checks each selected input's domain. Positive skewed densities use a natural **log**; nonnegative bus supply uses `log1p` so a true zero is allowed. Other features use identity. Scalar coordinates are centered at the SP median and divided by SP IQR; if an IQR is effectively zero, the implementation can fall back to population SD. This prevents a variable measured in jobs/km² from dominating one measured as a fraction solely because of numeric units. The fitted parameters are saved, so an eventual Chicago application must use the *SP-fitted* values unchanged. [Model config](../../analysis/config/sp_urban_model_v2.json), [transforms](../../analysis/scripts/sp_model/transforms.py).

M6 street-class shares sum to one: increasing one class requires another to decrease. Treating all shares as unrelated scalar columns would double-count their dependence. The SP model uses a square-root composition representation related to **Hellinger distance**. Each family receives a weight, and its pairwise squared distance is calibrated by the median positive SP **family squared distance** across district pairs. The total distance is the square root of the weighted sum of calibrated family squared distances. This is why six M6 shares do **not** receive six independent family weights. [Distance implementation](../../analysis/scripts/sp_model/distances.py), [SP v2 report](../../analysis/results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md).

**Worked intuition.** Suppose family A has calibrated squared distance 2 between two districts and family B has 0.5, with equal family weights. The combined squared distance is `(2 + 0.5)/2 = 1.25`, and combined distance is `sqrt(1.25)`. This is a constructed similarity score, not a natural physical distance between neighborhoods. The family contributions explain its computation; they do not prove causal urban importance.

**Other options.** Standard mean/SD scaling can be useful for roughly symmetric distributions but reacts strongly to outliers. Rank distances reduce unit sensitivity while discarding magnitude. Mahalanobis accounts for covariance but can become unstable when features are numerous or highly correlated; the SP v2 report tests a regularized variant. PCA can summarize variance or change a distance if truncated; PCA loadings are **not** predictive or causal importance. A supervised model would require a credible labeled outcome, which this descriptive analogue study does not have. A different weighting scheme is a research decision to test, not an automatic software choice.

## 13. Validate code, measurements and conclusions at different levels

### Technique: a validation ladder

| Level | Example from this project | What it can establish | What it cannot establish |
|---|---|---|---|
| **Schema/identity** | Unique district IDs, expected columns, non-null domains | Files can be joined and transformed as intended | The mapped feature describes real urban conditions. |
| **Arithmetic/conservation** | Land categories sum to district land; jobs inside + outside + unlocated equal source | No mass silently disappears or multiplies | Allocation is geographically correct. |
| **Synthetic fixture** | Two overlapping squares produce the known union; bridge/level junction example | A specific implementation rule behaves as specified | Real source records satisfy the rule. |
| **Independent recomputation** | Untiled B1 union checks; source ZIP recovery; SP distance reconstruction | Another calculation path agrees on selected outputs | The shared data-generating process is unbiased. |
| **External reference review** | Annotated imagery/official case labels for buildings, uses, junctions | Evidence about empirical source accuracy in inspected cases | Citywide error rate unless sampling supports inference. |
| **Sensitivity/robustness** | Alternative U1 ontology, U2 allocation, bus radius, family weights | How conclusions change under declared plausible choices | Which choice is objectively true. |

**Project context.** SP v1 distances were numerically correct, but 15 of 23 PCA loadings were attached to the wrong feature labels. SP v2 fixed that and ran 577 sensitivity scenarios. The H1–H3 paired candidate release passed thousands of numerical checks, while M2/M3/M4 and U1 remained unaccepted for shared modeling. This distinction is a core scientific lesson: *reproducible computation* is necessary, but the research claim also needs valid source interpretation. [Historical audit](../archive/audits/SP_MODEL_VALIDATION.md), [SP corrections](../sp/MODEL.md), [paired candidate release](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md).

For reproducibility, the project keeps dated releases, source/config/code/output hashes, machine-readable checks, method dictionaries and an execution ledger. A changed definition belongs in a new version rather than overwriting a frozen artifact. [Survey experiment ledger](EXPERIMENT_LEDGER.md), [reproduction protocol](README.md).

## 14. Practice scientific claim discipline

An evidence statement, an interpretation, and a generalization are different. Strong prose says exactly where the boundary lies. The [resource survey](DATA_RESOURCE_SURVEY.md) retains these distinctions because the differences are plausible topics for a methods paper.

| Observed here | Tempting overclaim | Defensible wording |
|---|---|---|
| Selected SP Microsoft tiles contain 2,035,929 height values coded −1 | Microsoft has no SP height anywhere | The **selected three SP tiles** cannot support a paired building-height feature. |
| Overture-derived SP footprint-times-floor scenario used a one-floor fallback on 99.7% of a metropolitan bbox extract | The project's primary SP B3 is fabricated Overture GFA | That scenario is a poor observed-GFA source; the **primary SP B3 instead uses IPTU fiscal constructed area**, with its own coverage/semantic limits. |
| O'Hare's municipal class 99 includes much airfield linework that is absent from eligible Overture streets | Overture misclassified runways as ordinary local streets | The municipal and Overture **source universes differ** at O'Hare; inspect raw classes and geometry before assigning blame. |
| Brás/Loop conditional entropy order reverses under four versus six categories | One ontology is correct and the other is wrong | The comparison depends strongly on the chosen estimand; independent labels and support rules are needed to judge either. |
| Brás/Loop POI provider mixes differ sharply | All apparent destination diversity is provider bias | Provider imbalance threatens comparability; independent case checks and sensitivity tests must estimate its effect. |
| Thousands of numerical checks pass for paired candidates | The common model is ready | Calculations reconcile; source, entity and ontology gates still prohibit a fitted common model. |

When reading a report, ask: *Was this directly observed? Was it computed under an assumption? Was it checked against an independent source? Is the result from selected pilots or the full study area?* Those four questions prevent many accidental overclaims.

## 15. A learning path through the actual files

These are **reading and small-calculation exercises**, not requests to rerun expensive processing:

1. **Define a feature.** Pick U1 and fill the estimand sentence in §1 twice: once for SP entity-count use and once for Chicago polygon-area use. Identify exactly why those values are not interchangeable. Compare [both dictionaries](../sp/ATTRIBUTES.md).
2. **Trace one number.** Open [six-unit U1 coverage](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/unit_coverage.csv). For Brás, divide classified-six area by land area; compare with the report's 57.9%. Then compute no-raw-lot area / land area. Explain why these are different supports.
3. **Check a conservation rule.** In [the land-area script](../../analysis/scripts/pilot_u1_clipped_area.py), locate the category-area reconciliation and identify where overlaps and uncovered land go. Ask what would happen if category polygons were summed without union.
4. **Compare sample and census-of-source.** Read 20 Brás land-point labels from [the sample](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/sampled_land_points.csv), then the exact district-clipped area fractions. Explain why 14/20 is not the exact classified-land fraction.
5. **Follow a negative result.** Read the [rail/barrier pilot](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md). Compute how much candidate→reference and reference→candidate matches changed. Explain why a clean-looking polygon count is not sufficient.
6. **Inspect model assumptions.** Read [SP model config](../../analysis/config/sp_urban_model_v2.json) next to [the distance code](../../analysis/scripts/sp_model/distances.py). Identify which variables are logged, which are identity, and why M6 is one family. Read the [corrected model report](../../analysis/results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md) before interpreting a rank.

When writing your own paper methods section, state the observation unit, inclusion/exclusion rules, source years, formulas, missing mass, sample design, computational validation, independent validation and sensitivity choices. Report failed pilots and remaining uncertainty. The project has unusually useful *negative findings*; preserving them is part of good research, not a sign that the analysis failed.
