# Chicago model Step 1: U3 resident density

Run 2 October 2026 by `analysis/scripts/evaluate_chicago_u3_step1.py` (about 2 min). Plan, definitions and decision rules (all fixed by the user before the run) are in [MODEL_PLAN.md](../../../../docs/chicago/MODEL_PLAN.md#step-1--u3-resident-density). **U3 is not accepted until the user signs the acceptance record. Two pre-registered rules returned cases for a user decision (S1-7 O'Hare, S1-8 Fuller Park and Burnside).**

## Definition (primary)

`U3 = ACS 2020–2024 5-year residents allocated to the Community Area ÷ land (km², area minus municipal hydrography)`.

- Residents: table B01003 (total population) by block group, 2020 geography. Pooled sample, 1 January 2020 to 31 December 2024; not a 2024 count.
- Allocation (S1-7 a): each block group's estimate goes to its 2020 blocks by their 2020 population share; each block goes to areas by the land share of its pieces (S1-3). 2020 decides only *where inside a block group* people live.
- Margin of error (S1-8): area MOE = √Σ(weight × block-group MOE)², the Census approximation for derived sums. It ignores correlation between block groups, so it understates uncertainty.

## Results

| Check | Rule (fixed in advance) | Result |
|---|---|---|
| Land support | equals release `hydro_land_m2` | max difference 0.0 m² |
| ACS inputs | all block groups present, valid margins | 2,316 of 2,316; no special or negative margins; 4 block groups have 0 residents in both 2020 and ACS (nothing to split) |
| ACS mass | inside + outside city = block-group total | 2,710,782.56 + 192,402.44 = 2,903,185 **pass** (edge block groups extend outside the city) |
| **S1-8 uncertainty** | every area CV ≤ 12% | **2 areas above, returned to the user:** Burnside (CHI:47) 16.8%, Fuller Park (CHI:37) 14.2%. Median CV 5.1%; next highest Riverdale 11.3%, Hegewisch 11.0% |
| **S1-7 allocation** (a) 2020-block split vs (b) block-group land split | every area within 5% and fewer than 5 ranks | **1 area returned to the user:** O'Hare (CHI:76) +9.5% under (b), rank unchanged (77th). All others within 1.44%; Spearman 0.99987 |
| U3-2 block → area allocation (2020 count, land vs gross) | within 5%, fewer than 5 ranks | pass: max 0.44%, 1 rank |
| U3-3 mass and coverage (2020 count) | conserved; uncovered ≤ 0.1% | pass: 2,746,058.90 + 36,420.10 = 2,782,479; 0.002% uncovered |
| S1-2 gross-area sensitivity (2020 count) | reported | Spearman 0.9988; no area moves 5 or more ranks |
| S1-9 period comparison | descriptive; list areas differing from the 2020 count by more than 10% | see below |

**U3 (ACS):** median 4,488 residents/km² of land, range 424 (O'Hare) to 15,688 (Near North Side). Highest: Near North Side, Lake View 12,698, Edgewater 12,576. Lowest: O'Hare, South Deering 554, Hegewisch 822. The 90% interval of the median area spans 8 rank positions (maximum 16).

**Returned cases in detail**

- *Fuller Park* 2,319 ± 540 residents (90%), U3 1,255 [962, 1,547]; *Burnside* 2,305 ± 635, U3 1,461 [1,058, 1,864]. Both are the two smallest populations; their intervals each contain only 3 areas' point estimates, so the uncertainty does not change their place among the lowest-density areas.
- *O'Hare:* 14,403 residents under (a), 15,775 under (b). The land split gives residents to block-group land that is airport; (a) puts them where 2020 blocks had residents. U3 424 vs 465; last under both.

**S1-9 period comparison (descriptive).** City: ACS 2020–2024 is 1.28% below the 2020 count (2,710,783 vs 2,746,059). Spearman between the two U3 versions 0.9947; 5 areas move 5 or more ranks (Lincoln Square 26→21, Garfield Ridge 57→52, Brighton Park 20→26, New City 51→56, Greater Grand Crossing 52→58). Listed for map review (more than 10% from the 2020 count): West Garfield Park −13.4% (difference 2,334, MOE 1,386), Calumet Heights −14.2% (1,859, MOE 1,383), Hegewisch −11.3% (1,134, MOE 1,599, so within the margin).

**Supplied ACS aggregate (provenance unresolved):** not the 2020–2024 5-year release. Per area it differs from it by a median 3.3% and up to 36.9%; citywide −2.3%. It stays unexplained and is not used.

## Limits

Population pooled over 2020–2024, per km² of land, at Community Area level; not daytime population. Within each block group the 2020 distribution is assumed. Margins understate uncertainty (no covariance). Land includes parks, vacant land, cemeteries and the airport (C2), so U3 also carries how much land is empty; the final joint review must check that against U1 and the other densities. Municipal hydrography covers the city only.

## Files

- `tables/u3_step1.csv|parquet`: per area. Primary `u3_acs_land_km2` with `u3_acs_lo90`/`u3_acs_hi90`, `acs_residents_a`, `acs_moe90_a`, `acs_cv_a`, `rank_span_90`; sensitivity `u3_acs_b_land_km2`; 2020 count versions `u3_land_km2` (land allocation), `u3_alloc_a_land_km2`, `u3_gross_km2`; comparisons.
- `checks.json`: every check with its numbers.
- `source_register.json`: C3 entries (source, release, observation period, SHA-256) including the ACS files, and hashes of derived inputs.
