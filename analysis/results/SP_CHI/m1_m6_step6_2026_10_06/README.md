# M1 street density and M6 street hierarchy (Step 6)

Run 6 October 2026 by `analysis/scripts/evaluate_m1_m6_step6.py` (8 min). Decisions S6-1 to S6-7 fixed by the user before the run ([MODEL_PLAN Step 6](../../../../docs/chicago/MODEL_PLAN.md#step-6--m1-street-density-and-m6-street-hierarchy)). **M1 and M6 were accepted with stated limits later on 6 October 2026.**

## Definitions

- `m1_km_per_km2` = Overture 2026-08-19.0 road length in ten classes (`motorway`, `trunk`, `primary`, `secondary`, `tertiary`, `residential`, `living_street`, `pedestrian`, `unclassified`, `unknown`; links and both carriageways kept), clipped exactly to each unit's land, ÷ land km² (C2).
- `m6_major_share` = share of that length in `motorway`, `trunk`, `primary`, `secondary`. Sensitivity: `m6_tertiary_share`, `m6_local_share`; all ten shares reported.

## Validation (S6-6)

| Rule | Chicago | São Paulo |
|---|---|---|
| M1 vs municipal street length per land km², Spearman ≥ 0.95 | **pass** 0.958 (city centerlines, status N, classes 1–4, 7, 9) | **pass** 0.975 (`logradouro`) |
| Overture ÷ municipal length, median | 1.018 | 0.936 |
| Areas outside 0.80–1.25 (returned) | **O'Hare 2.19** | **Marsilac 0.61, Parque do Carmo 0.76** |
| M6 major share vs municipal major share, Spearman ≥ 0.80 | **pass** 0.815 (classes 1–3, 9) | **pass** 0.828 (`classvias` arterial, coletora, rodovia, VTR) |
| Median major share, Overture / municipal | 0.222 / 0.272 | 0.185 / 0.337 (municipal "major" includes collectors) |

Three `logradouro` lines had one NaN vertex mid-line; the vertex was dropped and the line kept.

## Values and overlap (S6-7, descriptive)

| | Chicago | São Paulo |
|---|---|---|
| M1 median (km per km² of land) | 13.2 | 17.8 |
| Highest / lowest | Armour Square 22.9 / O'Hare 3.9 | República 27.4 / Marsilac 0.87 |
| M6 median major share | 0.222 | 0.185 |
| Spearman M1 with U3 / B1 | 0.386 / 0.391 | 0.669 / 0.724 |
| Spearman M6 with M1 | 0.262 | 0.042 |
| Median share of links / one-way / TomTom | 1.8% / 51.0% / 1.3% | 1.6% / 26.5% / 1.7% |
| Highest TomTom share | O'Hare 5.3% | Jaguaré 7.0% |

## Returned cases

- **O'Hare (CHI:76), Overture 2.19 × city file:** the city filter excludes class 99 (airfield circulation); Overture tags some airport roads with eligible classes. O'Hare is still the lowest-M1 area.
- **Marsilac (SP:52), 0.61:** rural roads missing from Overture (known since the M1/M6 review).
- **Parque do Carmo (SP:57), 0.76:** large park and environmental land; cause not examined.

## Files

`m1_m6_by_unit.csv` (all metrics and municipal comparisons per unit), `checks.json`, `source_register.json`.
