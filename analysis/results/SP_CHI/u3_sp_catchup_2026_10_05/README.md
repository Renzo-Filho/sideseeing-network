# São Paulo U3 catch-up: Census 2022 residents per km² of land

Run 5 October 2026 by `analysis/scripts/evaluate_sp_u3_catchup.py` (decision S3-0). Same estimand as Chicago U3 ([chicago_u3_step1](../../Chicago/chicago_u3_step1_2026_10_02/README.md)); kept for the common-model stage, not part of the Chicago contract.

**Definition:** `u3_land_km2` = Census 2022 residents (GeoSampa `densidade_demografica.gpkg`, 27,301 tracts) allocated to the 96 districts by tract area share ÷ district land (`land_area_m2`, area minus water, sp_prep v3).

| Check | Result |
|---|---|
| Residents assigned to districts | 11,446,054.47 of 11,451,999; 5,944.5 lie in tract parts outside the district boundary (same shortfall accepted for U4) |
| Equals the sp_prep v3 district allocation | max difference 1.5 × 10⁻¹¹ |
| Equals the U4 resident weights | pass |
| Gross-area sensitivity | Spearman 0.9993; 1 district moves 5 or more ranks |

**Values:** median 11,111 residents per km² of land; República 26,064 highest; Marsilac 55 lowest; Brás 10,690 (52nd).

**Cross-city caveat:** São Paulo uses a 2022 census count; Chicago U3 uses the ACS 2020–2024 pooled estimate. Instrument and vintage differ and are disclosed.

Files: `tables/u3_sp.csv|parquet`, `checks.json`.
