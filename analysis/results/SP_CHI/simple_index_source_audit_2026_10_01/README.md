# Simplified-index source audit — 1 October 2026

Checks, from local data only, every source the [simplified composite index](../../../../docs/SIMPLE_INDEX.md) would use. **No index, feature or model was built.** Every number below is in `tables/` or `summary.json` and was produced by one run of:

```bash
.venv/bin/python analysis/scripts/audit_simple_index_sources.py
```

Run: about 3 min, peak memory about 3.6 GB (`run_log.txt`). Input and code SHA-256 are in `summary.json`. Units: 96 São Paulo districts (`sp_prep_2026_09_10_v3/N02/districts.parquet`) and 77 Chicago Community Areas (`chi_local_2026_09_16_v1/districts.parquet`). "In city" means the point (or building bounding-box centre) lies inside the union of the reporting units.

## Results

### Reporting-unit area (`unit_areas.csv`)

| | Units | Land km² min / median / max |
|---|---:|---|
| Chicago | 77 | 1.570 / 7.393 / 34.521 |
| São Paulo | 96 | 2.148 / 9.632 / 206.876 |

### Overture Places, release 2026-08-19.0 (`places_*.csv`)

Fetched for this audit with `acquire_harmonized_overture.py <city> place` (2 km-buffered bounding box): 208,070 Chicago and 642,767 SP records; **143,509** and **446,015** inside the cities.

| | Chicago | São Paulo |
|---|---|---|
| Records crediting Meta (`places_dataset_credit.csv`) | 84,473 (58.86%) | 421,690 (94.55%) |
| Records crediting BrightQuery | 22,615 (15.76%) | 0 |
| Records crediting Microsoft / Foursquare | 19,473 / 14,967 | 10,460 / 11,245 |
| Records crediting `Overture-signals` | 78,551 (54.74%) | 0 |
| `operating_status` | open 89,036; null 50,897; permanently_closed 3,576 | null 446,001; open 14 |
| `confidence` median (P10–P90) | 0.920 (0.206–0.990) | 0.665 (0.264–0.974) |
| No taxonomy | 24,905 (17.35%) | 16,847 (3.78%) |

The source mix, the `operating_status` field and the confidence distribution differ between the cities. `permanently_closed` can be filtered in Chicago but not in São Paulo, where the field is almost always null. Apart from `Overture` and `Overture-signals`, every record credits exactly one provider (those provider counts sum to the in-city totals). The meaning of the `Overture-signals` dataset was not checked.

### IBGE CNEFE 2022, São Paulo (`cnefe_*.csv`)

File `analysis/data/SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv`: 5,689,391 records, 5,649,276 address IDs, no missing coordinates. Definitions are from IBGE *Notas metodológicas n. 04* (CNEFE) and *n. 01* (coordinates), saved in `CNEFE_2022/docs/` (`liv102091.pdf`, `liv102063.pdf`): enumerators walk every census sector, record every address and investigate its use type; "each record represents one use type (espécie) present at the address".

| `COD_ESPECIE` | Records |
|---|---:|
| 1 private dwelling | 4,992,162 |
| 2 collective dwelling | 4,367 |
| 4 education / 5 health / 8 religious | 10,108 / 10,717 / 15,662 |
| 6 other-purpose establishment | 570,229 |
| 7 under construction or renovation | 85,814 |

**Establishment records are not establishment counts.** The notes (p. 17–18) state that an address with several establishments may be recorded once, with `COD_INDICADOR_ESTAB_ENDERECO` = 2 (up to 10), 3 (more than 10) or 4 (unknown number). For use type 6: 551,783 single, 8,332 up to 10, 2,043 more than 10, 8,071 unknown. The smallest establishment count consistent with these codes (1, 2, 11, 2) is 607,062 citywide; no upper bound exists. By district, that lower bound is 1.016 (José Bonifácio, SP:47) to 1.382 (Consolação, SP:26) times the record count, median 1.041; Brás (SP:10) has 8,844 records and at least 11,114 establishments (198 addresses with more than 10).

`COD_DISTRITO` takes 96 values and maps one-to-one onto the 96 districts: in every district at least 95.02% of geocode-level-1 points fall in the modal polygon (`cnefe_district_crosswalk.csv`).

### GTFS (`gtfs_stops_by_mode.csv`)

| Feed | Mode (`route_type`) | Served stops | Distinct parent stations | Median distance to nearest stop of same mode | Share with a same-mode stop within 50 m |
|---|---|---:|---:|---:|---:|
| CTA (Chicago) | 1 subway/metro (`L`) | 298 | 143 | 0.0 m | 1.000 |
| CTA | 3 bus | 10,683 | — | 25.4 m | 0.847 |
| SPTrans (SP) | 1 metro | 109 | not in feed | 865.4 m | 0.128 |
| SPTrans | 2 rail (CPTM) | 104 | not in feed | 1,576.5 m | 0.096 |
| SPTrans | 3 bus | 22,048 | not in feed | 47.4 m | 0.520 |

Chicago `L` platforms come in co-located pairs under 143 parent stations; the SP feed has no parent stations. The CTA feed contains no commuter rail (Metra) or Pace; the SPTrans feed contains metro and CPTM routes but no EMTU.

### Overture building height (`building_height_fill.csv`)

| | Buildings in city | `height` > 0 | Height source |
|---|---:|---:|---|
| Chicago (release 2026-08-19.0) | 832,457 | 749,136 | USGS Lidar 617,576; Microsoft ML Buildings 131,166; OpenStreetMap 394 |
| São Paulo (`sao_paulo_building_morphology.gpkg`, same release, raw Overture height per its metadata) | 3,144,642 | 2,080,386 | OpenStreetMap 2,080,386 |

### Overture road segments (`overture_segments.csv`)

M1 ten classes, segments wholly inside the city: Chicago 52,796 (median 102.1 m, 1,938 distinct names, 25.14 segments per name); São Paulo 189,750 (median 68.4 m, 42,545 names, 3.93 per name).

## Limits

- No completeness of any source is measured here; see the reference assessment in [SIMPLE_INDEX.md](../../../../docs/SIMPLE_INDEX.md).
- Height-source attribution uses the dataset credited for `/properties/height`, otherwise the whole-record dataset.
- CNEFE coordinates are read as SIRGAS 2000 (EPSG:4674).
