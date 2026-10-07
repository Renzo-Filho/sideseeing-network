# M2 redundancy and SP v2 omission recheck (30 September 2026)

Run `analysis/scripts/review_m2_redundancy_2026_09_30.py`. It reads only published tables (no raw data, no fit) and writes `summary.json`, `m2_spearman.csv` and `m2_rank_r2.csv`.

**Inputs are the existing proxies, not the draft [pedestrian-junction convention](../../../../docs/harmonization/M2_JUNCTION_CONVENTION.md).**
- SP M2 is the v2 5 m planar proxy (`intersection_density_proxy_5m_km2`, 96 districts); M1, M3, M4 and M7 come from the same SP v2 attribute table (M3/M4 use municipal Quadra blocks).
- Chicago M2 is the unaccepted endpoint diagnostic (`m2_endpoint_candidates.csv`, 77 areas); M1 is municipal street density; M3/M4 are **experimental** centerline enclosures; B1 is municipal footprint coverage on land.

All densities divide by gross area.

## 1. SP v2 omission figure reproduces

From the stored `scenario_rankings.csv` (95 districts ranked by distance to Brás), Spearman between baseline and `without_M2` ranks is **0.991545**, identical to the stored summary. 9 of the top 10 neighbours are retained and the maximum rank shift is 14.

M2 is nevertheless **not a small contributor** to those distances. Its mean share of squared distance to Brás is **7.46%**, the fourth largest of 13 families (U1 22.3%, B1 13.7%, U4 12.7%); median 5.6%, maximum 23.9%. A large contribution with a small omission effect means the ranking information M2 carries is largely duplicated by other families.

## 2. Spearman correlations of M2 with other families

| Other family | SP (5 m proxy) | Chicago (endpoint diagnostic) |
|---|---:|---:|
| M1 street density | **0.864** | **0.948** |
| M3 block log-area median | −0.366 | −0.342 (experimental) |
| M3 block log-area IQR | −0.364 | 0.178 (experimental, p = 0.12) |
| M4 compactness median | 0.133 (p = 0.20) | −0.088 (experimental, p = 0.45) |
| M7 parcel density | 0.800 | — |
| B1 building coverage, land | 0.505 | 0.439 |
| U3 population density | 0.617 | — |
| U2 job density | 0.046 (p = 0.66) | — |

## 3. How much of the M2 ranking other rankings explain

R² of ranked M2 on ranked predictors (OLS with intercept):

| Predictors | SP | Chicago |
|---|---:|---:|
| M1 | 0.747 | 0.899 |
| M3 (Chicago: experimental) | 0.134 | 0.117 |
| M1 + M3 | 0.822 | 0.900 |
| SP: M1 + M3 + M7 | 0.851 | — |
| SP: M1 + M3 + M7 + B1 + U3; Chicago: M1 + M3 + B1 | 0.876 | 0.906 |

## 4. The overlap is not an artifact of the shared denominator

M1 and M2 both divide by gross area, which can create correlation by itself. Removing log gross area from the log counts (junction count, street km) leaves a correlation of **0.942 (SP)** and **0.958 (Chicago)**. These are essentially equal to the log-density correlations (0.945, 0.963). Districts with more street length per area have more junctions, independent of district size. The developed-land denominator could change this only if it reweights districts differently from gross area; that is not testable until the support is defined.

## 5. What M1 does not carry

`junctions_per_street_km` = M2 ÷ M1 is the number of junctions per kilometre of street, the inverse of the mean distance between junctions. It removes M1's level by construction.

| | SP | Chicago |
|---|---:|---:|
| vs M3 block log-area median | **−0.580** | −0.140 (experimental, p = 0.22) |
| vs M7 parcel density | 0.582 | — |
| vs M1 | 0.392 | 0.560 |
| vs B1 | 0.087 (p = 0.40) | 0.524 |

In SP this residual dimension tracks block size, as theory expects: smaller blocks mean junctions closer together along each street. In Chicago it does not track the experimental M3, which is itself unaccepted, so no conclusion can be drawn about Chicago.

## Reading (inference; nothing is accepted)

- For both existing proxies, M1 alone explains about **75% (SP) to 90% (Chicago)** of M2's ranking. Adding M3 brings SP to 82%.
- The information M2 adds beyond M1 is mainly junction spacing along streets (junctions per street km). In SP that is partly block grain (M3).
- This matches the 0.9915 omission result: M2 weighs a lot in distances, but its ranking signal is mostly repeated by M1 and M7.
- **Limits:** these are the old proxies. A pedestrian-junction count under the draft convention removes divided-road duplicates and excludes motorway nodes, so it could correlate more or less with M1; that cannot be known without building it. Chicago M3 is experimental. n = 96 and 77; correlations are not causal and say nothing about which family is "correct". Nothing here is a fit, contract or acceptance.
