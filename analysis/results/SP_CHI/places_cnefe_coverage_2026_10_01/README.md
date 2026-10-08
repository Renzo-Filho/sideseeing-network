# Places coverage of CNEFE establishment addresses — 1 October 2026

Protocol **P-PLACES-1**, fixed in [SIMPLE_INDEX.md](../../../../docs/SIMPLE_INDEX.md) before this run. Compares Overture Places with OpenStreetMap as the source of the "commercial establishments" factor. **No index was built.**

```bash
.venv/bin/python analysis/scripts/acquire_osm_places.py Chicago   # Geofabrik illinois-latest, HTTP Last-Modified 2026-10-01 08:25:53 GMT
.venv/bin/python analysis/scripts/acquire_osm_places.py SP        # Geofabrik sudeste-latest, HTTP Last-Modified 2026-09-30 23:15:43 GMT
.venv/bin/python analysis/scripts/evaluate_places_against_cnefe.py
```

Run: 1 min 40 s, peak 2.2 GB (`run_log.txt`). Hashes of code and inputs in `summary.json`. Both Geofabrik files passed their published MD5. An earlier attempt through public Overpass servers failed with repeated 504 time-outs and was abandoned (`overpass_attempt_abandoned.log`); none of its data is used.

## Inputs after the protocol filters

| | Overture Places (named, not `geographic_entities`) | OpenStreetMap (named; shop/amenity/office/craft/healthcare/tourism; street-furniture amenities excluded) |
|---|---:|---:|
| São Paulo, in city | 445,419 | 24,545 |
| Chicago, in city | 143,229 | 19,856 |

Reference (São Paulo only): 600,253 CNEFE 2022 records of `COD_ESPECIE` 4, 5, 6, 8 with address-level coordinates (education 9,978; health 10,598; other purposes 564,093; religious 15,584). Excluded for coarse coordinates: 6,431 at block-face level, 1 at locality level, 31 at sector level.

## Results, São Paulo (`coverage_citywide.csv`, `coverage_by_district.csv`, `district_spread.csv`)

Share of CNEFE establishment addresses with a matching record. "Chance" is the same rule applied after moving every reference point 500 m in a random direction.

| Match | Overture observed | Overture chance | OSM observed | OSM chance |
|---|---:|---:|---:|---:|
| Name within 25 m | 15.07% | 0.56% | 1.41% | 0.03% |
| **Name within 50 m (primary)** | **20.10%** | **2.04%** | **2.35%** | **0.13%** |
| Name within 100 m | 26.59% | 6.78% | 3.30% | 0.49% |
| Any record within 25 m | 75.66% | 41.01% | 10.50% | 5.32% |
| Any record within 50 m | 92.39% | 74.30% | 23.40% | 14.65% |
| Any record within 100 m | 98.87% | 91.53% | 42.75% | 33.15% |

Proximity alone is mostly chance for Overture: at 50 m, 74.30 of the 92.39 points are matched by a randomly displaced point too. Name matching is far less sensitive to chance, which is why it is the primary measure.

By use type, name within 50 m: Overture education 46.14%, health 34.87%, religious 29.18%, other purposes 19.11%; OSM 10.83%, 4.44%, 2.86%, 2.15%.

**Unevenness across the 96 districts** (name within 50 m, observed minus chance): Overture 3.20% to 35.16%, median 18.08%; OSM 0.22% to 13.41%, median 1.64%. Spearman correlation of that excess with district CNEFE establishment density: 0.319 (Overture), 0.310 (OSM). Brás (SP:10): Overture 29.35% (chance 7.06%), OSM 6.59% (chance 0.80%).

## Agreement between the sources (`source_agreement.csv`, `records_by_unit.csv`)

Share of one source's records with a name match in the other within 50 m. Agreement is not completeness.

| | OSM records found in Overture | Overture records found in OSM |
|---|---:|---:|
| São Paulo | 14,525 of 24,545 (59.18%) | 17,923 of 445,419 (4.02%) |
| Chicago | 14,993 of 19,856 (75.51%) | 17,381 of 143,229 (12.14%) |

OSM-to-Overture record ratio per unit: São Paulo 0.011 to 0.279; Chicago 0.051 to 0.339.

## Limits

- CNEFE names are enumerator free text and often describe the type of business rather than its trade name (IBGE notes n. 04); absolute name-match rates are therefore low for every source. The comparison between sources uses the identical rule and reference, so the ratio between them is the informative result.
- CNEFE is 2022; both candidate sources are 2026. Establishments that opened or closed in between lower the rates of both.
- CNEFE address coverage is a validation of São Paulo only. No reference exists for Chicago, so the Chicago rows describe agreement, not completeness.
- Way locations in OSM are the mean of their node coordinates; OSM relations are not used.
