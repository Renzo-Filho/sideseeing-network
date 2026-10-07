# Simplified composite index: advisor method (A) vs corrected method (B)

Opened 1 October 2026 at the advisor's suggestion; the [Chicago feature-acceptance plan](chicago/MODEL_PLAN.md) was paused briefly, then resumed and fitted on 6 October. Units: 96 São Paulo districts and 77 Chicago Community Areas. **Methods A and B were built and tested under protocol P-AB-1; [methodology report](../analysis/results/SP_CHI/simple_index_ab_2026_10_01/README.md).** Current project status is in [STATUS.md](STATUS.md).

**Evidence rule (user, 1 October 2026):** every number in this page is computed from repository data by a saved script, or comes from an official definition document saved next to its data. Figures from papers or web pages are not used as evidence. A completeness claim requires a demonstrated reference (ground truth) first.

## Study design

```
built_environment = commercial establishments + residential establishments + transportation hubs + building height
network           = number of streets + average street length
index             = built_environment + network          (each factor min–max scaled over both cities pooled)
```

- **Method A — advisor's method, built as stated:** raw counts and averages per unit, min–max over the 173 units pooled, equal weights.
- **Method B — corrected method:** the same counts divided by unit land area before min–max; other corrections listed per component below.
- **Methodology report:** compares A with B to test whether A is biased. The test is run, not presumed: "bias" needs an operational definition fixed before any result is seen (decision D9).

## Decision log

| Date | Decision (user) |
|---|---|
| 1 Oct 2026 | Pooled min–max per factor over both cities (advisor). One index first; component-vector similarity deferred |
| 1 Oct 2026 | Network: streets as the open source labels them, no re-splitting; count and average length |
| 1 Oct 2026 | Build both A and B and compare them in a documented methodology report |
| 1 Oct 2026 | Transportation hubs = subway, metro and bus stations/stops |
| 1 Oct 2026 | Equal weights for this first sketch (D6): each of the six factors weighs the same, so built environment = 4/6 and network = 2/6 of the index |
| 1 Oct 2026 | D8: run the CNEFE address-level check, under the protocol below, fixed before running; also compare OpenStreetMap places with Overture before choosing the commercial source |
| 1 Oct 2026 | Both results are shown in full (D9, partly): method A exactly as the advisor specified, then method B, then the comparison with the tests as proof. The tests and their pass/fail thresholds are still to be approved |
| 1 Oct 2026 | Establishments counted as points (not area by use) |
| 1 Oct 2026 | Divide counts by land area only in method B |
| 1 Oct 2026 | Commercial: Overture Places; completeness check against CNEFE (SP) and ZIP Business Patterns (Chicago) only if it can be easily harmonized |

## Components (current definitions; open items refer to the decisions below)

| Component | Method A | Method B | Source facts (audit) | Open |
|---|---|---|---|---|
| Commercial establishments | Count of Overture Places in the commercial categories | A ÷ land km² | Places in city: Chicago 143,509, SP 446,015 | D1, D2 |
| Residential establishments | Dwellings: Chicago Census 2020 `HOUSING20`; SP CNEFE 2022 private dwellings (`COD_ESPECIE` 1) | A ÷ land km² | SP 4,992,162 private + 4,367 collective dwelling records | D7 |
| Transportation hubs | Count of subway/metro stations and bus stops | A ÷ land km² | See GTFS facts | D3 |
| Building height | Mean Overture `height` of buildings with height | GHSL built-surface-weighted height ([B-family report](harmonization/B_FAMILY_DECISION_REPORT.md)) | See height facts | D4 |
| Number of streets | Count of Overture road segments | A ÷ land km² | Chicago 52,796; SP 189,750 (M1 classes, wholly inside city) | D5 |
| Average street length | Mean segment length | same as A | Median 102.1 m vs 68.4 m | D5 |
| Weights | equal per factor (six factors) | equal per factor (six factors) | — | decided |

## Verified source facts

All from [the source audit](../analysis/results/SP_CHI/simple_index_source_audit_2026_10_01/README.md) (`analysis/scripts/audit_simple_index_sources.py`, run 1 October 2026).

- **Unit size.** Land area: Chicago 1.570–34.521 km² (median 7.393); SP 2.148–206.876 km² (median 9.632). Raw counts in method A therefore carry unit size.
- **Overture Places differ by city in provenance and fields.** Meta is credited on 94.55% of SP records and 58.86% of Chicago records; BrightQuery on 15.76% of Chicago records and none in SP. `operating_status` is filled in Chicago (3,576 `permanently_closed`) and null on all but 14 SP records, so closed places can be removed only in Chicago. Median `confidence` 0.920 (Chicago) vs 0.665 (SP). No taxonomy: 17.35% vs 3.78%.
- **Building height differs by city in provenance.** Overture `height` is present on 749,136 of 832,457 Chicago buildings, credited mainly to USGS Lidar (617,576) and Microsoft ML Buildings (131,166), and on 2,080,386 of 3,144,642 SP buildings, all credited to OpenStreetMap.
- **Transit feeds represent stops differently.** CTA lists 298 `L` platform stops at 143 parent stations (co-located pairs); SPTrans lists 109 metro and 104 CPTM stop records without parent stations. A same-mode bus stop lies within 50 m of 84.7% of CTA bus stops and 52.0% of SPTrans bus stops. CTA has no commuter rail (Metra) or Pace; SPTrans includes CPTM but not EMTU.
- **Segments.** Chicago names are long and shared across units (25.14 segments per name); SP names are short (3.93).

## Reference (ground-truth) assessment for establishment completeness

A reference can support a completeness claim only if it (1) counts the same object, one establishment; (2) covers the whole unit; (3) is independent of Overture; and, for a cross-city claim, (4) is defined the same way in both cities.

**CNEFE 2022 (São Paulo) — not a ground truth for establishment counts.** IBGE *Notas metodológicas n. 04* (saved in `analysis/data/SP/Socioeconomico/CNEFE_2022/docs/`) states that enumerators walk every census sector and record every address and its use type (criteria 2 and 3 met), but also that an address with several establishments may be recorded once with a "multiple" indicator (criterion 1 fails). In the SP file, 18,446 of 570,229 other-purpose records are "multiple" (8,332 up to 10, 2,043 more than 10, 8,071 unknown). The establishment count is therefore only bounded below (607,062 citywide), with no upper bound, and the lower-bound-to-record ratio varies by district from 1.016 (José Bonifácio) to 1.382 (Consolação); Brás has 8,844 records and at least 11,114 establishments. CNEFE remains a valid reference for a different object, *addresses with at least one establishment*, which would require an address-matching rule (decision D8).

**ZIP Codes Business Patterns (Chicago) — not easily harmonized; not done.** The Census Bureau's [CBP methodology](https://www.census.gov/programs-surveys/cbp/technical-documentation/methodology.html) defines an establishment as a single physical location, covers only establishments with paid employees, excludes self-employed, private-household, railroad, agricultural-production and most government employment, and drops ZIP cells with fewer than three establishments (from 2017). Overture Places contains objects outside that universe, no crosswalk exists from Overture's taxonomy to NAICS, and ZIP codes do not nest in Community Areas. Per the user's condition, the check was not run and ZBP was not downloaded.

**Cross-city.** No available reference meets criterion 4, so the relative completeness of Overture Places in Chicago versus São Paulo **cannot be measured with the data we have**. The provenance and field differences above are documented asymmetries, not completeness measurements.

**Dwellings.** The Census 2020 PL 94-171 documentation (saved as `analysis/data/Chicago/tl_2022_17_tabblock20/2020Census_PL94_171_TechDoc.pdf`) defines a housing unit as separate living quarters, including vacant units, and defines group quarters separately. CNEFE separates private (1) from collective (2) dwellings. Whether CNEFE private dwellings include vacant units was not found in the notes read.

## Decisions D1–D9 (all decided 1 October 2026; the user accepted the recommendations)

| # | Decision |
|---|---|
| D1 | Commercial source: Overture Places (P-PLACES-1 result below). Commercial = taxonomy top level `shopping`, `food_and_drink`, `services_and_business`, `lifestyle_services`, `lodging`; records without taxonomy are excluded in both cities |
| D2 | No filter on `operating_status` or `confidence`, so both cities follow the same rule |
| D3 | Hubs = subway/metro stations + bus stops. Stations: Chicago CTA `L` parent stations; SP metro stop records grouped by name. CPTM excluded (no Metra counterpart in the data). Bus stops counted as listed in the feed; merging same-name stops within 50 m is a sensitivity |
| D4 | Height: method A, mean Overture `height` of buildings with height; method B, GHSL built-surface-weighted height |
| D5 | Streets: Overture road segments in the M1 ten classes; each segment assigned whole to the unit containing its midpoint |
| D6 | Each of the six factors has equal weight |
| D7 | SP dwellings = CNEFE private dwellings (`COD_ESPECIE` 1); Chicago = Census 2020 `HOUSING20`, blocks split by a unit boundary allocated by area share (existing U3 method) |
| D8 | CNEFE address-level check run for Overture and OSM (P-PLACES-1) |
| D9 | Both full results are reported; tests and thresholds fixed in protocol P-AB-1 below, before any A or B value was computed |

## Protocol P-AB-1: build and test of methods A and B (fixed 1 October 2026, before any A or B value was computed)

**Units and denominator.** 173 units: 96 SP districts and 77 Chicago Community Areas. Land area = unit minus municipal hydrography (SP `sp_prep_2026_09_10_v3/N02` `land_area_m2`; Chicago `chi_functional_2026_09_16_v2` `hydro_land_m2`).

**Factors** (raw value per unit):

| Factor | Method A | Method B |
|---|---|---|
| C commercial | count of D1 places inside the unit | C_A ÷ land km² |
| R residential | dwellings (D7) | R_A ÷ land km² |
| H hubs | stations + bus stops (D3) inside the unit | H_A ÷ land km² |
| V height | mean Overture `height` (> 0) of buildings whose bounding-box centre is in the unit | GHSL built-surface-weighted height |
| N streets | count of segments (D5) | N_A ÷ land km² |
| L street length | mean length of those segments (m) | same as A |

**Scaling and index.** Each factor min–max scaled over the 173 units pooled; index = sum of the six scaled factors (0–6). Same procedure in A and B.

**Construction checks** (any failure stops the run): 173 unique units and no missing factor values; SP dwellings sum to the CNEFE private-dwelling total; Chicago allocated dwellings plus outside-city remainder equal the `HOUSING20` total of the blocks that intersect the city; commercial counts recomputed by an independent point-in-polygon route match exactly, and per-unit totals by category match the source audit table; every scaled factor has minimum 0 and maximum 1; the index equals the sum of its scaled factors.

**Tests of method bias** (results reported for A and B side by side):

1. **T1, boundary invariance (decisive).** Merge the 96 SP districts into subprefeituras (`analysis/config/sp_district_subprefeitura.csv`) and recompute every factor on the merged units by the same definition (sum counts and land; recombine means from their sums). A factor passes for a merged unit if its value lies within the range of its districts' values. Criterion: a factor is **boundary-invariant** if it passes in at least 95% of subprefeituras with two or more districts; otherwise it **depends on how boundaries are drawn**. The index is tested the same way, using the 173-unit min–max unchanged.
2. **T2, size dependence.** Spearman correlation of each factor and the index with land area, pooled and within each city, with a 95% bootstrap interval (2,000 resamples, seed 20261001). Criterion: **size-dependent** if the interval excludes 0 and |ρ| ≥ 0.3. Real urban structure can also correlate with size (large peripheral districts), so T2 is interpreted together with T1.
3. **T3, agreement.** Spearman correlation between the A and B indices; overlap of the top 10; Brás rank; largest rank shift. Criterion: A and B **substantively disagree** if Spearman < 0.8 or the top-10 overlap is below 7.
4. **T4, city composition.** Units from each city in the top 20 and bottom 20 of each index, against the 77/173 Chicago share of units.
5. **Sensitivity S1.** Bus stops merged (same normalized name within 50 m), in A and B.

### P-AB-1 result (run 1 October 2026; 20 of 20 construction checks passed)

| Test (criterion fixed in advance) | Method A | Method B |
|---|---|---|
| T1 boundary invariance: merged subprefeitura within its districts' range (29 tested) | counts C, R, H, N and the index: 0 of 29, **depend on boundaries**; V and L 29 of 29 | every factor 29 of 29; index 28 of 29, **boundary-invariant** |
| T2 size dependence, index vs land area, Spearman (95% CI) | pooled +0.650 [0.539, 0.740], **size-dependent** in both cities | pooled −0.156 [−0.302, 0.005], not size-dependent; negative within SP (−0.583) and Chicago (−0.300) |
| T3 agreement | Spearman A vs B 0.552 pooled, 0.089 in SP; top-10 overlap 2; Brás rank 106 (A) vs 23 (B): **substantively disagree** | — |
| T4 Chicago units in top 20 / bottom 20 (8.9 expected) | 2 / 19 | 2 / 14 |
| S1 bus stops merged, Spearman with primary | 0.996 | 0.994 |

Application (Brás → Chicago, closest index value): method A picks Auburn Gresham (gap 0.005; its six-factor profile ranks 44th of 77), method B picks Lake View (gap 0.145; profile rank 7th).

Supported conclusion: method A is biased as a measure of urban intensity because it sums counts over units of unequal area; method B removes that bias but inherits the source limits shared by both (uneven Overture coverage; cross-city comparison not validated).

## Protocol P-PLACES-1: source coverage of CNEFE establishment addresses (fixed 1 October 2026, before any matching was run)

**Question.** Of the establishment addresses that IBGE enumerators recorded in São Paulo in 2022, what share has a record in each candidate source, and how evenly does that share vary across districts? This validates the *source* of the commercial factor, which methods A and B share. It measures address coverage, not establishment counts (see the CNEFE assessment).

1. **Reference:** CNEFE 2022 records with `COD_ESPECIE` 4, 5, 6 or 8 and `NV_GEO_COORD` 1, 2 or 3 (address-level coordinates); levels 4–6 are excluded and counted. District from `COD_DISTRITO` via the audited crosswalk. One reference point per record.
2. **Candidates (São Paulo, in city):**
   - Overture Places 2026-08-19.0 with a non-empty primary name, excluding taxonomy top level `geographic_entities`.
   - OpenStreetMap nodes and ways (way centroid) with a `name` and at least one of `shop`, `amenity`, `office`, `craft`, `healthcare`, `tourism`; `amenity` values that are street furniture or infrastructure are excluded (`bench, waste_basket, waste_disposal, recycling, parking, parking_space, parking_entrance, bicycle_parking, motorcycle_parking, toilets, drinking_water, post_box, telephone, vending_machine, shelter, fountain, clock, bicycle_rental, charging_station, taxi, bus_station, grit_bin, hunting_stand, loading_dock`). Snapshot date recorded.
3. **Distance:** planar metres in EPSG:31983; d = 25, 50 and 100 m.
4. **Match types:** (P) proximity, any candidate within d; (N) name, a candidate within d whose name matches: lowercase, accents and punctuation removed, tokens of at least 3 characters, stopwords removed (`de da do das dos del la las los el the and com para ltda eireli epp sa`), overlap coefficient |A∩B| / min(|A|,|B|) ≥ 0.5.
5. **Chance baseline:** the same computation with every reference point displaced 500 m in a uniformly random direction (seed 20261001). Reported beside each observed rate; the difference is the coverage above chance. Proximity matches in dense districts are expected to be largely chance.
6. **Outputs:** citywide and per-district rates for each source × d × match type, by `COD_ESPECIE`; per-district spread (min, median, max) and Spearman correlation of district rate with district reference-point density.
7. **No automatic choice.** The results are reported; the user chooses the source.

**Chicago (no reference exists):** descriptive only. Counts per Community Area for both sources, and agreement in both directions (share of one source's records with a name match in the other within 50 m). Agreement is not completeness.

### P-PLACES-1 result (run 1 October 2026; [results](../analysis/results/SP_CHI/places_cnefe_coverage_2026_10_01/README.md))

OpenStreetMap came from Geofabrik extracts (the public Overpass servers timed out repeatedly). After the protocol filters, São Paulo has 445,419 Overture and 24,545 OSM records in the city; Chicago 143,229 and 19,856. Of 600,253 CNEFE establishment addresses:

| Name match within 50 m (primary) | Observed | Chance (500 m displaced) | District range of observed − chance |
|---|---:|---:|---|
| Overture Places | 20.10% | 2.04% | 3.20% to 35.16% (median 18.08%) |
| OpenStreetMap | 2.35% | 0.13% | 0.22% to 13.41% (median 1.64%) |

Under the identical rule, Overture matches about 8.6 times as many CNEFE addresses by name as OSM (20.10% vs 2.35%), and OSM is not a superset: 59.18% of São Paulo OSM records (75.51% in Chicago) have a name match in Overture, while 4.02% of Overture records (12.14%) have one in OSM. Both sources cover CNEFE unevenly across districts, and the excess correlates with district establishment density (Spearman 0.319 Overture, 0.310 OSM). Proximity without names is mostly chance for Overture (92.39% observed vs 74.30% displaced at 50 m). Absolute name-match rates are low for every source because CNEFE names are enumerator free text; the comparison between sources is the informative result.

## Continuation

Done (1 October 2026):

1. Overture Places 2026-08-19.0 fetched for both cities: `analysis/data/{Chicago,SP}/overture_2026_08_19/place/` (manifests with SHA-256), via `analysis/scripts/acquire_harmonized_overture.py <city> place` (the script now maps `place` to the `places` theme).
2. Source audit: `analysis/scripts/audit_simple_index_sources.py` → `analysis/results/SP_CHI/simple_index_source_audit_2026_10_01/` (about 3 min, peak 3.6 GB; the SP building file is streamed through its R-tree because a full read exhausted memory and crashed the session).
3. OpenStreetMap places: Geofabrik `illinois-latest` and `sudeste-latest` (MD5 verified) in `analysis/data/shared/osm_geofabrik/`, extracted with `analysis/scripts/acquire_osm_places.py <city>` to `analysis/data/{Chicago,SP}/osm_2026_10_01/`; coverage test `analysis/scripts/evaluate_places_against_cnefe.py` → `analysis/results/SP_CHI/places_cnefe_coverage_2026_10_01/`.
4. Official definition documents saved: IBGE CNEFE notes n. 01 and n. 04; Census 2020 PL 94-171 technical documentation.

`analysis/data/` is git-ignored, so these inputs exist only locally. To restore them: rerun the Overture and OSM acquisitions above (Geofabrik files from https://download.geofabrik.de/north-america/us/illinois-latest.osm.pbf and https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf; later downloads will be newer snapshots), and download [CNEFE notes n. 04](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102091.pdf), [CNEFE coordinates note n. 01](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102063.pdf) and the [Census 2020 PL 94-171 technical documentation](https://www2.census.gov/programs-surveys/decennial/2020/technical-documentation/complete-tech-docs/summary-file/2020Census_PL94_171Redistricting_StatesTechDoc_English.pdf). The CNEFE São Paulo file itself (`3550308_SAO_PAULO.csv`) was already on disk before this work.

5. Methods A and B and tests T1–T4, S1: `analysis/scripts/build_simple_index_ab.py` → `analysis/results/SP_CHI/simple_index_ab_2026_10_01/` (README = methodology report; about 2 min, peak 1.6 GB).
7. Curio dataflow (2 October 2026): project “Composite urban index: method A and method B” (`4e6b8d2a-af2e-44f2-9ce9-32b1646553f3`, user 3), method A lane on top and method B below, each ending in a top-10 table and a five-closest-to-Brás table. Code, installer and validation in `analysis/curio_nodes/simple_index/` (reproduces the published indices to within 1e-15).
6. Notebook `analysis/simple_index_ab.ipynb`: builds A and B and runs T1–T4 and S1 by calling the same functions, with methodology in markdown cells; its last cell asserts it reproduces the published tables exactly.

Rerun order if an input changes: source audit, places coverage test, A/B build. Possible next steps (not decided): share the report with the advisor; revisit the sign of average street length; a component-vector similarity model.

## Candidate sources found but not evaluated

Not used as evidence; no figures quoted: Foursquare OS Places, OpenStreetMap POIs, EULUC-Globe, GHS-BUILT-S non-residential surface, GHS-OBAT, official parcel use (CMAP LUI 2023, SP IPTU `TIPO DE USO DO IMOVEL`).
