# The São Paulo–Chicago harmonized similarity model: versions, findings and conclusions

**What this is.** The single report on the cross-city model built to answer *which Chicago places most resemble Brás (São Paulo district SP:10)*. It covers:
- the method;
- the four versions fitted between 6 and 13 October 2026, with what each found and how to read it;
- the comparison across versions;
- the breakdown of Chicago's Community Areas into smaller pieces.

It replaces the separate settings note of 13 October 2026, whose content is folded in here. Decisions are recorded with their dates in [DECISIONS](../DECISIONS.md) and [MODEL_PLAN](../chicago/MODEL_PLAN.md); dated project status is in [STATUS](../STATUS.md).

**Status (13 October 2026).** No version is final:
- **v4** is the current proposal and the explorer's starting settings;
- **v3** is a candidate (decided as final, reopened the same day);
- **v2** and **v1** stay published, unchanged and reproducible.

| Version | Fitted | Contract | Outputs | Report |
|---|---|---|---|---|
| v1 | 6 Oct | [`sp_chicago_model_v1.json`](../../analysis/config/sp_chicago_model_v1.json) | [`sp_chicago_model_v1_2026_10_06`](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/README.md) | [§5](#5-version-1-hybrid-scaling-equal-weights-6-october-2026) |
| v2 | 8 Oct | [`sp_chicago_model_v2.json`](../../analysis/config/sp_chicago_model_v2.json) | [`sp_chicago_model_v2_2026_10_08`](../../analysis/results/SP_CHI/sp_chicago_model_v2_2026_10_08/README.md) | [§6](#6-version-2-the-u1-commerce-share-8-october-2026) |
| v3 | 13 Oct | [`sp_chicago_model_v3.json`](../../analysis/config/sp_chicago_model_v3.json) | [`sp_chicago_model_v3_2026_10_13`](../../analysis/results/SP_CHI/sp_chicago_model_v3_2026_10_13/README.md) | [§7](#7-version-3-position-within-each-city-13-october-2026) |
| **v4** | 13 Oct | [`sp_chicago_model_v4.json`](../../analysis/config/sp_chicago_model_v4.json) | [`sp_chicago_model_v4_2026_10_13`](../../analysis/results/SP_CHI/sp_chicago_model_v4_2026_10_13/README.md) | [§8](#8-version-4-brás-distinctive-traits-13-october-2026) |
| Sub-areas | 13 Oct | — | [`chicago_neighborhoods_2026_10_13`](../../analysis/results/Chicago/chicago_neighborhoods_2026_10_13/README.md); superseded [`chicago_tract_breakdown_2026_10_13`](../../analysis/results/Chicago/chicago_tract_breakdown_2026_10_13/README.md) | [§10](#10-below-community-area-scale) |

| Item | Location |
|---|---|
| Code | [`sp_chicago_model.py`](../../analysis/scripts/sp_chicago_model.py) (v1, v2; reuses [`chicago_model.py`](../../analysis/scripts/chicago_model.py)); [`sp_chicago_model_settings.py`](../../analysis/scripts/sp_chicago_model_settings.py) (v3, v4); [`chicago_neighborhoods.py`](../../analysis/scripts/chicago_neighborhoods.py) (sub-areas) |
| Notebook | [`analysis/sp_chicago_model_analysis.ipynb`](../../analysis/sp_chicago_model_analysis.ipynb) (v1, v2: all plots and tables) |
| Interactive explorer | [`viz/`](../../viz/README.md): starts from v4; v3 and the v2 runs are presets; any reference unit, family and within-family weights; a Chicago neighborhoods tab. Curio: [`interactive_harmonized`](../../analysis/curio_nodes/interactive_harmonized/README.md) (opens on v3) |
| Feature-by-feature evidence | [Chicago model report §3](../chicago/MODEL_REPORT.md#3-the-features) and each family's results README |

## 1. Conclusions

1. **At Community Area scale, Chicago has no close analogue of Brás.**
   - In every one of the 20 published fits (v1 and v2 under three scalings × three runs, plus v3 and v4), Brás's best Chicago match is weaker than the best cross-city match of most units. It sits between 125th and 170th of 173 (1 = closest).
   - Under the two Brás-focused versions it is among the very weakest: 165th under v3 and 170th under v4.
   - The model always names a closest area. That area is the least different, not a similar one ([§9.2](#92-match-strength-in-all-20-fits)).
2. **One area is in every fit's top five: West Town.** It is in Brás's Chicago top five in all 20 fits, and in 93–99% of 5,000 random family weightings under each scaling. It is the only area near the top on both halves of Brás's profile: 1st on Brás's ordinary traits (street density, hierarchy, parcels, business intensity) and 3rd on its extremes combined (coverage, land use, business mix), although specialists such as Near North Side, the Loop or Near South Side beat it on each extreme feature alone. It is not a commercial district. Avondale is in 17 of 20 fits, and Lower West Side leads under every all-relative fit. These are the robust part of the answer; first place is not ([§9.1](#91-bráss-closest-chicago-areas-in-each-version), [§9.5](#95-why-west-town-is-in-every-top-five)).
3. **The settings decide which side of Brás is matched, and each version asks a different question.**
   - Physical fabric, with same-instrument families compared on absolute levels (v1, v2 hybrid), points to **West Town** and the near northwest side.
   - Position within each city (v3) points to **Lower West Side and McKinley Park**: areas as unusual for Chicago as Brás is for São Paulo in grain, height and business density.
   - Brás's distinctive commercial and built-ground traits (v4) point to **Near West Side and Near North Side**.

   None of these is more correct than the others; they answer different questions ([§9.3](#93-what-the-settings-decide)).
4. **The more the distance targets what makes Brás distinctive, the weaker its best match.** Brás's position falls from 154th (v2 hybrid) to 165th (v3) to 170th (v4). Brás is an outlier even inside São Paulo:
   - 1st in building coverage and in retail's share of its businesses;
   - 3rd in commerce land share (65%);
   - 3rd lowest in residential land share.
5. **Why no Chicago place matches: it has nothing that combines a retail-led business mix with dense, low-rise building coverage.**
   - Chicago's commercial centres (the Loop, River North, West Loop) are high-rise and led by services and offices.
   - Its low-rise mixed neighborhoods (West Town, Bucktown, United Center) have less commercial land and much less ground covered by buildings.
   - The gap no Chicago unit closes is the retail mix: Brás's retail log-ratio is +1.37; every leading Chicago piece is between −0.08 and +0.15 ([§10.4](#104-why-the-closest-neighborhoods-still-miss)).
6. **Smaller Chicago units help only a little at Brás's own scale.**
   - With the City of Chicago's neighborhoods (median 5.1 km² of land; Brás has 3.6 km²), Brás's best match under v4 is 15% closer than its best area: Bucktown, in Logan Square. It is still farther than 95% of the units' best area-level matches.
   - The pieces that recur across settings are United Center (which beats its own area, Near West Side, under all four settings), West Town, Bucktown, Lincoln Park and River North.
   - Commercial-corridor tracts come closer (24%), but they are about a seventh of Brás's size ([§10](#10-below-community-area-scale)).
7. **How to report the result.** Name the question, report a group rather than a winner, and always give the match strength. Choosing a place is a claim about which side of Brás matters: built form (West Town), working character (Lower West Side) or commercial intensity (Near North Side, Near West Side). Each gives up another side ([§11](#11-what-choosing-a-place-means)). A defensible statement:

   > At Community Area scale Chicago has no close analogue of Brás: its best Chicago match is among the weakest cross-city matches in every version of the model. The least different areas are West Town (in every fit), Avondale, Lower West Side, and, when Brás's distinctive commercial profile is emphasized, Near West Side and Near North Side. At Brás's own scale, the least different places are the mixed neighborhoods just west and northwest of the Loop (United Center, West Town, Bucktown), then River North and West Loop on the downtown side. None combines Brás's retail-dominated mix with its dense low-rise coverage.

## 2. The question and the units

**Which Chicago Community Areas most resemble Brás?**
- Brás is São Paulo district SP:10: a dense, older central district of retail, wholesale and garment workshops, with 3.6 km² of land.
- The model places all 173 units (96 São Paulo districts, 77 Chicago Community Areas) in one space built from 21 measurements in 12 feature families (20 in v1).
- It measures the dissimilarity between every pair. Rankings are read around any reference; this report uses Brás.
- The model is **target-free**: nothing was fitted to Brás. Its weights (v3, v4) state a question but do not estimate one.

## 3. The features

The same 12 families as the Chicago model, built with the same definitions in both cities. Each was accepted step by step with checks fixed before its results were seen.

| Family | What it measures | Chicago source | São Paulo source | Same instrument? |
|---|---|---|---|---|
| M1 street density | street km per km² of land | Overture streets | Overture streets | yes |
| M3 block size | size of the block a typical m² of land sits in | Overture street faces | Overture street faces | yes |
| M4 block shape | compactness, elongation | Overture street faces | Overture street faces | yes |
| M6 street hierarchy | major-road share of street length | Overture streets | Overture streets | yes |
| M7 ground-parcel density | parcels per km² of land | Cook 2024 ground parcels | GeoSampa fiscal lots | yes (a condominium counts once in both) |
| B1 footprint coverage | building footprint share of land | Overture buildings | Overture buildings | yes |
| U3 resident density | residents per km² of land | ACS 2020–2024 | Census 2022 | yes (residents) |
| BV vertical form | built-surface-weighted height | GHSL | GHSL | **no**: reads about 10–15% higher in São Paulo against LiDAR |
| U2 job density | registered jobs per km² of land | LODES 2023 | RAIS 2022 | **no**: different registers; RAIS can place jobs at the head office |
| U4 transit access | PTAL index averaged over residents | CTA bus, 'L', Metra | SPTrans bus, Metrô, CPTM | **no**: the index rises with route count; medians 14.2 vs 5.7 |
| U6 activity composition | establishments per 100 dwellings, and their mix of five classes (food & drink, retail, services & offices, making & storing, institutions) | Overture places + ACS dwellings | Overture places + CNEFE dwellings | **no**: place coverage differs by country and class |
| U1 land-use shares | residential, commerce (from v2), industrial, institutional shares of occupied land | CMAP 2023 (observed) | IPTU 2026 (declared) | **no** |

**Missing values.** O'Hare, Marsilac and Parelheiros have no U1 shares (under 10% classified land). Pairs involving them use the families both units have.

**B1 for Brás.** Coverage is the union of Overture footprints clipped to land, divided by land. Brás has 0.566, 1st in São Paulo (medians: São Paulo 0.365, Chicago 0.224). The value is reliable: 98.5% of its footprint area comes from OpenStreetMap, and it equals GeoSampa's 0.568. Microsoft footprints miss whole blocks in Brás (0.205) and are not used. In São Paulo, 22 districts mapped mostly by machine learning read about 13% low.

## 4. How the model works

### 4.1 One scale for two cities (convention C6)

**The issue, with real numbers.**

| | Residents per km² | Position in its own city |
|---|---|---|
| Brás | 10,690 | 52nd of 96 (São Paulo median 11,110) |
| Loop | 10,739 | near the top (Chicago median 4,488) |

- **Absolute comparison** reads them as identical on density.
- **Relative comparison** reads Brás as an ordinary São Paulo district and the Loop as one of Chicago's densest.

Absolute comparison is right when a number means the same thing in both cities. Relative comparison is the safe choice when the instrument differs (the "no" rows of §3), where part of the gap between cities is the instrument itself. Example, U4 transit:

| | Brás | West Town | Gap |
|---|---|---|---|
| Absolute z | +1.87 | −0.06 | 1.93 SD |
| Relative z | +1.69 | +0.90 | 0.79 SD |

Part of the absolute gap is route coding, and pooling cannot separate it from real service.

| Scaling | Mean and SD from | Question it answers | Used by |
|---|---|---|---|
| Absolute | all 173 units | which area has the same measured values | v1, v2 extra run |
| Relative | the unit's own city | which area holds the same position in its city | v1, v2 extra run; **v3, v4** |
| Hybrid | absolute for the same-instrument families (M1, M3, M4, M6, M7, B1, U3), relative for the rest (BV, U2, U4, U6, U1) | the same physical fabric where measured alike, the same position where instruments differ | **v1, v2 primary** |

![Feature values by city](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/figures/city_levels_boxplots.png)

**What relative scaling cannot do.** It removes a city-wide shift and stretch caused by an instrument, but also real level differences: São Paulo's median resident density is 2.5 times Chicago's. It does not fix an instrument that mis-ranks units *inside* a city.

**What the scaling does to Brás's matches.**
- Relative scaling pulls Brás toward its city's middle and lifts Chicago areas. That closes density and coverage gaps and favours Lower West Side and McKinley Park.
- Absolute scaling keeps those gaps, but it stops penalizing towers on height and jobs, which brings in Near North Side.

### 4.2 The distance

1. **Transforms (J-5).** Natural log for strictly positive amounts on a ratio scale (U2, U3, U4, M1, M7, BV height, M4 elongation); identity for shares, indices and log-ratios.
2. **z-scores (J-6).** $z = (t - \bar t)/s$, with the population SD, capped at ±3 (§4.3).
3. **U6 composition.** The five classes are compared with the Aitchison distance: the Euclidean distance between centred log-ratios, $\operatorname{clr}_k=\ln(n_k+0.5)-\tfrac15\sum_j\ln(n_j+0.5)$, left unscaled. Under hybrid and all-relative scaling the log-ratios are centred within each city.
4. **Blocks and calibration (J-7).** Each family is a block; U6 is two blocks (intensity and composition), each with half the U6 budget. A block's dissimilarity is the weighted mean of its columns' squared differences, divided by its median over all 14,878 pairs:

   $$m_b(d,e)=\frac{\sum_j v_j\,(x_{dj}-x_{ej})^2}{\sum_j v_j},\qquad \beta_b=\operatorname*{median}_{d<e}\,m_b(d,e).$$

   The column weights $v_j$ are 1 in v1–v3. v4 sets them inside U1 and M4, and then $\beta_b$ is recomputed on the reweighted block. The family weight sets how much a family counts; $v_j$ sets only its inner mix.
5. **Distance (J-7, J-8).**

   $$D(d,e)=\sqrt{\frac{\sum_b w_{f(b)}\,s_b\,m_b(d,e)/\beta_b}{\sum_{b\ \text{available}} w_{f(b)}\,s_b}},$$

   where $w_f$ is the family weight (1/12 each in v1 and v2) and $s_b$ the block's share of its family. Only the ratios of the weights matter.
6. **What drives a match.** $D^2$ splits exactly into family parts. The explorer's contribution matrix and every worked example below show each family's share.

**Sub-types stay separate.** Retail, services, commerce land and the other sub-types are each their own axis, and two places are compared on each axis before anything is averaged. A retail-led place and a services-led place therefore come out far apart. Under v2, Brás vs the Loop on the U6 mix was 9.7 times the typical pair, farther than 97% of all pairs. Averaging rather than summing the sub-type gaps changes nothing, because the median calibration cancels the factor. Using absolute instead of squared gaps (L1) keeps v2's top four for Brás (Spearman 0.985).

### 4.3 z-scores and the cap

- **z = +2** is unusual: in the model's columns, 4–14 of the 173 units have |z| > 2.
- **z = +3** is extreme. Values beyond ±3 are set to ±3, so that one unit (the Loop, Marsilac) cannot dominate every distance it takes part in. The cap also hides how far the Loop is on jobs, height and transit.
- The same unit gets different z-scores depending on the reference group. Brás's coverage is +2.48 absolute and +1.96 relative.

### 4.4 Runs R1–R3 and the PCA distance

| Run | Rule |
|---|---|
| R1 | full calibrated distance (the reference reading) |
| R2 | Euclidean distance on the principal components reaching 90% of variance |
| R3 | drop scalar columns while any pair has \|ρ\| ≥ 0.70 |

**The PCA distance discards what separates close matches.**
- Under v2, the five kept components hold only 49% of the Brás–West Town squared distance.
- Below 90% of the variance the ranking changes: with 2 components, Lake View and Armour Square enter.
- With custom weights PCA amplifies them. A raised family gets its own kept component, a lowered one falls into the discarded part, and the number of components jumps (4 to 6).

v3 and v4 therefore use the full distance and keep PCA as a check.

### 4.5 Nominal and effective weights

A weight is a price per *typical* difference, because each block is calibrated by its median pair. A family's actual share of $D^2$ is that price times how large its gaps really are.
- **Long-tailed families deliver more than their weight.** Under v1 and v2, M3 block size has an average gap 13 times its typical gap: 19% of $D^2$ on an 8.3% budget. The tail comes from airports, rural land and industry.
- **Compact families deliver less.** U1's average gap is about 1.7 times its typical gap.
- **A family on which every candidate misses Brás by about the same amount changes no ranking.** Raising its weight raises every distance equally. Under v3, U1 is 0.64 of $D^2$ for Lower West Side and 0.66 for West Town.

### 4.6 What U1 and U6 measure

| | U6 activity composition | U1 land-use shares |
|---|---|---|
| Counts | establishments (Overture places), one point each | lot area by primary use |
| Columns | establishments per 100 dwellings; mix of five classes (centred log-ratios) | residential, commerce, industrial, institutional shares |
| Sees | type of commerce, vertical mixing, small shops | residential land, land taken by large sites |
| Misses | non-listed activity; country-specific coverage | ground-floor shops in residential buildings (primary use only) |

They overlap on commerce land ↔ intensity (Spearman 0.71 in São Paulo) and on industrial land ↔ making (0.69 and 0.66). Otherwise they carry different information:
- **Brás vs the Loop:** U1 sees them as alike (65% vs 59% commerce land). U6 separates them: Brás is retail-led, the Loop services-led.
- **Lower West Side:** U1 sees industry (49% of land). U6 sees only a mild lean toward making.

U6 uses log-ratios (Aitchison geometry); U1 uses plain shares, so "commercial instead of residential" is counted on two U1 columns.

### 4.7 Correlated families

Cross-family pairs with |ρ| ≥ 0.70 are in bold.

| Group | Pairs |
|---|---|
| **Urban grain** | **B1 ↔ U3 0.79, M1 ↔ B1 0.78, M1 ↔ M7 0.76, M7 ↔ B1 0.75**, M3 ↔ M1 −0.63 (São Paulo −0.90) |
| **Centrality** | **U2 ↔ U6 intensity 0.83, U2 ↔ commerce 0.70**, BV ↔ U4 0.65 (Chicago 0.88), BV ↔ U2 0.62 |
| Industry | U1 industrial ↔ U6 making 0.67 |
| City-specific | M4 compactness ↔ jobs and intensity 0.80 and 0.79, in São Paulo only |

Brás is extreme on both the grain and the centrality groups, so both count it several times. Dropping M3 and M7 from v3 on removed most of the grain double count. No pair reached the J-4 merge bar (0.90).

### 4.8 How results are judged

- **Rankings** around Brás, for the 77 Chicago areas and for all 172 other units. The face-validity check: Brás's nearest units overall should be its São Paulo inner-ring neighbours.
- **Stability:** 500 weight draws, each family weight × U(0.5, 1.5), seed 20261006. A match is stable if it stays in the top five in at least 80% of draws. Draws test stability around the chosen settings; **they do not show that a match is good.**
- **Named alternatives:** each version's table of nearby settings (Spearman over all pairs, shared top five, Brás's top five kept).
- **Match strength.** For each of the 173 units take its closest unit in the other city, sort those 173 distances, and see where Brás's falls (1 = closest). Distances are not comparable across versions; this position is.

## 5. Version 1: hybrid scaling, equal weights (6 October 2026)

**Settings.** 20 columns: U1 with three shares, residential, industrial and institutional; the commerce share failed the J-3 admission rule. Hybrid scaling primary, with all-absolute and all-relative as extra steps. Equal family weights (1/12). Runs R1–R3. All rules were fixed before any cross-city value was computed.

### 5.1 Brás under hybrid R1

| Chicago rank | Area | Distance | Rank among all 172 |
|---|---|---|---|
| 1 | West Town | 1.075 | 11 |
| 2 | Avondale | 1.119 | 14 |
| 3 | Logan Square | 1.143 | 16 |
| 4 | Lincoln Park | 1.196 | 25 |
| 5 | Lower West Side | 1.227 | 28 |
| 6–10 | North Center, McKinley Park, Edgewater, Lake View, Albany Park | 1.240–1.286 | 29–35 |

- **Brás's ten closest units overall are all in São Paulo:** Belém 0.716, Bom Retiro, Lapa, Cambuci, Mooca, Tatuapé, Ipiranga, Santa Cecília, Vila Guilherme, Pinheiros. These are the old inner-ring industrial and commercial districts around Brás, which supports face validity.
- The **Loop** ranks 69th of the 77 Chicago areas: it is a high-rise office centre, not a dense mixed district of shops and workshops.

![Distance to Brás](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/figures/maps_distance_to_bras.png)

**Worked example, Brás vs West Town.** $D^2 = 1.155$, so $D = 1.075$. B1 coverage makes up 40% of it (Brás covers 57% of its land with buildings, far above West Town), the U6 activity mix 23%, U1 land shares 15% and U4 6%; every other family is under 5%. On street layout, block size and shape, parcels and residents the two are very close.

![Contributions, Chicago top 10](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/figures/contributions_top10_chicago.png)

![Radar](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/figures/radar_bras_vs_top_chicago.png)

### 5.2 Principal components and R2

Five components carry 90.3% of the variance.
- **PC1 (55.1%), the grain axis:** M3 block size −0.95, M1 0.91, M7 0.80, B1 0.77, U3 0.70. Fine, dense, built-up fabric against coarse land.
- **PC2 (19.2%), residential vs central-arterial:** U1 residential land 0.75 against M6 major-road share −0.81, BV height −0.77, U2 jobs −0.70.

Brás and West Town sit side by side; the Loop and Sé are far out on the central end of PC2. **R2** gives the same ten Chicago areas as R1 in nearly the same order, with West Town first at 0.786.

![PCA](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/figures/pca_scatter.png)

### 5.3 R3: without correlated features

R3 drops B1 (partners U3 0.79, M1 0.78, M7 0.75), U2 (U6 intensity 0.83) and M1 (M7 0.76). Brás's closest Chicago areas: West Town, Avondale, Lower West Side, McKinley Park, Logan Square, then Lincoln Park, West Garfield Park, North Center, Bridgeport, Humboldt Park. West Town stays first; the southwest-side industrial-mixed areas move up.

### 5.4 Scale comparison

| Scaling, run | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| hybrid R1 | West Town | Avondale | Logan Square | Lincoln Park | Lower West Side |
| hybrid R2 | West Town | Avondale | Logan Square | Lincoln Park | North Center |
| hybrid R3 | West Town | Avondale | Lower West Side | McKinley Park | Logan Square |
| all-absolute R1 | West Town | Lincoln Park | Near North Side | Logan Square | Avondale |
| all-absolute R2 | West Town | Near North Side | Lincoln Park | Lake View | Logan Square |
| all-absolute R3 | West Town | Avondale | Lower West Side | Logan Square | McKinley Park |
| all-relative R1 | Lower West Side | McKinley Park | West Town | Avondale | Logan Square |
| all-relative R2 | Lower West Side | West Town | McKinley Park | Avondale | Lincoln Park |
| all-relative R3 | Lower West Side | McKinley Park | West Town | Avondale | Logan Square |

| Scaling, run (against hybrid R1) | All pairs (Spearman) | Shared top 5, all units | Brás's distances to the 77 Chicago areas (Spearman) | Brás's Chicago top 10 kept | Share of nearest five from the other city |
|---|---|---|---|---|---|
| hybrid R1 | 1 | 1 | 1 | 10 | 0.111 |
| hybrid R2 | 0.992 | 0.717 | 0.988 | 10 | 0.142 |
| hybrid R3 | 0.984 | 0.815 | 0.971 | 7 | 0.136 |
| all-absolute R1 | 0.960 | 0.822 | 0.951 | 8 | 0.072 |
| all-absolute R2 | 0.950 | 0.665 | 0.939 | 8 | 0.089 |
| all-absolute R3 | 0.968 | 0.719 | 0.966 | 7 | 0.083 |
| all-relative R1 | 0.954 | 0.743 | 0.981 | 7 | 0.238 |
| all-relative R2 | 0.947 | 0.578 | 0.976 | 8 | 0.276 |
| all-relative R3 | 0.902 | 0.640 | 0.966 | 7 | 0.261 |

- **West Town is in the top three of all nine runs.** Brás's distances to the Chicago areas agree with the hybrid at 0.94–0.99.
- **The scaling decides which Chicago side of Brás comes first.** Absolute levels bring in Near North Side, because Brás's absolute densities and transit are high. Relative levels favour Lower West Side and McKinley Park, which, like Brás inside São Paulo, are unusually commercial and industrial for their city.
- **The scaling decides how much the cities mix:** 7% of each unit's nearest five come from the other city under absolute levels, 24% under relative levels.

![City mixing](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/figures/scale_city_mixing.png)

### 5.5 Stability and sensitivities (hybrid R1)

- **Weight draws:** 75.8% of the 865 top-five relations are stable. Brás's Chicago top five: West Town, Avondale and Logan Square 100%, Lincoln Park 92%, Lower West Side 55.8% (**not stable**).
- **Sensitivities:**

| Scenario | All pairs | Shared top 5 | Brás's Chicago top 5 kept |
|---|---|---|---|
| Leave one family out (range over 12) | 0.906–0.997 | 0.816–0.916 | 3–5 (3 without U4) |
| Equal budget per domain | 0.986 | 0.865 | 4 |
| Robust median/IQR scaling | 0.982 | 0.888 | 4 |
| Rank-normal scaling | 0.861 | 0.719 | 5 |
| Ledoit-Wolf Mahalanobis (without U1) | **0.737** | **0.447** | **1** |
| M3 unweighted | 0.903 | 0.838 | 5 |
| M7 median parcel size | 0.993 | 0.879 | 5 |
| BV volume | 0.990 | 0.865 | 5 |
| U6 confidence ≥ 0.3 | 1.000 | 0.992 | 5 |
| *Post hoc:* mean calibration | 0.961 | 0.839 | 5 |

Results hold under every reweighting and alternative definition **except Mahalanobis**, which removes the correlation shared among features (mostly the grain axis) and so defines a different similarity. Removing M3, or switching to mean calibration, keeps all five of Brás's matches although M3 carries 18.9% of $D^2$.

### 5.6 Descriptive clusters (Ward, k = 4, silhouette 0.262)

The clusters cross the two cities, a sign that the hybrid scaling compares urban types rather than countries.

| Cluster | São Paulo | Chicago | Character |
|---|---|---|---|
| 0 | 42 | 47 | residential fabric of both cities (Chicago northwest and southwest sides; Penha, Itaquera, São Mateus, Pirituba) |
| 1 | 15 | 6 | mixed industrial edges and peripheral informal fabric (Archer Heights, Pullman; Brasilândia, Cidade Tiradentes) |
| 2 | 33 | 20 | **Brás's cluster**: dense mixed central and inner-ring areas (Brás, Belém, Bom Retiro, Sé, República; West Town, Logan Square, Lincoln Park, Lake View, the Loop) |
| 3 | 6 | 4 | large-land units: airport, heavy industry, rural south (O'Hare, Hegewisch; Marsilac, Parelheiros) |

![Clusters](../../analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/figures/maps_clusters.png)

### 5.7 Match strength and interpretation

- **Match strength:** hybrid R1, 148th of 173. Across v1's nine fits, 130th–160th.
- **Reading.** v1 finds Brás's **physical-fabric relatives**: older, dense, mixed-use areas on a fine grid with commercial corridors and an industrial past (the near northwest side, plus Pilsen and McKinley Park). It does not call Chicago's high-rise centre similar. The answer is robust to scaling, runs and most sensitivities, but it is a weak match: more than four fifths of units have a closer counterpart in the other city.

## 6. Version 2: the U1 commerce share (8 October 2026)

### 6.1 What changed and why

- **Change.** U1 compares **four** land-use shares (adding commerce): 21 columns. Nothing else changed: same tables and SHA-256, transforms, scaling, calibration, equal weights and runs.
- **Why (user decision).** Commercial land is central to Brás's profile. It devotes **65.0%** of its classified occupied land to commerce, 3rd of 94 São Paulo districts (city median 22.9%; Chicago median 10.5%), z = +2.68 within São Paulo.
- **What the decision overrides.** The commerce share failed J-3: its largest |Spearman| with U6, B1 and M1 is 0.708, with U6 intensity in São Paulo (the rule is < 0.70 in both cities). v2 therefore counts part of the commercial signal twice, once in U6 and once in U1. The overlap is accepted and reported, not corrected.
- **Inside U1** the four shares weigh a quarter each. Setting the commerce weight to 0 reproduces v1 exactly (maximum difference 2.2e-10 in the explorer, 2.2e-15 in Curio).

### 6.2 How much the model moves

Hybrid R1, v2 against v1:
- Spearman over all 14,878 pair distances: 0.9996.
- Mean shared top-five neighbours over all units: 0.975.
- Brás's distances to the 77 Chicago areas (Spearman): 0.9985.
- Brás's Chicago top 10 kept: 10 of 10.

### 6.3 Brás under v2 (hybrid R1)

| Chicago rank | v2 area | Distance | Rank among all 172 | v1 area (distance) |
|---|---|---|---|---|
| 1 | West Town | 1.096 | 12 | West Town (1.075) |
| 2 | Avondale | 1.132 | 14 | Avondale (1.119) |
| 3 | Logan Square | 1.148 | 15 | Logan Square (1.143) |
| 4 | Lincoln Park | 1.182 | 18 | Lincoln Park (1.196) |
| 5 | **North Center** | 1.271 | 29 | Lower West Side (1.227) |
| 6–10 | Lake View, Lower West Side, Edgewater, Albany Park, McKinley Park | 1.278–1.318 | 30–35 | |

- The first four are unchanged, and Lincoln Park moves closer: it is the most commercial of them (27.7% commerce land).
- Lower West Side drops from 5th to 7th: its land is industrial (49.2%) rather than commercial (13.1%).
- Bom Retiro (0.752) now precedes Belém (0.755) as Brás's nearest unit. The closest Chicago area enters at rank 12.
- The Loop is 67th of 77: its commerce share is Chicago's highest (58.6%), but height, jobs and transit still set it apart.
- **Worked example, Brás vs West Town:** $D^2 = 1.201$. B1 38.1%, U6 22.0%, **U1 18.2%** (v1 15.0%), U4 6.1%; every other family under 5%.
- **Stability:** West Town, Avondale and Logan Square 100% of draws, Lincoln Park 99.8%. North Center 27.0%: the fifth place is not firm. Over all units, 77.5% of top-five relations are stable.

### 6.4 Across scalings and runs

| Scaling, run | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| hybrid R1 | West Town | Avondale | Logan Square | Lincoln Park | North Center |
| hybrid R2 | West Town | Logan Square | Avondale | Lincoln Park | North Center |
| hybrid R3 | West Town | Avondale | Lincoln Park | Logan Square | Lower West Side |
| all-absolute R1 | West Town | Lincoln Park | Near North Side | Lake View | Logan Square |
| all-relative R1 | Lower West Side | Avondale | West Town | McKinley Park | Lincoln Park |

- West Town is in the top three in all nine combinations.
- R3 drops the same columns as v1 under hybrid (B1, U2, M1) and all-relative (U2, M3) scaling. Under all-absolute it also drops the commerce share itself (0.76 with BV height on absolute levels), with B1, U2, U4 and M1.
- **Structure.** U1 carries 6.4% of $D^2$ on average against its nominal 8.3%; M3 still carries the most (19.0%). PCA: five components carry 90.5%. PC2 (19.5%) now also loads the commerce share (−0.75): a residential versus central-commercial axis. Ward still finds k = 4 (silhouette 0.258). Mahalanobis keeps none of Brás's Chicago top five.

### 6.5 Match strength and interpretation

- **Match strength:** hybrid R1, 154th; all-relative R1, 146th. Across v2's nine fits, 125th–163th.
- **Reading.** Adding commerce barely moves the model (0.9996), because U1 is one family of twelve and its calibration keeps its typical contribution at its budget. It sharpens one thing: areas that are industrial rather than commercial (Lower West Side) move away from Brás, and commercial ones (Lincoln Park) move closer. **v2 hybrid R1 is the neutral baseline of the project:** equal weights and no question built into the weights.
- **Limits added.** Commerce is counted twice (U1 and U6 intensity). U1 compares observed CMAP use with declared IPTU use, relative to each city. Primary use per lot hides vertical mixing in both cities.

## 7. Version 3: position within each city (13 October 2026)

### 7.1 What changed and why

v3 fixes the settings used to answer the question; the data are v2's. It was decided by the user as the final settings after reviewing the scalings, the runs, the PCA distance, the weights and the correlations, and **reopened the same day** (§8.1). It stays published as a candidate.

| Setting | v2 | **v3** | Reason |
|---|---|---|---|
| Scaling | hybrid | **all-relative** | compare units by their position in their own city; sets aside instrument differences, and also real level differences |
| Distance | full | **full** | the 90% PCA cut drops directions that carry much of what separates close matches |
| U1 land use | 1/12 | **0.25** | land use and activity mix are the substance of the question |
| U6 activity | 1/12 | **0.20** | as U1 |
| BV, M1, B1 | 1/12 each | **0.10 each** | B1 returns as Brás's best-measured physical trait |
| U3, U4, M6, M4 | 1/12 each | **0.05 each** | context |
| U2 jobs | 1/12 | **0.05** | duplicates U6 intensity (Spearman 0.83) |
| M3 block size | 1/12 | **off** | long tail: in the user's draft it carried 12.3% of $D^2$ on a 5% weight. M3 was dropped rather than M1 because M1 is better validated and M3 is nearly constant across Brás's candidates |
| M7 parcel density | 1/12 | **off** | part of the grain cluster |

### 7.2 Brás under v3

| Chicago rank | Area | Distance | Rank among all 172 | Share of 500 draws in the top 5 |
|---|---|---|---|---|
| 1 | **Lower West Side** | 1.182 | 5 | 100% |
| 2 | **Avondale** | 1.273 | 9 | 100% |
| 3 | **West Town** | 1.292 | 10 | 100% |
| 4 | **McKinley Park** | 1.293 | 11 | 100% |
| 5 | Logan Square | 1.403 | 18 | 50.2% (not firm) |
| 6–10 | Lincoln Park, North Center, Humboldt Park, Belmont Cragin, Brighton Park | 1.407–1.506 | 19–25 | |

- Brás's nearest units are still São Paulo inner-ring districts: Bom Retiro 0.763, Belém, Pari, Vila Guilherme. The Loop is 52nd of 77.
- **Worked example, Brás vs Lower West Side.** $D^2 = 1.398$: U1 45.7%, U6 30.3%, B1 13.3%, U4 4.7%, BV 2.8%; every other family under 2%.
- **U1 is a large but nearly equal penalty for every candidate**, because Brás's land use is extreme. It mostly keeps residential areas off the shortlist. Within the shortlist the order is set by U6: Lower West Side is closer to Brás on making & storing, food & drink and institutions.
- **Effective weights:** U1 18.9% and U6 18.7% of $D^2$ on average. With M3 out, the largest overshoot is M1 (14.5% on 10%), through the rural and airport units.
- **Stability:** all four leaders hold in every draw. Over all units, 72.3% of top-five relations are stable.

### 7.3 v3 against named alternatives

| Alternative | Spearman, all pairs | Shared top 5 | Brás's Chicago top 5 kept | Brás's Chicago top 5 |
|---|---|---|---|---|
| v2 published (hybrid, equal weights) | 0.867 | 0.586 | 3 | West Town, Avondale, Logan Square, Lincoln Park, North Center |
| All-relative, equal weights | 0.923 | 0.667 | 4 | Lower West Side, Avondale, West Town, McKinley Park, Lincoln Park |
| Hybrid scaling, v3 weights | 0.945 | 0.739 | 5 | Avondale, West Town, Lower West Side, Logan Square, McKinley Park |
| v3 weights, PCA distance (7 components) | 0.995 | 0.758 | 4 | Lower West Side, McKinley Park, Avondale, West Town, Lincoln Park |
| User draft (B1 0, M3 0.05, U2 0.10) | 0.973 | 0.785 | 5 | Lower West Side, McKinley Park, Avondale, West Town, Logan Square |
| U2 0 | 0.998 | 0.926 | 5 | Lower West Side, Avondale, McKinley Park, West Town, Logan Square |
| B1 0.05 | 0.998 | 0.928 | 5 | Lower West Side, McKinley Park, Avondale, West Town, Logan Square |
| M1 out, M3 0.10 | 0.944 | 0.773 | 5 | Lower West Side, Avondale, West Town, McKinley Park, Logan Square |
| U1 0.10 | 0.991 | 0.860 | 5 | Lower West Side, Avondale, West Town, McKinley Park, Logan Square |

The weights move the answer more than the scaling: hybrid scaling with the v3 weights keeps all five, and every small change keeps the same five.

**Correlation left among the active columns** (all-relative, |ρ| ≥ 0.6 across families): U2 ↔ U6 intensity 0.83, U2 ↔ commerce 0.70, B1 ↔ U3 0.69, industrial ↔ making 0.67, BV ↔ U4 0.65, BV ↔ U2 0.62, intensity ↔ commerce 0.61, U4 ↔ commerce 0.60. The centrality group still moves together; U2 at 0.05 limits it, and setting U2 to 0 keeps Brás's top five.

### 7.4 Correction recorded

The first v3 text called its answer "a non-residential working district". That does not fit. By the model's own CMAP data:
- West Town and Avondale are 61–63% residential land;
- Lower West Side is 29% residential and 49% industrial;
- their commerce shares rank 8th–23rd in Chicago.

v3 finds areas that resemble Brás **in grain, height and business density for their city, not in being commercial**. The v3 contract's question was corrected.

### 7.5 Match strength and interpretation

- **Match strength:** 165th of 173 (weaker than 95% of units' best matches).
- **Reading.** v3 is the most stable version: its first four hold in every weight draw. But it answers "which area holds Brás's position in its own city on these weighted traits", and its answer is a set of residential and industrial-residential areas that are, for Chicago, as fine-grained and busy as Brás is for São Paulo. Its first Chicago match ranks 5th of all 172 units, the closest any version brings a Chicago area to Brás. Yet the match is weaker than under v2, because the weights concentrate the distance on traits where Brás is extreme.
- **Limits added.** The weights were chosen after v1 and v2 had been seen: they state a question and are not an estimate. All-relative scaling discards real level differences (São Paulo's median density is more than twice Chicago's). Double counting carries over from v2.

## 8. Version 4: Brás-distinctive traits (13 October 2026)

### 8.1 Why a v4

v3 was reopened by the user the same day for exploration. Its matches are not commercial areas, and they are weak (§7.4, §7.5). v4 asks: **which areas most closely reproduce the traits that distinguish Brás within São Paulo, each read relative to its own city?** v4 is the current proposal and the explorer's starting settings. It is not final.

### 8.2 Settings

Same data, scaling (all-relative) and distance (full) as v3; R3 pruning off. Brás's rank within São Paulo comes from `bras_profile_sao_paulo_v4.csv` (1 = highest value).

| Family | v3 | **v4** | Brás within São Paulo |
|---|---:|---:|---|
| U1 land use | 0.25 | **0.25** | commerce 3rd highest; residential 3rd lowest |
| U6 activity intensity and mix | 0.20 | **0.25** | retail share 1st; establishments per dwelling 5th |
| B1 footprint coverage | 0.10 | **0.20** | 1st |
| U4 transit access | 0.05 | **0.10** | 3rd |
| M4 block shape | 0.05 | 0.05 | compactness 12th |
| M6 major-road share | 0.05 | 0.05 | 15th |
| U2 job density | 0.05 | 0.04 | 15th; overlaps U6 intensity |
| BV height | 0.10 | 0.03 | 32nd |
| M1 street density | 0.10 | 0.02 | 44th |
| U3 resident density | 0.05 | 0.01 | 52nd |
| M3, M7 | 0 | 0 | off |

- **80% of the weight is on Brás's four most distinctive families.** A high weight makes a mismatch on that family costly; it does not reward high values.
- **Inside U1:** commerce 3, residential 2, industrial 1, institutional 0 (50%, 33%, 17%, off; Brás is 59th of 94 on the institutional share: ordinary). **Inside M4:** compactness 2, elongation 1. U6 keeps half intensity, half composition, because retail dominance is one composition, and boosting each extreme would count it several times.
- The weights come from Brás's São Paulo profile and were not tuned to a Chicago result. They are reasoned choices, with no unique mapping from rank to weight.

### 8.3 Brás under v4

| Chicago rank | Area | Distance | Rank among all 172 | v3 Chicago rank | Share of 500 draws in the top 5 |
|---|---|---|---:|---:|---:|
| 1 | **Near West Side** | 1.476 | 8 | 14 | 94.2% |
| 2 | **Near North Side** | 1.500 | 9 | 35 | 82.2% |
| 3 | Lower West Side | 1.533 | 11 | 1 | 77.8% (not stable) |
| 4 | **West Town** | 1.540 | 12 | 3 | 94.6% |
| 5 | **Avondale** | 1.551 | 13 | 2 | 81.2% |
| 6–10 | Lincoln Park, Logan Square, McKinley Park, Near South Side, Loop | 1.575–1.791 | 16–28 | | |

- **Brás's São Paulo neighbours** are its garment and wholesale neighbours and the centre: Bom Retiro (0.900), Pari, Belém, Santa Cecília and Sé.
- **The Loop** moves from 52nd to 10th: the low height weight no longer penalizes tall commercial areas.
- **The weights inside U1 decide the order.** With v4's family weights but equal inner weights, Lower West Side is first, then West Town and Avondale.
- **What still separates the leaders from Brás.** Near West Side: U6 50.4%, B1 19.9%, U1 15.9%, BV 7.1% of $D^2$. Near North Side: U6 43.5%, BV 20.4%, U1 14.4%, U2 11.1%. Both differ from Brás on its activity mix.
- **Effective weights** are close to nominal now that M3 is out: U6 23.9%, U1 21.6%, B1 19.4%, U4 10.4%; M1 delivers about twice its 2% (3.8%). Stability over all units: 73.8%.

### 8.4 v4 against named alternatives

| Alternative | Spearman, all pairs | Shared top 5 | Brás's Chicago top 5 kept | Brás's Chicago top 5 |
|---|---:|---:|---:|---|
| v2 published (hybrid, equal weights) | 0.803 | 0.519 | 2 | West Town, Avondale, Logan Square, Lincoln Park, North Center |
| v3 settings | 0.957 | 0.692 | 3 | Lower West Side, Avondale, West Town, McKinley Park, Logan Square |
| v4 family weights, equal inside U1 and M4 | 0.988 | 0.842 | 3 | Lower West Side, West Town, Avondale, Logan Square, Lincoln Park |
| Hybrid scaling, v4 weights | 0.942 | 0.720 | 4 | Near North Side, Near West Side, West Town, Avondale, Lincoln Park |
| v4 weights, PCA distance (7 components) | 0.994 | 0.750 | 3 | Near West Side, Near North Side, Near South Side, Lower West Side, Lincoln Park |
| B1 0.10 | 0.992 | 0.892 | 5 | Near West Side, Lower West Side, Near North Side, West Town, Avondale |
| B1 0.30 | 0.995 | 0.920 | 5 | Near North Side, Near West Side, West Town, Avondale, Lower West Side |
| U1 0.15 | 0.996 | 0.898 | 4 | Lower West Side, West Town, Avondale, Near West Side, Lincoln Park |
| U1 0.35 | 0.997 | 0.940 | 4 | Near West Side, Near North Side, Lower West Side, Lincoln Park, West Town |
| U6 0.15 | 0.997 | 0.912 | 4 | Near West Side, Near North Side, Lincoln Park, West Town, Avondale |
| U6 0.35 | 0.998 | 0.914 | 5 | Lower West Side, Near West Side, Near North Side, West Town, Avondale |
| BV 0.10 (v3's height weight) | 0.993 | 0.865 | 4 | Lower West Side, Avondale, West Town, Near West Side, Lincoln Park |

**The set is fairly robust; the order is not.** First place flips between Near West Side, Near North Side and Lower West Side. Lowering U1 to 0.15, raising U6 to 0.35 or restoring BV to 0.10 puts Lower West Side first again.

### 8.5 A variant explored in the explorer: v4 with U3 off and U6 at 26%

The user tried v4 with U3 off and U6 at 26% (U6 26%, U1 25%, B1 20%, U4 10%, M4 5%, M6 5%, U2 4%, BV 3%, M1 2%).

| Chicago rank | Area | Distance | Share of 500 draws in the top 5 |
|---|---|---|---|
| 1 | Near North Side | 1.490 | 88.4% |
| 2 | Near West Side | 1.491 | 92.6% |
| 3 | Lower West Side | 1.540 | 77.2% |
| 4 | West Town | 1.547 | 95.6% |
| 5 | Avondale | 1.558 | 80.8% |

**First place is a tie.** Across 500 weight draws, Near North Side is first in 35%, Near West Side in 31%, Lower West Side in 22% and West Town in 10%. Reading this as "select Near North Side" is not supported.

**Reading the explorer's matrix.** It shows what *separates* Brás from an area, not what supports the match. A family supports a match where that area's part of $D^2$ is smaller than its competitors' parts:

| Part of $D^2$ | Near North Side | Near West Side | Lower West Side | West Town | Avondale |
|---|---:|---:|---:|---:|---:|
| B1 | **0.024** | 0.432 | 0.372 | 0.127 | 0.123 |
| U1 | **0.324** | 0.347 | 1.273 | 1.264 | 1.237 |
| U6 | 1.018 | 1.141 | **0.551** | 0.823 | 0.776 |
| BV | 0.459 | 0.155 | 0.012 | 0.019 | 0.000 |
| U2 | 0.250 | 0.085 | 0.000 | 0.004 | 0.004 |
| U4 | 0.071 | 0.001 | 0.130 | 0.088 | 0.215 |
| $D^2$ | 2.220 | 2.222 | 2.371 | 2.393 | 2.429 |

- **B1 and U1 support Near North Side.** Its coverage is as exceptional for Chicago (0.375 against a 0.224 median) as Brás's is for São Paulo, and its land is far less residential than the West Town group's.
- **U6 works against it.** That is its largest remaining gap: retail log-ratio −0.02 against Brás's +1.37, making & storing −0.49 against +0.29. Height and jobs also work against it, kept small by their 3% and 4% weights.

### 8.6 Match strength and interpretation

- **Match strength:** 170th of 173 (weaker than 98% of units' best matches). Only Riverdale, Marsilac and O'Hare have weaker best matches.
- **Reading.** v4 is the version most faithful to what Brás *is*, and it finds Chicago's commercial edges of downtown: Near West Side and Near North Side. It also shows most clearly that Brás has no Chicago counterpart. The areas it prefers come closer than others on commercial land and, for Near North Side, on building coverage, but not on the kind of commerce (§10.4).
- **Limits added.**
  - The low weights on height, street density and residents (3%, 2%, 1%) mean the model largely ignores how tall, how fine-grained and how populated a candidate is.
  - The question itself was chosen after v3's results were seen.
  - Commerce is double counted, now with high weights on both U1 shares.
  - The weight draws vary family weights only; the inner U1 weights, the most consequential choice, are tested only by named alternatives.

## 9. Across versions

### 9.1 Brás's closest Chicago areas in each version

| Version (primary fit) | 1 | 2 | 3 | 4 | 5 | First Chicago area's rank among all 172 | Loop's rank of 77 |
|---|---|---|---|---|---|---|---|
| v1 hybrid R1 | West Town | Avondale | Logan Square | Lincoln Park | Lower West Side | 11 | 69 |
| v2 hybrid R1 | West Town | Avondale | Logan Square | Lincoln Park | North Center | 12 | 67 |
| v3 | Lower West Side | Avondale | West Town | McKinley Park | Logan Square | 5 | 52 |
| v4 | Near West Side | Near North Side | Lower West Side | West Town | Avondale | 8 | 10 |

Over all 20 published fits (v1 and v2 × three scalings × three runs, v3, v4):
- **West Town is in Brás's Chicago top five in all 20.**
- **Avondale is in 17**; it is missing only from all-absolute R2 in v1 and all-absolute R1 and R2 in v2.
- **Lower West Side is first in every all-relative fit of v1 and v2**, and in v3.
- **Near North Side** appears only under all-absolute scaling and in v4. **Near West Side** appears only in v4.

### 9.2 Match strength in all 20 fits

Brás's position among the 173 units' best cross-city distances (1 = closest), computed from each fit's published distance table:

| Fit | R1 | R2 | R3 |
|---|---|---|---|
| v1 hybrid | 148 | 132 | 130 |
| v1 all-absolute | 159 | 160 | 136 |
| v1 all-relative | 133 | 132 | 139 |
| v2 hybrid | 154 | 125 | 137 |
| v2 all-absolute | 163 | 162 | 136 |
| v2 all-relative | 146 | 138 | 152 |
| v3 | 165 | | |
| v4 | 170 | | |

- **In every fit Brás's best Chicago match is weaker than the median unit's**, and weaker than at least 72% of units' (the best position is 125th, v2 hybrid R2). Distances themselves are not comparable across fits; positions are.
- **R1 is the run the versions are built on, and Brás's position worsens as the distance targets its distinctive traits:** 154th under v2 hybrid, 165th under v3, 170th under v4. That reflects how distinctive Brás is. It does not make v4 more correct: v4 encodes Brás's profile by design, and no external check ranks the versions.
- Under v4, the full list puts Vila Matilde ↔ Portage Park first (0.305), the median unit at 0.591 (Mount Greenwood ↔ Cursino), the Loop ↔ República at 146th (0.842), Pari ↔ Lower West Side at 168th (1.411) and Brás ↔ Near West Side at 170th (1.476). Only Riverdale, Marsilac and O'Hare are weaker (1.545–1.820).

### 9.3 What the settings decide

| Emphasis | Versions | Brás's closest Chicago areas | What they share with Brás | Where they differ |
|---|---|---|---|---|
| Physical fabric, absolute where measured alike | v1, v2 hybrid | West Town, Avondale, Logan Square, Lincoln Park | fine grid, old dense mixed fabric, street layout, parcels | far less building coverage; residential land; activity mix |
| Position within each city | v1, v2 all-relative; v3 | Lower West Side, McKinley Park, Avondale, West Town | as fine-grained, busy and industrial-commercial for Chicago as Brás is for São Paulo | mostly residential or industrial land, not commercial |
| Brás's distinctive traits | v4 | Near West Side, Near North Side, Lower West Side, West Town | commercial land, building coverage (for their city) | services-and-office business mix; taller, more jobs |

Each row is a defensible reading of "resembles Brás". The rows agree on a stable core: West Town and Avondale, with Lower West Side whenever position within each city matters. They disagree on the commercial edge of downtown, which is close only when Brás's distinctive traits are weighted.

### 9.4 The model and a web search

**The concern.** A web search lists the Loop and nearby areas as Chicago's commercial hubs, and describes v3's top four as mostly residential.

**Check.** The model's own Chicago land use (CMAP 2023):

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

**Conclusion.** The search's facts and the model's data agree; they answer different questions. Chicago's commercial hubs are high-rise office and services centres, while Brás is a low-rise wholesale district of retail and workshops. Under v3 the hubs are far from Brás: the Loop is 52nd (height 34% and activity mix 26% of $D^2$) and Near North Side 35th (height 44%). The model does recognize centres: with the Loop as reference, its closest São Paulo districts are República, Sé and Bela Vista.

### 9.5 Why West Town is in every top five

**How robust it is.** West Town is in Brás's Chicago top five in all 20 published fits. A stress test shows that this holds for almost any weighting, not only the published ones. 5,000 random family weightings were drawn uniformly over all possible mixes of the 12 families, from "one family dominates" to "all equal", with v2's columns and equal weights inside each family. The share of weightings in which each area is in Brás's Chicago top five, then first:

| Scaling | West Town | Next most frequent |
|---|---|---|
| Hybrid | **99%** top five, 60% first | Logan Square 94% / 3%, Avondale 88% / 18%, Lincoln Park 68% / 7% |
| All-absolute | **98%**, 43% first | Lincoln Park 87% / 6%, Lake View 61% / 10%, Near North Side 61% / 37% |
| All-relative | **93%**, 10% first | Avondale 92% / 17%, Lower West Side 82% / 32%, McKinley Park 77% / 29% |

**Why: West Town is the only area near the top on both halves of Brás's profile.** Split the families into two groups:
- **Brás's extremes:** building coverage (B1), land use (U1) and activity (U6), where Brás is among São Paulo's most unusual districts;
- **Brás's ordinary traits:** streets, blocks, parcels, height, jobs, residents and transit (M1, M3, M4, M6, M7, BV, U2, U3, U4), where Brás is middling or moderately high.

Then rank every Chicago area on each group alone (v2 hybrid, equal weights within each group):

| Area | Rank on Brás's extremes | Rank on Brás's ordinary traits | Overall rank |
|---|---:|---:|---:|
| **West Town** | 3rd | **1st** | **1st** |
| Avondale | 2nd | 5th | 2nd |
| Logan Square | 8th | 2nd | 3rd |
| Lincoln Park | 10th | 4th | 4th |
| Lower West Side | 6th | 15th | 7th |
| Near West Side | 18th | 34th | 22nd |
| Near North Side | **1st** | 59th | 37th |
| Loop | 7th | 71st | 67th |

Near North Side is the closest of all on Brás's extremes, but it is 76th on height, 66th on jobs and 63rd on parcels, so it falls to 37th overall. The Loop does the same at 67th. Avondale and Logan Square are close on both halves, which is why they follow West Town.

**1. On Brás's extremes, no Chicago area is close, and specialists beat West Town one feature at a time.** On each extreme feature, a few Chicago areas come much closer than West Town; see "Brás's extreme features, one by one" below. Each of those specialists pays heavily on another extreme feature. Ranks among the 77 areas on each part (v2 hybrid):

| Area | Coverage (B1) | Land use (U1) | Business intensity (U6) | Business mix (U6) | Extremes combined |
|---|---:|---:|---:|---:|---:|
| Near North Side | 1 | 3 | 1 | 53 | 1 |
| Avondale | 11 | 12 | 19 | 16 | 2 |
| **West Town** | 13 | 10 | 5 | 41 | 3 |
| Lower West Side | 19 | 8 | 2 | 17 | 6 |
| Loop | 7 | 2 | 21 | 64 | 7 |
| Lake View | 2 | 34 | 16 | 72 | 19 |
| McKinley Park | 38 | 6 | 30 | 5 | 17 |
| New City | 43 | 9 | 35 | 8 | 21 |
| Near South Side | 25 | **1** | 28 | 73 | 22 |
| Armour Square | 61 | 4 | 14 | 68 | 34 |
| Fuller Park | 71 | 5 | 12 | 30 | 47 |

West Town is never the closest on an extreme feature. It is the most even across them: 5th to 13th on three of the four parts, and 41st on the business mix. Under all-relative scaling it is 4th on the extremes combined.

**2. On Brás's ordinary traits, West Town is the closest of all.** Its gap ranks among the 77 areas, as the hybrid scaling reads each column:
- street hierarchy 4th, parcel density 5th, street density 6th (absolute values);
- business intensity 5th, transit 9th, jobs 10th (within each city);
- residents 10th (absolute values).

**3. No weak spot.** For every candidate, rank each of the 12 families' parts of the distance among the 77 areas. Under v2 hybrid, West Town has the best average rank, with only one family in the worse half: block size, at 43rd. Logan Square and McKinley Park are about as even but farther overall. Avondale, Lincoln Park, Lower West Side and the two Near areas each have a family ranked 58th–76th, so a weighting that stresses that family pushes them out of the top five. No family does that to West Town.

| v2 hybrid | Mean family rank | Families in the worse half | Worst family rank |
|---|---:|---:|---:|
| **West Town** | **15.5** | 1 | 43 |
| Logan Square | 16.9 | 2 | 44 |
| Avondale | 17.3 | 1 | 58 |
| McKinley Park | 21.2 | 1 | 45 |
| Lincoln Park | 21.4 | 2 | 64 |
| Lower West Side | 23.6 | 3 | 63 |
| Near North Side | 26.7 | 3 | 76 |
| Near West Side | 28.9 | 4 | 73 |

**Where the within-city reading costs West Town.** Under all-relative scaling, West Town drops to 52nd on street density and 51st on residents. In absolute terms the two are alike (18.0 and 16.2 km of street per km²). But West Town is dense *for Chicago* (z +0.84 and +0.87), while Brás is ordinary *for São Paulo* (+0.29 and +0.15). There McKinley Park has the best average rank (12.1, no family in the worse half), and Lower West Side and McKinley Park lead. West Town still stays in the top five, 3rd under v2 all-relative and v3, 4th under v4.

**Feature by feature.** The rank column is West Town's gap to Brás among the 77 Chicago areas (1 = closest), under the hybrid scaling's reading of each column:

| Family | Column | Brás | West Town | São Paulo median | Chicago median | West Town's gap rank |
|---|---|---:|---:|---:|---:|---:|
| M1 | Street density (km/km²) | 18.0 | 16.2 | 17.8 | 13.2 | 6 |
| M3 | Typical block (m²) | 27,700 | 20,600 | 28,100 | 23,500 | 43 |
| M4 | Block compactness | 0.676 | 0.697 | 0.554 | 0.697 | 26 |
| M4 | Block elongation | 1.72 | 1.98 | 1.92 | 1.98 | 38 |
| M6 | Major-road share | 31% | 32% | 19% | 22% | 4 |
| M7 | Parcels per km² | 1,997 | 1,503 | 1,748 | 1,177 | 5 |
| B1 | Building coverage | 57% | 30% | 37% | 22% | 13 |
| BV | Height (m) | 14.6 | 12.9 | 13.4 | 9.8 | 34 |
| U2 | Jobs per km² | 13,984 | 3,700 | 3,052 | 944 | 10 |
| U3 | Residents per km² | 10,690 | 7,567 | 11,111 | 4,488 | 10 |
| U4 | Transit (PTAL) | 36.9 | 9.2 | 14.2 | 5.7 | 9 |
| U6 | Businesses per 100 dwellings | 25.8 | 12.3 | 7.0 | 6.6 | 5 |
| U6 | Retail share of businesses | 63% | 15% | 22% | 15% | 33 |
| U6 | Services & offices share | 16% | 44% | 36% | 36% | 65 |
| U6 | Food & drink share | 7% | 18% | 13% | 14% | 69 |
| U1 | Residential land | 15% | 61% | 65% | 68% | 25 |
| U1 | Commerce land | 65% | 19% | 23% | 11% | 9 |
| U1 | Industrial land | 16% | 12% | 5% | 5% | 17 |
| U1 | Institutional land | 4% | 8% | 4% | 9% | 5 |

**Reading.** West Town is **Brás's built-form and intensity twin without its commercial specialization.**
- **Alike:** street density, major-road share, block size and shape, parcel grain and height are close. Both hold a similar number of classified businesses (5,101 in Brás, 5,731 in West Town), and both are busy, transit-served and job-dense for their city.
- **Different:** West Town covers half as much of its land with buildings, is a residential majority, and its businesses lean to services, offices and food instead of retail.
- **Scale:** West Town (11.7 km² of land) is 3.2 times Brás's size. Its own neighborhood piece (5.3 km²) is the 2nd closest neighborhood under v4, and its Chicago Avenue and Grand tract was the closest tract under v2 hybrid (§10).

Choosing West Town claims that Brás's counterpart is a place built and used at the same intensity, not one that does the same trade.

#### Brás's extreme features, one by one

For each feature:
- **Brás:** its value, its rank among São Paulo's districts, and how the model reads it. Building coverage is read on absolute levels (the hybrid scaling), land use and business intensity within each city, and the business mix as city-centred log-ratios (shares shown for readability).
- **At or beyond Brás:** how many Chicago areas reach Brás's value.
- **Gap rank:** West Town's gap to Brás among the 77 areas (1 = closest).

| Feature | Brás | Chicago: lowest – median – highest | At or beyond Brás | Closest Chicago areas, as the model reads it (gap) | Median Chicago gap | West Town (Chicago rank) | West Town's gap | Gap rank |
|---|---|---|---:|---|---:|---|---:|---:|
| Building coverage | 57% (1st of 96); z +2.48 | 5% (O'Hare) – 22% – 37% (Near North Side) | 0 | Near North Side (1.68), Lake View (1.96), Hermosa (2.15) | 3.01 | 30% (13th) | 2.33 | 13 |
| Commerce land | 65% (3rd of 94); z +2.68 | 4% – 10% – 59% (Loop) | 0 | Armour Square (0.02), Loop (0.32), Near South Side (0.32), Near North Side (0.60) | 2.92 | 19% (9th) | 2.06 | 9 |
| Residential land | 15% (3rd lowest of 94); z −2.52 | 27% (Pullman) – 68% – 90% | 0 | Pullman (0.21), Lower West Side (0.36), Near West Side (0.44) | 2.70 | 61% (52nd highest) | 2.30 | 25 |
| Industrial land | 16% (17th of 94); z +0.91 | 0% – 5% – 54% (Burnside) | 19 | Humboldt Park (0.04), North Lawndale (0.06), Brighton Park (0.10) | 1.43 | 12% (25th) | 0.89 | 17 |
| Retail share of businesses | 63% (1st of 96); log-ratio +1.37 | 1% – 15% – 25% (Fuller Park) | 0 | Fuller Park (0.80), West Lawn (0.97), West Elsdon (0.98) | 1.33 | 15% (40th) | 1.30 | 33 |
| Services & offices share | 16% (2nd lowest of 96); −0.45 | 20% (Burnside) – 36% – 58% | 0 | New City (0.00), Englewood (0.03), Calumet Heights (0.07) | 0.46 | 44% (11th) | 0.66 | 65 |
| Food & drink share | 7% (2nd lowest of 96); −0.35 | 0% – 14% – 39% (Armour Square) | 3 | Forest Glen (0.00), Norwood Park (0.01), West Pullman (0.03) | 0.39 | 18% (10th) | 0.73 | 69 |
| Institutions share | 5% (lowest of 96); −0.86 | 13% (McKinley Park) – 24% – 65% | 0 | McKinley Park (0.05), Clearing (0.09), Archer Heights (0.16) | 0.82 | 18% (61st) | 0.52 | 23 |
| Businesses per 100 dwellings | 25.8 (5th of 96); z +1.71 | 2.2 – 6.6 – 42.7 (Loop) | 1 | Near North Side (0.03), Lower West Side (0.29), North Center (0.33) | 1.78 | 12.3 (7th) | 0.40 | 5 |

What the table shows:
- **Brás is out of Chicago's range on six of these features.** No Chicago area reaches its coverage, commerce land, low residential land, retail share, low services share or low institutions share. Chicago's highest retail share (25%, Fuller Park) is under half of Brás's 63%, and its lowest residential share (27%, Pullman) is almost twice Brás's 15%.
- **Within-city scaling makes some of these gaps small.** On commerce land, three areas are within 0.32 SD of Brás's position. Armour Square (39%), the Loop and Near South Side (58–59%) are as exceptional for Chicago as Brás's 65% is for São Paulo; for the Loop and Near South Side the z-score cap at 3 does part of the work. West Town, at 19%, is 9th of 77 and far.
- **West Town's position by feature:**
  - **Moderately close** on commerce land (9th), coverage (13th), industrial land (17th) and business intensity (5th).
  - **Mid-pack** on residential land (25th), institutions (23rd) and retail (33rd).
  - **Among the farthest** on services & offices (65th) and food & drink (69th): its businesses are 44% services and 18% food, against Brás's 16% and 7%.
- **Its business mix as a whole ranks 41st:** the far services and food shares outweigh the closer institutions and retail shares. The activity family still ranks 8th overall, because business intensity (5th) carries half of it.

## 10. Below Community Area scale

Chicago's Community Areas (median 7.2 km² of land) are larger than Brás (3.6 km²), and an area can average a Brás-like piece with unlike ones. Two breakdowns were tested on 13 October 2026.

### 10.1 Method

- **Pieces are built from 2020 census blocks** inside each Community Area (`block_district_pieces`, the support of the U3 and U2 allocations). They nest exactly in the 77 areas, and every family keeps the areas' own allocation of residents, jobs and dwellings.
- **All 21 columns are recomputed** for every piece with the accepted family scripts' own functions. Summing the pieces reproduces each area's published counts, and the non-additive functions reproduce the published area values. The only differences are two gaps in the block support along the Illinois–Indiana line: 0.149 km of street and 0.09% of land.
- **Pieces are scored, not refitted.** Each column is standardized with the fit's own mean and SD (the 77 areas for a relative column, all 173 units for an absolute one) and capped at ±3. The calibration $\beta_b$ and the weights are the 173-unit fit's. A piece therefore has the same distance scale as an area, and it does not change the model, its rankings or its match strength.
- **A fair yardstick.** The best of many small pieces can beat the best of 77 areas by chance, because there are more candidates and small units are more extreme. Each result is therefore compared with what every São Paulo district gains from the same breakdown.

### 10.2 Census tracts (first attempt; superseded)

2020 census tracts gave 801 published pieces (median 0.5 km², 10 per area); slivers under 5% of their tract's land or 0.05 km² were left out. The user replaced them the same day because a tract is about seven times smaller than Brás. Results: [`chicago_tract_breakdown_2026_10_13`](../../analysis/results/Chicago/chicago_tract_breakdown_2026_10_13/README.md).

| Settings | Closest whole area | Tracts closer than it | Best tract | Best ÷ best area | Typical São Paulo district | Districts that gain more than Brás |
|---|---|---|---|---|---|---|
| v4 | Near West Side 1.476 | 22 | Belmont Cragin 1901 (Diversey and Cicero), 1.116 | 0.756 | 1.006 | 4 |
| v3 | Lower West Side 1.182 | 11 | Humboldt Park 2305 (North Ave), 0.945 | 0.800 | 1.009 | 9 |
| v2 hybrid R1 | West Town 1.096 | 9 | West Town 2429 (Chicago Ave and Grand), 0.939 | 0.857 | 0.857 | 48 |
| v2 all-relative R1 | Lower West Side 0.963 | 4 | McKinley Park 8404 (Ashland, 35th, Archer), 0.883 | 0.917 | 0.971 | 33 |

- **The close tracts are commercial corridors inside residential areas.** Their establishments line one or two streets, according to the Overture place addresses: Chicago Ave and Grand (West Town), Ashland, 35th and Archer (McKinley Park), Clark and Howard (Rogers Park), North Ave (Humboldt Park), Clybourn and Armitage (Lincoln Park), Diversey and Cicero (Belmont Cragin), and Pilsen's 18th St and Ashland (Lower West Side). Their commerce shares are 16–41% of occupied land, against Brás's 65%.
- **Under v4 and v3 the gain is specific to Brás:** a typical São Paulo district gains nothing, while Brás gains 24% and 20%. Under v2 hybrid, Brás's gain is the typical one.
- **Pilsen alone does not help consistently.** Under v4 and v2 hybrid, its 18th St and Ashland tracts beat every whole area. Under v3 and v2 all-relative, the whole Lower West Side is closer than any of its tracts.
- **Thin data.** 480 of the 801 tracts have fewer than 100 establishments, so their U6 mix is noisy.

### 10.3 City neighborhoods (current)

The City of Chicago's 98-neighborhood map (layer bbvz-uum9, which the City calls approximate and unofficial) is cut inside each area: each block piece goes to the neighborhood holding its centre. Results: [`chicago_neighborhoods_2026_10_13`](../../analysis/results/Chicago/chicago_neighborhoods_2026_10_13/README.md).
- **102 published pieces** cover 99.99% of the land, with a median of 5.1 km² (Brás 3.6 km²). Only 6 have fewer than 100 establishments.
- **13 areas split:** Near North Side and West Town into 5; Near West Side and Loop into 4; Lake View and Lincoln Park into 3; Logan Square, Austin, Near South Side, Armour Square, Hyde Park, Woodlawn and Edgewater into 2.
- **The other 64 keep one neighborhood equal to the area.** Lower West Side is among them, so Pilsen cannot be isolated with this map.
- The smallest pieces are downtown: Greektown 0.14 km², Printers Row 0.20 km², Millennium Park 0.26 km².

| Settings | Closest whole area | Neighborhoods closer than it | Best neighborhood | Best ÷ best area | Typical São Paulo district | Districts that gain more than Brás | Best neighborhood's match strength (share of units' best area matches that are closer) |
|---|---|---|---|---|---|---|---|
| v4 | Near West Side 1.476 | 6 of 102 | Bucktown (Logan Square), 1.256 | 0.851 | 1.000 | 3 | 95% |
| v3 | Lower West Side 1.182 | 2 | United Center (Near West Side), 1.140 | 0.964 | 1.000 | 11 | 95% |
| v2 hybrid R1 | West Town 1.096 | 1 | Wicker Park (West Town), 1.095 | 0.999 | 1.000 | 22 | 88% |
| v2 all-relative R1 | Lower West Side 0.963 | 2 | United Center (Near West Side), 0.930 | 0.966 | 1.000 | 9 | 81% |

Inside v4's leading areas:

| Area (v4 distance) | Its neighborhoods (v4 distance) |
|---|---|
| Near West Side (1.476) | United Center 1.348, West Loop 1.386, Greektown 1.698, Little Italy and UIC 2.050 |
| Near North Side (1.500) | River North 1.379, Streeterville 1.752, Rush & Division 1.767, Old Town 1.975, Gold Coast 2.488 |
| West Town (1.540) | West Town 1.322, Wicker Park 1.662, Ukrainian Village 1.944, East Village 1.949, Humboldt Park 2.264 |
| Loop (1.791) | Loop 1.864, Printers Row 2.445, Millennium Park 2.774, Grant Park 3.350 |

Findings:
1. **The gain is modest and specific to the Brás-focused settings.** Under v4, Brás's best neighborhood is 15% closer than its best area, while a typical São Paulo district gains nothing (median ratio 1.000), and only 3 districts gain more than Brás. Under v3 and v2 all-relative the gain is 3–4%; under v2 hybrid there is none.
2. **The same few pieces recur.**
   - Under v4: Bucktown 1.256, West Town's own neighborhood 1.322, United Center 1.348, River North 1.379, West Loop 1.386, Lincoln Park 1.462.
   - **United Center beats its whole area (Near West Side) under all four settings**, and is first under v3 and v2 all-relative.
   - River North beats Near North Side under v4 and v3.
3. **Still not close.** The best neighborhood is farther from Brás than 81–95% of the units' best area-level cross-city matches, depending on the settings.

### 10.4 Why the closest neighborhoods still miss

Under v4, each family's share of the squared distance:

| Piece | $D$ | U6 | U1 | B1 | BV | U2 | M4 | U4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Bucktown | 1.256 | 39% | 18% | 8% | 0% | 0% | 20% | 8% |
| West Town (neighborhood) | 1.322 | 38% | 40% | 10% | 2% | 1% | 3% | 2% |
| United Center | 1.348 | 36% | 24% | 33% | 1% | 0% | 1% | 2% |
| River North | 1.379 | 48% | 3% | 0% | 24% | 13% | 4% | 5% |
| West Loop | 1.386 | 53% | 2% | 1% | 19% | 10% | 1% | 3% |
| Near West Side (whole area) | 1.476 | 50% | 16% | 20% | 7% | 4% | 1% | 0% |

And their profiles, each column read within its own city (z), with the raw value in brackets:

| | Brás | Bucktown | West Town | United Center | River North |
|---|---|---|---|---|---|
| Commerce share of occupied land | 2.68 (65%) | 2.40 (36%) | 0.93 (22%) | 1.10 (23%) | 2.90 (41%) |
| Residential share | −2.52 (15%) | −1.02 (48%) | −1.06 (47%) | −1.94 (33%) | −2.00 (32%) |
| Establishments per dwelling | 1.71 | 1.91 | 1.61 | 1.74 | 2.20 |
| Footprint coverage | 1.96 (57%) | 1.18 (30%) | 1.08 (29%) | 0.32 (24%) | 2.16 (37%) |
| Built height | 0.18 (15 m) | 0.46 (12 m) | 0.92 (14 m) | 0.71 (13 m) | 3.00 (26 m) |
| Job density | 0.94 | 1.14 | 1.44 | 1.21 | 3.00 |
| Retail in the business mix (log-ratio) | +1.37 | +0.15 | +0.08 | −0.06 | −0.08 |
| Services & offices in the mix (log-ratio) | −0.45 | +0.39 | +0.34 | −0.09 | +0.37 |

The near-matches fall into two types, and each misses Brás in a different way:
- **Downtown edge (River North, West Loop).** These match Brás's commercial intensity, and River North its coverage too, but they are high-rise and office-based: height and jobs sit at the z = 3 cap and make up 29–37% of their remaining distance.
- **Mixed neighborhoods west and northwest of the Loop (Bucktown, West Town, United Center).** These match Brás's low-rise height, job density and business intensity, but have less commercial land and much less ground covered by buildings. U1 and B1 make up 26–57% of their remaining distance; for United Center, coverage alone is 33%.

**The gap none of them closes is the retail mix.** U6 is 36–53% of every leading piece's remaining distance. Business intensity is matched (z 1.6–2.2 against Brás's 1.71); the mix is not. Brás's businesses lean strongly to retail (+1.37), while every leading Chicago piece is near zero on retail and leans to services and offices. Chicago has commercial places, but at Brás's scale none with its retail and wholesale character; the tracts (§10.2) suggest that character exists only along single commercial streets.

**One reading caution.** All-relative scaling compares each place within its own city. Bucktown's 36% commerce is as exceptional for Chicago (z 2.40) as Brás's 65% is for São Paulo (z 2.68). That is why it ranks close, although in absolute terms it is about half as commercial.

## 11. What choosing a place means

Every choice below is the **least different** place under one reading of "like Brás", never a close match (§1). In the tables, "matches Brás on" lists the families on which the place is among the 10 closest of the 77 Chicago areas under that version. "Main differences" lists the families with the largest shares of its remaining squared distance.

### 11.1 The claim behind each version's top three

**v1 and v2 (hybrid scaling, equal weights): "the same physical fabric."** Top three: West Town, Avondale, Logan Square (the same in both versions).

*Hypothesis: X is built like Brás: an old, fine-grained, mixed street fabric with comparable street density, parcel grain and residents; it is not a commercial district.*

| | Matches Brás on | Main differences |
|---|---|---|
| West Town | street hierarchy, parcels, street density, business intensity, transit, jobs, residents | coverage 38–40%, activity 22–23%, land use 15–18% |
| Avondale | height, activity, street density, street hierarchy | coverage 35–36%, activity 19–20%, land use 15–17% |
| Logan Square | street density, jobs, parcels, coverage, residents | coverage 34%, activity 22%, land use 20–21% |

What you accept: 61–69% residential land, about 20% commerce (7th–9th in Chicago) and half Brás's building coverage. West Town is the most robust choice in the project (§9.5).

**v3 (each place read within its own city; weights on land use and activity): "the same position in its city."** Top three: Lower West Side, Avondale, West Town.

*Hypothesis: X occupies a place in Chicago like Brás's in São Paulo: an unusually busy, working, mixed area for its city.*

| | Matches Brás on | Main differences |
|---|---|---|
| Lower West Side | residents, activity (the closest of all 77), jobs, block shape, street hierarchy, land use | land use 46%: 49% industrial, 13% commerce |
| Avondale | height, activity, street hierarchy | land use 41%, activity 37% (63% residential) |
| West Town | activity, transit, jobs | land use 39%, activity 38% (61% residential) |

What you accept: a working district of industry and workshops, or a mixed residential neighborhood, instead of a commercial one. Choosing Lower West Side means "Brás's counterpart is Chicago's working, industrial-commercial inner area". It is v3's most stable reading: its top four hold in all 500 weight draws.

**v4 (Brás's distinctive traits, read within each city): "the same exceptional traits."** Top three: Near West Side, Near North Side, Lower West Side.

*Hypothesis: X reproduces, for Chicago, the traits that make Brás exceptional in São Paulo: commercial land, little housing, business intensity, building coverage and transit.*

| | Matches Brás on | Main differences |
|---|---|---|
| Near West Side | transit, residents, land use; business intensity (10th) | activity mix 50%, coverage 20% |
| Near North Side | business intensity (the closest of all 77), coverage, land use, street hierarchy, transit | activity mix 43%, height 20%, land use 14% |
| Lower West Side | residents, activity (the closest of all 77), jobs, block shape, street hierarchy | land use 54% (industrial) |

What you accept: for the two Near areas, commerce of offices and services instead of retail, and for Near North Side towers too; for Lower West Side, industry instead of commerce. First place flips among the three under small weight changes (§8.4), so choose by which difference the study can live with, not by rank.

### 11.2 Under v4, are Near North Side and Near West Side "the most commercial, activity-intensive and dense" areas?

Only partly. Ranks within Chicago's 77 areas (Brás: within São Paulo's 96):

| Trait | Near North Side | Near West Side | Loop | Brás |
|---|---|---|---|---|
| Commerce share of land | 33% (4th) | 25% (6th) | 59% (1st) | 65% (3rd) |
| Businesses per 100 dwellings | 15.0 (4th) | 19.8 (2nd) | 42.7 (1st) | 25.8 (5th) |
| Jobs per km² | 29,855 (2nd) | 11,054 (3rd) | 122,514 (1st) | 13,984 (15th) |
| Residents per km² | 15,688 (1st) | 4,661 (36th) | 10,739 (5th) | 10,690 (52nd) |
| Building coverage | 37% (1st) | 26% (22nd) | 30% (7th) | 57% (1st) |
| Height | 28 m (2nd) | 18 m (4th) | 42 m (1st) | 15 m (32nd) |
| Transit (PTAL) | 20.6 (2nd) | 14.6 (4th) | 38.9 (1st) | 36.9 (3rd) |
| Retail share of businesses | 13% | 11% | 9% | **63%** |

- **Defensible:** both are among Chicago's most commercial and activity-intensive areas outside the Loop (top 6 on commerce land, top 4 on businesses per dwelling). Near North Side is also among the densest (1st in residents and coverage, 2nd in jobs). Near West Side is dense in jobs only (3rd), not in residents (36th) or coverage (22nd).
- **Not defensible:**
  - "The most commercial hub": the Loop is 1st on every measure above, and v4 ranks it 10th.
  - "The same kind of commercial district": their businesses lean to services and offices (40–43%), against Brás's 63% retail. Splitting the activity family shows it. Business intensity is matched: Near North Side z 1.74 against Brás's 1.71, the closest of all 77; Near West Side is 10th. The business mix is not: they rank 53rd and 55th of 77.
  - "v4 chose them for their density": v4 gives residents 1% and height 3% of the weight, so it hardly evaluates density.
- **A defensible sentence:** *"Under v4, Near North Side and Near West Side are the Chicago areas whose commercial land, business intensity and low share of housing are as exceptional within Chicago as Brás's are within São Paulo. Unlike Brás, their commerce is high-rise and led by offices and services, not retail."*

### 11.3 The trade-off

No Chicago area combines Brás's commercial profile with its retail-and-workshop character. Each choice keeps one side of Brás and gives up another:

| Choice | Keeps | Gives up |
|---|---|---|
| Near North Side, Near West Side (v4) | how commercial, busy and non-residential Brás is, for its city | what it sells (retail), and its low-rise form |
| Lower West Side (v3, v4) | the closest business mix (activity mix 17th of 77 under v4, against 53rd–55th for the Near areas), working character, residents | commercial land: its land is industrial |
| West Town (v1, v2; top five everywhere) | built form, grain and intensity; the most robust choice (§9.5) | commercial specialization: residential majority, services-led mix |

The write-up should say which side of Brás the study needs, and name the place that keeps it.

## 12. Open questions and recommendations

1. **Settle the question before any more tuning.** Each change of weights has moved first place. Name one reading:
   - least different overall profile: v2 hybrid R1 as the neutral baseline;
   - Brás's distinctive traits: v4;
   - Chicago's commercial hub: the Loop or Near North Side, which needs no similarity model.

   Report the others beside it. The recommended pairing is **v4 as the main reading and v2 as the baseline**.
2. **Report a group with its match strength, never a single winner** (§1 item 7). Do not adopt the U3-off variant (§8.5): it turns one near-tie into the opposite near-tie.
3. **Test scale like for like.** Neighborhoods compare Chicago pieces with whole São Paulo districts. Splitting São Paulo's districts the same way, for example by census tract groups, would show whether Brás itself is a mosaic and whether its retail core finds a closer Chicago piece.
4. **Fix the commerce double count in a new version.** Commerce enters U1 and U6 intensity, and U1's plain shares count "commercial instead of residential" twice. A log-ratio treatment of U1, like U6's, would remove the second count.
5. **External check.** Nothing outside the model validates similarity. Match strength and stability describe the model; they do not confirm the matches. A field visit or expert rating of the candidate group would be the first external evidence.
6. **Choosing a place** inside the group: §11 sets out what each choice claims and gives up. At neighborhood scale, take United Center or West Town if low-rise mixed fabric matters most, River North or West Loop if commercial intensity matters most.

## 13. Limits

**Method.**
- **No external truth** (§12 item 5). Evidence comes from each family's checks, São Paulo face validity (Brás's nearest units are its inner-ring neighbours in every version) and the robustness tables.
- **The scaling and the weights are modelling decisions, not findings.** The v3 and v4 weights were set after earlier results were seen. They state questions; they are not estimates.
- **Long-tailed families** (M3 in v1 and v2, M1 in v3) deliver more than their weight.
- **The ±3 cap compresses extremes:** the Loop on jobs, height and transit; River North and West Loop under v4; Marsilac on several columns.
- **Commerce is counted twice** from v2 on.

**Instruments.**
- **Relative scaling keeps within-city instrument errors:** RAIS head-office registration, LODES location error, Overture's formal-economy bias, GHSL's compression of tall buildings.
- **Vintages differ:** Overture 2026, Census 2022 and ACS 2020–2024, RAIS 2022 and LODES 2023, IPTU 2026 and CMAP 2023, GHSL 2018.
- **U1 sees primary use only,** so it misses vertical mixing in both cities; U6 counts listed establishments only.

**Units.**
- **Community Areas are larger than Brás,** and the City neighborhood map splits only 13 of them. Pilsen cannot be isolated.
- **Sub-area pieces are scored with the area fit's constants,** so they cannot shift the model's calibration. Small downtown pieces (0.14–0.26 km²) are more extreme than the units the model was fitted on.

## 14. Reproducing

| What | Command (repository `.venv`) |
|---|---|
| v1, v2 (all tables and figures) | `jupyter nbconvert --to notebook --execute --inplace analysis/sp_chicago_model_analysis.ipynb` (v2 is the default; `SP_CHI_MODEL_VERSION=v1` rebuilds v1 into its own folder) |
| v3, v4 | `python analysis/scripts/sp_chicago_model_settings.py v3` (or `v4`) |
| Neighborhood pieces | `python analysis/scripts/chicago_neighborhoods.py` (about 7 minutes) |
| Explorer data and check | `python analysis/scripts/export_viz_data.py`, then `node analysis/tests/check_viz_model.js` |

- Inputs are refused if any table's SHA-256 differs from the one recorded at acceptance. Seed 20261006.
- The explorer reproduces every published distance matrix: v4 to 1.2e-10, v3 to 9.9e-11, and the v2 runs to about 2e-10.
- Match strength (§9.2) is computed from each fit's `distance_*.csv`. The sub-area figures (§10) use the explorer's own code (`viz/model.js`, `projectedDistance`) on `viz/data.js`.
