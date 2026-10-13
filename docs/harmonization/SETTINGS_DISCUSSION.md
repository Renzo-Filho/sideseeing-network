# Choosing the cross-city model's settings for Brás: discussion and findings (13 October 2026)

**Status.** This is a research note. It records the review of the São Paulo–Chicago model's settings, carried out on 13 October 2026 to select a Chicago Community Area similar to Brás (SP:10). It explains the model's choices in plain terms and records what was decided and found. No setting below is final.

- Method and full results: [MODEL_REPORT](MODEL_REPORT.md) (§11 v2, §12 v3, §13 v4).
- Decisions: [DECISIONS](../DECISIONS.md) and the cross-city sections of [MODEL_PLAN](../chicago/MODEL_PLAN.md).
- Sources of the numbers: the model's published tables in `analysis/results/SP_CHI/sp_chicago_model_v{2,3,4}_*/`, recomputed during the session with the model's own code. Section 7 is a variant the user set in the explorer; it is reproduced here but not published as a version. Sections 9 and 10 use the census-tract pieces in `analysis/results/Chicago/chicago_tract_breakdown_2026_10_13/` and the neighborhood pieces in `analysis/results/Chicago/chicago_neighborhoods_2026_10_13/`, scored with the explorer's own code (`viz/model.js`).

## 1. Summary

1. **The model always names a closest Chicago area, but Brás has no close one.** In every version, Brás's best Chicago match is among the weakest cross-city matches of the 173 units (146th to 170th of 173; §6).
2. **The settings decide which kind of area comes closest:**
   - physical fabric favours West Town (v2);
   - position within each city favours Lower West Side (v3);
   - Brás's distinctive commercial and built-ground profile favours Near West Side and Near North Side (v4).

   Within each version only the set of the top five is reasonably stable. First place is not.
3. **A web search and the model do not disagree.** The model's own land-use data agree that v3's matches are mostly residential and that Chicago's commercial hubs are the Loop, Near South Side and Near North Side (§5). The model answers a different question: which area's whole profile is least different from Brás.
4. **A defensible statement of the result:**

   > At Community Area scale, Chicago has no close analogue of Brás. Its best Chicago match is among the weakest cross-city matches in every version of the model, and the more the distance emphasizes Brás's distinctive traits, the weaker that match becomes. The least different areas are Near West Side, Near North Side, Lower West Side, West Town and Avondale, their order depending on which traits are emphasized.
5. **Inside the areas, a few neighborhoods come closer, but none is close (§10).** With the City of Chicago's neighborhoods (102 pieces, median 5.1 km², near Brás's 3.6 km²), 6 pieces beat the best whole area under v4. The best is Bucktown, in Logan Square, at 1.256 against 1.476, 15% closer; only 3 of the 96 São Paulo districts gain more. United Center (the western part of Near West Side), West Town's own neighborhood, River North and West Loop follow. The best neighborhood is still farther from Brás than 95% of the units' best cross-city matches. A first try with census tracts (§9) found closer pieces on commercial corridors, but a tract is about 7 times smaller than Brás.

## 2. How the model works

### 2.1 Distance

- Every unit is a point in a space of 21 measured columns.
- Each column is turned into a z-score: $z = (\text{value} - \text{mean}) / \text{SD}$, capped at ±3.
- Each **family** groups one or more columns. Its gap between two units is the average squared z-difference over its columns, divided by the family's median gap over all 14,878 pairs (calibration).
- The distance is

$$D = \sqrt{\textstyle\sum_f w_f \cdot \text{gap}_f}$$

  with family weights $w_f$, renormalized over the families both units have.
- **$D^2$ splits exactly into family parts**, which is what the explorer's matrix shows.
- **Sub-types are not merged.** Retail, services, commerce land and the other sub-types are each a separate axis. Two places are compared on each axis before anything is averaged. A retail-led place and a services-led place therefore come out far apart.
  - Under v2, Brás vs the Loop on the U6 activity mix was 9.7 times the typical pair, farther than 97% of all pairs.
  - The retail-led units (Brás, Bom Retiro, Pari) and the services-led ones (Loop, Edison Park, Oakland) are 9.7 typical gaps apart, against 0.8 within the retail-led group.
- **Averaging the sub-type gaps instead of summing them changes nothing.** The calibration divides by the median, so the factor cancels (checked: difference below 1e-15).
- **Collapsing to one number does lose detail:** which way a gap goes, which family produced it, and how gaps compensate each other. The family breakdown recovers it.
- **Squared vs absolute gaps.** Squaring makes one large gap cost more than several small ones. Using absolute gaps instead (L1) keeps v2's top four for Brás (Spearman 0.985).

### 2.2 z-scores and the cap

- **z = +2** is unusual: in the model's columns, 4–14 of the 173 units have |z| > 2.
- **z = +3** is extreme. Values beyond ±3 are set to ±3, so that one unit (the Loop, Marsilac) cannot dominate every distance it takes part in.
- The same unit gets different z-scores depending on the reference group:
  - **absolute (pooled):** all 173 units;
  - **relative:** its own city.

  Brás's coverage is +2.48 absolute and +1.96 relative.

### 2.3 Scaling: absolute, relative, hybrid

| Scaling | Mean and SD from | Question it answers |
|---|---|---|
| Absolute | all 173 units | which area has the same measured values |
| Relative | the unit's own city | which area holds the same position in its city |
| Hybrid (v2) | absolute for the same-instrument families (M1, M3, M4, M6, M7, B1, U3), relative for the rest (BV, U2, U4, U6, U1) | the same physical fabric where measured alike; the same position where instruments differ |

**Why some families carry "instrument caveats".** Pooled scaling assumes a number means the same thing in both cities. When the two cities' numbers come from different instruments, part of the gap between them is the instrument:

| Family | São Paulo vs Chicago instrument |
|---|---|
| U2 jobs | RAIS vs LODES: different registers; RAIS can place jobs at the head office |
| U4 transit | The PTAL index grows with route counts, which the two agencies code differently. Medians 14.2 vs 5.7 |
| BV height | GHSL reads about 10–15% higher in São Paulo, checked against LiDAR |
| U6 activity | Overture's place coverage differs by country and by class |
| U1 land use | Declared tax use (IPTU) vs observed land use (CMAP) |

Worked example, U4:

| | Brás | West Town | Gap |
|---|---|---|---|
| Absolute z | +1.87 | −0.06 | 1.93 SD |
| Relative z | +1.69 | +0.90 | 0.79 SD |

Part of the absolute gap is route coding, and pooling cannot separate it from real service. Relative scaling removes the city-wide offset, but it also removes real level differences. For example, São Paulo's median resident density is 2.5 times Chicago's.

**What the scaling does to Brás's matches:**
- Relative scaling pulls Brás toward its city's middle and lifts Chicago areas. This closes density and coverage gaps, which favours Lower West Side and McKinley Park.
- Absolute scaling keeps those gaps but stops penalizing the towers on height and jobs, which brings in Near North Side.

### 2.4 Runs and the PCA distance

| Run | Rule | For Brás |
|---|---|---|
| R1 | full calibrated distance, equal weights | the reference reading |
| R2 | Euclidean distance on the principal components reaching 90% of variance (5 under v2) | top four as R1 |
| R3 | drop columns while any pair has \|ρ\| ≥ 0.70 | drops B1, U2 and M1 under hybrid scaling; industrial areas move up |

**The PCA distance discards what separates close matches.**
- Under v2, the five kept components hold only 49% of the Brás–West Town squared distance.
- Below 90% of the variance the ranking changes: with 2 components, Lake View and Armour Square enter.
- Combined with custom weights, PCA amplifies them. A raised family gets its own kept component, a lowered one falls into the discarded part, and the number of components jumps (4 to 6), so rankings jump too.
- Conclusion: use the full distance and keep PCA as a check. v3 and v4 do.

### 2.5 Nominal and effective weights

A weight is a price per *typical* difference. A family's actual share of $D^2$ is that price times how large its gaps really are, averaged over all pairs:
- Long-tailed families deliver more than their weight. Under v2, M3 block size: average gap 13 times its typical gap, 19% of $D^2$ on an 8.3% budget. The tail comes from airports, rural land and industry.
- Compact families deliver less. U1's average gap is only about 1.7 times its typical gap.
- **A family on which every candidate misses Brás by the same amount changes no ranking.** Raising its weight raises every distance equally. Example: under v3, U1 is 0.64 of $D^2$ for Lower West Side and 0.66 for West Town.

### 2.6 What U1 and U6 measure

| | U6 activity composition | U1 land-use shares |
|---|---|---|
| Counts | establishments (Overture places), one point each | lot area by primary use |
| Columns | establishments per 100 dwellings; mix of food, retail, services & offices, making & storing, institutions (centred log-ratios) | residential, commerce, industrial, institutional shares |
| Sees | type of commerce, vertical mixing, small shops | residential land, land taken by large sites |
| Misses | non-listed activity; country-specific coverage | ground-floor shops in residential buildings (primary use only) |

- They overlap on commerce land ↔ intensity (Spearman 0.71 in São Paulo) and industrial land ↔ making (0.69 / 0.66). Otherwise they carry different information.
- **Brás vs the Loop:** U1 sees them as alike (65% vs 59% commerce land). U6 separates them: Brás is retail-led, the Loop services-led.
- **Lower West Side:** U1 sees industry (49% of land). U6 sees only a mild lean toward making.
- **Treatment differs.** U6 uses log-ratios (Aitchison geometry). U1 uses plain shares, so "commercial instead of residential" is counted on two U1 columns.

### 2.7 Correlated families

Cross-family pairs with |ρ| ≥ 0.70 are in bold.

| Group | Pairs |
|---|---|
| **Urban grain** | **B1 ↔ U3 0.79, M1 ↔ B1 0.78, M1 ↔ M7 0.76, M7 ↔ B1 0.75**, M3 ↔ M1 −0.63 (São Paulo −0.90) |
| **Centrality** | **U2 ↔ U6 intensity 0.83, U2 ↔ commerce 0.70**, BV ↔ U4 0.65 (Chicago 0.88), BV ↔ U2 0.62 |
| Industry | U1 industrial ↔ U6 making 0.67 |
| City-specific | M4 compactness ↔ jobs / intensity 0.80 / 0.79 in São Paulo only |

- Dropping M3 and M7 (from v3 on) removed most of the grain double count.
- Brás is extreme on both the grain and the centrality groups, so both count it several times.
- The Ledoit-Wolf Mahalanobis distance removes all shared correlation, and it keeps none of v2's Chicago top five for Brás.

### 2.8 B1 footprint coverage

**Definition:** the union of Overture building footprints clipped to land, divided by land (unit area minus water).

| | Brás | São Paulo median | Chicago median |
|---|---|---|---|
| B1 | 0.566 (1st in São Paulo) | 0.365 | 0.224 |

- Brás's value is reliable: 98.5% of its footprint area comes from OpenStreetMap, and it equals GeoSampa's 0.568.
- Microsoft footprints miss whole blocks in Brás (0.205) and are not used.
- In São Paulo, 22 districts mapped mostly by machine learning read about 13% low.

## 3. Settings history

| Version | Scaling | Main weights | Brás's Chicago top 5 | Status |
|---|---|---|---|---|
| v2 (8 Oct) | hybrid | equal (1/12 each) | West Town, Avondale, Logan Square, Lincoln Park, North Center | published comparison |
| v3 (13 Oct) | all-relative | U1 .25, U6 .20, BV/M1/B1 .10, rest .05; M3, M7 off | Lower West Side, Avondale, West Town, McKinley Park, Logan Square | decided as final, reopened the same day |
| **v4** (13 Oct) | all-relative | U1 .25, U6 .25, B1 .20, U4 .10, M4/M6 .05, U2 .04, BV .03, M1 .02, U3 .01; inside U1 commerce 3, residential 2, industrial 1, institutional 0 | Near West Side, Near North Side, Lower West Side, West Town, Avondale | proposed, the explorer's start |

**Why v3.**
- M3's long tail made it carry about three times its weight in the user's draft.
- M3 was dropped rather than M1 because M1 is better validated, and M3 is nearly constant across Brás's candidates.
- B1 returned as Brás's best-measured trait.
- U2 was halved because it duplicates U6 intensity.

**Why v4.**
- v3's matches turned out to be mostly residential, and weak matches.
- v4 weights the families by how much they distinguish Brás within São Paulo (`bras_profile_sao_paulo_v4.csv`): retail share and coverage 1st, commerce 3rd, residential 3rd lowest, transit 3rd, establishments per dwelling 5th, height 32nd, streets 44th, residents 52nd.
- The weights inside U1 decide the order. With v4's family weights but equal inner weights, Lower West Side stays first.

## 4. Correction recorded

The first v3 text called its answer "a non-residential working district". That fits Lower West Side only partly (29% residential, 49% industrial) and does not fit West Town or Avondale (61–63% residential). The v3 contract's question and MODEL_REPORT §13.1 were corrected.

## 5. Web search vs the model

**The concern.** A web search lists the Loop and nearby areas as Chicago's commercial hubs and describes v3's top four as mostly residential.

**Check.** The model's Chicago land use is CMAP 2023:

| | Residential land | Commerce land | Industrial land | Establishments per 100 dwellings | Commerce-land rank in Chicago |
|---|---|---|---|---|---|
| Brás | 15% | 65% | 16% | 25.8 | — |
| Lower West Side | 29% | 13% | 49% | 13.0 | 23rd |
| Avondale | 63% | 20% | 13% | 8.3 | 8th |
| West Town | 61% | 19% | 12% | 12.3 | 9th |
| McKinley Park | 48% | 15% | 33% | 7.3 | 18th |
| Loop | 31% | 59% | 0% | 42.7 | 1st |
| Near South Side | 31% | 58% | 3% | 7.5 | 2nd |
| Near North Side | 46% | 33% | 9% | 15.0 | 4th |

**Conclusion.** The search's facts and the model's data agree. The two answer different questions. Chicago's commercial hubs are high-rise office and services centres; Brás is a low-rise wholesale district of retail and workshops.

Under v3, the hubs are far from Brás:

| Hub | Rank of 77 under v3 | Main separating families |
|---|---|---|
| Loop | 52nd | height 34%, activity mix 26% |
| Near North Side | 35th | height 44% |

The model does recognize centres: with the Loop as reference, its closest São Paulo districts are República, Sé and Bela Vista.

## 6. Match strength

**The measure.** For each of the 173 units, take its closest unit in the other city. Sort the 173 distances from closest to farthest, and see where Brás's falls.

| Fit | Brás's position (1 = closest) |
|---|---|
| v2 all-relative R1 | 146th |
| v2 hybrid R1 | 154th |
| v3 | 165th |
| v4 | 170th |

Under v4 the full list is computed from `distance_v4.csv`:

| Position | Unit | Its best match in the other city | Distance |
|---|---|---|---|
| 1 | Vila Matilde | Portage Park | 0.305 |
| 87 (median) | Mount Greenwood | Cursino | 0.591 |
| 146 | Loop | República | 0.842 |
| 168 | Pari | Lower West Side | 1.411 |
| **170** | **Brás** | **Near West Side** | **1.476** |
| 171–173 | Riverdale, Marsilac, O'Hare | | 1.545–1.820 |

- **Facts:** the positions and distances.
- **Interpretation:** "Chicago has no close analogue of Brás" holds within this model: its 21 measurements, its settings and Community Areas as units. It is not a statement about the real cities. Smaller units, such as retail corridors, could match better (untested).
- **Why the position worsens from v2 to v4.** Weighting the distance toward Brás's extremes makes Brás harder to match. That reflects how distinctive Brás is; it does not make v4 more correct. v4 encodes Brás's distinctive profile by design, and no external check ranks the versions.

## 7. Variant explored in the explorer: v4 with U3 off and U6 at 26%

**Settings.**
- v4 with U3 switched off and the U6 slider moved to 2.6.
- Budgets: U6 26%, U1 25%, B1 20%, U4 10%, M4 5%, M6 5%, U2 4%, BV 3%, M1 2%.
- Inside U1 and M4 as in v4.

**Ranking.**

| Chicago rank | Area | Distance | Share of 500 draws in the top 5 |
|---|---|---|---|
| 1 | Near North Side | 1.490 | 88.4% |
| 2 | Near West Side | 1.491 | 92.6% |
| 3 | Lower West Side | 1.540 | 77.2% |
| 4 | West Town | 1.547 | 95.6% |
| 5 | Avondale | 1.558 | 80.8% |

- Brás's São Paulo top five are unchanged: Bom Retiro, Pari, Belém, Santa Cecília, Sé.
- Match strength is unchanged: 170th of 173.

**First place is a tie.** Near North Side and Near West Side differ by 0.001. Across 500 weight draws, first place goes to Near North Side in 35%, Near West Side in 31%, Lower West Side in 22% and West Town in 10%. Reading the result as "select Near North Side" is not supported. Report the two Near areas as tied, with Lower West Side and West Town close behind.

**Reading the explorer's matrix.** The matrix shows each family's share of what *separates* Brás from an area, not of what supports the match. A family supports a match where that area's part of $D^2$ is smaller than its competitors' parts:

| Part of $D^2$ | Near North Side | Near West Side | Lower West Side | West Town | Avondale |
|---|---:|---:|---:|---:|---:|
| B1 | **0.024** | 0.432 | 0.372 | 0.127 | 0.123 |
| U1 | **0.324** | 0.347 | 1.273 | 1.264 | 1.237 |
| U6 | 1.018 | 1.141 | **0.551** | 0.823 | 0.776 |
| BV | 0.459 | 0.155 | 0.012 | 0.019 | 0.000 |
| U2 | 0.250 | 0.085 | 0.000 | 0.004 | 0.004 |
| U4 | 0.071 | 0.001 | 0.130 | 0.088 | 0.215 |
| $D^2$ | 2.220 | 2.222 | 2.371 | 2.393 | 2.429 |

- **B1 and U1 support Near North Side.** Its coverage is as exceptional for Chicago (0.375 against a 0.224 median) as Brás's is for São Paulo. Its land use is far less residential than the West Town group's.
- **U6 works against it.** It is Near North Side's largest remaining gap (46% of its $D^2$): retail log-ratio −0.02 against Brás's +1.37, making & storing −0.49 against +0.29.
- **BV and U2 also work against it** (towers, office jobs). Their 3% and 4% weights keep them small. Restoring height to 10% returns Lower West Side to first place (§13.4 of the report).

## 8. Open questions

- **Unit scale.** Tested with census tracts (§9) and with the City's neighborhoods (§10). Neighborhoods of Brás's size bring a modest gain, mostly near downtown. Smaller pieces such as commercial-corridor tracts come closer but are not comparable in size. A like-for-like test would split São Paulo's districts the same way.
- **The question to settle.** Is the target "least different overall profile" (v2, v3), "Brás's distinctive traits" (v4), or "a commercial hub" (which would point to the Loop or Near North Side)? Each is defensible; the write-up should name one and report the others beside it.
- **Double counting.** Commerce appears in U1 and U6 intensity. U1's plain shares count "commercial instead of residential" twice. A log-ratio treatment of U1 would be a new version.
- **External check.** Nothing outside the model validates similarity. Match strength and stability describe the model; they do not confirm the matches.

## 9. Census-tract breakdown (13 October 2026; superseded by §10)

*The explorer's tab first used these tracts. The user replaced them the same day because a tract (median 0.5 km²) is about 7 times smaller than Brás (3.6 km²). The results stay in `analysis/results/Chicago/chicago_tract_breakdown_2026_10_13/`, produced by `chicago_tract_breakdown.py` at commit `9e8220c9`.*

**Question.** The user asked what happens if only Pilsen is taken, and then for a way to break each Community Area into its neighbourhoods. The City of Chicago's neighbourhood layer maps 63 of the 77 areas one-to-one and does not split Lower West Side, so Pilsen cannot be isolated with it. Overture's neighbourhood polygons cover 6% of the city. The user chose **2020 census tracts**: 801 tract pieces (the part of a tract inside one area), median 10 per area. Lower West Side, which is Pilsen plus Heart of Chicago, has 11.

**Method.** Each piece is measured on the 21 columns with the areas' sources and rules. Summing the pieces reproduces each area's published counts ([results README](../../analysis/results/Chicago/chicago_tract_breakdown_2026_10_13/README.md)). Pieces are scored with the fit's constants and calibration, not refitted, and placed against Brás. The explorer's tab did this live until the tracts were replaced by neighborhoods (§10).

### 9.1 Pilsen (Lower West Side)

| Settings | Whole area (rank of 77) | Its 11 tracts | Tracts closer than the area | Best tract |
|---|---|---|---|---|
| v4 | 1.533 (3rd) | 1.414 – 2.131 | 3 | Tract 3107 (18th St and Ashland), 1.414: would rank 1st of 77 |
| v3 | 1.182 (1st) | 1.342 – 2.120 | 0 | Tract 8412 (Cermak and Western), 1.342: would rank 5th |
| v2 hybrid R1 | 1.278 (7th) | 1.008 – 2.746 | 3 | Tract 3108 (18th St and Ashland), 1.008: would rank 1st |
| v2 all-relative R1 | 0.963 (1st) | 1.096 – 2.890 | 0 | Tract 8412, 1.096: would rank 7th |

Taking only part of Pilsen does not help consistently:
- Under v4 and v2 hybrid, its 18th Street and Ashland tracts beat every whole area.
- Under v3 and v2 all-relative, the whole Lower West Side is closer than any of its tracts. There the area's mix as a whole is the match, not one piece of it.
- Tract 3107 is small (0.16 km², 80 establishments), so its U6 mix is noisy.

### 9.2 Across Chicago

| Settings | Closest whole area | Tracts closer than it | Best tract | Best tract ÷ best area | Typical São Paulo district (median ratio, 96 districts) | Districts that gain more than Brás |
|---|---|---|---|---|---|---|
| v4 | Near West Side 1.476 | 22 | Tract 1901, Belmont Cragin (Diversey and Cicero), 1.116 | 0.756 | 1.006 | 4 |
| v3 | Lower West Side 1.182 | 11 | Tract 2305, Humboldt Park (North Ave), 0.945 | 0.800 | 1.009 | 9 |
| v2 hybrid R1 | West Town 1.096 | 9 | Tract 2429, West Town (Chicago Ave and Grand), 0.939 | 0.857 | 0.857 | 48 |
| v2 all-relative R1 | Lower West Side 0.963 | 4 | Tract 8404, McKinley Park (Ashland, 35th, Archer), 0.883 | 0.917 | 0.971 | 33 |

Three findings:

1. **Under the Brás-focused settings the gain is specific to Brás.** A tract can beat the best area by chance alone, since there are 801 tracts against 77 areas and smaller units are more extreme. To check, the same ratio was computed for every São Paulo district. Under v4 and v3 a typical district gains nothing (median ratio about 1.0, and usually no tract beats its best area). Brás gains 24% and 20%, more than 92 and 87 of the 96 districts. Under v2 hybrid, Brás's gain is exactly the typical one.
2. **The close pieces are commercial corridors inside residential areas.** The top tracts recur across settings: West Town 2429, McKinley Park 8404, Rogers Park 102.02, Humboldt Park 2305, Lincoln Park 8326 and Belmont Cragin 1901 and 1910. Their establishments line one or two streets, according to the Overture place addresses:

   | Tract | Main streets |
   |---|---|
   | West Town 2429 | Chicago Ave, Grand Ave, Western Ave |
   | McKinley Park 8404 | Ashland Ave, 35th St, Archer Ave |
   | Rogers Park 102.02 | Clark St, Howard St |
   | Humboldt Park 2305 | North Ave |
   | Lincoln Park 8326 | Clybourn Ave, Armitage Ave |
   | Belmont Cragin 1901 | Diversey Ave, Cicero Ave |
   | Lower West Side 3107 and 3108 | 18th St, Ashland Ave |

   Their commerce shares of occupied land are 16–41%, against Brás's 65%, and they hold 80–481 establishments each. This is the "unit scale" open question (§8), now partly answered: Chicago's Brás-like places are strips, not areas.
3. **Still not close.** Even the best piece (1.116 under v4, 0.945 under v3) is farther from Brás than 94% (v4) and 86% (v3) of the 173 units' best area-level cross-city matches. Tracts make the match less weak; they do not make it strong. That comparison sets a tract against areas, so it is indicative only.

**Reading.** If the study needs one Chicago place that resembles Brás, the tract evidence points to a commercial corridor rather than a Community Area. The candidates recur across settings: Chicago Avenue and Grand in West Town, Pilsen's 18th Street, North Avenue in Humboldt Park and Ashland and 35th in McKinley Park. The best whole areas remain the group in §1 item 4. Neither is a close match.

## 10. City neighborhoods inside each area (13 October 2026)

**Unit.** The user chose the City of Chicago's 98-neighborhood map (layer bbvz-uum9; the City calls it approximate and unofficial). Each 2020 census-block piece goes to the neighborhood that holds its centre, so boundaries follow block edges, nest exactly in the 77 areas, and keep each family's block allocation. 102 pieces are published (99.99% of the land), with a median of 5.1 km² of land; Brás has 3.6 km². 13 areas split into 2 to 5 neighborhoods: Near North Side and West Town 5; Near West Side and Loop 4; Lake View and Lincoln Park 3; Logan Square, Austin, Near South Side, Armour Square, Hyde Park, Woodlawn and Edgewater 2. The other 64 keep one neighborhood equal to the area, Lower West Side among them, so Pilsen still cannot be isolated. The smallest pieces are downtown: Greektown 0.14 km², Printers Row 0.20 km², Millennium Park 0.26 km². All checks pass ([results README](../../analysis/results/Chicago/chicago_neighborhoods_2026_10_13/README.md)). The explorer's **Chicago neighborhoods** tab shows them live.

| Settings | Closest whole area | Neighborhoods closer than it | Best neighborhood | Best ÷ best area | Typical São Paulo district (median ratio) | Districts that gain more than Brás | Best neighborhood's percentile among units' best cross-city matches |
|---|---|---|---|---|---|---|---|
| v4 | Near West Side 1.476 | 6 of 102 | Bucktown (Logan Square), 1.256 | 0.851 | 1.000 | 3 | 95% |
| v3 | Lower West Side 1.182 | 2 | United Center (Near West Side), 1.140 | 0.964 | 1.000 | 11 | 95% |
| v2 hybrid R1 | West Town 1.096 | 1 | Wicker Park (West Town), 1.095 | 0.999 | 1.000 | 22 | 88% |
| v2 all-relative R1 | Lower West Side 0.963 | 2 | United Center (Near West Side), 0.930 | 0.966 | 1.000 | 9 | 81% |

Under v4, the next pieces are West Town's own neighborhood (1.322), United Center (1.348), River North (1.379), West Loop (1.386) and Lincoln Park (1.462). Inside the v4 group from §1:

| Area (v4 distance) | Its neighborhoods |
|---|---|
| Near West Side (1.476) | United Center 1.348, West Loop 1.386, Greektown 1.698, Little Italy and UIC 2.050 |
| Near North Side (1.500) | River North 1.379, Streeterville 1.752, Rush & Division 1.767, Old Town 1.975, Gold Coast 2.488 |
| West Town (1.540) | West Town 1.322, Wicker Park 1.662, Ukrainian Village 1.944, East Village 1.949, Humboldt Park 2.264 |
| Loop (1.791) | Loop 1.864, Printers Row 2.445, Millennium Park 2.774, Grant Park 3.350 |

Findings:

1. **The gain is modest and specific to the Brás-focused settings.** Under v4, Brás's best neighborhood is 15% closer than its best area. For a typical São Paulo district the best neighborhood is no closer than the best area (median ratio 1.000), and only 3 districts gain more than Brás. Under v3 and v2 all-relative the gain is 3–4%; under v2 hybrid there is none.
2. **The same few pieces recur.** United Center, West Town (with Wicker Park), Bucktown and Lincoln Park appear near the top under every setting. United Center beats its whole area (Near West Side) under all four settings. River North beats Near North Side under v4 and v3.
3. **Still not close.** The best neighborhood is farther from Brás than 81–95% of the 173 units' best cross-city matches, depending on the settings.
4. **Compared with tracts (§9).** Tracts found larger gains (24% under v4) on commercial corridors, but at about a seventh of Brás's size, and many of them had under 100 businesses (480 of 801). Neighborhoods are comparable in size and much more stable (6 of 102 pieces under 100), and they find less.

**Reading.** At a scale comparable to Brás, Chicago's closest pieces are west and northwest of the Loop: United Center and West Loop (Near West Side), West Town and Wicker Park, Bucktown, River North, and Lincoln Park. Bucktown leads under v4 and United Center under v3. None of them is a close match.
