# M3 block size, M4 block shape, M7 parcel grain (Step 8)

Run 6 October 2026 by `analysis/scripts/evaluate_m3_m4_m7_step8.py`. Decisions S8-1 to S8-8 were fixed by the user before the run ([MODEL_PLAN Step 8](../../../../docs/chicago/MODEL_PLAN.md#step-8--m3-block-size-m4-block-shape-m7-parcel-grain)).
- Post-hoc diagnostic: `audit_m3_m4_sp_reference.py` → `posthoc_reference_diagnostic.json`.
- Inputs hashed in `source_register.json`; all checks in `checks.json`; table `m3_m4_m7_by_unit.csv`.
- **Accepted with stated limits later on 6 October 2026.** The failed São Paulo municipal-line comparison and the accepted official-block comparison remain documented below.

## Definitions

**Faces.**
- The M1 Overture network (ten road classes; service roads and alleys excluded) is noded and polygonized. Every enclosed piece of land is a face.
- A face keeps its whole land area (water removed) and is never cut by a unit boundary.
- It enters each unit with weight = its land inside that unit.

| Column | Meaning |
|---|---|
| `ov_m3_wmedian_ln_m2` | **M3:** area-weighted median of ln(face land area), the size of the block in which a typical m² of land sits |
| `ov_m4_wmedian_compactness` | **M4:** area-weighted median of 4π·A/P² on the face's exterior ring (a 2:1 rectangle gives 0.698) |
| `ov_m4_wmedian_elongation` | **M4:** area-weighted median of longest ÷ shortest side of the minimum rotated rectangle |
| `m7_parcels_per_km2` | **M7 mapped ground-parcel density:** parcels per km² of land |
| `ov_m3_wiqr_ln`, `*_unweighted`, `m7_median_ln_m2` | Sensitivities |
| `muni_*`, `official_*`, `ref_records*` | Validation references |

**M7 parcels:**
- *São Paulo:* GeoSampa fiscal lot polygons, one per lot, a condominium lot counted once (1,677,181 lots). Each lot belongs to the district holding most of its land.
- *Chicago:* Cook 2024 ground pieces (no `Elevated*` air-rights parcels; polygons overlapping ≥ 90% merged; 605,803 pieces, all assigned by representative point).

## Pre-registered checks

| Check | Rule | Chicago | São Paulo |
|---|---|---|---|
| M3 vs the same faces from municipal centrelines (S8-4 i) | Spearman ≥ 0.90 | **0.959** pass | **0.563 fail** |
| M4 compactness vs municipal faces | ≥ 0.80 | **0.889** pass | **0.335 fail** |
| M4 elongation vs municipal faces | ≥ 0.80 | **0.810** pass | **0.499 fail** |
| M3 vs official blocks (S8-4 ii): Chicago 2020 Census blocks; São Paulo quadra viária `Quadra` | ≥ 0.80 | **0.831** pass | **0.977** pass |
| M7 density vs record density (S8-6): Chicago distinct 10-digit PINs (Assessor 2024); São Paulo distinct IPTU lots located by fiscal block | ≥ 0.95 | **0.998** pass (parcels ÷ records median 1.003) | **0.998** pass (0.999; 99.92% of IPTU lots located) |

Face counts:

| | Overture faces | Municipal faces | Official blocks |
|---|---|---|---|
| Chicago | 40,589 | 19,228 | 39,498 |
| São Paulo | 103,212 | 53,755 | 46,801 |

**Why São Paulo fails the like-for-like check (diagnosis, not a test):**
- **Faces from the municipal street lines are much larger in central districts** than both the Overture faces and the official blocks: 44× in SP:77, 9.9× in Brás, 5.7× in Bela Vista. In 10% of districts less than 43% of land falls inside any municipal face.
- **Missing joins are the likely cause.** In a box around Brás, Bela Vista and SP:77, 838 municipal line ends stop 0.01–10 m short of another line, against 149 for Overture (median gap 5.2 m; a quarter under 0.36 m). A ring that does not close cannot form a block, so neighbouring blocks merge.
- **The same Overture faces agree with São Paulo's official blocks at 0.977**, the highest agreement in this step.

**Post-hoc diagnostic** (written after the failure; `posthoc_reference_diagnostic.json`; not a test).

Which reference disagrees with the official blocks? M3 Spearman:

| | Overture vs official | Municipal-line faces vs official | Overture vs municipal |
|---|---|---|---|
| Chicago | 0.831 | 0.810 | 0.959 |
| São Paulo | **0.977** | **0.604** | 0.563 |

- In São Paulo the municipal-line faces are the outlier: they disagree with both other sources. In Chicago all three agree.
- **M4 of Overture faces vs the official quadras** (no M4 official check was pre-registered): compactness **0.911**, elongation **0.805**.
- A rebuild that closes line-end gaps in both networks was attempted and abandoned (too slow).

## Results

| | Chicago (77) | São Paulo (96) |
|---|---|---|
| M3 typical block (exp of median), p10 / p50 / p90 | 20,600 / 23,500 / 113,000 m² | 16,000 / 28,100 / 690,400 m² |
| M3 smallest | Loop 19,900; North Center, West Englewood, Washington Heights 20,400 | Ponte Rasa 12,500; República 13,900; São Miguel 14,500 |
| M3 largest | O'Hare 6.4 M; South Deering 4.6 M; Hegewisch 3.7 M | Marsilac 6.5 M; Anhanguera 6.4 M; Grajaú 6.1 M |
| M4 compactness p10 / p50 / p90 | 0.592 / 0.697 / 0.701 | 0.366 / 0.554 / 0.681 |
| M4 elongation p10 / p50 / p90 | 1.54 / 1.98 / 2.01 | 1.52 / 1.92 / 2.23 |
| M7 parcels per km², p10 / p50 / p90 | 626 / 1,177 / 1,464 | 723 / 1,748 / 2,593 |
| M7 highest / lowest | Bridgeport 1,702 / O'Hare 49, Riverdale 147, Loop 335 | Vila Medeiros 3,393 / Marsilac 5, Parelheiros 81 |
| Median parcel | 349 m² | 175 m² |
| Land inside faces (median; lowest) | 100%; South Chicago 77.5%, Oakland 78.9%, Uptown 79.9% (lakefront) | 100%; Marsilac 27%, Anhanguera 77% |

**Anchors:**

| | M3 typical block | M4 compactness | M4 elongation | M7 parcels per km² |
|---|---|---|---|---|
| Brás | 27,738 m² | 0.676 | 1.72 | 1,997 |
| Loop | 19,862 m² | 0.736 | 1.39 | 335 |

**What the numbers say:**
- **Chicago is one grid.** Most areas sit on the standard block of about 21,000–23,000 m² (incl. half-streets), shaped as a 2:1 rectangle (compactness 0.698, elongation 2.0).
  - M3 separates mainly the grid from industrial, airport and lakefront land.
  - M4 barely varies between the 10th and 90th percentiles in Chicago (0.697 vs 0.701).
- **São Paulo varies far more.** Irregular peripheral fabric has low compactness (Pedreira 0.08, Cidade Dutra 0.20), and rural or protected land forms huge faces.
- **Weighting decides the ranking.** Area-weighted and unweighted M3 are almost unrelated (Spearman 0.065 Chicago, −0.130 São Paulo): unweighted medians are driven by the number of small faces (islands, medians, slivers).

**Overlaps (S8-8, Spearman):**

| Pair | Chicago | São Paulo |
|---|---|---|
| M3 vs M1 | −0.54 | **−0.90** |
| M4 compactness vs M3 | −0.51 | −0.67 |
| M7 vs M3 | −0.73 | −0.76 |
| M7 vs M1 | 0.57 | 0.78 |
| M7 vs B1 | 0.43 | 0.72 |
| M7 vs U3 | 0.30 | 0.65 |

M3 is close to redundant with M1 in São Paulo (−0.90), as expected from block geometry. That is for the final review (C5).

## Limits

- **Centreline faces include half of each surrounding street**, so they are larger than official lot-edge blocks (São Paulo quadras median 24,800 m² vs Overture faces 28,100 m²). Ranks agree; sizes are not interchangeable.
- **Grade separation is ignored.** A bridge or viaduct crossing at a different level still splits the land beneath it.
- **Area weighting gives large non-block faces large weight.** Airports, rail yards, parks and protected land are treated as coarse grain, by design.
- **M7 is record consistency, not truth.** Parcels and records come from the same agencies. Condominium towers count once, so dense high-rise districts (Loop) read as coarse-grained.
- **M4 in Chicago has little variance.** Its information sits in a few non-grid areas.
