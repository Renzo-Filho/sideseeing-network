# Bounded 2022 LiDAR test for Chicago M3/M4 motorway candidates

**Finding:** 3D elevation is useful supporting evidence, especially for distinguishing built frontage blocks from many freeway slivers. It does not independently define a legal/public street block or safely classify every candidate. This is a targeted diagnostic in one CHI:11 motorway core, not an M3/M4 acceptance test.

**Follow-up:** The [classified 2022 point-cloud pilot](../chicago_m3_lidar_point_pilot_2026_09_26/README.md) shows that the two high-height slivers have vegetation rather than building-class returns. It also detects a road-surface trace at the West Veterans Place county-mask gap and a bridge deck above local ground. Those findings improve triage but do not certify M3/M4.

## Source and method

The [Illinois State Geological Survey](https://clearinghouse.isgs.illinois.edu/lidar-county) publishes 2022 Cook and DuPage classified LiDAR, digital terrain models (DTM), and digital surface models (DSM). The [Cook DTM service](https://data.isgs.illinois.edu/arcgis/rest/services/Elevation/IL_Cook_DTM_2022/ImageServer) and [Cook DSM service](https://data.isgs.illinois.edu/arcgis/rest/services/Elevation/IL_Cook_DSM_2022/ImageServer) yielded 600 × 600 m clips around the previously frozen CHI:11 motorway zone, exported at 0.5 m raster spacing in EPSG:26916. The services report NAVD88 vertical units in US survey feet. We converted `DSM − DTM` to metres and calculated the share of each saved candidate face more than 2.5 m above terrain. The raster clips and source metadata remain in the ignored `analysis/work/chicago_m3_lidar_motorway_pilot_2026_09_26/`; [summary.json](summary.json) records URLs, parameters, footprints and SHA-256 hashes. Candidate geometry was not redrawn after viewing LiDAR.

## Observations

| Frozen candidate group | Count | Fraction with DSM−DTM > 2.5 m |
|---|---:|---:|
| Five visually built residential faces | 5 | 0.383–0.450; median 0.417 |
| Thirteen small motorway slivers | 13 | 0–0.502; median 0.010 |

The narrow built frontage wedge (candidate 72), which a 30% motorway-exposure deletion would lose, has **0.383** above-ground fraction. This confirms a structural signal that helps preserve it for review. But motorway slivers 56 and 71 have **0.368** and **0.502** above-ground fraction: vegetation or elevated structures can create the same signal. A 0.30 height-fraction rule would retain all five built faces and incorrectly retain at least two of the 13 slivers. It also says nothing about legitimate open-space blocks, which can be flat. The [candidate-level table](candidate_height_support.csv) and [overlay](ndsm_candidate_overlay.png) show every value and location.

## Method decision

Use the 2022 DTM/DSM difference as a **reason-coded review feature**, alongside ROW/road edges, public-road status, ortho imagery, building footprints and motorway context. It is especially useful for spotting built land inside a high-motorway-exposure candidate and for checking terrain/structure at grade-separated crossings. A bare-earth DTM alone removes buildings and bridges, and `DSM−DTM` cannot distinguish trees from buildings or bridge decks without classified returns or other labels. Flat asphalt, landscaped medians, parks, parking lots and vacant true blocks can all have low height.

The next point-cloud pilot should extract only small tiles over (a) a true built frontage wedge, (b) a tree-covered false island, (c) a flat median, (d) an elevated crossing, and (e) a missing ordinary street such as West Veterans Place. Audit delivered point classes and vertical profiles against orthophotos and ROW. The [Cook acquisition contract](https://opendocs.cookcountyil.gov/procurement/contracts/2103-08021.pdf) specifies road-surface class 11 using existing edge-of-pavement planimetry, so class 11 may share omissions with that source; verify the delivered metadata and point cloud before treating it as independent confirmation. Compare a frozen 2D baseline with 2D+3D *review/repair* on complete, independently adjudicated zones. Score false blocks removed, true blocks wrongly removed, missing street splits, and boundary/shape error. The citywide Cook LAS distribution is in multi-hundred-GB parts; this pilot deliberately used two small public raster exports.

The source years also matter: 2022 elevation and the pilot's 2025 orthophoto can disagree where roads or buildings changed. LiDAR supplies physical surface evidence, while cadastral ROW and public-street records supply legal/status evidence. M3/M4 remain unaccepted.

## Reproduce

```bash
MPLCONFIGDIR=/tmp/mpl-m3-lidar .venv/bin/python analysis/scripts/pilot_chicago_m3_lidar_motorway_2026_09_26.py
```

The script reuses the cached rasters when present, validates matching CRS/grid, and regenerates `candidate_height_support.csv`, `ndsm_candidate_overlay.png`, and `summary.json` from the frozen CHI:11 candidate inventory. Initial raster acquisition requires access to the public ISGS image services.
