# São Paulo–Chicago attribute harmonization plan

## September 16 continuation: new data processed

The newly supplied Census blocks, LODES WAC, CTA GTFS and hydrography have been processed in a separate [functional extension](CHICAGO_FUNCTIONAL_EXTENSION.md), release `chi_functional_2026_09_16_v2`. It contains population/job densities for 77 Community Areas, six population-weighted bus-service scenarios (462 rows), hydrographic denominator diagnostics and explicit border residuals. **163 independent checks and 41 repository tests passed.** All strict cross-city flags remain false.

Matched Overture `2026-08-19.0` buildings for Chicago and road segments/connectors for both cities have also been acquired; paired candidate reviews are separate from the frozen releases. The older missing-data statements below describe the original v1 baseline. Current pending work concerns business-use jobs sensitivity, common morphology/entity definitions, paired SP companions and acceptance—not absence of blocks, bus schedules or workplace data.

**Status (16 September 2026): local Chicago attribute baseline completed and validated; strict cross-city acceptance and rankings remain pending.** See the current [data requirements](CHICAGO_DATA_REQUIREMENTS.md), [Chicago attribute documentation](CHICAGO_ATTRIBUTE_DOCUMENTATION.md) and [execution report](CHICAGO_EXECUTION_REPORT.md). The corrected [SP model v2](results/SP/models/sp_urban_model_v2/README.md) and [revalidation](SP_MODEL_FIXES.md) provide the reference calculations. This plan defines how to make the measurements comparable before comparing Brás with Chicago Community Areas.

The objective is comparable urban form and functional structure, not a convenient match between column names. Preserve the original SP attributes and v2 model. Any new shared measurement produces a separately versioned **harmonized SP–Chicago dataset**, including recomputed SP attributes where definitions change.

## 1. Historical inventory before the September 16 additions

A read-only inspection of `analysis/data/Chicago` on 15 September 2026 found:

| File / source | Observed condition | Role |
|---|---|---|
| `Boundaries_-_Community_Areas_20260831.geojson` | 77 records; EPSG:4326; all geometries valid; IDs in `area_numbe`/`area_num_1` | Starting reporting geography; still check ID agreement, municipal coverage, overlaps, holes and lake treatment |
| `Boundaries_-_Zoning_Districts_(current)_20260831.geojson` | 14,929 records; EPSG:4326; **118 invalid geometries**; at least one malformed date surfaced during parsing | Regulatory/context layer; repair audit if used; not observed land use |
| `chicago_acs_community_areas.csv` | 77 rows labeled `acs_year=2023`; population/demographic fields | Aggregate cross-check after verifying source vintage, period, definitions and geography joins |
| `cook_county_tracts_pop_2019.csv` | 1,319 tract rows; population and land-area fields; no geometry in this CSV | Historical auxiliary population table; not a direct Community Area or current bus-access population support |
| `morphological_data.csv` | One row: `ca=99`, **Brás (São Paulo)**, zero-valued placeholder metrics | Exclude completely from Chicago feature construction; zeros are not observed Chicago absence |
| `Socioeconomically_Disadvantaged_Areas_20260831.geojson` | 254 valid geometries | Context only; not an input to morphology similarity |
| `chicagosidewalks/` | Shapefile components present | Reserve for the later pedestrian-outcome study; do not use as street-network or morphology ground truth |

At that earlier inspection, no complete Chicago building, physical-parcel, road-network, fine-scale population/job geography or GTFS source was found in this folder. **This absence statement is now superseded by the updated data requirements: municipal buildings, centerlines and observed land use have been supplied.** Presence of aggregate population or zoning does not make U1/U3/U4 complete.

The exploratory `scripts/chi_01_fetch_boundaries.py` duplicates an already supplied boundary source, writes to a working-directory-dependent `../data/CHI/raw` location, and does not create its target directory. Do not run it as the Chicago pipeline. Replace or refactor it during acquisition to use repository-root paths, checksums, count verification and explicit failures. The existing local files should be profiled before any replacement download.

## 2. Geographic and temporal contract

### Reporting units and projections

- Use 96 SP districts and 77 Chicago Community Areas. Keys must be globally unique, e.g. `SP:10` and `CHI:10`, alongside city, local ID and name. Never join cities by a bare two-digit ID or name alone.
- Retain SP EPSG:31983. Use **NAD83 / UTM zone 16N, EPSG:26916**, in metres for Chicago calculations. Validate source CRSs rather than assuming a shapefile is WGS84; never calculate areas in longitude/latitude or Web Mercator. Store coordinate operations and units.
- Recompute geometry-based area. Do not assume `shape_area` or assessor area fields are m². For attribute fields explicitly documented as square feet, use `m² = ft² × 0.09290304`; geometric area comes from metric projected geometry.
- Use municipal support for reporting and a buffered extraction area for boundary-crossing features. At least 800 m beyond the city is required for the largest bus catchment; use a larger recorded geometry margin when constructing whole blocks or road topology.
- Union the water mask, clip it to each unit, and save gross, water and land area. Check Lake Michigan, river corridors, airport boundaries and islands explicitly. Parks remain land. Use the **same denominator convention in both cities**: preserve gross-area density formulas and land-area B1/B3 in the first compatibility comparison; publish land-denominator density sensitivities for both cities if water fractions materially affect ranks.
- Community Areas and SP districts differ in size and history. District-level rankings are the first descriptive support, not proof that scales are equivalent. Later 250/500 m matched grids must be constructed from source objects in both cities; the U4 population grid is not a morphology grid.

### Time contract

Maintain a source register with observation period, release date, extraction date, geography vintage, units, license/attribution, original URL and hash. Do not use a downloaded filename as the measurement year.

Prefer the same Overture snapshot for shared physical geometry. Freeze RAIS/LODES employment at 2022 where both definitions and availability are verified. For Chicago population, use 2020 Census blocks as the initial fine-scale count/support and disclose the gap from SP's 2022 census. Test a documented ACS-based update separately; an ACS period estimate is not a point-in-time 2023 census. Census guidance distinguishes the periods covered by [one- and five-year ACS estimates](https://www.census.gov/programs-surveys/acs/guidance/estimates.html).

For transit, select valid nonholiday local weekday/weekend scenarios in both feeds. If the matching September 2026 feeds are not archived/available, choose documented comparable local windows and mark the temporal mismatch. Do not invent historical service from a current feed. Keep 07:00–09:00 weekday and 09:00–11:00 weekend windows initially, using each city's local service calendar and timezone.

## 3. Source strategy

Use cloud/API extraction with explicit pagination and spatial filtering. Verify counts and completion; do not rely on a default 1,000-record API response or a fixed maximum feature count. Write source manifests and resumable partitions before deriving attributes.

- **Shared roads:** evaluate one frozen Overture Transportation release in both cities. Its official model uses road segments and connectors with common source classes. This offers a common representation, but does not establish equally complete mapping or independently correct connectivity. Use the [official transportation guide and schema](https://docs.overturemaps.org/guides/transportation/) to freeze the exact contract. Chicago's municipal [Transportation Centerline layer](https://gisapps.cityofchicago.org/arcgis/rest/services/ExternalApps/TransLegend/MapServer/1) is an independent source comparison, not an automatically interchangeable primary network.
- **Shared footprints:** prefer Overture Buildings using the same snapshot as SP where available; reuse SP's existing GeoPackage. The [Overture buildings guide](https://docs.overturemaps.org/guides/buildings/) is the extraction/schema reference. Chicago's [building-footprint source](https://data.cityofchicago.org/Buildings/Building-Footprints-current-/hz9b-7nh8/about) is a local completeness and geometry comparison. Its portal label “current” is not a guaranteed observation date or verified floor-count field.
- **Parcel/fiscal semantics:** investigate Cook County parcel geometry, parcel universe, residential improvement, condominium-unit and commercial records. The Assessor's [property detail guide](https://prodassets.cookcountyassessoril.gov/s3fs-public/event/2022%20Ressessments/Assessor%20Property%20Detail%20-%20Navigation%20Guide%20and%20FAQ%20%28002%29.pdf) distinguishes parcel and building record groups; the [commercial valuation catalogue](https://dev.socrata.com/foundry/datacatalog.cookcountyil.gov/csik-bsws/embed) is a candidate source. Exact schemas, vintage, units, coverage and record-level versus building-level area semantics must still be tested. Do not assume every property class is covered by one residential table.
- **Observed use:** CMAP's [Land Use Inventory](https://cmap.illinois.gov/data/land-use/land-use-inventory/) is a GIS survey with multiple categories and historical inventories. It can support an observed-use alternative, but its polygon-area mix is not automatically comparable to SP's cadastral entity-count mix. Zoning remains contextual.
- **Population geography:** obtain compatible Census population tables and [TIGER/Line geography](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html). Census statistical blocks are population supports, not automatically physical urban street blocks.
- **Workplace employment:** use LODES **WAC**, which totals jobs by workplace census block; do not use residence counts or OD flows as workplace totals. The Census [LODES examples and schema links](https://lehd.ces.census.gov/data/lehd-code-samples/sections/lodes/basic_examples.html) identify the products. Start by evaluating all-job totals against RAIS active job links; do not silently choose primary jobs, which count a different concept. Verify job-type definitions, reference timing, coverage and disclosure treatments from the release documentation.
- **Transit:** retrieve the licensed [CTA static GTFS feed](https://www.transitchicago.com/developers/gtfs/). Derive bus-only supply for the first SP-compatible operator scope; do not combine CTA rail with SP's bus-only index. Treat Pace/intermunicipal services as a separate extension requiring comparable operator-scope review in SP.

These are verified source candidates, not claims that their contents have already passed local schema or coverage validation. The original planning task did not execute acquisition or construction. The September 16 local-source implementation is tracked separately in the execution report.

## 4. Family-by-family harmonization decisions

### M1 — Street density

**Keep:** clipped geometric line length / gross reporting area, single ownership of boundary-coincident length.

**Change for the harmonized release:** choose one common road universe and representation, then recompute both cities. Proposed pilot contract: retain major through local street classes and designated pedestrian streets, preserve explicitly represented carriageways, exclude parking aisles, driveways, sidewalks, steps and nonstreet paths. Evaluate alleys/service streets separately because Chicago's alley network could dominate a mismatch in mapping conventions. Explicitly resolve unknown classes and private access; never assume missing access means public.

Use the same duplicate/self-retrace handling, line clipping, boundary ownership and inclusion rules. Compare the new SP M1 with the municipal-line baseline before accepting the shared source. Street names and identical API column names are insufficient evidence of equivalence.

### M2 — Intersection density

**Keep:** at least three incident eligible road arms per accepted counting point / gross area.

**Gate:** the current SP planar-plus-5 m exclusion proxy is not the same measurement as a Chicago routable intersection count. Preferred common-source pilot: derive the same connector/segment topology rule for both cities, count undirected physical arms once, exclude simple segmentation points, and inspect bridges, tunnels, divided roads, slip lanes and closely spaced junctions. Freeze any consolidation distance after reviewing the same fixture types in both cities.

Keep the original SP 5 m proxy as a legacy sensitivity. If topology cannot be validated comparably, either use a fully documented common planar/structure proxy in both cities or exclude M2 from the strict common model. Do not “improve” only Chicago and compare it to the old SP count.

### M3 and M4 — Physical block size and shape

**Keep:** whole-object area/log-area statistics, compactness `4πA/P²`, rectangle elongation, unweighted median/IQR.

**Gate:** Chicago census blocks, zoning polygons and SP cadastral `Quadra` are not equivalent block definitions. Preferred shared version: polygonize a common, planarized block-boundary network using identical road/ramp/alley rules, suppress duplicate carriageway artifacts and apply the same treatment of rail/water barriers. Derive physical blocks in **both** cities. The block-enclosure network is a 2D morphological construct; do not silently reuse it as a routable graph.

Audit boundary-truncated blocks, very large peripheral polygons, traffic islands, parks and industrial campuses. Keep complete objects with positive municipal intersection and deterministic largest-overlap ownership; identify extraction-edge truncation. Test the shared definition against SP Quadra and Chicago sample maps. If comparable blocks cannot be established, withhold M3/M4 from the strict model rather than using Census blocks as a convenient substitute.

### M6 — Road hierarchy composition

**Keep:** length-weighted composition and Hellinger distance, with missing/imputed mass separate.

**Change:** GeoSampa's six labels, including VTR, have no automatically proven Chicago equivalents. Propose common-source categories from the chosen transportation taxonomy, with an explicit mapping table reviewed in both cities. A candidate grouping is limited-access, major arterial, intermediate/collector, local/living street, pedestrian street, and unresolved; finalize it only after auditing source meanings. Treatment of included service roads must match M1.

Do not copy SP's “all unknown Local” assumption to Chicago without a new declared decision. A shared version can retain unknown as an explicit category and test complete-case or imputation alternatives in both cities. Unknown mass may encode mapping coverage rather than physical hierarchy: review asymmetric coverage and exclude M6 from the strict set if it dominates the comparison. This changes the SP representation and requires a new fit/calibration; do not mix new Chicago classes with the old six-vector.

### M7 — Physical cadastral parcel density

**Keep:** one accepted physical entity per location, whole-object assignment, count / gross area.

**Need:** Cook parcel polygons and a defensible parcel/condominium parent crosswalk. PINs can represent legal/tax units rather than the physical entities used by SP's corrected SQL/condominium keys. Counting every apartment PIN as a parcel would inflate density.

Build `physical_entity_id`, unit links, geometry lineage and ambiguity exclusions. Test condominium buildings, parcels with multiple structures, multi-PIN properties and public/transport parcels. Accept M7 only if both cities' entity universes are sufficiently aligned and coverage is reported. Otherwise retain it in city-specific analyses, not the strict cross-city model.

### B1 — Footprint coverage

**Keep:** exact union of clipped footprint polygons on land / land area; gross-area and overlap-excess diagnostics.

**Need:** Chicago Overture polygons at a matched release and a reviewed land mask. Use the same metric tiled-union algorithm and positive-area intersection rule. Compare both sources on dense high-rise, industrial, residential and peripheral samples. Avoid adding building parts and parent footprints twice. This is a strong candidate for the strict common model once mapped coverage and water handling pass; source uniformity alone is not proof of equal completeness.

### B2 — Reported floors

**Keep only if matched:** unweighted median/P90 of one eligible positive floor report per accepted comparable entity.

**Need:** actual stories/floor-count semantics across Cook residential, condominium and commercial records, including how basements, half-stories, split levels and ancillary units are encoded. A single-family subset cannot stand in for Chicago's whole built stock. Do not compare Chicago measured height with SP cadastral floors, convert height using an arbitrary metres-per-floor factor, or default missing floors to one.

If coverage/units cannot be aligned, exclude B2 from the strict common model. A shared building-level height/floors alternative requires new attributes in **both** cities and must not be labeled equivalent to the existing cadastral B2.

### B3 — Constructed floor-area intensity

**Keep only if matched:** accepted unique constructed-area mass / land area.

**Need:** determine whether Cook fields represent building gross area, living area, rentable area, unit area or repeated parent area. Resolve physical-building/parcel/unit joins and common-area handling before summing. Convert documented square feet to m² once. Do not sum residential living area and commercial rentable area as though both were gross floor area, nor multiply repeated condo building area by unit count.

The SP measure is a declared tax proxy, not certified surveyed GFA. A Chicago footprint-times-estimated-floors proxy is a different method; it must be separately constructed for both cities or omitted. Report coverage and unresolved mass rather than forcing B3 into the model.

### U1 — Land-use diversity

**Keep:** fixed-ontology normalized entropy, with classified mass and unknown coverage explicit.

**Preferred semantic match:** comparable observed cadastral use per physical entity and the same weighting/ontology in both cities. Construct and review a source-code crosswalk into the common categories; inspect vacant, mixed-use, parking, institutional and public land separately. Do not equate zoning permission with actual use.

CMAP area-based observed use can support an alternative only if SP gets a comparable observed-area representation. Do not compare CMAP land-area entropy to SP parcel-count entropy. If a valid shared weighting/domain cannot be built, omit U1 from the strict common model and use its profiles descriptively. This gate matters: the SP U1 area sensitivity retained only eight primary top-10 members.

### U2 — Workplace jobs

**Keep:** allocated workplace job links / gross area, with unresolved mass and uncertainty tiers.

**Need:** LODES WAC for the selected Illinois year/job universe plus the matching block geography. Deduplicate by geography/job-type/segment and use the published total field once. Include workplace blocks intersecting the city; preserve outside mass. For border blocks, choose a documented positive-area/ancillary workplace allocation and test it—do not apply population residential weights automatically to employment.

Compare coverage/reference definitions with RAIS active links, including public/federal work, multiple jobs, disclosure treatments and noncovered employment. LODES is not a direct individual-employer census with exact within-block locations. SP CEP weights and Chicago block allocation have different uncertainty structures; report those differences. Do not apply a CEP rule to Chicago block data merely to make algorithms look alike.

U2 should start in the extended functional comparison. The SP U2 variants kept the same top ten, but that does not prove RAIS–LODES measurement equivalence or eliminate the 508,844 unlocated SP jobs.

### U3 — Resident density

**Keep:** unique population mass allocated to reporting units / gross area, with outside residual preserved.

**Need:** Chicago Census block geometries and counts; compare their Community Area totals with the provided aggregate ACS data as a vintage-aware diagnostic. Area-intersection allocation must conserve source counts; do not join on imperfect Community Area names without an ID crosswalk.

A separate ACS update can use documented estimates and uncertainties, but the 2023 label must first be traced to its one-/five-year period and source. Do not discard margins of error or fabricate exact block-level current populations from Community Area totals. Record the 2020-versus-2022 census gap and test the effect of the chosen population support on U4.

### U4 — Population-weighted bus supply

**Keep:** sector/block ∩ district ∩ origin-zero 250 m grid support; proportional population; within-piece representative points; 400 m weekday primary and 800 m/weekend sensitivities; maximum reachable stop supply per route/direction followed by sum, then population-weighted mean.

**Need:** CTA static GTFS and fine-scale population. Filter bus service explicitly; validate service calendar/exceptions, after-midnight times, routes/directions, stop identities, scheduled departures and any frequency templates. Include stops outside Community Areas and city borders within the catchment. Preserve agency in keys when testing multiple feeds.

Compare city-operated bus scopes first (CTA versus the supplied SP bus operator scope), then label broader metropolitan bus/rail coverage as a separate two-city alternative. Frequency coverage, Euclidean barriers and timing differences remain limitations. Never add rail only in Chicago or interpret supply as observed ridership/access to jobs.

## 5. Comparison sets and modeling policy

Do not require all 13 families to pass by weakening definitions. Establish two explicit sets **before inspecting cross-city neighbor rankings**:

1. **Strict common set:** only families with matched entity, geometry, universe, units, weighting and temporal treatment. Candidate first targets are common-source M1/M2/M3/M4/M6, B1 and U3; none is accepted until its gates pass. U4 can join after bus/population support alignment.
2. **Extended functional/cadastral set:** add M7/B2/B3/U1/U2 only when their documented crosswalks and coverage are adequate. Otherwise present separate city-specific profiles or explicitly labeled alternatives.

Every excluded family is excluded in both cities and its weight is redistributed explicitly. Never zero-fill an unavailable Chicago attribute or silently use pair-specific available features. Publish the shared family list and reason for every exclusion. A reduced set is a new model, not a result from the original 13-family SP metric.

### Proposed primary fit: SP-anchored harmonized measurements

Recompute harmonized measurements for all 96 SP districts first. Fit transforms, scalar scales and positive-pair family calibrations to those SP harmonized values, then apply the **same saved state** to 77 Chicago rows. This asks which Chicago places resemble Brás in a common physical measurement space while retaining an interpretable SP reference. Do not refit scales for Chicago or z-score each city separately; that would change the question to within-city relative position.

Flag Chicago values outside the SP fitting range/quantiles; do not clip them to manufacture similarity. If the shared feature set changes, refit the harmonized SP reference rather than reuse the old 23-coordinate calibration unchanged.

As a sensitivity, compare a jointly fitted 173-unit model with an explicit city-balanced weighting scheme for scalar quantiles and family calibration. Save how row and pair weights are defined; do not claim equal city influence from pooling unequal sample sizes. Keep SP-anchored and pooled distances/ranks separate. PCA should be fitted on the declared reference universe; no city-specific rotations in a shared distance comparison.

Evaluate source variants, family omissions, weighting perturbations, water denominators, population vintage and district/grid support. Inspect domain shift and city separation, not just nearest-neighbor rank. No supervised accuracy or causal interpretation is available without independent labels/outcomes.

## 6. Execution sequence and deliverables

| Task | Work | Required output / gate |
|---|---|---|
| CHI-H01 — Freeze local inventory | Hash existing files; validate schemas, IDs, periods, placeholder exclusions | Source register, 77-ID crosswalk, explicit missing-input list; no duplicate boundary download |
| CHI-H02 — Establish geography | Metric CRS, boundary union, water mask, buffered extraction support | Gross/land/water conservation; overlap/gap/repair log; lake/airport review |
| CHI-H03 — Acquire shared physical sources | Frozen common roads/connectors and footprints for Chicago and required SP companion measures | Complete paginated/cloud extraction; source hashes, IDs, schema and attribution |
| CHI-H04 — Pilot shared geometry methods | Road universe/topology, physical blocks, class mapping and footprint unions | Synthetic bridge/loop/dual-carriageway/alley/water fixtures; reviewed maps in both cities |
| CHI-H05 — Resolve cadastral semantics | Cook parcel/unit/parent keys, stories and area scopes; SP crosswalk comparison | Entity and area conservation, ambiguity queues; accept or exclude each M7/B2/B3 family |
| CHI-H06 — Prepare use, jobs and population | Observed-use ontology; LODES WAC; Census supports and ACS metadata | Crosswalks, valid geographic joins, conserved source totals, unknown/unlocated mass |
| CHI-H07 — Prepare bus service | CTA mode/calendar/time validation, comparable operator scope and support points | Six scenario windows/radii, population conservation and no route-stop double counting |
| CHI-H08 — Freeze harmonization contract | Family inclusion, units, source universes, denominators, support and fit policy | Machine-readable attribute crosswalk; approve the common set before ranking |
| CHI-H09 — Construct paired attributes | Process both cities under the accepted common methods | City-keyed long/wide matrices, coverage metadata, dictionaries and validation |
| CHI-H10 — Fit and compare | SP-anchored reference, pooled sensitivity, explanations and source/weight tests | Chicago-to-Brás rankings with contribution and uncertainty profiles; no outcome leakage |
| CHI-H11 — Spatial robustness and release | 250/500 m matched grids if required for cross-scale claims; inspect candidates | Versioned report, tests, manifests, handoff and explicit deferred claims |

Pilot geography: use supplied Chicago IDs for Loop, Near West Side, West Town, South Lawndale and O'Hare after validating name-to-ID mapping. Together they provide dense, industrial/mixed, residential and edge/airport cases. They are processing fixtures, **not prespecified Brás analogues**. Retain Brás, Itaim Bibi and Grajaú as SP contrast cases; do not select pilots based on resulting similarity.

## 7. File organization and reproducibility

Use `analysis/data/Chicago` as the canonical Chicago source root; do not introduce parallel `CHI`, `Chicago data` or working-directory-dependent trees. Proposed new paths:

```text
analysis/config/sp_chicago_harmonization_v1.json
analysis/scripts/harmonization/          # shared entity, geometry and measurement functions
analysis/scripts/prepare_chicago.py
analysis/tests/test_harmonization.py
analysis/work/prepared/Chicago/<run>/
analysis/work/runs/sp_chicago_harmonization_v1/
analysis/results/Chicago/<release>/     # tables, spatial, reports, validation
analysis/results/SP_CHI/<model>/        # common-feature comparison and sensitivity
```

Keep acquisition/preparation intermediates local under existing ignore rules. Publish compact aggregate results, source metadata and code. Do not modify the frozen SP v2 model or overwrite Chicago source data. Store country/city-qualified IDs, effective periods, source field mappings, entity counts, area/job/population numerators, denominators, source/allocated coverage and uncertainty flags in the long table.

The current model loader correctly enforces the SP-only 96-ID contract. A cross-city loader must be a separate implementation with declared city-specific ID universes and common-feature schemas, not a weakened SP validator. Reuse the now-tested transform/apply, composition, weighting and distance mathematics once the cross-city data contract passes.

## 8. Acceptance and limits

Require exact identities and no row multiplication; valid metric geometry; mapped source completeness checks; conserved population/jobs/areas with explicit outside or unresolved buckets; common floor/use/parcel semantics; deterministic joins; transformed finite values; identical model state for both cities; and independently reconstructed distances/contributions. Tests must include square-foot conversion, duplicated condominium units, false planar overpasses, border blocks, zero support, multiple nearby same-route stops and mutually exclusive city IDs.

Coverage percentages describe their specific source universe. Do not replace unknown physical completeness with a generic 95% threshold or hide unmatched mass in zero-valued features. Publish exclusions and differences before the cross-city ranking.

**Current next steps:** close the common-source, topology, employment, fine-population, bus and cadastral gates listed in [CHICAGO_DATA_REQUIREMENTS.md](CHICAGO_DATA_REQUIREMENTS.md). Local values are descriptive/provisional, not yet paired harmonized features. Cross-city fitting remains deferred until common definitions and the SP companion reconstruction pass.
