# Decisions and open questions

This is a dated decision record. The [Chicago](chicago/MODEL_REPORT.md) and [cross-city](harmonization/MODEL_REPORT.md) models were fitted on 6 October 2026; [STATUS.md](STATUS.md) and those reports give the current inclusion lists. Earlier statements below that fitting is paused describe their original checkpoints.

## Open discussion: recovering urban structure and function across São Paulo and Chicago

**Current sequence — 25 September 2026:** the next model is Chicago-only; the SP–Chicago common score is future work. See the [Chicago-only reassessment](STATUS.md) for current feature gates. Cross-city semantic options below remain research notes for that later stage.

**Status: ideas and measurement decisions under discussion, 25 September 2026.** M2 has one settled scope decision: **defer it from both the Chicago model and future SP–Chicago common score**. No other option on this page is an accepted model feature. The [six-family H4 proposal](harmonization/PLAN.md) is reopened as a baseline for comparison, and the [original 13-family ledger](harmonization/PLAN.md) preserves historical definitions. Bulk rebuilding and fitting remain paused; both existing contracts prohibit fitting, and the original 13-family contract is no longer the current inclusion list. The paired candidate release covers 96 São Paulo districts and 77 Chicago Community Areas, but numeric completeness does not establish comparable meaning.

**B1/BV decision — 25 September 2026:** [paired evidence](#b1-and-bv-harmonization-decision--25-september-2026) supports a common measurement method for both families across all 173 units. Retain B1 mapped footprint coverage and BV GHSL-estimated vertical form in the planned Chicago and common model scope, with one BV family budget. Independent source-accuracy and land-support gates still apply. BV does not stand for reported floors (B2) or constructed floor area (B3), whose source questions remain open. No fit is authorized by this decision.

Our immediate problem is that the six-family distance retains only M1/M6 from street morphology and omits **U1 land-use mix** and **U2 workplace activity**. These are the three largest *conceptual* losses we will discuss first. M7/B2/B3 also remain important unresolved built-form losses; [their source/entity questions](#source-and-entity-decisions-before-further-model-construction) are tracked separately. The aim is to recover each characteristic's urban meaning, either by repairing its original measure or by explicitly defining a related measure in **both** cities. A pivot changes what the feature claims to measure and must be named accordingly.

### Decision: defer M2 in both new models

**Decision on 25 September 2026:** omit M2 from the Chicago model and any future cross-city similarity distance. Do not allocate an M2 family weight, use its missing Chicago value as zero, or substitute Chicago source-connector counts for São Paulo's historical 5 m proxy. The original SP v2 score and all junction pilots remain unchanged as historical analyses. A new Chicago-only model must also omit M2 from its active feature list; the decision is not limited to the harmonized comparison.

**Reason and cost:** M2 measures junction frequency that M1 street length and M6 class shares cannot represent. But the two cities' current candidates have different meanings, and the [Chicago held-out cases](../analysis/results/Chicago/chicago_m_holdout_2026_09_25/README.md) have not validated a physical-junction algorithm beyond selected examples. The [SP v2 omission sensitivity](../analysis/results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md) gave Spearman 0.9915 and 9/10 original top-ten Brás neighbors retained, with a maximum district rank shift of 14; that is evidence about the old SP proxy, not proof that M2 is redundant or that Chicago results would be stable. Omitting M2 improves the defensibility of the new comparison but weakens claims about fine-grained street connectivity, especially if M3/M4 are also absent. The model must not claim pedestrian permeability from M1/M6 alone.

**Reopening condition:** an explicit future scope decision, a declared same-meaning junction estimand and eligible street universe, paired physical-arm/grade fixtures, and a new versioned acceptance/weight contract before fitting. This is a future option, not a current work package. A [draft pedestrian-junction convention](harmonization/M2_JUNCTION_CONVENTION.md) (30 September 2026) proposes the estimand and street universe; it is not accepted and does not reopen M2.

### Factual corrections to the initial draft

- São Paulo's **primary U1** is entropy of **cadastral-entity counts** across seven uses. It also has an **area-weighted sensitivity**. It is not primarily a built-floor-space metric. Chicago's CMAP U1 is **observed land-use polygon area** across eight groups; those are not dissolved assessor polygons. The size and direction of any bias from unregistered settlements have not been established.
- The O'Hare M1 outlier includes extensive **local municipal road class 99 airfield linework**, much of which is absent from eligible Overture roads. It is not evidence that Overture classified airport tracks as ordinary streets. For M6, `unclassified` (a known lower-order road class) and `unknown` (undetermined class) are already kept separate in the proposed common method; unequal source coverage remains the issue.
- M2 connector counts and M3/M4 buffered-road enclosures are **diagnostic candidates**. Their citywide errors relative to real physical junctions or blocks have not been quantified. Rail centerlines and arbitrary corridors were tested and rejected as complete block boundaries; a land-only shoreline and local rail envelopes remain diagnostics. No equivalent São Paulo rail right-of-way boundary has been certified.
- The eight-unit Microsoft B1 pilot differs from Overture by **−36.12 percentage points in Brás**, not a 36% relative reduction. Different area definitions in Chicago B3 risk **noncomparability**; repeated condominium parent area creates a distinct double-counting risk. The M7/B2/B3 crosswalk remains unresolved, not proven impossible.

### Decision principles

1. **Define the estimand first.** State the physical or social characteristic, observation unit, source universe, numerator, denominator, geography and date before choosing a convenient column.
2. **Use the same interpretation in both cities.** Source-specific joins are acceptable; a city-specific feature definition or an undocumented city normalization is not. If we intentionally switch to *relative within-city centrality*, name that new estimand and its city denominator before fitting the SP reference state.
3. **Keep unknown and unmatched mass visible.** Do not zero-fill missing features, silently reassign unknown land use, treat informal work as measured jobs, or imply a topological connection from a 2D crossing.
4. **Validate small, contrasting places before scaling.** Include Brás and the Loop, residential, industrial and peripheral units, and O'Hare/Marsilac where road coverage is atypical. Use independent local references as diagnostics, not as interchangeable common inputs.
5. **Precommit acceptance tests and family weights.** Check source coverage, spatial support, sensitivity to ambiguous records and added information beyond M1/M6/U3/B1. Do not choose the version that produces appealing Brás rankings. A replacement may justify one family budget; three correlated proxies do not automatically restore three lost families.

### Loss 1 — Street morphology: connectivity, grain and block form

**Characteristic to recover:** how finely the street fabric divides land. M1 reports mapped street length and M6 its class mix; neither establishes physical junctions, block size, block shape or pedestrian permeability. Junction frequency remains a conceptual loss because M2 is deferred; it is not a current model-construction target.

| Path | Proposed common measurement | Strength | Main risk and evidence needed |
|---|---|---|---|
| **Historical M2 option — deferred** | At least three incident **physical street arms** per junction on a declared eligible street universe. | Would keep the original junction-frequency concept if the scope were reopened. | Overture source connectors can split one junction; proximity can merge distinct stacked roads. Requires an explicit new decision and paired validation before any 173-unit rebuild. |
| **Repair M3/M4** | One shared ground-road/block-boundary network; whole-block size and shape on the **same** accepted polygons. | Keeps urban grain and block geometry. | Buffered carriageways create slivers; grade filtering loses reference blocks; track lines create false enclosures. Validate real rail right-of-way edges, shorelines, campuses and edge blocks against local maps. Chicago Census blocks and São Paulo Quadra remain city-specific references, not automatic common definitions. |
| **Pivot to continuous street grain** | On a defined land or built-up support, summarize distance from sampled locations to the nearest **eligible mapped street** (for example median and upper quantile). Optionally inspect length-weighted street orientation as a separate diagnostic. | Avoids claiming that road lines form true blocks or a routable graph; spatial arrangement can differ even at similar total street length. | Measures spacing/coverage, **not** junctions or physical blocks. Sensitive to unmapped roads, parks/airport land and the chosen support; may largely repeat M1. Test paired maps, reference-block associations and incremental information after M1/M6. |

**Working approach:** focus any next bounded morphology review on M3/M4 and an explicitly renamed *street-grain* fallback. Existing M2 fixture reviews remain historical evidence; do not schedule further M2 tests for the current model. Do not call a distance-to-street statistic a physical block or restore M2/M3/M4 weights merely by changing its label. The street universe must reconcile the `pedestrian` class difference identified between earlier block pilots and M1/M6.

#### New Chicago-only bounded M sample — 25 September 2026

The [four-area quartile sample and M7 source-cardinality audit](../analysis/results/Chicago/chicago_m_sample_2026_09_25/README.md) extend the earlier purposive pilots without rebuilding all 77 areas. In those four new areas, Overture and municipal M1 densities differ by at most 2.7%; this is local source-scope evidence, not class equivalence. M2 has 13 pairs within 10 m queued for physical-arm annotation. Removing `link` road segments reduces narrow block candidates in three areas, yet does not improve Census-reference recall; adding local rail right-of-way edges can restore narrow slivers. M4 compactness IQR changes substantially even where median block size remains stable. A separate 62-PIN10 Cook sample plus 10 DuPage class cases shows condominium tax-PIN counts can exceed mapped parcel features by orders of magnitude. No M2/M3/M4/M7 measure is accepted from these diagnostics; the next evidence is annotated physical junctions, blocks and parcel-parent relationships, not a full-cohort run.

The [predeclared physical-case follow-up](../analysis/results/Chicago/chicago_m_physical_cases_2026_09_25/README.md) reviewed four junction pairs and six block candidates against Cook 2025 imagery, plus seven Cook PIN10 groups against parcel geometry and Assessor fields. Three junction pairs appear to occupy one surface crossing; one interchange remains ambiguous. The one pair without a short source link still appears to be one crossing, while an earlier Loop case has near-coincident junctions on different levels. Two block candidates are plausible street-bounded land blocks; four are paved/rail/traffic-island fragments under a provisional neighborhood-block definition. Cook parcel records show both overlapping and disjoint geometries under one PIN10, and `tieback_key_pin` is a tax-proration key rather than a verified physical parent. These observations support targeted M2/M3/M4 rule design but do not promote them; original M7 needs the Clerk/Assessor parent relation or a formally renamed proxy. No 77-area processing or fit followed.

The [held-out Chicago M audit](../analysis/results/Chicago/chicago_m_holdout_2026_09_25/README.md) then froze three unused linked junction pairs, two isolated T controls, seven unused block cases and a known stacked-road control before image review. A tentative `arms(A)+arms(B)−2` count matches the three linked surface cases; the stacked case still requires raw scoped level rules. A predeclared area/width block filter falsely retained a 2,462 m² industrial-yard fragment, so simple size cleanup does not solve M3/M4. Seven Cook PIN10 cases exactly match the public 2024 polygon service by object ID, but that service exposes no `REF_PIN`, `POLYTYPE`, related tables or layer relationships. Original M7 therefore still needs the underlying parent crosswalk, while Assessor PIN10 grouping is only *typically* building-level for condos. These are case-level diagnostics, not feature acceptance or error-rate estimates.

### Loss 2 — U2: workplace intensity and economic centrality

**Characteristic to recover:** concentration of jobs or destinations, distinct from where residents sleep. RAIS 2022 counts formal job links allocated partly through uncertain CEP support; Chicago LODES WAC 2022 uses a different covered-job universe and Census block geography. São Paulo has **508,844 jobs left unlocated** in the documented primary allocation. Conservation checks alone do not establish equivalent coverage.

| Path | Proposed common measurement | Strength | Main risk and evidence needed |
|---|---|---|---|
| **Repair absolute U2** | Covered workplace-job links per gross km², with a documented common sector/worker universe or explicit bound on differing coverage. | Closest to original workplace intensity and interpretable in jobs/km². | Formal versus LODES coverage may differ by sector, employment arrangement and geography. Build a source-universe table; check sector shares, city/outside/unlocated mass and matched downtown/peripheral allocation cases. Do not equate job links with unique workers. |
| **Pivot to relative workplace centrality** | District covered-job density divided by the corresponding **citywide covered-job density**, with boundary and source population fixed in advance. | Compares whether a place is unusually job concentrated within its city; can reduce differences in overall city job counts. | It no longer measures absolute jobs/km². A biased source can still distort where jobs appear. This is intentional within-city normalization **inside the feature definition**, not permission to fit separate Chicago model scales. Test alongside absolute density and sector/source coverage. |
| **Pivot to destination/activity intensity** | Density or diversity of mapped nonresidential destinations from a verified common-source point inventory. | Could capture economic activity when job universes cannot be aligned. | Destinations are not employment; POI mapping and category bias can be severe, and the bounded Overture Places U1 sample has not validated employment or citywide mapping completeness. Treat as a new feature proposal, not U2 job counts. |

**Working approach:** audit RAIS/LODES coverage and the existing paired U2 allocations first; then compare absolute density with a predeclared relative-centrality sensitivity. A destination proxy becomes relevant only if the jobs estimand remains untenable and an independently validated common source exists.

### Loss 3 — U1: land-use and urban-function mix

**Characteristic to recover:** the coexistence of residential, commercial/service, industrial, institutional and other uses within a district. São Paulo primary U1 gives one vote to each classified cadastral entity in seven categories; Chicago CMAP measures classified polygon area in eight broad groups. Different weights and source meanings cause the current mismatch. Mixed use and unknown/unclassified support must remain explicit.

| Path | Proposed common measurement | Strength | Main risk and evidence needed |
|---|---|---|---|
| **Repair area-weighted U1** | Crosswalk both sources to one small, defensible category ontology; compute **classified land-area shares and entropy** on comparable land support in both cities. São Paulo's existing cadastral area sensitivity is a starting point. | Closest available paired land-use question without requiring Chicago entity counts. | São Paulo fiscal primary use and Chicago observed land use may still disagree; parcel area is not actual occupied use area. Align mixed, vacant, transport, agriculture/open-space and unknown rules; inspect mapped examples and classified coverage before acceptance. |
| **All-land area mix** | Add open space, agriculture and other land to a shared area ontology on the district land denominator. | Represents the whole district rather than only developed classified support. | Chicago has observed open-space codes, but the available SP parks layer is partial; CMAP `6000` nonparcel mass also needs a defensible allocation. A grid cannot supply missing observed use. |
| **Shared grid support for U1** | Assign broad source-use shares to common-sized cells, then aggregate cell area or diversity to districts using the same rule. | Makes spatial support and edge allocation explicit and can show local mixture hidden by a district total. | A grid **does not** fix category semantics or missing/mixed-use source bias. Its resolution and cell assignment are new choices requiring sensitivity tests. |
| **Pivot to destination diversity** | Diversity of mapped destinations/amenities in broad common categories, with source completeness diagnostics. | Represents the variety of accessible activities rather than legal parcel use. | Does not represent housing, vacant land, industrial area or land-use shares; POI presence may be uneven. It should be named *destination diversity*, not cadastral/observed land-use entropy. |

**Working approach:** the coarse area-weighted ontology remains the closest repair of original U1, and its support has now been computed on district-clipped land in six units; unknown/mixed/nonparcel/unmapped mass remains visible. The [12-unit summary screen](../analysis/results/SP_CHI/u1_summary_pilot_2026_09_22/README.md) identified asymmetric omitted categories. A subsequent [six-unit bounded source and POI sample](../analysis/results/SP_CHI/u1_source_samples_2026_09_22/README.md) compared all three interpretations without a citywide U1 run.

#### U1 evidence from the six-unit sample

- **Developed-use area mix:** of 20 uniform land points per unit, SP cadastral-use polygons covered 14 in Brás, 14 in Alto de Pinheiros and 16 in São Domingos. Among covered points, mixed/other or unknown labels remain. Chicago CMAP covered all 20 sampled points in each unit, but its generic `6000` code occurred at 4 Loop, 7 Albany Park and 2 Humboldt Park points. These counts flag support gaps; 20 points per unit do not estimate their precise area shares. Fiscal primary use and observed CMAP use are still distinct semantics.
- **All-land use mix:** Chicago identified four Loop points as open space. The SP parks layer identified one Alto de Pinheiros point outside cadastral use, but that layer is not a complete open-land inventory. No paired source currently supports a comparable all-land ontology; zoning cannot fill observed use.
- **Destination diversity:** matched-release Overture Places yielded 5,443 Brás and 16,569 Loop records within exact district boundaries. A fixed 12-category destination entropy was 0.538 and 0.780, respectively, but 4.8% of Brás and 23.0% of Loop records lacked one of those categories. A confidence ≥0.75 sensitivity shifted entropy to 0.597 and 0.760; its threshold is not a validated quality filter. Brás destinations were heavily shopping-coded, while the Loop was service/business-heavy. This describes mapped destinations, not housing or land-area mix. The 20-record Loop inspection flags several implausible-looking, unclassified names; independent verification remains open.

**Bounded developed-use follow-up:** [exact six-unit area accounting and two-anchor POI source audit](../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md) clarify which gaps are structural. SP has 20–25% of selected district land outside raw lot polygons after reading neighboring source partitions, plus 1–5% inside raw lots without an accepted use; Chicago has 27–33% in the mostly `6000` nonparcel/unclassifiable class. A conservative use of explicit SP fiscal predominance labels recovers 0.9–7.3 percentage points of district land from `mixed/other`, leaving 1.9–10.6 points unresolved. Brás/Loop conditional entropy **reverses order** when the ontology changes: six classes 0.706/0.735, four occupied classes 0.774/0.662. This is a definition decision, not a parameter tune. The sampled POI release has asymmetric provider mixes (Meta 96.6% of Brás versus 54.1% of Loop) and unequal category coverage; the candidate remains unweighted.

**Missingness diagnosis:** another IPTU-derived map will not fill land outside cadastral geometry. The bounded block overlay finds 7–8.5% of each selected SP district outside raw lots but inside ordinary mapped blocks, a targeted completeness lead; 12–15% lies outside mapped blocks. Public-space, ROW and land-cover layers may explain portions but do not supply primary parcel use. Some raw-lot/no-use cases and explicit mixed labels may be recoverable from existing source records. More POI feeds may improve coverage while worsening cross-city source selection, so independent reference checks and provider sensitivity come before adding a destination variable.

**Provisional judgment for discussion:** keep developed-use area mix as the primary U1 repair candidate, with independent-label checks next. Keep POI diversity as a **separately named** candidate whose value and source quality must be tested; it could complement U1 or replace its research question only by an explicit decision. Defer all-land entropy until comparable open-land and nonparcel support exists. No U1 feature is accepted and none has been given model weight.

### U1 and POI alternatives to investigate — 23 September 2026

**Discussion status only.** The fiscal map should not be our sole whole-district land-use source: the six-unit pilot found 20–25% of selected SP land outside the read raw-lot geometry, plus 1–5% inside raw lots without an accepted use. This does not establish that every absent area contains a missing taxable use. Some is plausibly public space or right-of-way; 7–8.5% of each selected district lies outside raw lots but inside mapped ordinary blocks and deserves case-level inspection. The classified fiscal area can remain a *partial* source or reference after its support is made explicit. [Exact six-unit diagnosis](../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md).

#### Candidate estimands and source roles

| Candidate | Data to obtain or inspect | What it could claim | Main acceptance problem |
|---|---|---|---|
| **Paired observed primary-use area** | Same-date OpenStreetMap (OSM) land-use polygons, mapped institutional/open-space features and both cities' public rights-of-way/land masks; retain CMAP and fiscal layers as local reference, not silently fused primary truth. | Area shares of *mapped primary use* on a common district-land support, if coverage and tags pass independent review. | OSM polygons may be incomplete and mapping intensity unequal; a common source is not automatically a common observation process. POI points cannot fill unlabeled polygon area by area allocation alone. |
| **Paired destination diversity** | OSM amenity/shop/office/craft/tourism objects plus the pinned Overture Places release; source-specific counts, categories and exact geometries. | Variety of mapped publicly observable destinations, with provider and record-density diagnostics. | Does not describe residential/industrial/vacant area. OSM nodes, ways and relations may duplicate one venue; Overture provider/taxonomy missingness differs. Keep sources separate until independent matching and truth checks. |
| **Registered activity mix** | São Paulo CNPJ establishments/CNAE and a verified Chicago Data Portal Business Licenses dataset, with dates, addresses and deduplicated establishment/location keys. | Mix of *covered registered activities*, if both legal universes can be described and compared. | CNPJ establishment and Chicago city-license eligibility are not equivalent; administrative records can have renewals, multiple licenses, headquarters addresses and missing/inaccurate geocodes. This is not land use or a POI census. |
| **Physical cover/context** | MapBiomas or comparable land-cover/built-up layers, parks/open-space and street/right-of-way geometry. | Built versus vegetated/open/water support and residual context. | Land cover is not residential versus commercial function. Use it to partition unexplained land, not to invent primary use. |

At the planning stage, the project **had tested Overture Places** but recorded **no OSM/Overpass POI test and no Chicago Citywide POI extract**; the bounded OSM test appears below. Overture's [Places guide](https://docs.overturemaps.org/guides/places/) states that its Places theme does not include OSM, making OSM a useful partially independent comparison; the providers still need lineage checks before calling any pair fully independent. The OSM [land-use](https://wiki.openstreetmap.org/wiki/Landuse) and [shop tagging](https://wiki.openstreetmap.org/wiki/Shops) schemes show why polygon use and destination tags need separate crosswalks. Public [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API) instances are suitable for a small pilot but can reject heavy queries; a pinned regional extract is the reproducible scale-up route. OSM data carry ODbL attribution/share-alike obligations. We have not verified an official Chicago Data Portal dataset with the exact title “Citywide POIs”; the portal's [current-active business licenses](https://data.cityofchicago.org/Community-Economic-Development/Business-Licenses-Current-Active/uupf-x98q) are a narrower administrative source. If “Citywide POIs” refers to another dataset, its URL/schema must be inspected before treating it as a source.

#### Next bounded evaluation, before choosing a replacement U1

1. Reuse the **same six districts** and saved SP no-lot/Chicago 6000/mixed cases. First freeze an OSM snapshot or query timestamp, tag list and category crosswalk. Extract only bounded OSM nodes, ways and relations for the six units; record unsampled/unclassified tags and topology, deduplicate a venue represented as both point and polygon, and retain source IDs. The first acquisition attempt targeted Overpass; the completed fallback used six small official OSM API map tiles after the tested public endpoints failed. Later replication may use pinned Illinois and Sudeste OSM extracts.
2. Compare **land-use polygons by area**, not by POI counts: classified, mixed, nonfunctional/open and uncovered district-land fractions in each unit. In SP, ask whether OSM supplies independent use labels specifically for no-lot land *inside ordinary blocks*; in Chicago, ask what OSM calls selected CMAP 6000 polygons. Do not infer that a point's category fills the containing block.
3. Compare **destinations by object**, not parcel area: OSM versus Overture category support, provider mix, count density, spatial/name matches and unmatched records. Manually check a fixed, stratified set of matched, OSM-only and Overture-only cases in Brás/Loop and the residential/industrial units using independent reference evidence. Preserve uncertain cases. Avoid a single confidence cutoff tuned to make the cities look alike.
4. Inspect any proposed Chicago portal POI dataset's publisher, update period, feature types, legal coverage, geometry, key and duplication rules; check whether it is a map of administrative facilities or an actual citywide venue inventory. Treat official license data as a partial positive reference, not ground truth for all POIs. Search for an SP counterpart only after choosing the registered-activity estimand.
5. Predeclare the acceptance criteria *before* a wider extraction: category validity on independent cases, mapped area/venue coverage by stratum and city, residual mass, source agreement/disagreement, rank stability across definitions and added information beyond U2/U3/B1. If no area source supports comparable coverage, keep a destination variable under its own name and leave area-use U1 unresolved rather than forcing one index to stand for both.

#### Bounded source test — 23 September 2026

The [six-tile OSM/Overture/Chicago portal pilot](../analysis/results/SP_CHI/u1_osm_tiles_2026_09_23/README.md) has now tested one 400 m tile around a saved diagnostic point in each of the six units. OSM `landuse=*` polygons cover only **2.5%, 3.6%, 6.5%** of the three selected São Paulo tiles, versus **68.2%, 99.8%, 74.7%** in the Chicago tiles. Both selected SP no-lot/inside-block center points remain unlabeled by OSM. Two Chicago `6000` center points fall under broad OSM `residential` polygons; that may overgeneralize surrounding land across a nonparcel point, so apparent fill is not a verified functional correction. These are purposive small tiles, not district coverage estimates or an accuracy rate. The official OSM map API supplied bounded XML after public Overpass probes failed; full district map requests exceeded the API's node limit.

A necessary POI filtering correction arose in the Loop tile: 159 raw OSM amenity/shop/office/craft/tourism objects shrink to **49 provisional venue candidates** after excluding street furniture, parking and ambiguous values. The equivalent candidate counts are **45, 0, 0** in SP and **49, 2, 2** in Chicago. Pinned Overture Places returns **280, 17, 50** and **1,135, 10, 11** records in those same tiles, respectively; OSM and Overture have different category universes, so these are source-presence diagnostics, not comparable entropy. Exact-name/≤30 m matches exist (7 Brás, 18 Loop, 1 Humboldt Park), but independent venue truth and deduplication remain open. The official Chicago active-license view supplies bounded administrative counts, not a general POI census; no exact “Citywide POIs” dataset title was verified in the official catalog search.

**Working implication:** OSM polygon land use is not ready to repair paired U1 area coverage. OSM destination objects may help adjudicate selected cases but cannot stand alone as a common venue inventory on this evidence. Continue with manual independent labels and alternative area-source discovery; keep Overture destination diversity as a separately named, unweighted candidate. No full-district inference, replacement U1 or model fit follows from this test.

#### Case-level independent audit — 23 September 2026

The [seven land-point and seven venue-case audit](../analysis/results/SP_CHI/u1_independent_cases_2026_09_23/README.md) now adds a small, single-reviewer reference check. A Brás no-lot point *inside an ordinary mapped Quadra* lies on visible **rail tracks**, and a São Domingos no-lot point lies on a street. Two Chicago CMAP `6000` points that OSM calls `residential` visibly lie on an **alley** and a **street edge**. Thus neither inside-block fiscal absence nor broad OSM polygon coverage can be equated with an observed parcel-use label. Other SP paved/roof-adjacent cases remain unresolved. Imagery was Cook County 2025 for Chicago and Esri World Imagery of unverified capture date for SP; the physical labels are not contemporary legal-use truth or a district-wide rate.

The venue audit intentionally separates existence, location and taxonomy. An OSM+Overture name/30 m match for Shopping Bolívia still places the paired locations **at least 384 m** from the municipal street segment containing the published address number; Shopping All Brás's OSM point is **at least 265 m** from its operator's broad address-number interval. An Overture-only care home aligns with its published address segment, while a low-confidence workshop point conflicts with registry-mirror address evidence. The Ledge exists as a Willis Tower attraction, yet Overture calls it `travel_service` with confidence 0.942; an OSM-only Do-Rite location has operator and official Chicago license support. A garbled Overture-only name remains *unverified*, not declared false. These seven purposively selected records cannot estimate source precision or recall. They show that common-source agreement, confidence and raw POI counts each miss different error modes.

**Revised U1 working position:** do not use OSM polygons to fill fiscal/CMAP residuals, and do not treat either POI inventory as a validated venue census. Preserve Overture destination diversity as an unweighted, separately named candidate. A second reviewer and a probability-sampled, source-stratified case set are needed before rates, corrections or feature acceptance. No new common fit follows.

No candidate above is accepted or weighted. The model contracts remain fit-blocked.

### Decisions to make together

| ID | Question | Current status |
|---|---|---|
| D1 | Which retained street characteristic should supplement M1/M6: **block grain/shape** or a more modest **mapped-street spacing** measure? | M2 is deferred for Chicago and cross-city scoring. M3/M4 and continuous grain remain open; neither is accepted. |
| D2 | Should U2 prioritize **absolute workplace-job intensity** or **relative workplace centrality** if the job universes cannot be fully matched? | Open. No normalization policy chosen. |
| D3 | Should U1 describe **occupied-four use**, **six-class parcel use**, **all-land mix**, or **destination diversity**? | Exact six-unit coverage shows the four/six choice reverses Brás–Loop entropy order. Developed-use remains the closest repair; POI diversity is a distinct unweighted candidate with provider bias; all-land lacks paired open-land support. Selection and acceptance remain open. |
| D4 | If replacements pass, should they extend the six-family baseline as separately weighted families, or be grouped within fewer conceptual budgets to avoid redundant weight? | Open. Decide after measurement and overlap audits, before ranking. |

The next step is to settle the **meaning** of D1–D3. For U1, district-clipped source coverage is now measured in six units. Next independently inspect the saved cases, choose the four- versus six-class estimand, and precommit paired definitions and rejection criteria. No citywide production, new fit or Brás ranking is authorized by this discussion draft.

### Evidence and definitions

- [Current model status](STATUS.md) and [reopened six-family review](harmonization/PLAN.md).
- [Original SP attribute definitions](sp/ATTRIBUTES.md), [Chicago exploratory attributes](chicago/ATTRIBUTES.md) and [13-family gate ledger](harmonization/PLAN.md).
- [M2 topology pilots](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md), [M3/M4 reference review](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures/README.md), [rail/water pilots](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md) and [M1/M6 source-coverage review](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md).

## Open question: uniform-allocation assumption and a developed-land denominator — 1 October 2026

**Status:** documentation of a known limitation and a possible redefinition. **No decision, no code change, no fit.** Measured values below were computed on 2026-10-01 from the prepared tables (`analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N07/census_sectors.parquet` with `N02/districts.parquet`; `analysis/work/prepared/Chicago/chi_functional_2026_09_16_v2/blocks.parquet` and `block_district_pieces.parquet`); no script was saved, so treat them as a reproducible spot check, not a published result.

### A. The split-block (uniform within-unit) assumption

**What it is.** When a source unit is cut by a reporting boundary, its count is divided by area. Chicago U2/U3: each positive piece receives `source count × piece area / whole block area`, with gross polygon area as support ([Chicago attributes](chicago/ATTRIBUTES.md), "U2/U3 allocation"). São Paulo U3: `P_sd = P_s × area(s ∩ d) / area(s)` ([SP attributes](sp/ATTRIBUTES.md), "U3"). Both assume residents (or jobs) are spread evenly over the whole polygon, including parks, rail yards, vacant land and water. U4's population grid reuses the same assumption inside each piece.

**Where it can matter.** Only for units not wholly inside one reporting unit. Measured (units with population):

| | Chicago (2020 blocks) | São Paulo (2022 sectors) |
|---|---:|---:|
| Median / mean / 90th-percentile unit area, km² | 0.0099 / 0.0135 / 0.0203 | 0.0226 / 0.0495 / 0.0660 |
| Largest unit, km² | 5.85 | 18.09 |
| Units straddling two or more reporting units (count; share of residents) | 3,681 blocks; 8.0% | 2,490 sectors; 9.35% |
| Units inside one reporting unit but partly outside the city (count; share of residents) | 1,400 blocks; 2.8% | 323 sectors; 1.3% |
| Residents in units not wholly inside one reporting unit | 10.8% | 10.7% |

São Paulo's sectors are about 2.3 times larger at the median and 3.7 times at the mean than Chicago's blocks, but both have a heavy tail of large peripheral units. The two unit types, years and boundary vintages differ, and the "partly outside" group has not been decomposed (it may include water, the boundary-vintage gap and true suburban edges).

**What this implies, and what it does not.** Roughly one resident in ten lives in a unit that the assumption must split. The share allocated *across a line* is smaller than the whole unit, and for a straddling unit the error is bounded by that unit's population; the 8.0% and 9.35% figures are therefore **worst-case bounds on the share of residents that could sit on the wrong side**, not error estimates. The actual within-unit unevenness, and hence the real error, has **not been measured**.

**Possible checks (proposals, not scheduled).**
1. Dasymetric refinement: split a straddling unit by mapped building footprint area on each side (the B1 footprint data) and compare district totals with area weighting.
2. Land-only weights: Chicago blocks retain `ALAND20`/`AWATER20`; compare gross-polygon support with land-only support for the straddling blocks.
3. Concentrate review where it matters: districts with the largest shares of residents in split units, and large peripheral units.
4. Report the split-unit share beside each district's U3 value rather than a single citywide figure.

### B. A developed-land denominator

**Current denominators.** M1, U2 and U3 divide by gross district area; B1 and B3 divide by land (water removed); M3/M4/B2/U1/M6 are distributions or compositions with no area denominator ([SP attributes](sp/ATTRIBUTES.md), "Denominator choice matters").

**The issue.** A gross-area density mixes two things: *how much of the unit is developed* and *how dense the development is where it exists*. For street density, M1 ≈ (developed fraction) × (density on developed land). The [M1 review](../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md) shows why this matters: O'Hare (CHI:76, M1 3.86 km/km²) is dominated by airfield and Marsilac (SP:52, 0.87 km/km², next-lowest SP unit 4.31) by rural land. Some of their low values are real sparseness, and some are map-coverage artifacts; a gross denominator cannot separate the two.

**A three-step ladder.**

| Step | Denominator | Status |
|---|---|---|
| 1 | Gross unit area | Current for M1/U2/U3 |
| 2 | Land area (water removed) | Land masks already built for B1/B3; Chicago's is a CMAP `5000` parcel-based water proxy, SP's municipal hydrography. Cheap sensitivity for M1/U2/U3 in both cities; untested |
| 3 | **Developed land** (also removes airfield, forest, farmland, large undeveloped land) | **Needs a new mask that does not exist yet.** Candidate masks to evaluate, with availability and fitness unverified: GHSL built-up/height support, a buffer on mapped building footprints, observed land use (CMAP LUI; SP zoning or cadastre), municipal land-cover layers |

**Features affected.** M1 strongly; U2 and U3 moderately; M7 if reopened. B1 and B3 already use land. M3/M4/B2/U1/M6 are unaffected.

**Risks and costs.**
1. It is a **new feature definition**, not a repair: it needs a decision, construction in both cities by the same method, and validation of the mask itself.
2. **Circularity:** a mask built from buildings makes B1 (footprint coverage) close to a tautology on that denominator, and a mask built from population would do the same for U3. The mask must come from a source independent of the numerator.
3. The mask is itself an estimate (thresholds, resolution, source date). The 100 m GHSL grid is coarse for small units.
4. It mainly changes values for edge and mixed units; fully urban units barely move, so it will not change the ranking of the core.
5. It interacts with the modifiable-areal-unit problem; the planned 250/500 m grid sensitivity ([protocol](PROTOCOL.md)) addresses the same heterogeneity from another direction.

**Not done.** No developed-land mask has been built or tested, and no denominator sensitivity has been computed for M1, U2 or U3.

**Proposed order (not scheduled).** (1) Land-area sensitivity for M1 and U3 in both cities with existing masks. (2) Evaluate candidate developed-land masks on a few contrasting units (O'Hare, Marsilac, Brás, the Loop). (3) Only then decide whether a separately named developed-area density variant is worth defining. Keep gross density as the primary until that decision; do not replace it silently.

## B1 and BV harmonization decision — 25 September 2026

### Decision

**Yes: B1 footprint coverage and BV estimated vertical form can be constructed with common definitions in São Paulo and Chicago. Retain both in the planned Chicago and SP–Chicago model scope.** This resolves the question of whether a paired measurement method exists. It does not claim that mapped footprints or GHSL height are independently verified in every neighborhood, or authorize a model fit. Complete the source-accuracy gates below before accepting their values as model inputs.

| Family | Shared primary measurement | Source and role |
|---|---|---|
| B1 | Area of the exact union of mapped building footprints clipped to district hydrographic land, divided by that land area. Report the gross-area variant. | Matched Overture building release, 2026-08-19.0, in both cities. Microsoft footprints remain a diagnostic source. |
| BV | Area-weighted mean of valid GHSL ANBH 2018 net-height grid values over district hydrographic land, retaining observed zero. This is a mean over 100 m grid support, not an individual-building mean. | Same JRC GHSL R2023A/V1-0 product in both cities. GHSL AGBH is diagnostic; 2020 total volume is a same-family alternative. |

B1 and BV each receive **one family budget** in a future contract if accepted. Height, gross height and volume must not each receive an independent full BV weight. The removed M2 weight is not transferred automatically. BV does not supply B2 reported floors or B3 constructed floor area; those remain separate unresolved source questions.

### Evidence for feasibility

- [H1–H3 paired construction](../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md) covers all 96 SP districts and 77 Chicago Community Areas. B1 has one paired value per unit; GHSL has three products on both gross and land support. Both use the same conceptual district land mask, with source geometry transformed to each calculation's CRS. Numeric land areas vary with projection: the observed B1-versus-BV relative area difference is at most 0.1542% in Chicago and 0.4903% in SP. Those area numbers should not be treated as identical across projections; the underlying support and masks, not their projected area values, must be reviewed.
- Full-run receipts report **176/176** footprint bounds/reconstruction checks and **1,211/1,211** GHSL coverage/partition checks. The independent paired-table/source-cell audit was rerun for this decision: **31 passed, 0 failed**. The minimum BV ANBH valid-area fraction is effectively 1 in both cohorts; no candidate value is missing. These are construction checks, not field accuracy tests.
- The [eight-unit Microsoft pilot](../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md) used the same B1 union/denominator formula. Microsoft minus Overture land coverage ranges from −2.28 to −0.87 percentage points across five Chicago units, but is −36.12 in Brás, −0.04 in Grajaú and +8.64 in Itaim Bibi. Microsoft is partly in Overture's lineage and cannot independently adjudicate which footprint source is complete.
- In the [H4 built-form review](../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md), Spearman B1–ANBH correlations are 0.511 in SP and 0.537 in Chicago. Height–volume correlations are 0.953 and 0.933, respectively. The first pair suggests B1 and BV carry distinguishable variation; the latter supports one BV family budget. Correlation alone does not establish satellite accuracy.

### Remaining acceptance gates and next work

1. **B1 independent source check:** in a bounded, preselected set of dense, residential, industrial and peripheral areas in both cities, compare Overture polygons against local imagery/building references. Include Brás, Loop, O'Hare and one SP peripheral area. Record omission/commission cases and whether B1 conclusions change under plausible coverage bounds. Do not use the Microsoft pilot alone as ground truth.
2. **Common land support:** document the SP and Chicago hydrographic masks, vintages and district-edge treatment. Compare land and gross variants. Preserve the distinction between projected area distortion and a genuine support mismatch.
3. **BV plausibility:** inspect selected GHSL cells against independent building-height or local reference evidence in both cities; report observed-zero/NoData area, edge-cell allocation and the 2018 epoch. The 2020 volume product is related to the 2018 height surface, so it is a sensitivity rather than independent validation. The supplied Microsoft SP tiles have no positive heights and cannot serve as the paired height reference.
4. **Precommitted model sensitivity:** once the broader feature scope is settled, compare primary B1+ANBH with no-BV, volume-only BV under the same budget, gross-support variants and no-B1. Report contribution and rank changes without selecting a variant for attractive Brás analogues.

The B1/BV method gate is **passed**: matched definitions and complete paired candidate values exist. The independent source-accuracy and land-support gates remain **open**, so the current `strict_cross_city_accepted=false` flags and `fit_authorized=false` contracts remain correct. No citywide spatial rebuild is needed to answer this feasibility question.

## Source and entity decisions before further model construction

**Decision checkpoint — 22 September 2026.** Bulk candidate rebuilding and model fitting are paused while the shared measurements are reviewed. This note is a discussion record, not a claim that any family has passed. The [current model status](STATUS.md), [13-family ledger](harmonization/PLAN.md) and [v2 contract](../analysis/config/sp_chicago_harmonization_v2_full_scope.json) govern scope: the full-scope route retains all 13 families; the [six-family proposal](harmonization/PLAN.md) is reopened for review. Neither route authorizes fitting.

### Start with the quantity we intend to measure

The target must be written before a source is selected. For each family, record: the counted object or fiscal unit; included stock; observation year; geographic assignment and denominator; duplicate and many-to-one handling; missingness; and the limits of any proxy. A column with a plausible name or matching units is insufficient. We can inspect a few representative records and maps to decide these rules; no citywide production run is needed yet.

| Family | Existing SP quantity | Chicago evidence | Unresolved decision |
|---|---|---|---|
| **M7** | One count per accepted physical cadastral entity, assigned to a district; 1,667,297 accepted SP entities. Tax accounts, apartments and footprints do not each count as a parcel. | Cook and DuPage parcel geometries and PINs; Cook parent/tieback/condo relationships. PINs can represent tax units or related records rather than one physical entity. | What is the cross-city **physical cadastral entity**? Specify when adjacent parcels merge, a condominium parent counts once, multiple buildings share one parcel, and a parcel crosses a reporting boundary. County-qualified IDs and source vintages are mandatory. |
| **B2** | One eligible, distinct positive *reported* floor count per accepted entity; district median and P90 give each eligible entity one vote. SP has 1,548,308 eligible profiles, and missing entities remain visible. | Cook residential stories are categorical, including `3 Story +` and split levels; the tested 2024 commercial slice has no populated `stories`; condominium and DuPage coverage is incomplete. Overture `num_floors` is partial and may refer to a building rather than a cadastral entity. | Can Chicago supply a floor report for a comparable entity and stock? Decide exact treatment of top-coded/split reports, multiple cards and buildings, and missingness **before** computing quantiles. Metres of height are not reported floors. |
| **B3** | Each accepted IPTU fiscal unit contributes constructed area once; total divided by district land area. Accepted SP source allocation is 581,313,100 m² from 3,842,434 accounts; this does not prove complete real-building coverage. | Residential exterior area, condo unit and repeated parent-building area, commercial building/rentable area, and limited benchmarking GFA have different definitions and coverage. DuPage parcel data do not supply floor area. | Is there a Chicago **all-stock area quantity** with a defensible relationship to SP fiscal constructed area? Define shared included space, treatment of garages/common areas, nonresidential/exempt stock, repeated parent totals and spatial assignment. Do not sum incompatible area fields to manufacture completeness. |

The key cross-family choice is the observation unit. M7 counts physical cadastral entities; B2 attaches reported floors to an eligible subset of those entities; B3 sums unique fiscal-unit areas that must be assigned without multiplying them through entity/building/condo joins. These populations are related but **not identical**. A proposed Chicago crosswalk should show explicit cardinalities (parcel ↔ PIN ↔ parent ↔ improvement/building ↔ fiscal unit) and what is unmatched at each step. It should not assume one PIN equals one parcel equals one building.

### Manual review protocol

1. **Freeze a source inventory and definitions.** For each SP and Chicago table, retain the publisher's field meaning, year, geographic coverage, unit, legal/reuse limits and missing codes. Identify the particular Cook/DuPage sources supporting each proposed quantity. Use existing files and documentation; new acquisition follows only a demonstrated gap.
2. **Inspect representative cases.** Review Loop and Brás plus peripheral, condominium, multi-building commercial, mixed-use and county-edge examples. For each, draw the actual key/geometry relationships and expected M7 count, B2 vote and B3 area contribution. Record ambiguous cases rather than forcing an answer.
3. **Write a shared rule and exclusions.** Apply the same *concept* to both cities even if source-specific joins differ. Specify how missing or conflicting reports remain missing, how repeated areas are counted once, and what stock is outside each source. Separate observed quantities from inferred proxies.
4. **Predefine acceptance evidence.** Require source-to-result count/area reconciliation, measured coverage by district and property class, duplicate/crosswalk diagnostics, spatial spot checks and a sensitivity to ambiguous cases. Choose any coverage or bias threshold with a substantive justification before seeing the final rankings. Passing arithmetic alone cannot settle semantic equivalence.
5. **Record a decision per family.** Mark a method accepted only with evidence and a named definition. If comparable data are absent, record the exact gap and the smallest source request that could close it. Any revised measurement must be built in **both** cities and explicitly agreed before it replaces the original definition. A six-family core or GHSL vertical-form sensitivity may be reported separately, but it cannot be represented as completion of the original 13-family model. Its release role is under discussion.

### Decision options and consequences

| Route | What it means | Scientific consequence |
|---|---|---|
| **Preserve original cadastral/fiscal meanings** (recommended starting point) | Resolve the crosswalk and seek missing Chicago characteristics or an equivalent documented source, particularly for B2/B3. | Best continuity with SP v2 and the 13-family goal; completion remains paused if all-stock Chicago evidence cannot be obtained. |
| **Explicitly redefine a family in both cities** | First specify the new quantity and why it still serves the urban-science question; reconstruct paired values and label the release accordingly. | Potentially feasible, but it is a changed estimand and needs a documented decision. Footprints, height and volume cannot silently become cadastral entities, reported floors or fiscal constructed area. |
| **Publish a limited exploratory comparison** | Analyze only the families whose meanings are defensible, clearly separate from the full model. | Useful interim science; it does **not** satisfy the requested 13-family Chicago model and does not authorize the rejected six-family H4 fit. |

After M7/B2/B3, the same protocol should settle U1 (entity-weighted fiscal use versus area-weighted observed use), U2 (RAIS versus LODES employment universes), and the M2–M4 physical-junction/block definitions before any full rebuild. U3/U4 timing and service qualifications, M1/M6 mapped-street coverage, and B1 footprint completeness also need explicit review, as recorded in the [ledger](harmonization/PLAN.md).

## SP method decisions: M6 classification, U2 allocation and M2 simplification

Updated 11 September 2026 after the user's response to v3 preparation. This document supplements the [current handoff](sp/PREPARATION.md) and [attribute implementation plan](archive/plans/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md). M6's broader Local rule and M2's **5 m bridge/viaduct/tunnel exclusion** are accepted and applied as separate preparation overlays. **Ten U2 allocation experiments have been executed**; area-first was subsequently selected for the completed N10 construction. No model was fitted.

### Subsequent N10 construction — completed

The user approved starting attribute construction with the recommended area-first U2 policy and an explicit unlocated bucket. N10 now provides all 13 families for 96 districts, including the approved M2/M6 rules. The [construction report](../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) records the complete methods, pilot values, full-data checks and additional issues caught during implementation. This supersedes the earlier primary-selection/no-attributes status below, which describes the experiment stage.

Newly tested construction issues include clipped versus original street length, mixed-dimensional boundary contacts, tiled footprint unions and U4 population-grid approximation. Both street issues were corrected before release, and source totals reconcile. The U4 125 m pilot refinement differs from the 250 m primary by at most 1.28% for weekday/400 m service across the three pilots. No similarity model has been fitted.

### Issue, cause, action and validation register

| Issue | Why it occurs | What we did | What the result establishes |
|---|---|---|---|
| M6 unclassified roads | Street geometry/identifiers and classification coverage do not match completely; some candidate classes conflict | Applied the user's decision to assign every remaining unclassified edge Local; retained original matches, conflict flags and imputation flags | Complete classification under the assumption, with 23.85% imputed length. One-to-one IDs and observed+imputed coverage were checked; this does not verify actual road hierarchy. |
| M2 ambiguous physical crossings | Planar lines do not encode bridge/tunnel levels; independent structure geometry is offset and can include multiple components | Compared 0/5/10/20 m exclusion scenarios; applied the user's selected 5 m rule to PONTE/VIADUTO/TUNEL | Exactly 1,060 municipal candidates excluded, leaving 106,625. Brás retains 244. This validates implementation of a proxy, not a surveyed connected graph. |
| U2 CEP spanning districts | Postal identifiers do not align with municipal district borders; an exact CEP join cannot uniquely locate all jobs | Constructed CEP-specific support and ran area, address, hybrid, equal-share, residential and mixed-use variants | Every CEP and city total is conserved. The distribution is sensitive: area versus address weighting shifts 275,226.71 job links between districts, and 11 districts differ by more than 10%. |
| U2 asymmetric geographic evidence | Cadastral and address coverage differ; the fiscal data can identify business space on only one side of a CEP | Saved support-asymmetry diagnostics and compared A/B/hybrid allocations | 889 CEPs, containing 495,877 jobs, have positive business area in one district but establishment addresses in multiple districts. Area-only concentration is not automatically ground truth. |
| U2 nongeographic/unmatched codes | Some exported CEP strings lack usable location, especially 99999999; other fiscal supports are mixed-use or have no positive eligible area | Retained explicit UNLOCATED rows in base experiments; separately distributed residual jobs with two municipality-wide priors | Base area/address variants locate 90.5551%; four fully allocated variants conserve 100% by explicit imputation. The experiment does not turn imputed locations into observations. |

### 1. M6: all remaining unclassified streets become Local

The user explicitly authorized treating unclassified roads as Local. The new rule retains every observed match and prior Local imputation, then assigns LOCAL to all 23,764 remaining unclassified records, including records previously quarantined for conflicting classes. Original evidence and conflict flags remain available. There are now 171,232 observed and 47,958 imputed source-edge records; the canonical-edge flag still excludes the nine exact geometry duplicates when measuring length.

This provides 100% classification under the selected assumption. Citywide street length remains 76.1491% observed; 23.8509% is now imputed Local. It does not become 100% observed coverage. No further road-class acquisition is required to construct the chosen primary M6 variant. The observed-only version remains useful as a sensitivity check, not a blocker.

The validated v3 run is unchanged. Apply `analysis/outputs/sp_simplification_review_2026_09_10/m6_classification_overlay.parquet` one-to-one on `edge_id` as implemented in N10 feature construction. Use its `class_model` and `class_imputed`, retaining v3 geometry, `class_observed`, conflicts and `canonical_edge`. `m6_method.json` records the decision; `m6_coverage_overlay.csv` updates preparation coverage. The old v3 readiness JSON remains historical and therefore still describes the earlier incomplete-class rule. The current rule in this document supersedes that M6 limitation.

### 2. U2: allocate jobs using geographic evidence, preserving the CEP total

#### Distinguish three problems

1. **A CEP has evidence in multiple districts.** This is an allocation problem: split its job count across the candidate districts using documented weights.
2. **A CEP has only fiscal evidence, or fiscal and address sources disagree.** This is partly a source-validation problem. Such cases can receive provisional weights, but they are not equivalent to corroborated locations.
3. **A CEP has no usable geographic support.** A within-CEP border rule cannot locate it; this requires new geolocation or an explicitly separate municipality-wide imputation model.

The current pipeline retained, rather than discarded, all 5,387,474 exported job links: 3,194,165 located and 2,193,309 unresolved. The newly inspected unmatched queue contains **351,576 jobs under `99999999`**. This string has no location in the current supports; its official coding semantics require upstream verification. It represents **6.5258% of all exported jobs**. Even if every other CEP were geolocated, retaining this code as unlocated caps directly supported geographic coverage at **93.4742%**. Filling it with an assumption must not be described as passing a 95% observed-geolocation gate.

The top ten unmatched codes contain 425,561 of 507,963 unmatched jobs. Targeted upstream/establishment review is therefore more productive than manually reviewing thousands of low-mass CEPs. The priority table is saved with the analysis evidence.

#### Common allocation formula

For CEP c with job total J_c, let S_cd be its nonnegative allocation support in district d. Allocate:

`w_cd = S_cd / sum_d(S_cd)`

`allocated_jobs_cd = J_c * w_cd`

Weights must sum to one within every allocated CEP. Fractional allocated jobs are expected; retain floating-point values until presentation. If integer counts are required, use largest-remainder rounding within each CEP to preserve its total. Zero support triggers an explicit fallback; it never produces division by zero or silent zero jobs.

The supplied data contain observed CEP addresses, not authoritative CEP polygons. Build candidate districts from those addresses and accepted cadastral evidence. Do not invent a CEP polygon from a convex hull or spread jobs across a whole district merely because one address occurs there. The support below must be associated with the **same CEP**, not total business/residential area of the entire district. For a parcel crossing a district border, a documented intersection-area split can distribute its support; do not duplicate the unit's entire area on both sides.

#### Options to compare

| Option | Support S_cd | Strength | Limitation / role |
|---|---|---|---|
| A. Nonresidential constructed area | Sum positive IPTU constructed area once per accepted fiscal unit for that CEP and district, initially commerce/services, industry/warehouse, institutional and transport/utilities | Uses vertical capacity as well as footprint; available in existing data and directly related to workplace space | Employment per m² varies by activity; tax year differs from RAIS; cadastral coverage varies. Recommended primary proxy to test, not observed establishment employment. |
| B. Establishment-address counts | Number of unique eligible CNEFE establishment addresses for that CEP/district | Simple, less dependent on cadastral floor-area completeness | Assumes equal employment per address; a small shop and large hospital count equally. Recommended first fallback and main alternative. |
| C. Business footprint area | Union of building/parcel footprint area attributable to business use and the CEP, intersected with each district | Purely geometric and understandable | Requires resolving building–parcel–CEP many-to-many links and mixed use; misses vertical differences. Useful sensitivity, with more preparation than A/B. |
| D. Residential area | Residential constructed/parcel area attributable to the CEP in each district | Supplies geographic support where the CEP occurs mainly in housing | Assumes jobs follow residential space and can pull employment away from business concentrations. Consider a low-confidence fallback or sensitivity, not the primary employment model. |
| E. Equal shares / hybrid | Equal shares across supported districts, or a declared mix of normalized A and B weights | Simple benchmark; a hybrid can reduce dominance of one evidence type | Equal shares ignore district-side size; hybrid coefficients are assumptions, not calibrated estimates. Test rather than silently choose coefficients. |

A's initial categories exclude mixed/other and vacant/residential uses. Compare inclusion of mixed-use business support as a sensitivity; do not assign the whole area of an apartment-heavy mixed parcel to employment. Preserve different fiscal units once rather than counting every building–parcel overlap as independent floor area. Do not invent sector-specific jobs-per-m² coefficients without calibration data.

This is an application of ancillary-data redistribution (dasymetric allocation). [EPA's method overview](https://www.epa.gov/enviroatlas/dasymetric-toolbox) explains redistribution using spatial ancillary evidence; it does not validate our employment weights. Employment-to-building disaggregation has been studied explicitly by [Ludick and van Heerden](https://repository.up.ac.za/items/081b2876-15ed-4ea9-a340-d8e01ce00353). The simple A/B rules proposed here are project assumptions to test, not a reproduction or validation of their optimization model.

#### What the existing inputs can support

| Current unresolved group | Job mass | Job mass in CEPs with positive nonresidential constructed-area evidence (A) |
|---|---:|---:|
| Multi-district review | 1,100,410 | 1,077,631 |
| Fiscal-only location candidate | 569,787 | 551,983 |
| Cross-source conflict | 15,149 | 15,083 |
| Unmatched | 507,963 | 0 |

For multi-district cases, 1,803 of 2,025 CEPs have positive A support. **Availability is not yet validation:** some of these CEPs have area evidence on only one side, so a weight of 100% on that side may reflect missing cadastre rather than the true job distribution. Use the union of candidate districts and flag disagreement between A and B before choosing the primary allocation.

Residential support does not solve most unmatched job mass: 1,690 unmatched CEPs have residential fiscal evidence but represent only 15,042 jobs; 1,225 have eligible dwelling-address evidence but represent only 10,981 jobs. These sets overlap, so their job totals cannot be added. The remaining mass is concentrated in large codes including `99999999`.

#### Experiment protocol and execution boundary

1. Preserve the currently corroborated/unique placements as a baseline, but review generic/large-employer codes and existing source conflicts separately.
2. Create `cep_district_support` with business unit area, establishment addresses, residential support, district provenance, nonzero-support coverage and conflict flags. No district density is needed to compare weights.
3. Calculate A and B allocations for the same multi-district CEPs. Use B when A is absent. Where A is positive on only one of several independently supported sides, compare B and a declared hybrid; do not automatically label the A result high confidence.
4. Give fiscal-only placements a provisional status. Treat cross-source conflicts as weighted scenarios plus priority review, not proof that both sources are correct. Inspect the largest job contributors first.
5. Handle `99999999` and other genuinely unlocated mass separately. Compare a municipality-wide business-area prior against a prior based on the already located job distribution. Both conserve the city total but impute geographic structure. Alternatively retain an explicit unlocated-city bucket in the primary result while publishing the fully allocated scenarios. None of these jobs is discarded.
6. Publish at least A-led and B-led district allocation scenarios, and a separately marked residual-imputation scenario. Record `observed/corroborated_job_mass`, `CEP_weighted_job_mass`, `citywide_imputed_job_mass` and `unlocated_job_mass` separately.
7. Check per-CEP and city mass conservation, unique fiscal units/addresses, support completeness, boundary cases, weights in [0,1], and no multiplication through geometry joins. Compare district allocation differences and the fraction attributable to assumptions, especially Brás and high-employment districts. Later N10/N11 should test similarity stability with and without heavily imputed U2.

Independent establishment-level job counts or verified large-employer addresses would improve validation. Existing unique-district CEPs can test geographic assignment, but they do not validate the internal employment split of a truly multi-district CEP. Sharing IPTU area between U2 weights and B3 also introduces methodological dependence; correlation cannot automatically be interpreted as independent agreement between employment and built form.

#### Executed U2 experiments and results

The executable implementation is `analysis/scripts/experiment_sp_allocations.py`. It preserves all 3,194,165 previously located job links at their v3 district assignment. Only previously unresolved CEPs vary. Unique accepted fiscal units contribute constructed area once; CNEFE support comes from the existing deduplicated establishment-address table. No Overture building-to-parcel overlap is multiplied into fiscal area.

Geography remains the v3 whole-parcel, largest-district-overlap assignment for fiscal supports and the v3 point assignment for CNEFE. This experiment **did not redo cadastral parcel/district intersections**. Thus CEP totals are conserved exactly, but fine-scale placement within a border-crossing parcel remains a stated approximation. The support table includes business, residential and mixed area and establishment-address counts, keyed uniquely by CEP/district.

Six base experiments were run:

| Saved scenario | Executed rule | Located jobs | Unlocated jobs |
|---|---|---:|---:|
| `area_first` | Business area; establishment addresses if no business area; residential area if neither workplace support exists | 4,878,630 | 508,844 |
| `address_first` | Establishment addresses; business area if no addresses; residential fallback | 4,878,630 | 508,844 |
| `hybrid` | 50/50 mix of independently normalized area/address weights when both exist; otherwise available support and residential fallback | 4,878,630 | 508,844 |
| `equal_workplace` | Equal weights among districts with positive workplace support; residential fallback where none exists | 4,878,630 | 508,844 |
| `residential_first` | Residential-area weights first, then workplace support if unavailable; stress test rather than preferred workplace model | 4,878,630 | 508,844 |
| `area_mixed` | Include positive mixed/other fiscal area with business area, then address/residential fallbacks | 4,894,553 | 492,921 |

The hybrid's 50/50 coefficient is a declared experimental value, not fitted or independently calibrated. The pure footprint option remains unexecuted because business–footprint–CEP attribution has not been resolved; treating every parcel overlap as accepted would introduce an additional unsupported allocation. It is retained as a later option, not reported as a completed experiment.

Four additional scenarios take `area_first` and `address_first`, then allocate their 508,844 residual jobs across all 96 districts using either (i) the municipality-wide distribution of accepted business constructed area or (ii) the fixed v3 located-job distribution. These are named `*_business_prior` and `*_located_jobs_prior`. Each conserves all 5,387,474 jobs and labels the residual contribution `citywide_imputed_proxy`.

The principal area/address base mass decomposition is: 3,194,165 fixed located-proxy jobs; 1,667,542 workplace-weighted jobs; 16,923 residential-fallback jobs; and 508,844 unlocated jobs. The residual is now 717 originally unmatched CEPs containing 492,921 jobs plus 25 fiscal-only CEPs containing 15,923 jobs. Including mixed area resolves those 25 fiscal-only cases, explaining the gain to 90.8506% geographic allocation. This is a coverage gain under a broader assumption, not evidence that the mixed-use variant is more accurate.

#### District sensitivity: what we discovered

The following are **experimental allocated job totals**, not density attributes or observed district employment counts. Values are rounded for readability; files retain fractional precision.

| District | Business area first | Addresses first | 50/50 hybrid | Area/address difference relative to address result |
|---|---:|---:|---:|---:|
| Brás | 45,959.91 | 43,809.35 | 44,884.63 | +4.91% |
| Itaim Bibi | 452,709.40 | 451,802.72 | 452,256.06 | +0.20% |
| Grajaú | 18,283.05 | 20,218.98 | 19,251.01 | −9.57% |
| Santo Amaro | 242,285.24 | 228,085.61 | 235,185.43 | +6.23% |
| Alto de Pinheiros | 23,302.45 | 31,643.25 | 27,472.85 | −26.36% |
| Jardim Ângela | 15,121.05 | 21,246.78 | 18,183.91 | −28.83% |

Across 1,770 CEPs with differing allocations, half the sum of absolute CEP/district differences is **275,226.71 jobs**: the amount redistributed between districts by changing area-first to address-first weights. This is neither job loss nor a measured error. Eleven districts have an absolute change exceeding 10% relative to the address-first result. Detailed per-CEP disagreement and district tables identify the drivers for review.

Residential-first gives Brás 39,569.07 jobs. The area-first result with a business-area citywide residual prior gives Brás **56,654.03**, whereas the located-job prior gives **50,135.43**. Thus residual placement changes Brás more than the base area-versus-address choice. This is a material modeling decision, not an inconsequential final fill operation.

**Recommendation after the experiment:** retain area-first as the leading provisional workplace-capacity candidate and address-first as the mandatory sensitivity comparison; neither is proven more accurate by conservation tests. Keep the citywide residual tier separate and publish its contribution. Do not silently select a fully allocated variant because it reaches 100%. Prioritize the job-heavy disagreement queue and upstream correction of `99999999` before claiming directly observed geographic completeness. A primary U2 scenario remains a methodological choice; the experiments are complete and available for that decision.

#### How the experiment was validated

All **45 integration checks passed**: three M2 identity/count checks, four checks for each of ten U2 scenarios, and an input-hash preservation check. Each allocation has unique CEP/district rows, finite weights in [0,1], per-CEP weights summing to one, and the complete original job count conserved per CEP. Fixed v3 located job mass remains unchanged in every scenario. Files used as inputs were hashed before and after processing and are unchanged.

Three synthetic tests also passed: contrasting 70/30 area versus 25/75 address weights (and their 47.5/52.5 hybrid); residential fallback with no invented allocation where all supports are zero; and invariance to area-unit scaling with exact mass conservation. These test arithmetic and fallback behavior. **No establishment-level ground-truth job counts were available**, so they do not establish geographic accuracy. No district densities, model feature matrix or similarity ranking was built.

### 3. M2: quantify the include/exclude simplification

#### Comparable geographic scope and units

The source structure table has 4,416 PONTE, 1,129 VIADUTO and 114 TUNEL line records (5,659 combined), plus 821 PASSARELA and 68 CALCADAO records. Restricting to records that intersect the municipal union gives **4,246 PONTE, 927 VIADUTO and 112 TUNEL (5,285 combined)**, plus 789 pedestrian-bridge and 68 pedestrian-mall records. These are line features, not a certified inventory of unique physical bridges/tunnels; original identifiers and components can repeat.

There are **107,685 three-or-more-source-arm intersection candidates inside municipal districts**. The earlier 107,906 figure included 221 outside/unassigned candidates. Do not compare structure records directly to intersection points as though they were the same unit. A structure may have multiple nearby intersections, or none.

The primary review below uses PONTE/VIADUTO/TUNEL. Pedestrian bridges and pedestrian malls are separate sensitivity categories, not assumed road-network grade separation. Each candidate is counted once even if several structure records are nearby. Distances are to the original line geometry, using all source structures as the proximity context, including any just outside the municipal boundary.

| Proximity threshold | Municipal candidates near bridge/viaduct/tunnel | Candidates farther away | Reduction if all nearby candidates are excluded | Brás near / all 256 candidates | Brás reduction |
|---|---:|---:|---:|---:|---:|
| Exact intersection (0 m) | 0 | 107,685 | 0% | 0 | 0% |
| 5 m | 1,060 | 106,625 | 0.984% | 12 | 4.688% |
| 10 m | 2,792 | 104,893 | 2.593% | 28 | 10.938% |
| 20 m | 4,141 | 103,544 | 3.845% | 45 | 17.578% |

At 5 m, adding all structure types increases the municipal exclusion to 1,265 points (1.175%). The zero exact intersections show that an exact point-on-structure test is ineffective on these two geometry representations; it does **not** prove absence of grade separation. The 5 m result is a tolerance-dependent scenario, not a measured error rate.

At 5 m, exclusion changes Brás from **256 to 244**, Itaim Bibi from **1,378 to 1,316 (−4.50%)**, and Grajaú from **3,625 to 3,615 (−0.28%)**. Effects are concentrated: Santa Cecília **330→274 (−16.97%)**, Bela Vista **179→149 (−16.76%)**, Sé **344→304 (−11.63%)**, República **443→395 (−10.84%)**, and Consolação **300→268 (−10.67%)**. A small citywide percentage is therefore insufficient to conclude that district comparisons are unaffected.

#### What each simplification means

**Include every planar candidate:** use a clearly named planar-intersection proxy, with at least three source arms and unique municipal assignment. Counting a grade-separated crossing as connected can inflate local intersection density. It can create false connections if reused as a routing graph. For a fixed district area, the percentage change in the count equals the percentage change in the corresponding density; no density or ranking was constructed in this review.

**Exclude every nearby candidate:** use a clearly named structure-buffer-excluded proxy. This can remove real approach/interchange junctions and other same-level crossings near the structure. It still leaves undetected grade-separated crossings farther from the supplied geometry. It is not automatically the physical truth.

The two counts are sensitivity scenarios, not statistical confidence bounds on the actual number of physical junctions. Missing crossings, positional differences, divided carriageways and duplicated nodes can affect both. The original coordinates have not been snapped/consolidated into a certified graph. All frozen v3 `accepted_m2_junction` flags remain false.

**User-selected decision, now implemented:** use the **5 m structure-buffer-excluded planar proxy** as the primary M2 definition. Retain source candidates with at least three source arms, a municipal district assignment, and no PONTE/VIADUTO/TUNEL geometry within distance ≤5 m. Exclude PASSARELA/CALCADAO from the primary structure test. This selects 106,625 candidates and excludes 1,060, a 0.98435% citywide reduction. Brás selects 244 and excludes 12. The 0/10/20 m variants remain recorded sensitivity evidence.

The new `m2_selection_overlay.parquet` preserves all original nodes and geometry, with `near_bridge_tunnel_5m`, `selected_m2_proxy` and `m2_method`. N10 uses `selected_m2_proxy`; the frozen v3 `accepted_m2_junction` field remains false because it means certified physical connectivity. Do not use the selected proxy as a validated routing graph. Implementation matches the requested threshold exactly; it does not resolve missing grade information or positional uncertainty. Final similarity effects remain N11 work.

### 4. Executed work and reproduction

Executed in this review: municipality-scoped M2 counts and 0/5/10/20 m proximity scenarios; district and pilot effects; M6's authorized classification overlay and coverage reconciliation; U2 business/residential evidence-availability checks; unmatched-job prioritization and inspection of `99999999`. The initial review did not reassign jobs. The subsequent authorized experiment now supplies ten U2 allocations and the accepted M2 5 m selection, as described above; no candidate is certified as a physical intersection.

Reproduce from the repository root:

```bash
.venv/bin/python analysis/scripts/review_sp_simplifications.py
```

Outputs are in `analysis/outputs/sp_simplification_review_2026_09_10/`: `evidence.json`, `m2_district_scenarios.csv`, `m6_classification_overlay.parquet`, `m6_coverage_overlay.csv`, `m6_method.json`, `u2_weight_evidence_availability.csv`, `u2_residential_evidence_availability.csv`, `u2_unmatched_priority.csv`, `u2_residual_summary.json`, and `reproduction.json`. The last file fingerprints this script and the frozen source checkpoints. Future construction must bind both v3 and the accepted M6 overlay in its manifest.

#### Current execution artifacts and continuation

The current experiment directory is `analysis/outputs/sp_allocation_experiments_2026_09_10/`. Key products are `m2_selection_overlay.parquet`, `m2_method.json`, `m2_district_selection.csv`, `cep_district_support.parquet`, `support_asymmetry.parquet`, ten `*_allocations.parquet` and `*_district_totals.csv` pairs, `scenario_mass_summary.csv`, `district_scenario_comparison.csv`, `district_sensitivity.csv`, `cep_allocation_disagreement.csv`, `unlocated_by_original_status.csv`, `experiment_findings.json`, `checks.json` and `manifest.json`.

```bash
.venv/bin/python analysis/scripts/experiment_sp_allocations.py
.venv/bin/python analysis/scripts/summarize_sp_experiments.py
.venv/bin/python -m unittest discover -s analysis/tests -p 'test_sp_allocations.py' -v
```

The experiment runner writes only its dedicated output directory and may deterministically regenerate those experiment files; it does not modify frozen v3. Its manifest records input hashes and the executed code hash. `analysis/config/sp_current_methods.json` binds the current base run, approved M6/M2 overlays and U2 experiment directory; U2 primary selection is now `area_first`. The N10 run manifest freezes those bindings and its selected scenario.

### 5. Other preparation issues retained in the project record

These earlier issues were addressed during v3 and remain relevant to interpretation. Their detailed source evidence and validation are in `SP_DATA_RESOLUTION_HANDOFF.md`; they were not independently rerun as part of the U2 experiment.

| Issue and cause | Action and validation | Remaining interpretation |
|---|---|---|
| Condominium parcel identity: lot 0000 is shared across separate condominiums within a block, making SQL alone ambiguous | Used sector–block–condominium keys for condominium entities; retained SQL for noncondominiums; quarantined competing/multiple-geometry links. Unique fiscal-unit count and source area were conserved. | 97.3% of source fiscal area is located, but that does not establish cadastral coverage of all physical buildings. |
| Building height/floors: Overture floor observations are extremely sparse and the one-floor GFA fallback is not measured built area | B2 uses a declared cadastral floor-count proxy; repeated reports collapse by entity, conflicts/ancillary reports are excluded. B3 uses unique fiscal-unit area without fraction reapplication. | Common-area semantics and cadastral coverage remain proxy limitations; floors are not metres. |
| District/water denominators: district overlaps and overlapping water masks can double-count area | Applied deterministic district overlap ownership; unioned water before subtraction; checked positive land and land+water=gross. | Boundary convention and supplied water coverage are documented, not independently adjudicated physical truth. |
| Building/parcel cardinality: many footprints intersect several parcels, and parcel coverage differs by district | Retained positive overlap candidates without copying tax area to each footprint; checked 3,145,436 unique municipal building IDs against an independent source scan. | Brás has 99.52% parcel-overlap candidates versus 57.75% in Grajaú; overlap is not an accepted tax match. |
| Population boundary crossings and duplicated thematic layers | Allocated unique census sectors by area, retained explicit outside residual, and did not append the duplicate vulnerability population. | Allocations are fractional proxies; allocated plus residual population conserves 11,451,999. |
| GTFS frequency templates, after-midnight times and missing exceptions | Validated keys, time ordering and headways; calculated expected stop service for fixed scenarios rather than counting templates as operated departures. | Bus-only expected service, mixed dates, Euclidean access and absent holiday exceptions remain explicit assumptions. |

The resolution standard throughout is to distinguish implemented arithmetic, user-selected assumptions and independently established facts. Passing integrity checks establishes reproducibility and conservation, not external accuracy of every proxy.
