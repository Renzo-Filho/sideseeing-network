# Data register: `analysis/data/`

This folder holds the original downloads behind every São Paulo and Chicago feature, check and model in this repository. Each dataset has an entry below: what it contains, how it was obtained, what it was used for, and its reuse terms and known gaps.

- **Snapshot:** 20 October 2026, 3,480 files, 19.66 GB (Chicago 7.30, SP 10.80, shared 1.56). That day, 5.45 GB of duplicates and files no model uses were removed (see [Removed on 20 October 2026](#removed-on-20-october-2026)), leaving 14.21 GB (Chicago 3.62, SP 9.03, shared 1.56).
- **Git:** the data files are git-ignored. Only this README and [`SHA256SUMS`](SHA256SUMS) are tracked. `SHA256SUMS` keeps the hash of every file in the 20 October snapshot, removed files included.
- **Integrity, checked 20 October 2026 before the removals:**
  - All 153 SP files fingerprinted by the frozen SP preparation on 10 September (`work/prepared/SP/sp_prep_2026_09_10_v3/N01/manifest.json`) were byte-identical.
  - So were all 18 Chicago files hashed by the first Chicago release on 16 September (`results/Chicago/chi_local_2026_09_16_v1/validation/source_manifest.json`).
  - Every SHA-256 quoted in `analysis/docs/` and in the result READMEs matched the file on disk.

**Verify** (a deleted file is skipped, not reported as a failure):

```bash
cd analysis/data && sha256sum -c --quiet --ignore-missing SHA256SUMS
```

## How to read the register

**Use** codes. A dataset can carry several.

| Code | Meaning |
|---|---|
| **Model** | Direct input to a feature of the fitted models: Chicago model v1 (`config/chicago_model_v1.json`) and the São Paulo–Chicago model v1–v4 (`config/sp_chicago_model_v*.json`), which share the same 12 families |
| **Check** | Reference in a pre-registered acceptance check of a model family, or evidence behind a stated limit. Needed to rerun the acceptance record in `docs/chicago/MODEL_PLAN.md` |
| **SP v2** | Input to the frozen São Paulo attribute release `sp_attributes_2026_09_11_v1` and SP model v2 (`analysis/docs/sp/`) |
| **Index** | Advisor's simple index, methods A/B (`analysis/docs/SIMPLE_INDEX.md`) |
| **Pilot** | Only used by earlier discovery, pilots or superseded releases |
| **Unused** | No script reads it |

- **Obtained:** a script name means the download is reproducible from code; "manual" means a person downloaded it.
- **Dates:**
  - A filename date or "saved" date is the download date, not the observation period. The observation period is given where the publisher states it.
  - "File dated" is the file's modification time on disk, recorded where no download date exists.
- **Sizes** are decimal MB (10⁶ bytes).

## What the models read

Inputs of the 12 families in `chicago_model_v1.json` and `sp_chicago_model_v1`–`v4`. The build scripts are in `analysis/scripts/`. Their outputs are the tables named in the contracts, under `results/SP_CHI/` and `results/Chicago/`.

| Family | Chicago input | São Paulo input | Build script | Acceptance checks used |
|---|---|---|---|---|
| Units, land (C2) | Community Areas; City hydrography | GeoSampa districts; GeoSampa water bodies | `prepare_chicago.py`, `prepare_sp_inputs.py` / `sp_v3` N02 → `work/prepared/` | — |
| U3 residents | ACS 2020–24 B01003, split by 2020 blocks (TIGER) | Census 2022 tracts (`densidade_demografica`) | `evaluate_chicago_u3_step1.py`, `evaluate_sp_u3_catchup.py` | — |
| U4 transit (PTAL) | CTA GTFS, Metra GTFS, Overture segments (walk network), U3 residents | SPTrans GTFS (bus, Metrô, CPTM), Overture segments, Census tracts | `evaluate_u4_ptal_step2.py` | TfL guide (method) |
| U2 jobs | LODES 2023 WAC, 2020 blocks | RAIS 2022 by CEP + CEP allocation evidence (`work/evidence/`) | `evaluate_u2_step3.py` | LODES 2022, OD 2023, CMAP travel survey, `jobs_docs/` |
| B1 coverage | Overture buildings | Overture buildings (`Edificacoes/` GeoPackage) | `prepare_harmonized_footprints.py`, `curio_nodes/B1.py` | Cook 2022 footprints, City 2015 footprints, GeoSampa `edificacao`, Microsoft (SP), OSM, IPTU |
| BV height | GHSL city clips | GHSL city clips | `evaluate_bv_step5.py` | Cook 2022 heights, GeoSampa LiDAR 2020, GeoSampa `edificacao`, IPTU |
| M1, M6 streets | Overture segments | Overture segments | `evaluate_m1_m6_step6.py` | City centerlines; GeoSampa logradouros, `classvias` |
| M3, M4 blocks | Overture segments, hydrography | Overture segments, water (N02) | `evaluate_m3_m4_m7_step8.py` | centerlines, 2020 blocks; logradouros, `quadra_viaria_editada` |
| M7 parcels | Cook 2024 parcels | GeoSampa fiscal lots | `evaluate_m3_m4_m7_step8.py` | Cook parcel universe; IPTU, fiscal blocks |
| U1 land shares | CMAP LUI 2023 | IPTU 2026 + fiscal lots | `evaluate_u1_step7.py` | Cook parcel universe, Cook parcels; CNEFE |
| U6 activity | Overture places; ACS B25001 dwellings | Overture places; CNEFE dwellings | `build_u6_activity.py` | business licences; RAIS 2022 establishments; CNEFE |
| Neighborhood breakdown | City neighborhoods, plus the inputs above | — | `chicago_neighborhoods.py` | — |

## Chicago (`Chicago/`)

### Units, population, jobs

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `Boundaries_-_Community_Areas_20260831.geojson` | 2.1 | City of Chicago Community Areas: 77 polygons, WGS84, two agreeing ID fields | Manual, City data portal dataset `igwz-8jzy`, 31 Aug 2026 | **Model**: the 77 units of every family; spatial filter of the cadastral acquisitions; their union (+2 km) set the Overture bbox | SHA `c4b9c42a…` is recorded in every cadastral manifest |
| `Hydro_20260916.geojson` | 2.8 | City hydrography: 605 polygons (rivers, canals, Lake Michigan) | Manual, portal `knfe-65pw`, 16 Sep 2026 | **Model**: water removed from every land denominator (C2) | Edit dates mostly March 2001; observation year unresolved; city only (misses a Cook-side O'Hare pond) |
| `Boundaries_-_Neighborhoods_20261013.geojson` | 2.2 | City's 98 neighborhoods | Manual, portal `bbvz-uum9`, 13 Oct 2026 | **Model** (breakdown): neighborhood pieces scored with the fitted model (MODEL_REPORT §10) | The City calls the layer approximate and unofficial |
| `acs_2020_2024_5yr/` | 41.7 | ACS 2020–2024 5-year table-based Summary File: `acsdt5y2024-b01003.dat` (total population), `-b25001.dat` (housing units), table shells; all geographies, block groups used | Manual, `https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/`, 2 Oct (B01003) and 6 Oct 2026 (B25001) | **Model**: U3 residents, U4 resident weights, U6 dwellings | Pooled 2020–2024 on 2020 geography; block-group MOE. File URLs in MODEL_PLAN Step 1 |
| `tl_2022_17_tabblock20/` | 308.6 | TIGER/Line 2022 Illinois 2020 tabulation blocks: 369,978 polygons, EPSG:4269, `POP20` (2020 count after disclosure avoidance), ISO metadata, PL 94-171 tech doc | Supplied extracted by the user; publisher ZIP `https://www2.census.gov/geo/tiger/TIGER2022/TABBLOCK20/tl_2022_17_tabblock20.zip` | **Model**: block support that carries ACS and LODES counts into areas (U2, U3, U4, U6). **Check**: official-block reference for M3. **Index** | Original archive checksum not supplied |
| `lodes_2023/il_wac_S000_JT00_2023.csv.gz` | 2.1 | LEHD LODES 8, workplace area characteristics 2023, Illinois, all workers (S000), all jobs (JT00), by 2020 block | Manual, `https://lehd.ces.census.gov/data/lodes/LODES8/il/wac/`, 5 Oct 2026 | **Model**: U2 | UI-covered and Federal jobs, about 1 April 2023; partly synthetic (noise infusion) |
| `il_wac_S000_JT00_2022.csv` | 12.2 | LODES WAC 2022, same universe: 91,481 workplace blocks, 5,825,390 jobs statewide, `createdate=20240920` | Supplied extracted by the user | **Check**: 2022 comparison in `evaluate_u2_step3.py`. **Pilot**: U2 of `chi_functional_2026_09_16_v2` and the employment sensitivity | Compressed-file identity not established |
| `chicago_acs_community_areas.csv` | <0.1 | 77 rows labelled ACS 2023 resident totals | Supplied | **Pilot**: provisional U3 of `chi_local_2026_09_16_v1` | Source table, period, MOE and aggregation unknown; tested 2 Oct 2026 and it is **not** the 2020–2024 release |
| `cook_county_tracts_pop_2019.csv` | <0.1 | Cook tracts, `B01003_001E` labelled 2019, no geometry | Supplied | **Unused** | |

### Transit

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `google_transit/` | 429.3 | CTA static GTFS (bus and 'L'): calendar 11 Sep–30 Nov 2026, 124 bus routes, 8 'L' lines; includes the developer licence agreement | Supplied extracted (files dated 14 Sep 2026); publisher `https://www.transitchicago.com/downloads/sch_data/google_transit.zip` | **Model**: U4 bus and metro. **Pilot**: bus supply in `chi_functional` v2. **Index** | The publisher serves only the current feed, so this exact feed cannot be downloaded again. Licence: CTA developer agreement (in folder) |
| `metra_gtfs_2026_10_05/` | 13.5 | Metra GTFS, 11 lines: `schedule.zip` and its extracted files (byte-identical; both kept because `evaluate_u4_ptal_step2.py` hashes both) | Manual, `https://schedules.metrarail.com/gtfs/schedule.zip`, 5 Oct 2026 | **Model**: U4 rail | Column names have leading spaces; service periods change weekly |
| `CTA_-_System_Information_-_List_of_'L'_Stops_20260915.csv` | 0.1 | 302 directional 'L' stop records | Supplied, 15 Sep 2026 | **Unused** | The GTFS feed covers it |

### Streets, buildings, height

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `overture_2026_08_19/` | 284.6 | Overture Maps release 2026-08-19.0, whole objects intersecting the city bbox plus 2 km: `building/` 1,381,239 (159.4 MB), `segment/` 350,885 (66.5), `connector/` 689,832 (32.5), `place/` (26.2) | `acquire_harmonized_overture.py`, 16 Sep 2026 (places 1 Oct). Each subfolder's `manifest.json` records the S3 asset, SQL, schema, access time, counts and hashes | **Model**: B1 (buildings), M1, M6, M3, M4 and the U4 walk network (segments), U6 (places). **Index** | Roads ODbL; places CDLA-Permissive-2.0 / Apache-2.0; buildings per-source attribution in `sources`. Old releases are eventually removed from S3 |
| `steet_center_lines_20260915.geojson` [sic] | 83.6 | City street centerlines (`6imu-meau`): 56,338 records, CLASS/STATUS codes, from/to levels, length in feet | Supplied, 15 Sep 2026 | **Check**: municipal reference for M1/M6 and M3/M4. **Pilot**: local M1/M6 in `chi_local` v1, M3 block pilots | Field dictionary PDF in `work/evidence/chicago_centerline_dictionary/`; code meanings in `docs/chicago/DATA_SOURCES.md` |
| `Building_Footprints_20260915.geojson` | 1,109.8 | City building footprints: 820,606 records, `stories` field; publisher metadata (`syp8-uezg`) says current as of August 2015 | Supplied, 15 Sep 2026 | **Check**: municipal 2015 footprints reported (not ruled) in B1 Step 4. **Pilot**: B1/B2 in `chi_local` v1, floor-field scan | `no_stories` is below-ground stories; `bldg_sq_fo` and `z_coord` not maintained. A byte-identical copy is installed as Curio dataset `data.cityofchicago.building-footprints@1` (checked 20 Oct 2026) |
| ~~`Building_Permits_20260915.geojson`~~ **removed 20 Oct 2026** | 2,965.6 | City building permits: events with descriptions, fees, dates, points | Supplied, 15 Sep 2026 | **Pilot** only: `scan_chicago_floor_fields.py` searched it for floor/area fields (B2/B3, later refused) | Permits do not enumerate the building stock |
| `ghsl_public_2026_09_21/` | 0.6 | GHSL R2023A clips for Chicago: ANBH and AGBH height 2018, BUILT-V volume 2020, 100 m Mollweide, each with a JSON receipt (source tiles, SHA-256) | `acquire_ghsl_city_rasters.py` from `shared/ghsl_public_2026_09_21/`, 21 Sep 2026 | **Model**: BV | CC BY 4.0 (EU/JRC) |
| ~~`microsoft_buildings_2026_08_13/raw_tiles/`~~ **removed 20 Oct 2026** | 230.0 | Microsoft Global ML Building Footprints, 13 Aug 2026 release: three level-9 quadkey tiles (`.geojsonl.gz`) | Supplied by the user; matched to the link index and moved by `organize_microsoft_building_downloads.py` (`scripts/_archive/one_time_migrations.zip`) | **Pilot**: `microsoft_footprints_2026_09_22_review` | CDLA-Permissive-2.0. Microsoft footprints are not used by any model |

### Land use and activity

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `LUI_2023_view_332920193481040239.gpkg` | 635.7 | CMAP Land Use Inventory 2023: parcel-based polygons with primary and secondary `LANDUSE`, EPSG:3857 | Supplied | **Model**: U1 land shares. **Pilot**: U1 entropy (`chi_local` v1), M3 pilots, employment sensitivity | Code `6000` = generated non-parcel polygons. Field guide: `cmap-repos.github.io/LUI-wiki` |
| `lui_2023_docs/` | <0.1 | LUI_2023_view layer-1 schema (code domain) | Fetched 1 Oct 2026; SHA `3ef224bc…` | Documentation of the U1 codes | |
| `business_licenses_2026_10_06/` | 30.0 | City "Business Licenses – Current Active" (`uupf-x98q`). The full export `business_licenses_current_active.csv` is **truncated**: it ends mid-record after 43,366 complete rows, while the U1 audit counted 54,006 licences; no script reads it. The two files scripts read are distinct-row extracts of the whole table: `license_site_activities.csv` (52,106 rows: community area, account, site, licence description, activity) and `license_sites_by_area.csv` (43,762 rows: community area, account, site) | Manual, 6 Oct 2026 | **Check**: U6 check V2 (Overture vs licensed sites, from `license_site_activities.csv`), U1 alternatives audit (`license_sites_by_area.csv`) | The two extracts have no duplicate rows and cover the same sites: every site of the truncated export plus 7,633 more (checked 20 Oct 2026). The query text that made them was not saved, and the live table has changed since |
| `business_2652811-20190701_20260915.geojson` | <0.1 | 20 licence records of one account | Supplied | **Unused** | Not a business census |
| ~~`Boundaries_-_Zoning_Districts_(current)_20260915.geojson`~~ **removed 20 Oct 2026** | 39.8 | Current zoning polygons | Supplied | **Unused** | Regulation, not observed use |
| `Socioeconomically_Disadvantaged_Areas_20260831.geojson` | 0.7 | City layer of that name | Supplied | **Unused** | |
| ~~`chicagosidewalks/`~~ **removed 20 Oct 2026** | 202.6 | City sidewalk polygons, shapefile (files dated 30 Nov 2011; publisher marks it a draft) | Supplied | **Unused** | Listed as future pedestrian context |
| `morphological_data.csv` | <0.1 | One dummy Brás row, `ca=99`, all metrics zero | Supplied | **Unused**, explicitly excluded | Never read these zeros as data |

### Cook and DuPage cadastre (`chicago_cadastral_2026_09_18/`, 497.3 MB)

Acquired by `acquire_chicago_cadastral.py` on 18 September 2026 (commercial bulk CSV via `acquire_chicago_assessor_bulk.py`). Each subfolder's `manifest.json` records:
- the source URL and query;
- remote and kept row counts and the spatial filter;
- part hashes and limitations.

Raw bulk CSVs are in `work/evidence/chicago_cadastral_2026_09_18/`. `documentation/` holds the Assessor open-data SOP, the class definitions and the DuPage publisher terms. Audit: `results/Chicago/chicago_cadastral_2026_09_18/` (4,473 checks).

| Subfolder | MB | Content | Use |
|---|---:|---|---|
| `cook_parcels_2024/` | 95.7 | Cook 2024 parcel polygons, 613,802 Chicago-intersecting rows (clipped; original area kept), EPSG:26916 | **Model**: M7 (ground pieces, rule of 30 Sep 2026). **Check**: U1 post-hoc land-area diagnostic. **Pilot**: M3 pilots |
| `cook_universe_2024/` | 61.4 | Assessor Parcel Universe 2024 (`nj4t-kc8j`), 883,597 Chicago PIN rows with class | **Check**: M7 (distinct PIN10), U1 S7-5 (residential PIN share) |
| `cook_buildings_2022/` | 306.0 | Cook 2022 LiDAR building footprints with height, 779,962 Chicago rows | **Check**: B1 S4-2 (Spearman 0.983), BV S5-5 and the LiDAR bias sample |
| `cook_residential_2024/`, `cook_condo_2024/`, `cook_commercial_2024/` | 33.2 | Assessor improvement characteristics (439,730 / 287,189 / 32,930 Chicago rows) | **Pilot**: B2/B3 investigation (both families refused) |
| `benchmarking_2023/`, `benchmarking_covered_current/` | 0.9 | Energy benchmarking 2023 (3,434) and covered-building register (3,693) | **Pilot**: B3 investigation |
| `dupage_parcels_current/` | 0.1 | DuPage parcels intersecting Chicago (81) | **Pilot**: M7 O'Hare and M3 DuPage pilots. **DuPage terms prohibit redistributing this layer** |

### Other Chicago acquisitions

| Path | MB | Content | Obtained | Use |
|---|---:|---|---|---|
| `osm_2026_10_01/` | 4.1 | 30,265 named OSM objects (shop, amenity, office, craft, healthcare, tourism) in the Chicago bbox | `acquire_osm_places.py` from `shared/osm_geofabrik/illinois-latest.osm.pbf`, 1 Oct 2026; `manifest.json` | **Index** (`evaluate_places_against_cnefe.py`). ODbL |
| `cmap_mdt_2024_25/` | 111.7 | CMAP travel-survey public archive `TravelSurveys_PublicData_CMAP.zip` (holds My Daily Travel 2024–25 Phase 1 and older surveys) and its readme. Two nested extractions of the archive (221.3 MB, verified identical) were removed on 20 Oct 2026; unzip `MyDailyTravel_2024_2025Phase1.zip` from the archive to get them back | Manual, 5 Oct 2026, URL in `results/SP_CHI/u2_work_data_search_2026_10_05/README.md`; SHA `e7e9ec59…` | **Check** (computed by hand, no script): U2 source audit. 1,313 sampled workers in tracts touching Chicago, too few for area estimates |
| `chicago_workbooks_2026_09_19/` | 34.5 | Firecrawl text extracts of the eight 2024 Cook commercial valuation workbooks, 32,231 detail records | Firecrawl, 19 Sep 2026 (binaries returned HTTP 403) | **Pilot**: B2/B3 |
| `manual_acquisition_2026_09_21/` | 11.4 | Request texts (Addison, Cook); 81 DuPage PINs; Cook PIN scope ZIP (its unzipped CSV, 23.0 MB, identical, was removed on 20 Oct 2026); `incoming/` with seven 2024 valuation XLSX (T76 missing) | Prepared 21 Sep 2026; XLSX saved by the user the same day | **Pilot**. The XLSX were never validated or transformed |
| `dupage_characteristics_2026_09_21/` | <0.1 | 81-parcel lookup list, township intersections | Copied from the validated DuPage parcel subset, 21 Sep 2026 (`results/Chicago/dupage_characteristics_2026_09_21/`) | **Pilot** |

## São Paulo (`SP/`)

The municipal layers, including `IPTU_2026.csv`, were downloaded manually by the user from GeoSampa (`geosampa.prefeitura.sp.gov.br`). Most file dates fall between 5 and 10 September 2026. GeoSampa layer names match the file names. The exact download dates were not written down, so the file date on disk is given instead. Their SHA-256 values were frozen on 10 September 2026 in the SP preparation manifest. CRS for metric work is EPSG:31983.

### Units, population, jobs

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `Cadastro e Vias/distrito_municipal_v2.gpkg` | 2.4 | 96 municipal districts | GeoSampa (layer `geoportal:distrito_municipal`), file dated 5 Sep 2026 | **Model**: the 96 units (via `work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet`). **SP v2**, **Index** | 22.067 m² of inter-district overlap given to the lower ID |
| `Meio Ambiente/massa_d_agua.gpkg` | 12.1 | Water bodies | GeoSampa, file dated 10 Sep 2026 | **Model**: water removed from district land (N02), all land denominators. **SP v2** | |
| `Socioeconomico/densidade_demografica.gpkg` | 25.1 | Census 2022 population by census tract: 27,301 tracts, 11,451,999 residents | GeoSampa, file dated 31 Aug 2026 | **Model**: U3, U4 resident weights. **SP v2**: U3, U4 | Area allocation to districts conserves the total |
| `Socioeconomico/CNEFE_2022/` | 946.6 | IBGE CNEFE 2022 address list for the municipality (`3550308_SAO_PAULO.csv`: every address with species, enumerator description, coordinates), plus IBGE method notes in `docs/` | IBGE, `https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/Censo_Demografico_2022/Arquivos_CNEFE/CSV/Municipio/35_SP/3550308_SAO_PAULO.zip` (file dated 17 May 2024) | **Model**: U6 dwellings. **Check**: U1 S7-5, U6 CNEFE variant (`*_sp_cnefe`). **SP v2**: U2 address evidence. **Index** | `;`-separated. Misses offices stacked in towers (U6 finding) |
| `Socioeconomico/rais_empregos_sp_2022.csv` | 0.4 | RAIS 2022 active formal jobs summed by CEP: 29,594 CEPs, 5,387,474 jobs (columns `cep`, `empregos`) | `fetch_RAIS.py` (Base dos Dados BigQuery, `br_me_rais.microdados_estabelecimentos`, `ano=2022`, `id_municipio=3550308`), file dated 10 Sep 2026 | **Model**: U2 (area-first CEP allocation). **SP v2**: U2 | The pandas `groupby` drops CEP-null rows. Checked 20 Oct 2026 against `rais_2022_estab`: 281 establishments with null CEP hold exactly 2,972 jobs, the full gap to the official 5,390,446. CEP `99999999` holds 351,576 unlocatable jobs |
| `rais_2022_estab/rais_estab_sp_2022.parquet` | 2.7 | RAIS 2022 establishment microdata for the municipality: 702,834 records, CNAE 2.0, CEP (`distritos_sp` empty) | `fetch_RAIS_estab.py` (Base dos Dados), 6 Oct 2026; SHA `0849e70f…` | **Check**: U6 instrument test D7b-3 | 314,022 non-"RAIS negativa" records match the city's published 2022 table |
| `od2023_metro/` | 396.7 | Metrô Pesquisa Origem-Destino 2023 site package (tables, microdata `.sav`/`.dbf`, layout, zone maps): the ZIP and its byte-identical extraction `Site_190225/` | Manual, `https://transparencia.metrosp.com.br/sites/default/files/Site_190225_PesquisaOD2023.zip`, 5 Oct 2026; SHA `1844d38a…` | **Check**: U2 OD agreement test (`audit_u2_od2023.py`, `evaluate_u2_step3.py`) | The scripts read the folder; `evaluate_u2_step3.py` also hashes the ZIP, so both stay |

### Transit

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `Socioeconomico/f-6gy-sptrans-latest/` | 69.9 | SPTrans GTFS: bus, Metrô and CPTM; all trips as headways (`frequencies.txt`, 40,402 rows); calendar 2023-10-01 to 2027-04-01; no `feed_info` | Manual from the SPTrans developer area (`BaixarGTFS`), 9 Sep 2026 | **Model**: U4 bus, metro, rail. **SP v2**: U4 (which also counted 9 metro and 7 rail routes). **Index** | Calendar range is not an observation date; no holiday exceptions |

### Streets and blocks

| Path | MB | Content | Obtained | Use |
|---|---:|---|---|---|
| `Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg` | 55.4 | Municipal street lines (logradouros), 219,190 valid edges | GeoSampa, file dated 6 Sep 2026 | **SP v2**: M1, M2, M6. **Check**: M1 (S6-6), M3/M4 like-for-like (S8-4, failed because of line-end gaps) |
| `Cadastro e Vias/classvias.gpkg` | 61.4 | Street functional classification | GeoSampa, file dated 13 Nov 2025 | **SP v2**: M6. **Check**: M6 major share |
| `Cadastro e Vias/geoportal_classificacao_viaria_cet.gpkg` | 21.5 | CET road classification | GeoSampa, file dated 10 Sep 2026 | **SP v2** (v2 baseline preparation). **Pilot**: street-class inventory |
| `Cadastro e Vias/obra_arte.gpkg` | 2.1 | Bridges, viaducts, tunnels (mostly referenced to 2004) | GeoSampa, file dated 10 Sep 2026 | **SP v2**: M2 5 m exclusion |
| `Cadastro e Vias/quadra_viaria_editada.gpkg` | 115.1 | Municipal blocks: 65,720 records, 46,801 of type `Quadra` | GeoSampa, file dated 8 Sep 2026 | **SP v2**: M3, M4. **Check**: official-block reference for M3 (0.977) |
| `Cadastro e Vias/GEOSAMPA_v_praca_largo.gpkg` | 4.7 | Squares | GeoSampa | **Pilot**: U1 gap context |
| `Cadastro e Vias/area_influencia_trem.gpkg` | 0.6 | Rail influence/domain polygons | GeoSampa | **Pilot**: local rail block-boundary test |

### Cadastre and land use

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `Cadastro e Vias/IPTU_2026.csv` | 937.9 | IPTU 2026 fiscal register: one row per fiscal account (3,920,972 unique accounts) with contributor number (sector–block–lot), condominium, use type, land, built and occupied area, floors, construction year | Manual download from GeoSampa by the user (file dated 11 Feb 2026) | **Model**: U1. **Check**: M7 (distinct lots), B1 occupied-area test, BV floors comparison. **SP v2**: M7, B2, B3, U1, U2 support | `;`-separated, UTF-8 (reading it as latin-1 garbles use labels). Fiscal accounts are not physical buildings |
| `Cadastro e Vias/Dicionario_dados_IPTU.xlsx`, `iptu_dict_summary.txt` | <0.1 | IPTU field dictionary, and a text copy of its definitions | Supplied | **SP v2** (`sp_v3/fiscal.py`); documentation | |
| `Cadastro e Vias/Lotes/` | 556.5 | Fiscal lot polygons, 96 GeoPackages, one per district | GeoSampa, files dated 6 Sep 2026 | **Model**: M7 and U1 lot areas (cached in `work/u1_step7_2026_10_06/`). **SP v2**: M7, parcel geometry | All non-zero condominium rows use lot `0000`: the entity key is sector–block–condominium |
| `Cadastro e Vias/geoportal_quadra_fiscal_gsc.gpkg` | 105.5 | Fiscal blocks (sector + block) | GeoSampa, file dated 5 Sep 2026 | **Check**: places IPTU lots in districts for the M7 check and the B1 occupied-area test; height audit | |

### Buildings and height

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `Edificacoes/sao_paulo_building_morphology.gpkg` (+ `.metadata.json`, `.validation.json`) | 4,688.4 | Overture 2026-08-19.0 buildings over the metropolitan bbox: 7,278,768 records, EPSG:31983, footprint area, height (28.7%), floors (0.3%), layers `buildings`, `rmsp_boundary`, `extraction_bbox`, `morphology_metadata` | `prepare_overture_sp.py` + `extract_sao_paulo_buildings.py`; method in `docs/sp/PREPARATION.md`. The executed SQL, extraction manifest, STAC items and IBGE inputs are kept in `analysis/cache/overture_sp/`; the 679 MB filtered Parquet checkpoint was removed on 20 Oct 2026 | **Model**: B1. **Check**: footprints for the LiDAR sample. **SP v2**: B1. **Index** | `gross_floor_area_m2` assumes one floor where floors are missing (99.7%); not a floor-area measure. Read in chunks (whole-file reads run out of memory) |
| `geosampa_edificacao_2026_10_05/` | 373.2 | GeoSampa `edificacao` WFS layer: 2,817,745 photogrammetric outlines with height, 141 zipped pages + `manifest.json` (page hashes) | `acquire_geosampa_edificacao.py`, 5 Oct 2026 | **Check**: B1 S4-3 (failed → stated limit), Brás B1 check, BV S5-6 (withdrawn) | Aerial photographs of 2004; records created 2007, last edit 2014 |
| `geosampa_lidar_2020/` | 2.9 | GeoSampa LiDAR 2020 tile index (`quadricula_mdt_mds_2020.geojson`, 5,401 tiles) and `sample_tiles.csv` (two random tiles in each of Brás, Itaim Bibi, Cidade Tiradentes; seed 20261005) | Index from GeoSampa, 5 Oct 2026 | **Check**: BV LiDAR bias sample | The code that drew the sample was not saved, and the draw cannot be reproduced. Applying the stated rule (tiles wholly inside the district) gives 19 candidates in Itaim Bibi and 29 in Cidade Tiradentes, not the recorded 16 and 15 (checked 20 Oct 2026). Treat the six tiles as a fixed, documented sample, not a verifiable random one |
| `MDS-MDT/` | 236.4 | Six LiDAR 2020 tiles: surface (MDS) and terrain (MDT) LAZ. The 12 ZIPs they came in (236.2 MB, verified identical) were removed on 20 Oct 2026 | Manual GeoSampa portal download by the user, 6 Oct 2026 (no direct URL pattern) | **Check**: BV GHSL÷LiDAR bias (`evaluate_bv_lidar_sample.py`) | |
| `quadricula_folha_mdt_mds_2020.gpkg` | 1.6 | Same LiDAR tile index as a GeoPackage | GeoSampa | **Unused** (the GeoJSON copy is read) | |
| `ghsl_public_2026_09_21/` | 1.1 | GHSL R2023A clips for São Paulo (as for Chicago) | `acquire_ghsl_city_rasters.py`, 21 Sep 2026 | **Model**: BV | CC BY 4.0 |
| `microsoft_buildings_2026_08_13/raw_tiles/` | 233.3 | Three Brazil quadkey tiles, 2,035,929 records, every height `-1` | As for Chicago | **Check**: Brás B1 explanation (Microsoft misses whole blocks). **Pilot** | CDLA-Permissive-2.0 |

### Activity

| Path | MB | Content | Obtained | Use |
|---|---:|---|---|---|
| `overture_2026_08_19/` | 157.4 | Overture 2026-08-19.0, SP bbox + 2 km: `segment/` 423,904 (61.0 MB), `connector/` 452,539 (22.5), `place/` (73.9). SP buildings are in `Edificacoes/` | `acquire_harmonized_overture.py`, 16 Sep 2026 (places 1 Oct); manifests as for Chicago | **Model**: M1, M6, M3, M4, U4 walk network, U6 places. **Index** |
| `osm_2026_10_01/` | 4.8 | 37,934 named OSM objects in the SP bbox | `acquire_osm_places.py` from `shared/osm_geofabrik/sudeste-latest.osm.pbf`, 1 Oct 2026 | **Index**. ODbL |

### SP layers no script reads

All were downloaded manually from GeoSampa at the start of the project (they are in the 10 September manifest). They were collected for the removed families M5 (green space) and U5 (accessibility), and for context. No model, release or check reads them. The large ones were removed on 20 October 2026 (next section). These small ones are kept:

| Folder | Files (MB) |
|---|---|
| `Cadastro e Vias/` | `hierarquia_pedestre.gpkg` (1.5), `subprefeitura_v2.gpkg` (1.5), `area_influencia_metro.gpkg` (0.6), `linha_trem_v2.gpkg` (0.5), `estacao_metro_v2.gpkg`, `estacao_trem_v2.gpkg`, `linha_metro_v4.gpkg` (0.1 each) |
| `Meio Ambiente/` | `pde2014_v_parq_pde_map.gpkg` (0.7). `GEOSAMPA_cadparcs_parque_unidade_conservacao.gpkg` (2.1) is read, but only as a Curio map layer and in a U1 pilot |
| `Planejamento e Zoneamento/` | `pde2014_v_eetr_03_map_v2.gpkg` (2.2), `pde2014_v_zeis_04_map_v2.gpkg` (1.3), `pde_macroarea_lei_18209.gpkg` (1.1), `pde2014_v_zeis_04a_map_v2.gpkg` (0.6) |
| `Socioeconomico/` | `equipamento_feira_livre_v2.gpkg` (0.5), `turismo.gpkg` (0.3), `equipamento_shopping_center.gpkg` (0.2), `equipamento_mercados_municipais_v2.gpkg`, `equipamento_sacoloes_v2.gpkg` (0.1 each) |

## Shared (`shared/`)

| Path | MB | Content | Obtained | Use | Notes |
|---|---:|---|---|---|---|
| `osm_geofabrik/` | 1,220.3 | Geofabrik extracts `illinois-latest.osm.pbf` (360.4; Last-Modified 1 Oct 2026) and `sudeste-latest.osm.pbf` (859.8; 30 Sep 2026), with the publisher's `.md5` files | Manual, `download.geofabrik.de`, 1 Oct 2026 (`acquire_osm_places.py` then read them and recorded URL, Last-Modified, md5 and SHA-256 in the `osm_2026_10_01` manifests) | Source of both OSM place extracts (**Index**). **Check**: Brás B1 explanation (OSM building lineage). **Pilot**: U1 alternatives audit | ODbL. "latest" files are replaced daily, so this snapshot cannot be downloaded again |
| `ghsl_public_2026_09_21/` | 334.0 | GHSL R2023A source tiles: ANBH and AGBH 2018 height, BUILT-V 2020 volume; tiles R4_C11, R5_C11 (Chicago) and R12_C14 (SP); `copyright.txt`; one `.source.json` receipt per file (URL, retrieval time, HTTP Last-Modified, SHA-256) | `acquire_ghsl_city_rasters.py` from `https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/`, 21 Sep 2026 | Source of the city clips (**Model**: BV). **Pilot**: harmonized GHSL; one boundary cell recovered from these originals | CC BY 4.0, © European Union. Report: `results/SP_CHI/ghsl_public_2026_09_21/` |
| `jobs_docs/` | 2.5 | LODES 8.4 technical documentation, OnTheMap overview, São Paulo city RAIS tables (2022 establishments; districts 2011–2024), OD 2023 trip tables; `.txt` extractions | Manual, 5 Oct 2026; URLs and SHA-256 in `results/SP_CHI/u2_source_audit_2026_10_05/README.md` | **Check**: U2 source audit, RAIS total check | |
| `ptal_method/` | 6.6 | TfL *Connectivity Assessment Guide* (2015), with a text extraction | Manual, London Datastore PTAL dataset, 5 Oct 2026; SHA `aafbbe1c…` | U4 method source; `harmonization/ptal.py` reproduces its figure 2.15 | |

## Removed on 20 October 2026

These files were removed to free disk space, with the user's approval. Their SHA-256 values stay in `SHA256SUMS`, so a re-obtained copy can be checked against what was used.

| Path | MB | Why it could go | To get it back |
|---|---:|---|---|
| `SP/MDS-MDT/*.zip` (12 files) | 236.2 | Byte-identical to the `.laz` files kept beside them | GeoSampa portal, same six tiles |
| `Chicago/cmap_mdt_2024_25/MyDailyTravel_2024_2025Phase1.zip`, `mdt_2024_25/` | 221.3 | Nested extractions of `TravelSurveys_PublicData_CMAP.zip`, which is kept | Unzip the kept archive |
| `Chicago/manual_acquisition_2026_09_21/cook_chicago_pin_scope.csv` | 23.0 | Byte-identical to the member of `cook_chicago_pin_scope.zip`, which is kept | Unzip the kept ZIP |
| `SP/Cadastro e Vias/SIRGAS_SHP_calcada/` | 654.5 | Unused (sidewalks) | GeoSampa |
| `SP/Meio Ambiente/SIRGAS_GPKG_VEGETACAO_SIGNIFICATIVA.gpkg` | 638.7 | Unused (significant vegetation) | GeoSampa |
| `Chicago/chicagosidewalks/` | 202.6 | Unused (2012 draft sidewalks) | City data portal |
| `SP/Planejamento e Zoneamento/perimetro_zona_lei_18177_24.gpkg`, `zoneamento_2016_map1.gpkg` | 146.5 | Unused (zoning) | GeoSampa |
| `SP/Cadastro e Vias/auditoria_calcadas_bras.gpkg` | 41.6 | Unused; read only by an archived v2 audit | Byte-identical copies in the `auditoriaBras` repository (`github.com/Renzo-Filho/auditoriaBras`, commit `81769e0`) and in `~/Documents/auditoriaCalcadas/` |
| `Chicago/Boundaries_-_Zoning_Districts_(current)_20260915.geojson` | 39.8 | Unused (zoning) | City data portal (current version only) |
| `SP/Socioeconomico/indice_paulista_vulnerabilidadesocial.gpkg` | 24.5 | Unused; read only by an archived v2 audit | GeoSampa |
| `SP/Cadastro e Vias/linha_onibus.gpkg`, `ponto_onibus.gpkg` | 26.6 | Unused (the GTFS feed is used instead) | GeoSampa |
| `Chicago/Building_Permits_20260915.geojson` | 2,965.6 | Read only by `scan_chicago_floor_fields.py`, the B2/B3 floor-field search (families refused) | City data portal; a new download will differ (live table) |
| `Chicago/microsoft_buildings_2026_08_13/` | 230.0 | Read only by the Chicago half of the Microsoft footprint pilot | Microsoft `dataset-links.csv`, quadkeys in `results/SP_CHI/microsoft_footprints_2026_09_22_review/selected_tiles.csv` |

**Effect on reruns:**
- No model, model input table or acceptance check reads any of these files.
- `prepare_sp_v3.py` fingerprints the whole `SP/` tree. That fingerprint already stopped matching when folders were added after 10 September, so the frozen run already refuses a rerun under its run ID.
- `prepare_chicago.py` re-hashes `Chicago/` but does not compare against earlier hashes.

**Removed outside this folder the same day:**
- `analysis/cache/overture_sp/buildings_2026-08-19.0_bbox.parquet` and `duckdb_extensions/` (0.78 GB). These were regenerable, and the delivered SP buildings GeoPackage is unchanged.
- The two Cook 2022 LAS tiles in `analysis/work/chicago_m3_lidar_point_pilot_2026_09_26/` (2.30 GB). See `analysis/work/README.md` for their hashes and how to re-fetch them.

## Provenance gaps and reuse terms

**Not recorded.** These should be stated as such in any paper:
- **Download dates.** The SP layers and `IPTU_2026.csv` were downloaded manually from GeoSampa, but the download dates were not written down. Only the file dates on disk are known. Their content hashes have been frozen since 10 September 2026.
- **Extracted copies only.** TIGER 2022 blocks, LODES 2022 and the CTA GTFS were supplied already extracted, so the original archive checksums are unknown.
- **Business licences.** The query text behind the two licence extracts was not saved, and the full licence export is truncated (see its row).
- **LiDAR sample.** The code that drew the six sample tiles was not saved, and the draw cannot be reproduced (see the `geosampa_lidar_2020/` row).
- **Unresolved provenance.** `chicago_acs_community_areas.csv` has unknown provenance; no model uses it.

**Cannot be downloaded again identically:**
- CTA GTFS and SPTrans GTFS (the publishers serve only the current feed).
- Geofabrik "latest" extracts.
- Live City of Chicago and Cook County tables.
- The GeoSampa WFS layers.
- Overture 2026-08-19.0, once it leaves S3.

Deleting any of these loses the exact input. `SHA256SUMS` can still prove what was used.

**Reuse terms recorded with the data:**

| Source | Terms |
|---|---|
| OSM, Overture roads | ODbL |
| Overture places | CDLA-Permissive-2.0 / Apache-2.0 |
| Microsoft footprints | CDLA-Permissive-2.0 |
| GHSL | CC BY 4.0 |
| CTA GTFS | CTA developer agreement (`google_transit/developers_license_agreement.htm`) |
| DuPage parcels | The county terms prohibit redistributing the real-estate layer (`chicago_cadastral_2026_09_18/documentation/dupage_publisher_terms.json`). Publish only derived aggregates, after checking those terms |

No licence was recorded for the other sources. Check before redistributing any raw file.

## Adding data

- Put each new download in `<city>/<source>_<YYYY_MM_DD>/`, with the URL, query, date, row counts and SHA-256 in a `manifest.json` (the Overture and cadastral manifests are the model).
- Add a row to this register.
- Append the new hashes to `SHA256SUMS`:

  ```bash
  cd analysis/data && sha256sum <new files> >> SHA256SUMS
  ```

- Never edit or overwrite a file that a frozen release hashed. Download into a new dated folder instead.
