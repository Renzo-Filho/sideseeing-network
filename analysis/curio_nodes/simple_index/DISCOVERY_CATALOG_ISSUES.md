# Discovery Catalog: test report and issues

Tested 2 October 2026 on Curio **0.16.214** (commit `4c319953`), local install, user 3, while moving the data loading of the project "Composite urban index: method A and method B" to the Discovery Catalog. The catalog was driven through `DiscoveryService`, the class behind the `/api/discovery` routes (search, describe, acquire, job polling), as that user; the browser UI was not tested. Every call and its full answer is in [`discovery_tests/results.jsonl`](discovery_tests/results.jsonl); the harness is [`discovery_tests/harness.py`](discovery_tests/harness.py).

## What was tested

| Source | Request | Result |
|---|---|---|
| City of Chicago Data Portal (Socrata) | search "Boundaries - Community Areas"; download `igwz-8jzy` as GeoJSON | Worked (2 s). 77 areas, geometry identical to the project's own copy (symmetric difference 0 m²) |
| City of Chicago Data Portal | search "Hydro"; download `knfe-65pw` as GeoJSON | Worked (8 s). 605 polygons, identical to the project's copy |
| GeoSampa (WFS) | search; download `geoportal:distrito_municipal` | Download worked (12 s, 96 districts, EPSG:4326 as GeoJSON requires). Search has a problem: **issue 1** |
| OpenStreetMap (Autark) | Buildings for the named area Brás, São Paulo | Download worked (42 s), but buildings are grouped: **issue 2** |
| Direct URL | CTA GTFS zip, sample GTFS zip, Census TIGER blocks zip, LODES `.csv.gz`, GHSL tile zip, one Overture GeoParquet file | All refused (archive or over 64 MiB): **issue 4** |
| Search every portal | "community areas" | Worked (7 s); results from three portals, each source's state reported |
| Folder storage source (`.curio/discovery/source.sideseeing.local-data@1`) | 16 table rows and 2 raster collections | 17 of 18 adds worked (Parquet, semicolon CSV → Parquet with text codes intact, GTFS `.txt` tables, a GeoPackage → GeoParquet, raster collections). The 4.7 GB GeoPackage was refused by the 512 MiB limit after being listed as addable: **issue 3** |

The project's dataflow now reads 17 of its 21 datasets and both raster collections from these downloads and adds. The four that remain hand-registered are project-derived tables (prepared reporting units, Census blocks with housing units, São Paulo building heights from the GeoPackage too large to add).

---

## Issue 1

**Title:** GeoSampa (WFS) search matches the query as one literal substring, so natural queries miss layers

**Summary.** The WFS provider keeps a layer when the whole lower-cased query is a substring of `"<name> <title> <abstract> <keywords>"` (`providers/wfs.py`, `needle in t["haystack"]`). Multi-word queries therefore only match text that appears verbatim and in the same order, accents must match exactly, and singular/plural forms do not match each other. Common queries return nothing or miss the layer a user is after, while the Socrata portal handles the same kind of query.

**Steps to reproduce.**
1. Open the GeoSampa source page (`/catalog/discovery/source.saopaulo.geosampa@1`), or call `GET /api/discovery/sources/source.saopaulo.geosampa@1/search?q=…`.
2. Search `distrito municipal`.
3. Search `ponto onibus`, then `ponto de ônibus`, then `ponto_onibus`.
4. Search `onibus`, then `ônibus`.

**What should happen.** `distrito municipal` lists the district layer `geoportal:distrito_municipal`. A search for bus stops (`ponto onibus` or `ponto de ônibus`) lists the bus-stop layer `geoportal:ponto_onibus` ("Pontos de ônibus"). Accented and unaccented spellings return the same layers. Words should match in any order, as separate terms.

**Actual result.**
- `distrito municipal`: **0 results**; `distrito_municipal`: 1 result (the district layer, titled "Distrito").
- `ponto onibus`: **0 results**. `ponto de ônibus`: 5 results, all customer-service request layers (`sac_…`), **not** `geoportal:ponto_onibus`, whose title is the plural "Pontos de ônibus". Only `ponto_onibus` (the layer id spelling) finds it.
- `onibus` and `ônibus` return different first pages of 20 results.

---

## Issue 2

**Title:** OpenStreetMap "Buildings" download merges separate adjacent buildings into GeometryCollection features

**Summary.** The Buildings resource is described as "Building footprints, a building of several parts as one feature". In a dense area, the download instead groups many distinct buildings, each a separate OSM building with its own tags, into one feature whose geometry is a `GeometryCollection`. Each building's own tags (height, levels) survive only inside a nested `parts` list. Counting buildings, attributing heights, or any per-building analysis on the downloaded dataset is wrong, and many GIS tools do not handle GeometryCollection footprints. The grouping comes from autk-db's `loadOsm` / `getLayer`, which the provider runs unchanged (`providers/autark_osm.mjs`).

**Where the problem is: Curio, not OpenStreetMap.**
- *OpenStreetMap holds the buildings separately.* Each of the 197 entries in the largest bundle carries its own `building=yes` tag and its own height, from São Paulo's municipal import (`source=pmsp`). In OpenStreetMap, parts of one building are tagged `building:part`; these are separate buildings. Overture, whose São Paulo buildings come from OpenStreetMap, also has them separately (8,354 in Brás).
- *The grouping happens in autk-db*, the library behind Autark map nodes. The Discovery provider (`providers/autark_osm.mjs`) calls autk-db's `loadOsm` and `getLayer` and writes their output as the dataset, unchanged. Grouping adjacent footprints may suit drawing a map, but not a downloaded dataset.
- *So this is either a bug in autk-db's buildings layer or a mismatch in how the Discovery provider uses it.* A fix on Curio's side: split each grouped feature back into one feature per entry in `parts`, each with that building's own tags. If autk-db is maintained separately, the grouping is worth raising there as well.
- *Not checked:* the raw OpenStreetMap ways for one bundle were not queried directly; the evidence above is the per-building tags and Overture's count.

**Steps to reproduce.**
1. Open the OpenStreetMap source and click **Download** on **Buildings**.
2. Set **Area** to Named areas: Within `São Paulo`, area `Brás`. Download.
3. Open the dataset (`imported.x9f5dbb0daf7b` here) with GeoPandas: count features, geometry types and polygons after `explode()`.

**What should happen.** One feature per building (or per multi-part building, as described), with Polygon or MultiPolygon geometry and that building's own tags as columns. Brás holds about 8,000 buildings: Overture, whose São Paulo buildings come from OpenStreetMap, has 8,354 with their centre inside the district.

**Actual result.** **600 features**, all of type `GeometryCollection`, containing **7,968 polygons** in total; 270 features hold more than one polygon, the largest **197**. That feature's `parts` lists 197 separate entries such as `{'building': 'yes', 'height': '7.087', 'source': 'pmsp'}`, each a different building with its own height. The top-level columns of a feature describe only one of its buildings. The footprints are complete (they cover 2.03 km² of Brás's 3.63 km² of land), so nothing is missing; the buildings are grouped.

---

## Issue 3

**Title:** A storage row over the GeoPackage size limit is listed as addable and only fails after **Add to Data Catalog**

**Summary.** A folder source lists a 4.7 GB GeoPackage with `acquirable: true` and no warning, although GeoPackage adds are limited to 512 MiB. Clicking **Add** starts a job that fails at once with the limit message. The limit is known when the folder is scanned, since each row carries its size.

**Steps to reproduce.**
1. Write a folder source in `.curio/discovery/<id>@1/manifest.json` with one resource `{"kind": "table", "format": "gpkg", "datasets": "per-file", "path": "<a GeoPackage over 512 MiB>"}`.
2. Open its page: the row shows its size (4,688,367,616 bytes here) and an **Add to Data Catalog** action.
3. Click **Add to Data Catalog**.

**What should happen.** The row says it is over the 512 MiB GeoPackage limit and offers no **Add**, or **Add** is disabled with that reason, as a portal row that cannot be downloaded is marked not acquirable.

**Actual result.** The listing returns `"acquirable": true` for the row. The add starts, and the job ends `failed` with: `SP/Edificacoes/sao_paulo_building_morphology.gpkg is 4,688,367,616 bytes; the limit here is 536,870,912`.

---

## Issue 4

**Title:** Most source data of a typical urban-indicator dataflow cannot be obtained through the Discovery Catalog (archives refused, 64 MiB limit, no cloud-native subsetting)

**Summary.** The dataflow "Composite urban index: method A and method B" reads 12 public source datasets for São Paulo and Chicago. Only **3** could be fetched through the Discovery Catalog from where they are published. The other 9 are refused or have no route, for three reasons that recur across sources:

1. **Archives are refused** (`.zip`, `.gz`). The standard formats of transit schedules (GTFS), Census geography (TIGER/Line), US job counts (LODES) and the GHSL rasters are archives.
2. **The 64 MiB download limit** is below the size of single files of those products: a state's Census block file, a city transit feed, any Overture GeoParquet file.
3. **No subsetting of cloud-native data.** Overture publishes global GeoParquet files on S3 that are read with a bounding-box filter; the catalog can only fetch whole files, and has no Overture source.

The portal search does find datasets with the right names, but for other places (CNEFE for Porto Alegre and Salvador) or without the needed fields (the City of Chicago's 2020 blocks have no housing counts), so a user cannot tell from the results that the source they need is unreachable. Every one of these was added here through a hand-written folder source over files already downloaded outside Curio.

| Dataset (what the dataflow uses it for) | Published as | Tried through the catalog | Result |
|---|---|---|---|
| Chicago Community Area boundaries | City of Chicago portal | Portal download `igwz-8jzy` | **Obtained** |
| Chicago hydrography (land area) | City of Chicago portal | Portal download `knfe-65pw` | **Obtained** |
| São Paulo districts | GeoSampa WFS | Portal download `geoportal:distrito_municipal` | **Obtained** |
| CTA GTFS (Chicago transit stops) | `google_transit.zip`, 68,738,293 bytes | Direct URL | Refused: over the 64 MiB limit, and a zip |
| SPTrans GTFS (São Paulo transit stops) | GTFS zip from SPTrans | Not tested directly: a GTFS zip is refused (a 3,217-byte sample feed was refused as an archive) | No route |
| US Census 2020 blocks with housing units (Chicago dwellings) | TIGER/Line `tl_2022_17_tabblock20.zip`, 159,143,670 bytes | Direct URL; portal search | Refused: over the 64 MiB limit, and a zip. The portal's "Boundaries - Census Blocks - 2020" (`3aji-w8h2`) has identifiers only (block, tract, ward, community area, ZIP), no housing or population |
| LODES workplace jobs (shipped in the prepared Census block file; not used by the index, tested as a `.gz` example) | `il_wac_S000_JT00_2022.csv.gz` | Direct URL | Refused: `application/x-gzip archive` |
| IBGE CNEFE 2022, São Paulo (dwellings) | IBGE file archives | Portal search ("CNEFE", "CNEFE São Paulo"); not tested by Direct URL | Search lists CNEFE extracts for Porto Alegre, Salvador and other RS municipalities only; none for São Paulo |
| GHSL height and volume rasters (method B height) | Zip tiles on the JRC FTP (e.g. `…_R12_C14.zip`, 37,261,404 bytes) | Direct URL | Refused: `application/zip archive` |
| Overture Places (commercial establishments) | Global GeoParquet on S3, 614–706 MB per file | No Overture source; Direct URL on one Overture file | Refused: a 541,236,607-byte file is over the 64 MiB limit; files are global, not per city |
| Overture road segments (streets) | Same | Same (the tested file is a segment file) | Refused, as above |
| Overture buildings, Chicago (heights) | Same | Same pattern | No route |
| Overture buildings, São Paulo (heights) | Same | Same pattern; the local GeoPackage built from it (4.7 GB) is also over the 512 MiB folder-source limit | No route |

**Steps to reproduce.**
1. Open **Direct URL** (`/catalog/discovery/source.curio.direct-url@1`, **Add by link**) and download, one at a time:
   - `https://www.transitchicago.com/downloads/sch_data/google_transit.zip`
   - `https://developers.google.com/static/transit/gtfs/examples/sample-feed.zip`
   - `https://www2.census.gov/geo/tiger/TIGER2022/TABBLOCK20/tl_2022_17_tabblock20.zip`
   - `https://lehd.ces.census.gov/data/lodes/LODES8/il/wac/il_wac_S000_JT00_2022.csv.gz`
   - `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_H_GLOBE_R2023A/GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_54009_100_V1_0_R12_C14.zip`
   - `https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/release/2026-08-19.0/theme=transportation/type=segment/part-00060-efcea9bd-5042-55cd-98ec-6f3fbd419991-c000.zstd.parquet`
2. In **Search every portal**, search `CNEFE`, `CNEFE São Paulo`, `Overture` and `Census Blocks`.
3. Open the City of Chicago portal's "Boundaries - Census Blocks - 2020" and look at its fields.

**What should happen.** The standard public sources of an urban dataflow can be brought in through the catalog, or the catalog says clearly that a source is out of reach and why:
- **Archives of data files** are unpacked: a single-file zip or gzip into that file, a GTFS feed into its tables (one dataset per `.txt`, or one group, as an uploaded `.osm.pbf` becomes a group of layers), a zipped shapefile into GeoParquet, a zipped GeoTIFF tile into a raster.
- **Large or global files** can be narrowed at download, as a Socrata or WFS row already can with **Narrow…**: an Area (bounding box) and a column list for GeoParquet read in place, and a window for cloud-optimized rasters. An Overture source (places, transportation, buildings by area) would cover a large share of urban dataflows.
- **The limit** is either raised for a download narrowed by an Area or shown on the row before the download starts.

**Actual result.**
- CTA feed: `the response declares 68738293 bytes, over the 67108864-byte bound`.
- Sample GTFS feed: `that resource is a application/zip archive. Curio downloads single data files; unpack it and import the file you want.`
- Census blocks: `the response declares 159143670 bytes, over the 67108864-byte bound`.
- LODES: `that resource is a application/x-gzip archive. Curio downloads single data files; unpack it and import the file you want.`
- GHSL tile: `that resource is a application/zip archive. …`
- Overture file: `the response declares 541236607 bytes, over the 67108864-byte bound`.
- `Overture` returns 0 results; `CNEFE` and `CNEFE São Paulo` return 20 results each, none for São Paulo; Chicago's 2020 blocks carry no housing or population fields.
- Workaround used: download each source outside Curio, unpack it, and declare the files in a folder source in `.curio/discovery/`, which needs operator access to the Curio machine.

---

## Limitations met (documented, not bugs)

- **Most source data has no route in:** see issue 4. It was added instead through a folder source over files downloaded outside Curio.
- **GeoJSON downloads are in EPSG:4326.** GeoSampa's districts arrive in WGS84 rather than the layer's native SIRGAS 2000 / UTM 23S; the round trip moves boundaries by millimetres (largest area change 1.05 m²), which changed method B's index by at most 2.8e-7 and no rank.
- **Downloaded datasets get opaque ids** (`imported.x662f76045de9`), so a loader's `curio_dataset_path("imported.x…")` does not say what it reads; the dataflow's loaders carry a comment naming each source.
