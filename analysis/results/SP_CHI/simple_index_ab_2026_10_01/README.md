# Methodology report: advisor's composite index (A) vs corrected index (B) — 1 October 2026

Protocol **P-AB-1**, fixed in [docs/SIMPLE_INDEX.md](../../../../docs/SIMPLE_INDEX.md) before any A or B value was computed. Units: 96 São Paulo districts and 77 Chicago Community Areas (173). Every number below is in `tables/`, `checks.json` or `summary.json`, produced by one run of:

```bash
.venv/bin/python analysis/scripts/build_simple_index_ab.py
```

Run: about 1 min 50 s, peak 1.6 GB (`run_log.txt`); code and input SHA-256 in `summary.json`. To inspect step by step, open [`analysis/simple_index_ab.ipynb`](../../../simple_index_ab.ipynb), which calls the same functions and asserts that it reproduces these tables.

## 1. The two methods

```
index = C + R + H + V + N + L        (each factor min–max scaled over the 173 units; equal weights; range 0–6)
```

| Factor | Method A (advisor, as specified) | Method B (corrected) |
|---|---|---|
| C commercial establishments | Overture Places, taxonomy top level shopping / food_and_drink / services_and_business / lifestyle_services / lodging, counted per unit | C ÷ land km² |
| R residential establishments | Dwellings: SP CNEFE 2022 private dwellings; Chicago Census 2020 housing units (blocks split by area share) | R ÷ land km² |
| H transportation hubs | Metro/subway stations + bus stops (CTA; SPTrans, CPTM excluded) | H ÷ land km² |
| V building height | Mean Overture `height` of buildings with height | GHSL built volume ÷ built surface |
| N number of streets | Overture road segments, M1 ten classes, assigned whole by midpoint | N ÷ land km² |
| L average street length | Mean length of those segments | same as A |

Land = unit minus municipal hydrography. Source choices and their validation: [source audit](../simple_index_source_audit_2026_10_01/README.md) and [places coverage test](../places_cnefe_coverage_2026_10_01/README.md).

## 2. Construction checks (20 of 20 passed; `checks.json`)

| Check | Result |
|---|---|
| Commercial counts, two independent point-in-polygon routes | identical in every unit, both cities |
| Commercial counts vs the earlier source audit | identical in every unit |
| SP dwellings | 4,992,162 assigned = CNEFE private-dwelling total |
| Chicago dwellings | 39,498 blocks intersect the city with 1,278,961 housing units; 1,262,056.0 allocated to units, 16,905.0 outside the city; no block over-allocated; the same weights reproduce the published U3 population exactly |
| Buildings with height assigned | Chicago 749,136, SP 2,080,386 = audit totals |
| GHSL height recombined from volume and surface | reproduces the stored values (relative difference < 1e-9) |
| Completeness, scaling, index | 173 units, no missing value; every scaled factor spans exactly 0–1; index = sum of scaled factors |

Totals per city: commercial places Chicago 73,672 / SP 301,655; stations in units 123 / 100; bus stops in units 9,867 / 21,978; road segments 53,329 / 190,348.

## 3. Test results

### T1 — boundary invariance (decisive test)

**Question.** If two neighbouring districts are reported as one unit, does the factor give a value consistent with its parts? A measure of urban intensity must: a merged area cannot be more intense than its most intense part. The 96 SP districts were merged into their subprefeituras; 29 of the 32 contain two or more districts.

| Factor | A: merged value within its districts' range | A: merged ÷ largest district, median (max) | B: within range |
|---|---:|---:|---:|
| C commercial | 0 of 29 | 2.32 (4.55) | 29 of 29 |
| R residential | 0 of 29 | 2.49 (5.18) | 29 of 29 |
| H hubs | 0 of 29 | 2.29 (5.68) | 29 of 29 |
| V height | 29 of 29 | — | 29 of 29 |
| N streets | 0 of 29 | 2.41 (6.61) | 29 of 29 |
| L street length | 29 of 29 | — | 29 of 29 |
| **Index** | **0 of 29** | **2.14 (4.29)** | **28 of 29** |

Verdict by the pre-registered criterion (≥ 95%): in method A, four of six factors and the index **depend on how boundaries are drawn**; in method B every factor and the index are **boundary-invariant**.

**Why this is a proof, not only a measurement.** For a count, the value of a merged unit is the sum of its parts, so it always exceeds the largest part when two or more parts are positive. For a ratio of sums (count ÷ land, volume ÷ surface, total length ÷ segments), the merged value is a weighted average of the parts and always lies between them. The run confirms the algebra on real data and measures its size: in A, merging districts more than doubles a subprefeitura's index relative to its highest district (median 2.14). The single B failure is subprefeitura 27 (index 0.527 vs parts 0.551–1.000): each factor stays within range, but a sum of separately scaled factors can fall just outside the range of the parts' sums.

### T2 — size dependence (`t2_size_dependence.csv`)

Spearman correlation with land area, 95% bootstrap interval:

| | Pooled (173) | São Paulo (96) | Chicago (77) |
|---|---|---|---|
| A index | **+0.650** [0.539, 0.740] size-dependent | **+0.635** [0.466, 0.769] size-dependent | **+0.610** [0.419, 0.748] size-dependent |
| B index | −0.156 [−0.302, 0.005] not size-dependent | **−0.583** [−0.734, −0.389] size-dependent | **−0.300** [−0.501, −0.073] size-dependent |

A count factors pooled: C +0.282, R +0.582, H +0.728, N +0.754. B per-km² factors pooled: C −0.163, R −0.044, H −0.205, N +0.009.

The signs are opposite. In A, larger districts score higher; in B, within each city, larger districts score lower (the large districts are peripheral). T1 shows that A's count factors grow with unit size by construction, so A's positive size relation is a property of the method. B's negative relation is consistent with less dense peripheries, but T2 alone cannot prove that it reflects urban form rather than another bias.

### T3 — agreement between A and B (`t3_agreement.csv`)

| Measure | Value |
|---|---|
| Spearman A vs B, pooled / São Paulo / Chicago | 0.552 / 0.089 / 0.490 |
| Top-10 overlap | 2 (Itaim Bibi, Loop) |
| Brás rank (of 173) | A 106, B 23 |
| Largest rank shift | Grajaú (SP:30): A rank 1, B rank 168 |

Verdict: **substantively disagree** (Spearman < 0.8 and overlap < 7). Within São Paulo the two rankings are nearly unrelated (0.089).

| Rank | Method A | Method B |
|---|---|---|
| 1 | Grajaú (92.4 km²) | República (2.4 km²) |
| 2 | Itaim Bibi | Sé |
| 3 | Sacomã | Loop |
| 4 | Jabaquara | Bela Vista |
| 5 | Jardim Ângela (36.3 km²) | Near North Side |
| 6 | Santo Amaro | Santa Cecília |
| 7 | Loop | Itaim Bibi |
| 8 | Jardim São Luís (25.9 km²) | Vila Mariana |
| 9 | Itaquera | Consolação |
| 10 | Pirituba | Jardim Paulista |

**Worked example.** Grajaú has 92.4 km² of land; Brás has 3.6 km².

| | Grajaú A | Brás A | Grajaú B (per km²) | Brás B (per km²) |
|---|---:|---:|---:|---:|
| Commercial places | 3,437 | 4,649 | 37.2 | 1,281.0 |
| Dwellings | 154,175 | 19,723 | 1,668.3 | 5,434.4 |
| Hubs | 644 | 72 | 7.0 | 19.8 |
| Road segments | 6,089 | 658 | 65.9 | 181.3 |

Method A ranks Grajaú first mainly because it is 25 times larger than Brás; per km², Brás has 34 times the commercial places, 3.3 times the dwellings, 2.8 times the hubs and 2.8 times the street segments.

### T4 — city composition (`t4_city_composition.csv`)

| | Chicago units in top 20 | in bottom 20 |
|---|---:|---:|
| A | 2 | 19 |
| B | 2 | 14 |
| Expected at Chicago's share of units (77/173) | 8.9 | 8.9 |

Both methods place most Chicago areas low. In A, part of this follows from Chicago's smaller units (land median 7.170 vs 9.632 km²), so counts are smaller. In B it may reflect real density differences or unequal sources (Overture Places provenance differs by city, and the dwelling counts come from two different censuses); **no available reference can separate the two**, so B's cross-city ranking is not validated.

### S1 — bus stops merged (`s1_bus_merged.csv`)

Merging same-name bus stops within 50 m (Chicago 9,867 stops → 6,044 clusters in units; SP 21,978 → 20,596) barely changes either index: Spearman with the primary index 0.996 (A) and 0.994 (B); top-10 overlap 9 of 10; Brás rank A 106 → 97, B 23 → 24.

## 3b. Application: the Chicago area most similar to Brás (`bras_chicago_match.csv`)

Rule for the agreed one-number index: the Chicago area whose index value is closest to Brás's, |I(area) − I(Brás)|, smallest first; each method chooses on its own index. Diagnostic, not part of the agreed model: the Euclidean distance between the six scaled factors of the area and of Brás, ranked among the 77 areas.

| Method | Chosen area | Its index (Brás) | Gap | Runner-up, gap | Pick's profile-distance rank |
|---|---|---|---:|---|---:|
| A | Auburn Gresham (CHI:71) | 0.828 (0.833) | 0.005 | South Deering, 0.011 | 44 of 77 |
| B | Lake View (CHI:06) | 1.852 (1.998) | 0.145 | Edgewater, 0.292 | 7 of 77 |

Closest six-factor profiles to Brás and their index-gap rank: method A, North Center (26), Lincoln Park (54), Edgewater (12); method B, West Town (7), Near West Side (4), Logan Square (9). Method A's choice rests on a total that is matched to within 0.005 by an area whose factor mix differs from Brás's; method B's choice also ranks among the closer profiles.

## 4. Conclusions supported by these tests

1. **Method A is biased as a measure of urban intensity.** Its four count factors and its index depend on how unit boundaries are drawn (T1, 0 of 29 merged units consistent), rise with unit size in both cities (T2), and A's ranking is nearly unrelated to B's within São Paulo (T3). The bias is structural: it follows from summing counts over units of unequal land area (2.148–206.876 km² in SP, 1.570–33.958 km² in Chicago; `unit_components.csv`), and it would remain with perfect data.
2. **Method B removes that bias** (T1 passed for every factor and the index).
3. **Method B is not proven unbiased in general.** It inherits the source limits that A shares: Overture Places covers 3.2%–35.2% of São Paulo CNEFE establishment addresses depending on the district (P-PLACES-1), Overture heights come from LiDAR in Chicago and OSM tags in São Paulo (A only), and the cross-city comparison (T4) cannot be validated with available data.

## 5. Limits

- Average street length enters both indices positively, as specified, although longer segments usually indicate a coarser network; the sign was not changed in B because it was not part of the agreed corrections.
- Min–max over the pooled 173 units lets single extremes set each scale.
- Vintages differ: Overture 2026, CNEFE 2022, Census 2020, GTFS feeds as supplied, GHSL height 2018.
