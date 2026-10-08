# BV: GHSL height vs LiDAR building height, same method in both cities

Run 6 October 2026 by `analysis/scripts/evaluate_bv_lidar_sample.py` (`p95` default; `max` sensitivity in `../lidar_sample_max/`). Follows the Step 5 failure in São Paulo (S5-6) as pre-registered in S5-7. Descriptive; no pass/fail rule.

**Data.** São Paulo: GeoSampa LiDAR 2020 (Fototerra, 1:1,000), six tiles drawn at random wholly inside three districts (`analysis/data/SP/geosampa_lidar_2020/sample_tiles.csv`, seed 20261005): Brás 3323-111, 3321-344; Itaim Bibi 3316-312, 3315-262; Cidade Tiradentes 4316-223, 4316-242. Files `analysis/data/SP/MDS-MDT/` (downloaded manually from the GeoSampa portal by the user, 6 October 2026); MDS point clouds classified (class 6 building), MDT ground points (class 8); SHA-256 in `summary.json`. Chicago: Cook County 2022 building footprints with `Height` (maximum point minus ground, US feet).

**Method.** For each GHSL 100 m cell (wholly inside a sample tile in São Paulo; inside the city in Chicago): footprint-area-weighted building height of footprints whose centroid is in the cell, compared with GHSL ANBH 2018 of that cell. São Paulo building height = height above the MDT terrain of class-6 points inside each Overture footprint (at least 5 points), 95th percentile (`p95`) or maximum (`max`, identical in kind to Cook's `Height`). Cells with at least 500 m² of footprint and ANBH > 0.

## Results: GHSL ÷ LiDAR, median per cell

| | Chicago (40,471 cells) | São Paulo `max` (88 cells) | São Paulo `p95` (88 cells) |
|---|---:|---:|---:|
| All cells | 1.151 | 1.084 | 1.232 |
| LiDAR height < 8 m | 1.267 | 1.465 | 1.577 |
| 8–15 m | 1.045 | 1.167 | 1.206 |
| 15–25 m | 0.716 | 0.806 | 0.931 |
| ≥ 25 m | 0.528 | 0.654 | 0.626 |
| Cell-level Spearman | 0.695 | — | 0.538 |

São Paulo districts (`p95`): Brás 1.13, Itaim Bibi 1.35, Cidade Tiradentes 1.51 (low-rise cells dominate there).

## Reading

- **GHSL behaves the same way in both cities:** it inflates low buildings and compresses tall ones.
- **With the same statistic as Chicago (`max`), São Paulo's ratios are about 10–15% higher than Chicago's within each height class;** the overall median is lower (1.08 vs 1.15) because the sample's height mix differs.
- **This corrects the 5 October reading** (`../README.md`) that GHSL is about 1.6–2 times too high in São Paulo. That figure came from GeoSampa photogrammetric heights (2007/2014) and IPTU floors × a storey height; against LiDAR 2020 those references understate building height. The LiDAR comparison is the like-for-like test.
- Limits: 88 cells in three districts; LiDAR 2020 (São Paulo) vs 2022 (Chicago) vs GHSL 2018; Overture footprints (2026) used to group São Paulo points.
