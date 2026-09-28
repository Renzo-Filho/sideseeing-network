# U1 developed-use and POI source diagnosis — bounded six-unit follow-up

**22 September 2026. Diagnostic only; no U1 or new POI variable is accepted.** This follows the [six-unit source/POI sample](../u1_source_samples_2026_09_22/README.md). It tests whether a developed-use mix can be made honest on exact land support, and whether destination diversity merits a separate variable. No citywide U1 rebuild, model fit or ranking was run.

## Computational and source scope

The units remain Brás (SP:10), Alto de Pinheiros (SP:02), São Domingos (SP:95), Loop (CHI:32), Albany Park (CHI:14) and Humboldt Park (CHI:23). `pilot_u1_clipped_area.py` reads the three selected SP parcel partitions plus their 50 m adjacent source-district partitions (18 files in total), three Chicago CMAP 2023 spatial bounding boxes, the six district land geometries, and bounded SP parks and urban-block reads. It unions polygons by source class, clips to district land, isolates cross-class overlaps, and records the uncovered complement. The same district-land denominator is used for the fractions below. It separately unions raw SP lot polygons from those same selected/adjacent partitions to distinguish no lot from a lot with no accepted fiscal use. Adjacent files matter because GeoSampa source partitions and accepted fiscal district assignment differ; they add 0.47% of Brás land and 0.98% of São Domingos land in raw-lot area. This bounded neighbor read cannot certify that no farther source file intersects a selected district; its remaining edge effect is unmeasured. None of the 60 original sampled SP point labels changes after adding neighbors. Category areas reconcile to district land within 0.01 m² or 1e-8 relative tolerance.

`pilot_u1_gap_context.py` checks only the 15 sampled no-lot SP points against bounded urban-block and plaza reads. `pilot_u1_mixed_labels.py` reads compact SP fiscal profiles and three bounded CMAP extracts to inspect mixed-use coding. `pilot_u1_dominant_use.py` scans only projected fiscal fields for the three SP districts and reassigns a mixed parcel **only if every raw fiscal label for it explicitly states the same predominant residential or commercial use**. This is a sensitivity, not an accepted mapping. `pilot_u1_poi_quality.py` reads Overture Places 2026-08-19.0 for **Brás and Loop only**, spatially filters to exact district points, and summarizes provider/category/confidence relationships. It does not store the full POI extracts. [Validation receipts](validation.json) and code preserve the scope.

## Exact land-area result

Percent of each district's prepared **land area**; categories are mutually exclusive after isolating tiny overlaps. `Six` is residential, commerce/services, industrial, institutional, transport/utilities and vacant. `Four` is the occupied-use subset: residential, commerce/services, industrial and institutional. Entropy is conditional on those named classified classes; percentages describe how much land enters each entropy.

| Unit | Six-class support | Four-class support | Mixed/other | Source-unclassified | Open space | No accepted source polygon | Six / four entropy |
|---|---:|---:|---:|---:|---:|---:|---:|
| Brás | 57.9% | 54.6% | 14.5% | 2.5% | — | 25.1% | 0.706 / 0.774 |
| Alto de Pinheiros | 55.6% | 50.4% | 11.5% | 2.9% | — | 30.0% | 0.433 / 0.353 |
| São Domingos | 63.1% | 50.1% | 5.8% | 7.4% | — | 23.7% | 0.724 / 0.692 |
| Loop | 42.3% | 34.3% | embedded in commercial | 32.6% | 24.7% | 0.5% | 0.735 / 0.662 |
| Albany Park | 66.2% | 64.1% | embedded in commercial | 31.5% | 2.3% | <0.1% | 0.485 / 0.531 |
| Humboldt Park | 72.3% | 58.9% | embedded in commercial | 27.0% | 0.7% | <0.1% | 0.874 / 0.857 |

Chicago source-unclassified area is overwhelmingly raw `6000`, labelled nonparcel/unclassifiable in CMAP's [published LUI legend](https://services5.arcgis.com/LcMXE3TFhi1BSaCY/ArcGIS/rest/services/LUI20_geodatabase_v1_CMAP/FeatureServer/0); small Loop `9999` and clipped water remnants also appear. We have not certified that every 2023 `6000` polygon is a street. Chicago's source covers almost all land geometrically but does **not classify** 27–33% into a functional parcel use. São Paulo's fiscal source leaves 25–30% without an accepted use polygon. These are different missingness mechanisms, despite similarly sized residuals. The Loop's open-space area is observed use, not a missing label.

The ontology choice materially changes the anchor comparison: Brás versus Loop entropy is **0.706 versus 0.735** for six classes, but **0.774 versus 0.662** for four occupied uses. We must define the intended characteristic before choosing classes. Including vacant and transport in something named *developed use* is questionable; retaining them as separate land-mass diagnostics is a defensible alternative. Neither conditional entropy may be treated as a full-district mix while its support is this selective.

### Why SP land lacks a use polygon

| Unit | No raw lot polygon | Raw lot but no accepted use | Selected mapped park outside accepted use |
|---|---:|---:|---:|
| Brás | 24.0% | 1.2% | <0.1% |
| Alto de Pinheiros | 25.4% | 4.6% | 2.2% |
| São Domingos | 20.4% | 3.3% | 0.4% |

Of the **16 previously sampled SP points** without accepted use, **15 lie outside raw lot polygons in the selected/adjacent source partitions**; one lies inside a raw lot without an accepted use. The exact area result and sampled points agree on the dominant mechanism. No raw lot is a *source-universe gap*, not a null tax-use field. Streets, plazas, public land and geometry/vintage differences are plausible constituents, but their exact composition has **not** been independently mapped. A bounded overlay with GeoSampa's mapped urban blocks splits **no-lot land** further (percent of district land):

| Unit | Inside ordinary `Quadra` | Inside `Praca_Canteiro` | Outside all mapped block polygons |
|---|---:|---:|---:|
| Brás | 8.5% | 0.7% | 14.9% |
| Alto de Pinheiros | 7.2% | 3.3% | 15.0% |
| São Domingos | 7.8% | 0.9% | 11.7% |

The first column is a **plausible data-completeness lead**, not proof that a taxable parcel or a particular activity exists. Block polygons are cartographic reference objects, not an observed-use census. In the earlier point sample, 10 of 15 no-lot points lie outside mapped block polygons, four lie inside ordinary `Quadra`, and one lies in `Praca_Canteiro` and a mapped park; none intersects the separate local plaza layer. See [point context](sp_no_lot_point_context.csv). This mixture rules out calling the entire no-lot residual road area.

The raw-lot/no-use fraction is a smaller, potentially recoverable source/join gap that needs case review before searching for another dataset. The mapped parks and block context explain some, not all, source-universe absence; the park layer is not a complete observed open-land map.

### Can mixed-use labels be recovered?

The SP `mixed/other` class is **not synonymous with truly mixed activity**. In these units, many mixed-labelled parcels have just one broad fiscal category. The [source dictionary](../../../work/prepared/SP/sp_prep_2026_09_10_v3/N03/use_mapping.csv) contains explicit “predominância residencial” and “predominância comercial” labels, but also generic “Não residencial” and multiple-use labels. The conservative raw-label sensitivity recovers this fraction of district land into a **dominant** class:

| Unit | Explicit residential | Explicit commercial | Still unresolved mixed |
|---|---:|---:|---:|
| Brás | 2.2% | 5.1% | 7.2% |
| Alto de Pinheiros | 0.3% | 0.5% | 10.6% |
| São Domingos | 2.7% | 1.2% | 1.9% |

These add back to original SP mixed area within 0.1 m²; they do **not** allocate actual floor or parcel-area shares between uses. Chicago [CMAP guidance](https://cmap-repos.github.io/LUI-wiki/CodingMultipleUses.html) retains a primary use and may list secondary uses. In these three Chicago districts, primary `1216` mixed commercial/residential covers 0.8%, 2.9% and 1.6% of land, respectively; `LANDUSE2` exists on other portions. SP dominance and CMAP primary-use rules still need paired case inspection before a shared classification.

## POI candidate: useful signal, unequal source quality

The [Overture Places guide](https://docs.overturemaps.org/guides/places/) says taxonomy coverage and duplicate/junk quality are known issues, and that confidence measures existence only and is **not calibrated across providers**. Our exact district audit finds:

| Anchor | POIs | No taxonomy hierarchy | No-category records with confidence <0.5 | Largest base-provider share |
|---|---:|---:|---:|---:|
| Brás | 5,443 | 254 (4.7%) | 173 | Meta 5,257 (96.6%) |
| Loop | 16,569 | 3,773 (22.8%) | 2,908 | Meta 8,966 (54.1%) |

The other Loop records are heavily supplied by BrightQuery, Microsoft and Foursquare. Of the Loop's 3,773 no-category records, 2,959 are Meta and 625 Microsoft; the latter have a median confidence of 0.85, so a global confidence cutoff would not fix taxonomy absence. Meta-only classified-destination entropy remains different (Brás 0.537, Loop 0.737), but Meta destination-category coverage is also unequal: 95.4% of its Brás records versus 66.6% of its Loop records have one of the fixed 12 destination categories. Provider restriction therefore does not establish comparability. [Provider profile](poi_provider_profile.csv), [quality summary](poi_quality_summary.csv), and the previous [six-unit taxonomy/count screen](../u1_source_samples_2026_09_22/poi_summary.csv) are saved.

**Candidate variable to track:** `destination_diversity_12`, the fixed-12 top-category entropy of verified mapped destinations, with classified-record share, provider mix, count density and confidence sensitivity published as diagnostics. It describes *variety of destinations*, not land-use area, housing, employment or accessibility. The Brás shopping and Loop business/service contrast suggests possible added urban-function information, but this pilot cannot establish cross-city completeness, duplicate rate, independent truth, or added value beyond U1/U2/U3/B1. It remains **unweighted and outside the accepted model**. The six chosen units cannot support a redundancy estimate or threshold calibration.

## Answer to the data-search question

| Gap | Search for more data? | Why |
|---|---|---|
| SP no raw lot in selected/adjacent partitions (20–25% of selected land) | **Targeted contextual data**, not more IPTU rows. | The fiscal-use source has no lot polygon there. The 7–8.5% of district land inside ordinary mapped blocks warrants a targeted parcel/observed-use check. Areas outside blocks and mapped plaza/median polygons warrant separate public-space/ROW context. Neither context alone reveals residential or commercial use. Reassigning residential/commercial use would invent information. |
| SP raw lot without accepted use (1–5%) | **First audit existing joins and raw records.** | Some cases may be recoverable; cause not established by these aggregate checks. |
| SP mixed/unknown (roughly 12–17% of selected land) | **Partly recoverable from existing raw descriptions.** | Explicit dominance recovers 0.9–7.3 percentage points of land across the three units. Generic and truly mixed labels remain unresolved. |
| Chicago `6000` (27–33%) | **Only for a separate public/nonparcel classification.** | It is a structural nonparcel/unclassifiable LUI category, not absent polygon coverage or latent residential/commercial area. |
| Chicago open space (Loop 24.7%) | **No search needed to find it.** | It is measured; the choice is whether an occupied-use feature excludes it and reports it separately. |
| POI missing category and suspect listings | **Targeted provider and independent-reference checks.** | Some labels might be recovered or filtered, but Overture's provider coverage and confidence differ across cities; an extra feed does not automatically create a common establishment census. |

A [GeoSampa official predominant-use map](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/resources/datasets/73e0158b-2ec0-485c-b609-300f604afae7) exists for 2014/2018/2021, but its metadata says it is derived from IPTU and fiscal blocks. It could check our classifications and dominant-use choices; it is older, coarser and **not an independent fix for cadastral noncoverage**. [MapBiomas](https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/cobertura-10m/cobertura/) can help distinguish built/vegetated cover, not residential versus commercial activity. The most valuable next search is therefore a **small observed-use reference for the six sampled units**, especially SP no-lot land inside ordinary blocks, raw-lot/no-use cases and mixed parcels, plus an independently checkable POI reference—not another bulk citywide download.

## Next bounded acceptance work

1. Visually/independently adjudicate a stratified subset of the saved SP no-lot, raw-lot/no-use and mixed cases, and Chicago `6000`/mixed cases. State which are ROW, park/plaza, actual parcel, mapped error or uncertain. Do not infer all no-lot land is streets.
2. Predeclare **occupied-four** versus **six-class parcel-use** as the U1 estimand. On the same six units, recompute category shares after only explicit SP dominance, retain every residual on district land, and compare to independent labels and CMAP primary/secondary examples. Only then consider more units.
3. Keep the POI variable in a candidate register. Check sampled listings for existence, location and category against an independent source; inspect duplicate and provider-specific errors, then test a prespecified provider/threshold sensitivity in a few more contrasting units. Added information beyond accepted land-use and U2 must be shown before any family weight.

Reproduce with `.venv/bin/python analysis/scripts/pilot_u1_clipped_area.py`, `pilot_u1_mixed_labels.py`, `pilot_u1_dominant_use.py`, `pilot_u1_gap_context.py` and `pilot_u1_poi_quality.py` (all paths under `analysis/scripts/`; the last requires network and DuckDB `httpfs`). [Unit coverage](unit_coverage.csv), [category areas](category_areas.csv), [SP point gap causes](sp_point_gap_causes.csv), [dominant-use sensitivity](sp_dominant_use_sensitivity.csv) and [validation](validation.json) provide the bounded evidence. No source-label accuracy rate is claimed without independent reference labels.
