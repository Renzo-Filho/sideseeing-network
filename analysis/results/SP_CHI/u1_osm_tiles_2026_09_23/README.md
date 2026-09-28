# U1 alternatives: six small OSM tiles, Overture comparison, Chicago portal check

**23 September 2026. Diagnostic pilot only.** No U1 replacement, destination-diversity variable, model fit, or family weight is accepted. This report follows the [exact six-unit U1 area audit](../u1_developed_area_2026_09_22/README.md) and the [open discussion](../../../../docs/OPEN_DISCUSSION.md). The six sites were chosen to inspect known source problems, so their results are **not representative estimates** for the districts or cities.

## Question and sample

Can a shared OpenStreetMap (OSM) polygon source repair missing fiscal/CMAP U1 support? Can OSM destinations corroborate the pinned Overture Places signal? Is the Chicago portal's active-license feed a usable POI reference?

We extracted **one 400 m square OSM API map tile per previously sampled unit**, centered on a saved land point from `u1_source_samples_2026_09_22/sampled_land_points.csv`: Brás sample 9 and Alto de Pinheiros sample 2 (both fiscal-no-lot points inside mapped ordinary blocks); São Domingos sample 1 (a fiscal residential point, because no sampled no-lot point there had the same inside-block status); Loop sample 5, Albany Park sample 3 and Humboldt Park sample 10 (all CMAP `6000` points). Tile polygons were clipped to each prepared district's land geometry. The raw XML totals about 8.9 MB, under a 30 MB per-request cap, and is retained locally under `analysis/work/u1_osm_tiles_2026_09_23/`. [Receipts](receipts.json) record live-query URLs, UTC acquisition/check time, tile bounds and SHA-256 hashes. This is a **live OSM API snapshot**, not an immutable OSM planet timestamp. Full-district OSM API requests were rejected for exceeding 50,000 nodes; tiny public Overpass probes returned HTTP 406 or timed out. The small-tile fallback does not prove that OSM or Overpass lack the data.

The XML was parsed with OSMnx 2.1.0, including OSM nodes, ways and relations. `landuse=*` polygons were projected to EPSG:6933, clipped to tile land and unioned before area measurement, so overlapping mapped polygons do not inflate the tagged-area numerator. This is **presence of any landuse polygon**, not an independently verified *correct* use or accepted category. Tags and a provisional crosswalk are in [landuse_tags.csv](landuse_tags.csv) and the script. The tile center was separately checked for a containing `landuse` polygon.

## Result: OSM land-use polygon support

| Diagnostic tile | Land in tile, km² | OSM `landuse=*` polygon area | Label at the saved center | Raw tagged objects | Provisional destination candidates |
|---|---:|---:|---|---:|---:|
| Brás, SP:10 | 0.159 | 2.5% | none | 52 | 45 |
| Alto de Pinheiros, SP:02 | 0.159 | 3.6% | none | 0 | 0 |
| São Domingos, SP:95 | 0.159 | 6.5% | none | 0 | 0 |
| Loop, CHI:32 | 0.119 | 68.2% | none | 159 | 49 |
| Albany Park, CHI:14 | 0.160 | 99.8% | `residential` | 5 | 2 |
| Humboldt Park, CHI:23 | 0.160 | 74.7% | `residential` | 5 | 2 |

[Exact numeric output](tile_summary.csv). The two selected São Paulo no-lot/inside-block centers gained **no OSM land-use label**. The São Domingos fiscal-residential center also had none. OSM's broad residential polygons did label two Chicago `6000` centers, but `6000` is a nonparcel/unclassifiable CMAP class; a residential polygon that covers a road or public right-of-way may **overgeneralize** surrounding use. We have not independently checked those geometries against imagery or local cadastral/road boundaries. Hence the high Chicago tile coverage cannot be treated as proof that OSM accurately fills `6000` support. The sharp São Paulo/Chicago difference within these selected tiles is strong evidence *against promoting OSM polygon area as a ready paired U1 repair*, but cannot quantify citywide completeness.

## Result: destination mapping on identical tiles

OSM `shop/amenity/office/craft/tourism` objects were spatially filtered to the same clipped land tile. The **raw tag count is not a POI count**: 110 of the 159 Loop tagged objects drop out under our provisional venue filter, largely because `amenity=bench`, `parking_entrance`, `bicycle_parking`, `loading_dock` and `parking` are infrastructure or street furniture. The filter includes named commercial, civic, service and selected tourism/amenity tags, excludes `shop=vacant` and ambiguous `*=yes`, and is documented verbatim in `pilot_u1_osm_tiles.py`. It is a screening rule, not a validated cross-city ontology. OSM node/way duplicates have **not** been fully adjudicated, so even filtered counts are candidate objects rather than unique venues.

| Tile | OSM venue candidates | OSM candidates with name | Overture records | Overture 12-class destinations | OSM candidates with exact normalized-name match ≤30 m |
|---|---:|---:|---:|---:|---:|
| Brás | 45 | 18 | 280 | 257 | 7 |
| Alto de Pinheiros | 0 | 0 | 17 | 16 | 0 |
| São Domingos | 0 | 0 | 50 | 47 | 0 |
| Loop | 49 | 49 | 1,135 | 943 | 18 |
| Albany Park | 2 | 2 | 10 | 10 | 0 |
| Humboldt Park | 2 | 2 | 11 | 11 | 1 |

[Comparison CSV](osm_overture_overlap.csv), [example matches](name_match_examples.csv), [Overture receipt](overture_receipt.json). Overture is the pinned **2026-08-19.0** Places release, fetched by six small Parquet bounding boxes and exact point-in-tile filter; matching uses exact normalized names and 30 m in local projected CRS (EPSG:32723 São Paulo, EPSG:26916 Chicago). The 12-class column follows the earlier Overture diagnostic, whereas OSM candidates use a different provisional tag screen: **these counts and categories are not an entropy comparison**. Exact-name spatial matches are a conservative agreement check, not precision/recall: legitimate venues may be unmatched owing to missing names, transliteration, point placement, vintages or provider differences. Shared coordinates/names may also reflect common upstream data. In particular, OSM's zero venue candidates in two São Paulo tiles does **not** imply no venues there; Overture mapped 17 and 50 records.

**Implication for the proposed POI variable:** OSM is too sparse in two chosen São Paulo tiles to serve as a universal replacement here. Overture is more populated in all six, but the earlier [provider-quality audit](../u1_developed_area_2026_09_22/README.md) showed asymmetric Meta dependence and taxonomy missingness. Neither source is independently validated as a common venue census. A destination-diversity statistic remains a separately named candidate, requiring manual existence/category checks and predeclared source rules; we did not compute or accept a cross-source entropy.

## Chicago portal check

The official [Business Licenses – Current Active](https://data.cityofchicago.org/Community-Economic-Development/Business-Licenses-Current-Active/uupf-x98q) view is explicitly **business licenses with future expiration dates**, a view of the broader license dataset. It has `license_id`, `license_number`, `account_number`, `site_number`, `license_description`, location and other fields. The page notes one license ID can have multiple records across transactions. A bounded official SoQL aggregate (no full download) returned:

| Community area | License rows | Rows with `location` | Distinct license numbers |
|---|---:|---:|---:|
| Loop | 3,550 | 3,509 | 3,446 |
| Albany Park | 779 | 776 | 769 |
| Humboldt Park | 806 | 800 | 794 |

[Portal metadata and query receipt](chicago_portal_receipt.json). These are **administrative license records**, not a count of establishments or all urban destinations. Multiple licenses, renewals, license-exempt activities and the `account_number`/`site_number` relationship require record-level deduplication before any venue comparison. An official portal/catalog search for the exact title “Citywide POIs” found no verified dataset; that is an unsuccessful search, **not proof of nonexistence**. If a specific dataset URL is supplied, its schema can be tested directly. The license feed is suitable as a *partial positive reference* for eligible business cases, subject to its location/record rules, not as ground truth for U1 or general POI diversity.

## Reproduction and limits

Run, from the repository root:

```bash
.venv/bin/python analysis/scripts/pilot_u1_osm_tiles.py
.venv/bin/python analysis/scripts/pilot_u1_osm_overture_overlap.py
```

The first script reuses cached XML in `analysis/work/u1_osm_tiles_2026_09_23/`; delete a cache file only if you intentionally want a **new live OSM snapshot**, which will not exactly reproduce this one. The second script queries the pinned Overture release and writes compact counts/match examples. Chicago license metadata/aggregate URLs and returned values are saved in `chicago_portal_receipt.json`. Reproduction needs prepared district-land files and the prior sampled land-point CSV. Neither script runs the 173-unit cohort.

**Acceptance remains open.** Next scientific step is a blinded, stratified manual case audit: inspect a few SP no-lot inside-block polygons, Chicago `6000` spots and OSM-only/Overture-only/matched venue records against independent current imagery or official local references; code actual use, venue existence and uncertainty. Add a second tile per stratum before inferring source rates. If OSM polygon support stays strongly asymmetric, reject it as a paired U1 area source and seek a separately defined common observed-use reference. Do not interpolate POI points into missing area or count licenses as a shared SP–Chicago venue universe.
