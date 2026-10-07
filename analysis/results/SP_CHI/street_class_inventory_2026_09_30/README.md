# Street length by each source's own class (2026-09-30)

Run `analysis/scripts/tabulate_street_classes_by_source.py`. Every record of each source is kept, clipped to the municipal boundary (Chicago: union of the 77 Community Areas, EPSG:26916; São Paulo: union of the 96 districts, EPSG:31983), and its length summed by the class the source itself assigns. **No filtering, de-duplication, class recoding or imputation.** Missing class is shown as `(missing)`. Outputs: `street_class_by_class.csv` (one row per source and class) and `street_class_inventory.csv` (adds Chicago `status` and Overture `subtype`, plus an `m1_eligible` flag for Overture rows that the locked ten-class M1 rule would keep).

Lengths are raw sums and include exact duplicate geometries and both carriageways, so they are not the M1 numerator. Each source's share is of *that source's* total.

## Chicago: City Street Center Lines (7,171 km, 56,237 records inside the city)

| CLASS | City label | km | Share |
|---|---|---:|---:|
| 4 | Other streets | 4,963 | 69.2% |
| 3 | Collectors | 750 | 10.5% |
| 2 | Arterials | 659 | 9.2% |
| 1 | Expressway | 283 | 3.9% |
| 9 | Ramps | 157 | 2.2% |
| 99 | Unclassified (O'Hare) | 141 | 2.0% |
| E | Extent | 128 | 1.8% |
| RIV | River | 68 | 0.9% |
| 7 | Tiered | 15 | 0.2% |
| 5 | Named alleys | 8 | 0.1% |
| S, missing | Sidewalk, none | 0.5 | <0.01% |

By `STATUS`: N 7,081 km, P (private) 69, UC 9, V 7, C 3.5, missing 2. Extent, river and sidewalk lines (196 km, 2.7%) are not streets.

## São Paulo: `classvias` (19,910 km, 210,351 records) — the SP layer that carries a class on its own geometry

| Class (source label) | km | Share |
|---|---:|---:|
| LOCAL | 12,821 | 64.4% |
| COLETORA | 4,165 | 20.9% |
| ARTERIAL | 2,164 | 10.9% |
| RODOVIA | 311 | 1.6% |
| VIA DE PEDESTRES | 277 | 1.4% |
| VTR | 172 | 0.9% |
| (missing) | 0.7 | <0.01% |

Two other SP local layers are tabulated in the CSVs. The CET classification export (`geoportal_classificacao_viaria_cet`) has exactly 75,000 rows and 7,048 km inside the city (Local 62.6%, Coletora 21.3%, Arterial 11.8%, Rodovia 1.6%, Vias de pedestre 1.5%, VTR 1.2%); it is a partial export, not a citywide inventory. The `logradouro` street lines (19,370 km) carry **no functional class**, only a street-type code (R 66.2%, AV 13.7%, PC 4.9%, blank 3.3%, TV 3.0%, ES 2.8%, …).

### `logradouro` versus `classvias` (checked 2026-09-30)

They are two separately drawn copies of largely the same streets, with different roles. `logradouro` is the street-segment inventory (name, type, address ranges, street code) and is the geometry the SP model measures for M1/M6. `classvias` is a street-line layer that carries the functional class. Neither replaces the other, so the `classvias` table above is a complete inventory of *that layer's* classes, not a class split of the `logradouro` geometry.

| Overlap test (length-weighted, 3 sample points per line) | 2 m | 5 m | 15 m |
|---|---:|---:|---:|
| `logradouro` length within tolerance of a `classvias` line | 88% | 95% | 97% |
| `classvias` length within tolerance of a `logradouro` line | 86% | 93% | 97% |

By street code: 88.4% of `logradouro` length has a code (the other 11.6%, about 2,262 km, has a blank code and cannot be joined by code); of the coded length, 96.3% has a code that occurs in `classvias`. `classvias` also has 915 exact duplicate geometries.

**What the earlier SP imputation was.** The class was not absent from the source. The SP preparation transferred classes onto `logradouro` edges with strict rules (same normalized street code, compatible address ranges, at least 80% coverage by a 2 m buffer, plus a ≤1 m Hausdorff fallback). Per `docs/sp/PREPARATION.md`: 76.15% of length was matched to an observed class, 10.70% was assigned Local by imputation, 13.15% stayed unresolved; the 23.85% later assigned Local is the imputed plus unresolved share. Because 95% of `logradouro` length lies within 5 m of a `classvias` line, the unclassified share is largely a consequence of the matching rules, not evidence that classes are unavailable; whether a looser rule would be correct has not been tested. A per-class table of the `logradouro` geometry (observed class versus unresolved, no imputation) has not been produced. It is also unverified which of the two layers underlies the `local_density_km_km2` used in the earlier Overture/local ratio review.

## Overture road segments (release 2026-08-19.0), raw class × subtype

| | Chicago | São Paulo |
|---|---:|---:|
| All segments, km | 28,958 | 24,021 |
| Subtype `road`, km | 26,276 | 23,072 |
| Subtype `rail`, km | 2,670 | 943 |
| M1-eligible (ten classes, road subtype), km | 7,164 | 17,917 |

| Overture class | Chicago km (share of all) | São Paulo km (share of all) |
|---|---:|---:|
| footway | 12,063 (41.7%) | 1,814 (7.6%) |
| service | 6,460 (22.3%) | 2,439 (10.2%) |
| residential | 4,442 (15.3%) | 12,276 (51.1%) |
| secondary | 1,027 (3.5%) | 1,248 (5.2%) |
| tertiary | 754 (2.6%) | 1,564 (6.5%) |
| primary | 184 (0.6%) | 925 (3.9%) |
| trunk | 37 (0.1%) | 569 (2.4%) |
| motorway | 481 (1.7%) | 450 (1.9%) |
| unclassified | 122 (0.4%) | 367 (1.5%) |
| unknown | 415 (1.4%) | 459 (1.9%) |
| living_street / pedestrian | 13 (<0.1%) | 161 (0.7%) |
| path, cycleway, steps, track | 589 (2.0%) | 702 (2.9%) |
| rail-type classes (standard_gauge, subway, light_rail, …) | 2,360 | 842 |
| (missing) | 12 | 6 |

Among the M1-eligible classes, residential is 62.0% of length in Chicago and 68.5% in São Paulo.

## Observations (descriptive; nothing here is accepted or corrected)

- Chicago Overture carries 12,063 km of `footway` and 6,460 km of `service` (64% of all its segments), against 4,253 km (18%) in São Paulo. Sidewalk and alley-like mapping is far denser in Chicago's Overture, which is why the M1 class rule removes 75% of Chicago's raw Overture length but 25% of São Paulo's.
- After that rule, Chicago's eligible Overture length (7,164 km) is about equal to the local file's whole length (7,171 km, which includes extent, river and other non-street lines), and São Paulo's (17,917 km) is about 90% of `classvias` (19,910 km). This matches the earlier district-level ratios (Chicago ≈ 1.05, São Paulo ≈ 0.94) only roughly and is a citywide total, not a per-district comparison.
- Within each city the local class shares and the Overture eligible shares look similar in the middle of the hierarchy (Chicago local class 4 69% vs Overture residential 62%; São Paulo LOCAL 64% vs residential 68.5%), but the two schemes are not equivalent classes; see the [Chicago class-4 cross-check](../../Chicago/chicago_centerline_class_review_2026_09_30/README.md).
- Chicago's local file includes non-street lines (extent, river) and private streets; São Paulo's `classvias` has essentially complete class coverage (5 features unclassified).
