# Chicago-only model: feature acceptance plan

**Paused and resumed 1 October 2026.** The route was paused while the advisor's simplified composite index was built and tested ([SIMPLE_INDEX.md](../SIMPLE_INDEX.md), finished the same day) and then resumed by the user at Step 1.

Opened 1 October 2026. This page is the working plan for building the **Chicago-only model** over the 77 Community Areas (`CHI:01`–`CHI:77`), one feature family at a time. Each family is accepted, deferred or omitted by an explicit user decision recorded here. Dated project status stays in [STATUS.md](../STATUS.md); family definitions stay in [ATTRIBUTES.md](ATTRIBUTES.md); the earlier evidence is in the [M-family](../harmonization/M_FAMILY_DECISION_REPORT.md) and [B-family](../harmonization/B_FAMILY_DECISION_REPORT.md) decision reports. `fit_authorized=false` until the final step below.

## What "harmonize" means at this stage

In the cross-city stage, harmonizing means making one feature mean the same thing in São Paulo and Chicago. In the Chicago-only stage there is no second city. Here the word means **fixing one definition, one source, one spatial support and one vintage for a family, so that all 77 areas are measured the same way and the family fits beside the others in one contract.** A family is *accepted* when that definition is frozen, its pre-registered checks have run, and the user has signed the acceptance record. Matching São Paulo is not a criterion ([STATUS](../STATUS.md#chicago-only-model-current-stage)).

## Procedure for each family

1. **Freeze the definition**: numerator, denominator, source and release, vintage, allocation rule and missing-data rule. Write it in the step section below.
2. **Pre-register the checks**: each check gets a decision rule fixed and approved by the user **before** its result is seen. A number computed before the rule exists is context, not a test.
3. **Run the checks**: one script in `analysis/scripts/`, one dated results folder with a README, inputs read from the existing releases (no rebuild unless a check requires it).
4. **Acceptance record**: the user marks the family `accepted`, `accepted with stated limits`, `deferred` or `omitted (loss stated)`. Record the date and the reason.
5. **Contract entry**: accepted families are appended to a new Chicago contract `analysis/config/chicago_model_v1.json`, created at the first acceptance. It carries the frozen definitions only; weights, transforms and scales are set in the final step.

## Cross-cutting conventions

Decide each convention once, at the first step that needs it, then apply it to every later family.

| ID | Convention | Proposal | Decided at |
|---|---|---|---|
| C1 | Reporting units | 77 Community Areas, EPSG:26916, IDs `CHI:NN` | already fixed |
| C2 | Area denominator for densities (U2, U3, M1, B1) | **Decided 2 October 2026 (user): land = Community Area minus water** (release field `hydro_land_m2`). Replaces the 1 October direction toward developed land: land minus water is simpler to define and compute. Water layer and sensitivities: decisions S1-1 and S1-2 below | Step 1 (U3) |
| C3 | Source register | Every accepted family lists source, release, observation period and hash; vintages are not aligned, they are disclosed | Step 1 |
| C4 | Missing data | Null with a reason; never imputed into an accepted family | already fixed |
| C5 | Family budgets, transforms, scaling | Set jointly at the end on the Chicago cohort, not per family | final step |
| C6 | Cross-city levels | **Decided 5 October 2026 (user): settle once at the common stage**, not per family, whether São Paulo and Chicago are compared on absolute values or on values relative to each city. Families where source behaviour differs by city: U4 (route counts), U2 (different registers, informality), BV (GHSL about 10–15% higher relative to LiDAR in São Paulo within height classes; corrected 6 October 2026) | common stage |

### C2 note: developed land (spot check, 1 October 2026; scratch computation, not a published result)

**Superseded as the denominator by the 2 October 2026 decision.** Kept because the same facts matter for U1 (open-space and vacant shares) and for the final joint review: with land minus water, open space, vacant land, cemeteries and the airport stay inside every density, so the "how much land is empty" signal is counted in each of U2, U3, M1 and B1 as well as in U1 (identity below). The final step must check that redundancy (C5).

Candidate mask: CMAP LUI 2023 primary codes on hydro land. Variant A counts `11`–`15` (all built uses, including rail `1511`, roadway parcels `1512`, airport `1530`) plus `6000` nonparcel/ROW as developed; open space `3`, vacant `4`, agriculture `2`, unknown `9` and unmapped land are not.

- Developed share of land: median 0.920, minimum 0.507 (Washington Park, CHI:40: 33.8% open space, 15.4% vacant).
- U3 on developed vs hydro land: Spearman 0.9709; 17 areas move 5 or more ranks; Washington Park moves 28, Woodlawn 16, South Chicago 12 (26.4% vacant).
- Airport `1530` is 25.16 km² of O'Hare's 33.96 km² land (and 1.86 / 1.36 km² in CHI:56 / CHI:64). Excluding it would multiply O'Hare's density about 3.9-fold.

### C2 support audit (1 October 2026; scratch computation, to be recomputed by the step-1 script)

Code meanings are taken from the source's own domain (`LUI_2023_view` FeatureServer layer 1, saved as `analysis/data/Chicago/lui_2023_docs/LUI_2023_view_layer1_schema_fetched_2026_10_01.json`, SHA-256 `3ef224bc…eacc9`): `41xx` vacant (residential, commercial, industrial, other), `42xx` under construction, `1360` cemetery, `1530` airport, `1540` parking, `1563` landfill, `3200` golf, `9999` uncodeable; `6000` is not in the domain (generated non-parcel polygons). Land = Community Area minus municipal hydrography; it matches the release `hydro_land_m2` within 0.06 m² per area.

- **Missing support is negligible:** uncodeable `9999` is at most 0.09% of any area's land; land with no LUI polygon is at most 0.72% except Oakland (CHI:36, 5.86%), which needs a map check.
- **Construction is negligible:** `42xx` is at most 0.68% (New City, CHI:61).
- **Variant A treats cemeteries as developed** (they are institutional `13xx`) while golf (`3200`) is open space. Cemeteries are 18.15% of Lincoln Square (CHI:04), 14.90% of North Park (CHI:13) and 13.78% of Mount Greenwood (CHI:74). Moving cemeteries and landfill (Hegewisch, CHI:55, 10.12%) out of developed land changes U3 by +23.6% in Lincoln Square (15 ranks) and moves 4 areas by 5 or more ranks; Spearman 0.9945 with Variant A.
- **Airport:** with cemeteries and landfill already out, excluding `1530` multiplies O'Hare's U3 by 9.39 (26 ranks) and moves Clearing (CHI:64) 10 and Garfield Ridge (CHI:56) 8 ranks.
- **Denominator and information:** log(residents ÷ land) = log(residents ÷ developed land) + log(developed share). A density on hydro land therefore already contains the developed share; moving to developed land plus one explicit share does not discard information, it decides how many times that share is counted across U2, U3, M1 and B1. A single "developed share" would mix parks (amenity) with vacant land (disinvestment); U1 already carries both as separate shares.

The developed-land sub-decisions (vacant, parks, airport, cemetery, ROW) and the proposed developed-share feature are closed by the 2 October decision; nothing in this note is a model input.

## Order and ledger

Order follows readiness and dependency, **not importance**. M1/M6 are the backbone of a street-morphology model and need the most user decisions; they are scheduled after the families whose remaining gates are smallest, but their decisions can be prepared in parallel.

| Step | Family | Why here | Status |
|---|---|---|---|
| 1 | U3 resident density | Closest to a defined measure; its population support is reused by U4; it forces C2 in its simplest case | **accepted with stated limits (5 Oct 2026)**; in `chicago_model_v1.json` |
| 2 | U4 public transport accessibility (redefined 5 Oct 2026; was reachable bus supply) | Depends on U3's population support | **accepted with stated limits (5 Oct 2026)**; PTAL, Chicago in `chicago_model_v1.json`, São Paulo kept for the common stage |
| 3 | U2 workplace-job density | Same block-allocation machinery as U3; job universe and downtown allocation to state | **accepted with stated limits (5 Oct 2026)**; Chicago LODES 2023 in `chicago_model_v1.json`, São Paulo RAIS 2022 kept for the common stage |
| 4 | B1 footprint coverage | Retained by user decision; Chicago has three footprint sources for triangulation (B-report T1, T4, T7) | **accepted with stated limits (5 Oct 2026)**; Overture in both cities; Chicago in `chicago_model_v1.json` |
| 5 | BV vertical form (and the `BI` question) | Retained; the coverage–height mix and the three BI options must be decided | **accepted with stated limits (5 Oct 2026)** for Chicago; São Paulo LiDAR check done 6 Oct 2026 |
| 6 | M1 street density + M6 class mix | Street universe (Overture ten-class or municipal), class 4 treatment, O'Hare | **accepted with stated limits (6 Oct 2026)**; M1 and M6 in `chicago_model_v1.json` |
| 7 | U1 land-use mix | Ontology, `6000` nonparcel and unknown/vacant support | **mix score dropped (6 Oct 2026)**: ranks Sé and República least mixed; the four **land shares kept as an unweighted candidate** under a pre-registered admission rule for the final review |
| 7b | U6 activity composition (new, user request 6 Oct 2026) | Composition and diversity of unit types (homes, food & drink, retail, services, making, institutions), vertical mixing included | **accepted with stated limits (6 Oct 2026)**; Overture in both cities (D7b-3 RAIS test); in `chicago_model_v1.json` |
| 8 | M3/M4 blocks, M7 parcels | Open method tracks; may end as omitted with stated loss | **built 6 Oct 2026**; Chicago passes all checks; São Paulo fails the municipal-line check for M3/M4 (reference topology gaps) but passes official blocks (0.977); M7 passes both; **M3, M4, M7 accepted with stated limits (6 Oct 2026)**; in `chicago_model_v1.json` |
| — | M2, B2, B3 | Excluded/out of scope/refused by user decisions (25 and 30 September 2026) | closed |
| Cross-city | `sp_chicago_model_v1` (Brás reference; C6 hybrid) | User request after the Chicago fit | **fitted 6 Oct 2026**; [report](../harmonization/MODEL_REPORT.md) |
| Final | Joint review | Redundancy among accepted families, family budgets (C5), no-family sensitivities, contract freeze, then a fit-authorization decision | **done 6 Oct 2026**: J-1 to J-10 approved; contract frozen (12 families); fit run (R1, R2, R3); [model report](MODEL_REPORT.md) |

---

## Step 1 — U3 resident density

### Candidate definition (to freeze)

`U3 = Σ allocated 2020 Census residents ÷ Community Area land (km², area minus water, C2)`. Residents: `POP20` from TIGER 2022 tabulation blocks (2020 Census, adjusted by the Disclosure Avoidance System). Allocation: each block piece receives `POP20 × piece area ÷ whole block area` (gross polygon area). Existing values: `population_allocated` and `hydro_land_m2` (the released `population_density_2020_gross_km2` uses gross area and becomes a sensitivity) in [chi_functional_2026_09_16_v2](../../analysis/results/Chicago/chi_functional_2026_09_16_v2/README.md); 163/163 independent checks passed; allocated 2,745,500.35 residents, 36,978.65 in the outside-city remainder of border blocks, 0.002% of city area uncovered by blocks.

### Context already known (computed 1 October 2026, before any rule; not tests)

- **Gross vs hydro-land denominator:** Spearman 0.9988 across the 77 areas. Largest level changes: Hegewisch (CHI:55) +25.5%, South Deering (CHI:51) +21.6%, Riverdale (CHI:54) +11.8%, Loop (CHI:32) +8.4%. Lowest density under both: O'Hare (CHI:76), 389 residents/km² gross.
- **Split blocks:** share of each area's allocated residents that comes from blocks not wholly inside that area (straddling two areas or the city edge): median 6.1%, maximum 19.9% (Forest Glen, CHI:12), then O'Hare 19.3%, Kenwood 14.3%. These are upper bounds on the share that the uniform-area rule could misplace, not error estimates. *Superseded 2 October 2026:* these counted blocks touching a boundary by slivers; counting only blocks with at least 1% of their land across a boundary gives median 0.55%, maximum 7.23% (Hegewisch).

Both were computed directly from the release table and `block_district_pieces.parquet`; the step-1 script must recompute them.

### Checks to pre-register (decision rules need user approval)

| ID | Check | Proposed decision rule |
|---|---|---|
| U3-1 | Denominator (C2) | **Decided 2 October 2026:** land minus water. Sensitivity set: decision S1-2 |
| U3-2 | Allocation sensitivity for split blocks: (a) gross area of each piece, current; (b) land area of each piece (piece minus water); (c) Overture footprint area of each piece (dasymetric) | Rule and primary allocation: decision S1-3 |
| U3-3 | Mass conservation and coverage | Re-verify from existing validation: allocated + outside residual equals the city-intersecting block total; uncovered area ≤ 0.1%. Already passed; cite, do not rebuild |
| U3-4 | Period diagnostic against the supplied ACS aggregate | Descriptive only (different period and unresolved provenance); list areas with a difference above 10% for map review |

### What U3 will and will not claim

Residents counted by the 2020 Census, per km² of land, at Community Area level. Not daytime population, not housing units, not 2026 population. Disclosure Avoidance noise is negligible at Community Area totals but present in single blocks.

### Step 1 decisions (user, 2 October 2026: all recommendations accepted)

Answered before the step-1 script ran.

| ID | Decision | Options | Decided (recommendation accepted) and reason |
|---|---|---|---|
| S1-1 | Which water layer defines "land minus water" | (a) municipal hydrography `Hydro_20260916.geojson`, already used for `hydro_land_m2`; (b) CMAP LUI 2023 water `5000`; (c) the CMAP proxy water already in the release (`cmap_proxy_water_m2`) | **(a).** Already built and verified, independent of the land-use source, and the same layer will serve U2, M1 and B1 |
| S1-2 | Which denominator sensitivities are reported | (a) gross area only; (b) gross area and developed land; (c) none | **(a).** Gross area is free and already known to agree (Spearman 0.9988). Developed land would bring back the LUI sub-decisions just closed |
| S1-3 | Primary allocation of residents in blocks split by a boundary, and the U3-2 rule | Primary (a) gross piece area or (b) land piece area; compare with the other; (c) footprints in or out | **(b) primary, (a) as comparison, (c) out.** (b) assumes residents live on land, matching the denominator; (c) would make U3 depend on the B1 source. Rule: if no area changes by more than 5% and none moves 5 or more ranks between (a) and (b), the choice is immaterial and (b) stands; otherwise the cases come back for a decision. The earlier 2-rank limit is dropped because, among closely spaced mid-range values, a change of about 1% can move 2 ranks |
| S1-4 | U3-3 mass conservation and coverage | Cite the existing validation, or recompute | **Cite and recompute in the step-1 script** (cheap): allocated + outside residual equals the city-intersecting block total; uncovered area ≤ 0.1% |
| S1-5 | U3-4 period diagnostic against the supplied ACS aggregate | Keep as written (descriptive; list areas differing by more than 10%), change the threshold, or drop | **Keep as written.** It cannot fail U3; it only directs map review |
| S1-6 | Source register entry (C3) for U3 | Record source, release, observation period and SHA-256 for: TIGER 2022 tabulation blocks (`POP20`, 2020 Census), Community Area boundaries (20260831), municipal hydrography (20260916) | **Approve this list.** It is the first C3 entry and fixes the format for later families |

### Step 1 results (2 October 2026)

`analysis/scripts/evaluate_chicago_u3_step1.py` → [chicago_u3_step1_2026_10_02](../../analysis/results/Chicago/chicago_u3_step1_2026_10_02/README.md). All gates pass:

- **U3-2:** allocation by land (b) vs gross piece area (a): max change 0.44%, max 1 rank (rule: within 5% and fewer than 5 ranks). (b) stands.
- **U3-3:** 2,746,058.90 allocated + 36,420.10 outside = 2,782,479 block residents; uncovered city area 0.002%.
- **S1-2:** gross-area sensitivity Spearman 0.9988; no area moves 5 or more ranks.
- **U3-4 (descriptive):** 17 areas differ from the supplied ACS aggregate by more than 10%, 16 of them with Census above ACS (largest Oakland +55.4%, Kenwood +33.1%; O'Hare −17.5%); citywide +3.7%. Kept for map review; cannot fail U3.
- U3 ranges from 395 (O'Hare) to 15,416 (Near North Side) residents per km² of land; median 4,600.

### Source change: ACS 2020–2024 5-year (user decision, 2 October 2026)

**Decision:** the 2020 Census count is too old for U3; use the latest official estimate, the American Community Survey 2020–2024 5-year, table B01003 (total population). Its margin of error is accepted because it is an official measurement. The 2020 build above becomes a sensitivity, not the primary value.

**What the estimate is:** a sample survey pooled over 1 January 2020 to 31 December 2024 on 2020 Census geography. It is not a 2024 population; its observation period is the five years. It is published down to block group (2,316 block groups touch the city), not to block.

**Acquired 2 October 2026** (keyless table-based Summary File; the Census API now requires a key), in `analysis/data/Chicago/acs_2020_2024_5yr/` (git-ignored):

| File | URL | SHA-256 |
|---|---|---|
| `acsdt5y2024-b01003.dat` | https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b01003.dat | `38d1a992…b6ca90` |
| `ACS20245YR_Table_Shells.txt` (definition: B01003_001 = Total population) | https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/documentation/ACS20245YR_Table_Shells.txt | `5b46f4af…6b517d` |

**Feasibility (not a result):** all 2,316 block groups are present with estimate and margin of error, and no special margin codes; every block group with ACS residents has positive 2020 population in its own blocks (statewide TIGER file), so a 2020-block split is defined wherever there are residents to split. *Corrected 2 October 2026:* 4 block groups have zero residents in both sources; the earlier wording said every block group had 2020 population. Block-group estimates are noisy (median coefficient of variation 0.22), which is why the rule S1-8 is needed.

### Decisions for the ACS version (user, 2 October 2026: all recommendations accepted before any ACS value was computed)

| ID | Decision | Options | Recommendation and reason |
|---|---|---|---|
| S1-7 | How block-group estimates reach Community Areas (block groups do not nest in them) | (a) split each block-group estimate among its 2020 blocks by their 2020 population share, then blocks to areas by land pieces (S1-3); (b) split each block group by land area of its pieces | **(a) primary, (b) sensitivity.** Blocks nest exactly in block groups, so 2020 is used only for *where inside a block group* people live, while the *level* is 2020–2024. Same immateriality rule as U3-2: if no area changes more than 5% or moves 5 or more ranks between (a) and (b), (a) stands; otherwise the cases come back |
| S1-8 | Uncertainty gate | Area margin of error = √Σ(weight × block-group MOE)² (Census approximation; it ignores correlation between block groups, so it understates uncertainty). Coefficient of variation = MOE ÷ 1.645 ÷ estimate | **Gate: every area's coefficient of variation ≤ 12%.** Areas above it come back for a decision (accept with stated limit, or flag). Report each area's 90% interval and how many ranks it spans |
| S1-9 | Role of the 2020 Census build | Keep as period sensitivity, or drop | **Keep as a descriptive period comparison** (replaces the old U3-4 against the unresolved ACS aggregate): list areas whose ACS value differs from the 2020 count by more than 10%. Also test, descriptively, whether the supplied unresolved ACS aggregate equals any official vintage |
| S1-10 | Source register (C3) | Add the two ACS files above with URL, release (2020–2024 5-year, Summary File) and observation period | **Approve** |

### ACS results (2 October 2026)

Same script and [results folder](../../analysis/results/Chicago/chicago_u3_step1_2026_10_02/README.md). U3 (ACS) median 4,488 residents/km² of land, range 424 (O'Hare) to 15,688 (Near North Side); median CV 5.1%. Mass is conserved (2,710,782.56 inside + 192,402.44 outside = 2,903,185 block-group total).

| Rule | Outcome | Returned case | Recommendation |
|---|---|---|---|
| S1-8 every CV ≤ 12% | **2 areas above** | Burnside (CHI:47) 16.8%, Fuller Park (CHI:37) 14.2%; the two smallest populations (about 2,300 each). Each 90% interval contains only 3 areas' point estimates | Accept both with stated limit: the uncertainty does not change their place among the lowest-density areas |
| S1-7 (a) vs (b) within 5%, fewer than 5 ranks | **1 area outside** | O'Hare +9.5% under the land split (b), rank 77th under both | Keep (a): the land split assigns residents to airport land; (a) puts them where 2020 blocks had residents |
| S1-9 period comparison (descriptive) | 3 areas more than 10% from the 2020 count | West Garfield Park −13.4%, Calumet Heights −14.2% (both beyond the 90% margin), Hegewisch −11.3% (within it). City −1.28%; Spearman with the 2020 version 0.9947; 5 areas move 5 or more ranks | Map review only; cannot fail U3 |

The supplied ACS aggregate is **not** the 2020–2024 release (median per-area difference 3.3%, maximum 36.9%); its provenance stays unresolved and it is not used.

Returned cases decided by the user on 5 October 2026: all three recommendations accepted.

### Acceptance record

**U3: accepted with stated limits, 5 October 2026 (user).** Primary value `u3_acs_land_km2` (ACS 2020–2024 residents per km² of land). Stated limits:

1. Population pooled over 2020–2024, not a 2024 count; the 2020 distribution is assumed inside each block group.
2. Margins of error understate uncertainty (no covariance between block groups).
3. Burnside (CHI:47, CV 16.8%) and Fuller Park (CHI:37, CV 14.2%) exceed the 12% gate; accepted because each 90% interval spans 3 rank positions among the lowest-density areas.
4. O'Hare (CHI:76): the 2020-block split (a) is kept; the land split would add 9.5% by assigning residents to airport land.
5. Land includes parks, vacant land, cemeteries and the airport (C2); redundancy with U1 and the other densities is checked at the final joint review.
6. Municipal hydrography covers the city only.

Entered in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json) (created at this acceptance; `fit_authorized=false`), with table and script hashes. Sensitivities kept: 2020 count (`u3_land_km2`), block-group land split (`u3_acs_b_land_km2`), gross area (`u3_gross_km2`).

---

## Step 2 — U4 public transport accessibility (was: reachable bus supply)

### What already exists (built 16 September 2026; context, not tests)

[chi_functional_2026_09_16_v2](../../analysis/results/Chicago/chi_functional_2026_09_16_v2/README.md), `tables/bus_service_access`. Feed: CTA GTFS, calendar 11 September – 30 November 2026, 124 bus routes, 91,196 bus trips, no frequency templates, all integrity checks passed (`validation/transit_checks.json`).

**Method.** Residents are represented by points on a 250 m grid, each weighted by its share of 2020 block population. For each point, take every bus route and direction with a stop within the radius (straight line), count that route-direction's scheduled departures in the window at its best stop, and add them up. The area value is the population-weighted mean of the points: **scheduled bus departures available to the average resident within the radius in two hours.** The release calls it `expected_departures_per_resident`, but nothing is divided among residents, so the name is misleading.

**Scenarios built:** weekday 07:00–09:00 (16 September 2026), Saturday and Sunday 09:00–11:00 (19 and 20 September), each at 400 m and 800 m. Weekday 400 m: median 47.0 departures, range 7.1–269.6. Spearman between the six scenarios 0.928–0.985. Share of residents with any stop within 400 m: median 0.986 (weekday), minimum 0.464.

### Candidate definition (to freeze)

`U4 = population-weighted mean, over the area's residents, of scheduled CTA bus departures (sum over route-directions of departures at the best stop within r) in window w`.

### Redefinition (user, 5 October 2026)

U4 is widened from CTA bus supply to **public transport accessibility, including subway ('L') and commuter rail (Metra)**. The bus-only decisions S2-1 to S2-6 below are **superseded**; S2-1 (ACS resident weights, consistent with U3) is expected to carry over.

**Three meanings of "accessibility"** (they rank areas differently): *proximity* (is there a stop near the resident), *service* (how much transit runs near the resident), and *accessibility proper* (how many destinations the resident can reach by transit in a given time). Only the last measures what transit is for; it also depends on where destinations are.

**Data on hand (checked 5 October 2026; scratch, not results):**

| Source | Status |
|---|---|
| CTA GTFS (on disk) | 124 bus routes and 8 'L' lines (`route_type` 1); 143 'L' parent stations, in 42 of 77 areas |
| Metra GTFS | public, no key: `https://schedules.metrarail.com/gtfs/schedule.zip` (calendar to 31 December 2026); 11 lines, 241 stops, 74 inside the city in 34 areas. Not yet saved to `analysis/data` |
| Pace GTFS | public feed exists; the URL found is dated 2023, current file not yet identified |
| Rail station inside the area (L or Metra) | 59 of 77 areas; 18 have none inside (stations just outside a boundary can still serve them) |
| Street network for walking/routing | OSM Illinois extract on disk; Java 21 and `osmnx` installed; `r5py` not installed |
| Destinations | LODES WAC 2022 jobs (U2 source) on disk |
| São Paulo (later stage) | SPTrans GTFS on disk with bus, metro and CPTM stop records |

**Candidate definitions** (to choose one primary; others may be sensitivities):

| ID | Candidate | Meaning | Data and effort | Main weakness |
|---|---|---|---|---|
| A | Multimodal departures available to the average resident (current method, all modes; bus 400 m, rail 800 m) | service | CTA + Metra GTFS; reuse existing code | A train and a bus departure count the same, so the many bus departures dominate and rail adds little |
| B | PTAL-style accessibility index (Transport for London method): per route, access time = walk time + average wait; equivalent frequency = 30 ÷ access time; best route per mode at full weight, others at half; summed over modes; kept continuous | service + proximity, modes comparable in minutes | GTFS only; moderate code; method parameters must be taken from TfL's document and saved | Does not know where routes go; parameters calibrated for London |
| C | Jobs reachable by transit within 45 minutes (cumulative opportunities), median over 07:00–09:00 departures | accessibility proper | GTFS (CTA, Metra, Pace) + OSM + LODES jobs; `r5py` routing, heavier compute | Tied to where jobs are: overlaps U2 and distance to the Loop; threshold choice |
| D | Two components: share of residents within 800 m of a rail station + bus departures available to the average resident | proximity (rail) + service (bus) | easiest | Ignores rail frequency (a Metra stop with few trains counts like the Red Line); two features in one family |
| E | Ready-made index (EPA Smart Location Database transit variables, CNT AllTransit) | varies | download only | Vintage and method not ours; US only (fails the later São Paulo stage); best used as an external cross-check |
| F | Transit travel time to the Loop | accessibility to one place | `r5py` | Essentially distance to downtown; monocentric |

**Choice (user, 5 October 2026): candidate B, the PTAL Access Index, built for both Chicago and São Paulo** so it can enter the later common model. The Chicago value enters the Chicago contract; the São Paulo value is kept for the common stage.

### PTAL method as published (source saved)

Transport for London, *Connectivity Assessment Guide* (2015), section 2, tables 2.1–2.2 and figure 2.15: `analysis/data/shared/ptal_method/tfl_connectivity_assessment_guide_2015.pdf`, SHA-256 `aafbbe1c…5de416`, from the [London Datastore PTAL dataset](https://data.london.gov.uk/dataset/public-transport-accessibility-levels).

For a location, for every route with a stop within the maximum walk:

1. Walk time = network walk distance ÷ 80 m/min (4.8 km/h). Maximum walk 640 m (8 min) to bus, 960 m (12 min) to Underground or rail.
2. Scheduled waiting time SWT = 0.5 × 60 ÷ frequency (vehicles per hour, weekday 08:15–09:15). Only the route's nearest stop counts; if a route runs both ways, the most frequent direction is used. Rail services count only if they have at least two stops in the city.
3. Average waiting time AWT = SWT + reliability factor (2 min bus; 0.75 min Underground, rail, tram).
4. Total access time TAT = walk time + AWT; equivalent doorstep frequency EDF = 0.5 × 60 ÷ TAT.
5. Per mode: AI = largest EDF + 0.5 × sum of the other EDFs. Total AI = sum over modes. PTAL bands (0, 1a … 6b) are cut points on the AI; TfL averages the AI over all locations of a zone.

**Implementation check:** `analysis/scripts/harmonization/ptal.py` reproduces figure 2.15 (published total 15.16; computed 15.1619).

### Data for the two cities (5 October 2026)

| | Chicago | São Paulo |
|---|---|---|
| Bus | CTA GTFS (Sept 2026, calendar 11 Sep – 30 Nov 2026), 124 routes, exact timetables | SPTrans GTFS (downloaded 9 Sep 2026, no `feed_info`, calendar 2023-10-01 – 2027-04-01), 1,346 routes, **all trips given as hourly headways** (`frequencies.txt`, 40,402 rows) |
| Metro (TfL "Underground") | CTA 'L', 8 lines (same feed) | Metrô, 9 lines incl. monorail 15 and 17 (same SPTrans feed) |
| Rail | Metra GTFS saved 5 Oct 2026 (`analysis/data/Chicago/metra_gtfs_2026_10_05/schedule.zip`, SHA-256 `06b6f940…12926d`), 11 lines, service periods change weekly | CPTM, 7 lines (same SPTrans feed) |
| Suburban bus | Pace: current feed not identified | EMTU: not in the feed |
| Residents | ACS 2020–2024 allocation accepted for U3 (block level) | Census 2022 population by census tract, GeoSampa `densidade_demografica.gpkg` (27,301 tracts, 11,451,999 residents) |
| Walking network | Overture 2026-08-19 segments: 124,721 `footway` of 350,885 road segments | Overture 2026-08-19 segments: 35,449 `footway` of 423,904 |

### Decisions for U4 = PTAL (user, 5 October 2026: all recommendations accepted before any area value was computed)

| ID | Decision | Recommendation and reason |
|---|---|---|
| S2-7 | Modes and feeds | bus, metro, rail = CTA bus / CTA 'L' / Metra and SPTrans bus / Metrô / CPTM. Suburban bus operators (Pace, EMTU) **excluded in both cities** for symmetry; stated limit |
| S2-8 | Parameters | **TfL values unchanged in both cities** (walk speed, 640/960 m, reliability 2/0.75 min, weights 1/0.5, nearest stop per route, most frequent direction, rail services with at least two stops in the city). A local recalibration would need data we lack and could differ between cities |
| S2-9 | Window and frequency | Weekday 08:15–09:15. Frequency = departures of the route-direction at the stop inside the window: Chicago from the timetable on **Wednesday 14 October 2026** (inside the CTA and Metra calendars); São Paulo by generating each departure from the headway records plus each stop's time offset, weekday service. Same object in both cities |
| S2-10 | Walking network | Network distance on Overture segments, **excluding motorway and trunk** (TfL removes motorways and major trunk roads), including footways, paths, steps and pedestrian ways (TfL adds footpaths), plus the straight-line distance from the location to the network. Searched beyond the city edge so border residents reach stops outside it |
| S2-11 | Locations and weights | 100 m grid (TfL's grid) cut by population polygons; Chicago weights from the U3 ACS allocation, São Paulo from Census 2022 tract population by area share. Area value = **population-weighted mean AI** (the average resident's access); the unweighted mean over populated cells is reported |
| S2-12 | Feature and reported values | Feature `u4_ptai_avg_resident` (continuous mean AI). Reported: AI per mode, share of residents in each PTAL band, share with AI = 0. Bands are not used as the feature (they discard information) |
| S2-13 | Checks and rules | **U4-1 construction (must pass):** TfL example reproduced; Chicago departures equal raw timetable counts and São Paulo generated departures equal headway arithmetic on sampled routes; resident weights equal each area's residents; total AI = sum of mode AIs; share of stops more than 100 m from the walk network reported. **U4-2 footway sensitivity (harmonization gate):** streets-only network (no footway, path, steps, cycleway). If no area changes more than 10% and none moves 5 or more ranks within its city, the footway difference is immaterial; otherwise the cases return and streets-only may become primary. **U4-3 straight-line distance:** descriptive. **U4-4 descriptive:** Chicago bus-only U4 vs PTAL, mode shares, areas with more than 10% of residents beyond walking reach listed for map review |

### Step 2 results (5 October 2026)

[u4_ptal_step2_2026_10_05](../../analysis/results/SP_CHI/u4_ptal_step2_2026_10_05/README.md), script `analysis/scripts/evaluate_u4_ptal_step2.py`. Construction checks pass (TfL example 15.1619; Chicago residents equal U3; independent timetable counts; headway expansion), except the São Paulo district-assignment tolerance: 5,944.5 of 11,451,999 Census residents (0.05%) lie in tract parts outside the district boundary; no district value is affected.

| | Chicago | São Paulo |
|---|---|---|
| Median AI (range) | 5.65 (1.73 Edison Park – 38.93 Loop) | 14.20 (1.04 Marsilac – 70.97 República); Brás 36.9, 3rd |
| AI share bus / metro / rail | 80.6 / 16.1 / 3.3% | 96.9 / 2.4 / 0.7% |
| U4-2 footway gate | **3 cases:** Near South Side −10.8%, Douglas −11.0%, Archer Heights −13.5% (6 ranks); median −3.7% | **7 cases:** Jardim Helena −14.0%, Cidade Dutra −10.2%, Butantã (7 ranks), Vila Leopoldina (7), Artur Alvim (6), Vila Curuçá (6), Vila Jacuí (5); median −4.2% |
| U4-3 straight line | median +30.7% | median +62.5% |

**Returned for decision:** (1) the U4-2 cases; recommendation: keep footways in the primary network, because the effect is similar in both cities (median −3.7% vs −4.2%), within-city order barely moves (Spearman ≥ 0.997), and footways carry real links such as station and rail footbridges (to be checked on the map for Archer Heights and Jardim Helena); state the sensitivity as a limit. (2) The São Paulo assignment tolerance; recommendation: accept, the missing residents are outside the city's districts.

**Finding for the common model:** PTAL grows with the number of routes faster than with one route's frequency, so São Paulo's many overlapping bus lines raise its level and its Metrô contributes 2.4%. Within-city use is unaffected; cross-city levels need a decision at the common stage.

### Bus-only decisions (superseded 5 October 2026)

| ID | Decision | Options | Recommendation and reason |
|---|---|---|---|
| S2-1 | Resident weights | (a) 2020 block population, as built; (b) ACS 2020–2024 allocation accepted for U3 | **(b).** U3 and U4 then describe the same population. Within a block group nothing changes (the same 2020 shares are used); only block-group totals change |
| S2-2 | Primary service window | weekday 07:00–09:00; Saturday or Sunday 09:00–11:00; or a new weekday midday window | **Weekday 07:00–09:00 primary;** weekend windows reported as sensitivities. Already built and checked; a midday window would need a new rule and adds a choice without a stated question it answers |
| S2-3 | Primary radius | 400 m or 800 m, straight line | **400 m primary, 800 m sensitivity.** 400 m is the usual walking catchment for a bus stop; straight-line distance overstates real walking access across rail lines, rivers and expressways (stated limit) |
| S2-4 | Statistic | (a) departures available to the average resident; (b) share of residents within reach of any stop | **(a) primary, renamed `u4_bus_departures_avg_resident`;** (b) reported beside it as coverage. (b) is near 1 in most areas, so it separates few of them |
| S2-5 | Mode scope | (a) CTA bus only; (b) add CTA 'L' rail from the same feed | **(a), named as bus supply.** Rail is a different service with stations far apart; adding it changes the concept. Pace and Metra are not in the data (stated limit) |
| S2-6 | Checks and rules | Construction checks (feed integrity, radius monotonicity, population mass equals the U3 ACS residents per area) must pass. Support change (S2-1 a vs b): descriptive. Window and radius sensitivities: descriptive (Spearman and areas moving 5 or more ranks); a different window measures a different service, so disagreement is information, not failure | **Approve.** List areas whose 400 m coverage is below 0.90 for map review |

Next: user answers S2-1 to S2-6; then `analysis/scripts/evaluate_chicago_u4_step2.py`, a dated results folder, and the acceptance record.

### Acceptance record

**U4: accepted with stated limits, 5 October 2026 (user).** Returned cases decided: footways stay in the primary network (streets-only reported as a sensitivity); the São Paulo assignment shortfall (5,944.5 residents outside the district boundary) accepted. Primary value `u4_ptai_avg_resident`, rows `city == 'CHI'`, entered in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json) with table, script and method-code hashes. São Paulo rows are kept for the common-model stage. Stated limits:

1. Service near home, not where it goes.
2. Grows with the number of routes faster than with one route's frequency; cross-city levels need a decision at the common stage.
3. Scheduled service, not reliability; suburban buses (Pace, EMTU) excluded.
4. Footway sensitivity: streets-only lowers values by a median 3.7% (Chicago) and 4.2% (São Paulo); 3 Chicago and 7 São Paulo areas change by more than 10% or 5 ranks.
5. Walking ignores slope, crossings and safety; points snap to the nearest network node.
6. Lines with no departure counted in the window: Metra Heritage Corridor, Metrô Line 6; CPTM Line 13 excluded by the two-stops-in-city rule.

---

## Step 3 — U2 workplace-job density

### What already exists (context, not tests)

- **Chicago:** LODES WAC 2022, segment `S000` (all workers), job type `JT00` (all jobs), by 2020 Census block: 1,458,263 jobs in blocks touching the city; 1,409,454 allocated to the 77 areas by gross block area ([chi_functional_2026_09_16_v2](../../analysis/results/Chicago/chi_functional_2026_09_16_v2/README.md)). A CMAP business-land allocation sensitivity exists ([chi_employment_sensitivity_2026_09_22_v2](../../analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/README.md)).
- **São Paulo:** RAIS 2022 formal job links by postal code (CEP), `analysis/data/SP/Socioeconomico/rais_empregos_sp_2022.csv` (two columns, `cep` and `empregos`; 29,594 CEPs; 5,387,474 jobs). Provenance unresolved: the file was supplied already aggregated. CEPs are not polygons; earlier work located them with CNEFE 2022 establishment addresses and IPTU fiscal evidence ([SP ATTRIBUTES §12](../sp/ATTRIBUTES.md)). The documented primary (`area_first`) allocates 4,878,630 and leaves **508,844 unlocated**, of which **351,576 are under the placeholder CEP `99999999`** (6.5% of all jobs; no address).
- **Concentration (computed 5 October 2026, context):** the 100 largest Chicago blocks hold 44.6% of the city's jobs (15 blocks have 10,000 or more); the 100 largest São Paulo CEPs hold 23.8% (31 CEPs have 10,000 or more, the largest 130,394). Large single-address counts can be real towers or head-office reporting of dispersed workers; the data have no sector field to tell them apart.

### Decisions for Step 3 (proposed; need user approval before any value is computed)

| ID | Decision | Recommendation and reason |
|---|---|---|
| S3-0 | Scope | Build U2 for **both cities** (as for U4), and add São Paulo's U3 (Census 2022 tracts per km² of land) as a short catch-up step, so every accepted family exists in both cities. Chicago values enter `chicago_model_v1.json`; São Paulo values are kept for the common stage |
| S3-1 | Estimand | **Formal (registered) jobs at the workplace per km² of land** (C2). Jobs, not unique workers. Absolute density is the feature; **relative centrality** (area density ÷ city density) is computed beside it for the common stage, where cross-city levels will be decided for all families at once (U4 has the same question) |
| S3-2 | Source universe | Save the official documentation of LODES 8 and RAIS, write a side-by-side universe table (who is counted, job versus person, public sector, self-employed, reference date), and check the São Paulo file total against an official RAIS 2022 publication for the municipality. If the total cannot be verified, the file is used with a stated limit |
| S3-3 | Chicago allocation | Block → area by **land share** (same rule as U3); the CMAP business-land allocation as a comparison, with the usual rule (no area beyond 5% or 5 ranks, otherwise cases return) |
| S3-4 | São Paulo allocation | Keep the documented `area_first` allocation (business constructed area, then establishment addresses, then residential area); `address_first` as a comparison under the same 5%/5-rank rule |
| S3-5 | Unlocatable São Paulo jobs (508,844) | **Spread in proportion to the located jobs** (assumes they are distributed like the locatable ones; keeps the official total, which absolute density needs, and leaves district shares unchanged). Exclusion reported as a sensitivity |
| S3-6 | Concentration sensitivity | Descriptive, both cities: recompute without the 10 largest blocks (Chicago) or CEPs (São Paulo) and list areas changing by more than 10% |
| S3-7 | Construction checks | Mass conservation (Chicago inside + outside = block total; São Paulo allocated + unlocated = file total), land denominators equal the C2 fields, no missing values |

### Measurement problem and options (discussion opened by the user, 5 October 2026; no decision yet)

**User's statement:** "U2 is a location-uncertainty and covered-universe problem. We mostly know how many jobs exist, but not exactly where they are. Both registers count formal job links. A large share of work in São Paulo is informal. Both registers place a job at the address the employer reports, not where the person actually works."

**Evidence gathered (S3-2, [u2_source_audit_2026_10_05](../../analysis/results/SP_CHI/u2_source_audit_2026_10_05/README.md)):** LODES counts unemployment-insurance-covered and Federal jobs, all jobs per person, employed on about 1 April (verified). The São Paulo file is RAIS 2022 within 0.055% of the official municipal total (5,387,474 vs 5,390,446; verified). Public administration holds 693,043 RAIS jobs in 178 establishments (verified). The Metrô OD 2023 survey gives work trips attracted by district (all work, actual destination): district totals agree with RAIS at Spearman 0.836, but 18 of 96 districts differ by more than a factor of two, with the centre and head-office districts too high in RAIS (Jaguaré 4.4×, Pari 3.0×, Sé 2.3×) and peripheral districts too low (Cachoeirinha 0.27×, Cidade Tiradentes 0.33×). The São Paulo informality level is not verified.

**Options (for discussion):**

| Option | What it changes | Cost and risk |
|---|---|---|
| O1. Name the register measure honestly | `registered jobs at the declaring establishment per km² of land` | Nothing fixed; prevents over-reading |
| O2. Location-uncertainty interval | Report each area's bounds (certain-only vs all candidate jobs) and the scenario range; judge ranks against interval width | Exposes, does not remove, the error |
| O3. Head-office diagnostic | Flag postal codes or blocks whose jobs far exceed the survey share of their area; sensitivity without them | No sector field in the file, so causes cannot be separated |
| O4. Worker-reported workplace as primary | São Paulo: OD 2023 work trips attracted per km² of land; Chicago: a survey counting workers at their reported place of work (CTPP 2017–2021, to verify) | Counts all work at the real place; but sample error, trips ≠ jobs, different vintages, Chicago source and pandemic-era remote work unverified |
| O5. Register as primary, survey as validation | Keep register U2; pre-register an agreement test against the survey in both cities | Keeps register errors in the feature, but measured |
| O6. Smoothed job potential | Jobs within a distance band of each resident | Robust to small address errors only; not to head-office or informality |
| O7. Within-city relative centrality | Area density ÷ city density | Removes city-level universe differences (informality level), not within-city location errors |

**Evidence update (5 October 2026; [audit follow-up](../../analysis/results/SP_CHI/u2_source_audit_2026_10_05/README.md#follow-up-od-2023-jobs-by-workplace-zone-city-district-series-chicago-checks-5-october-2026), script `analysis/scripts/audit_u2_od2023.py`).** A second agent's [source search](../../analysis/results/SP_CHI/u2_work_data_search_2026_10_05/README.md) was verified and one figure corrected.

- **OD 2023 Table 14 counts jobs by workplace zone** (fixed outside home / at home / no fixed address; no-fixed-address jobs are placed at the residence zone). The microdata reproduce it exactly and carry the employment relationship.
- **Informality is real at city level:** of jobs located in São Paulo, 57.7% are RAIS-comparable, 26.0% informal, 16.3% other non-RAIS (self-employed with CNPJ, liberal professionals, employers).
- **But informality does not explain the district distortions.** Comparing like with like (RAIS vs OD RAIS-comparable fixed-workplace jobs), large gaps remain: Pari 4.0×, Jaguaré 3.2× (RAIS high); Perus, Cidade Tiradentes 0.40× (RAIS low). The register's main district error is **where jobs are registered**.
- **Totals disagree:** RAIS 5.39 million vs OD 3.75 million RAIS-comparable jobs located in the city.
- **The city's district RAIS table is unstable** (Brás 420,022 in 2022, 76,383 in 2023; Sé −372,760 the same year); the project's CEP allocation agrees with OD in Brás (45,960 vs 48,486).
- **OD precision:** 23 of 96 districts have fewer than 50 RAIS-comparable observations.
- **Chicago has no area-level independent check:** CMAP 2024–25 has a median of 6 workers per community area; LODES 2023 is available (+3.6% on 2022).

**Revised recommendation (for discussion):** (1) Chicago U2 from LODES 2023, land-share allocation; location error stated as unmeasured. (2) São Paulo register U2 from the project's RAIS 2022 CEP allocation, with **OD 2023 RAIS-comparable jobs as a pre-registered agreement test** (districts outside an approximate sampling interval are returned for decision). (3) An all-work São Paulo variant (OD fixed-workplace jobs) kept for the common stage, not primary, because Chicago has no equivalent. (4) The city's district RAIS table not used. (5) Cross-city levels decided at the common stage together with U4.

### User decisions (5 October 2026)

Estimand **(a): registered jobs at the employer's establishment per km² of land**; **LODES 2023** for Chicago; districts flagged by the OD agreement test **accepted with stated limits**. The S3-0 to S3-7 recommendations apply (the user asked to proceed).

### Step 3 results (5 October 2026)

[u2_jobs_step3_2026_10_05](../../analysis/results/SP_CHI/u2_jobs_step3_2026_10_05/README.md), script `analysis/scripts/evaluate_u2_step3.py`. Mass checks pass in both cities. Chicago median 944 jobs/km² (Loop 122,514); São Paulo median 3,052 (Sé 136,113; Brás 13,984, 15th).

**Returned for decision:**
1. **S3-3 Chicago:** Woodlawn (−5.4%, 5 ranks) and Hegewisch (−23.6%) change under the CMAP business-land allocation. Recommendation: keep land share (same rule as U3); state the two areas as a limit.
2. **S3-4 São Paulo:** 26 districts change by more than 5% under address-first weights (Spearman 0.9974; Alto de Pinheiros moves 10 ranks; Marsilac +157% on 251 jobs). Recommendation: keep `area_first`; state as a limit.
3. **OD agreement:** 45 of 96 flagged with the approximate interval, but only 6 when standard errors are doubled to allow for household clustering, all with RAIS higher (Pari, Jaguaré, Sé, Casa Verde, Consolação, Itaim Bibi). Already accepted with stated limits by the user; the limit is worded as a head-office bias in those districts.

Next: user signs the U2 acceptance record; then the São Paulo U3 catch-up (S3-0).

### Acceptance record

**U2: accepted with stated limits, 5 October 2026 (user).** Returned cases decided: Chicago keeps land-share allocation (Woodlawn, Hegewisch stated); São Paulo keeps `area_first` (26 districts' address-first sensitivity stated); OD-flagged districts accepted, worded as a head-office bias in six districts. Primary `u2_jobs_land_km2`, rows `city == 'CHI'`, entered in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json). Stated limits:

1. Registered jobs at the employer's establishment, not where people physically work; self-employed and informal work excluded (São Paulo OD 2023: 26.0% informal, 16.3% other non-RAIS).
2. São Paulo head-office bias: Pari, Jaguaré, Sé, Casa Verde, Consolação, Itaim Bibi higher in RAIS than OD under any plausible sampling allowance.
3. São Paulo CEP allocation: 26 districts change by more than 5% under address-first weights; 508,844 unplaced jobs spread like the placed ones.
4. RAIS 2022 exceeds OD 2023 RAIS-comparable jobs in São Paulo by 1.64 million (unexplained).
5. Chicago location error unmeasured; Woodlawn and Hegewisch sensitive to business-land allocation; LODES partially synthetic.
6. Reference dates: about 1 April 2023 (LODES), 2022 reference year (RAIS).

### São Paulo U3 catch-up (S3-0, 5 October 2026)

[u3_sp_catchup_2026_10_05](../../analysis/results/SP_CHI/u3_sp_catchup_2026_10_05/README.md): Census 2022 residents per km² of district land; equals the sp_prep v3 allocation and the U4 resident weights; median 11,111, Brás 10,690 (52nd). Kept for the common stage. U3, U4 and U2 now exist in both cities.

---

## Step 4 — B1 footprint coverage

### What already exists (context, not tests)

- **Values for all 173 units:** `analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/footprints/footprint_candidates.csv`, Overture buildings 2026-08-19.0, exact footprint union clipped to land, divided by land (`B1_coverage_land`); Chicago land equals the C2 field (`hydro_land_m2`). Code: `analysis/curio_nodes/B1.py`.
- **Prior decision** ([B-family report](../harmonization/B_FAMILY_DECISION_REPORT.md#b1--footprint-coverage)): retain B1 with Overture primary in both cities; the gap is validation, not data. Tests T1–T8 were planned and never run.
- **Related numbers computed earlier** (BV evaluation, 30 September; context): Cook 2022 LiDAR footprint coverage vs Overture B1, Spearman 0.986 (Cook about 9% higher); GHSL implied built fraction (no footprints used) vs Overture B1, Spearman 0.862 (Chicago) and 0.905 (São Paulo); Microsoft minus Overture in **Brás −36.12 percentage points**, unadjudicated.
- **Lineage caveat:** Overture cites Microsoft on part of its records in both cities, and Chicago's municipal 2015 footprints may have entered Overture through OpenStreetMap; these are not independent references. Cook 2022 LiDAR footprints and GHSL are separate efforts.

### Decisions for Step 4 (proposed; need user approval before any test is run)

| ID | Decision | Recommendation and reason |
|---|---|---|
| S4-1 | Definition and source | **Keep** `B1 = Overture footprint union on land ÷ land` (C2) in both cities; reuse the existing values after checking that São Paulo land equals the C2 field too. One schema in both cities |
| S4-2 | Chicago triangulation (T1) | Compare Overture with Cook 2022 LiDAR footprints and municipal 2015 footprints, same union and land. **Rule:** Overture stands if its Spearman with Cook is at least 0.95 and no area differs from the Cook value by more than 25% relative; otherwise cases return. Municipal 2015 reported, not ruled (possible shared lineage) |
| S4-3 | São Paulo independent reference (T6, T8) | Search for a municipal building-footprint layer (GeoSampa) and test the IPTU `AREA OCUPADA` field. A source found is **QA only**, not primary, so both cities keep one schema; it is judged with the same rule as S4-2 |
| S4-4 | Brás (T3) | **Must be explained before acceptance** (reference district): Overture vs Microsoft vs GHSL vs OpenStreetMap in Brás, plus a small imagery check of sample blocks |
| S4-5 | Lineage (T2) | Tabulate Overture `sources` by district in both cities; descriptive; districts dominated by one machine-learning source listed |
| S4-6 | Cross-city consistency | Ratio of Overture B1 to GHSL built fraction by district; descriptive; districts outside their city's 5th–95th percentile listed for review |
| S4-7 | Broad imagery sample (T7) | **Skip** unless S4-2 or S4-3 fails; it is costly and S4-4 already covers the reference district |

### Step 4 results (5 October 2026; decisions S4-1 to S4-7 approved before the tests)

[b1_step4_2026_10_05](../../analysis/results/SP_CHI/b1_step4_2026_10_05/README.md).

- **Chicago passes (S4-2):** Overture vs Cook 2022 LiDAR footprints Spearman 0.983, no area beyond 25% (Overture a median 8.5% lower). Chicago B1 can be accepted for the Chicago contract on its own.
- **Brás explained (S4-4):** Overture 0.566 equals the municipal GeoSampa map 0.568; Microsoft (0.205) misses whole blocks.
- **São Paulo fails (S4-3).** A municipal source was found: GeoSampa `edificacao`, 2,817,745 photogrammetric outlines. [City metadata](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/bcf69ef1-2f9e-42c2-b7ec-e808f89e8116) dates the underlying aerial photographs to **2004**; 2007 is the records' creation field and 2014 the last recorded edit, not the imagery date. Overture vs GeoSampa Spearman 0.937, 12 districts beyond 25%, 51 districts moving 5 or more ranks. Cause: Overture is two mapping regimes. In 65 OpenStreetMap-mapped districts it agrees with GeoSampa (median +3.9%); in **22 machine-learning-dominated districts** (North, South, West) it is a median 13.4% lower and ranks them on average 10 places lower; imagery in Itaim Bibi shows missed and partial outlines. Where Overture is higher, construction after the old photography is a plausible cause (Anhanguera, Iguatemi, Parelheiros).
- Per S4-7, the S4-3 failure brought imagery into scope; windows were inspected in Brás, Itaim Bibi and Parelheiros.

**Options for São Paulo B1 (decision needed):**

| Option | What it is | Gains | Costs |
|---|---|---|---|
| A. Keep Overture | One schema in both cities | Simple; current | 22 districts under-mapped; mean 10-rank distortion; a known, uneven error |
| B. GeoSampa | Official photogrammetric map, one method citywide | Consistent method for the mapped vintage | Based on 2004 photographs, with recorded edits through 2014; misses later growth; different source from Chicago |
| C. Union GeoSampa ∪ Overture | Every outline seen by either source | Fixes some machine-learning misses and adds growth | Keeps buildings removed after the old photography (redevelopment districts); mixes vintages |
| D. Regime hybrid | Overture where OpenStreetMap-mapped, GeoSampa elsewhere | — | Discontinuous rule inside one city; not recommended |
| E. GHSL built fraction in both cities | Modeled 100 m built surface, one method | Uniform method and vintage | A different estimand (built surface, not footprints); its ratio to footprints differs by city (0.74 vs 0.95) |

### User decision (5 October 2026)

**Keep Overture in both cities** (option A). GeoSampa (2007, edited 2014) is judged too old to describe current built form. It remains the evidence for the São Paulo limit below; the per-district machine-learning share is kept as a flag for the common stage.

### Acceptance record

**B1: accepted with stated limits, 5 October 2026 (user).** Primary `B1_coverage_land` (Overture footprint union on land ÷ land), Chicago rows entered in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json); São Paulo rows kept for the common stage. Stated limits:

1. Mapped footprint coverage, not surveyed coverage; Overture release 2026 with non-uniform observation dates.
2. Chicago: Overture a median 8.5% below Cook 2022 LiDAR footprints (range −17.8% to +3.8%); 99.4% of footprint area from OpenStreetMap.
3. São Paulo: 22 districts whose Overture footprints are more than 50% machine-learning-derived (North, South, West) are a median 13.4% below the 2007–2014 municipal map and rank on average 10 places lower; flag `ml_share` in `analysis/results/SP_CHI/b1_step4_2026_10_05/tables/b1_sp_explanations.csv`.
4. Microsoft footprints are not used (they miss whole blocks in Brás).

---

## Step 5 — BV vertical form (and the BI question)

### What already exists (context, not tests)

From the [B-family report](../harmonization/B_FAMILY_DECISION_REPORT.md#bv--estimated-vertical-form) and [bv_ghsl_lidar_evaluation_2026_09_30](../../analysis/results/SP_CHI/bv_ghsl_lidar_evaluation_2026_09_30/README.md):

- **Frozen BV** = land-weighted mean of GHSL 2018 building height (ANBH) **including empty cells**, so it mixes coverage and height (Spearman with B1 0.524 Chicago, 0.515 São Paulo). Example: Grajaú, 3.6 m including empty cells vs 10.9 m over built surface.
- **Built-surface-weighted height** (Σ volume ÷ Σ built surface) removes most of the overlap with B1 (0.330 Chicago, 0.132 São Paulo).
- **BI** (built volume per m² of land) was proposed as a stand-in for the refused B3; it overlaps B1 (0.741 / 0.670) and BV (0.933 / 0.949).
- **Height accuracy:** in Chicago, built-weighted GHSL height vs Cook 2022 LiDAR building height Spearman 0.852, but GHSL compresses tall areas (Loop 41.6 m vs 92.9 m). GHSL height is epoch 2018, modeled from elevation models and Sentinel-2.
- **New São Paulo reference on disk:** the GeoSampa `edificacao` download (Step 4) includes each building's photogrammetric height `qt_altura_edificacao` (2007, edited 2014). Overture São Paulo heights (2,090,405 buildings) come from OpenStreetMap, reportedly a municipal import.

**Identity worth knowing:** volume = height × built surface, so BI ≈ BV(built-weighted) × built fraction. BI carries almost no information that B1 and a built-weighted BV do not already carry; adding it mainly re-weights coverage and height.

### Decisions for Step 5 (proposed; need user approval before any test is run)

| ID | Decision | Recommendation and reason |
|---|---|---|
| S5-1 | BV definition | **Built-surface-weighted GHSL height** on land (Σ volume ÷ Σ built surface, m): "how tall is what is built", separated from coverage (B1) |
| S5-2 | BI | **No separate BI family**; compute it descriptively. By the identity above it is nearly the product of B1-like coverage and BV; a separate budget would double-count both |
| S5-3 | Vertical tail | Built-weighted P90 height reported, not a feature (100 m cells, GHSL error largest in towers) |
| S5-4 | Source | **GHSL R2023A in both cities** (one modeled method, epoch 2018); LiDAR and municipal heights used only to validate |
| S5-5 | Chicago validation | GHSL built-weighted height vs Cook 2022 LiDAR building height (area-weighted, per area). **Rule:** Spearman ≥ 0.80; level ratios by height class reported. Note: 0.852 was computed earlier, so this rule confirms rather than tests blind |
| S5-6 | São Paulo validation | GHSL built-weighted height vs GeoSampa photogrammetric height (area-weighted per district; 2007/2014). **Rule:** Spearman ≥ 0.80. Overture/OpenStreetMap heights reported descriptively |
| S5-7 | Cross-city bias | Compare GHSL ÷ reference height ratios by height class in both cities, descriptive; a markedly different tall-building bias is flagged for the common stage. Downloading GeoSampa LiDAR 2017 only if S5-6 fails |

### Step 5 results (5 October 2026; S5-1 to S5-7 approved before the run)

[bv_step5_2026_10_05](../../analysis/results/SP_CHI/bv_step5_2026_10_05/README.md).

- **Chicago passes (S5-5):** GHSL built-weighted height vs Cook 2022 LiDAR Spearman 0.852, median ratio 0.95; tall areas compressed (≥ 25 m class 0.59; Loop 42 m).
- **São Paulo fails (S5-6):** vs GeoSampa heights Spearman 0.788; GHSL a median 2.12 times GeoSampa. Against IPTU 2026 floors GHSL implies 4.92 m per floor (GeoSampa 2.39, OpenStreetMap 2.77); GeoSampa tracks floors best (0.925). *(Withdrawn 6 October 2026, see the LiDAR result below: these municipal references understate building height.)*
- **BI confirmed redundant (S5-2):** BI vs BV × built fraction Spearman 0.9999 in both cities.
- Per S5-7, the São Paulo failure brings a GeoSampa LiDAR 2017 sample into scope.

**Decisions needed:** (1) accept Chicago BV for the Chicago contract with stated limits; (2) São Paulo BV for the common stage: keep GHSL with a stated level bias and compare cities only on within-city relative height, or measure the bias with a GeoSampa LiDAR 2017 sample (Brás, Itaim Bibi, one peripheral district) before choosing.

### User decisions (5 October 2026)

Accept Chicago BV; for São Paulo, first measure GHSL's bias with a municipal LiDAR sample, then keep GHSL with the stated bias and compare cities on within-city relative height (C6).

**LiDAR sample (in progress).** GeoSampa publishes a **2020** LiDAR survey (`geoportal:quadricula_folha_mdt_mds_2020`, 5,401 tiles of about 0.31 km², 1:1,000, Fototerra), closer to GHSL's 2018 epoch than the 2017 survey. Tiles must be downloaded through the GeoSampa portal (no direct URL pattern found; the download endpoint answers but its file-type parameter is undocumented). Two tiles wholly inside each district, drawn at random (seed 20261005), listed in `analysis/data/SP/geosampa_lidar_2020/sample_tiles.csv`: Brás 3323-111, 3321-344; Itaim Bibi 3316-312, 3315-262; Cidade Tiradentes 4316-223, 4316-242. Method once files arrive: terrain from MDT points, surface from MDS points (1 m), height above ground within building outlines (per-building 95th percentile, mirroring Cook's maximum-point height), compared with GHSL in the cells inside each tile; reported beside Chicago's GHSL ÷ LiDAR ratios. Descriptive, no pass/fail.

### Acceptance record

**BV (Chicago): accepted with stated limits, 5 October 2026 (user).** Primary `bv_height_built_m`, rows `city == 'CHI'`, entered in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json). BI is not a separate family (it equals BV × built fraction). Stated limits:

1. Modeled height (GHSL epoch 2018, 100 m), not measured.
2. Spearman 0.852 with Cook 2022 LiDAR; GHSL a median 5% lower; tall areas compressed (≥ 25 m class at 0.59 of LiDAR; Loop 42 m).
3. Absolute levels compared across cities under C6: against LiDAR with the same method, GHSL is about 10–15% higher relative to LiDAR in São Paulo than in Chicago within each height class (corrected 6 October 2026; the earlier “1.6–2 times” reading was withdrawn).

### LiDAR result and correction (6 October 2026)

[lidar_sample](../../analysis/results/SP_CHI/bv_step5_2026_10_05/lidar_sample/README.md), script `analysis/scripts/evaluate_bv_lidar_sample.py`; tiles downloaded manually by the user. Same method in both cities (GHSL cell vs footprint-area-weighted LiDAR building height): GHSL ÷ LiDAR median per cell Chicago 1.151 (40,471 cells); São Paulo 1.084 with the same maximum-point statistic as Cook (88 cells; 1.232 with the 95th percentile). By height class Chicago 1.27 / 1.05 / 0.72 / 0.53 and São Paulo 1.47 / 1.17 / 0.81 / 0.65 (< 8, 8–15, 15–25, ≥ 25 m). **GHSL inflates low and compresses tall buildings in both cities; São Paulo is about 10–15% higher within each class.** The 5 October reading (“about 1.6–2 times too high”) is **withdrawn**: it relied on GeoSampa 2007/2014 heights and IPTU floors, which understate LiDAR building height. A bug was found and fixed during this run (GHSL cells read past the raster edge were shifted 19.5 km in Chicago); the reported figures are after the fix.

---

## Step 6 — M1 street density and M6 street hierarchy

### What already exists (context, not tests)

From the [M-family report](../harmonization/M_FAMILY_DECISION_REPORT.md#m1--street-density-and-m6--street-hierarchy), the [M1/M6 review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md), the [street class inventory](../../analysis/results/SP_CHI/street_class_inventory_2026_09_30/README.md) and the [Chicago centerline class review](../../analysis/results/Chicago/chicago_centerline_class_review_2026_09_30/README.md):

- **Locked candidate:** M1 = clipped Overture street length in ten classes (`motorway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `living_street`, `pedestrian`, `unclassified`, `unknown`; links and both carriageways kept; service, alleys, driveways, footways and paths excluded) per **gross** km²; M6 = the ten length shares.
- **Validation already seen:** Overture ÷ municipal street length median 1.048 (Chicago) and 0.936 (São Paulo); Spearman 0.961 and 0.976; six Chicago and seven São Paulo areas outside 0.85–1.15. The upper hierarchy agrees between Chicago's city classes and Overture (classes 1–3 → motorway/primary/secondary/tertiary). Chicago class 4 is a residual (about 80% residential-type).
- **Source scope:** the class rule removes 75% of Chicago's raw Overture road length (footways and service roads are mapped densely there) and 25% of São Paulo's; after the rule Chicago has 7,164 km of eligible Overture streets against 7,171 km in the city file.
- **Lineage (5 October 2026, context):** Overture eligible road length is 97.8% OpenStreetMap and 2.2% TomTom in Chicago, 98.3% and 1.7% in São Paulo: one mapping regime in both cities, unlike buildings.
- **Outliers:** O'Hare (airfield circulation, city class 99) and Marsilac (rural lines missing from Overture).

### Decisions for Step 6 (proposed; need user approval before any test is run)

| ID | Decision | Recommendation and reason |
|---|---|---|
| S6-1 | Street universe | **Overture ten-class in both cities** (one schema, one regime, validated against both municipal networks). Municipal centerlines (Chicago) and `logradouro`/`classvias` (São Paulo) used only to validate; this makes Chicago's class 4 a validation question, not a feature question |
| S6-2 | Denominator | **Land (C2)**, replacing gross area |
| S6-3 | Length rule | Keep the locked rule: exact clipping, links and both carriageways counted (mapped street length, not centreline length); dual-carriageway double counting stated as a limit |
| S6-4 | M6 representation | **One coordinate: share of length in major classes** (motorway, trunk, primary, secondary). Ten shares are too many for one family and mostly near zero; reported in full but not as features. Sensitivity: three groups (major; tertiary; local = residential, living_street, unclassified, pedestrian, unknown) |
| S6-5 | O'Hare and Marsilac | No special rule: both are real (few streets on an airfield or in rural land); flagged, and their influence handled by the transforms set at the final step (C5) |
| S6-6 | Validation rules | M1: Overture vs municipal street length per area (Chicago centerlines status N, classes 1–4, 7, 9; São Paulo `logradouro`), same land support. **Rule:** Spearman ≥ 0.95 in each city; areas whose ratio falls outside 0.80–1.25 are returned for decision. M6: Overture major share vs municipal major share (Chicago classes 1–3, 9; São Paulo `classvias` arterial, coletora, rodovia, VTR). **Rule:** Spearman ≥ 0.80. Note: M1 rank agreement was seen before (0.961 / 0.976), so the M1 rule confirms rather than tests blind |
| S6-7 | Descriptive | Lineage (OpenStreetMap vs TomTom) by area; overlap of M1 with U3 and B1; dual-carriageway share |

### Step 6 results (6 October 2026; S6-1 to S6-7 approved before the run)

[m1_m6_step6_2026_10_06](../../analysis/results/SP_CHI/m1_m6_step6_2026_10_06/README.md), script `analysis/scripts/evaluate_m1_m6_step6.py`. **All four rules pass:** M1 vs municipal street length Spearman 0.958 (Chicago) and 0.975 (São Paulo); M6 major share vs municipal 0.815 and 0.828. Chicago M1 median 13.2 km/km² of land, São Paulo 17.8. Overlap: M1 with U3 0.386 / 0.669, with B1 0.391 / 0.724; M6 nearly independent of M1 (0.262 / 0.042).

**Returned (outside 0.80–1.25):** O'Hare 2.19 (Overture tags airport roads that the city's class 99 excludes); Marsilac 0.61 (rural roads missing from Overture); Parque do Carmo 0.76 (cause not examined). Recommendation: keep Overture values with stated limits; all three are already extreme-low M1 areas.

### Acceptance record

**M1 and M6: accepted with stated limits, 6 October 2026 (user).** Returned areas kept with Overture values. Primary `m1_km_per_km2` and `m6_major_share`, Chicago rows in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json); São Paulo rows kept for the common stage. Stated limits:

1. Mapped street length, not legal access or walkability; divided roads count both carriageways.
2. O'Hare (Overture 2.19 × city file), Marsilac (0.61) and Parque do Carmo (0.76).
3. M6 major share is lower in Overture than in municipal schemes (Chicago 0.22 vs 0.27); ranks agree (0.815 / 0.828).
4. In São Paulo M1 overlaps U3 and B1 (about 0.7); redundancy is handled at the final step (C5).

---

## Step 7 — U1 land-use mix

### What already exists (context, not tests)

From [DECISIONS.md, Loss 3](../DECISIONS.md), the [six-unit developed-use diagnosis](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md) and the attribute definitions ([Chicago](ATTRIBUTES.md), [São Paulo §11](../sp/ATTRIBUTES.md)):

- **Different sources and meanings.** Chicago: CMAP LUI 2023, observed primary use as land-area polygons, eight groups; 27–33% of land in the sampled areas is the generic `6000` nonparcel code (largely right-of-way). São Paulo: fiscal use of cadastral entities (IPTU), seven categories, entity-count primary; 20–25% of land has no lot polygon (streets, public land) and `mixed/other` mixes true mixed use with generic labels.
- **The category set decides the answer.** Brás vs Loop entropy: six classes 0.706 vs 0.735; four occupied classes (residential, commerce/services, industrial, institutional) 0.774 vs 0.662. This is a definition decision, not a tuning.
- **Earlier provisional judgment:** an area-weighted mix of occupied uses on classified parcel land, with unknown, nonparcel, vacant and open land kept explicit as coverage, is the closest common measure. Destination (POI) diversity is a different variable, not U1.
- **Link to C2:** with land minus water as the density denominator, open space and vacant land stay inside U2, U3, M1 and B1; U1 can carry those shares explicitly once, and the final step checks the redundancy.

### Decisions for Step 7 (proposed; need user approval before any value is computed)

| ID | Decision | Recommendation and reason |
|---|---|---|
| S7-1 | What U1 measures | **Mix of occupied uses**: residential, commerce/services, industrial, institutional, **area-weighted on classified lot land**, normalized Shannon entropy (÷ ln 4). Vacant, open space, transport/utilities and right-of-way are not "uses being mixed"; they are reported as land shares |
| S7-2 | Sources | **Chicago CMAP LUI 2023** primary `LANDUSE` (as before). **São Paulo IPTU 2026** use type per physical lot (setor + quadra + lote, or + condomínio), lot area from the GeoSampa fiscal lot polygons. Each city's best observed or declared use; there is no common source at lot level (Overture/OpenStreetMap land-use polygons are coarse and their completeness is unverified) |
| S7-3 | Crosswalk | One written table per city mapping every source code to the four classes or to a named non-occupied class. **Mixed residential + commercial** lots go to commerce/services in both cities (CMAP already codes them so: 1215/1216); a São Paulo condominium lot is mixed if its units include both residential and non-residential use types |
| S7-4 | Coverage | Report per area: classified occupied land ÷ land; vacant, open space, transport/utilities, right-of-way/nonparcel, unclassified and no-lot shares. Entropy is missing (not zero) if classified occupied land is below 10% of land |
| S7-5 | Validation | **São Paulo:** commerce/services share vs the share of CNEFE 2022 addresses that are establishments (independent census address list); **Chicago:** residential share vs the share of Cook Assessor 2024 PINs in residential classes. **Rule:** Spearman ≥ 0.70 in each city; otherwise the cases return. Both are plausibility checks of the use labels, not ground truth |
| S7-6 | Descriptive | Overlap of U1 entropy with U2, U3, B1; the Brás and Loop values under four and six classes (to keep the reversal visible) |

### Step 7 results (6 October 2026; S7-1 to S7-6 approved before the run)

[u1_step7_2026_10_06](../../analysis/results/SP_CHI/u1_step7_2026_10_06/README.md), script `analysis/scripts/evaluate_u1_step7.py`. U1 computed for 76 Chicago and 94 São Paulo units (O'Hare, Marsilac, Parelheiros below 10% classified land). Medians 0.649 (Chicago) and 0.664 (São Paulo). U1 is nearly independent of U3 and B1 in Chicago (0.04, 0.08) and moderately related to U2 (0.36 / 0.35).

**S7-5 failed in both cities** (Chicago 0.390, São Paulo 0.422). Cause: both pre-registered references count units (Cook PINs, 32% condominium units; CNEFE addresses, every apartment) while U1 weights land area. Post-hoc like-for-like diagnostics: Chicago residential share vs Cook ground-parcel land area 0.825; São Paulo commerce share vs CNEFE buildings with an establishment 0.744. Reported as diagnostics, not as a passed test.

**Main limit found:** primary use per lot cannot see vertical mixing, so mixed-use centres read as single-use (República 0.316 and Sé 0.384 are São Paulo's least mixed districts).

Errors found and fixed during the run: the IPTU file was read with the wrong encoding (labels unmapped; fixed before any result was used), and vacant lots fell to "unclassified" because their built area is zero (record-count tiebreak added; U1 unaffected).

### Alternatives to U1: what is done in each neighbourhood (research, 6 October 2026)

User request: a variable for the kinds of buildings and places in a neighbourhood that sees vertical mixing. [Research memo](../../analysis/results/SP_CHI/u1_alternatives_2026_10_06/README.md), script `analysis/scripts/audit_u1_alternatives.py`. Rejected: building-use tags (São Paulo 94.8% untyped in Brás; Chicago 60% untyped), CMAP secondary use (0.37% of land), floor-space mix (no Chicago floor area), Overture places in São Paulo (vs CNEFE Spearman 0.484). Usable: **CNEFE 2022** in São Paulo (every dwelling and establishment, establishments described by enumerators), **Overture places in Chicago** (vs licensed sites Spearman 0.969) with licences as a check. Unit-based face validity: Sé 4th and Brás 2nd of 96 for establishments per 100 dwellings (U1 ranks Sé 93rd); Loop 1st in Chicago.

**Proposal:** an "activity composition" variable from units (non-residential intensity and diversity over five activity groups), piloted under pre-registered checks before deciding between it and U1.

### Step 7b plan — U6 activity composition (user request, 6 October 2026)

**User's point:** entropy alone cannot tell a high-residential from a high-commercial or high-other neighbourhood (both can have the same entropy); the model must also carry *which* classes dominate. Goal: classes defined once for both cities, with each class's share ("value") and the entropy.

**Why shares and not only entropy.** Entropy is invariant to relabelling the classes: 70% residential / 30% commercial and 30% / 70% have the same entropy (0.61 with two classes). The class shares carry the identity. Shares sum to 1, so they are compared through log-ratios (compositional data analysis, Aitchison geometry); entropy is kept as a summary, and its redundancy with the shares is checked at the final step (C5).

**Two levels.** Dwellings outnumber establishments about eight to one in São Paulo (4.99 M vs 0.61 M), so one composition over all units would be almost all "residential". The variable is therefore hierarchical:

| Level | Coordinate | Meaning |
|---|---|---|
| 1 | **Non-residential intensity** = establishments per 100 dwellings (log) | How much non-housing activity sits among the homes (vertical mixing counted) |
| 2 | **Composition of establishments** over five classes (shares; log-ratio coordinates) | Which activities dominate |
| 2 | **Diversity** = normalized entropy of the five shares | How evenly they are spread |

**Classes (proposed):** food & drink; retail; services & offices (personal services, professional, finance, real estate); making & storing (industry, workshops, repair, warehouses, wholesale); institutions (education, health, religious, civic, social). Excluded and reported: vacant premises, parking and garages, unclassifiable.

**Harmonization problems and treatment**

| Problem | Treatment |
|---|---|
| Different instruments: São Paulo CNEFE 2022 (census list, every establishment incl. informal and vacant); Chicago Overture places (provider mix; overall count validated against licences 0.969) | One written crosswalk per source into the five classes; class-level validation in each city; **bridge study in São Paulo**: apply the Chicago instrument (Overture) to São Paulo and compare its class composition with CNEFE, to measure the instrument's class bias (for example, places datasets may favour food and retail over workshops) |
| Level differences (counts depend on the instrument's completeness) | Level 1 intensity is compared across cities under C6 (relative to each city); Level 2 shares are relative by construction and less sensitive to uniform completeness, but class bias is measured in the bridge study |
| CNEFE descriptions are free text | Keyword dictionary (from the description words), hand-audited sample |
| Chicago dwellings | Census housing units, vintage consistent with U3 (decision S7b-5) |
| Zero counts in a class | Small pseudo-count before log-ratios (decision S7b-6); areas with too few establishments flagged |
| A unit is a unit (a kiosk = a store) | Stated limit; floor-area weighting is impossible in Chicago |

**Phases**

| Phase | Work | Output |
|---|---|---|
| A | Freeze classes and write the crosswalks (CNEFE species + description keywords; Overture taxonomy; licence activities) | Crosswalk tables |
| B | Classify CNEFE; hand-check 400 random descriptions | Classifier audit |
| C | Classify Chicago Overture places; class-level check against licences | Chicago validation |
| D | Bridge study in São Paulo (Overture vs CNEFE by class, city and district) | Instrument class bias |
| E | Compute intensity, shares (with log-ratios) and entropy for 173 units; face validity (centres, industrial areas, residential suburbs); overlap with U1, U2, U3 | Feature table |
| F | Decide the roles of U1 and U6; acceptance | Acceptance record |

**Decisions S7b-1 to S7b-8 (approved by the user on 6 October 2026, before any value was computed)**

| ID | Decision | Recommendation |
|---|---|---|
| S7b-1 | Unit of counting | Address units: each dwelling and each establishment counts once (vertical mixing included) |
| S7b-2 | Classes | The five above, plus excluded vacant / parking / unclassifiable reported |
| S7b-3 | Coordinates | Intensity (log establishments per 100 dwellings), five shares as log-ratio coordinates, entropy; one family budget (C5) |
| S7b-4 | Sources | São Paulo CNEFE 2022; Chicago Overture places 2026-08-19.0 with licences as check |
| S7b-5 | Chicago dwellings | ACS 2020–2024 housing units allocated like U3 (consistent with U3) |
| S7b-6 | Zeros and small counts | Pseudo-count 0.5 per class before log-ratios; composition flagged if an area has fewer than 100 classified establishments |
| S7b-7 | Pre-registered checks | V1 São Paulo classifier: ≥ 90% correct and ≤ 15% unclassifiable in a 400-description hand audit. V2 Chicago: Overture food & drink and making & storing counts vs matching licence types per area, Spearman ≥ 0.80. V3 bridge (descriptive): Overture ÷ CNEFE class shares in São Paulo. V4 face validity and V5 overlaps (descriptive) |
| S7b-8 | U1's future | Decided in phase F; meanwhile U1's land shares (residential, commerce, industrial, institutional) are kept as a land-based composition with the same log-ratio treatment, so both families carry identity, not only entropy |


### Step 7b results (6 October 2026; phases B–E)

[u6_activity_2026_10_06](../../analysis/results/SP_CHI/u6_activity_2026_10_06/README.md), script `analysis/scripts/build_u6_activity.py`, crosswalks frozen in `analysis/config/u6/` before the checks.

| Check | Result |
|---|---|
| V1 São Paulo classifier | Accuracy **96.0%** (312/325; audit by Claude, not yet checked by the user): pass. Unclassifiable **15.6%** of establishments: **fails ≤ 15% by 0.6 pt**. District shares 11.7–21.2% (p10–p90), unrelated to intensity (Spearman −0.007) |
| V2 Chicago vs licences | Food & drink **0.980**, making & storing **0.875**: pass |
| V3 bridge (Overture ÷ CNEFE in São Paulo) | Food 0.71, retail 0.87, services **1.73**, making **0.41**, institutions 1.32; district Spearman 0.40–0.85. Chicago's Overture-to-licence ratio is equal for food and making (2.12 each), so the instrument's class bias differs by city: absolute shares are not comparable; composition is read relative to each city (C6) |
| V4 face validity | Intensity: Pari 53.0, Brás 33.4, Bom Retiro 29.5, Sé 24.6 lead São Paulo; Loop 42.7 leads Chicago. Brás retail 48% / making 31%; Loop services 53%; Archer Heights making; Beverly and Alto de Pinheiros institutions |
| V5 overlaps | Intensity vs U2: Chicago 0.71, São Paulo 0.18. Entropy vs U1: 0.28 / −0.04. Entropy saturates in São Paulo (median 0.981; p10–p90 0.94–0.99) |

**Found during phase E:**

- **Chicago places without a taxonomy are mostly noise.**
  - They make up 17.5% of places, concentrated in Kenwood (73%), Hyde Park (60%) and the Lower West Side (52%).
  - Median confidence is 0.21, against 0.92 for places with a taxonomy. 84% come from Meta. The names are non-words or codes.
  - They are excluded. Dropping typed places with confidence < 0.3 as well leaves every ranking in place (Spearman ≥ 0.995).
- **CNEFE appears to miss offices in towers.**
  - Consolação and Bela Vista rank among São Paulo's lowest for intensity.
  - In Consolação, CNEFE lists 18.5 dwellings per building address but only 1.16 establishments per building address.
  - In the same districts, Overture has 3–4 times CNEFE's establishment count, and RAIS has 50–100 jobs per CNEFE establishment (city median 7.5).
  - Across districts, the two independent signals agree: Spearman 0.884.
  - Mechanism (offices on upper floors not listed one by one) is a hypothesis; IBGE's method text was not read.
  - Consequence: in São Paulo, U6 undercounts services and intensity where offices stack vertically.

**Decisions D7b-1 to D7b-5 (proposed; need user approval)**

| ID | Decision | Recommendation |
|---|---|---|
| D7b-1 | V1 coverage failure (15.6% vs ≤ 15%) | Record as **failed**; accept with stated limit (even across districts, unrelated to intensity). A second dictionary round would need a fresh audit sample |
| D7b-2 | Chicago untyped places | Exclude as noise (evidence above); flag areas with more than 30% untyped (Kenwood, Hyde Park, Lower West Side, Lincoln Park, Lake View) |
| D7b-3 | São Paulo instrument, given the office gap | (a) CNEFE with stated limit; (b) Overture in both cities (same instrument, but it misses São Paulo's workshops and informal trade: making 0.41×); (c) **recommended:** before choosing, add an independent arbiter: formal establishments by sector and postcode from RAIS 2022 (the São Paulo analogue of Chicago's licences; availability of postcode in the public file not yet verified), with a pre-registered comparison of CNEFE and Overture counts by class |
| D7b-4 | Coordinates | Log intensity relative to each city; five city-centred log-ratios (`u6_clr_city_*`) as the composition; entropy kept as a descriptive summary (saturates in São Paulo) |
| D7b-5 | U1 and U6 roles (S7b-8) | U6 is the primary "what is done here" family once D7b-3 is settled. U1 is kept only as a land-based horizontal descriptor until the final redundancy review (their entropies correlate 0.28 / −0.04: different variables) |

### User decisions (6 October 2026)

- **D7b-1, D7b-2 and D7b-4** were accepted as recommended:
  - V1 coverage is recorded as **failed** and accepted with its limit.
  - Chicago untyped places are excluded; areas above 30% untyped are flagged.
  - The coordinates are log intensity plus five city-centred log-ratios. Entropy is descriptive only.
- **D7b-3: option (c).** São Paulo's instrument is chosen by a pre-registered test against RAIS 2022 formal establishments (below).
- **D7b-5: the U1 mix score is dropped.** The user's reason: it scores Sé and República among the least mixed districts, where a high score is expected (93rd and 94th of 94).
  - Correction to the stated premise: U1 itself varies widely (p10–p90 0.47–0.85 in Chicago, 0.53–0.85 in São Paulo). What barely varies is U6 *entropy* in São Paulo (0.94–0.99).
  - The drop rests on validity: entropy carries no class identity, and with no view of vertical mixing it ranks the two centres last.
- **U1 land shares kept as a candidate (user, 6 October 2026, option b on Claude's recommendation).**
  - The four land shares (residential, commerce, industrial, institutional) are right where the entropy reads wrong (Sé: 86% commerce land, 7% residential; Beverly: 90% residential). Their labels pass like-for-like checks (0.825 / 0.744).
  - They carry what U6 cannot: land taken by each use (industrial corridors, campuses, rail yards have few establishments but much land).
  - They are renamed **"land-use composition"** and carry no weight.
  - **Pre-registered admission rule for the final review** (fixed before any overlap was computed): a land share is admitted only if its largest absolute Spearman correlation with the U6 coordinates (log intensity, five centred log-ratios), B1 and M1 is **below 0.70 in both cities**. Shares that fail are dropped, with the loss stated.
  - Missing units (O'Hare, Marsilac, Parelheiros: below 10% classified land) follow the common missing-data rule.

### D7b-3 test: CNEFE vs Overture against RAIS 2022 establishments (rules approved by the user on 6 October 2026 before the run)

**Why this test.** CNEFE (census list) and Overture (commercial places) each miss part of São Paulo's activity:
- CNEFE appears to miss offices in towers.
- Overture misses workshops and informal trade.

Neither can judge the other. RAIS 2022 is the employer register: one record per formal establishment, with its sector (CNAE 2.0) and postcode. That is the São Paulo analogue of Chicago's business licences.

| ID | Rule (proposed) |
|---|---|
| RT-1 Reference | RAIS 2022 establishment microdata for São Paulo municipality: establishments with at least one active job on 31 December 2022. Located by postcode with the U2 `area_first` postcode-to-district weights; `UNLOCATED` and unknown postcodes are dropped. (RAIS's own district field is empty, so the postcode route applies) |
| RT-2 Classes | CNAE 2.0 class → five classes by `analysis/config/u6/rais_cnae.csv` (longest prefix wins). It is aligned line by line with the Overture and CNEFE crosswalks and frozen before any count. Parking and households-as-employers are excluded |
| RT-3 Quantities | The model coordinates for each instrument (CNEFE, Overture, RAIS), by district: log of classified establishments per 100 CNEFE dwellings, and the five centred log-ratios (pseudo-count 0.5). Six Spearman correlations per instrument with RAIS, over the 96 districts |
| RT-4 Decision | Keep **CNEFE** unless Overture's mean of the six correlations exceeds CNEFE's by **≥ 0.05**. In that case use **Overture in both cities**. All twelve values reported. A tie goes to CNEFE (census, includes informal activity, same year as RAIS) |
| RT-5 Descriptive | Per-class Spearman; the districts where the CNEFE office gap was found; jobs per RAIS establishment by district |

**Reference data (acquired and checked 6 October 2026; structure only, no comparison run).**
- Source: Base dos Dados `br_me_rais.microdados_estabelecimentos` via `analysis/scripts/fetch_RAIS_estab.py` → `analysis/data/SP/rais_2022_estab/rais_estab_sp_2022.parquet` (sha256 `0849e70f…`).
- 702,834 records. The 314,022 that are not "RAIS negativa" and their 5,390,446 jobs match the city's published 2022 table exactly (`analysis/data/shared/jobs_docs/msp_estabelec_empregos_2022.pdf`).
- 282,689 have at least one active job on 31 December.
- The CNAE 2.0 class is filled for all records. The `distritos_sp` field is empty.
- 98.75% of the 282,689 are placed by the U2 postcode weights.
- Crosswalk `rais_cnae.csv` sha256 `4694501b…`.

**Known biases of the reference** (stated before the result):
- RAIS covers formal employers only, so it shares Overture's formal-economy tilt. That favours Overture in Brás, Pari and Bom Retiro, which is why RT-4 has a margin.
- Some small firms register at their accountant's address, which inflates services in central districts.
- Sole traders without employees (MEI) are absent.

### D7b-3 result (6 October 2026)

`build_u6_activity.py rais_test` → [rais_test.json](../../analysis/results/SP_CHI/u6_activity_2026_10_06/README.md#d7b-3-which-são-paulo-instrument-rais_testjson-rais_test_by_unitcsv).

**RT-3: Spearman with RAIS over 96 districts.**

| | Log intensity | Food | Retail | Services | Making | Institutions | Mean |
|---|---|---|---|---|---|---|---|
| CNEFE | 0.284 | −0.278 | 0.406 | 0.853 | 0.794 | 0.754 | **0.469** |
| Overture | 0.988 | 0.141 | 0.491 | 0.850 | 0.766 | 0.882 | **0.686** |

**RT-4: Overture's mean is 0.217 higher, so Overture is used in both cities.**

**What the RT-5 detail shows:**
- **The office gap is real.** Consolação ranks 95th on CNEFE, 14th on Overture and 12th on RAIS; Itaim Bibi ranks 56th, 4th and 4th.
- **Total counts agree far better for Overture** (0.930 against CNEFE's 0.170).
- **Overture's agreement is not borrowed from RAIS.** 95% of São Paulo's classified places come from Meta, not a registry.
- **Food & drink is weak for both instruments.** Informal bars are invisible to RAIS.

**U6 rebuilt with Overture in both cities.** The CNEFE version is kept as `*_sp_cnefe` and was reproduced byte-identical.
- São Paulo intensity: Sé 1st, Pari 2nd, Pinheiros 3rd, Itaim Bibi 4th, Brás 5th, República 12th.
- Entropy p10–p90 is 0.86–0.95, no longer saturated.
- The confidence < 0.3 sensitivity check gives Spearman ≥ 0.97 in both cities.
- **New overlap to resolve at the final review:** U6 intensity vs U2 is 0.91 in São Paulo (0.71 in Chicago).
- **Stated losses:**
  - workshops and informal trade are under-seen (Brás and Pari read as retail);
  - food & drink is the weakest coordinate in São Paulo;
  - V1 (the CNEFE classifier) no longer feeds the model; CNEFE still supplies São Paulo dwellings.

### Acceptance record

**U6 accepted with stated limits by the user on 6 October 2026** (eighth family in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json); Chicago rows; São Paulo rows kept for the common stage).

- **Coordinates:** `u6_log_intensity` and the five `u6_clr_city_*`. Entropy, shares and dominant class are descriptive.
- **Limits:**
  - a unit is a unit;
  - Overture leans formal and online (workshops and informal trade under-seen);
  - Chicago untyped places are excluded;
  - the provider mix differs by city;
  - food & drink is the weakest coordinate in São Paulo;
  - years differ.
- **Open for the final review:**
  - the overlap of U6 intensity with U2 (0.71 / 0.91);
  - the U1 land-share candidate under its pre-registered admission rule.
- **U1 mix score:** dropped (user decision, 6 October 2026); not in the contract.


---

## Step 8 — M3 block size, M4 block shape, M7 parcel grain

### What already exists (context, not tests)

**M3 and M4: block size and block shape.**
- *São Paulo v2:* municipal *quadra viária* polygons of type `Quadra` (46,801 of 65,720; squares and medians `Praca_Canteiro`, edges, CET and islands excluded). Unweighted median and IQR of log area, compactness and elongation ([SP ATTRIBUTES §4–5](../sp/ATTRIBUTES.md)).
- *Chicago:*
  - There is no official street-block layer. A Chicago-only physical-block protocol ([BLOCKS_M3_M4.md](BLOCKS_M3_M4.md), pilots of 26 September 2026) builds blocks from Cook right-of-way, road edges and LiDAR.
  - It has not converged: motorway islands, a missing named street (West Veterans Place), merged Loop blocks, and no complete independent reference.
  - It cannot be run the same way in São Paulo.
  - 2020 Census blocks follow streets in Chicago but are a tabulation geography.

**M7: parcel grain.**
- *São Paulo v2:* one count per accepted cadastral lot; 1,679,263 lot polygons are cached from U1 (`analysis/work/u1_step7_2026_10_06/sp_lot_areas.parquet`).
- *Chicago:*
  - Cook 2024 parcel polygons are on disk.
  - The 30 September ground-piece study ([chicago_m7_ground_pieces_2026_09_30](../../analysis/results/Chicago/chicago_m7_ground_pieces_2026_09_30/tables/)) found 605,803 ground pieces. Its rule: without `Elevated*` air-rights parcels, polygons overlapping by ≥ 90% merged.
  - The earlier verdict was "not ready under the physical-entity definition". A separately named mapped-parcel statistic needs its own decision.

**Pattern that worked for M1/M6:** the same instrument (Overture streets) and the same rules in both cities, validated against each city's municipal source.

### Decisions for Step 8 (proposed; need user approval before any value is computed)

| ID | Decision | Recommendation and reason |
|---|---|---|
| S8-1 | M3/M4 instrument | **Street faces from the M1 Overture network in both cities.** These are the land areas enclosed by the ten street classes. Service roads and alleys are excluded, so alleys do not split blocks, as in the Chicago protocol. Same instrument and rules in both cities, as for M1/M6. The Chicago-only protocol stays as a research record. Alternatives: (b) official layers (São Paulo quadra viária; Chicago 2020 Census blocks), different instruments with a systematic right-of-way difference; (c) omit M3/M4 with the loss stated |
| S8-2 | Face rules | Polygonize the noded network. Remove water (C2). Each face keeps its **whole** area (never cut by a unit boundary) and enters each unit with a weight equal to its land inside that unit |
| S8-3 | Statistics | **M3:** area-weighted median of ln(face area): the size of the block in which a typical square metre of land sits. Slivers, medians and traffic islands carry almost no weight, so no arbitrary minimum-size rule is needed. **M4:** area-weighted medians of compactness (4πA/P²) and elongation (longest ÷ shortest side of the minimum rotated rectangle). Unweighted medians and IQRs are sensitivities |
| S8-4 | M3/M4 validation | (i) **Like-for-like:** the same code on municipal centrelines (Chicago street centerlines, São Paulo logradouros, as in M1). Spearman ≥ 0.90 for M3 and ≥ 0.80 for each M4 statistic. (ii) **Official blocks**, M3 only: São Paulo quadra viária `Quadra` and Chicago 2020 Census blocks, same weighting, Spearman ≥ 0.80. Stated dependency: OpenStreetMap roads in the US partly descend from TIGER, the Census line source |
| S8-5 | M7 definition | Renamed **mapped ground-parcel density** (parcels per km² of land). São Paulo: fiscal lot polygons, one per lot, a condominium lot counted once. Chicago: Cook 2024 ground pieces as defined on 30 September. Assigned by representative point. Sensitivity: median ln(parcel area) |
| S8-6 | M7 validation | Record consistency, not independent truth. Chicago ground pieces vs distinct 10-digit PIN prefixes in the Assessor 2024 universe, per area. São Paulo lot polygons vs distinct IPTU lots (sector, block, lot) per district. Spearman ≥ 0.95 in each city; otherwise the cases return |
| S8-7 | Missing and edge cases | O'Hare (DuPage part has no Cook parcels): M7 flagged and left to the common missing-data rule. Faces crossing the city boundary keep their whole area. No imputation (C4) |
| S8-8 | Descriptive | Overlap of M3 with M1, which is expected to be strong (in a grid, block area ≈ 1 ÷ street density²), and of M7 with M3, B1 and U3. Brás and Loop values. Redundancy is decided at the final review (C5) |

### Step 8 results (6 October 2026; S8-1 to S8-8 approved before the run)

[m3_m4_m7_step8_2026_10_06](../../analysis/results/SP_CHI/m3_m4_m7_step8_2026_10_06/README.md), script `analysis/scripts/evaluate_m3_m4_m7_step8.py`.

| Check | Chicago | São Paulo |
|---|---|---|
| M3 vs municipal-centreline faces (≥ 0.90) | 0.959 pass | **0.563 fail** |
| M4 compactness / elongation vs municipal faces (≥ 0.80) | 0.889 / 0.810 pass | **0.335 / 0.499 fail** |
| M3 vs official blocks (≥ 0.80) | 0.831 pass (2020 Census blocks) | **0.977** pass (quadra viária) |
| M7 vs records (≥ 0.95) | 0.998 pass | 0.998 pass |

**What the results show:**
- **Why São Paulo fails:**
  - Faces built from the municipal street lines (logradouros) are 5–44 times larger than Overture's in some central districts (Brás 9.9×).
  - In a central test box, 838 municipal line ends stop short of another line, against 149 for Overture, so blocks merge.
  - The same Overture faces agree with the official blocks at 0.977.
- **Chicago's grid is nearly uniform.** The typical block is about 23,500 m² (p10 20,600), shaped as a 2:1 rectangle. M4 barely varies (compactness p10–p90 0.59–0.70).
- **Weighting matters.** Area-weighted and unweighted M3 are almost unrelated (0.07 / −0.13).
- **Overlaps:**
  - M3 vs M1: −0.54 in Chicago, **−0.90** in São Paulo.
  - M7 vs M3: −0.73 / −0.76.
- **Post-hoc diagnostic** (after the failure, not a test):
  - São Paulo municipal-line faces vs official blocks: **0.604**, against **0.977** for Overture. The municipal reference is the outlier.
  - Overture M4 vs official quadras: compactness 0.911, elongation 0.805.

**Decisions D8-1 to D8-3 (proposed)**

| ID | Decision | Recommendation |
|---|---|---|
| D8-1 | M3 | Accept with stated limits. Record São Paulo's like-for-like check as **failed**, with the diagnosed reference defect; the official-block check passes 0.977 / 0.831. Limits: centreline faces include half-streets; grade separation ignored; near-redundant with M1 in São Paulo (−0.90), for C5 |
| D8-2 | M4 | Accept compactness and elongation with stated limits. São Paulo's municipal check **failed**; post-hoc agreement with official blocks is 0.911 / 0.805. Little variance inside Chicago's grid (compactness p10–p90 0.59–0.70) |
| D8-3 | M7 | Accept as **mapped ground-parcel density** (checks 0.998 / 0.998). Limits: record consistency, not truth; condominium towers count once (the Loop reads coarse); O'Hare flagged (its DuPage part has no Cook parcels) |

### Acceptance record

**M3, M4 and M7 accepted with stated limits by the user on 6 October 2026** (D8-1 to D8-3 as recommended; the user's "ok, let's proceed"). Chicago rows are in [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json); São Paulo rows are kept for the common stage. São Paulo's M3/M4 like-for-like failures stay recorded as failed, with the reference-defect diagnosis.

---

## Final joint review (opened 6 October 2026)

### What is in hand (context, not tests)

**Contract.** [chicago_model_v1.json](../../analysis/config/chicago_model_v1.json) holds **11 accepted families, 17 columns**, with no missing Chicago value.

| Domain | Families (columns) |
|---|---|
| Street morphology | M1 (1), M3 (1), M4 (2), M6 (1), M7 (1) |
| Built form | B1 (1), BV (1) |
| Use and activity | U2 (1), U3 (1), U4 (1), U6 (6: log intensity + five city-centred log-ratios) |

**Candidate.** U1 land shares (4 columns, pre-registered admission rule). O'Hare has no U1 value.

**Flags carried by the families:**
- U3: Burnside and Fuller Park over the 12% CV gate; O'Hare allocation.
- U6: Oakland, Burnside and Riverdale under 100 establishments; five areas over 30% untyped.
- M7: O'Hare (DuPage part).

**Distribution shape** (computed while drafting J-6, before any distance). Under robust median/IQR scaling, several columns have near-zero IQR because Chicago's grid is uniform:
- M4 compactness: IQR 0.016; 16 areas beyond 3 IQR units; maximum 18.8 (Riverdale).
- M4 elongation: IQR 0.043 on the log scale; 16 areas beyond 3 IQR units; maximum 12.9.
- M3: 8 areas beyond 3 IQR units; maximum 11.0 (O'Hare).
- M7: 5 areas beyond 3 IQR units; maximum 9.0.

Robust scaling (the São Paulo v2 precedent) would therefore inflate rounding-level differences inside the grid and let these columns dominate the distances of non-grid areas.

**Out of scope here:** C6 (cross-city levels) and any comparison with Brás belong to the common stage.

### Decisions J-1 to J-10 (proposed; need user approval before any distance is computed)

| ID | Decision | Recommendation and reason |
|---|---|---|
| J-1 | What the fit produces | A **77 × 77 dissimilarity matrix** of Community Areas and, for each area, its five nearest neighbours with each family's contribution. Target-free: any ranking (for example, around one area) or typology is read from it. The STATUS plan asks for rank stability "within Chicago"; Brás belongs to the common stage |
| J-2 | Feature set | The 11 accepted families (17 columns) as frozen, plus the U1 land-share candidate only if it passes J-3 |
| J-3 | U1 land-share candidate | Apply the rule already fixed: a share is admitted only if its largest absolute Spearman with the U6 coordinates, B1 and M1 is below 0.70 **in both cities**. An admitted U1 is one family |
| J-4 | Redundancy among accepted families | Spearman between the primary columns of every pair of families on the 77 areas (U6: intensity). Where \|ρ\| ≥ **0.90**, the two families **share one budget** (half each) instead of one being dropped. Known before the rule: U6 intensity vs U2 0.71, M3 vs M1 −0.54 in Chicago |
| J-5 | Transforms | Natural log for strictly positive ratio-scale quantities: U2, U3, U4, M1, M7, BV height, M4 elongation. Identity for shares, log-ratios and indices: B1, M6, M4 compactness, M3 (already ln), U6 |
| J-6 | Scaling | **z-score on the 77 areas after transform, capped at ±3.** The standard deviation includes the tail that carries the real variation of grid-uniform columns, and the cap stops one extreme value (O'Hare, Riverdale) from dominating. Sensitivities: robust median/IQR (precedent) and rank normal scores |
| J-7 | Budgets and distance | **Equal budget per family.** Within a family, Euclidean distance on its scaled columns, divided by the family's median positive pairwise distance, so that families contribute alike. Total = weighted sum. U6 = ½ intensity + ½ composition, where composition uses Aitchison distance on its unscaled log-ratios (z-scoring log-ratios one by one breaks compositional geometry). M4 = ½ compactness + ½ elongation |
| J-8 | Missing data and flags | No Chicago value is missing in the accepted families. Flags are published with results, never imputed (C4). If U1 is admitted, pairs involving O'Hare use the families both areas have, with budgets renormalized |
| J-9 | Pre-registered sensitivities and stability | Leave-one-family-out (11 runs); equal budget per domain; 500 weight draws (each family × uniform 0.5–1.5, renormalized, seed 20261006); scaling variants (J-6); metric variants (regularized Mahalanobis, PCA-Euclidean); the recorded family sensitivities (M3 unweighted, U6 confidence ≥ 0.3, M7 median parcel size, BV volume). **Publication rule:** a neighbour is reported as **stable** if it stays in an area's top five in ≥ 80% of weight draws |
| J-10 | Freeze and authorization | After J-3 and J-4 run: freeze `chicago_model_v1` (columns, transforms, scaling, budgets, hashes), set `fit_authorized = true`, run the fit once, and report results with the J-9 sensitivities. Any later change is `chicago_model_v2` |

### User decisions (6 October 2026)

**J-1 to J-10 approved as recommended.** The user also asked for three runs and a final model report with a notebook in the style of `analysis/model_analysis.ipynb` (same plots and tables). The runs are defined here **before any correlation or distance was computed**:

| Run | Definition |
|---|---|
| **R1: equal weights** | J-4 to J-8 as approved. Distance D² = Σ over blocks of w_b · mean_c(Δx²) / b_b, where b_b is the block's median positive pairwise value and w_b the family budget (U6 split ½ intensity, ½ Aitchison composition). This is the São Paulo v2 implementation (weighted Euclidean). It gives an exact Euclidean embedding, which the PCA and clustering steps need |
| **R2: PCA weights** | As in `model_analysis`. PCA of the centred R1 embedding; keep the fewest components reaching ≥ 90% cumulative variance; Euclidean distance on the unwhitened retained scores |
| **R3: without correlated features** | Spearman among the 12 scalar columns (U6 intensity, both M4 columns and the other ten families). The U6 composition block stays: it is a composition, not a scalar. While any pair has \|ρ\| ≥ **0.70** (the U1 admission bar), drop the column with the most such pairs; ties go to the higher mean \|ρ\| with the remaining columns, then to the later contract position. Equal budgets over the surviving families |

**Display choice (not a model parameter).** Target-based views (top 10, contribution bars, radar, maps, rank shifts) use **the Loop (CHI:32)** as reference, the Chicago anchor used throughout this plan. The notebook's `TARGET` can be set to any area. Target-free outputs (77 × 77 matrix, every area's top five, stability) do not depend on it.

### Final review results and fit (6 October 2026)

[Model report](MODEL_REPORT.md) · notebook `analysis/chicago_model_analysis.ipynb` · code `analysis/scripts/chicago_model.py` · outputs [chicago_model_v1_2026_10_06](../../analysis/results/Chicago/chicago_model_v1_2026_10_06/README.md).

**Pre-registered checks.**
- **J-3:** U1 residential, industrial and institutional land shares admitted. Commerce is not admitted (0.708 with U6 intensity in São Paulo).
  - O'Hare's U1 is missing (4.9% classified land; the S7-4 coverage rule extended to the shares). Pairs involving O'Hare use the 11 families both areas have (J-8).
- **J-4:** no pair at |ρ| ≥ 0.90; no budgets merged.

**Contract.** Frozen with 12 families (20 columns), `fit_authorized = true`.

**Implementation note.** R2 principal components are computed from the R1 distance matrix (principal-coordinate analysis). This is identical to PCA of the embedding when every area has every family (asserted in the code). It also places O'Hare.

**Runs.**
- **R1, equal weights.** The Loop's top five: Near North Side, Near West Side, Near South Side, Uptown, Hyde Park. They are identical in R2 and R3 and stable in ≥ 86.8% of weight draws.
- **R2, PCA weights.** Four components (91.0%): PC1 grain 64.2%, PC2 centrality 17.3%. Agreement with R1: 0.990 over all pairs; 72% of top fives shared.
- **R3, without correlated features.** Dropped BV, M3, B1 and U2, so built form leaves the model. Agreement with R1: 0.963; 72% of top fives shared.

**Stability and sensitivities.**
- 80.8% of top-five relations are stable under 500 weight draws.
- Leave-one-family-out agreement is 0.959–0.998.
- The model is sensitive to M3 unweighted (0.757), rank scaling (0.870) and Mahalanobis (0.858).

**Caveats found at the fit, reported and not corrected (a correction would be v2):**
- **M3 weighs more than its budget.** Calibration by the median pairwise value is tiny for grid-uniform M3, so M3 carries 19.3% of D² on average against a nominal 8.3%, and over half of D² in 579 of 2,926 pairs. A post-hoc mean calibration keeps 83% of top fives.
- **The ±3 cap hides extremes.** The Loop and Near North Side read identical on jobs and height.

---

## Cross-city model `sp_chicago_model_v1` (opened 6 October 2026)

**User request.** The model the user asked for is the **São Paulo–Chicago model** with Brás as reference (like `analysis/model_analysis.ipynb`): the same notebook, report and three runs as above. The Chicago-only fit stays as a step. J-1's "Brás belongs to the common stage" was Claude's misreading of the request.

**C6 decision (user, 6 October 2026).**
- **Primary: hybrid.** A family is compared on **absolute levels** (pooled standardization) when both cities use the same instrument validated in both. It is compared on **position within its own city** (standardization within each city) when the instruments differ.
- **Two extra runs:** all-absolute and all-relative.

**Design (fixed before any cross-city value was computed).**

| ID | Rule |
|---|---|
| X-1 Units and reference | 173 units (96 São Paulo districts, 77 Chicago Community Areas). Reference **Brás (SP:10)**. Outputs: ranking of the 172 others; ranking of the 77 Chicago areas (the cross-city answer); ranking of the 95 other São Paulo districts; five nearest neighbours of every unit |
| X-2 Features | The 12 families and 20 columns of `chicago_model_v1`, same definitions. São Paulo rows from the same accepted tables; U3 São Paulo from the S3-0 catch-up (`u3_sp.parquet`, Census 2022 per km² of land). U1 coverage rule: Marsilac, Parelheiros and O'Hare missing (J-8 available-case distance) |
| X-3 Transforms | As J-5 |
| X-4 Scaling (C6) | z-score with population SD, capped at ±3. **Absolute (pooled over 173):** M1, M3, M4, M6, M7, B1, U3. **Relative (within each city):** U2, U4, BV, U6 intensity, U1. U6 composition: city-centred log-ratios (relative). All-absolute: every column pooled, and U6 composition uses the raw log-ratios. All-relative: every column within its city |
| X-5 Budgets and distance | As J-7 and J-8; calibration = median positive value over all 14,878 pairs |
| X-6 Runs | For each scaling (hybrid, all-absolute, all-relative): **R1** equal weights, **R2** PCA weights (fewest components ≥ 90%), **R3** without correlated features. R3 Spearman is computed on the 173 scaled columns as that scaling defines them; same pruning rule as before (\|ρ\| ≥ 0.70) |
| X-7 Robustness (hybrid R1) | 500 weight draws (×U(0.5, 1.5), seed 20261006) with the 80% stability rule; leave-one-family-out (covers dropping each different-instrument family); the J-9 alternatives (scaling method, Mahalanobis, M3 unweighted, M7 median parcel size, BV volume, U6 confidence ≥ 0.3) |
| X-8 Display | Brás-based views as in `model_analysis` (contributions, maps of both cities, radar against the top Chicago match, PCA, truncated-PCA rank shifts, Ward clusters on 173 units) |
| X-9 Contract | New `analysis/config/sp_chicago_model_v1.json`, referencing the accepted tables and hashes; fit authorized by this decision |

### Cross-city results (6 October 2026)

[Cross-city model report](../harmonization/MODEL_REPORT.md) · notebook `analysis/sp_chicago_model_analysis.ipynb` · code `analysis/scripts/sp_chicago_model.py` · outputs [sp_chicago_model_v1_2026_10_06](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/README.md).

**Brás's closest Chicago areas (hybrid R1):** West Town, Avondale, Logan Square, Lincoln Park, Lower West Side.
- The first four are stable in ≥ 92% of 500 weight draws; Lower West Side in 55.8%.
- The nearest Chicago area ranks 11th among all 172 units; the first ten are São Paulo inner-ring districts (Belém, Bom Retiro, Lapa, Cambuci, Mooca, …).
- The Loop ranks 69th of 77 Chicago areas.

**Robustness across runs.**
- West Town is in Brás's Chicago top three in all nine scaling × run combinations.
- All-absolute brings in Near North Side; all-relative puts Lower West Side and McKinley Park first.
- The other city's share of each unit's nearest five: 7% (absolute), 11% (hybrid), 24% (relative).

**PCA and clusters.**
- PC1, grain, carries 55.1%; PC2, residential vs central-arterial, carries 19.2%.
- Five components carry 90.3%.
- Ward k = 4 clusters cross both cities.

**Caveats.**
- M3 carries 18.9% of D² (nominal 8.3%).
- Mahalanobis gives a different similarity (0.737; keeps 1 of Brás's Chicago top five).

---

## Cross-city model v2: U1 commerce share (8 October 2026)

**User decision.** Add the U1 **commerce** land share to the cross-city model although it failed J-3 (|Spearman| 0.708 with U6 intensity in São Paulo; rule < 0.70 in both cities). Reason: commercial land is central to Brás's profile and its "essence" (65.0% of its occupied land, 3rd of 94 São Paulo districts). The redundancy with U6 is accepted and reported, not corrected.

**Design (fixed before the v2 fit).**

| ID | Rule |
|---|---|
| V2-1 Version | New contract `analysis/config/sp_chicago_model_v2.json`. v1 and its results stay unchanged and reproducible (`SP_CHI_MODEL_VERSION=v1`) |
| V2-2 Columns | U1 = `p_residential`, `p_commerce`, `p_industrial`, `p_institutional` from the same accepted table (same SHA-256); 21 columns. Same coverage rule: O'Hare, Marsilac and Parelheiros have no U1 |
| V2-3 Everything else | As X-1 to X-9: transforms, C6 hybrid (U1 relative) and the two variants, median calibration, equal family budgets, R1–R3, robustness |
| V2-4 Within-family weights | Equal in the published fit (each U1 share a quarter of U1's budget). Tools may let users set column weights $v_j$: the block becomes $\sum_j v_j \Delta_j^2 / \sum_j v_j$ and its calibration is recomputed, so column weights change only the mix inside a family and the family weight keeps its meaning. $v_{commerce} = 0$ must reproduce v1 exactly |
| V2-5 Scope | Cross-city model only. The Chicago-only model (`chicago_model_v1`) has no Brás reference and is unchanged |

**Results (8 October 2026).** [Report §11](../harmonization/MODEL_REPORT.md#11-version-2-u1-commerce-share-8-october-2026) · outputs [sp_chicago_model_v2_2026_10_08](../../analysis/results/SP_CHI/sp_chicago_model_v2_2026_10_08/README.md).
- Agreement with v1 over all pairs 0.9996; 97.5% of top-five neighbours shared.
- Brás's closest Chicago areas: West Town, Avondale, Logan Square, Lincoln Park (all ≥ 99.8% of weight draws) and North Center (27.0%: not firm); Lower West Side moves from 5th to 7th.
- U1 carries 18.2% of Brás–West Town's $D^2$ (v1: 15.0%) and 6.4% of $D^2$ over all pairs.
- PC2 now loads the commerce share (−0.75). Under all-absolute scaling R3 prunes the commerce share itself (0.76 with BV height).
- Checks: V2-4 holds (commerce weight 0 reproduces v1 to 2.2e-10 in the explorer and 2.2e-15 in Curio lane H).
