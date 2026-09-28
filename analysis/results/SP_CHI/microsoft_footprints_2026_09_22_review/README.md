# Microsoft Global ML Building Footprints: bounded paired-source review

**Current decision:** retain the existing matched Overture B1 candidate. Microsoft's 2026-08-13 release has now been organized and tested in eight paired city pilots. It remains a footprint-source diagnostic, with large and uneven São Paulo differences. Every selected SP record reports missing height, so this release cannot supply a paired building-height sensitivity. The new data has **not** been accepted for any of the 13 model families. It does not supply cadastral parcels, reported floors or constructed floor area. Earlier prospective statements below describe the pre-acquisition review.

## Local acquisition, organization and paired pilot

The six user-supplied compressed files were matched to the [selected level-9 quadkeys](selected_tiles.csv), including restoration of the missing leading zero in the Chicago filenames. Every gzip stream was read to completion and compared byte for byte to its decompressed `.geojsonl` copy; record counts and source hashes are in [local_file_inventory.json](local_file_inventory.json). Originals were moved under `analysis/data/Chicago/microsoft_buildings_2026_08_13/raw_tiles/` and `analysis/data/SP/microsoft_buildings_2026_08_13/raw_tiles/` with normalized quadkey filenames. The six verified redundant plain copies were deleted; the unrelated `test/predios_sp_raw/` file was left alone. The [organized inventory](organized_inventory.json) records paths, hashes and deletions. The source data remains Git-ignored.

[Paired pilot output](pilot/paired_microsoft_pilot.csv) applies the existing gross and hydrographic land supports and the shared exact tiled-union B1 formula to five Chicago and three SP fixture units. [Tile diagnostics](pilot/tile_diagnostics.json) count source records, missing height/confidence and geometry validity. Four invalid pilot polygons were repaired **only in the projected working copy**; the [repair log](pilot/working_geometry_repairs.json) shows area changes no greater than 0.000002 m². Raw tiles remain unchanged.

| Unit | Microsoft B1 land | Overture B1 land | Difference, percentage points | Microsoft positive height |
|---|---:|---:|---:|---:|
| CHI:24 West Town | 27.89% | 30.13% | −2.24 | 15,421 / 15,422 intersecting buildings |
| CHI:28 Near West Side | 24.51% | 25.82% | −1.31 | 4,483 / 4,491 |
| CHI:30 South Lawndale | 20.65% | 21.52% | −0.87 | 12,654 / 12,655 |
| CHI:32 Loop | 28.67% | 30.49% | −1.82 | 322 / 326 |
| CHI:76 O'Hare | 2.53% | 4.81% | −2.28 | 1,546 / 1,610 |
| SP:10 Brás | 20.46% | 56.58% | −36.12 | 0 / 175 |
| SP:30 Grajaú | 10.47% | 10.52% | −0.04 | 0 / 19,471 |
| SP:35 Itaim Bibi | 34.37% | 25.73% | +8.64 | 0 / 5,054 |

Across **all 2,035,929 records** in the three selected SP tile files, height is exactly `-1`; no feature has positive height. This is a tile-wide observation, not merely a Brás sampling result. Chicago's five pilots have high positive-height coverage by count, but that one-sided information cannot define a common SP–Chicago building-height feature. GHSL BV remains a separate grid statistic. The uneven B1 direction in SP warns against globally replacing the matched Overture input; the differences describe two mapped sources, not which is ground truth. Brás's large gap specifically requires map and local-reference review if Microsoft is reconsidered for B1.

[Independent arithmetic/support validation](pilot/validation.json) passes **52/52 checks**, including union and denominator bounds, reconstruction of land/gross fractions and differences, all-SP height absence, and small working-geometry repairs. These checks do not establish detection accuracy or which source best represents real buildings.

## Source and index evidence

Microsoft's [repository](https://github.com/microsoft/GlobalMLBuildingFootprints) describes imagery-derived footprint polygons under [CDLA Permissive 2.0](https://cdla.dev/permissive-2-0/), EPSG:4326. Its August 13 update advertises 30,340 level-9 tiles across 225 regions. Some features carry neural-network height estimates in metres; `-1` means missing height. Confidence is footprint-detection confidence, with `-1` on older records; it does not measure height accuracy. Imagery vintage varies by source and place, and update/index date is not observation date. Microsoft's published regional evaluation is not a Chicago or São Paulo validation sample. Microsoft's FAQ explicitly warns that some imagery was omitted, producing square coverage gaps.

The user-supplied `/home/renzo/Downloads/dataset-links.csv` is a 6,382,044-byte **link index**, not building features. Its SHA-256 and complete audit are in [links_audit.json](links_audit.json). It has exactly 30,340 unique URLs, one upload date (`2026-08-13`), 225 region labels and five columns: `Location`, `QuadKey`, `Url`, `Size`, `UploadDate`. File extensions are `.csv.gz`, but the repository says the decompressed content is line-delimited GeoJSON.

Level-9 quadkey intersection against the existing 77 Chicago and 96 SP reporting units, with a 1.5 km source buffer, selects [six files](selected_tiles.csv): three `UnitedStates` and three `Brazil` tiles. Two Chicago tiles and all three SP tiles intersect the city directly. The selected tile polygons cover the two complete city supports in the index (`unindexed_city_support_m2=0`), **which says nothing about building detection completeness inside those tiles**. Rounded CSV sizes total approximately 230 MB compressed for Chicago and 233 MB for SP; city clipping would greatly reduce retained features. Those size estimates are not exact byte counts.

The current Chicago Overture parquet has 1,381,239 building rows, of which **373,434 cite `Microsoft ML Buildings`** in source lineage. It already has positive `height` on 1,258,170 rows and positive `num_floors` on 429,594 rows. SP's frozen Overture GeoPackage has 7,278,768 building rows, of which **869,479 cite Microsoft ML Buildings**; 2,090,405 have positive height and 21,250 have positive floor counts. These are attribute-presence counts, not verified building/floor accuracy or complete stock coverage. The Overture height sources in Chicago include USGS Lidar. Thus Microsoft is partly upstream of existing candidates **in both cities** and cannot be treated as independent ground truth. The August Microsoft tile release may still contain changed or additional geometries; polygon comparison is required.

## How this affects the plan

| Family | Potential contribution | Required gate before use |
|---|---|---|
| B1 | Paired alternate footprint union/land-coverage measure; the eight-pilot comparison reveals uneven source differences, especially in SP. | Keep Overture primary. An expanded Microsoft sensitivity needs map/local-reference review before any source choice, with identical union/land formulas on both sides. |
| BV supplemental | Microsoft building-level height is unavailable for SP in these files. | Do not form a paired Microsoft height feature. Retain GHSL BV under its separate grid definition. |
| M7, B2, B3 | No direct resolution. | Footprints are not legal cadastral entities; metres of height are not reported floors; footprint area or footprint × height is not fiscal constructed floor area. |
| Other families | No direct method change. | M2/M3/M4 roads/blocks and U1/U2 functional gates remain. |

The completed paired pilot does **not** support replacing the current B1 input or fitting a model now. Comparing an Overture candidate that includes Microsoft lineage with Microsoft polygons measures release differences, but cannot independently prove completeness. Local footprint and map checks remain necessary.

## Reproduction and limitation

```bash
.venv/bin/python analysis/scripts/audit_microsoft_building_links.py \
  --links /home/renzo/Downloads/dataset-links.csv \
  --output analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review
```

The source CSV and six source tiles are outside Git and must accompany a transferred workspace. The user supplied the files after direct acquisition from this environment failed. Reproduce the acquisition check with `.venv/bin/python analysis/scripts/verify_microsoft_building_downloads.py --output analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/local_file_inventory.json` **only when the original root folders are present**; the historical verification manifest is retained after their move. Reproduce the pilot with `.venv/bin/python analysis/scripts/pilot_microsoft_buildings.py`. Exact polygon-to-polygon Overture matching and local visual completeness review remain open. The six source tiles and all frozen model artifacts are unchanged.
