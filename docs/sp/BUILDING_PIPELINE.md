# São Paulo building morphology pipeline

Current technical reference, reviewed 10 September 2026. The completed extraction is unchanged. Current project status is in `SP_DATA_RESOLUTION_HANDOFF.md`; no new cloud extraction was required for v3 integration.

This pipeline extracts Overture building polygons intersecting the bounding box of metropolitan São Paulo. It queries remote GeoParquet on the public Overture S3 bucket through DuckDB, then computes metrics in bounded GeoPandas batches. It does not download fragmented GeoSampa building archives.

## Run

From the repository root, with a Python virtual environment:

```bash
python -m pip install -r analysis/requirements-buildings.txt
python analysis/scripts/prepare_overture_sp.py
python analysis/scripts/extract_sao_paulo_buildings.py --self-test
python analysis/scripts/extract_sao_paulo_buildings.py
```

Network access is needed for official IBGE geography, Overture STAC metadata, signed DuckDB extensions and selected S3 byte ranges. No AWS credentials are required. Preparation pins the release from the catalog into `analysis/cache/overture_sp`; reruns reuse that release and the completed extraction. For a different release or extent, use a fresh cache. Old Overture releases may eventually be unavailable remotely.

The extraction uses a 2 GB DuckDB memory limit, four query threads and 25,000-record GeoPandas batches. `--batch-size` controls the latter. The memory limit applies to DuckDB, not the entire Python process. The script refuses to overwrite an existing final or partial GeoPackage. After an interrupted conversion, move the partial file aside before rerunning; a completed filtered Parquet stage is reusable without another cloud query.

## Selection and geometry

- Release: **2026-08-19.0**, pinned from the official catalog during this run.
- Scope: the 39 municipalities listed by the IBGE metropolitan-region API, ID `04901`.
- IBGE municipal extent in WGS84: approximately `[-47.2084, -24.0643, -45.6948, -23.1834]`.
- Outward-rounded extraction bounding box: **west -47.21, south -24.07, east -45.69, north -23.18**.
- STAC file-extent pruning is followed by Parquet bbox predicate pushdown and exact geometry/box intersection.
- Complete source footprints are retained at the box edge; they are not clipped into partial buildings.
- Source geometry is EPSG:4326. All delivered spatial layers use **SIRGAS 2000 / UTM zone 23S, EPSG:31983**.
- Areas are calculated only after projection. Invalid geometries are repaired where possible and flagged; an unrecoverable polygon fails the run instead of silently losing a building.

The bounding box includes neighboring territory outside the metropolitan municipality union. Use `in_rmsp = 1` to select buildings whose interior representative point falls within that union. This is based on generalized IBGE API cartography, not a cadastral boundary adjudication. The two boundary layers make this distinction inspectable.

## Delivered GeoPackage

`analysis/data/SP/Edificacoes/sao_paulo_building_morphology.gpkg`

| Layer/table | Contents |
|---|---|
| `buildings` | One record per Overture building ID, with full MultiPolygon geometry and morphology attributes |
| `rmsp_boundary` | Union of the 39 metropolitan municipal polygons |
| `extraction_bbox` | Actual extraction box |
| `morphology_metadata` | Nonspatial provenance, definitions, query scope and aggregate quality checks |

Core fields in `buildings`:

| Field | Meaning |
|---|---|
| `building_id` | Overture ID, enforced unique by a database index |
| `footprint_area_m2` | Projected footprint area in square metres |
| `height_m` | Source building height in metres when available; null otherwise |
| `floor_count` | Source number of above-ground floors when available; null otherwise |
| `gross_floor_area_m2` | `footprint_area_m2 * COALESCE(floor_count, 1)` |
| `floors_used_for_gfa` | Floor multiplier actually used in the calculation |
| `floor_count_imputed` | True where the missing floor count was replaced with 1 for GFA only |
| `underground_floor_count` | Separately reported basement-floor count where available |
| `has_parts` | Source flag for associated building parts; parts are not double-counted as additional buildings |
| `is_underground` | Source flag for wholly underground buildings |
| `geometry_repaired` | Whether geometry repair was necessary |
| `in_rmsp` | Representative point lies in the metropolitan municipality union |
| `sources_json` | Source-specific attribution, source record IDs and available provenance |
| `overture_release` | Release identifier |

**GFA is an estimate, not measured actual floor area.** The requested formula assumes every floor occupies the entire footprint. A one-floor fallback does not establish that a building has one floor. Overture defines `num_floors` as above-ground floors, so the calculation does not include basement floor area; basement counts are retained separately. Heights are not inferred from floor counts, and missing floor counts are not inferred from heights. Buildings with varying-height parts may need a later part-level volume model.

Coverage means all matching building records in the selected Overture release. It is not a guarantee that every physical building is mapped, or that source footprints represent cadastral wall outlines rather than imagery-derived roofprints. Missing height/floor coverage must be considered before using B2/B3 for neighborhood similarity.

The completed cloud query selected **7,278,768 records** from **four of 512** Parquet assets. Of these source records, **2,090,405 (28.7192%)** have height and **21,250 (0.2919%)** have above-ground floor counts. Therefore **7,257,518 (99.7081%)** require the requested one-floor GFA fallback. These are bounding-box-wide source coverage rates, not rates for Brás or the metropolitan-only subset.

For the current model, B2 uses a separately validated cadastral floor-count proxy and B3 targets cadastral constructed area. Do not substitute the mostly one-floor Overture GFA scenario for either. The existing file remains useful for footprints and source-height diagnostics. Municipal district analysis requires an actual municipal restriction; metropolitan membership alone is insufficient.

## Validation

The pipeline verifies projected area and null-floor fallback against synthetic 10 m squares, reconciles source and output record counts, validates all output geometries before writing, enforces unique/nonmissing IDs, checks the stored GFA formula over the full table, checks SQLite integrity, verifies CRS and layer counts, and recalculates area from a sample of the exported geometries. A `.partial.gpkg` is renamed to the final filename only after these checks pass.

A JSON metadata sidecar duplicates the embedded metadata for convenient inspection. The filtered WKB Parquet checkpoint, STAC catalog/items, IBGE inputs and executed SQL remain in the cache to support reproduction; they are not substitutes for the delivered GeoPackage.

## Municipal preparation in v3

`analysis/scripts/prepare_sp_v3.py --stages N06` reads the existing indexed GeoPackage in 25,000-record batches. It retains buildings with positive intersection area in the 96-district municipal union, assigns each whole footprint to the district with the largest intersection (ascending ID breaks ties), and saves district GeoParquet partitions with source IDs and parcel-overlap candidate tables. No fiscal area is transferred to footprints. N09 independently rescans the source municipal extent to reconcile the prepared count; current results are in `SP_DATA_RESOLUTION_HANDOFF.md`. The original GeoPackage and its metropolitan scope remain unchanged.

## Sources

- [Overture catalog](https://stac.overturemaps.org/catalog.json)
- [Official DuckDB extraction guidance](https://docs.overturemaps.org/getting-data/duckdb/)
- [Overture building schema](https://docs.overturemaps.org/schema/reference/buildings/building/)
- [Overture attribution guidance](https://docs.overturemaps.org/attribution/)
- [IBGE metropolitan membership](https://servicodados.ibge.gov.br/api/v1/localidades/regioes-metropolitanas/04901)
- [IBGE municipal geography](https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&qualidade=maxima&intrarregiao=municipio)

Source-level attribution is retained in every building's `sources_json`; consult those fields and the release attribution terms when redistributing the resulting data.
