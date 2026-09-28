# São Paulo–Chicago harmonization: execution documentation

**New scope review:** the user requested restoration of the prior [six-family proposal](SIX_FAMILY_PLAN_REASSESSMENT.md) for renewed pros/cons assessment. The prior rejection remains part of the historical record; the sealed H4 matrix is unchanged. Scope and scientific acceptance remain open, and no fit or bulk processing has resumed. The [model status](../MODEL_STATUS.md) is the current entry point.

**Current work mode:** the user paused large-scale processing for a manual [source/entity definition review](ENTITY_SOURCE_DECISION_BRIEF.md). The [model status](../MODEL_STATUS.md) is the current entry point. No fit or new bulk rebuild is authorized during this review.

**Current status — 22 September 2026:** six supplied Microsoft tiles were organized and the paired footprint pilot is complete. The user has reopened the prior [six-family proposal](SIX_FAMILY_PLAN_REASSESSMENT.md) for scope review; the original [13-family route](CHICAGO_13_FAMILY_COMPLETION_LEDGER.md) remains documented. The scope decision and semantic gates are open, and no new shared model has been fitted. Earlier contrary statements in this cumulative record are historical.

## Local rail envelopes and M1/M6 matched-road review

The next rail-source check found a genuine Chicago CMAP LUI rail right-of-way class, 1511, documented in the [CMAP field guide](https://cmap-repos.github.io/LUI-wiki/1500_TransportationCommunicationsUtilities.html). São Paulo's twelve `area_influencia_trem` polygons are labelled influence/domain and do not certify the same right-of-way boundary. `review_local_rail_envelopes_v1.py` used the two only as city-specific block-reference diagnostics, never as common inputs. [Eight-unit results](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v4_local_rail/README.md) show modest Chicago changes (CHI:30 reference IoU≥.50 match .149→.169) but a Brás decline (.915→.902) and new narrow polygons. This does not close M3/M4.

The work then audited the independent matched-source M1/M6 gate rather than continuing to tune unverified block exclusions. [The 173-unit M1/M6 review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md) reconstructs all ten class shares and M1 numerator/denominator values, compares each city's independent local road baseline, samples linework at 5/15/30 m tolerances in ten pilots, and attributes the two largest local-network outliers by raw Overture class. Chicago and SP M1 Spearman correlations against their local networks are .961 and .976; median Overture/local ratios are 1.048 and .936. Six Chicago and seven SP units fall outside a 0.85–1.15 ratio band. The sampled geometry method passed one synthetic fixture; it is an approximate length-weighted positional diagnostic, not exact overlap.

O'Hare's local road inventory contains 141.2 km of code 99, labelled by the city as “Unclassified (O'Hare).” Of that length, about 30.6 km is near raw Overture `service` and 83.0 km has no raw Overture road within 15 m. The map places much of code 99 in the airfield. In rural Marsilac, 40.2 km of municipal `LOCAL` lines and 20.2 km of unresolved municipal lines are near excluded Overture `track`; 45.4 km and 21.2 km, respectively, are more than 15 m from any raw Overture road. These differences mix policy and source completeness. Do not repair them with a citywide ratio or by including airport/timber tracks as ordinary streets without a physical definition.

The [Overture RoadClass schema](https://docs.overturemaps.org/schema/reference/transportation/types/segment/road_class/) defines `unclassified` as known paved lower-order roads, whereas `unknown` is undetermined. Keep these distinct in M6; citywide weighted `unknown` is 1.46% (Chicago) and 2.00% (SP), while district maxima reach 5.3% and 7.0%. No unknown-to-Local imputation is carried from SP v2. The ten-class common M1 universe, links/carriageways, boundary ownership and access-agnostic interpretation are now [locked for review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/method_decisions.json); source coverage remains open and neither family is strict accepted for fitting.

A consistency defect was also found: the earlier prepared road layer used by M2/M3/M4 pilots omits Overture `pedestrian`, while the H1–H3 M1/M6 run includes it. `review_pedestrian_street_boundaries_v1.py` restored that class in the eight no-link block pilots; at most seven extra enclosures appear (CHI:28), with small reference-match changes. All prior morphology outputs remain diagnostic, but any new block method must use the declared ten-class street universe or explicitly justify a different boundary network. Sealed H1–H3/H4 artifacts were not changed. No model fit/ranking occurred.

## Paired rail and water boundary continuation

After local-reference validation rejected the grade-filtered road networks, `analysis/scripts/review_block_barrier_pilots_v3.py` tested at-grade Overture `standard_gauge` rail portions and local water-mask shorelines as separate additions to the no-link street baseline in all eight pilots. `review_block_water_land_filter_v3.py` removed majority-water polygons only in saved shoreline sensitivities; `review_rail_corridor_pilots_v3.py` tested 10/20/30 m dissolved rail corridors in Loop, CHI:28, Brás and SP:30. [The barrier review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md) retains 32 main, 16 land-only and 12 corridor scenarios with whole polygons and bidirectional local-reference comparisons. `validate_block_barrier_pilots_v3.py` confirmed row coverage, no-link identity with the previous pilot, finite land candidates and count conservation; compilation passed.

Individual rail centerlines cannot be treated as block edges: CHI:28 jumps 765→1,404 owned polygons and 5→359 narrow (<6 m) polygons, while candidate-to-reference IoU≥.50 match falls .634→.350. A 20 m corridor lowers added narrow polygons to 24 but still reduces candidate match to .565 and gives no reference-coverage gain. Brás likewise acquires narrow rail polygons. **Reject rail centerlines and arbitrary buffered corridors as shared M3/M4 boundaries.** Rail rights-of-way require a defensible outer-edge source rather than track centerline guesses.

Shorelines create water enclosures: SP:30 gains 265 polygons, 262 of which have majority-water area. Removing those leaves 1,531 land candidates versus 1,528 baseline and essentially unchanged reference agreement. Loop's land-only shoreline candidate improves reference-block IoU≥.50 match .397→.452 while candidate match .372→.394; other pilots show small or no benefit. Keep this as a bounded sensitivity, not an accepted block definition, because local masks, shoreline geometry and remaining road slivers differ. M3/M4 and the 13-family fit remain open.

## Eight-unit local-reference validation of M3/M4 pilot modes

`analysis/scripts/review_block_reference_fixtures_v2.py` rebuilt four boundary modes for all eight paired pilots and asserted each whole-owned polygon count against the previous sensitivity table. It matched candidate polygons to whole 2020 Chicago Census blocks or eligible São Paulo municipal Quadra by best bidirectional IoU, with IoU ≥ 0.50 as a diagnostic threshold. These local references have different semantics/vintages and are not common model inputs. Two synthetic IoU fixtures pass. The [reference review](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures/README.md) contains all 32 comparisons, saved polygons, maps and six structured case annotations.

Every filtered mode improves the candidate-to-reference match share over all streets in all eight units. Neither grade-filtered mode improves the reference-to-candidate match share in any unit. In Loop, all streets match 28.7% of candidate polygons and 37.9% of Census blocks at IoU ≥ 0.50; interval-aware filtering changes these to 57.1% and 30.6%. At the stacked-road fixture, it produces no owned enclosure within 140 m while 13 owned Census blocks intersect that circle. Brás changes 60.5%/96.1% to 77.8%/89.5% against municipal Quadra. This is a survival/coverage tradeoff, not an accuracy gain. **Reject the whole-grade and interval-aware filters as complete M3/M4 block networks.** All-streets and no-links remain diagnostics; neither is accepted. The O'Hare case has low reference agreement under every mode and still needs edge/barrier review.

The fixture annotations identify a source-confirmed false distance merger in Loop; a source-linked but physically undecided Brás connector pair; a 3.01 m² Loop sliver with negligible Census overlap; a 51.79 m² Brás wedge with no eligible Quadra overlap; and a local-reference-aligned Brás candidate. Reference disagreement is not automatically a physical error. The next method iteration must preserve block coverage while resolving carriageway slivers, rail/water boundaries and true ground-road edges, then be checked against matched imagery/local references. No M2/M3/M4 values were promoted into the 13-family fit.

## Paired M2/M3/M4 method continuation: source topology and boundary intervals

The user directed continuation after the Microsoft review. The new work uses the same five Chicago and three São Paulo pilots and keeps all original 13 families in scope. The sealed H1–H3 outputs and rejected H4 proposal were not modified. Reproduce the source-topology and road-context diagnostics with `analysis/scripts/review_junction_complexes_v2.py`, `review_junction_link_context_v2.py` and `review_junction_fixture_sources.py`. Four new junction fixtures test short linked pairs, nonlinks, false planar proximity and oversized chains. Reproduce four block-boundary modes with `analysis/scripts/review_block_boundary_pilots_v2.py`; three road-interval fixtures test scoped/unscoped flags and invalid ranges. `python -m unittest analysis/tests/test_road_intervals.py analysis/tests/test_junctions_v2.py` passed **7/7** with the repository virtual environment.

[M2 evidence](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md) shows why a distance threshold is invalid: two Loop connector candidates only 2.49 m apart belong to stacked roads with Overture level `+1` versus `-1`/`-2`, whereas a Brás pair 8.28 m apart is directly linked on the same street without a grade flag. Of 71 Loop pairs within 10 m, only 34 have a short source-road link; all 13 Brás close pairs are source-linked. Yet 40 of Loop's 114 short links lie on roads with possible ramp/grade context. Source links therefore remain diagnostic; physical-arm labeling and scoped grade review are required before M2 counts can be accepted.

[M3/M4 evidence](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/README.md) compares all streets, removal of link roads, whole-segment bridge/tunnel removal and interval-aware exclusion of explicit link/nonzero-level/bridge/tunnel/covered portions. The last mode respects Overture `between` rules, which can apply to only part of a segment. For whole enclosures owned by Loop, all streets yield **453 enclosures, 125 under 6 m, median 921 m²**; the interval-aware mode yields **184, 0, median 9,591 m²**. Brás changes **243/2/9,661 m²** to **176/0/12,965 m²**. This strong sensitivity can merge legitimate blocks as well as remove carriageway slivers. Neither rule includes rail/water barriers or verifies a physical block against a matched reference. Level zero is visual Z-order, not proof of ground-level identity. Municipal São Paulo Quadra is only a city-specific diagnostic. M3 identity and M4 shape population remain unaccepted.

The next decision gate is an annotated paired sample of true junction arms and block polygons, including divided roads, ramps, stacked roads, narrow real blocks, traffic islands, rail/water edges and campuses. Once the physical definitions and their sensitivity are defensible, rebuild M2/M3/M4 for 96 SP and 77 Chicago units in a new version. No shared fit or cross-city ranking has been run.

## H1/H2 source continuation: supplied Microsoft tiles

The six compressed user files exactly matched the previously selected Chicago/SP tile keys, allowing for root filenames that omitted Chicago's leading quadkey zero. `verify_microsoft_building_downloads.py` read all six gzip streams, checked their GeoJSONL schema and record counts, and proved each decompressed plain file identical to its compressed original. `organize_microsoft_building_downloads.py` then moved originals to `analysis/data/{Chicago,SP}/microsoft_buildings_2026_08_13/raw_tiles/`, verified hashes after moving, deleted the six redundant plain files and removed the two empty root directories. The unrelated `test/predios_sp_raw/` sample remains untouched. [Local and organized inventories](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md) bind URLs, tile keys, hashes, counts and deletions; the source files are ignored by Git.

`pilot_microsoft_buildings.py` streamed all six tiles, preserving height `-1` and confidence `-1` as separate missingness concepts, and applied the same gross/land supports and `union_coverage` formula as the matched Overture B1 candidate to the five Chicago and three SP fixtures. Four invalid pilot polygons were repaired only in projected working geometry; maximum absolute area adjustment was about 0.0000014 m², logged with validity reasons. `validate_microsoft_building_pilot.py` passed **52/52** arithmetic/support checks. The [pilot table](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/pilot/paired_microsoft_pilot.csv) reports per-unit coverage and height support.

All **2,035,929** records in the three SP tiles report Microsoft height `-1`; the release therefore supplies no paired building-height BV candidate. Microsoft–Overture B1 land-coverage differences are between −2.28 and −0.87 percentage points in the five Chicago fixtures, but −36.12 in Brás, −0.04 in Grajaú and +8.64 in Itaim Bibi. The direction and size of SP differences are uneven. Keep matched Overture as the B1 candidate and treat Microsoft as a diagnostic source pending local map/reference checks. The pilot does not determine which source is accurate. It does not close M7 cadastral, B2 floor or B3 constructed-area gates. No family was promoted into the fitted model, and no old release was modified.

## Initial full-scope review: Microsoft source and paired physical pilot (historical)

The Microsoft [repository](https://github.com/microsoft/GlobalMLBuildingFootprints) documents footprint polygons and some estimated heights in metres, with `-1` for unavailable heights, under CDLA Permissive 2.0. Its 2026-08-13 date is a release date; imagery dates vary. Footprint confidence does not establish height accuracy. The user's 30,340-row index was audited in [this source review](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md). A 1.5 km buffered tile selection covers Chicago and SP with three indexed files per city (about 230 MB and 233 MB of advertised compressed size respectively). The index covers both city geometries, but feature-level coverage is unverified because the tile files were not fetched. Reproduce selection and provenance counts with `analysis/scripts/audit_microsoft_building_links.py` using the downloaded CSV.

The existing Chicago Overture building file cites Microsoft ML Buildings on 373,434 of 1,381,239 rows. It has positive height on 1,258,170 rows and positive `num_floors` on 429,594 rows. The frozen SP Overture GeoPackage likewise cites Microsoft on 869,479 of 7,278,768 rows; 2,090,405 have positive height and 21,250 positive floor counts. These are presence and lineage counts, not accuracy or complete-stock coverage. Microsoft cannot serve as independent ground truth for Overture completeness. It is a worthwhile paired B1 alternate-source and BV building-height sensitivity after a bounded tile pilot, but cannot supply M7 cadastral entities, B2 reported floors or B3 constructed area. The source CSV index is linked from the v2 contract; no old candidate table or frozen model was altered. The Firecrawl CLI and `curl` could not resolve their hosts, and the in-app browser blocked a tile URL; web documentation was checked separately. Direct tile acquisition remains pending.

To continue the original M2/M3/M4 family gates, `analysis/scripts/review_paired_junction_block_pilots.py` summarized the sealed connector/enclosure candidates in the same eight pilot areas. [Pilot flags](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/README.md) show Loop with 71 connector pairs within 10 m and 125 narrow enclosures, compared with Brás at 13 and 2. Those are inspection flags, not physical junction/block corrections. The next stage is to annotate matched junction and barrier cases, implement a common consolidation/block-boundary method, then independently review its paired outputs. No M2/M3/M4 candidate was promoted into the model.


Started 22 September 2026. This is the cumulative documentation for the [approved harmonization plan](CHICAGO_HARMONIZATION_PLAN.md). It will record every H0–H6 step, its inputs, definitions, implementation, checks, artifacts and limitations. **The model build is in progress; this is not a completed-model report.**

## Authorization and release boundaries

The user approved proceeding on September 22 and requested documentation covering all steps. Construction and targeted scientific checks are now authorized. Preserve SP model v2 and the existing Chicago local/functional releases. All new outputs use separate paths. No new downloads, agency requests, paid access or model fits have occurred in this checkpoint.

The approved common comparison excludes M7 physical cadastral entity density, B2 reported floors and B3 fiscal constructed-area density. A new GHSL BV family describes estimated vertical form; it does not recreate those excluded attributes. Core/functional family acceptance remains conditional on paired measurement gates. Fit the eventual new state on harmonized SP and apply it unchanged to Chicago.

## Checkpoint ledger

| Step | Status | Evidence / work remaining |
|---|---|---|
| H0 — Measurement contract | Candidate definitions documented | Road universe, access interpretation, land support and functional policies are explicit; final family acceptance remains H4 |
| H1 — Paired pilots | Numerical pilots complete; semantic gates recorded | Eight maps, graph/block/raster fixtures and paired footprint/function checks. M2/M3/M4 remain withheld pending physical interpretation |
| H2 — Full paired physical attributes | Candidate construction complete | Roads, footprint coverage and GHSL for 173 units; diagnostic graph/block measures separated. No accepted model matrix |
| H3 — Paired functional attributes | Candidate construction complete | 173 population rows, 1,038 bus-only scenarios, completed employment sensitivity; U1 withheld and U2 extended-only |
| H4 — Common matrix acceptance | Technical readiness complete; scope approval pending | Proposed six-family/15-column matrix covers173 units;13 checks pass. Reduced scope must be reviewed before fitting |
| H5 — Fit updated SP and Chicago comparison | Not started | No new rankings or fitted state |
| H6 — Robustness and final release | Not started | Final synthesis will extend this document with all outputs and limitations |

## H0: GHSL definitions and decisions

Read the locally acquired *GHSL Data Package 2023*, sections 2.2.1, 2.2.4 and 2.3 (printed pages 26, 31 and 33). The source PDF hash and interpretation record are saved in [definition evidence](../../analysis/results/SP_CHI/harmonization_2026_09_22_h0_h1/ghsl_definition_evidence.json).

ANBH is net height: built volume divided by built surface. AGBH is gross height: volume divided by the full cell surface. Consequently, AGBH reflects both height and coverage. The multitemporal volume series multiplies 2018 height by time-specific built surface; the 2020 volume is not independent evidence of height change since 2018. These related products receive one BV family budget, not separate full weights.

The primary candidate remains an **area-weighted mean of the ANBH grid** over valid district-land support, including observed zeros. It is not the mean height of individual buildings, nor a built-surface-weighted city height. No companion surface raster is needed for this explicitly spatial statistic. Report its valid and zero areas so its support is visible. AGBH is a diagnostic alternative; volume-only and combined BV variants are sensitivities. These choices precede rankings.

Volume allocation multiplies each source-cell volume by district-land overlap divided by full cell area. Density divides the allocated mass by district land area. This assumes uniform volume within a cell; actual building locations within the cell are unknown. Gross support is retained as a sensitivity. No raster resampling, height-to-floor conversion or volume-to-GFA conversion occurs.

**Metadata discrepancy:** Table 15 lists 255 as the AGBH NoData value, whereas both acquired AGBH city rasters declare −1. ANBH declares 255; volume declares 4294967295. Read each raster's own mask. Do not classify every value 255 as missing: the volume rasters contain valid 255 m³ cells. Original values and files remain unchanged.

The contract is [sp_chicago_harmonization_v1.json](../../analysis/config/sp_chicago_harmonization_v1.json), with a checkpoint snapshot. Its status explicitly prohibits fitting until H4 gates pass. No family is marked accepted yet.

## H1: native-grid pilot implementation

Implementation: [rasters.py](../../analysis/scripts/harmonization/rasters.py), with runner [pilot_harmonized_ghsl.py](../../analysis/scripts/pilot_harmonized_ghsl.py).

For each source raster, create native 100 m Mollweide cell polygons, transform the reporting support to that equal-area CRS, and calculate exact positive-area cell intersections. Reuse the current SP water-subtracted district support and Chicago hydrographic land support provisionally; this does not yet establish source equivalence of the water masks. Intersect land with its district to avoid allocating outside reporting support.

The pilot uses Loop, Near West Side, West Town, South Lawndale and O'Hare in Chicago and Brás, Itaim Bibi and Grajaú in SP. SP names are resolved from the source district table, rather than guessed IDs. Compute three products on gross and land support for each pilot: 48 candidate rows. All rows are explicitly unaccepted for modeling.

Every row records support area, covered area, valid area, NoData area, outside-raster area, observed-zero area, partial-cell area, epoch and candidate value. For volume, retain observed allocated mass but withhold density if support is missing beyond numerical tolerance; do not extrapolate observed mass into unknown area. Height means use valid area and expose missing support, with full-model acceptance still pending coverage review.

### Checks and reproduction

Eight focused unit tests cover partial-cell mass conservation, observed zero, NoData exclusion, valid-area height weighting, zero support, invalid/duplicated areas, nonfinite values and missing raster extent. They pass. The pilot additionally checks complete raster extent over each support and gross = land + water volume partition for each area. This is arithmetic/coverage verification, not independent accuracy validation of satellite height.

```bash
.venv/bin/python -m unittest discover -s analysis/tests -p test_harmonization_rasters.py -v
.venv/bin/python analysis/scripts/pilot_harmonized_ghsl.py
```

Results and exact run status: [checkpoint directory](../../analysis/results/SP_CHI/harmonization_2026_09_22_h0_h1/README.md). Source receipts bind the input rasters and reporting supports. Existing release tests were not rerun without a new reason.

## Remaining work and final documentation requirements

Next is H4: review the candidate dictionary, source qualifications and unresolved M2/M3/M4 gates. A reduced common set of M1/M6/B1/U3/U4 plus the BV extension is a proposal for review, not an accepted or fitted model. Alternatively improve the physical junction/block methods before accepting those families. U1 remains withheld and U2 extended-only. No single-city shortcut may enter a common feature.

For every subsequent checkpoint append: exact source/config/code references, formulas and decisions, outputs and coverage, test commands/results, acceptance or exclusion rationale, unresolved limitations and next step. At H6 include the accepted dictionary/family weights, saved SP fit and Chicago application, SP-to-Brás and Chicago-to-Brás results, contribution reconstruction, sensitivity/stability findings and reproducibility instructions. Mark this document complete only after all required steps are actually complete.


## H1–H3 continuation: paired construction and discovered defects

The user requested H1, H2 and H3 on September 22. These stages produce candidate companions; H4 acceptance and H5 fitting remain separate. Open semantic gates must not be obscured by complete tables.

### Shared roads and physical-block gates

Use the matched Overture release in both cities with motorway, trunk, primary, secondary, tertiary, residential, living-street, designated pedestrian, unclassified and unknown classes. Exclude service/alleys/driveways, sidewalks, paths, steps and cycleways from this candidate street universe. Preserve explicit carriageways and link ramps. Interpret this as **mapped physical streets regardless of legal access**, not a public-access or pedestrian-routing network. Retain unknown as its own composition coordinate and publish the share of length with access rules; missing access rules do not establish public access.

Connector-arm counting deduplicates segment-side incidence and uses source connector IDs, never planar crossings. Synthetic bridge, interior T-junction, loop and duplicate-ID fixtures pass. Nonetheless, raw source connectors have not established consolidated physical junctions across divided roads: M2 remains diagnostic. Polygonized buffered roads yield whole enclosures assigned by largest district overlap; no district clipping creates fake boundary blocks. Enclosures touching the extraction boundary are withheld. Narrow rectangles and very large enclosures are flagged, not silently deleted to improve results. M3/M4 remain diagnostic until carriageway artifacts and barrier definitions are resolved. The loop pilot map visibly shows adjacent carriageways and repeated junction points; numerical reproducibility does not remove that concern.

### Footprints and land support

Chicago footprint unions are recomputed for all 77 areas using the same exact tiled-union method as SP. Reuse the 96 frozen SP union numerators from the same Overture release and unchanged land supports; independently reconstruct Brás, Grajaú and Itaim Bibi with the shared implementation. All 176 bounds/reconstruction checks pass. Source receipts identify both the raw footprint sources and reused SP intermediates.

Land is gross reporting area minus supplied hydrography in both cities, but source vintage/completeness still differ. Publish gross and land variants. In the current support, water fractions reach 20.3% in Chicago and 7.5% in SP; denominator sensitivity is therefore material. No universal completeness percentage is invented. Very small negative water residuals at floating precision are reported as numerical residuals rather than physical negative water.

### GHSL expansion and geometry handling

The full 173-unit run extends the pilot's formulas without interpolation. Reprojection exposed an invalid land geometry outside the original pilot sample. Repair only the new projected working geometry with `make_valid`, retain before/after area and validity reason, and leave original sources unchanged. Full-run `geometry_repairs.json` records the affected units/layers. Use exact source-cell overlap on the repaired support.

An initial full run spent excessive time intersecting interior cells and lines. It was stopped and restarted with an exact containment shortcut: whole interior cells retain 10,000 m² and whole interior lines retain their geometry; only boundary crossings require overlay. A separate hole/boundary fixture verifies the shortcut against known areas/lengths. This is a computational optimization, not a new spatial allocation rule.

### U3 and U4: paired functional companions

Reconstruct population from the existing whole-source Census allocations, retaining outside residuals: Chicago Census 2020 versus SP Census 2022. Both use gross reporting-area density. Keep the two-year mismatch explicit rather than inventing an ACS update.

**New defect found in the legacy SP U4 calculation:** the feed contains 1,346 bus routes, nine metro routes and seven rail routes. The original processing did not filter route type; 32 nonbus trips contributed 1,212 service rows. Calling that historic result bus-only was incorrect. The new SP companion filters `route_type=3` before recalculating every district and all six scenarios from saved population support points. Existing SP v2 data and fitted outputs remain unchanged for lineage, but their U4 scope limitation is now explicit.

The filtered service removes 16,881.288 expected weekday stop calls and 12,221.705 on each weekend window at feed level. These are stop-call totals, not passengers or route supply. The primary 400 m weekday value for Brás decreases about 16.6%; the largest reduction across all district/scenario combinations is about 35.8%. The new bus-only values use the same route/direction stop maximum as Chicago. Retain SP frequency-based expected departures versus CTA schedules, one-week scenario-date difference and missing SP holiday exceptions as limitations. No rail is included in either new companion.

All 576 SP bus-only scenarios were recomputed; the paired output contains 1,038 scenarios. The functional reconstruction passes 2,171 checks, including complete cohort/scenario keys, population conservation, radius monotonicity, ratio replay and full primary-catchment pilot reconstruction using a separate calculation path.

### U2 sensitivity and U1 exclusion

The previously paused employment run failed on an approximately 0.0001 m² overlay discrepancy at block `170310707001004`. Preserve that old run. A new v2 run permits only residuals within `0.001 m² + 1e-7 × support area`, records the residual and normalizes partition mass within that bound to conserve jobs exactly. Material errors still fail. The mathematical rationale is bounded overlay roundoff, not arbitrary rescaling of missing workplace support.

Both business-support scenarios now cover all 14,990 positive-job blocks, preserving whole-block outside mass. Business-core support falls back to gross area in 5,817 blocks; adding transport/communications/utilities reduces this to 5,125. There are 14 blocks with under 99% CMAP coverage and some positive supports below 1 m², so this remains a sensitivity rather than a new exact employment allocation. The independent audit passes 138 checks, including alternative geometry reconstruction on 16 stratified blocks, mass conservation and residual bounds.

U2 stays extended-only because RAIS and LODES coverage/unlocated mass differ; the allocation sensitivity does not establish population-universe equivalence. U1 stays explicitly missing in the common table because CMAP polygon-area use and SP cadastral-use entities do not yet share a defensible observed-use domain/ontology. No fabricated crosswalk or zero-fill is used.

### Native cell recovery at the reporting boundary

The first full GHSL output withheld North Park's volume variants because about 0.009 m² intersected a masked cell in the city extract. That extract used the acquisition boundary, whereas reporting calculations use prepared/reprojected supports. The revised reader resolves positive-area masked intersections directly against the original source ZIPs, verifies exact CRS/resolution/cell-centre alignment, and uses the source value only when its source mask is valid. This is recovery of observed source data, not imputation or tolerance relaxation. `source_cell_recovery.json` records every recovered cell and its archive. Actual source NoData would still remain missing.

Projected-geometry repair affects 14 working geometries across the two cities. Most area changes are numerical; the largest is about 236.65 m² in SP land support. Full source and before/after areas are retained, and unchanged original geometries remain available. This is a limitation of the transformed support, not a claim that the revised boundary is surveyed ground truth.

## H1–H3 artifacts and reproduction

The common checkpoint is `analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/`. Subdirectories `roads/`, `footprints/`, `ghsl/` and `functional/` contain stage outputs, evidence and source receipts. `tables/` contains the paired long/wide candidate tables and dictionary; `family_acceptance_ledger.json` distinguishes candidates from withheld/excluded families. Separate SP and Chicago companion tables are published under each city's `harmonized_candidates_2026_09_22/` directory. These are new attribute releases, not fitted models.

Use the project environment from the repository root. Scripts with independent inputs may be run separately, but avoid launching every large geometry job simultaneously on this 16 GB machine. Cached working data is ignored by Git and requires separate transfer when reproducing on another machine.

```bash
.venv/bin/python analysis/scripts/prepare_harmonized_roads.py
.venv/bin/python analysis/scripts/prepare_harmonized_footprints.py
.venv/bin/python analysis/scripts/prepare_harmonized_ghsl.py
.venv/bin/python analysis/scripts/prepare_chicago_employment_sensitivity_v2.py
.venv/bin/python analysis/scripts/validate_chicago_employment_sensitivity_v2.py
.venv/bin/python analysis/scripts/rebuild_sp_bus_companion.py
.venv/bin/python analysis/scripts/prepare_harmonized_functional.py
.venv/bin/python analysis/scripts/assemble_harmonized_candidates.py
.venv/bin/python analysis/scripts/validate_harmonized_candidates.py
```

The source-cell reader uses a local native-TIFF cache to avoid repeated ZIP decompression. It only attempts recovery when masked overlap exceeds the existing coverage tolerance; smaller masked areas remain explicit diagnostic residuals, without upweighting. The final independent audit reads the recovered values directly from original ZIP windows through a different I/O path.

Publisher provenance: European Commission JRC/GHSL (R2023A, CC BY 4.0; city extraction, boundary allocation and aggregation are our modifications); Overture Maps Foundation and source contributors (2026-08-19 release; original attribution/licensing remains in acquisition manifests); municipal hydrography; IBGE Census 2022; US Census 2020 and LODES 2022; SP/CTA GTFS; CMAP 2023; and RAIS 2022. Different source years and observation regimes remain explicit limitations.

### What this checkpoint does not establish

Passing numerical tests does not prove equal mapping completeness, exact building height, surveyed subcell volume, equivalent employment universes, or equivalent spatial scale of Community Areas and SP districts. No new distances, rankings, PCA, fitted transformations or family calibrations were computed. H4 must resolve the remaining family gates and common-set scope before H5 begins. The final H6 documentation and model release are still pending.


The full-raster recovery also exposed a performance issue in Marsilac (SP:52): `make_valid` returned a polygon collection plus a zero-area line. Retaining that line prevented an efficient prepared-polygon query. The final area-support path keeps polygonal components only, with a regression test showing unchanged area. For the actual Marsilac geometry, union normalization changes area by only 1.16e-6 m² (5.6e-15 relative). Native TIFF caches address repeated ZIP reads separately. Initial interrupted/slow attempts do not represent completed releases; the final receipt and checks identify the completed output.


## H1–H3 final checkpoint totals

Published 6,209 long-form rows and 37 candidate/diagnostic feature columns across 173 units. All 1,038 GHSL product/support values are present after recovering one North Park cell in each of the three source products. The independent audit verified those three values against original ZIP windows. Tiny remaining coverage residuals are at floating precision; minimum valid coverage is 0.999999999999954.

Final checks: 1,211 GHSL coverage/partition checks, 176 footprint checks, 2,171 paired functional checks, 576 SP bus-only monotonic-removal checks, 138 independent employment checks, 31 independent candidate-table/source-cell checks, and 28 targeted unit tests passed. No failures remain in the final numerical reports. Unresolved scientific gates for M2/M3/M4 and U1 remain explicit; these counts do not turn them into accepted features.

[Checkpoint report](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md), [candidate dictionary](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/tables/candidate_dictionary.csv), [family ledger](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/family_acceptance_ledger.json), and [publication manifest](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/publication_manifest.json) provide the compact audit trail. The manifest binds code/config/tests, environment, stage-source receipts, output hashes and the per-city companions. No construction job remains running. H4 review is next; H5/H6 and the final fitted-model documentation remain pending.


## H4 bounded readiness review — quota-aware stop

With 14% quota remaining reported by the user, the next checkpoint was limited to reviewing existing candidate tables. [H4 review report](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md) presents a concrete six-family proposal: M1, M6, B1, BV, U3 and U4, with equal family weights and 15 raw columns. All 173 rows have complete selected inputs; all 13 readiness checks pass. Source/code/output hashes bind this separate review without modifying the sealed H1–H3 release.

Height and volume have Spearman correlations of0.953 in SP and0.933 in Chicago, reinforcing one BV weight. Some Chicago hierarchy components exceed SP marginal ranges; all five scalar inputs lie within observed SP ranges. These are descriptive readiness diagnostics, not transformed domain-shift results or ranks.

The proposal omits physical junction/block families as well as previously unavailable or incompatible families. Its narrower scientific scope needs approval before H5; `fit_authorized=false`. No fitting or large processing was started. H4 scientific acceptance, H5 and H6 remain pending; no jobs are running. The exact next step is scope acceptance or reopening junction/block work, followed by a bounded H5 implementation.


## U1 bounded three-option screen — 22 September 2026

Following the user instruction to test only sampled neighborhoods, `analysis/scripts/pilot_u1_source_samples.py` drew 20 uniform land points and 20 uniform source polygons in each of six selected units (Brás, Alto de Pinheiros, São Domingos, Loop, Albany Park and Humboldt Park). It read only the three SP parcel partitions and three Chicago CMAP LUI bounding boxes, plus small land/park layers. Raw codes and locations are retained in the [sample report](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/README.md). The sample exposed SP cadastral gaps and Chicago `6000` nonparcel support; source labels have no independent truth adjudication yet.

`analysis/scripts/pilot_u1_poi_samples.py` queried Overture Places release 2026-08-19.0 through geographic Parquet row-group reads in the same six units. It used two remote partitions, one combined bounding box per city, one thread and a 512 MB memory cap; exact district point membership retained 10,479 SP and 19,503 Chicago POIs. Only aggregates and 20 fixed-seed records per unit were saved. A three-bbox OR query was tried as a possible reduction in returned rows but took longer before the first city completed, so it was interrupted; the successful combined-bbox query was retained. A fixed 12-category destination entropy and confidence sensitivity distinguish destination diversity from land-area U1. Brás shopping and Loop services/business profiles are visible, but the Loop has 23% records outside those destination categories and the two cities' confidence distributions differ. Sampled Loop records include implausible-looking unclassified names requiring independent checking.

The discussion now compares developed-use area mix, all-land area mix and destination diversity explicitly. The developed-use route is the closest original-U1 repair; all-land lacks a paired comprehensive open-land source; POIs are a separately named activity/destination pivot. The next bounded checkpoint is independent label inspection and six-unit district-clipped land coverage. None of the options is accepted, no full-city U1 rebuild occurred, and H4 fit authorization remains false.


## U1 exact-area and POI provider follow-up — 22 September 2026

The user asked to further test developed-use mix and track whether POI diversity could become a new variable, while diagnosing whether missing data can be found elsewhere. [The bounded follow-up report](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md) records exact six-unit district-land accounting, SP raw-lot versus accepted-use gaps, explicit fiscal dominance, Chicago mixed-use codes, and a Brás/Loop Overture Places provider audit. Four new scripts under `analysis/scripts/` reproduce only these selected-unit checks: `pilot_u1_clipped_area.py`, `pilot_u1_mixed_labels.py`, `pilot_u1_dominant_use.py` and `pilot_u1_poi_quality.py`. The previous six-unit source sample and 12-unit summary screen remain separate historical diagnostics.

SP no-accepted-use area is 25.1%, 30.0% and 23.7% of Brás, Alto de Pinheiros and São Domingos land, respectively, after adding immediately adjacent source-district parcel files. Most is **outside raw lot polygons** (24.0%, 25.4%, 20.4%); raw lots without accepted use account for 1.2%, 4.6%, 3.3%. Chicago `6000`/unclassifiable area is 32.6%, 31.5%, 27.0% in Loop, Albany Park and Humboldt Park. Six-class versus four occupied-use conditional entropy reverses Brás/Loop order, showing ontology scope matters. Explicit SP source labels recover 7.3, 0.9 and 3.8 percentage points of land from mixed/other under a conservative dominance sensitivity, but remaining mixed area is unresolved and no recode is accepted. Category-area conservation and dominant-use reconciliation checks pass. No independent source truth labels were produced.

Overture Places provider composition differs sharply: Meta contributes 96.6% of Brás POIs versus 54.1% in Loop. Loop has 3,773 records without taxonomy hierarchy; 2,908 have confidence below 0.5. Overture's own guide says confidence is not calibrated across providers and does not solve duplicate/property-completeness issues. The new `destination_diversity_12` proposal remains an unweighted research candidate pending independent POI verification, balanced-source sensitivity and added-information testing. No citywide U1 processing, fit, ranking or PCA followed.

**Edge-source correction:** the first exact-area pass read only each SP district's source-named parcel file. `prepare_sp_inputs.py` partitions lots by GeoSampa source file while accepted fiscal profiles use assigned district, so neighboring files can contribute to a district's land. The final pass reads the three selected files plus 50 m adjacent district files (18 files total); raw-lot area rises 0.47 percentage points in Brás and 0.98 in São Domingos. The 20-point gap classification is unchanged. The report and status use the corrected values; no full-city source scan was made.

**No-lot context:** a further bounded intersection with local `quadra_viaria_editada` polygons puts 8.5%, 7.2%, 7.8% of Brás/Alto de Pinheiros/São Domingos land outside lots but inside ordinary `Quadra`; 14.9%, 15.0%, 11.7% lies outside every mapped block type. These are cartographic contexts, not independent use labels; they show the no-lot residual cannot all be called road ROW. Among 15 sampled no-lot points, 10 are outside mapped block polygons, four in ordinary `Quadra`, and one in `Praca_Canteiro`/mapped park. The [source report](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md) and `sp_no_lot_point_context.csv` give the exact scope.
