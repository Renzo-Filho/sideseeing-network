# BV variants, GHSL built fraction and Chicago LiDAR footprint check — 30 September 2026

Exploratory evaluation, not a model input and not an acceptance of any family. Reads only existing sealed inputs; H1–H3 outputs are untouched. Script: `analysis/scripts/evaluate_bv_built_form_2026_09_30.py` (run with this folder's `tables/` as argv[1]; log in `run_log.txt`).

## What was computed

**GHSL at native 100 m cells, all 173 units, gross support** (whole-cell overlap weights, cells valid in ANBH, AGBH and volume; minimum valid fraction 1.0). From the GHSL Data Package 2023 §2.2.1 (`ANBH = BUVOL/BUSURF`, `AGBH = BUVOL/S`, `AGBH/ANBH = BUSURF/S`), per cell:

| Variable | Definition here |
|---|---|
| `anbh_mean_incl_zero` | Land-overlap-weighted mean of ANBH including zero cells (the sealed candidate `net_grid_height_gross`) |
| `agbh_mean`, `volume_density_m` | Same for AGBH and for volume ÷ cell area (equal by identity; metres of built volume per m² of ground) |
| `ghsl_built_fraction` | Weighted mean of `AGBH/ANBH` (0 where ANBH = 0): GHSL's implied built-surface fraction. **Derived from the documented identity, not read from the GHS-BUILT-S raster** |
| `height_built_weighted` | Σ(w·AGBH) / Σ(w·AGBH/ANBH), i.e. district built volume ÷ district built surface: mean height *of built surface* |
| `anbh_p50_built`, `anbh_p90_built` | Quantiles of cell ANBH weighted by built surface |

Reconciliation with the sealed H1–H3 gross values: maximum absolute difference 3.8e-9 (Chicago) and 2.7e-6 (SP). No cell has AGBH > 0 with ANBH = 0.

**Chicago Cook County 2022 footprints (779,962 buildings):** `Height` is in **US feet** (source metadata: `heightUnit: us-foot`, NAVD88; `Height = Max_Point − Ground_Z`, ground elevations ~598 ft), converted × 0.3048006. Buildings assigned to Community Areas by centroid (not clipped), EPSG:26916, gross support. Height is the highest LiDAR point, so it overstates mean roof height on pitched roofs; LiDAR "volume" = footprint × max height is an upper-biased proxy, not measured volume.

## Results (Spearman rank correlations across units; ratios are medians unless noted)

| Pair | Chicago (77) | SP (96) |
|---|---|---|
| Overture B1 gross vs `anbh_mean_incl_zero` | 0.524 | 0.515 |
| Overture B1 gross vs volume density | 0.741 | 0.670 |
| Overture B1 gross vs **GHSL built fraction** | **0.862** | **0.905** |
| Overture B1 gross vs `height_built_weighted` | 0.330 | 0.132 |
| `anbh_mean_incl_zero` vs `height_built_weighted` | 0.933 | 0.822 |
| Height (built-weighted) vs volume density | 0.807 | 0.738 |
| Share of support area with ANBH = 0 | median 0.9%, max 37.8% | median 0.6%, max 87.7% |
| GHSL built fraction ÷ Overture B1 gross | 1.37 (range 0.91–2.93) | 1.07 (range 0.72–1.54) |

Chicago only, against Cook 2022 LiDAR footprints (Spearman): Overture B1 gross vs Cook footprint coverage **0.986** (Cook ÷ Overture median 1.09, range 0.97–1.22); GHSL volume density vs footprint × max height **0.925** (GHSL ÷ LiDAR median 1.22, range 0.40–1.78; lowest in the Loop, CHI:32, 0.40); `height_built_weighted` vs LiDAR area-weighted height 0.852 (level ratio median 0.95, range 0.41–1.30; Loop 41.6 m vs 92.9 m).

Brás (SP:10) gross B1 from Overture 0.566; GHSL built fraction 0.444; Microsoft land coverage 0.205 (pilot table). Itaim Bibi (SP:35): Overture 0.253, GHSL 0.389, Microsoft 0.338.

## Caveats

- GHSL is modeled (Sentinel-2/DEM regression, 2018 height, 2020 volume); the Data Package reports ANBH MAE 1.97 m and RMSE 3.55 m against Copernicus Urban Atlas 2012 in 38 **European** urban areas only. No US or Brazilian validation is cited there.
- Agreement between Overture and GHSL built fraction is a consistency check, not ground truth; GHSL is systematically higher in Chicago (ratio 1.37).
- Cook 2022 assignment is by centroid; Cook footprints include ancillary structures.
- Nothing here sets acceptance thresholds; none were pre-registered.

## Addendum — B3 comparison tables (30 September 2026)

Computed ad hoc from the tables above (not by the script) and saved for the `BI` proposal:

- `tables/sp_ghsl_vs_cadastral_b2_b3.csv`: SP GHSL variants joined to `analysis/results/SP/tables/attributes_primary.csv`. Spearman with cadastral B3 (`cadastral_floor_area_density`): volume density 0.901, ANBH mean incl. zero 0.917, built-weighted height 0.719, Overture B1 0.635. Volume density ÷ B3: median 8.48, range 3.78–97.81.
- `tables/chicago_ghsl_vs_energy_usage_2010.csv`: Energy Usage 2010 (`8yq3-m6wp`, live API) sum of max(`kwh_total_sqft`, `therms_total_sqft`) per Community Area (name-matched, 77/77) × 0.09290304 ÷ gross area. Spearman: GHSL volume density 0.891, Cook LiDAR volume 0.931, Overture B1 0.794.
