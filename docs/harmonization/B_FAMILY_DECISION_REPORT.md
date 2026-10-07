# B-family decision report

Opened 30 September 2026. This page records decisions about the built-form families (B1, BV, B2, B3), one section per family, added as each is decided. Checks marked "not run" have not been run; the B2 source search was run on 30 September 2026 and its commands are cited in that section. Current project status stays in [STATUS.md](../STATUS.md); the earlier B1/BV feasibility decision is in [DECISIONS.md](../DECISIONS.md). Figures below are taken from those documents and the cited result READMEs; they were not recomputed for this report.

## Framework used

Every family is judged at three gates: (1) **arithmetic**: the code computes what it says; (2) **source coverage and measurement**: the source contains the real-world objects; (3) **semantic meaning and spatial support**: the number means the same thing in both cities and the denominator is sound. A complete numeric table passes only gate 1.

| Family | Gate 1 | Gate 2 | Gate 3 | Section |
|---|---|---|---|---|
| B1 | passed | open | open | below |
| BV | passed | open (partly probed, see below) | open | evaluation recorded, decision pending |
| B2 | Chicago subset only | failed | failed | **out of scope** (30 September 2026), below |
| B3 | SP only | failed | failed | **refused** (30 September 2026); alternative `BI` proposed, below |

---

## B1 — footprint coverage

### Decision (30 September 2026)

1. **Retain B1** in the planned Chicago and common model scope, as already decided on 25 September. The family is **provisional**: `strict_cross_city_accepted` and `fit_authorized` remain `false`.
2. **Primary source stays Overture Maps buildings, release 2026-08-19.0**, in both cities, computed as the exact union of footprints clipped to district hydrographic land, divided by land area (gross variant reported). Definition: [DECISIONS.md](../DECISIONS.md), [SP attributes §8](../sp/ATTRIBUTES.md).
3. **Before accepting B1 as a model input, run the further tests and dataset review listed below**, including a search for additional independent footprint sources for São Paulo to reduce the asymmetry between cities.
4. **Fallback rule:** if no additional independent SP source is found, continue with the available sources (Overture primary, Microsoft diagnostic). B1 is the least problematic of the B families, so this is acceptable, provided B1 is labelled *mapped Overture footprint coverage, not surveyed coverage*, and the limits below are disclosed next to every reported value.

### Update (5 October 2026): tests run, B1 accepted

The planned tests were run as Step 4 of the [Chicago model plan](../chicago/MODEL_PLAN.md#step-4--b1-footprint-coverage) ([results](../../analysis/results/SP_CHI/b1_step4_2026_10_05/README.md)). Chicago passes against Cook 2022 LiDAR footprints. Brás is explained: Microsoft misses whole blocks; Overture equals the municipal map. A municipal São Paulo source was found (GeoSampa `edificacao`, 2007/2014) and shows that 22 São Paulo districts whose Overture footprints are mostly machine-learning-derived are under-mapped. The user kept Overture in both cities (GeoSampa too old) and accepted B1 with stated limits. The text below is the 30 September record.

### Why the problem is validation, not data availability

B1 already exists for all 96 SP districts and 77 Chicago Community Areas (176/176 footprint checks passed). What is missing is a reference that can tell whether Overture's footprints are complete, which is gate 2.

- **Microsoft cannot referee Overture.** Overture cites Microsoft on 373,434 of 1,381,239 Chicago rows and 869,479 of 7,278,768 SP rows, so the sources share lineage. Agreement is weak evidence; disagreement does not say which source is complete.
- **Microsoft minus Overture (eight-unit pilot):** Brás −36.12 pp, Grajaú −0.04, Itaim Bibi +8.64; five Chicago units −2.28 to −0.87. Which source is right in Brás is **unadjudicated**. Source: [pilot README](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md).
- **Source asymmetry.** Chicago has three footprint files on disk: municipal (820,606 records; publisher metadata says current as of August 2015; used for the original B1), Cook County 2022 (779,962 records per the cadastral acquisition; listed in [DATA_SOURCES.md](../chicago/DATA_SOURCES.md) as QA-only), and Overture. The only SP footprint file identified so far is the Overture-derived `analysis/data/SP/Edificacoes/sao_paulo_building_morphology.gpkg` (7,278,768 polygons, metropolitan bounding box), plus Microsoft. SP therefore has no known independent mapping effort to check against.
- **Denominator support.** Chicago's original water mask (CMAP parcel proxy) covers 1.24 km²; the municipal hydrography layer covers 13.91 km², many records edited around 2001. SP uses its own hydrography.
- **Vintage.** Overture 2026, municipal Chicago 2015, Cook 2022; observation dates within Overture are not uniform.

### Reasoning for accepting Overture-only if nothing better is found

- It is one schema and one release in both cities; mixing sources across cities would add a worse inconsistency.
- A similarity model depends on relative position, so uniform under-mapping matters less than **differential completeness** by district or by city. That is the risk to test.
- The project's own rule permits a disclosed, qualified measurement.

### Planned tests and dataset review (not yet run)

The thresholds that would downgrade B1 must be **fixed before running the tests and approved by the user**; none are set here.

| # | Item | Purpose | Status |
|---|---|---|---|
| T1 | Compare Overture B1 with the Chicago municipal (2015) and Cook 2022 footprints, using the same union and land denominator in all 77 areas | Triangulate Chicago with separate mapping efforts; identify areas where Overture differs most | not run; Cook 2022 never compared per the docs read |
| T2 | Tabulate Overture `sources` field by city and by district | Test whether lineage, and so likely completeness, differs between SP and Chicago | not run; only Microsoft share is documented |
| T3 | Explain the Brás −36.12 pp gap (map samples, polygon scheme: parts versus outlines, source mix in Brás) | Decide whether it signals under-mapping or a representation difference | not run |
| T4 | Quantify the water-mask effect: B1 under CMAP proxy versus municipal hydrography (Chicago) and SP hydrography | Close the land-support gate | not run; gross and land variants already exist |
| T5 | Compare the between-district spread of B1 with a plausible mapping-error bound | Show whether rankings are robust to the error | not run |
| T6 | Search for additional SP footprint or built-surface sources | Reduce the city asymmetry | not run; see below |
| T7 | Stratified imagery sample (dense, industrial, peripheral; Brás, Loop, O'Hare and one SP peripheral area) with omission/commission counts | Independent accuracy check when no separate source exists | not run; method precedent in the M3 pilots |
| T8 | Evaluate the SP IPTU column `AREA OCUPADA` (occupied area) as a cadastral, non-Overture footprint-area check for SP | Possible independent SP source, reducing the city asymmetry | not run; found 30 September 2026 during the B2 search. Meaning, units, and whether it repeats across condominium accounts of one lot are **unknown**; it would need one-value-per-lot deduplication before any district sum |

### SP source search (T6): leads to verify, none confirmed

All entries are **unverified ideas**, not found sources. Each needs checking for coverage, date, licence and independence from Overture/Microsoft lineage before any use.

- A municipal or cadastral building layer published by the city of São Paulo (existence and coverage unknown).
- OpenStreetMap buildings taken directly, with the caveat that OSM feeds Overture.
- Other open global footprint products.
- GHSL built-surface layers from the same R2023A package already acquired for BV: a modeled, not mapped, built-up share per 100 m cell, usable as a coarse consistency check only. Whether the built-surface product is on disk is **not checked**.
- IBGE address or census counts as indirect completeness indicators (not footprint sources).
- Lot and IPTU constructed-area records: these measure floor area, not footprint, and cannot substitute for B1.

### What B1 will and will not claim

- It reports mapped Overture footprint area over hydrographic land. It does not report surveyed building coverage, plot coverage or site coverage in the planning sense.
- Source dates differ across cities and sources; report them beside the value.
- Acceptance flags stay `false` until T1–T7 are reviewed and the user decides.

### Open questions for the user

1. Downgrade criteria for T1, T2, T5 and T7, to be set before the tests are run.
2. If T6 finds a candidate SP source, is it primary, sensitivity or QA only?
3. Is a manual imagery sample (T7) in scope if no separate SP source is found?

---

## B2 — reported floors

### Decision (30 September 2026)

**B2 is out of scope** for the Chicago-only model and the future SP–Chicago common model. It will not be built. After an exhaustive search of local and public sources, no Chicago source reports floor counts for the whole building stock, and the partial sources cannot be combined without imputation or entity assumptions the project forbids.

- No proxy takes B2's name or weight. GHSL height (BV), LiDAR height and footprint data do not substitute for reported floors, and metres are not converted to floors.
- The existing Chicago reported-subset values (municipal `stories`, [chi_local_2026_09_16_v1](../../analysis/results/Chicago/chi_local_2026_09_16_v1/README.md)) remain a descriptive diagnostic outside every model.
- SP B2 is constructible and remains in the existing SP v2 model, which is unchanged. It is not carried into a cross-city distance.
- Reopening B2 requires a new, whole-stock Chicago floor source and a separately recorded decision.

### SP: constructible

`QUANTIDADE DE PAVIMENTOS` ("número de pavimentos do imóvel", IPTU 2026) is positive on 3,821,418 of 3,920,972 fiscal records (97.5%; 99,554 zero), computed 30 September 2026 from `analysis/data/SP/Cadastro e Vias/IPTU_2026.csv`. After the one-report-per-entity rule: 1,548,308 eligible profiles of 1,667,297 accepted entities (about 92.9%). This is a tax-register field, not a survey; its accuracy is not audited.

### Chicago: sources searched and why each fails

Local fields were scanned with [scan_chicago_floor_fields.py](../../analysis/scripts/scan_chicago_floor_fields.py) on 30 September 2026. Cook commercial years were queried live through the Socrata API (`datacatalog.cookcountyil.gov/resource/csik-bsws.json`, grouped by `year`, `township`, `sheet` and `stories`) on the same date.

| Source | Finding | Why it cannot form B2 |
|---|---|---|
| City building footprints, `stories` | 427,998 of 820,606 positive; 392,608 are `0` (no report). Assigned ACTIVE coverage 52.16%, district range 20.90–76.78% | About half the stock, selective by area; publisher says current as of August 2015 |
| Overture 2026-08-19.0 `num_floors` | 429,594 of 1,381,239 positive; all from OpenStreetMap (359,000 OSM + USGS Lidar, 65,274 Microsoft + OSM, 5,320 OSM) | Not independent: counts mirror the city file (2 floors 197,579 vs 198,439; 1 floor 191,282 vs 191,840), and OSM imported the city footprints in 2012–13. Inferred from distributions and import history, not a record-level join |
| Cook residential characteristics 2024, `char_type_resd` | 439,730 records: 1 Story 155,746; 1.5 Story 54,330; 2 Story 188,168; 3 Story + 32,525; Split Level 8,950; blank 11 | Categorical and top-coded at 3+, so no P90; covers single-family and multifamily under 7 units only |
| Cook condominium characteristics 2024 | No stories field | Condominium buildings have no floor report |
| Cook commercial valuation, `stories` | 2021: 7,065 of 35,182 rows non-null; 2022–2025: zero. 2021 by township: Rogers Park 0/1,122, West Chicago 0/8,117, Jefferson 20/6,712, Hyde Park 2,321/4,324, Lake 3,727/10,104, North Chicago 482/2,413, South Chicago 515/2,390. Mostly the `Class3` sheet (5,483). Contains year values (1915, 1908) | Geographically incomplete, 2021 vintage, valuation records (`keypin`) not physical buildings, known bad values |
| 2024 commercial workbooks (T70–T75, T77; T76 absent) and text extracts | Only property-type labels: "Low Rise (3 floors or less)", "MidRise (4 to 12 floors)", "High Rise (13 floors +)" | Bins, not counts |
| Energy benchmarking 2023 / covered register | Gross floor area on 2,583 of 3,434 records; no floors field | Floor area, not floors; buildings over 50,000 ft² only |
| Cook 2022 building footprints | `Height` positive on all 779,962 | Metres, not floors |
| DuPage parcels; city building permits | No floor field (permit free-text `work_description` not searched) | No data |
| Web search | No PLUTO-style Chicago register; HiTAB (Li & Sharma 2024) is 1 m height in metres; tall-building databases cover skyscrapers only; parcel vendors are paid; Cook subscription/FOIA availability unconfirmed and previously ruled out by the user | No public whole-stock source |

### Why the partial sources cannot be combined

1. **Non-random gaps.** Condominium towers and larger apartment/commercial buildings are the missing stock, so a stitched P90 would be biased downward.
2. **Different entities.** Footprint buildings, residential PIN cards and commercial valuation records have no resolved crosswalk (the same gap as M7).
3. **Different vintages:** 2015, 2021 and 2024.
4. **Incompatible coding:** exact counts, top-coded categories, half-stories, split levels.
5. **Forbidden repairs.** Imputing missing reports, treating a missing report as one floor, or converting metres to floors all violate project rules.

### Not searched

Permit free text; extended-mode web search; paid sources; records requests.

---

## B3 — constructed floor-area intensity

### Decision (30 September 2026): refused

**B3 is refused** for the Chicago-only model and the future SP–Chicago common model, on the same basis as B2. After local audits, a Socrata catalog search and extended web searches, no public source gives constructed floor area for the whole Chicago building stock. The partial sources cover different stock, define area differently and cannot be summed without double counting or omission. No proxy takes B3's name or weight; SP B3 stays in the unchanged SP v2 model only. Reopening B3 requires a new whole-stock Chicago area source with documented meaning and a recorded decision.

### Evidence

**Local assessor sources** (2024 schemas; [DATA_SOURCES.md](../chicago/DATA_SOURCES.md)): residential `char_bldg_sf` is exterior-measured area for single-family and multifamily under 7 units; commercial `bldgsf` is populated on 30,166 of 32,931 2024 rows (`gross_building_area` on zero), and 2024 is Chicago's reassessment year, so this slice is citywide for income-producing classes (an earlier draft of this report wrongly called it a partial-triad limit); benchmarking covers buildings over 50,000 ft² (2,583 of 3,434 with area); municipal `BLDG_SQ_FOOTAGE` is not maintained; DuPage has no area. A [PIN-level coverage audit](../../analysis/results/Chicago/chicago_pin_area_coverage_2026_09_30/README.md) (PIN counts, not area) finds 63.5% of 883,597 Chicago-linked PINs with some recorded area: class 3 79.0%, class 5 84.9%, residential class 2 69.0%, exempt 1.5% of 49,958.

**Condominiums** (checked 30 September 2026): condo `char_building_sf` exists for 12,221 of 14,352 condo groups by `pin10` (85.2%), but for only **3 of 899** groups with 50 or more units; 76,325 of 287,189 unit records sit in groups with building area. The live API (`3r7i-mrz4`, Chicago townships 70–77) shows 2024 building-area fill of 2.8% in South Chicago township (1,300 of 46,021 records) and 7.5% in North Chicago (4,910 of 65,581), the townships containing the Loop and Near North high-rises; fill has stayed near 72,000–73,000 records per year since 2021. `pin10` is a grouping lead, not a verified building ID. The 2024 commercial workbooks' `Condos` sheets (1,947 rows across T70–T75/T77) are commercial retail/office/parking condos, not residential condominiums.

**Socrata catalog search** (`api.us.socrata.com/api/catalog/v1`, domains `datacatalog.cookcountyil.gov` and `data.cityofchicago.org`; queries "square feet", "square footage", "floor area", "building area", "sqft", "building size"): no whole-stock area dataset. Cook hits were the residential, condominium and commercial datasets already held, plus archived (May 2022) residential characteristics. The `Assessor - Property Tax-Exempt Parcels` dataset (`vgzx-68gb`) has no area field. City hits were program-specific (TIF, PACE, grocery stores, city-owned land, green roofs) plus:

- **Energy Usage 2010** (`8yq3-m6wp`): census-block aggregates by building type with `kwh_total_sqft`/`therms_total_sqft`; publisher says the data cover 88% of Chicago buildings in 2010 but only 68% of electricity and 81% of gas use; blocks with under 4 accounts are reported at Community Area level. Sum of the larger of the two sqft columns: 1.714 billion ft². The sqft definition and origin are undocumented. Not accepted as B3: 2010 vintage, unknown area meaning, and large consumers under-represented. It is used below only as a Chicago check.

**Paid sources:** ReportAll ($250, "Building Size"), Regrid and Dynamo Spatial sell Cook parcels with building area fields; one vendor page reports 64–67% coverage for building area fields. Not purchased. Their coverage is similar to the 63.5% already held, so they are unlikely to close the condo and exempt gaps (inference).

---

## BI — built-volume intensity (proposed alternative to B3; not B3)

**Status: proposed, for user evaluation; decision deferred (30 September 2026).** Tag `BI`, role `supplemental_proxy`, never labelled B3 and never given B3's weight by default.

### Definition

`BI_ghsl_volume_intensity_land = Σ_cells (GHSL BUILT-V 2020 volume × share of the cell on district hydrographic land) ÷ district land area`, in m³ per m² (metres). This is the existing sealed H1–H3 candidate `volume_density_land`, so no new construction is needed. It measures how much built volume stands on each square metre of land. It is not floor area: volume per unit of floor area varies (see the ratio below), so it is never divided by a floor height.

### Why it is the closest defensible substitute

B3 itself is floor space per land area, which combines ground coverage and number of floors. Built volume per land area combines coverage and height in the same way, is paired in both cities from one product and one method, and covers every unit.

| Check | Result |
|---|---|
| SP: `volume_density` (gross) vs cadastral B3 (IPTU) across 96 districts | Spearman **0.901** |
| SP: same vs SP B2 median / P90 floors | 0.580 / 0.599 |
| Chicago: vs Energy Usage 2010 floor-area intensity (77 areas) | **0.891** |
| Chicago: vs Cook 2022 LiDAR footprint × max height | 0.925 |
| SP: ratio volume density ÷ cadastral B3 | median 8.48 m, range 3.78–97.81 m |

Tables: `sp_ghsl_vs_cadastral_b2_b3.csv` and `chicago_ghsl_vs_energy_usage_2010.csv` in [bv_ghsl_lidar_evaluation_2026_09_30](../../analysis/results/SP_CHI/bv_ghsl_lidar_evaluation_2026_09_30/README.md). The SP comparison uses gross-support volume against land-support B3.

### Limits

- Modeled, not measured: 2020 volume is 2018 GHSL height × 2020 built surface; published ANBH error (MAE 1.97 m) is from European cities only. GHSL underestimates the Loop (41.6 m vs 92.9 m LiDAR built height).
- Wide variation in volume per floor area (3.8–97.8 m) means BI and B3 rank similarly but are not proportional; BI is not an estimate of floor area.
- Vintage differs from other families (2018/2020).

### Redundancy and weighting (must be decided with BI)

BI overlaps the other built-form measures: Spearman with Overture B1 0.741 (Chicago) / 0.670 (SP), with the current BV coordinate 0.933 / 0.949, and with built-surface-weighted height 0.807 / 0.738. Volume is currently the same-family sensitivity inside BV. If BI is adopted it cannot also remain inside BV, and three full budgets for B1, BV and BI would triple-count coverage and height. Options:

1. **BI replaces the volume sensitivity; BV becomes built-surface-weighted height** (0.330 / 0.132 with B1). The three are then coverage, height and intensity, sharing a built-form budget to be set by the user.
2. **BI instead of BV**: one vertical family (volume), keeping B1.
3. **No BI**: accept the loss of the B3 dimension; BV and B1 only.

## BV — estimated vertical form

### Evaluation (30 September 2026), decision pending

Results are in [bv_ghsl_lidar_evaluation_2026_09_30](../../analysis/results/SP_CHI/bv_ghsl_lidar_evaluation_2026_09_30/README.md); figures below are from that README and were computed from existing sealed inputs.

1. **The current BV coordinate mixes coverage and height.** `net_grid_height_*` is a land-weighted ANBH mean including zero-height cells. The GHSL identities (Data Package §2.2.1) give ANBH = volume ÷ built surface and AGBH/ANBH = built fraction. Empty cells (ANBH = 0) cover up to 37.8% of a Chicago area and 87.7% of an SP district (Marsilac, SP:52). Example of the mix: Grajaú (SP:30), with 54.5% of its area in empty cells, has a mean of 3.6 m including zeros vs 10.9 m over built surface. (Corrected 1 October 2026: an earlier version attributed the Grajaú figures to Marsilac and labelled Marsilac SP:30; values from `bv_variants_with_b1.csv`.) Its rank correlation with B1 is 0.524 (Chicago) and 0.515 (SP).
2. **A built-surface-weighted height removes the overlap with B1.** Σ volume ÷ Σ built surface per unit, computable from the two rasters already on disk, correlates 0.330 (Chicago) and 0.132 (SP) with B1 while staying close to the current coordinate (0.933 and 0.822). It is a different statistic from the frozen candidate and would need a new definition and decision; the 25 September decision specifies the land-weighted ANBH mean.
3. **Distribution, not only a mean.** Built-weighted P50 and P90 of ANBH were computed (P90 vs B1: 0.203 Chicago, 0.131 SP). They describe tower versus low-rise mix, at 100 m resolution and with GHSL's estimation error.
4. **Independent check for B1, including SP.** GHSL's implied built fraction (`AGBH/ANBH`, derived from the documented identity and not read from GHS-BUILT-S) tracks Overture B1 at Spearman 0.862 (Chicago) and 0.905 (SP), without using any footprint source. Level ratios differ (Chicago 1.37, SP 1.07). Brás: Overture 0.566, GHSL 0.444, Microsoft 0.205; Itaim Bibi (SP:35): Overture 0.253, GHSL 0.389, Microsoft 0.338. This partly addresses the B1 SP-asymmetry item (T6) and supports Overture over Microsoft in Brás, but not in Itaim Bibi.
5. **Chicago height plausibility.** Cook 2022 LiDAR footprint coverage vs Overture B1: Spearman 0.986 (Cook about 9% higher, range −3.5% to +21.6%). Built-weighted GHSL height vs LiDAR area-weighted height: 0.852, with large underestimates in the Loop (41.6 m vs 92.9 m).
6. **Validation limits.** The Data Package's published error (MAE 1.97 m, RMSE 3.55 m) comes from 38 European cities. An SP reference does exist but has not been acquired (see below; an earlier draft of this section wrongly said none exists). `Height` in the Cook 2022 footprint file is in US feet (source metadata), which the earlier docs listed as unconfirmed.

### How BV is computed (sealed candidate `net_grid_height_land`)

1. District hydrographic land = district geometry minus the water mask (SP municipal hydrography; Chicago municipal `Hydro`).
2. Intersect land with the **native GHSL 100 m cells** (ESRI:54009 Mollweide; no resampling); weight each cell by its cell ∩ land area, computed in Mollweide.
3. `BV = Σ(weight × ANBH_2018) ÷ Σ(weight)`, in metres. Valid zero cells are included; NoData is excluded and its area reported.
4. Diagnostics and alternatives: AGBH 2018 on the same weights; volume intensity = Σ(cell volume_2020 × share of the cell on land) ÷ land area.

Sources: [DECISIONS.md](../DECISIONS.md) B1/BV decision, [BV.py](../../analysis/curio_nodes/BV.py), and the cell-level reproduction in the evaluation folder (maximum difference from sealed values 2.7e-6).

### Vintage (verified in GHSL Data Package 2023, §2.2 and §2.3)

- **Height (ANBH, AGBH): epoch 2018.** Predicted by regression from the global DEMs AW3D30 and SRTM30 plus a 2017–2018 Sentinel-2 composite (shadow markers). The DEM inputs are older than 2018 (SRTM dates from 2000; AW3D30 acquisition years not checked in the PDF).
- **Volume: `BUVOL = ANBH × BUSURF`.** The 2020 volume is the 2018 height multiplied by the 2020 built surface, which is itself interpolated in 5-year steps (1975–2030). It is therefore not independent evidence of height or of height change.
- Other B-family sources have different dates: Overture B1 2026, Chicago municipal footprints 2015, Cook LiDAR footprints 2022, SP LiDAR 2017.

### What the B1–BV correlation means

The 0.52 figure is a **Spearman rank correlation across districts, computed separately within each city** (not pooled, not Pearson): 0.524 Chicago, 0.515 SP on gross support (this evaluation); 0.537 Chicago, 0.511 SP on land support (sealed [H4 review](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md)). It is a moderate overlap, arising partly because BV averages in zero-height empty cells (a coverage effect) and partly because denser districts also tend to be taller. With built-surface-weighted height the overlap falls to 0.330 and 0.132.

### Main harmonization problem: cross-city comparability of GHSL error

Using the same product, epoch, grid and aggregation in both cities secures the same definition, not the same accuracy. GHSL is modeled, and its error depends on building height and possibly terrain. In Chicago, built-weighted GHSL height tracks LiDAR in rank (0.852) but compresses the tall end (level ratio 0.41–1.30; Loop 41.6 m vs 92.9 m). If this bias differs between SP and Chicago, a cross-city distance would read instrument bias as urban difference or similarity. Whether GHSL errors differ with terrain (SP hilly, Chicago flat) is **inferred, not tested**. The coverage–height mix (point 1 above) is a second, fixable-by-definition problem.

### SP height references (searched 30 September 2026)

Local check plus extended web searches. None has been acquired or tested.

| Source | Description | Independent of GHSL | Possible role |
|---|---|---|---|
| **GeoSampa LiDAR 2017** | Municipal helicopter survey, Feb–Jun 2017 (Optech Gemini); surface model (MDS) and terrain model (MDT) at 0.5 m over the whole municipality, 5–30 points/m², PEC-PCD class A; LAZ files downloaded tile by tile from GeoSampa ("Download de Arquivos"). Licence, point classification and total size not checked | Yes (measured) | **Primary SP height reference.** MDS − MDT gives height of all objects including trees, so a building mask is needed |
| Overture SP `height` (local, `sao_paulo_building_morphology.gpkg`) | Positive on 2,090,405 of 7,278,768 buildings, **all from OpenStreetMap** (2,088,387 in the metropolitan region). The OSM wiki's *PMSP Buildings* page describes a 2014–2018 import of the municipal "Mapa Digital da Cidade" retaining a `height` tag; survey year, method and units not documented there | Yes (municipal lineage, per wiki) | Secondary check; lineage and date to be confirmed |
| IPTU floors and constructed area | Floors and m², not metres | Yes | Rank check only. Already computed: GHSL volume density vs SP cadastral B3, Spearman 0.901; vs SP B2 median 0.580 |
| Google Open Buildings 2.5D Temporal | 4 m rasters of presence, count and height, 2016–2023, from Sentinel-2; covers Latin America including Brazil, not the US | No (modeled) | SP-only cross-check; cannot be paired with Chicago |
| 3D-GloBFP (2020), GlobalBuildingAtlas, UT-GLOBUS, WSF 3D (90 m) | Global modeled building heights | No | Alternative paired products, not truth. A blog test found 3D-GloBFP imprecise at micro scale in Brooklin, SP |
| Published GHSL validation | Pesaresi et al. 2024 (*Int. J. Digital Earth*): height regression coefficients estimated from experiments in six cities **including São Paulo and New York**; 100 m height MAE 2.27 m | n/a | São Paulo was a calibration city, so it is not an independent SP test. Full text returned HTTP 403; details come from search snippets, not verified |

A fair cross-city test must use the **same method in both cities**: LiDAR height with a building mask, aggregated to the same 100 m cells. The reference dates differ: SP 2017, Chicago Cook LAS 2022; GHSL height is 2018.

### Options for the user (not decided)

| Option | What changes | Cost |
|---|---|---|
| Keep frozen BV (land-weighted ANBH) | Nothing | Keeps the coverage–height mix; Marsilac-type units are dominated by empty cells |
| Replace with built-weighted height | New definition, one coordinate, less overlap with B1 | Requires a recorded decision; derived from the AGBH/ANBH identity |
| Add built-weighted P90 | Captures vertical tail | Extra coordinate inside the same budget; 100 m grid |
| Volume density as named alternative | Nearest B3-like intensity (m³/m²) | Correlated with B1 and height; one BV budget |
| Acquire GHS-BUILT-S | Reads built surface directly instead of deriving it | New download; epoch alignment with 2018 height |
| Paired LiDAR validation (GeoSampa 2017 tiles for Brás, Itaim Bibi and one peripheral district; Cook LAS 2022 tiles for the Loop and a low-rise area) | Measures whether GHSL's tall-building underestimate differs between cities | Download and processing of LAZ tiles; building mask; epoch gap 2017/2022 |
| Adopt `BI` (see the BI section) | Volume leaves BV and becomes its own proposed family | Requires restructuring BV to built-surface height and setting a shared built-form budget |

---

## Constraints carried forward

BV is not a replacement for B2 or B3; no proxy may take the name or weight of B2 or B3; a missing floor report is not one floor; footprint × height is volume, not floor area. Current gate status is in [STATUS.md](../STATUS.md).
