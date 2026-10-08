# U4 public transport accessibility (PTAL Access Index), Chicago and São Paulo

Run 5 October 2026 by `analysis/scripts/evaluate_u4_ptal_step2.py` (4 min, 1.9 GB peak). Method: Transport for London PTAL (Connectivity Assessment Guide 2015), applied unchanged; decisions S2-7 to S2-13 were fixed by the user before the run ([MODEL_PLAN.md](../../../../docs/chicago/MODEL_PLAN.md#step-2--u4-public-transport-accessibility-was-reachable-bus-supply)). **Not accepted until the user decides the returned cases and signs the acceptance record.**

## Definition

`u4_ptai_avg_resident` = resident-weighted mean, over 100 m grid locations, of the PTAL Access Index for weekday 08:15–09:15 on Wednesday 14 October 2026. Per route: network walk (Overture segments without motorway and trunk; 4.8 km/h; at most 640 m to bus, 960 m to metro or rail) to its nearest stop, plus half the headway plus a reliability allowance (2 min bus, 0.75 min metro and rail); equivalent doorstep frequency = 30 ÷ that time; most frequent direction; per mode the best route counts fully and others half; modes summed. Modes: Chicago CTA bus, CTA 'L', Metra; São Paulo SPTrans bus, Metrô, CPTM. Residents: Chicago ACS 2020–2024 (U3 allocation), São Paulo Census 2022 tracts.

## Construction checks (U4-1)

| Check | Result |
|---|---|
| TfL figure 2.15 reproduced | 15.1619 vs published 15.16, pass |
| Chicago residents equal U3 ACS allocation | max difference 1.5 × 10⁻¹¹, pass |
| Grid conserves residents | Chicago 171,185 points, 2,710,782.56; São Paulo 318,335 points, 11,446,054.47; pass |
| Timetable departures equal an independent DuckDB count | CTA 75,260; Metra 648; pass |
| São Paulo headway expansion equals explicit enumeration (25 sampled trips) | pass |
| São Paulo residents assigned to districts (tolerance 0.01%) | **fails the tolerance:** 11,446,054.47 of 11,451,999; the 5,944.5 missing residents lie in tract parts outside the district boundary, so no district value is affected |
| Walking network | Chicago 536,070 nodes, 99.3% in the main component; São Paulo 325,765, 98.5%; stop rows more than 100 m from the network 0.13% and 0.42% |
| No missing values; total AI = sum of mode AIs | pass |

Service counted in the window (stop-route-direction departures per hour): Chicago bus 71,137 (123 routes), 'L' 3,149 (8), Metra 327 (10; Heritage Corridor has none); São Paulo bus 423,079 (1,111 routes), Metrô 6,126 (8; Line 6 has none), CPTM 1,623 (6; Line 13 excluded, it has one station in the city).

## Results

| | Chicago (77) | São Paulo (96) |
|---|---|---|
| Median AI | 5.65 | 14.20 |
| Range | 1.73 (Edison Park) – 38.93 (Loop) | 1.04 (Marsilac) – 70.97 (República) |
| Highest | Loop, Near North Side 20.6, Near South Side 17.1, Near West Side 14.6, Lake View 12.6 | República, Sé 50.4, **Brás 36.9 (3rd)**, Bela Vista 35.3, Santa Cecília 32.8 |
| Share of AI from bus / metro / rail (resident-weighted) | 80.6% / 16.1% / 3.3% | 96.9% / 2.4% / 0.7% |
| Areas with more than 10% of residents beyond walking reach (map review) | Edison Park, Norwood Park, Forest Glen, Pullman, Riverdale, Hegewisch, Garfield Ridge, Ashburn, Beverly, Mount Greenwood, Morgan Park | Marsilac, Parelheiros |

**U4-2 footway gate (rule: no area changes more than 10% and none moves 5 or more ranks in its city): fails in both cities; cases returned.** Removing footways, paths, steps and cycleways lowers values by a median 3.7% in Chicago and 4.2% in São Paulo (Spearman 0.998 and 0.997), so the effect is similar in the two cities. Chicago cases: Near South Side −10.8%, Douglas −11.0%, Archer Heights −13.5% (6 ranks). São Paulo: Jardim Helena −14.0%, Cidade Dutra −10.2%, Butantã −9.8% (7 ranks), Vila Leopoldina −9.6% (7), Artur Alvim −9.4% (6), Vila Curuçá −2.1% (6), Vila Jacuí −2.0% (5).

**U4-3 straight-line distance (descriptive):** raises values by a median 30.7% in Chicago and 62.5% in São Paulo (Spearman 0.991 and 0.978; 8 and 38 areas move 5 or more ranks). Straight-line distance would favour São Paulo; network walking removes that.

**U4-4 (descriptive):** Chicago PTAL vs the old bus-only U4, Spearman 0.939.

## Limits

- PTAL measures service near home, not where it goes.
- It grows with the **number of routes** (each extra route adds half its EDF) faster than with the frequency of one route (each route's EDF is capped by walking and the reliability allowance). São Paulo's network of many overlapping bus lines therefore scores high and its very frequent Metrô contributes little. Within a city this is the published method; between cities the level difference partly reflects network design. The common model must treat cross-city levels with care.
- Scheduled service, not reliability; São Paulo rail headways as published by SPTrans, not by the operators; suburban buses (Pace, EMTU) excluded in both cities; SPTrans feed date is its download date (9 September 2026).
- The walking network ignores slope, crossings and safety. Points are snapped to the nearest network node.

## Files

- `tables/u4_ptal.csv|parquet`: one row per unit (both cities): `u4_ptai_avg_resident`, `ai_bus|metro|rail`, PTAL band shares, `share_ai_zero`, `ai_unweighted_populated`, residents, points, `u4_streets_only`, `u4_straight_line`, ranks and changes, `chi_bus_only_u4_old`.
- `checks.json`, `source_register.json` (feeds with active services and SHA-256, TfL method document, inputs).
