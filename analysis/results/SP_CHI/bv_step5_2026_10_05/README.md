# BV vertical form (Step 5)

> **Correction (6 October 2026):** a like-for-like LiDAR comparison ([lidar_sample](lidar_sample/README.md)) shows that GHSL is **not** 1.6–2 times too high in São Paulo. With the same per-building statistic as Chicago, São Paulo's GHSL ÷ LiDAR ratios are about 10–15% above Chicago's within each height class, and GHSL inflates low and compresses tall buildings in both cities. The municipal references below (GeoSampa 2007/2014 heights, IPTU floors) understate LiDAR building height; the readings that rely on them are superseded.

Run 5 October 2026. Scripts: `analysis/scripts/evaluate_bv_step5.py`, `analysis/scripts/audit_sp_height_references.py`. Decisions S5-1 to S5-7 fixed by the user before the run ([MODEL_PLAN Step 5](../../../../docs/chicago/MODEL_PLAN.md#step-5--bv-vertical-form-and-the-bi-question)). **BV was accepted with stated limits for Chicago later on 5 October 2026;** the cross-city LiDAR follow-up and its limits are recorded separately.

## Definition (S5-1)

`bv_height_built_m` = GHSL R2023A built-surface-weighted building height on land: Σ(cell∩land weight × AGBH) ÷ Σ(weight × AGBH/ANBH), native 100 m cells, height epoch 2018. Equivalent to Σ volume ÷ Σ built surface. Land support changes nothing material (Spearman with the earlier gross-support values 0.99992 / 0.99997).

## Results

| Check | Rule | Chicago | São Paulo |
|---|---|---|---|
| **S5-5 / S5-6 GHSL vs reference height** (footprint-area-weighted, buildings by centroid) | Spearman ≥ 0.80 | **pass**: vs Cook 2022 LiDAR 0.852; GHSL ÷ LiDAR median 0.95 | **fail**: vs GeoSampa photogrammetric heights (2007/2014) 0.788; GHSL ÷ GeoSampa median **2.12** |
| S5-7 GHSL ÷ reference by reference height class | descriptive | < 8 m 1.11 (20 areas); 8–15 m 0.92 (45); 15–25 m 0.83 (8); ≥ 25 m **0.585** (4) | < 8 m 2.14 (79); 8–15 m 1.95 (13); 15–25 m 1.52 (4) |
| Median BV | — | 9.76 m (Loop 41.99 m highest; Riverdale 6.55 m lowest) | 13.40 m (República 31.25 m; Marsilac 2.98 m) |
| Overlap with B1 (Spearman) | — | 0.349 (frozen BV 0.537) | 0.130 (frozen BV 0.511) |
| **S5-2 BI identity** | — | BI vs BV × built fraction **0.99992** | **0.99995** |

**Third São Paulo reference (IPTU 2026 floors, weighted by occupied area, once per physical lot):**

| Height source | Spearman with IPTU floors | Implied metres per floor (median) |
|---|---:|---:|
| GeoSampa photogrammetric (2007/2014) | 0.925 | 2.39 |
| Overture / OpenStreetMap | 0.755 | 2.77 |
| **GHSL BV** | 0.813 | **4.92** |

GeoSampa tower check: Edifício Itália 125.3 m and Copan 118.4 m in GeoSampa (commonly cited heights 165 m and 115 m, not verified here); GeoSampa is plausible for towers.

## Reading

- **Chicago:** GHSL ranks areas like the LiDAR and is about right in level, but compresses tall areas (≥ 25 m class at 0.59 of LiDAR; Loop 42 m).
- **São Paulo:** GHSL ranks districts less well than in Chicago and is **about 1.6–2 times too high in level** against two municipal references (floors × typical storey height; photogrammetric height). The cause is not established (GHSL height is regressed from global elevation models and Sentinel-2; terrain and canopy effects are plausible but untested).
- **Cross-city consequence:** with GHSL in both cities, São Paulo would appear much taller relative to Chicago than it is. Absolute BV levels are not comparable across the two cities.
- **BI** is numerically the product of BV and the GHSL built fraction (Spearman 0.9999 in both cities); S5-2 (no separate family) is confirmed.

## Files

`bv_step5_by_unit.csv` (GHSL variants, BI, P90, references per unit), `sp_iptu_floors.csv`, `checks.json`.
